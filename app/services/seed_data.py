import random
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app.database.database import Base, SessionLocal, engine
from app.models.alert import Alert
from app.models.refund import Refund
from app.models.shift import Shift
from app.models.transaction import Transaction

random.seed(42)
Base.metadata.create_all(bind=engine)


def seed_database(reset: bool = False) -> dict:
    db = SessionLocal()
    try:
        if reset:
            db.query(Alert).delete(synchronize_session=False)
            db.query(Refund).delete(synchronize_session=False)
            db.query(Transaction).delete(synchronize_session=False)
            db.query(Shift).delete(synchronize_session=False)
            db.commit()

        if db.query(Shift).count() and not reset:
            return {
                "message": "Database already contains seed data.",
                "shifts": db.query(Shift).count(),
                "transactions": db.query(Transaction).count(),
                "refunds": db.query(Refund).count(),
                "alerts": db.query(Alert).count(),
            }

        shifts = generate_shifts(db, count=100)
        transactions = generate_transactions(db, shifts=shifts, count=2000)
        refunds = generate_refunds(db, transactions=transactions, count=180)
        alerts = generate_alerts(
            db, shifts=shifts, transactions=transactions, refunds=refunds
        )

        db.commit()
        return {
            "message": "Seed data generated successfully.",
            "shifts": len(shifts),
            "transactions": len(transactions),
            "refunds": len(refunds),
            "alerts": len(alerts),
        }
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def generate_shifts(db, count: int = 100) -> list[Shift]:
    shifts: list[Shift] = []
    base_time = datetime.now(timezone.utc) - timedelta(days=60)

    for index in range(count):
        shift_start = base_time + timedelta(
            days=index // 10, hours=random.randint(0, 23)
        )
        opening_cash = Decimal(str(random.randint(1200, 2500)))
        expected_cash = opening_cash + Decimal(str(random.randint(3200, 7800)))

        cash_variance = Decimal(str(random.randint(-900, 700)))
        actual_cash = expected_cash + cash_variance
        if index % 7 == 0:
            cash_variance = Decimal("-650")
            actual_cash = expected_cash + cash_variance
        elif index % 11 == 0:
            cash_variance = Decimal("550")
            actual_cash = expected_cash + cash_variance

        shift = Shift(
            shift_id=f"SHIFT-{index + 1:03d}",
            cashier=random.choice(
                [
                    "Alicia Brooks",
                    "Marcus Chen",
                    "Nina Patel",
                    "Owen Lewis",
                    "Sofia Rivera",
                    "Derrick Moore",
                    "Maria Gomez",
                    "Jamal Turner",
                ]
            ),
            opening_cash=opening_cash,
            expected_cash=expected_cash,
            actual_cash=actual_cash,
            cash_variance=cash_variance,
            shift_status="review" if abs(cash_variance) >= 400 else "closed",
            created_at=shift_start,
            updated_at=shift_start,
        )
        db.add(shift)
        shifts.append(shift)

    db.commit()
    for shift in shifts:
        db.refresh(shift)
    return shifts


