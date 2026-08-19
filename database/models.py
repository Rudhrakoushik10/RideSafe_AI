import os
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///ridesafe.db")

if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True, index=True)
    plate_number = Column(String(20), unique=True, index=True)
    vehicle_type = Column(String(50), default="two_wheeler")
    created_at = Column(DateTime, default=datetime.utcnow)

    violations = relationship("Violation", back_populates="vehicle")


class Violation(Base):
    __tablename__ = "violations"

    id = Column(Integer, primary_key=True, index=True)
    violation_id = Column(String(50), unique=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=True)
    violation_type = Column(String(50), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    location = Column(String(200), nullable=True)
    confidence = Column(Float, default=0.0)
    fine_amount = Column(Integer, default=0)
    status = Column(String(20), default="pending")
    plate_number = Column(String(20), nullable=True)
    track_id = Column(Integer, nullable=True)
    camera_id = Column(String(50), nullable=True)

    vehicle = relationship("Vehicle", back_populates="violations")
    evidence_items = relationship("Evidence", back_populates="violation")


class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(Integer, primary_key=True, index=True)
    violation_id = Column(Integer, ForeignKey("violations.id"), nullable=False)
    image_path = Column(String(500), nullable=True)
    video_timestamp = Column(String(50), nullable=True)
    full_frame_path = Column(String(500), nullable=True)
    vehicle_crop_path = Column(String(500), nullable=True)
    plate_crop_path = Column(String(500), nullable=True)
    metadata_json = Column(JSON, nullable=True)

    violation = relationship("Violation", back_populates="evidence_items")


class Camera(Base):
    __tablename__ = "cameras"

    id = Column(Integer, primary_key=True, index=True)
    camera_id = Column(String(50), unique=True, index=True)
    name = Column(String(100))
    location = Column(String(200))
    configuration = Column(JSON, default=dict)
    active = Column(Boolean, default=True)


class ViolationRule(Base):
    __tablename__ = "violation_rules"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(50), unique=True, nullable=False)
    fine_amount = Column(Integer, default=1000)
    active = Column(Boolean, default=True)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)


def seed_rules():
    db = SessionLocal()
    try:
        from src.config import load_violation_rules
        rules = load_violation_rules().get("rules", {})
        for rule_type, rule_data in rules.items():
            existing = db.query(ViolationRule).filter(ViolationRule.type == rule_type).first()
            if not existing:
                db.add(ViolationRule(
                    type=rule_type,
                    fine_amount=rule_data.get("fine_amount", 1000),
                    active=rule_data.get("active", True),
                ))
        db.commit()
    finally:
        db.close()
