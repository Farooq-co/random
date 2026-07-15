from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.transaction import Transaction
from app.services.transaction_service import (
    get_high_value_transactions,
    get_recent_transactions,
    get_transaction_by_id,
    get_transaction_summary,
    get_transactions,
    get_transactions_by_cashier,
    get_transactions_by_fuel_type,
    get_transactions_by_payment_method,
    get_transactions_by_station,
    get_transactions_by_status,
    get_transactions_by_type,
)
from app.services.transaction_service import (
    search_transactions as search_transactions_service,
)

router = APIRouter(prefix="/transactions", tags=["transactions"])


def serialize_transaction(transaction: Transaction) -> dict:
    return {
        "id": transaction.id,
        "transaction_id": transaction.transaction_id,
        "shift_id": transaction.shift_id,
        "station_id": transaction.station_id,
        "pump_no": transaction.pump_no,
        "cashier": transaction.cashier,
        "fuel_type": transaction.fuel_type,
        "quantity": float(transaction.quantity),
        "amount": float(transaction.amount),
        "payment_method": transaction.payment_method,
        "transaction_type": transaction.transaction_type,
        "status": transaction.status,
        "currency": transaction.currency,
        "created_at": (
            transaction.created_at.isoformat() if transaction.created_at else None
        ),
        "updated_at": (
            transaction.updated_at.isoformat() if transaction.updated_at else None
        ),
    }


@router.get("/")
def list_transactions(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> list[dict]:
    transactions = get_transactions(db, skip=skip, limit=limit)
    return [serialize_transaction(transaction) for transaction in transactions]


@router.get("/high-value")
def high_value_transactions(db: Session = Depends(get_db)) -> list[dict]:
    transactions = get_high_value_transactions(db)
    return [serialize_transaction(transaction) for transaction in transactions]


@router.get("/payment-method/{payment_method}")
def transactions_by_payment_method(
    payment_method: str, db: Session = Depends(get_db)
) -> list[dict]:
    transactions = get_transactions_by_payment_method(db, payment_method)
    return [serialize_transaction(transaction) for transaction in transactions]


@router.get("/fuel-type/{fuel_type}")
def transactions_by_fuel_type(
    fuel_type: str, db: Session = Depends(get_db)
) -> list[dict]:
    transactions = get_transactions_by_fuel_type(db, fuel_type)
    return [serialize_transaction(transaction) for transaction in transactions]


@router.get("/summary")
def transaction_summary(db: Session = Depends(get_db)) -> dict:
    return get_transaction_summary(db)


@router.get("/search")
def search_transactions(
    station_id: str | None = Query(default=None),
    cashier: str | None = Query(default=None),
    fuel_type: str | None = Query(default=None),
    payment_method: str | None = Query(default=None),
    transaction_type: str | None = Query(default=None),
    status: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[dict]:
    transactions = search_transactions_service(
        db,
        station_id=station_id,
        cashier=cashier,
        fuel_type=fuel_type,
        payment_method=payment_method,
        transaction_type=transaction_type,
        status=status,
    )
    return [serialize_transaction(transaction) for transaction in transactions]


@router.get("/by-station/{station_id}")
def transactions_by_station(
    station_id: str, db: Session = Depends(get_db)
) -> list[dict]:
    transactions = get_transactions_by_station(db, station_id)
    return [serialize_transaction(transaction) for transaction in transactions]


@router.get("/by-cashier/{cashier}")
def transactions_by_cashier(cashier: str, db: Session = Depends(get_db)) -> list[dict]:
    transactions = get_transactions_by_cashier(db, cashier)
    return [serialize_transaction(transaction) for transaction in transactions]


@router.get("/by-type/{transaction_type}")
def transactions_by_type(
    transaction_type: str, db: Session = Depends(get_db)
) -> list[dict]:
    transactions = get_transactions_by_type(db, transaction_type)
    return [serialize_transaction(transaction) for transaction in transactions]


@router.get("/recent")
def recent_transactions(
    limit: int = Query(default=20, ge=1, le=100), db: Session = Depends(get_db)
) -> list[dict]:
    transactions = get_recent_transactions(db, limit=limit)
    return [serialize_transaction(transaction) for transaction in transactions]


@router.get("/status/{status}")
def transactions_by_status(status: str, db: Session = Depends(get_db)) -> list[dict]:
    transactions = get_transactions_by_status(db, status)
    return [serialize_transaction(transaction) for transaction in transactions]


@router.get("/{transaction_id}")
def get_transaction(transaction_id: int, db: Session = Depends(get_db)) -> dict:
    transaction = get_transaction_by_id(db, transaction_id)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return serialize_transaction(transaction)
