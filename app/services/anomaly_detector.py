from __future__ import annotations

import numpy as np
import statistics
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List

from sklearn.ensemble import IsolationForest
from sqlalchemy.orm import Session

from app.models.transaction import Transaction
from app.models.alert import Alert


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

@dataclass
class DetectorConfig:
    # High amount anomaly
    min_sample_size: int = 10          # need this many past txns before stats are trusted
    std_dev_multiplier: float = 3.0    # amount > mean + (multiplier * std) => anomaly
    lookback_days: int = 30            # how far back to build the baseline

    # Cashier behavior anomaly
    rate_window_hours: int = 1
    rate_spike_multiplier: float = 3.0     # today's hourly rate vs cashier's own historical avg
    refund_rate_threshold: float = 0.15    # 15% of a cashier's txns being refunds is suspicious

    # Shrinkage detection
    shrinkage_tolerance_pct: float = 0.05  # 5% variance between expected and recorded is normal

    # Time-based anomaly
    quiet_hours_start: int = 23  # 11 PM
    quiet_hours_end: int = 5     # 5 AM
    quiet_hour_amount_threshold: float = 100.0  # flag quiet-hour txns above this amount

    # No-sale gap anomaly
    max_transaction_gap_minutes: float = 30.0  # alert if gap between transactions exceeds this

    # Price per liter fallback, keyed by fuel_type (used only if you don't
    # already have a pricing source). Update these to your real prices.
    expected_price_per_liter: dict = field(default_factory=lambda: {
        "Petrol": 2.0,
        "Diesel": 1.9,
    })

    # ML-based anomaly detection
    ml_contamination: float = 0.05
    ml_n_estimators: int = 100
    ml_max_samples: str = "auto"
    ml_critical_threshold: float = -0.4
    ml_high_threshold: float = -0.2


CONFIG = DetectorConfig()


# ---------------------------------------------------------------------------
# Result object
# ---------------------------------------------------------------------------

@dataclass
class AnomalyResult:
    triggered: bool
    alert_type: str
    severity: str          # "low" | "medium" | "high"
    message: str
    score: float | None = None
    ml_score: float | None = None


def calculate_alert_score(severity: str) -> float:
    return {
        "low": 0.25,
        "medium": 0.6,
        "high": 0.9,
        "critical": 1.0,
    }.get(severity, 0.5)


# ---------------------------------------------------------------------------
# 1. High Amount Anomaly (statistical, not fixed threshold)
# ---------------------------------------------------------------------------

def detect_high_amount_anomaly(db: Session, txn: Transaction) -> AnomalyResult:
    """
    Compares txn.amount against the mean + N*std of recent transactions
    for the same fuel_type, instead of a hardcoded cutoff like amount >= 180.
    """
    cutoff = datetime.utcnow() - timedelta(days=CONFIG.lookback_days)

    baseline = (
        db.query(Transaction.amount)
        .filter(
            Transaction.fuel_type == txn.fuel_type,
            Transaction.created_at >= cutoff,
            Transaction.id != txn.id,
        )
        .all()
    )
    amounts = [float(row[0]) for row in baseline if row[0] is not None]

    if len(amounts) < CONFIG.min_sample_size:
        return AnomalyResult(False, "high_amount", "low", "Not enough history to evaluate.")

    mean = statistics.mean(amounts)
    std = statistics.pstdev(amounts) or 1.0  # avoid divide-by-zero-like flatness
    threshold = mean + (CONFIG.std_dev_multiplier * std)
    txn_amount = float(txn.amount)

    if txn_amount > threshold:
        deviation = txn_amount - threshold
        return AnomalyResult(
            True,
            "high_amount",
            "critical" if txn_amount > threshold * 2 else "high" if txn_amount > threshold * 1.5 else "medium",
            f"High amount anomaly: the transaction amount of {txn.amount:.2f} is {deviation:.2f} above the expected threshold of {threshold:.2f} for fuel type {txn.fuel_type}.",
        )

    return AnomalyResult(False, "high_amount", "low", "Within normal range.")


