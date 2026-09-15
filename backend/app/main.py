from datetime import datetime, timedelta, timezone
from uuid import UUID
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from .config import get_settings
from .database import get_db
from .models import CaseReason, FuelType, Operation, ReviewCase, Station, User, Vehicle
from .schemas import CaseUpdate, Login, OperationIn, StationIn, Token, UserOut, VehicleIn
from .security import create_token, current_user, hash_password, require_roles, verify_password

settings = get_settings()
app = FastAPI(title='FuelTrack API', version='1.0.0', description='Prototipo académico con datos sintéticos.')
app.add_middleware(CORSMiddleware, allow_origins=[x.strip() for x in settings.cors_origins.split(',')], allow_credentials=True, allow_methods=['*'], allow_headers=['*'])

def ensure_demo_users(db: Session):
    demos = [
        ('Administrador Demo', 'admin@fueltrack.local', 'Cambiar123!', 'ADMIN'),
        ('Operador Demo', 'operador@fueltrack.local', 'Operador123!', 'OPERATOR'),
        ('Supervisor Demo', 'supervisor@fueltrack.local', 'Supervisor123!', 'SUPERVISOR'),
    ]
    created = False
    for full_name, email, password, role in demos:
        if not db.scalar(select(User).where(User.email == email)):
            db.add(User(full_name=full_name, email=email, password_hash=hash_password(password), role=role))
            created = True
    if created:
        db.commit()

@app.get('/health')
def health(): return {'status': 'ok'}

@app.post('/api/auth/login', response_model=Token)
def login(data: Login, db: Session = Depends(get_db)):
    ensure_demo_users(db)
    user = db.scalar(select(User).where(User.email == data.email))
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Correo o contraseña incorrectos')
    return Token(access_token=create_token(user))

@app.get('/api/auth/me', response_model=UserOut)
def me(user: User = Depends(current_user)): return user

@app.get('/api/dashboard')
def dashboard(db: Session = Depends(get_db), _: User = Depends(current_user)):
    now = datetime.now(timezone.utc)
    return {
      'operations_today': db.scalar(select(func.count()).select_from(Operation).where(Operation.occurred_at >= now - timedelta(days=1))) or 0,
      'pending_cases': db.scalar(select(func.count()).select_from(ReviewCase).where(ReviewCase.status.in_(['PENDING', 'IN_REVIEW']))) or 0,
      'active_vehicles': db.scalar(select(func.count()).select_from(Vehicle).where(Vehicle.is_active.is_(True))) or 0,
      'active_stations': db.scalar(select(func.count()).select_from(Station).where(Station.is_active.is_(True))) or 0,
      'recent_operations': operations_response(db.scalars(select(Operation).order_by(Operation.occurred_at.desc()).limit(6)).all())
    }

@app.get('/api/vehicles')
def list_vehicles(q: str | None = None, db: Session = Depends(get_db), _: User = Depends(current_user)):
    query = select(Vehicle).order_by(Vehicle.plate)
    if q: query = query.where(Vehicle.plate.ilike(f'%{q.upper()}%'))
    return [{'id': x.id, 'plate': x.plate, 'vehicle_type': x.vehicle_type, 'internal_code': x.internal_code, 'is_active': x.is_active} for x in db.scalars(query).all()]

@app.post('/api/vehicles', status_code=201)
def create_vehicle(data: VehicleIn, db: Session = Depends(get_db), _: User = Depends(require_roles('ADMIN', 'SUPERVISOR'))):
    if db.scalar(select(Vehicle).where(Vehicle.plate == data.plate.upper())): raise HTTPException(409, 'La placa ya existe')
    entity = Vehicle(plate=data.plate.upper(), vehicle_type=data.vehicle_type, internal_code=data.internal_code)
    db.add(entity); db.commit(); db.refresh(entity); return {'id': entity.id, 'plate': entity.plate}

@app.get('/api/stations')
def list_stations(db: Session = Depends(get_db), _: User = Depends(current_user)):
    return [{'id': x.id, 'code': x.code, 'name': x.name, 'municipality': x.municipality, 'address': x.address, 'is_active': x.is_active} for x in db.scalars(select(Station).order_by(Station.name)).all()]

@app.post('/api/stations', status_code=201)
def create_station(data: StationIn, db: Session = Depends(get_db), _: User = Depends(require_roles('ADMIN', 'SUPERVISOR'))):
    if db.scalar(select(Station).where(Station.code == data.code.upper())): raise HTTPException(409, 'El código ya existe')
    entity = Station(code=data.code.upper(), **data.model_dump(exclude={'code'})); db.add(entity); db.commit(); db.refresh(entity); return {'id': entity.id, 'code': entity.code}

