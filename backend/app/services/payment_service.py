import hashlib
import hmac
import logging
import time
import urllib.parse
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.enums import PaymentStatus, SubscriptionTier, UserRole
from app.models.payment import PaymentOrder
from app.models.user import User
from app.schemas.payment import CheckoutCreateResponse, OrderStatusResponse

logger = logging.getLogger(__name__)


def get_client_ip(request: Request) -> str:
    """
    Safely extract client IP address.
    Handles proxy headers (X-Forwarded-For) and normalizes IPv6 ::1 or localhost
    to 127.0.0.1 for VNPay gateway compatibility.
    """
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    ip = request.client.host if request.client else "127.0.0.1"
    return "127.0.0.1" if ip in ("::1", "localhost") else ip


def generate_order_code() -> str:
    """
    Generate standard vnp_TxnRef order code:
    Format: 10-digit Unix timestamp + 6-character random hex string.
    Exactly 16 alphanumeric lowercase characters [0-9a-z], guaranteeing uniqueness.
    """
    return f"{int(time.time())}{uuid.uuid4().hex[:6]}"


def create_payment_order(db: Session, user: User, ip_address: str) -> CheckoutCreateResponse:
    """
    Creates a Pro upgrade payment order and generates VNPay payment URL.
    Cancels any previous pending orders for the user to prevent stale entries.
    """
    # 1. Cancel previous pending orders for user
    db.execute(
        update(PaymentOrder)
        .where(
            PaymentOrder.user_id == user.id,
            PaymentOrder.status == PaymentStatus.PENDING,
        )
        .values(status=PaymentStatus.CANCELLED)
    )

    # 2. Generate immutable order code and record PaymentOrder
    order_code = generate_order_code()
    amount = settings.PRO_PLAN_PRICE

    payment_order = PaymentOrder(
        order_code=order_code,
        user_id=user.id,
        amount=amount,
        plan_type="1_MONTH",
        status=PaymentStatus.PENDING,
    )
    db.add(payment_order)
    db.commit()
    db.refresh(payment_order)

    # 3. Normalize timestamp to GMT+7 (Asia/Ho_Chi_Minh)
    tz_vn = timezone(timedelta(hours=7))
    now_vn = datetime.now(tz_vn)
    vnp_create_date = now_vn.strftime("%Y%m%d%H%M%S")
    vnp_expire_date = (now_vn + timedelta(minutes=15)).strftime("%Y%m%d%H%M%S")

    # 4. Unaccented order info to avoid VNPay checksum encoding issues
    vnp_order_info = f"Thanh toan goi Pro 1 thang - Don hang {order_code}"

    # 5. Build VNPay 2.1.0 query parameters
    vnp_params: dict[str, str] = {
        "vnp_Version": "2.1.0",
        "vnp_Command": "pay",
        "vnp_TmnCode": settings.VNPAY_TMN_CODE,
        "vnp_Amount": str(amount * 100),  # VNPay amount multiplied by 100
        "vnp_CurrCode": "VND",
        "vnp_TxnRef": order_code,
        "vnp_OrderInfo": vnp_order_info,
        "vnp_OrderType": "other",
        "vnp_Locale": "vn",
        "vnp_ReturnUrl": settings.VNPAY_RETURN_URL,
        "vnp_IpAddr": ip_address,
        "vnp_CreateDate": vnp_create_date,
        "vnp_ExpireDate": vnp_expire_date,
    }

    # 6. Sort alphabetically by key and URL-encode
    sorted_items = sorted(
        [(k, str(v)) for k, v in vnp_params.items() if v is not None and str(v) != ""]
    )
    hash_data = urllib.parse.urlencode(sorted_items)

    # 7. Compute HMAC-SHA512 checksum
    secure_hash = hmac.new(
        settings.VNPAY_SECURE_SECRET.encode("utf-8"),
        hash_data.encode("utf-8"),
        hashlib.sha512,
    ).hexdigest()

    payment_url = f"{settings.VNPAY_PAYMENT_URL}?{hash_data}&vnp_SecureHash={secure_hash}"

    logger.info("Created VNPay order %s for user %s: amount=%s", order_code, user.id, amount)

    return CheckoutCreateResponse(
        order_code=order_code,
        payment_url=payment_url,
        amount=amount,
    )