# ---------------------------------------------------------------------------
# 2. Cashier Behavior Detection
# ---------------------------------------------------------------------------

def detect_cashier_behavior_anomaly(db: Session, txn: Transaction) -> List[AnomalyResult]:
    results: List[AnomalyResult] = []
    if not txn.cashier:
        return results

    now = datetime.utcnow()
    window_start = now - timedelta(hours=CONFIG.rate_window_hours)
    lookback_start = now - timedelta(days=CONFIG.lookback_days)

    # --- Rate spike check ---
    recent_count = (
        db.query(Transaction)
        .filter(
            Transaction.cashier == txn.cashier,
            Transaction.created_at >= window_start,
            Transaction.id != txn.id,
        )
        .count()
    )

    historical_total = (
        db.query(Transaction)
        .filter(
            Transaction.cashier == txn.cashier,
            Transaction.created_at >= lookback_start,
            Transaction.created_at < window_start,
            Transaction.id != txn.id,
        )
        .count()
    )
    historical_hours = max((window_start - lookback_start).total_seconds() / 3600, 1)
    historical_avg_per_window = (historical_total / historical_hours) * CONFIG.rate_window_hours

    if historical_avg_per_window >= 1 and recent_count > historical_avg_per_window * CONFIG.rate_spike_multiplier:
        spike_factor = recent_count / historical_avg_per_window
        results.append(AnomalyResult(
            True,
            "cashier_rate_spike",
            "medium",
            f"Cashier anomaly: {txn.cashier} processed {recent_count} transactions in the last {CONFIG.rate_window_hours}h, "
            f"which is {spike_factor:.1f}x the normal rate of {historical_avg_per_window:.1f} transactions.",
        ))

    # --- Refund rate check ---
    total_txns = (
        db.query(Transaction)
        .filter(
            Transaction.cashier == txn.cashier,
            Transaction.created_at >= lookback_start,
            Transaction.id != txn.id,
        )
        .count()
    )
    refund_txns = (
        db.query(Transaction)
        .filter(
            Transaction.cashier == txn.cashier,
            Transaction.created_at >= lookback_start,
            Transaction.transaction_type.ilike("refund"),
            Transaction.id != txn.id,
        )
        .count()
    )

    if total_txns >= CONFIG.min_sample_size:
        refund_rate = refund_txns / total_txns
        if refund_rate > CONFIG.refund_rate_threshold:
            results.append(AnomalyResult(
                True,
                "cashier_refund_rate",
                "medium",
                f"Cashier anomaly: {txn.cashier} has a refund rate of {refund_rate:.1%}, "
                f"which exceeds the normal threshold of {CONFIG.refund_rate_threshold:.0%}.",
            ))

    return results


# ---------------------------------------------------------------------------
# 3. Pump / Fuel Shrinkage Detection
# ---------------------------------------------------------------------------

def detect_shrinkage_anomaly(txn: Transaction) -> AnomalyResult:
    """
    Compares recorded amount against expected amount (quantity * price/liter).
    Only runs for sale-type transactions with a known fuel_type price.
    """
    if not txn.quantity or not txn.fuel_type or not txn.amount:
        return AnomalyResult(False, "shrinkage", "low", "Missing quantity/fuel_type/amount, skipped.")

    if txn.transaction_type and "sale" not in txn.transaction_type.lower():
        return AnomalyResult(False, "shrinkage", "low", "Non-sale transaction, skipped.")

    price = CONFIG.expected_price_per_liter.get(txn.fuel_type)
    if price is None:
        return AnomalyResult(False, "shrinkage", "low", f"No reference price for {txn.fuel_type}, skipped.")

    expected_amount = float(txn.quantity) * float(price)
    if expected_amount == 0:
        return AnomalyResult(False, "shrinkage", "low", "Expected amount is zero, skipped.")

    variance_pct = (expected_amount - float(txn.amount)) / expected_amount

    if variance_pct > CONFIG.shrinkage_tolerance_pct:
        return AnomalyResult(
            True,
            "shrinkage",
            "critical" if variance_pct > 0.25 else "high" if variance_pct > 0.15 else "medium",
            f"Pump {txn.pump_no}: expected ~{expected_amount:.2f} for "
            f"{txn.quantity}L of {txn.fuel_type}, but only {float(txn.amount):.2f} was recorded "
            f"({variance_pct:.1%} shortfall).",
        )

    return AnomalyResult(False, "shrinkage", "low", "Within tolerance.")


