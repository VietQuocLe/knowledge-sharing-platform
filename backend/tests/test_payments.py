import concurrent.futures
import os
import sys
import time
import urllib.parse
import hmac
import hashlib
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import select

# Ensure backend directory is in sys.path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from app.main import app
from app.core.config import settings
from app.core.database import SessionLocal
from app.models.enums import PaymentStatus, SubscriptionTier, UserRole
from app.models.payment import PaymentOrder
from app.models.user import User
from app.models.notebook import Notebook
from app.services import payment_service, quota_service, notebook_service


def get_test_user(db, suffix: str = "") -> User:
    email = f"pay_test_{suffix}_{int(time.time() * 1000)}@example.com"
    user = User(
        email=email,
        full_name=f"Test User {suffix}",
        password_hash="test_hashed_pwd",
        role=UserRole.USER,
        tier=SubscriptionTier.FREE,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def build_signed_vnpay_params(order_code: str, amount: int, response_code: str = "00", trans_status: str = "00") -> dict:
    params = {
        "vnp_TmnCode": settings.VNPAY_TMN_CODE,
        "vnp_Amount": str(amount * 100),
        "vnp_TxnRef": order_code,
        "vnp_OrderInfo": f"Thanh toan don hang {order_code}",
        "vnp_ResponseCode": response_code,
        "vnp_TransactionStatus": trans_status,
        "vnp_TransactionNo": f"TRANS_{int(time.time())}",
        "vnp_PayDate": datetime.now(timezone(timedelta(hours=7))).strftime("%Y%m%d%H%M%S"),
    }
    sorted_items = sorted([(k, str(v)) for k, v in params.items() if v is not None and str(v) != ""])
    hash_data = urllib.parse.urlencode(sorted_items)
    secure_hash = hmac.new(
        settings.VNPAY_SECURE_SECRET.encode("utf-8"),
        hash_data.encode("utf-8"),
        hashlib.sha512,
    ).hexdigest()
    params["vnp_SecureHash"] = secure_hash
    return params


# =====================================================================
# 1. Test Client IP Extraction
# =====================================================================
def test_get_client_ip():
    req_proxy = MagicMock()
    req_proxy.headers = {"X-Forwarded-For": "203.0.113.195, 70.41.3.18, 150.172.238.178"}
    assert payment_service.get_client_ip(req_proxy) == "203.0.113.195"

    req_ipv6 = MagicMock()
    req_ipv6.headers = {}
    req_ipv6.client.host = "::1"
    assert payment_service.get_client_ip(req_ipv6) == "127.0.0.1"

    req_local = MagicMock()
    req_local.headers = {}
    req_local.client.host = "localhost"
    assert payment_service.get_client_ip(req_local) == "127.0.0.1"


# =====================================================================
# 2. Test Create Payment Order & Auto-cancel Old PENDING Orders
# =====================================================================
def test_create_payment_order_and_auto_cancel_old():
    db = SessionLocal()
    try:
        user = get_test_user(db, "order_cancel")

        # Đơn 1
        res1 = payment_service.create_payment_order(db, user, "127.0.0.1")
        assert len(res1.order_code) == 16
        assert "vnp_SecureHash=" in res1.payment_url

        order1 = db.execute(select(PaymentOrder).where(PaymentOrder.order_code == res1.order_code)).scalar_one()
        assert order1.status == PaymentStatus.PENDING

        # Đơn 2 cho cùng user
        res2 = payment_service.create_payment_order(db, user, "127.0.0.1")
        db.refresh(order1)
        order2 = db.execute(select(PaymentOrder).where(PaymentOrder.order_code == res2.order_code)).scalar_one()

        # Đơn 1 phải bị hủy, đơn 2 ở trạng thái PENDING
        assert order1.status == PaymentStatus.CANCELLED
        assert order2.status == PaymentStatus.PENDING
    finally:
        db.close()


# =====================================================================
# 3. Test Verify VNPay Signature
# =====================================================================
def test_verify_vnpay_signature():
    order_code = payment_service.generate_order_code()
    valid_params = build_signed_vnpay_params(order_code, 49000, "00")
    assert payment_service.verify_vnpay_signature(valid_params) is True

    # Tampered data
    tampered_params = dict(valid_params)
    tampered_params["vnp_Amount"] = "9999900"
    assert payment_service.verify_vnpay_signature(tampered_params) is False

    # TMN Code sai
    wrong_tmn = dict(valid_params)
    wrong_tmn["vnp_TmnCode"] = "WRONG_CODE"
    assert payment_service.verify_vnpay_signature(wrong_tmn) is False


# =====================================================================
# 4. Test Concurrency Race Condition (Pessimistic Lock with_for_update)
# =====================================================================
def test_concurrency_race_condition():
    db = SessionLocal()
    try:
        user = get_test_user(db, "race_cond")
        order_res = payment_service.create_payment_order(db, user, "127.0.0.1")
        order_code = order_res.order_code
        vnp_data = build_signed_vnpay_params(order_code, 49000, "00")

        # Giả lập 2 HTTP workers độc lập gọi fulfill_payment_order đồng thời với 2 session riêng
        def worker():
            thread_db = SessionLocal()
            try:
                payment_service.fulfill_payment_order(thread_db, order_code, vnp_data)
            finally:
                thread_db.close()

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(worker), executor.submit(worker)]
            concurrent.futures.wait(futures)

        # Kiểm tra trạng thái đơn và user
        db.refresh(user)
        final_order = db.execute(select(PaymentOrder).where(PaymentOrder.order_code == order_code)).scalar_one()

        assert final_order.status == PaymentStatus.SUCCESS
        assert user.tier == SubscriptionTier.PRO
        assert user.pro_expires_at is not None

        # Pro expires at phải đúng khoảng 30 ngày (29 đến 31 ngày), tuyệt đối KHÔNG PHẢI 60 ngày
        now_utc = datetime.now(timezone.utc)
        remaining_days = (user.pro_expires_at - now_utc).days
        assert 29 <= remaining_days <= 30
    finally:
        db.close()


