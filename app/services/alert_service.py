from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.alert import Alert


def get_all_alerts(db: Session) -> list[Alert]:
    return db.query(Alert).order_by(Alert.score.desc(), Alert.created_at.desc()).all()


def get_alerts_by_severity(db: Session, severity: str) -> list[Alert]:
    return (
        db.query(Alert)
        .filter(Alert.severity == severity)
        .order_by(Alert.score.desc(), Alert.created_at.desc())
        .all()
    )


def get_alerts_by_type(db: Session, alert_type: str) -> list[Alert]:
    return (
        db.query(Alert)
        .filter(Alert.alert_type == alert_type)
        .order_by(Alert.score.desc(), Alert.created_at.desc())
        .all()
    )


def get_top_ml_alerts(db: Session, limit: int = 20) -> list[Alert]:
    return (
        db.query(Alert)
        .filter(Alert.alert_type == "ml_isolation_forest")
        .order_by(Alert.score.desc(), Alert.created_at.desc())
        .limit(limit)
        .all()
    )


def get_alert_type_summary(db: Session) -> list[dict]:
    rows = (
        db.query(Alert.alert_type, func.count(Alert.id).label("count"))
        .group_by(Alert.alert_type)
        .order_by(func.count(Alert.id).desc())
        .all()
    )
    return [{"alert_type": row.alert_type, "count": row.count} for row in rows]


def get_alert_severity_summary(db: Session) -> list[dict]:
    rows = (
        db.query(Alert.severity, func.count(Alert.id).label("count"))
        .group_by(Alert.severity)
        .order_by(Alert.severity)
        .all()
    )
    return [{"severity": row.severity, "count": row.count} for row in rows]


def get_alert_summary(db: Session) -> dict:
    return {
        "total": db.query(Alert).count(),
        "high": db.query(Alert).filter(Alert.severity == "high").count(),
        "critical": db.query(Alert).filter(Alert.severity == "critical").count(),
        "medium": db.query(Alert).filter(Alert.severity == "medium").count(),
        "low": db.query(Alert).filter(Alert.severity == "low").count(),
    }
