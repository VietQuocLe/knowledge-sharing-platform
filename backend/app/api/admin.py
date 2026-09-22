from datetime import date, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import Date, cast, func, case
from sqlalchemy.orm import Session

from app.api.auth import require_admin
from app.core.database import get_db
from app.models.document import Document
from app.models.enums import DocumentStatus, PaymentStatus, SubscriptionTier
from app.models.notebook import Notebook
from app.models.payment import PaymentOrder
from app.models.user import User

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/stats")
def get_admin_stats(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Return aggregated platform statistics for the admin dashboard."""
    # User breakdown by tier and active status
    user_stats = db.query(
        func.count(User.id).label("total"),
        func.sum(case((User.tier == SubscriptionTier.PRO, 1), else_=0)).label("pro"),
        func.sum(case((User.tier == SubscriptionTier.FREE, 1), else_=0)).label("free"),
        func.sum(case((User.is_active.is_(True), 1), else_=0)).label("active"),
    ).one()

    # Document breakdown by status
    doc_stats = db.query(
        func.count(Document.id).label("total"),
        func.sum(case((Document.status == DocumentStatus.PUBLIC, 1), else_=0)).label("public"),
        func.sum(case((Document.status == DocumentStatus.DRAFT, 1), else_=0)).label("draft"),
    ).one()

    # Notebook count
    notebook_count = db.query(func.count(Notebook.id)).scalar() or 0

    # Payment revenue from successful orders
    payment_stats = db.query(
        func.count(PaymentOrder.id).label("successful_orders"),
        func.coalesce(func.sum(PaymentOrder.amount), 0).label("total_revenue"),
    ).filter(PaymentOrder.status == PaymentStatus.SUCCESS).one()

    return {
        "users": {
            "total": user_stats.total or 0,
            "pro": int(user_stats.pro or 0),
            "free": int(user_stats.free or 0),
            "active": int(user_stats.active or 0),
        },
        "documents": {
            "total": doc_stats.total or 0,
            "public": int(doc_stats.public or 0),
            "draft": int(doc_stats.draft or 0),
        },
        "notebooks": {
            "total": notebook_count,
        },
        "payments": {
            "total_revenue": int(payment_stats.total_revenue or 0),
            "successful_orders": payment_stats.successful_orders or 0,
        },
    }


@router.get("/activities")
def get_admin_activities(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Return recent VNPay transactions and newly registered users."""
    recent_transactions = (
        db.query(PaymentOrder, User.email)
        .outerjoin(User, PaymentOrder.user_id == User.id)
        .order_by(PaymentOrder.created_at.desc())
        .limit(10)
        .all()
    )

    recent_users = (
        db.query(User)
        .order_by(User.created_at.desc())
        .limit(10)
        .all()
    )

    return {
        "recent_transactions": [
            {
                "order_code": po.order_code,
                "user_email": email or "N/A",
                "amount": po.amount,
                "plan_type": po.plan_type,
                "status": po.status.value,
                "created_at": po.created_at.isoformat(),
                "paid_at": po.paid_at.isoformat() if po.paid_at else None,
            }
            for po, email in recent_transactions
        ],
        "recent_users": [
            {
                "id": u.id,
                "email": u.email,
                "full_name": u.full_name,
                "tier": u.tier.value,
                "role": u.role.value,
                "is_active": u.is_active,
                "created_at": u.created_at.isoformat(),
            }
            for u in recent_users
        ],
    }


@router.get("/trends")
def get_admin_trends(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Return daily user registrations and revenue for the past 30 days."""
    today = date.today()
    thirty_days_ago = today - timedelta(days=29)

    # New user registrations per day
    user_reg_rows = (
        db.query(
            cast(User.created_at, Date).label("day"),
            func.count(User.id).label("count"),
        )
        .filter(User.created_at >= thirty_days_ago)
        .group_by(cast(User.created_at, Date))
        .order_by(cast(User.created_at, Date))
        .all()
    )

    # Revenue from successful payments per day (by paid_at)
    revenue_rows = (
        db.query(
            cast(PaymentOrder.paid_at, Date).label("day"),
            func.sum(PaymentOrder.amount).label("amount"),
        )
        .filter(
            PaymentOrder.status == PaymentStatus.SUCCESS,
            PaymentOrder.paid_at.isnot(None),
            PaymentOrder.paid_at >= thirty_days_ago,
        )
        .group_by(cast(PaymentOrder.paid_at, Date))
        .order_by(cast(PaymentOrder.paid_at, Date))
        .all()
    )

    # Build lookup maps keyed by ISO date string
    reg_map: dict[str, int] = {str(r.day): r.count for r in user_reg_rows}
    rev_map: dict[str, int] = {str(r.day): int(r.amount) for r in revenue_rows}

    # Generate complete 30-day date range (fill gaps with 0)
    dates = [(thirty_days_ago + timedelta(days=i)).isoformat() for i in range(30)]

    return {
        "user_registrations": [
            {"date": d, "count": reg_map.get(d, 0)} for d in dates
        ],
        "daily_revenue": [
            {"date": d, "amount": rev_map.get(d, 0)} for d in dates
        ],
    }

