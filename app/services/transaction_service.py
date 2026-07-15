from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.transaction import Transaction


def get_transactions(db: Session, skip: int = 0, limit: int = 50) -> list[Transaction]:
    return (
        db.query(Transaction)
        .order_by(Transaction.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_transaction_by_id(db: Session, transaction_id: int) -> Transaction | None:
    return db.query(Transaction).filter(Transaction.id == transaction_id).first()


def get_high_value_transactions(
    db: Session, threshold: float = 180.0
) -> list[Transaction]:
    return (
        db.query(Transaction)
        .filter(Transaction.amount >= threshold)
        .order_by(Transaction.created_at.desc())
        .all()
    )


def get_transactions_by_payment_method(
    db: Session, payment_method: str
) -> list[Transaction]:
    return (
        db.query(Transaction)
        .filter(Transaction.payment_method == payment_method)
        .order_by(Transaction.created_at.desc())
        .all()
    )


def get_transactions_by_fuel_type(db: Session, fuel_type: str) -> list[Transaction]:
    return (
        db.query(Transaction)
        .filter(Transaction.fuel_type == fuel_type)
        .order_by(Transaction.created_at.desc())
        .all()
    )


def get_transactions_by_status(db: Session, status: str) -> list[Transaction]:
    return (
        db.query(Transaction)
        .filter(Transaction.status == status)
        .order_by(Transaction.created_at.desc())
        .all()
    )


def get_transaction_summary(db: Session) -> dict:
    return {
        "total": db.query(Transaction).count(),
        "high_value": db.query(Transaction).filter(Transaction.amount >= 180).count(),
        "cash": db.query(Transaction)
        .filter(Transaction.payment_method == "Cash")
        .count(),
        "card": db.query(Transaction)
        .filter(Transaction.payment_method == "Card")
        .count(),
        "average_amount": round(
            float(db.query(func.avg(Transaction.amount)).scalar() or 0), 2
        ),
        "total_amount": round(
            float(db.query(func.sum(Transaction.amount)).scalar() or 0), 2
        ),
    }


def search_transactions(
    db: Session,
    station_id: str | None = None,
    cashier: str | None = None,
    fuel_type: str | None = None,
    payment_method: str | None = None,
    transaction_type: str | None = None,
    status: str | None = None,
) -> list[Transaction]:
    query = db.query(Transaction)

    if station_id:
        query = query.filter(Transaction.station_id == station_id)
    if cashier:
        query = query.filter(Transaction.cashier.ilike(f"%{cashier}%"))
    if fuel_type:
        query = query.filter(Transaction.fuel_type == fuel_type)
    if payment_method:
        query = query.filter(Transaction.payment_method == payment_method)
    if transaction_type:
        query = query.filter(Transaction.transaction_type == transaction_type)
    if status:
        query = query.filter(Transaction.status == status)

    return query.order_by(Transaction.created_at.desc()).all()


def get_transactions_by_station(db: Session, station_id: str) -> list[Transaction]:
    return (
        db.query(Transaction)
        .filter(Transaction.station_id == station_id)
        .order_by(Transaction.created_at.desc())
        .all()
    )


def get_transactions_by_cashier(db: Session, cashier: str) -> list[Transaction]:
    return (
        db.query(Transaction)
        .filter(Transaction.cashier.ilike(f"%{cashier}%"))
        .order_by(Transaction.created_at.desc())
        .all()
    )


def get_transactions_by_type(db: Session, transaction_type: str) -> list[Transaction]:
    return (
        db.query(Transaction)
        .filter(Transaction.transaction_type == transaction_type)
        .order_by(Transaction.created_at.desc())
        .all()
    )


def get_recent_transactions(db: Session, limit: int = 20) -> list[Transaction]:
    return (
        db.query(Transaction).order_by(Transaction.created_at.desc()).limit(limit).all()
    )