def generate_transactions(
    db, shifts: list[Shift], count: int = 2000
) -> list[Transaction]:
    transactions: list[Transaction] = []
    fuel_types = ["Diesel", "Gasoline", "Premium", "Ethanol"]
    payment_methods = ["Cash", "Card", "Mobile Wallet", "Fleet Card"]
    transaction_types = ["fuel_sale", "fuel_addon", "car_wash", "misc_purchase"]

    for index, shift in enumerate(shifts):
        for offset in range(20):
            transaction_number = (index * 20) + offset + 1
            created_at = shift.created_at + timedelta(minutes=random.randint(20, 780))
            if transaction_number % 37 == 0:
                created_at = created_at.replace(hour=2, minute=15)
            elif transaction_number % 41 == 0:
                created_at = created_at.replace(hour=23, minute=45)

            amount = Decimal(str(round(random.uniform(22, 175), 2)))
            if transaction_number % 23 == 0:
                amount = Decimal(str(round(random.uniform(180, 320), 2)))
            if transaction_number % 59 == 0:
                amount = Decimal(str(round(random.uniform(320, 450), 2)))

            transaction = Transaction(
                transaction_id=f"TXN-{transaction_number:05d}",
                shift_id=shift.id,
                station_id=f"ST{random.randint(1, 6)}",
                pump_no=random.randint(1, 8),
                cashier=shift.cashier,
                fuel_type=random.choice(fuel_types),
                quantity=round(random.uniform(8, 70), 2),
                amount=amount,
                payment_method=random.choice(payment_methods),
                transaction_type=random.choice(transaction_types),
                status="completed",
                currency="USD",
                created_at=created_at,
                updated_at=created_at,
            )
            db.add(transaction)
            transactions.append(transaction)

    db.commit()
    for transaction in transactions:
        db.refresh(transaction)
    return transactions


def generate_refunds(
    db, transactions: list[Transaction], count: int = 180
) -> list[Refund]:
    refunds: list[Refund] = []
    sampled_transactions = random.sample(transactions, k=min(count, len(transactions)))

    for index, transaction in enumerate(sampled_transactions):
        if transaction.amount <= 0:
            continue

        refund_ratio = random.uniform(0.08, 0.35)
        if index % 9 == 0:
            refund_ratio = 0.5
        elif index % 4 == 0:
            refund_ratio = 0.2

        refund_amount = (transaction.amount * Decimal(str(refund_ratio))).quantize(
            Decimal("0.01")
        )
        refund_amount = min(refund_amount, transaction.amount - Decimal("1.00"))
        if refund_amount <= Decimal("0"):
            refund_amount = Decimal("10.00")

        refund = Refund(
            transaction_id=transaction.id,
            refund_id=f"REF-{index + 1:03d}",
            amount=refund_amount,
            reason=random.choice(
                [
                    "Customer dissatisfaction",
                    "Overcharge detected",
                    "Receipt mismatch",
                    "Fuel quality concern",
                    "Pricing discrepancy",
                ]
            ),
            status=random.choice(["approved", "requested", "completed"]),
            created_at=transaction.created_at
            + timedelta(minutes=random.randint(10, 180)),
            updated_at=transaction.created_at
            + timedelta(minutes=random.randint(10, 180)),
        )
        db.add(refund)
        refunds.append(refund)

    db.commit()
    for refund in refunds:
        db.refresh(refund)
    return refunds


