"""FuelTrack API.

The API is intentionally the source of truth for tenancy and station context:
clients never choose an institution or the station of a fuel operation.
"""
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
import json
import smtplib
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .config import get_settings
from .database import get_db
from .models import (
    Alert, AuditLog, CaseLog, CaseReason, FuelType, Institution, Operation,
    ReviewCase, Station, StationFuelAuthorization, TrackingRule, User,
    UserStationAssignment, Vehicle,
)
from .schemas import (
    AssignmentIn, CaseUpdate,     FuelAuthorizationIn, InstitutionIn, Login, OperationIn, StationIn,
    Token, UserCreate, UserOut, VehicleIn,
)
from .security import create_token, current_user, hash_password, require_roles, verify_password

settings = get_settings()
app = FastAPI(
    title="FuelTrack API",
    version="2.0.0",
    description="Seguimiento multiinstitución con datos sintéticos y aislamiento por backend.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[x.strip() for x in settings.cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def audit(db: Session, actor: User | None, action: str, entity_type: str, entity_id=None, details=None, institution_id=None):
    db.add(AuditLog(
        actor_id=actor.id if actor else None,
        institution_id=institution_id or (actor.institution_id if actor else None),
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id else None,
        details=json.dumps(details, ensure_ascii=False) if isinstance(details, dict) else details,
    ))


def ensure_seed(db: Session):
    """Create a safe, repeatable synthetic dataset for local/demo installations."""
    institution_specs = [
        ("INST-001", "Cristo Autogas S.R.L.", "EST-001", "E/S Cristo Autogas S.R.L."),
        ("INST-002", "Comercializadora Gas-May S.R.L.", "EST-002", "E/S Gas-May S.R.L."),
        ("INST-003", "Estación de Servicio Volcán S.R.L.", "EST-003", "E/S Volcán S.R.L."),
    ]
    institutions = []
    stations = []
    for institution_code, institution_name, station_code, station_name in institution_specs:
        institution = db.scalar(select(Institution).where(Institution.code == institution_code))
        if not institution:
            institution = db.scalar(select(Institution).where(Institution.name == institution_name))
        if not institution and institution_code == "INST-001":
            institution = db.scalar(select(Institution).where(Institution.code == "DEMO-01"))
        if not institution:
            institution = Institution(code=institution_code, name=institution_name)
            db.add(institution)
            db.flush()
        else:
            institution.code = institution_code
            institution.name = institution_name
        station = db.scalar(select(Station).where(Station.code == station_code))
        if not station:
            station = db.scalar(select(Station).where(Station.name == station_name))
        if not station and station_code in {"EST-001", "EST-002"}:
            legacy_code = "LPZ-CENTRO" if station_code == "EST-001" else "LPZ-SUR"
            station = db.scalar(select(Station).where(Station.code == legacy_code))
        if not station:
            station = Station(code=station_code, name=station_name, municipality="La Paz", institution_id=institution.id)
            db.add(station)
            db.flush()
        else:
            station.code = station_code
            station.name = station_name
            station.institution_id = institution.id
        institutions.append(institution)
        stations.append(station)
    for code, name in (("GAS_ESP", "Gasolina Especial"), ("DIESEL", "Diesel Oil"), ("GNV", "Gas Natural Vehicular")):
        fuel = db.scalar(select(FuelType).where(FuelType.code == code))
        if not fuel:
            fuel = FuelType(code=code, name=name, is_active=True)
            db.add(fuel)
            db.flush()
        for station in stations:
            if not db.scalar(select(StationFuelAuthorization).where(
                StationFuelAuthorization.station_id == station.id,
                StationFuelAuthorization.fuel_type_id == fuel.id,
            )):
                db.add(StationFuelAuthorization(station_id=station.id, fuel_type_id=fuel.id))
    rules = [
        ("HIGH_VOLUME", "Volumen elevado", "Cantidad superior a 120 litros.", 120, 24),
        ("SHORT_INTERVAL", "Carguíos frecuentes", "Carguíos dentro de cuatro horas.", 1, 4),
        ("MULTI_STATION", "Entre estaciones", "Uso de estaciones diferentes en 24 horas.", 2, 24),
        ("THIRD_FUELING", "Tercer carguío prioritario", "Tres o más carguíos del vehículo en 24 horas.", 3, 24),
    ]
    for code, name, description, threshold, hours in rules:
        if not db.scalar(select(TrackingRule).where(TrackingRule.code == code)):
            db.add(TrackingRule(code=code, name=name, description=description, threshold=threshold, window_hours=hours))
    demos = [
        ("Administrador Demo", "admin@fueltrack.local", "Cambiar123!", "ADMIN", None, None),
        ("Operador Cristo", "operador.cristo@fueltrack.local", "Operador123!", "OPERATOR", institutions[0], stations[0]),
        ("Operador Gas-May", "operador.gasmay@fueltrack.local", "Operador123!", "OPERATOR", institutions[1], stations[1]),
        ("Operador Volcán", "operador.volcan@fueltrack.local", "Operador123!", "OPERATOR", institutions[2], stations[2]),
        ("Supervisor Multiestación", "supervisor@fueltrack.local", "Supervisor123!", "SUPERVISOR", institutions[0], stations[0]),
    ]
    for full_name, email, password, role, institution, station in demos:
        user = db.scalar(select(User).where(User.email == email))
        if not user:
            user = User(
                full_name=full_name, email=email, password_hash=hash_password(password),
                role=role, institution_id=institution.id if institution else None,
                fixed_station_id=station.id if station else None,
            )
            db.add(user)
            db.flush()
        if station and not db.scalar(select(UserStationAssignment).where(
            UserStationAssignment.user_id == user.id, UserStationAssignment.station_id == station.id,
        )):
            db.add(UserStationAssignment(user_id=user.id, station_id=station.id, is_primary=True))
    supervisor = db.scalar(select(User).where(User.email == "supervisor@fueltrack.local"))
    if supervisor:
        for station in stations:
            if not db.scalar(select(UserStationAssignment).where(
                UserStationAssignment.user_id == supervisor.id,
                UserStationAssignment.station_id == station.id,
            )):
                db.add(UserStationAssignment(
                    user_id=supervisor.id,
                    station_id=station.id,
                    is_primary=station.id == stations[0].id,
                ))
    if not db.scalar(select(Vehicle).where(Vehicle.plate == "SYN-001")):
        db.add_all([
            Vehicle(plate="SYN-001", institution_id=institution.id, vehicle_type="Camioneta",
                    internal_code="DEMO-001", b_sisa_code="BSISA-SYN-001", synthetic_make_model="Modelo Sintético A",
                    synthetic_year=2022, rfid_uid="RFID-DEMO-001", rfid_enabled=True),
            Vehicle(plate="SYN-002", institution_id=institution.id, vehicle_type="Sedán",
                    internal_code="DEMO-002", b_sisa_code="BSISA-SYN-002", synthetic_make_model="Modelo Sintético B",
                    synthetic_year=2023, rfid_enabled=False),
        ])
    db.commit()


def scope(query, user: User, model, station_field=None):
    if user.role == "ADMIN":
        return query
    query = query.where(model.institution_id == user.institution_id)
    if station_field is not None:
        assigned_stations = select(UserStationAssignment.station_id).where(
            UserStationAssignment.user_id == user.id,
            UserStationAssignment.is_active.is_(True),
        )
        query = query.where(station_field.in_(assigned_stations))
    return query


def page_response(items, total, page, page_size):
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/auth/login", response_model=Token)
def login(data: Login, db: Session = Depends(get_db)):
    ensure_seed(db)
    user = db.scalar(select(User).where(func.lower(User.email) == data.email.lower().strip()))
    if not user or not user.is_active or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Correo o contraseña incorrectos")
    audit(db, user, "LOGIN", "User", user.id)
    db.commit()
    return Token(access_token=create_token(user))


@app.get("/api/auth/me", response_model=UserOut)
def me(user: User = Depends(current_user)):
    return user


@app.get("/api/dashboard")
def dashboard(db: Session = Depends(get_db), user: User = Depends(current_user)):
    now = datetime.now(timezone.utc)
    operation_query = scope(select(Operation), user, Operation, Operation.station_id)
    case_query = scope(select(ReviewCase), user, ReviewCase, ReviewCase.station_id)
    vehicle_query = select(Vehicle).where(Vehicle.is_active.is_(True))
    station_query = select(Station).where(Station.is_active.is_(True))
    if user.role != "ADMIN":
        vehicle_query = vehicle_query.where(Vehicle.institution_id == user.institution_id)
        assigned_stations = select(UserStationAssignment.station_id).where(
            UserStationAssignment.user_id == user.id,
            UserStationAssignment.is_active.is_(True),
        )
        station_query = station_query.where(Station.id.in_(assigned_stations))
    recent = db.scalars(operation_query.order_by(Operation.occurred_at.desc()).limit(8)).all()
    operation_subquery = operation_query.subquery()
    case_subquery = case_query.where(ReviewCase.status.in_(["PENDING", "IN_REVIEW"])).subquery()
    return {
        "operations_today": db.scalar(select(func.count()).select_from(operation_subquery).where(operation_subquery.c.occurred_at >= now - timedelta(days=1))) or 0,
        "pending_cases": db.scalar(select(func.count()).select_from(case_subquery)) or 0,
        "active_vehicles": db.scalar(select(func.count()).select_from(vehicle_query.subquery())) or 0,
        "active_stations": db.scalar(select(func.count()).select_from(station_query.subquery())) or 0,
        "recent_operations": operations_response(recent),
    }


@app.get("/api/institutions")
def list_institutions(db: Session = Depends(get_db), _: User = Depends(require_roles("ADMIN"))):
    return [{"id": x.id, "code": x.code, "name": x.name, "is_active": x.is_active}
            for x in db.scalars(select(Institution).order_by(Institution.name)).all()]


@app.post("/api/institutions", status_code=201)
def create_institution(data: InstitutionIn, db: Session = Depends(get_db), user: User = Depends(require_roles("ADMIN"))):
    code = data.code.upper()
    if db.scalar(select(Institution).where(Institution.code == code)):
        raise HTTPException(409, "El código de institución ya existe")
    entity = Institution(code=code, name=data.name)
    db.add(entity)
    audit(db, user, "CREATE", "Institution", details={"code": code})
    db.commit()
    db.refresh(entity)
    return {"id": entity.id, "code": entity.code, "name": entity.name}


@app.get("/api/users")
def list_users(db: Session = Depends(get_db), user: User = Depends(require_roles("ADMIN"))):
    users = db.scalars(select(User).order_by(User.full_name)).all()
    return [{"id": x.id, "full_name": x.full_name, "email": x.email, "role": x.role,
             "institution_id": x.institution_id, "fixed_station_id": x.fixed_station_id, "is_active": x.is_active}
            for x in users]


@app.post("/api/users", status_code=201)
def create_user(data: UserCreate, db: Session = Depends(get_db), user: User = Depends(require_roles("ADMIN"))):
    if data.role not in {"ADMIN", "SUPERVISOR", "OPERATOR"}:
        raise HTTPException(422, "Rol no válido")
    if db.scalar(select(User).where(func.lower(User.email) == data.email.lower())):
        raise HTTPException(409, "El correo ya existe")
    if data.role != "ADMIN" and (not data.institution_id or not data.fixed_station_id):
        raise HTTPException(422, "Supervisor y operador requieren institución y estación fija")
    entity = User(**data.model_dump(exclude={"password"}), password_hash=hash_password(data.password))
    db.add(entity)
    audit(db, user, "CREATE", "User", details={"email": data.email, "role": data.role})
    db.commit()
    db.refresh(entity)
    return UserOut.model_validate(entity)


@app.post("/api/user-stations", status_code=201)
def assign_station(data: AssignmentIn, db: Session = Depends(get_db), user: User = Depends(require_roles("ADMIN"))):
    target, station = db.get(User, data.user_id), db.get(Station, data.station_id)
    if not target or not station or (target.role != "ADMIN" and target.institution_id != station.institution_id):
        raise HTTPException(422, "Asignación incompatible")
    assignment = UserStationAssignment(user_id=target.id, station_id=station.id, is_primary=data.is_primary)
    db.add(assignment)
    if data.is_primary:
        target.fixed_station_id = station.id
    audit(db, user, "ASSIGN_STATION", "User", target.id, {"station_id": str(station.id)})
    db.commit()
    return {"ok": True, "user_id": target.id, "station_id": station.id}


@app.get("/api/vehicles")
def list_vehicles(q: str | None = None, page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=100),
                  db: Session = Depends(get_db), user: User = Depends(current_user)):
    query = select(Vehicle).order_by(Vehicle.plate)
    if user.role != "ADMIN":
        query = query.where(Vehicle.institution_id == user.institution_id)
    if q:
        query = query.where(Vehicle.plate.ilike(f"%{q.upper()}%"))
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = db.scalars(query.offset((page - 1) * page_size).limit(page_size)).all()
    items = [{"id": x.id, "plate": x.plate, "vehicle_type": x.vehicle_type, "internal_code": x.internal_code,
              "b_sisa_code": x.b_sisa_code, "synthetic_make_model": x.synthetic_make_model,
              "synthetic_year": x.synthetic_year, "rfid_uid": x.rfid_uid, "rfid_enabled": x.rfid_enabled,
              "institution_id": x.institution_id, "is_active": x.is_active} for x in rows]
    return page_response(items, total, page, page_size)