def verify_vnpay_signature(params: dict) -> bool:
    """
    Verifies HMAC-SHA512 checksum of VNPay response data.
    Validates vnp_TmnCode before computing hash.
    """
    # 1. Validate Merchant Code
    if params.get("vnp_TmnCode") != settings.VNPAY_TMN_CODE:
        logger.warning("VNPay signature failed: TMN_CODE mismatch (%s != %s)",
                       params.get("vnp_TmnCode"), settings.VNPAY_TMN_CODE)
        return False

    received_hash = params.get("vnp_SecureHash")
    if not received_hash:
        return False

    # 2. Filter vnp_ parameters, excluding hash fields
    filtered_items = [
        (k, str(v))
        for k, v in params.items()
        if k.startswith("vnp_")
        and k not in ("vnp_SecureHash", "vnp_SecureHashType")
        and v is not None
        and str(v) != ""
    ]

    # 3. Sort alphabetically and encode query string
    sorted_items = sorted(filtered_items)
    hash_data = urllib.parse.urlencode(sorted_items)

    # 4. Compute HMAC-SHA512 hash
    calculated_hash = hmac.new(
        settings.VNPAY_SECURE_SECRET.encode("utf-8"),
        hash_data.encode("utf-8"),
        hashlib.sha512,
    ).hexdigest()

    # 5. Constant-time comparison to prevent timing attacks
    return hmac.compare_digest(calculated_hash.lower(), received_hash.lower())


def fulfill_payment_order(db: Session, order_code: str, vnp_data: dict) -> PaymentOrder | None:
    """
    Idempotent order fulfillment using pessimistic locking (SELECT ... FOR UPDATE).
    Guarantees single fulfillment execution between Return URL and IPN Webhook.
    """
    # Lock order row in transaction
    order = db.execute(
        select(PaymentOrder)
        .where(PaymentOrder.order_code == order_code)
        .with_for_update()
    ).scalar_one_or_none()

    if not order or order.status != PaymentStatus.PENDING:
        # Already processed or cancelled -> Skip
        return order

    # Validate amount (VNPay amount is multiplied by 100)
    vnp_amount = int(vnp_data.get("vnp_Amount", 0)) // 100
    if order.amount != vnp_amount:
        raise ValueError(f"Amount mismatch: order={order.amount}, vnpay={vnp_amount}")

    # Update status to SUCCESS
    order.status = PaymentStatus.SUCCESS
    order.paid_at = datetime.now(timezone.utc)
    order.vnp_transaction_no = vnp_data.get("vnp_TransactionNo")

    # Extend Pro tier by 30 days (cumulative if active)
    user = db.execute(select(User).where(User.id == order.user_id)).scalar_one_or_none()
    if user:
        now_utc = datetime.now(timezone.utc)
        current_expiry = user.pro_expires_at
        if current_expiry is not None:
            if current_expiry.tzinfo is None:
                current_expiry = current_expiry.replace(tzinfo=timezone.utc)
            else:
                current_expiry = current_expiry.astimezone(timezone.utc)

        base_time = current_expiry if (current_expiry and current_expiry > now_utc) else now_utc
        user.pro_expires_at = base_time + timedelta(days=30)
        user.tier = SubscriptionTier.PRO
        db.add(user)

    db.add(order)
    db.commit()
    db.refresh(order)

    logger.info("Order %s fulfilled successfully. User %s upgraded to PRO until %s",
                order_code, order.user_id, user.pro_expires_at if user else None)
    return order