# =====================================================================
# 5. Test Sequential Return then IPN
# =====================================================================
def test_sequential_return_then_ipn():
    db = SessionLocal()
    try:
        user = get_test_user(db, "return_first")
        order_res = payment_service.create_payment_order(db, user, "127.0.0.1")
        order_code = order_res.order_code
        vnp_data = build_signed_vnpay_params(order_code, 49000, "00")

        # 1. Return URL redirect về trước -> fulfill
        return_res = payment_service.process_vnpay_return(db, user, vnp_data)
        assert return_res.status == PaymentStatus.SUCCESS
        db.refresh(user)
        first_expiry = user.pro_expires_at

        # 2. IPN Server-to-Server gọi sau -> nhận diện đã confirmed
        ipn_response = payment_service.process_vnpay_ipn(db, vnp_data)
        assert ipn_response.status_code == 200
        import json
        body = json.loads(ipn_response.body.decode("utf-8"))
        assert body["RspCode"] == "02"  # Order already confirmed

        db.refresh(user)
        assert user.pro_expires_at == first_expiry  # Không bị cộng dồn
    finally:
        db.close()


# =====================================================================
# 6. Test Sequential IPN then Return
# =====================================================================
def test_sequential_ipn_then_return():
    db = SessionLocal()
    try:
        user = get_test_user(db, "ipn_first")
        order_res = payment_service.create_payment_order(db, user, "127.0.0.1")
        order_code = order_res.order_code
        vnp_data = build_signed_vnpay_params(order_code, 49000, "00")

        # 1. IPN đến trước -> fulfill
        ipn_response = payment_service.process_vnpay_ipn(db, vnp_data)
        assert ipn_response.status_code == 200
        import json
        body = json.loads(ipn_response.body.decode("utf-8"))
        assert body["RspCode"] == "00"  # Confirm Success

        db.refresh(user)
        first_expiry = user.pro_expires_at
        assert user.tier == SubscriptionTier.PRO

        # 2. Return redirect về sau -> nhận diện đã SUCCESS, trả thông tin bình thường
        return_res = payment_service.process_vnpay_return(db, user, vnp_data)
        assert return_res.status == PaymentStatus.SUCCESS

        db.refresh(user)
        assert user.pro_expires_at == first_expiry  # Không bị cộng dồn
    finally:
        db.close()


