from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.db.base import Base


class MonitoringEvent(Base):
    __tablename__ = "monitoring_events"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    simulation_id = Column(Integer, ForeignKey("simulation_results.id", ondelete="CASCADE"), nullable=True, index=True)

    event_type = Column(String(50), nullable=False, default="data_point")

    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    production_kwh = Column(Float, nullable=True)
    consumption_kwh = Column(Float, nullable=True)
    battery_level_percent = Column(Float, nullable=True)
    temperature = Column(Float, nullable=True)

    system_status = Column(String(50), default="normal", nullable=False)

    alert_type = Column(String(100), nullable=True)
    severity = Column(String(50), nullable=True)
    message = Column(Text, nullable=True)
    probable_cause = Column(Text, nullable=True)
    recommended_action = Column(Text, nullable=True)

    raw_data = Column(JSONB, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="monitoring_events")
    simulation = relationship("SimulationResult", back_populates="monitoring_events")