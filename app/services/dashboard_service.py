from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.alert import Alert
from app.models.refund import Refund
from app.models.shift import Shift
from app.models.transaction import Transaction


def get_dashboard_metrics(db: Session) -> dict:

    # =========================
    # KPI Metrics
    # =========================

    total_transactions = db.query(Transaction).count()

    total_sales = round(
        float(db.query(func.sum(Transaction.amount)).scalar() or 0), 2
    )

    average_transaction = round(
        float(db.query(func.avg(Transaction.amount)).scalar() or 0), 2
    )

    average_refund = round(
        float(db.query(func.avg(Refund.amount)).scalar() or 0), 2
    )

    average_cash_variance = round(
        float(db.query(func.avg(Shift.cash_variance)).scalar() or 0), 2
    )

    high_value_transactions = (
        db.query(Transaction)
        .filter(Transaction.amount >= 180)
        .count()
    )

    large_refunds = (
        db.query(Refund)
        .filter(Refund.amount >= 90)
        .count()
    )

    cash_shortages = (
        db.query(Alert)
        .filter(Alert.alert_type == "cash_shortage")
        .count()
    )

    total_alerts = db.query(Alert).count()

    # =========================
    # Recent Tables
    # =========================

    recent_transactions = (
        db.query(Transaction)
        .order_by(Transaction.id.desc())
        .limit(5)
        .all()
    )

    recent_alerts = (
        db.query(Alert)
        .order_by(Alert.id.desc())
        .limit(5)
        .all()
    )

    # =========================
    # Revenue Chart
    # =========================

    sales_chart = (
        db.query(
            func.date(Transaction.created_at).label("day"),
            func.sum(Transaction.amount).label("sales")
        )
        .group_by(func.date(Transaction.created_at))
        .order_by(func.date(Transaction.created_at))
        .all()
    )

    revenue_labels = [
        str(row.day) for row in sales_chart
    ]

    revenue_values = [
        float(row.sales) for row in sales_chart
    ]

    # =========================
    # Alert Severity Chart
    # =========================

    severity_chart = (
        db.query(
            Alert.severity,
            func.count(Alert.id)
        )
        .group_by(Alert.severity)
        .all()
    )

    alert_labels = [
        row[0] for row in severity_chart
    ]

    alert_values = [
        row[1] for row in severity_chart
    ]

    # =========================
    # Return
    # =========================

    return {
    "total_transactions": total_transactions,
    "total_sales": total_sales,
    "average_transaction": average_transaction,
    "average_refund": average_refund,
    "average_cash_variance": average_cash_variance,
    "cash_shortages": cash_shortages,
    "high_value_transactions": high_value_transactions,
    "large_refunds": large_refunds,
    "alerts": total_alerts,
    "recent_transactions": recent_transactions,
    "recent_alerts": recent_alerts,

    # Charts
    "revenue_labels": revenue_labels,
    "revenue_values": revenue_values,
    "alert_labels": alert_labels,
    "alert_values": alert_values,
}