@app.post("/api/vehicles", status_code=201)
def create_vehicle(_: VehicleIn, user: User = Depends(current_user)):
    raise HTTPException(403, "Los vehículos provienen del padrón sintético B-SISA; ningún rol puede crearlos")


@app.get("/api/stations")
def list_stations(db: Session = Depends(get_db), user: User = Depends(current_user)):
    query = select(Station).order_by(Station.name)
    if user.role != "ADMIN":
        assigned_stations = select(UserStationAssignment.station_id).where(
            UserStationAssignment.user_id == user.id,
            UserStationAssignment.is_active.is_(True),
        )
        query = query.where(Station.id.in_(assigned_stations), Station.institution_id == user.institution_id)
    return [{"id": x.id, "code": x.code, "name": x.name, "municipality": x.municipality,
             "address": x.address, "institution_id": x.institution_id, "is_active": x.is_active,
             "is_fixed_for_session": x.id == user.fixed_station_id} for x in db.scalars(query).all()]


@app.post("/api/stations", status_code=201)
def create_station(data: StationIn, db: Session = Depends(get_db), user: User = Depends(require_roles("ADMIN", "SUPERVISOR"))):
    code = data.code.upper()
    if db.scalar(select(Station).where(Station.code == code)):
        raise HTTPException(409, "El código ya existe")
    institution_id = data.institution_id if user.role == "ADMIN" else user.institution_id
    if not institution_id:
        raise HTTPException(422, "La institución es obligatoria")
    if user.role == "SUPERVISOR" and data.institution_id and data.institution_id != user.institution_id:
        raise HTTPException(403, "El supervisor solo puede crear estaciones de su institución")
    entity = Station(code=code, name=data.name, municipality=data.municipality, address=data.address,
                     institution_id=institution_id)
    db.add(entity)
    audit(db, user, "CREATE", "Station", details={"code": code})
    db.commit()
    db.refresh(entity)
    return {"id": entity.id, "code": entity.code}