@app.get('/api/fuel-types')
def fuel_types(db: Session = Depends(get_db), _: User = Depends(current_user)):
    return [{'id': x.id, 'code': x.code, 'name': x.name} for x in db.scalars(select(FuelType).order_by(FuelType.id)).all()]

def operations_response(items):
    return [{'id': x.id, 'vehicle_id': x.vehicle_id, 'plate': x.vehicle.plate, 'station': x.station.name, 'fuel_type': x.fuel_type.name, 'quantity_liters': float(x.quantity_liters), 'occurred_at': x.occurred_at, 'notes': x.notes} for x in items]

@app.get('/api/operations')
def list_operations(vehicle_id: UUID | None = None, station_id: UUID | None = None, start: datetime | None = None, end: datetime | None = None, db: Session = Depends(get_db), _: User = Depends(current_user)):
    query = select(Operation).order_by(Operation.occurred_at.desc())
    if vehicle_id: query = query.where(Operation.vehicle_id == vehicle_id)
    if station_id: query = query.where(Operation.station_id == station_id)
    if start: query = query.where(Operation.occurred_at >= start)
    if end: query = query.where(Operation.occurred_at <= end)
    return operations_response(db.scalars(query.limit(200)).all())

@app.post('/api/operations', status_code=201)
def create_operation(data: OperationIn, db: Session = Depends(get_db), user: User = Depends(require_roles('ADMIN', 'OPERATOR'))):
    if not db.get(Vehicle, data.vehicle_id) or not db.get(Station, data.station_id) or not db.get(FuelType, data.fuel_type_id): raise HTTPException(422, 'Vehículo, estación o combustible inválido')
    entity = Operation(**data.model_dump(), registered_by=user.id); db.add(entity); db.commit(); db.refresh(entity)
    reasons = analyze_operation(entity, db)
    if reasons:
        review = ReviewCase(vehicle_id=entity.vehicle_id, operation_id=entity.id, status='PENDING'); db.add(review); db.flush()
        db.add_all([CaseReason(case_id=review.id, reason=reason, observed_value=float(entity.quantity_liters)) for reason in reasons]); db.commit()
    return {'id': entity.id, 'requires_review': bool(reasons), 'reasons': reasons}

def analyze_operation(operation: Operation, db: Session):
    reasons=[]
    if float(operation.quantity_liters) > 120: reasons.append('Volumen superior al umbral configurado (120 L).')
    recent = db.scalars(select(Operation).where(Operation.vehicle_id == operation.vehicle_id, Operation.id != operation.id, Operation.occurred_at >= operation.occurred_at - timedelta(hours=4), Operation.occurred_at <= operation.occurred_at)).all()
    if recent: reasons.append('Existe un carguío previo del vehículo dentro de las últimas 4 horas.')
    stations = {x.station_id for x in db.scalars(select(Operation).where(Operation.vehicle_id == operation.vehicle_id, Operation.occurred_at >= operation.occurred_at - timedelta(hours=24), Operation.occurred_at <= operation.occurred_at)).all()}
    if len(stations) >= 2: reasons.append('El vehículo utilizó más de una estación durante las últimas 24 horas.')
    return reasons

@app.get('/api/cases')
def list_cases(db: Session = Depends(get_db), _: User = Depends(require_roles('ADMIN', 'SUPERVISOR'))):
    items = db.scalars(select(ReviewCase).order_by(ReviewCase.created_at.desc())).all()
    return [{'id': x.id, 'plate': x.vehicle.plate, 'status': x.status, 'created_at': x.created_at, 'conclusion': x.conclusion, 'operation_id': x.operation_id, 'reasons': [r.reason for r in db.scalars(select(CaseReason).where(CaseReason.case_id == x.id)).all()]} for x in items]

@app.patch('/api/cases/{case_id}')
def update_case(case_id: UUID, data: CaseUpdate, db: Session = Depends(get_db), _: User = Depends(require_roles('ADMIN', 'SUPERVISOR'))):
    entity = db.get(ReviewCase, case_id)
    if not entity: raise HTTPException(404, 'Caso no encontrado')
    if data.status not in {'PENDING','IN_REVIEW','RESOLVED','DISMISSED'}: raise HTTPException(422, 'Estado no válido')
    entity.status=data.status; entity.conclusion=data.conclusion; db.commit(); return {'id': entity.id, 'status': entity.status}
