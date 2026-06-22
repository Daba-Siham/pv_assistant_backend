from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.db.base import Base


class SimulationResult(Base):
    __tablename__ = "simulation_results"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    simulation_type = Column(String(50), nullable=False, default="dimensioning")

    city = Column(String(100), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    daily_consumption_kwh = Column(Float, nullable=True)
    available_area_m2 = Column(Float, nullable=True)
    budget = Column(Float, nullable=True)
    autonomy_days = Column(Float, nullable=True)
    installation_type = Column(String(50), nullable=True)

    orientation = Column(String(50), nullable=True)
    tilt_angle = Column(Float, nullable=True)
    shade_factor = Column(Float, nullable=True)
    roof_type = Column(String(100), nullable=True)
    distance_to_load_m = Column(Float, nullable=True)

    ghi = Column(Float, nullable=True)
    dni = Column(Float, nullable=True)
    temperature_avg = Column(Float, nullable=True)
    peak_sun_hours = Column(Float, nullable=True)

    panel_count = Column(Integer, nullable=True)
    panel_power_w = Column(Float, nullable=True)
    total_power_kwp = Column(Float, nullable=True)
    estimated_daily_production_kwh = Column(Float, nullable=True)
    required_area_m2 = Column(Float, nullable=True)

    battery_capacity_kwh = Column(Float, nullable=True)
    battery_capacity_ah = Column(Float, nullable=True)
    battery_needed = Column(String(20), nullable=True)

    inverter_power_kw = Column(Float, nullable=True)

    total_cost = Column(Float, nullable=True)
    annual_saving = Column(Float, nullable=True)
    roi_years = Column(Float, nullable=True)

    cable_section_mm2 = Column(Float, nullable=True)

    input_data = Column(JSONB, nullable=True)
    solar_data = Column(JSONB, nullable=True)
    panels_result = Column(JSONB, nullable=True)
    battery_result = Column(JSONB, nullable=True)
    inverter_result = Column(JSONB, nullable=True)
    cost_result = Column(JSONB, nullable=True)
    roi_result = Column(JSONB, nullable=True)
    cable_result = Column(JSONB, nullable=True)
    stores_result = Column(JSONB, nullable=True)
    recommendations = Column(JSONB, nullable=True)
    assumptions = Column(JSONB, nullable=True)

    status = Column(String(50), default="completed", nullable=False)
    error_message = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="simulation_results")

    monitoring_events = relationship(
        "MonitoringEvent",
        back_populates="simulation",
        cascade="all, delete-orphan"
    )