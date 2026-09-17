from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class Login(BaseModel):
    email: str
    password: str


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


class UserCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: str
    password: str = Field(min_length=8)
    role: str
    institution_id: UUID | None = None
    fixed_station_id: UUID | None = None


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
