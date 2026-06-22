from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import relationship
from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    knowledge_level = Column(String(50), default="debutant", nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    chat_histories = relationship("ChatHistory", back_populates="user", cascade="all, delete-orphan")
    simulation_results = relationship("SimulationResult", back_populates="user", cascade="all, delete-orphan")
    monitoring_events = relationship("MonitoringEvent", back_populates="user", cascade="all, delete-orphan")