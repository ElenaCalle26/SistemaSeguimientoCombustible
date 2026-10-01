# FuelTrack - Seguimiento de Operaciones de Combustible

Prototipo académico para centralizar el registro, la consulta y el seguimiento de operaciones de carguío de combustible. Usa exclusivamente datos sintéticos o anonimizados.

> Importante: FuelTrack identifica señales para revisión mediante criterios transparentes. No determina irregularidades, no emite sanciones y no se conecta con B-SISA, ANH ni estaciones de servicio reales.

## Funcionalidades

- Autenticación con JWT y perfiles `ADMIN`, `OPERATOR` y `SUPERVISOR`.
- Multiinstitución con aislamiento backend y estaciones asignadas a cada sesión.
- Solo tres roles: `ADMIN`, `SUPERVISOR` y `OPERATOR`; ADMIN administra pero no registra carguíos.
- Vehículos sintéticos precargados con campos B-SISA simulados y RFID opcional.
- Combustibles autorizados por estación, operaciones con estación fija de sesión y paginación/filtros.
- Alertas explicables (volumen, intervalo, entre estaciones y tercer carguío prioritario), casos con bitácora y SMTP opcional.
- Auditoría append-only consultable por ADMIN (`/api/audit`).
- Panel React minimalista y responsivo.
- Esquema SQL PostgreSQL listo para importar.

## Arquitectura

`React (Vite / Nginx) -> FastAPI REST -> PostgreSQL`

Puertos por defecto: web `5173`, API `8000` y PostgreSQL `5432`.

## Inicio rápido con Docker

1. Copia la configuración: `cp .env.example .env` (Linux/Mac) o `Copy-Item .env.example .env` (Windows).
2. Cambia `POSTGRES_PASSWORD` y `SECRET_KEY` en `.env`.
3. Inicia: `docker compose up --build`.
4. Abre `http://localhost:5173`; documentación API: `http://localhost:8000/docs`.

La primera creación ejecuta automáticamente `database/schema.sql`.

Credenciales demo:

- `admin@fueltrack.local` / `Cambiar123!`
- `operador.cristo@fueltrack.local` / `Operador123!`
- `operador.gasmay@fueltrack.local` / `Operador123!`
- `operador.volcan@fueltrack.local` / `Operador123!`
- `supervisor@fueltrack.local` / `Supervisor123!`

Las cuentas demo y el tenant sintético se crean automáticamente en el primer inicio de sesión; cámbialas o elimínalas antes de cualquier uso no local.

## Ejecución local

Requisitos: Python 3.12+, Node 20+ y PostgreSQL 16+.

1. Crea la base de datos y ejecuta `database/schema.sql` desde pgAdmin o `psql`.
2. En `backend`, copia `.env.example` como `.env`, crea un entorno virtual, instala `requirements.txt` e inicia `uvicorn app.main:app --reload`.
3. En `frontend`, ejecuta `npm install` y `npm run dev`.

Configura `DATABASE_URL` en `backend/.env` con tus credenciales PostgreSQL. No subas ese archivo ni secretos al repositorio.

## API principal

| Método | Ruta | Uso | Roles |
|---|---|---|---|
| POST | `/api/auth/login` | Inicia sesión | Público |
| GET | `/api/dashboard` | Indicadores y actividad | Todos |
| GET | `/api/vehicles` | Consulta el padrón nacional sintético | Todos |
| GET/POST | `/api/stations` | Consulta/crea estaciones | Todos / Admin, Supervisor |
| GET/POST | `/api/operations` | Consulta/registra operaciones (estación de sesión) | Todos / Operator |
| POST | `/api/rfid/read` | Consulta vehículo por UID RFID (ESP32/PN532) | Público (sin JWT) |
| GET/PATCH | `/api/cases` | Seguimiento de casos | Admin, Supervisor |
| GET | `/api/cases-report.pdf` | PDF de cambios de casos y bitácora visible | Admin, Supervisor |
| GET | `/api/alerts` | Alertas y tercer carguío prioritario | Admin, Supervisor |
| GET | `/api/audit` | Bitácora inmutable | Admin |
| GET/POST | `/api/users`, `/api/user-stations` | Usuarios y asignaciones | Admin |
| GET/POST | `/api/stations/{id}/fuel-authorizations` | Combustibles permitidos por estación | Todos / Admin |

