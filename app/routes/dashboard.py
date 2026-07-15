from pathlib import Path



from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.services.dashboard_service import get_dashboard_metrics
from fastapi.responses import HTMLResponse


router = APIRouter(prefix="/dashboard", tags=["dashboard"])
TEMPLATES_DIR = Path(__file__).resolve().parents[2] / "templates"
templates = Jinja2Templates(directory=TEMPLATES_DIR)

@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):

    metrics = get_dashboard_metrics(db)

    context = {
        "request": request,
        "title": "Transaction Anomaly & Shrinkage Dashboard",
        **metrics,
        "alert_labels": ["Cash Shortages", "High Value Txns", "Large Refunds"],
        "alert_values": [
            metrics["cash_shortages"],
            metrics["high_value_transactions"],
            metrics["large_refunds"],
        ],
    }

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
            context={
        "request": request,
        "title": "Transaction Anomaly & Shrinkage Dashboard",
        **metrics,
    },
    )