@app.get("/api/fuel-types")
def fuel_types(db: Session = Depends(get_db), _: User = Depends(current_user)):
    return [{"id": x.id, "code": x.code, "name": x.name} for x in db.scalars(
        select(FuelType).where(FuelType.is_active.is_(True)).order_by(FuelType.id)).all()]


@app.get("/api/stations/{station_id}/fuel-authorizations")
def list_fuel_authorizations(station_id: UUID, db: Session = Depends(get_db), user: User = Depends(current_user)):
    station = db.get(Station, station_id)
    if not station or (user.role != "ADMIN" and (
        station.institution_id != user.institution_id or station_id != user.fixed_station_id
    )):
        raise HTTPException(404, "Estación no encontrada")
    rows = db.scalars(select(StationFuelAuthorization).where(
        StationFuelAuthorization.station_id == station_id
    ).order_by(StationFuelAuthorization.fuel_type_id)).all()
    return [{"id": x.id, "station_id": x.station_id, "fuel_type_id": x.fuel_type_id,
             "fuel_type": x.fuel_type.name, "is_active": x.is_active} for x in rows]


@app.post("/api/stations/{station_id}/fuel-authorizations", status_code=201)
def authorize_fuel(station_id: UUID, data: FuelAuthorizationIn, db: Session = Depends(get_db),
                   user: User = Depends(require_roles("ADMIN"))):
    station, fuel = db.get(Station, station_id), db.get(FuelType, data.fuel_type_id)
    if not station or not fuel:
        raise HTTPException(404, "Estación o combustible no encontrado")
    entity = db.scalar(select(StationFuelAuthorization).where(
        StationFuelAuthorization.station_id == station_id,
        StationFuelAuthorization.fuel_type_id == fuel.id,
    ))
    if entity:
        entity.is_active = data.is_active
    else:
        entity = StationFuelAuthorization(station_id=station_id, fuel_type_id=fuel.id, is_active=data.is_active)
        db.add(entity)
    audit(db, user, "AUTHORIZE_FUEL", "Station", station_id, {"fuel_type_id": data.fuel_type_id})
    db.commit()
    return {"station_id": station_id, "fuel_type_id": fuel.id, "is_active": data.is_active}