# ---------------------------------------------------------------------------
# 4. Time-Based Anomaly
# ---------------------------------------------------------------------------

def detect_time_based_anomaly(txn: Transaction) -> AnomalyResult:
    if not txn.created_at:
        return AnomalyResult(False, "time_based", "low", "No timestamp available.")

    hour = txn.created_at.hour
    in_quiet_hours = (
        hour >= CONFIG.quiet_hours_start or hour < CONFIG.quiet_hours_end
    )

    if in_quiet_hours and txn.amount >= CONFIG.quiet_hour_amount_threshold:
        return AnomalyResult(
            True,
            "time_based",
            "medium",
            f"Time-based anomaly: transaction of {txn.amount:.2f} occurred at {txn.created_at.strftime('%H:%M')} during quiet hours "
            f"({CONFIG.quiet_hours_start}:00–{CONFIG.quiet_hours_end}:00) and exceeded the threshold of {CONFIG.quiet_hour_amount_threshold:.2f}.",
        )

    return AnomalyResult(False, "time_based", "low", "Normal hours.")


def detect_ml_anomaly(db: Session, txn: Transaction) -> AnomalyResult:
    if txn.amount is None or txn.quantity is None or txn.pump_no is None:
        return AnomalyResult(False, "ml_isolation_forest", "low", "Missing regression features, skipped.")

    cutoff = datetime.utcnow() - timedelta(days=CONFIG.lookback_days)
    rows = (
        db.query(Transaction.amount, Transaction.quantity, Transaction.pump_no)
        .filter(
            Transaction.created_at >= cutoff,
            Transaction.id != txn.id,
            Transaction.amount.isnot(None),
            Transaction.quantity.isnot(None),
            Transaction.pump_no.isnot(None),
        )
        .all()
    )

    if len(rows) < CONFIG.min_sample_size:
        return AnomalyResult(False, "ml_isolation_forest", "low", "Not enough history to evaluate.")

    X = np.array([[float(amount), float(quantity), float(pump_no)] for amount, quantity, pump_no in rows])
    if X.shape[0] < CONFIG.min_sample_size:
        return AnomalyResult(False, "ml_isolation_forest", "low", "Not enough valid history to evaluate.")

    model = IsolationForest(
        n_estimators=CONFIG.ml_n_estimators,
        contamination=CONFIG.ml_contamination,
        max_samples=CONFIG.ml_max_samples,
        random_state=42,
    )
    model.fit(X)

    x_txn = np.array([[float(txn.amount), float(txn.quantity), float(txn.pump_no)]])
    pred = model.predict(x_txn)[0]
    score = float(model.decision_function(x_txn)[0])

    if pred == -1:
        severity = (
            "critical"
            if score <= CONFIG.ml_critical_threshold
            else "high"
            if score <= CONFIG.ml_high_threshold
            else "medium"
        )
        rank = max(calculate_alert_score(severity), -score)
        return AnomalyResult(
            True,
            "ml_isolation_forest",
            severity,
            f"ML anomaly: IsolationForest marked this transaction as an outlier with decision score {score:.3f}.",
            score=rank,
            ml_score=score,
        )

    return AnomalyResult(False, "ml_isolation_forest", "low", "Within ML normal range.")

# ---------------------------------------------------------------------------
# 5. No-Sale Gap Detection
# ---------------------------------------------------------------------------

