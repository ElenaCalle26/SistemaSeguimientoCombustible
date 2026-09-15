from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field

class Login(BaseModel): email: str; password: str
class Token(BaseModel): access_token: str; token_type: str = 'bearer'
class UserOut(BaseModel): id: UUID; full_name: str; email: str; role: str
class VehicleIn(BaseModel): plate: str = Field(min_length=3, max_length=15); vehicle_type: str | None = None; internal_code: str | None = None
class StationIn(BaseModel): code: str; name: str; municipality: str = 'La Paz'; address: str | None = None
class OperationIn(BaseModel): vehicle_id: UUID; station_id: UUID; fuel_type_id: int; quantity_liters: float = Field(gt=0); occurred_at: datetime; notes: str | None = None
class CaseUpdate(BaseModel): status: str; conclusion: str | None = None