def operations_response(items):
    return [{"id": x.id, "vehicle_id": x.vehicle_id, "plate": x.vehicle.plate,
             "station_id": x.station_id, "station": x.station.name, "fuel_type_id": x.fuel_type_id,
             "fuel_type": x.fuel_type.name, "quantity_liters": float(x.quantity_liters),
             "occurred_at": x.occurred_at, "notes": x.notes, "registered_by": x.registered_by}
            for x in items]


@app.get("/api/operations")
def list_operations(vehicle_id: UUID | None = None, station_id: UUID | None = None,
                    start: datetime | None = None, end: datetime | None = None,
                    page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=100),
                    db: Session = Depends(get_db), user: User = Depends(current_user)):
    query = scope(select(Operation), user, Operation, Operation.station_id).order_by(Operation.occurred_at.desc())
    if vehicle_id:
        query = query.where(Operation.vehicle_id == vehicle_id)
    if station_id and user.role == "ADMIN":
        query = query.where(Operation.station_id == station_id)
    if start:
        query = query.where(Operation.occurred_at >= start)
    if end:
        query = query.where(Operation.occurred_at <= end)
    total = db.scalar(select(func.count()).select_from(query.order_by(None).subquery())) or 0
    rows = db.scalars(query.offset((page - 1) * page_size).limit(page_size)).all()
    return page_response(operations_response(rows), total, page, page_size)


