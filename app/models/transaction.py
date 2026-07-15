from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)

    transaction_id = Column(String(100), unique=True, nullable=False, index=True)
    shift_id = Column(Integer, ForeignKey("shifts.id"), nullable=False)
    station_id = Column(String(50), nullable=False)
    pump_no = Column(Integer, nullable=False)

    cashier = Column(String(100), nullable=False)

    fuel_type = Column(String(50), nullable=False)

    quantity = Column(Float, nullable=False)

    amount = Column(Numeric(12, 2), nullable=False)

    payment_method = Column(String(50), nullable=False)

    transaction_type = Column(String(50), nullable=False)

    status = Column(String(50), nullable=False, default="completed")

    currency = Column(String(10), default="USD")

    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    shift = relationship("Shift", back_populates="transactions")

    refunds = relationship(
        "Refund", back_populates="transaction", cascade="all, delete-orphan"
    )