# =====================================================================
# 7. Test IDOR Protection (404 NOT FOUND)
# =====================================================================
def test_idor_protection():
    db = SessionLocal()
    try:
        user_a = get_test_user(db, "user_a")
        user_b = get_test_user(db, "user_b")
        admin = User(
            email=f"admin_test_{int(time.time())}@example.com",
            full_name="Admin Test",
            role=UserRole.ADMIN,
            is_active=True,
        )
        db.add(admin)
        db.commit()

        order_res = payment_service.create_payment_order(db, user_a, "127.0.0.1")
        order_code = order_res.order_code

        # User A xem đơn của chính mình -> OK
        status_a = payment_service.get_order_status_safe(db, order_code, user_a)
        assert status_a.order_code == order_code

        # User B xem đơn của User A -> Phải ném 404 NOT FOUND (chống Enumeration)
        with pytest.raises(HTTPException) as exc_info:
            payment_service.get_order_status_safe(db, order_code, user_b)
        assert exc_info.value.status_code == 404

        # Admin xem đơn của User A -> OK
        status_admin = payment_service.get_order_status_safe(db, order_code, admin)
        assert status_admin.order_code == order_code
    finally:
        db.close()


# =====================================================================
# 8. Test IPN Fallback CANCELLED for All Error Codes & HTTP 200 Always
# =====================================================================
def test_ipn_error_codes_mapping_and_http_200():
    db = SessionLocal()
    try:
        user = get_test_user(db, "errors_mapping")
        order_res = payment_service.create_payment_order(db, user, "127.0.0.1")
        order_code = order_res.order_code

        # User bấm hủy giao dịch (vnp_ResponseCode = "24")
        params_cancelled = build_signed_vnpay_params(order_code, 49000, response_code="24", trans_status="02")
        ipn_resp = payment_service.process_vnpay_ipn(db, params_cancelled)

        # Bắt buộc HTTP 200 OK
        assert ipn_resp.status_code == 200
        import json
        body = json.loads(ipn_resp.body.decode("utf-8"))
        assert body["RspCode"] == "00"

        # Đơn phải chuyển CANCELLED ngay
        order = db.execute(select(PaymentOrder).where(PaymentOrder.order_code == order_code)).scalar_one()
        assert order.status == PaymentStatus.CANCELLED
    finally:
        db.close()


# =====================================================================
# 9. Test Soft-cap Quota Policy (Không xóa cũ, chỉ chặn thêm mới)
# =====================================================================
def test_softcap_quota_policy():
    db = SessionLocal()
    try:
        user = get_test_user(db, "softcap")
        # Giả lập user từng là Pro nhưng đã hết hạn hôm qua
        user.tier = SubscriptionTier.PRO
        user.pro_expires_at = datetime.now(timezone.utc) - timedelta(days=1)
        db.commit()

        # Tạo 1 notebook
        nb = Notebook(title="Softcap Test Notebook", owner_id=user.id)
        db.add(nb)
        db.commit()
        db.refresh(nb)

        # 1. Lazy Downgrade ngầm khi gọi get_effective_user_tier
        effective_tier = quota_service.get_effective_user_tier(db, user)
        assert effective_tier == SubscriptionTier.FREE
        assert user.tier == SubscriptionTier.FREE

        # Quota Free là 8 sources, 10 quiz
        quotas = quota_service.get_user_quotas(effective_tier)
        assert quotas.max_sources == 8
        assert quotas.max_artifacts == 10

        # Giả lập notebook đang có 15 nguồn (tạo từ thời còn Pro)
        # Hàm check_sources_quota phải ném 400 Bad Request kèm thông báo chi tiết
        with pytest.raises(HTTPException) as exc_info:
            # Mock get_notebook_source_count trả về 15
            with pytest.MonkeyPatch.context() as mp:
                mp.setattr("app.services.notebook_service.get_notebook_source_count", lambda _db, _nb_id: 15)
                quota_service.check_sources_quota(db, user, nb.id)

        assert exc_info.value.status_code == 400
        assert "15/8 nguồn" in exc_info.value.detail
        assert "vượt hạn mức" in exc_info.value.detail
    finally:
        db.close()


if __name__ == "__main__":
    pytest.main(["-v", __file__])
