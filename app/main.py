from fastapi import FastAPI
from pathlib import Path


from fastapi.staticfiles import StaticFiles

from app.database.database import Base, engine
from app.models.alert import Alert
from app.models.refund import Refund
from app.models.shift import Shift
from fastapi import Request
from fastapi.responses import RedirectResponse
# Import all models so SQLAlchemy knows about them
from app.models.transaction import Transaction
from app.routes import alerts, analytics, dashboard, transactions

# Create all database tables
Base.metadata.create_all(bind=engine)

ROOT_DIR = Path(__file__).resolve().parent.parent

app = FastAPI(title="Transaction Anomaly & Shrinkage Detection", version="1.0.0")

app.mount("/static", StaticFiles(directory=ROOT_DIR / "static"), name="static")

app.include_router(transactions.router)
app.include_router(alerts.router)
app.include_router(dashboard.router)
app.include_router(analytics.router)


@app.get("/")
async def root():
    return RedirectResponse(url="/dashboard/")
