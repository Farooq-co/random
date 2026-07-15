from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.refund import Refund
from app.models.shift import Shift
from app.models.transaction import Transaction


def get_sales_by_day(db: Session) -> list[dict]:
    rows = (
        db.query(
            func.date(Transaction.created_at).label("date"),
            func.sum(Transaction.amount).label("total_sales"),
        )
        .group_by(func.date(Transaction.created_at))
        .order_by(func.date(Transaction.created_at))
        .all()
    )
    return [{"date": row.date, "total_sales": float(row.total_sales)} for row in rows]


def get_hourly_sales(db: Session) -> list[dict]:
    rows = (
        db.query(
            func.strftime("%Y-%m-%d %H:00:00", Transaction.created_at).label("hour"),
            func.sum(Transaction.amount).label("total_sales"),
        )
        .group_by(func.strftime("%Y-%m-%d %H:00:00", Transaction.created_at))
        .order_by(func.strftime("%Y-%m-%d %H:00:00", Transaction.created_at))
        .all()
    )
    return [{"hour": row.hour, "total_sales": float(row.total_sales)} for row in rows]


def get_refunds_by_day(db: Session) -> list[dict]:
    rows = (
        db.query(
            func.date(Refund.created_at).label("date"),
            func.sum(Refund.amount).label("total_refunds"),
        )
        .group_by(func.date(Refund.created_at))
        .order_by(func.date(Refund.created_at))
        .all()
    )
    return [
        {"date": row.date, "total_refunds": float(row.total_refunds)} for row in rows
    ]


def get_cashier_performance(db: Session) -> list[dict]:
    rows = (
        db.query(
            Transaction.cashier.label("cashier"),
            func.count(Transaction.id).label("transaction_count"),
            func.sum(Transaction.amount).label("total_sales"),
            func.avg(Transaction.amount).label("average_transaction"),
        )
        .group_by(Transaction.cashier)
        .order_by(func.sum(Transaction.amount).desc())
        .all()
    )
    return [
        {
            "cashier": row.cashier,
            "transaction_count": row.transaction_count,
            "total_sales": float(row.total_sales),
            "average_transaction": round(float(row.average_transaction or 0), 2),
        }
        for row in rows
    ]


def get_top_stations(db: Session, limit: int = 10) -> list[dict]:
    rows = (
        db.query(
            Transaction.station_id.label("station_id"),
            func.count(Transaction.id).label("transaction_count"),
            func.sum(Transaction.amount).label("total_sales"),
        )
        .group_by(Transaction.station_id)
        .order_by(func.sum(Transaction.amount).desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "station_id": row.station_id,
            "transaction_count": row.transaction_count,
            "total_sales": float(row.total_sales),
        }
        for row in rows
    ]


def get_shrinkage_summary(db: Session) -> dict:
    average_cash_variance = round(
        float(db.query(func.avg(Shift.cash_variance)).scalar() or 0), 2
    )
    negative_variance = round(
        float(
            db.query(func.sum(Shift.cash_variance))
            .filter(Shift.cash_variance < 0)
            .scalar()
            or 0
        ),
        2,
    )
    positive_variance = round(
        float(
            db.query(func.sum(Shift.cash_variance))
            .filter(Shift.cash_variance > 0)
            .scalar()
            or 0
        ),
        2,
    )
    negative_shifts = db.query(Shift).filter(Shift.cash_variance < 0).count()
    positive_shifts = db.query(Shift).filter(Shift.cash_variance > 0).count()

    return {
        "average_cash_variance": average_cash_variance,
        "negative_variance": negative_variance,
        "positive_variance": positive_variance,
        "negative_shifts": negative_shifts,
        "positive_shifts": positive_shifts,
    }


def get_payment_method_summary(db: Session) -> list[dict]:
    rows = (
        db.query(Transaction.payment_method, func.count(Transaction.id).label("count"))
        .group_by(Transaction.payment_method)
        .order_by(func.count(Transaction.id).desc())
        .all()
    )
    return [{"label": row.payment_method, "value": row.count} for row in rows]


def get_fuel_type_summary(db: Session) -> list[dict]:
    rows = (
        db.query(Transaction.fuel_type, func.count(Transaction.id).label("count"))
        .group_by(Transaction.fuel_type)
        .order_by(func.count(Transaction.id).desc())
        .all()
    )
    return [{"label": row.fuel_type, "value": row.count} for row in rows]


def get_cash_variance_summary(db: Session) -> list[dict]:
    negative = db.query(Shift).filter(Shift.cash_variance < 0).count()
    positive = db.query(Shift).filter(Shift.cash_variance > 0).count()
    neutral = db.query(Shift).filter(Shift.cash_variance == 0).count()

    return [
        {"label": "negative", "value": negative},
        {"label": "positive", "value": positive},
        {"label": "neutral", "value": neutral},
    ]
