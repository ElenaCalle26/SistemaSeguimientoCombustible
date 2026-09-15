import uuid
from datetime import datetime
from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Numeric, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base

class User(Base):
    __tablename__ = 'users'
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    full_name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    password_hash: Mapped[str] = mapped_column(Text)
    role: Mapped[str] = mapped_column(Enum('ADMIN', 'OPERATOR', 'SUPERVISOR', name='user_role', create_type=False), default='OPERATOR')
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

class Station(Base):
    __tablename__ = 'stations'
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    code: Mapped[str] = mapped_column(String(30), unique=True)
    name: Mapped[str] = mapped_column(String(150))
    municipality: Mapped[str] = mapped_column(String(100), default='La Paz')
    address: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

class Vehicle(Base):
    __tablename__ = 'vehicles'
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    plate: Mapped[str] = mapped_column(String(15), unique=True)
    vehicle_type: Mapped[str | None] = mapped_column(String(60))
    internal_code: Mapped[str | None] = mapped_column(String(50))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

class FuelType(Base):
    __tablename__ = 'fuel_types'
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(20), unique=True)
    name: Mapped[str] = mapped_column(String(80))

class Operation(Base):
    __tablename__ = 'fuel_operations'
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    vehicle_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('vehicles.id'))
    station_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('stations.id'))
    fuel_type_id: Mapped[int] = mapped_column(ForeignKey('fuel_types.id'))
    quantity_liters: Mapped[float] = mapped_column(Numeric(10, 2))
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    registered_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey('users.id'))
    notes: Mapped[str | None] = mapped_column(String(500))
    vehicle = relationship('Vehicle')
    station = relationship('Station')
    fuel_type = relationship('FuelType')

class ReviewCase(Base):
    __tablename__ = 'review_cases'
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    vehicle_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('vehicles.id'))
    operation_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey('fuel_operations.id'))
    status: Mapped[str] = mapped_column(Enum('PENDING', 'IN_REVIEW', 'RESOLVED', 'DISMISSED', name='case_status', create_type=False), default='PENDING')
    assigned_to: Mapped[uuid.UUID | None] = mapped_column(ForeignKey('users.id'))
    conclusion: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text('NOW()'))
    vehicle = relationship('Vehicle')

class CaseReason(Base):
    __tablename__ = 'case_reasons'
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    case_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('review_cases.id'))
    rule_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey('tracking_rules.id'))
    reason: Mapped[str] = mapped_column(Text)
    observed_value: Mapped[float | None] = mapped_column(Numeric(12,2))
    case = relationship('ReviewCase')

class TrackingRule(Base):
    __tablename__ = 'tracking_rules'
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    code: Mapped[str] = mapped_column(String(40), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[str] = mapped_column(Text)
    threshold: Mapped[float] = mapped_column(Numeric(12,2))
    window_hours: Mapped[int]
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