def resolve_session_station(user: User, db: Session) -> Station:
    if user.role == "ADMIN":
        raise HTTPException(403, "ADMIN no registra operaciones; use un operador o supervisor asignado")
    if not user.fixed_station_id:
        raise HTTPException(403, "La sesión no tiene una estación fija asignada")
    station = db.get(Station, user.fixed_station_id)
    if not station or not station.is_active or station.institution_id != user.institution_id:
        raise HTTPException(403, "La estación fija no está disponible")
    return station


def notify_priority_alert(vehicle: Vehicle, reasons: list[str]):
    if not settings.smtp_host or not settings.alert_recipient:
        return
    message = EmailMessage()
    message["Subject"] = f"FuelTrack: alerta prioritaria para {vehicle.plate}"
    message["From"] = settings.smtp_user or "fueltrack@localhost"
    message["To"] = settings.alert_recipient
    message.set_content("Alerta sintética de FuelTrack:\n" + "\n".join(reasons))
    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=8) as server:
            server.starttls()
            if settings.smtp_user and settings.smtp_password:
                server.login(settings.smtp_user, settings.smtp_password)
            server.send_message(message)
    except (OSError, smtplib.SMTPException):
        # SMTP is optional and must never make a fuel operation fail.
        return


@app.post("/api/operations", status_code=201)
def create_operation(data: OperationIn, db: Session = Depends(get_db), user: User = Depends(require_roles("OPERATOR", "SUPERVISOR"))):
    station = resolve_session_station(user, db)
    vehicle = db.get(Vehicle, data.vehicle_id)
    fuel = db.get(FuelType, data.fuel_type_id)
    if not vehicle or vehicle.institution_id != user.institution_id or not vehicle.is_active or not fuel or not fuel.is_active:
        raise HTTPException(422, "Vehículo o combustible inválido para la institución")
    authorization = db.scalar(select(StationFuelAuthorization).where(
        StationFuelAuthorization.station_id == station.id,
        StationFuelAuthorization.fuel_type_id == fuel.id,
        StationFuelAuthorization.is_active.is_(True),
    ))
    if not authorization:
        raise HTTPException(422, "El combustible no está autorizado en la estación de la sesión")
    entity = Operation(institution_id=user.institution_id, vehicle_id=vehicle.id, station_id=station.id,
                       fuel_type_id=fuel.id, quantity_liters=data.quantity_liters,
                       occurred_at=data.occurred_at, registered_by=user.id, notes=data.notes)
    db.add(entity)
    db.flush()
    reasons = analyze_operation(entity, db)
    case = None
    if reasons:
        priority = "URGENT" if any(code == "THIRD_FUELING" for code, _ in reasons) else "NORMAL"
        case = ReviewCase(institution_id=user.institution_id, station_id=station.id, vehicle_id=vehicle.id,
                          operation_id=entity.id, status="PENDING", priority=priority)
        db.add(case)
        db.flush()
        db.add(CaseLog(case_id=case.id, actor_id=user.id, action="CREATED", note="Caso generado por regla automática"))
        for code, reason in reasons:
            db.add(CaseReason(case_id=case.id, rule_id=db.scalar(select(TrackingRule.id).where(TrackingRule.code == code)),
                              reason=reason, observed_value=data.quantity_liters))
            db.add(Alert(institution_id=user.institution_id, station_id=station.id, vehicle_id=vehicle.id,
                         operation_id=entity.id, case_id=case.id, code=code,
                         severity="CRITICAL" if priority == "URGENT" else "WARNING", message=reason))
        if priority == "URGENT":
            notify_priority_alert(vehicle, [reason for _, reason in reasons])
    audit(db, user, "CREATE", "Operation", entity.id, {"station_id": str(station.id), "alert": bool(reasons)})
    db.commit()
    return {"id": entity.id, "station_id": station.id, "requires_review": bool(reasons),
            "priority": case.priority if case else None, "reasons": [reason for _, reason in reasons]}