Usa `Authorization: Bearer <token>` en rutas protegidas. La documentación interactiva está en `/docs`.

## Integración RFID (PN532 + ESP32)

Hardware utilizado en la demo: ESP32 de 38 pines con módulo PN532 NFC/RFID en modo SPI (13.56 MHz).

Conexión SPI:

| PN532 | ESP32 |
|---|---|
| 3.3V | 3V3 |
| GND | GND |
| SCK | GPIO 18 |
| MISO | GPIO 19 |
| MOSI | GPIO 23 |
| SS | GPIO 5 |

UIDs del hardware registrados en el padrón sintético:

| UID | Placa | Tipo |
|---|---|---|
| `D0:9B:E2:5F` | SYN-001 | Llavero NFC |
| `D0:89:22:5F` | SYN-002 | Tarjeta NFC |
| `CC:21:6B:06` | SYN-003 | Camioneta sintética |
| `1C:F8:6B:06` | — | UID de reserva (resultado: UNKNOWN) |

### Endpoint de lectura

`POST /api/rfid/read` — sin JWT (el ESP32 no mantiene sesión de usuario).

```json
{
  "rfid_uid": "D0:9B:E2:5F",
  "station_code": "EST-001",
  "device_id": "ESP32-EST-001"
}
```

La respuesta incluye el estado del vehículo (`AUTHORIZED`, `OBSERVED`, `RESTRICTED` o `UNKNOWN`),
datos del padrón sintético, combustibles autorizados en la estación, historial reciente y alertas activas.

La lectura RFID **nunca registra automáticamente una operación**; el operador confirma manualmente
los litros y el tipo de combustible antes de guardar.

### Simulación desde la interfaz web

En la vista **Operaciones** (rol Operador) aparece el panel **Lectura RFID** con:
- Campo de ingreso manual de UID.
- Botones de acceso rápido para los UIDs del hardware real.
- Tarjeta de resultado con placa, tipo, modelo, combustibles, historial y alertas.
- Preselección automática del vehículo en el formulario de operación si el estado es `AUTHORIZED`.

## Estructura

- `backend/`: API FastAPI, seguridad y modelos.
- `frontend/`: interfaz React/Vite.
- `database/schema.sql`: tablas y reglas iniciales para PostgreSQL.
- `docker-compose.yml`: entorno completo de desarrollo.

## Reglas de revisión iniciales

Los umbrales están inicializados en `tracking_rules`: más de 120 litros en una operación, un carguío anterior dentro de 4 horas, o dos o más estaciones usadas en 24 horas. El resultado crea un caso pendiente con sus razones; una persona debe evaluarlo y registrar la conclusión.

## Seguridad y límites

- Usa secretos distintos por entorno y HTTPS en producción.
- No ingreses nombres de propietarios, documentos de identidad, fotos o información oficial confidencial.
- Usa copias de seguridad, usuarios de mínimo privilegio y una red restringida para PostgreSQL.
- SMTP es opcional: configura `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD` y `ALERT_RECIPIENT` para notificar el tercer carguío prioritario. Si no se configura, la alerta permanece disponible en la API.
Desde **Casos de revisión**, el botón **PDF de actividad** genera un reporte con los cambios de casos
(quién, rol, acción, fecha y conclusión) y la bitácora general. ADMIN obtiene el alcance global;
SUPERVISOR solo recibe los eventos de su institución y los casos de sus estaciones asignadas.

## Licencia

Proyecto académico. Revisa las licencias de las dependencias antes de redistribuirlo.
