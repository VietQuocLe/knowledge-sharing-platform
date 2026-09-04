import logging
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.payment import CheckoutCreateResponse, OrderStatusResponse
from app.services import payment_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/create-checkout", response_model=CheckoutCreateResponse)
def create_checkout(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Tạo đơn hàng nâng cấp Pro (49.000đ/tháng) và lấy URL thanh toán VNPay Sandbox.
    Tự động dọn dẹp các đơn PENDING cũ của user.
    """
    client_ip = payment_service.get_client_ip(request)
    return payment_service.create_payment_order(db, current_user, client_ip)


@router.get("/vnpay-return", response_model=OrderStatusResponse)
def vnpay_return(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Xử lý khi trình duyệt redirect về từ cổng thanh toán VNPay (Dual-Fulfill Engine cho Localhost).
    Xác thực chữ ký HMAC-SHA512 và cập nhật trạng thái đơn hàng.
    """
    params = dict(request.query_params)
    return payment_service.process_vnpay_return(db, current_user, params)


@router.get("/vnpay-ipn", response_class=JSONResponse)
def vnpay_ipn(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Webhook IPN từ Server VNPay (Server-to-Server).
    Quy định khắt khe: LUÔN TRẢ VỀ HTTP 200 OK với body JSON chuẩn {"RspCode": "xx", "Message": "..."}.
    """
    params = dict(request.query_params)
    return payment_service.process_vnpay_ipn(db, params)


@router.get("/orders/{order_code}/status", response_model=OrderStatusResponse)
def get_order_status(
    order_code: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Tra cứu trạng thái đơn hàng (Bảo mật IDOR/Enumeration: Trả 404 nếu không phải chính chủ đơn).
    """
    return payment_service.get_order_status_safe(db, order_code, current_user)

