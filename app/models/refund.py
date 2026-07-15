from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.database import Base


class Refund(Base):
    __tablename__ = "refunds"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=False)
    refund_id = Column(String(100), unique=True, nullable=False, index=True)
    amount = Column(Numeric(12, 2), nullable=False)
    reason = Column(String(255), nullable=True)
    status = Column(String(50), nullable=False, default="requested")
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    transaction = relationship("Transaction", back_populates="refunds")
