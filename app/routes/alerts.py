from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.alert import Alert
from app.services.alert_service import (
    get_alert_severity_summary,
    get_alert_summary,
    get_alert_type_summary,
    get_alerts_by_severity,
    get_alerts_by_type,
    get_all_alerts,
    get_top_ml_alerts,
)

router = APIRouter(prefix="/alerts", tags=["alerts"])


def serialize_alert(alert: Alert) -> dict:
    return {
        "id": alert.id,
        "transaction_id": alert.transaction_id,
        "shift_id": alert.shift_id,
        "alert_type": alert.alert_type,
        "severity": alert.severity,
        "score": round(float(alert.score), 2),
        "ml_score": round(float(alert.ml_score), 3) if alert.ml_score is not None else None,
        "reason": alert.reason,
        "status": alert.status,
        "created_at": alert.created_at.isoformat() if alert.created_at else None,
    }


@router.get("/")
@router.get("")
def list_alerts(db: Session = Depends(get_db)):
    alerts = get_all_alerts(db)
    return [serialize_alert(alert) for alert in alerts]


@router.get("/low")
def low_alerts(db: Session = Depends(get_db)):
    alerts = get_alerts_by_severity(db, "low")
    return [serialize_alert(alert) for alert in alerts]


@router.get("/medium")
def medium_alerts(db: Session = Depends(get_db)):
    alerts = get_alerts_by_severity(db, "medium")
    return [serialize_alert(alert) for alert in alerts]


@router.get("/high")
def high_alerts(db: Session = Depends(get_db)):
    alerts = get_alerts_by_severity(db, "high")
    return [serialize_alert(alert) for alert in alerts]


@router.get("/critical")
def critical_alerts(db: Session = Depends(get_db)):
    alerts = get_alerts_by_severity(db, "critical")
    return [serialize_alert(alert) for alert in alerts]


@router.get("/types")
def alert_types(db: Session = Depends(get_db)):
    return get_alert_type_summary(db)


@router.get("/type/{alert_type}")
def alerts_by_type(alert_type: str, db: Session = Depends(get_db)):
    alerts = get_alerts_by_type(db, alert_type)
    return [serialize_alert(alert) for alert in alerts]


@router.get("/ml-top")
def top_ml_alerts(limit: int = 20, db: Session = Depends(get_db)):
    alerts = get_top_ml_alerts(db, limit=limit)
    return [serialize_alert(alert) for alert in alerts]


@router.get("/severity")
def alert_severity_summary(db: Session = Depends(get_db)):
    return get_alert_severity_summary(db)


@router.get("/severity/{severity}")
def alerts_by_severity(severity: str, db: Session = Depends(get_db)):
    alerts = get_alerts_by_severity(db, severity)
    return [serialize_alert(alert) for alert in alerts]


@router.get("/summary")
def alert_summary(db: Session = Depends(get_db)):
    return get_alert_summary(db)