def analyze_operation(operation: Operation, db: Session):
    """Return (rule_code, explanation) pairs; rules only create review signals."""
    reasons = []
    if float(operation.quantity_liters) > 120:
        reasons.append(("HIGH_VOLUME", "Volumen superior al umbral configurado (120 L)."))
    window_4h = db.scalars(select(Operation).where(
        Operation.vehicle_id == operation.vehicle_id,
        Operation.id != operation.id,
        Operation.occurred_at >= operation.occurred_at - timedelta(hours=4),
        Operation.occurred_at <= operation.occurred_at,
    )).all()
    if window_4h:
        reasons.append(("SHORT_INTERVAL", "Existe un carguío previo del vehículo dentro de las últimas 4 horas."))
    window_24h = db.scalars(select(Operation).where(
        Operation.vehicle_id == operation.vehicle_id,
        Operation.occurred_at >= operation.occurred_at - timedelta(hours=24),
        Operation.occurred_at <= operation.occurred_at,
    )).all()
    if len({x.station_id for x in window_24h}) >= 2:
        reasons.append(("MULTI_STATION", "El vehículo utilizó más de una estación durante las últimas 24 horas."))
    if len(window_24h) + 1 >= 3:
        reasons.append(("THIRD_FUELING", "Tercer carguío o posterior en 24 horas: revisión prioritaria."))
    return reasons


