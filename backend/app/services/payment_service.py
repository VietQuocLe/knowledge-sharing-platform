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
    Trích xuất an toàn Client IP.
    Xử lý đúng IP thật khi chạy sau Reverse Proxy (X-Forwarded-For)
    và chuẩn hóa IPv6 ::1 hoặc localhost về 127.0.0.1 để VNPay không từ chối.
    """
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    ip = request.client.host if request.client else "127.0.0.1"
    return "127.0.0.1" if ip in ("::1", "localhost") else ip


def generate_order_code() -> str:
    """
    Khóa cứng định dạng vnp_TxnRef (Hard Rule):
    Format: 10 chữ số timestamp Unix + 6 ký tự hex ngẫu nhiên viết thường.
    Độ dài đúng 16 ký tự, chỉ gồm [0-9a-z], đảm bảo tính duy nhất 100%.
    """
    return f"{int(time.time())}{uuid.uuid4().hex[:6]}"


def create_payment_order(db: Session, user: User, ip_address: str) -> CheckoutCreateResponse:
    """
    Tạo đơn hàng nâng cấp Pro và sinh URL thanh toán VNPay Sandbox.
    Tự động hủy các đơn PENDING cũ của user để tránh rác hệ thống.
    """
    # 1. Tự động hủy các đơn hàng PENDING cũ của user
    db.execute(
        update(PaymentOrder)
        .where(
            PaymentOrder.user_id == user.id,
            PaymentOrder.status == PaymentStatus.PENDING,
        )
        .values(status=PaymentStatus.CANCELLED)
    )

    # 2. Sinh mã đơn hàng bất biến và lưu PaymentOrder
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

    # 3. Chuẩn hóa ngày giờ theo GMT+7 (Asia/Ho_Chi_Minh)
    tz_vn = timezone(timedelta(hours=7))
    now_vn = datetime.now(tz_vn)
    vnp_create_date = now_vn.strftime("%Y%m%d%H%M%S")
    vnp_expire_date = (now_vn + timedelta(minutes=15)).strftime("%Y%m%d%H%M%S")

    # 4. Nội dung thanh toán không dấu (chống lỗi encoding Checksum 97)
    vnp_order_info = f"Thanh toan goi Pro 1 thang - Don hang {order_code}"

    # 5. Build tham số VNPay 2.1.0
    vnp_params: dict[str, str] = {
        "vnp_Version": "2.1.0",
        "vnp_Command": "pay",
        "vnp_TmnCode": settings.VNPAY_TMN_CODE,
        "vnp_Amount": str(amount * 100),  # VNPay nhân 100 số tiền
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

    # 6. Sắp xếp key alphabet và encode
    sorted_items = sorted(
        [(k, str(v)) for k, v in vnp_params.items() if v is not None and str(v) != ""]
    )
    hash_data = urllib.parse.urlencode(sorted_items)

    # 7. Ký HMAC-SHA512
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
    Xác thực chữ ký HMAC-SHA512 của dữ liệu VNPay gửi về.
    Bắt buộc kiểm tra vnp_TmnCode trước khi tính toán hash.
    """
    # 1. Xác thực Merchant Code
    if params.get("vnp_TmnCode") != settings.VNPAY_TMN_CODE:
        logger.warning("VNPay signature failed: TMN_CODE mismatch (%s != %s)",
                       params.get("vnp_TmnCode"), settings.VNPAY_TMN_CODE)
        return False

    received_hash = params.get("vnp_SecureHash")
    if not received_hash:
        return False

    # 2. Lọc các tham số bắt đầu bằng vnp_, loại bỏ vnp_SecureHash và vnp_SecureHashType
    filtered_items = [
        (k, str(v))
        for k, v in params.items()
        if k.startswith("vnp_")
        and k not in ("vnp_SecureHash", "vnp_SecureHashType")
        and v is not None
        and str(v) != ""
    ]

    # 3. Sắp xếp alphabet theo key và encode query string
    sorted_items = sorted(filtered_items)
    hash_data = urllib.parse.urlencode(sorted_items)

    # 4. Tính toán hash HMAC-SHA512
    calculated_hash = hmac.new(
        settings.VNPAY_SECURE_SECRET.encode("utf-8"),
        hash_data.encode("utf-8"),
        hashlib.sha512,
    ).hexdigest()

    # 5. So sánh an toàn chống timing attack
    return hmac.compare_digest(calculated_hash.lower(), received_hash.lower())


