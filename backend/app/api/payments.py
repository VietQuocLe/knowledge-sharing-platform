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
    Create a Pro upgrade order (49,000 VND/month) and generate a VNPay Sandbox payment URL.
    Automatically expires stale PENDING orders for the user.
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
    Handle browser redirect from VNPay payment gateway (dual-fulfillment engine).
    Validates HMAC-SHA512 checksum signature and updates order status.
    """
    params = dict(request.query_params)
    return payment_service.process_vnpay_return(db, current_user, params)


@router.get("/vnpay-ipn", response_class=JSONResponse)
def vnpay_ipn(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Server-to-server IPN webhook from VNPay.
    Strict gateway requirement: Always return HTTP 200 with standard payload {"RspCode": "xx", "Message": "..."}.
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
    Query order status securely (anti-IDOR/enumeration: returns 404 if not order owner).
    """
    return payment_service.get_order_status_safe(db, order_code, current_user)

