from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict, field_validator
from .email_policy import parse_account_email


class Login(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        return parse_account_email(value)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    full_name: str
    email: str
    role: str
    institution_id: UUID | None = None
    fixed_station_id: UUID | None = None
    institution_code: str | None = None
    institution_name: str | None = None


class UserCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: str
    password: str = Field(min_length=8)
    role: str
    institution_id: UUID | None = None
    fixed_station_id: UUID | None = None

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        return parse_account_email(value)


class VehicleIn(BaseModel):
    plate: str = Field(min_length=3, max_length=15)
    vehicle_type: str | None = None
    internal_code: str | None = None
    institution_id: UUID | None = None
    b_sisa_code: str | None = None
    synthetic_make_model: str | None = None
    synthetic_year: int | None = Field(default=None, ge=1980, le=2100)
    rfid_uid: str | None = None
    rfid_enabled: bool = False


class StationIn(BaseModel):
    code: str = Field(min_length=2, max_length=30)
    name: str = Field(min_length=2, max_length=150)
    municipality: str = "La Paz"
    address: str | None = None
    institution_id: UUID | None = None


class InstitutionIn(BaseModel):
    code: str = Field(min_length=2, max_length=30)
    name: str = Field(min_length=2, max_length=160)


class AssignmentIn(BaseModel):
    user_id: UUID
    station_id: UUID
    is_primary: bool = False


class FuelAuthorizationIn(BaseModel):
    fuel_type_id: int
    is_active: bool = True


class OperationIn(BaseModel):
    vehicle_id: UUID
    fuel_type_id: int
    quantity_liters: float = Field(gt=0, le=2000)
    occurred_at: datetime
    notes: str | None = Field(default=None, max_length=500)
    # Accepted for old clients but ignored: station is always taken from session.
    station_id: UUID | None = None


class CaseUpdate(BaseModel):
    status: str
    conclusion: str | None = None
    note: str | None = None


class Page(BaseModel):
    items: list
    total: int
    page: int
    page_size: int


class RfidReadIn(BaseModel):
    """Payload enviado por el ESP32 al leer una tarjeta NFC/RFID con el PN532."""
    rfid_uid: str = Field(min_length=1, max_length=80)
    station_code: str = Field(min_length=2, max_length=30)
    device_id: str = Field(min_length=1, max_length=80)
