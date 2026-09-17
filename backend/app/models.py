"""SQLAlchemy models for the multi-institution FuelTrack domain.

All values in this project are synthetic.  Institution and station foreign keys
are deliberately present on every operational entity so that the API can
enforce tenant isolation instead of relying on frontend filtering.
"""
import uuid
from datetime import datetime
from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Numeric, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base


class Institution(Base):
    __tablename__ = "institutions"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    code: Mapped[str] = mapped_column(String(30), unique=True)
    name: Mapped[str] = mapped_column(String(160))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class User(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    institution_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("institutions.id"))
    fixed_station_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("stations.id"))
    full_name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    password_hash: Mapped[str] = mapped_column(Text)
    role: Mapped[str] = mapped_column(Enum("ADMIN", "OPERATOR", "SUPERVISOR", name="user_role", create_type=False), default="OPERATOR")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    institution = relationship("Institution")
    fixed_station = relationship("Station", foreign_keys=[fixed_station_id])


class UserStationAssignment(Base):
    __tablename__ = "user_station_assignments"
    __table_args__ = (UniqueConstraint("user_id", "station_id", name="uq_user_station"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    station_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("stations.id", ondelete="CASCADE"))
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    user = relationship("User")
    station = relationship("Station")


class Station(Base):
    __tablename__ = "stations"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    institution_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("institutions.id"))
    code: Mapped[str] = mapped_column(String(30), unique=True)
    name: Mapped[str] = mapped_column(String(150))
    municipality: Mapped[str] = mapped_column(String(100), default="La Paz")
    address: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    institution = relationship("Institution")


class Vehicle(Base):
    __tablename__ = "vehicles"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    institution_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("institutions.id"))
    plate: Mapped[str] = mapped_column(String(15), unique=True)
    vehicle_type: Mapped[str | None] = mapped_column(String(60))
    internal_code: Mapped[str | None] = mapped_column(String(50))
    b_sisa_code: Mapped[str | None] = mapped_column(String(40))
    synthetic_make_model: Mapped[str | None] = mapped_column(String(100))
    synthetic_year: Mapped[int | None]
    rfid_uid: Mapped[str | None] = mapped_column(String(80), unique=True)
    rfid_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    institution = relationship("Institution")


class FuelType(Base):
    __tablename__ = "fuel_types"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(20), unique=True)
    name: Mapped[str] = mapped_column(String(80))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class StationFuelAuthorization(Base):
    __tablename__ = "station_fuel_authorizations"
    __table_args__ = (UniqueConstraint("station_id", "fuel_type_id", name="uq_station_fuel"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    station_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("stations.id", ondelete="CASCADE"))
    fuel_type_id: Mapped[int] = mapped_column(ForeignKey("fuel_types.id", ondelete="CASCADE"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    station = relationship("Station")
    fuel_type = relationship("FuelType")


class Operation(Base):
    __tablename__ = "fuel_operations"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    institution_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("institutions.id"))
    vehicle_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("vehicles.id"))
    station_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("stations.id"))
    fuel_type_id: Mapped[int] = mapped_column(ForeignKey("fuel_types.id"))
    quantity_liters: Mapped[float] = mapped_column(Numeric(10, 2))
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    registered_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    notes: Mapped[str | None] = mapped_column(String(500))
    vehicle = relationship("Vehicle")
    station = relationship("Station")
    fuel_type = relationship("FuelType")


class TrackingRule(Base):
    __tablename__ = "tracking_rules"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    code: Mapped[str] = mapped_column(String(40), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[str] = mapped_column(Text)
    threshold: Mapped[float] = mapped_column(Numeric(12, 2))
    window_hours: Mapped[int]
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class ReviewCase(Base):
    __tablename__ = "review_cases"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    institution_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("institutions.id"))
    station_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("stations.id"))
    vehicle_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("vehicles.id"))
    operation_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("fuel_operations.id"))
    status: Mapped[str] = mapped_column(Enum("PENDING", "IN_REVIEW", "RESOLVED", "DISMISSED", name="case_status", create_type=False), default="PENDING")
    priority: Mapped[str] = mapped_column(String(15), default="NORMAL")
    assigned_to: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    conclusion: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("NOW()"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("NOW()"))
    vehicle = relationship("Vehicle")
    station = relationship("Station")


class CaseReason(Base):
    __tablename__ = "case_reasons"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    case_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("review_cases.id", ondelete="CASCADE"))
    rule_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("tracking_rules.id"))
    reason: Mapped[str] = mapped_column(Text)
    observed_value: Mapped[float | None] = mapped_column(Numeric(12, 2))
    case = relationship("ReviewCase")


class CaseLog(Base):
    __tablename__ = "case_logs"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    case_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("review_cases.id", ondelete="CASCADE"))
    actor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(40))
    note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("NOW()"))


class Alert(Base):
    __tablename__ = "alerts"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    institution_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("institutions.id"))
    station_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("stations.id"))
    vehicle_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("vehicles.id"))
    operation_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("fuel_operations.id"))
    case_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("review_cases.id"))
    code: Mapped[str] = mapped_column(String(40))
    severity: Mapped[str] = mapped_column(String(15), default="WARNING")
    message: Mapped[str] = mapped_column(Text)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("NOW()"))


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    actor_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    institution_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("institutions.id"))
    action: Mapped[str] = mapped_column(String(80))
    entity_type: Mapped[str] = mapped_column(String(60))
    entity_id: Mapped[str | None] = mapped_column(String(80))
    details: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("NOW()"))