def case_response(x, db):
    return {"id": x.id, "plate": x.vehicle.plate, "station": x.station.name, "status": x.status,
            "priority": x.priority, "created_at": x.created_at, "updated_at": x.updated_at,
            "conclusion": x.conclusion, "operation_id": x.operation_id,
            "reasons": [{"reason": r.reason, "rule": r.rule_id} for r in db.scalars(
                select(CaseReason).where(CaseReason.case_id == x.id)).all()],
            "log": [{"action": l.action, "note": l.note, "created_at": l.created_at} for l in db.scalars(
                select(CaseLog).where(CaseLog.case_id == x.id).order_by(CaseLog.created_at)).all()]}


@app.get("/api/cases")
def list_cases(page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=100),
               status_filter: str | None = Query(None, alias="status"),
               db: Session = Depends(get_db), user: User = Depends(require_roles("ADMIN", "SUPERVISOR"))):
    query = scope(select(ReviewCase).order_by(ReviewCase.created_at.desc()), user, ReviewCase, ReviewCase.station_id)
    if status_filter:
        query = query.where(ReviewCase.status == status_filter)
    total = db.scalar(select(func.count()).select_from(query.order_by(None).subquery())) or 0
    return page_response([case_response(x, db) for x in db.scalars(
        query.offset((page - 1) * page_size).limit(page_size)).all()], total, page, page_size)


@app.patch("/api/cases/{case_id}")
def update_case(case_id: UUID, data: CaseUpdate, db: Session = Depends(get_db),
                user: User = Depends(require_roles("ADMIN", "SUPERVISOR"))):
    entity = db.get(ReviewCase, case_id)
    if not entity or (user.role != "ADMIN" and (
        entity.institution_id != user.institution_id or entity.station_id != user.fixed_station_id
    )):
        raise HTTPException(404, "Caso no encontrado")
    if data.status not in {"PENDING", "IN_REVIEW", "RESOLVED", "DISMISSED"}:
        raise HTTPException(422, "Estado no válido")
    entity.status, entity.conclusion, entity.updated_at = data.status, data.conclusion, datetime.now(timezone.utc)
    db.add(CaseLog(case_id=entity.id, actor_id=user.id, action=data.status, note=data.note or data.conclusion))
    audit(db, user, "UPDATE", "ReviewCase", entity.id, {"status": data.status})
    db.commit()
    return {"id": entity.id, "status": entity.status}


@app.get("/api/alerts")
def list_alerts(page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=100),
                unread_only: bool = False, db: Session = Depends(get_db),
                user: User = Depends(require_roles("ADMIN", "SUPERVISOR"))):
    query = scope(select(Alert).order_by(Alert.created_at.desc()), user, Alert, Alert.station_id)
    if unread_only:
        query = query.where(Alert.is_read.is_(False))
    total = db.scalar(select(func.count()).select_from(query.order_by(None).subquery())) or 0
    rows = db.scalars(query.offset((page - 1) * page_size).limit(page_size)).all()
    return page_response([{"id": x.id, "code": x.code, "severity": x.severity, "message": x.message,
                          "station_id": x.station_id, "vehicle_id": x.vehicle_id, "case_id": x.case_id,
                          "is_read": x.is_read, "created_at": x.created_at} for x in rows], total, page, page_size)


@app.get("/api/audit")
def list_audit(page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=100),
               action: str | None = None, db: Session = Depends(get_db),
               user: User = Depends(require_roles("ADMIN"))):
    query = select(AuditLog).order_by(AuditLog.created_at.desc())
    if action:
        query = query.where(AuditLog.action == action)
    total = db.scalar(select(func.count()).select_from(query.order_by(None).subquery())) or 0
    rows = db.scalars(query.offset((page - 1) * page_size).limit(page_size)).all()
    return page_response([{"id": x.id, "actor_id": x.actor_id, "action": x.action, "entity_type": x.entity_type,
                          "entity_id": x.entity_id, "details": x.details, "created_at": x.created_at} for x in rows],
                         total, page, page_size)
