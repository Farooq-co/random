from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.database import Base


class Shift(Base):
    __tablename__ = "shifts"

    id = Column(Integer, primary_key=True, index=True)

    shift_id = Column(String(100), unique=True, nullable=False, index=True)

    cashier = Column(String(100), nullable=False)

    opening_cash = Column(Numeric(12, 2), nullable=False)

    expected_cash = Column(Numeric(12, 2), nullable=False)

    actual_cash = Column(Numeric(12, 2), nullable=False)

    cash_variance = Column(Numeric(12, 2), nullable=False)

    shift_status = Column(String(50), default="closed")

    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    transactions = relationship("Transaction", back_populates="shift")