def fulfill_payment_order(db: Session, order_code: str, vnp_data: dict) -> PaymentOrder | None:
    """
    Idempotency Guard: Fulfill đơn hàng an toàn với Pessimistic Locking (SELECT ... FOR UPDATE).
    Đảm bảo cả Return URL và IPN URL cùng gọi thì chỉ có 1 luồng thực thi gia hạn Pro.
    """
    # Khóa dòng đơn hàng trong transaction
    order = db.execute(
        select(PaymentOrder)
        .where(PaymentOrder.order_code == order_code)
        .with_for_update()
    ).scalar_one_or_none()

    if not order or order.status != PaymentStatus.PENDING:
        # Đã được xử lý bởi luồng kia hoặc đã hủy -> Bỏ qua
        return order

    # Validate số tiền thanh toán (VNPay nhân 100)
    vnp_amount = int(vnp_data.get("vnp_Amount", 0)) // 100
    if order.amount != vnp_amount:
        raise ValueError(f"Số tiền không khớp: order={order.amount}, vnpay={vnp_amount}")

    # Cập nhật trạng thái SUCCESS
    order.status = PaymentStatus.SUCCESS
    order.paid_at = datetime.now(timezone.utc)
    order.vnp_transaction_no = vnp_data.get("vnp_TransactionNo")

    # Gia hạn Pro 30 ngày cho User (cộng nối tiếp nếu còn hạn)
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
    Xử lý Webhook IPN từ Server VNPay.
    Quy chuẩn bất biến: LUÔN TRẢ VỀ HTTP 200 OK với body JSON chuẩn.
    """
    try:
        # 1. Xác thực chữ ký & Merchant code
        if not verify_vnpay_signature(params):
            return JSONResponse(status_code=200, content={"RspCode": "97", "Message": "Invalid Checksum"})

        order_code = params.get("vnp_TxnRef")
        if not order_code:
            return JSONResponse(status_code=200, content={"RspCode": "01", "Message": "Order Not Found"})

        # 2. Tìm đơn hàng
        order = db.execute(
            select(PaymentOrder).where(PaymentOrder.order_code == order_code)
        ).scalar_one_or_none()

        if not order:
            return JSONResponse(status_code=200, content={"RspCode": "01", "Message": "Order Not Found"})

        # 3. Kiểm tra số tiền
        vnp_amount = int(params.get("vnp_Amount", 0)) // 100
        if order.amount != vnp_amount:
            return JSONResponse(status_code=200, content={"RspCode": "04", "Message": "Invalid Amount"})

        # 4. Kiểm tra xem đơn đã được xác nhận trước đó chưa (bởi Return URL hoặc IPN trước)
        if order.status != PaymentStatus.PENDING:
            return JSONResponse(status_code=200, content={"RspCode": "02", "Message": "Order already confirmed"})

        # 5. Xử lý trạng thái giao dịch
        vnp_response_code = params.get("vnp_ResponseCode")
        vnp_trans_status = params.get("vnp_TransactionStatus")

        if vnp_response_code == "00" and vnp_trans_status == "00":
            fulfill_payment_order(db, order_code, params)
            return JSONResponse(status_code=200, content={"RspCode": "00", "Message": "Confirm Success"})

        # Bất kỳ mã lỗi nào khác (24, 07, 09, 10, 11, 51, 65...) -> Chuyển CANCELLED ngay
        order.status = PaymentStatus.CANCELLED
        db.add(order)
        db.commit()
        return JSONResponse(status_code=200, content={"RspCode": "00", "Message": "Confirm Success"})

    except Exception as exc:
        logger.error("VNPay IPN Unhandled Error: %s", exc, exc_info=True)
        return JSONResponse(status_code=200, content={"RspCode": "99", "Message": "Unknown Error"})


def process_vnpay_return(db: Session, user: User, params: dict) -> OrderStatusResponse:
    """
    Xử lý khi trình duyệt redirect về từ cổng VNPay (Dual-Fulfill Engine cho Localhost).
    Bắt buộc verify chữ ký, thực hiện fulfill an toàn nếu đơn vẫn PENDING.
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

    # Chống IDOR: Chỉ tìm đơn thuộc quyền sở hữu của user
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
        # Thành công -> Fulfill (nếu đơn chưa được IPN fulfill trước đó)
        fulfill_payment_order(db, order_code, params)
    else:
        # Bất kỳ mã lỗi nào khác -> Chuyển CANCELLED nếu vẫn PENDING
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
    Tra cứu trạng thái đơn hàng an toàn chống IDOR và Enumeration Attack:
    Nếu không phải đơn của chính user (hoặc Admin), trả HTTP 404 NOT FOUND đồng nhất.
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

    # Lấy thông tin user sở hữu đơn
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