def detect_no_sale_gaps(db: Session, txn: Transaction) -> AnomalyResult:
    """
    Detect unusually long periods with no sales for the same pump
    during the same shift.

    Business Logic:
    - Compare only transactions from the SAME shift.
    - Compare only transactions from the SAME pump.
    - Ignore first transaction of a shift.
    - Raise an alert if the gap exceeds the configured threshold.
    """

    # Validate required fields
    if txn.created_at is None:
        return AnomalyResult(
            False,
            "no_sale_gap",
            "low",
            "Transaction timestamp unavailable."
        )

    if getattr(txn, "shift_id", None) is None:
        return AnomalyResult(
            False,
            "no_sale_gap",
            "low",
            "Shift information unavailable."
        )

    if getattr(txn, "pump_no", None) is None:
        return AnomalyResult(
            False,
            "no_sale_gap",
            "low",
            "Pump information unavailable."
        )

    # Find the previous transaction for the same pump within the same shift
    previous_txn = (
        db.query(Transaction)
        .filter(
            Transaction.shift_id == txn.shift_id,
            Transaction.pump_no == txn.pump_no,
            Transaction.created_at < txn.created_at,
        )
        .order_by(Transaction.created_at.desc())
        .first()
    )

    # First transaction of the shift for this pump
    if previous_txn is None:
        return AnomalyResult(
            False,
            "no_sale_gap",
            "low",
            "First transaction for this pump in the shift."
        )

    # Calculate gap
    gap = txn.created_at - previous_txn.created_at
    gap_minutes = gap.total_seconds() / 60

    threshold = CONFIG.max_transaction_gap_minutes

    if gap_minutes <= threshold:
        return AnomalyResult(
            False,
            "no_sale_gap",
            "low",
            f"Gap of {gap_minutes:.1f} minutes is within the normal threshold of {threshold:.1f} minutes."
        )

    # Determine severity
    if gap_minutes >= threshold * 4:
        severity = "critical"
    elif gap_minutes >= threshold * 2:
        severity = "high"
    else:
        severity = "medium"

    return AnomalyResult(
        True,
        "no_sale_gap",
        severity,
        (
            f"No sales recorded on Pump {txn.pump_no} for "
            f"{gap_minutes:.0f} minutes during Shift {txn.shift_id}. "
            f"Previous sale at "
            f"{previous_txn.created_at.strftime('%H:%M')}, "
            f"current sale at "
            f"{txn.created_at.strftime('%H:%M')}."
        ),
    )
# ---------------------------------------------------------------------------
# Master runner: runs all detectors and persists Alert rows
# ---------------------------------------------------------------------------

def run_anomaly_checks(db: Session, txn: Transaction) -> List[Alert]:
    """
    Runs all detection rules against a single transaction and creates
    Alert records for anything triggered. Returns the list of created
    Alert objects (empty list if nothing was flagged).
    """
    results: List[AnomalyResult] = []

    results.append(detect_high_amount_anomaly(db, txn))
    results.extend(detect_cashier_behavior_anomaly(db, txn))
    results.append(detect_shrinkage_anomaly(txn))
    results.append(detect_time_based_anomaly(txn))
    results.append(detect_no_sale_gaps(db, txn))
    results.append(detect_ml_anomaly(db, txn))

    created_alerts: List[Alert] = []

    for result in results:
        if not result.triggered:
            continue

        alert = Alert(
            transaction_id=txn.id,
            shift_id=getattr(txn, "shift_id", None),
            alert_type=result.alert_type,
            severity=result.severity,
            score=result.score if result.score is not None else calculate_alert_score(result.severity),
            ml_score=result.ml_score,
            reason=result.message,
            status="Open",
            created_at=datetime.utcnow(),
        )
        db.add(alert)
        created_alerts.append(alert)

    if created_alerts:
        for alert in created_alerts:
            db.refresh(alert)

    return created_alerts