def generate_alerts(
    db,
    shifts: list[Shift],
    transactions: list[Transaction],
    refunds: list[Refund],
) -> list[Alert]:
    alerts: list[Alert] = []

    for transaction in transactions:
        if transaction.amount >= Decimal("180"):
            alerts.append(
                Alert(
                    transaction_id=transaction.id,
                    shift_id=transaction.shift_id,
                    alert_type="high_value_transaction",
                    severity="high",
                    score=0.92,
                    reason=f"Transaction {transaction.transaction_id} exceeded the high-value threshold.",
                )
            )

        if transaction.created_at.hour < 6 or transaction.created_at.hour > 22:
            alerts.append(
                Alert(
                    transaction_id=transaction.id,
                    shift_id=transaction.shift_id,
                    alert_type="outside_business_hours",
                    severity="low",
                    score=0.65,
                    reason=f"Transaction {transaction.transaction_id} occurred outside business hours.",
                )
            )

        if transaction.payment_method == "Cash" and transaction.amount >= Decimal(
            "220"
        ):
            alerts.append(
                Alert(
                    transaction_id=transaction.id,
                    shift_id=transaction.shift_id,
                    alert_type="suspicious_cash_transaction",
                    severity="medium",
                    score=0.81,
                    reason=f"Transaction {transaction.transaction_id} used cash for a large amount.",
                )
            )

        if transaction.quantity >= Decimal("55") and transaction.amount >= Decimal(
            "150"
        ):
            alerts.append(
                Alert(
                    transaction_id=transaction.id,
                    shift_id=transaction.shift_id,
                    alert_type="unusual_fuel_quantity",
                    severity="medium",
                    score=0.79,
                    reason=f"Transaction {transaction.transaction_id} had unusually high fuel quantity.",
                )
            )

        if (
            transaction.transaction_type == "misc_purchase"
            and transaction.amount >= Decimal("200")
        ):
            alerts.append(
                Alert(
                    transaction_id=transaction.id,
                    shift_id=transaction.shift_id,
                    alert_type="misc_purchase_spike",
                    severity="medium",
                    score=0.77,
                    reason=f"Transaction {transaction.transaction_id} was a large miscellaneous purchase.",
                )
            )

    for refund in refunds:
        if refund.amount >= Decimal("90"):
            alerts.append(
                Alert(
                    transaction_id=refund.transaction_id,
                    shift_id=refund.transaction.shift_id,
                    alert_type="large_refund",
                    severity="critical" if refund.amount >= Decimal("140") else "high",
                    score=0.95 if refund.amount >= Decimal("140") else 0.88,
                    reason=f"Refund {refund.refund_id} exceeded the large refund threshold.",
                )
            )

        if refund.reason in {
            "Overcharge detected",
            "Pricing discrepancy",
        } and refund.amount >= Decimal("50"):
            alerts.append(
                Alert(
                    transaction_id=refund.transaction_id,
                    shift_id=refund.transaction.shift_id,
                    alert_type="refund_discrepancy",
                    severity="high",
                    score=0.9,
                    reason=f"Refund {refund.refund_id} matches a pricing or overcharge discrepancy.",
                )
            )

        if refund.status == "requested" and refund.amount >= Decimal("80"):
            alerts.append(
                Alert(
                    transaction_id=refund.transaction_id,
                    shift_id=refund.transaction.shift_id,
                    alert_type="pending_large_refund",
                    severity="medium",
                    score=0.8,
                    reason=f"Refund {refund.refund_id} is still pending for a large amount.",
                )
            )

    for shift in shifts:
        if shift.cash_variance < Decimal("-300"):
            alerts.append(
                Alert(
                    shift_id=shift.id,
                    transaction_id=None,
                    alert_type="cash_shortage",
                    severity=(
                        "critical" if shift.cash_variance <= Decimal("-600") else "high"
                    ),
                    score=0.97 if shift.cash_variance <= Decimal("-600") else 0.94,
                    reason=f"Shift {shift.shift_id} shows a cash shortage of {abs(shift.cash_variance)}.",
                )
            )

        if abs(shift.cash_variance) >= Decimal("400"):
            alerts.append(
                Alert(
                    shift_id=shift.id,
                    transaction_id=None,
                    alert_type="excessive_cash_variance",
                    severity=(
                        "high"
                        if abs(shift.cash_variance) >= Decimal("700")
                        else "medium"
                    ),
                    score=0.9 if abs(shift.cash_variance) >= Decimal("700") else 0.83,
                    reason=f"Shift {shift.shift_id} exceeded the cash variance threshold.",
                )
            )

        high_value_count = sum(
            1
            for transaction in transactions
            if transaction.shift_id == shift.id and transaction.amount >= Decimal("180")
        )
        if high_value_count >= 3:
            alerts.append(
                Alert(
                    shift_id=shift.id,
                    transaction_id=None,
                    alert_type="transaction_spike",
                    severity="high",
                    score=0.87,
                    reason=f"Shift {shift.shift_id} had multiple high-value transactions in one shift.",
                )
            )

    db.add_all(alerts)
    db.commit()
    for alert in alerts:
        db.refresh(alert)
    return alerts


if __name__ == "__main__":
    print(seed_database(reset=True))