def process_vnpay_ipn(db: Session, params: dict) -> JSONResponse:
    """
    Processes VNPay IPN Webhook.
    Always returns HTTP 200 with standard JSON response body.
    """
    try:
        # 1. Verify signature and merchant code
        if not verify_vnpay_signature(params):
            return JSONResponse(status_code=200, content={"RspCode": "97", "Message": "Invalid Checksum"})

        order_code = params.get("vnp_TxnRef")
        if not order_code:
            return JSONResponse(status_code=200, content={"RspCode": "01", "Message": "Order Not Found"})

        # 2. Find order
        order = db.execute(
            select(PaymentOrder).where(PaymentOrder.order_code == order_code)
        ).scalar_one_or_none()

        if not order:
            return JSONResponse(status_code=200, content={"RspCode": "01", "Message": "Order Not Found"})

        # 3. Validate amount
        vnp_amount = int(params.get("vnp_Amount", 0)) // 100
        if order.amount != vnp_amount:
            return JSONResponse(status_code=200, content={"RspCode": "04", "Message": "Invalid Amount"})

        # 4. Check if order was already confirmed
        if order.status != PaymentStatus.PENDING:
            return JSONResponse(status_code=200, content={"RspCode": "02", "Message": "Order already confirmed"})

        # 5. Process transaction status
        vnp_response_code = params.get("vnp_ResponseCode")
        vnp_trans_status = params.get("vnp_TransactionStatus")

        if vnp_response_code == "00" and vnp_trans_status == "00":
            fulfill_payment_order(db, order_code, params)
            return JSONResponse(status_code=200, content={"RspCode": "00", "Message": "Confirm Success"})

        # Any other error code -> Transition to CANCELLED
        order.status = PaymentStatus.CANCELLED
        db.add(order)
        db.commit()
        return JSONResponse(status_code=200, content={"RspCode": "00", "Message": "Confirm Success"})

    except Exception as exc:
        logger.error("VNPay IPN Unhandled Error: %s", exc, exc_info=True)
        return JSONResponse(status_code=200, content={"RspCode": "99", "Message": "Unknown Error"})


def process_vnpay_return(db: Session, user: User, params: dict) -> OrderStatusResponse:
    """
    Processes user browser return redirect from VNPay (Dual-Fulfill Engine for localhost).
    Verifies signature and idempotently fulfills pending order.
    """
    if not verify_vnpay_signature(params):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Chữ ký xác thực giao dịch VNPay không hợp lệ.",
        )

    order_code = params.get("vnp_TxnRef")
    if not order_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Thiếu mã giao dịch (vnp_TxnRef).",
        )

    # Anti-IDOR: Find order owned by current user (or admin)
    stmt = select(PaymentOrder).where(
        PaymentOrder.order_code == order_code,
        PaymentOrder.user_id == user.id,
    )
    if user.role == UserRole.ADMIN:
        stmt = select(PaymentOrder).where(PaymentOrder.order_code == order_code)

    order = db.execute(stmt).scalar_one_or_none()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Đơn hàng không tồn tại hoặc bạn không có quyền truy cập.",
        )

    vnp_response_code = params.get("vnp_ResponseCode")
    vnp_trans_status = params.get("vnp_TransactionStatus")

    if vnp_response_code == "00" and vnp_trans_status == "00":
        # Success -> Fulfill order if not yet fulfilled by IPN
        fulfill_payment_order(db, order_code, params)
    else:
        # Any other response code -> Transition to CANCELLED if still PENDING
        if order.status == PaymentStatus.PENDING:
            order.status = PaymentStatus.CANCELLED
            db.add(order)
            db.commit()

    db.refresh(order)
    db.refresh(user)

    return OrderStatusResponse(
        order_code=order.order_code,
        status=order.status,
        amount=order.amount,
        plan_type=order.plan_type,
        paid_at=order.paid_at,
        tier=user.tier,
        pro_expires_at=user.pro_expires_at,
    )


def get_order_status_safe(db: Session, order_code: str, user: User) -> OrderStatusResponse:
    """
    Retrieves order status safely against IDOR and Enumeration attacks.
    Returns HTTP 404 if order does not belong to user (unless admin).
    """
    stmt = select(PaymentOrder).where(
        PaymentOrder.order_code == order_code,
        PaymentOrder.user_id == user.id,
    )
    if user.role == UserRole.ADMIN:
        stmt = select(PaymentOrder).where(PaymentOrder.order_code == order_code)

    order = db.execute(stmt).scalar_one_or_none()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Đơn hàng không tồn tại hoặc bạn không có quyền truy cập.",
        )

    # Retrieve order owner user
    owner = user if order.user_id == user.id else db.execute(select(User).where(User.id == order.user_id)).scalar_one()

    return OrderStatusResponse(
        order_code=order.order_code,
        status=order.status,
        amount=order.amount,
        plan_type=order.plan_type,
        paid_at=order.paid_at,
        tier=owner.tier,
        pro_expires_at=owner.pro_expires_at,
    )

