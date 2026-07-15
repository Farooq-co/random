from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.database import Base


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)

    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=True)

    shift_id = Column(Integer, ForeignKey("shifts.id"), nullable=True)

    alert_type = Column(String(100), nullable=False)

    severity = Column(String(20), nullable=False)

    score = Column(Float, nullable=False)
    #ml_score = Column(Float, nullable=True)#

    reason = Column(String(255), nullable=False)

    status = Column(String(50), default="Open")

    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    transaction = relationship("Transaction")
    shift = relationship("Shift")
