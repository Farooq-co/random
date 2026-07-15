from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.services.analytics_service import (
    get_cash_variance_summary,
    get_cashier_performance,
    get_fuel_type_summary,
    get_hourly_sales,
    get_payment_method_summary,
    get_refunds_by_day,
    get_sales_by_day,
    get_shrinkage_summary,
    get_top_stations,
)

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/sales-by-day")
def sales_by_day(db: Session = Depends(get_db)):
    return get_sales_by_day(db)


@router.get("/hourly-sales")
def hourly_sales(db: Session = Depends(get_db)):
    return get_hourly_sales(db)


@router.get("/refunds-by-day")
def refunds_by_day(db: Session = Depends(get_db)):
    return get_refunds_by_day(db)


@router.get("/cashier-performance")
def cashier_performance(db: Session = Depends(get_db)):
    return get_cashier_performance(db)


@router.get("/top-stations")
def top_stations(db: Session = Depends(get_db)):
    return get_top_stations(db)


@router.get("/shrinkage")
def shrinkage(db: Session = Depends(get_db)):
    return get_shrinkage_summary(db)


@router.get("/payment-methods")
def payment_methods(db: Session = Depends(get_db)):
    return get_payment_method_summary(db)


@router.get("/fuel-types")
def fuel_types(db: Session = Depends(get_db)):
    return get_fuel_type_summary(db)


@router.get("/cash-variance")
def cash_variance(db: Session = Depends(get_db)):
    return get_cash_variance_summary(db)
