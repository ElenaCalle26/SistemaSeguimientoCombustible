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

1. Copia la configuración: `Copy-Item .env.example .env`.
2. Cambia `POSTGRES_PASSWORD` y `SECRET_KEY` en `.env`.
3. Inicia: `docker compose up --build`.
4. Abre `http://localhost:5173`; documentación API: `http://localhost:8000/docs`.

La primera creación ejecuta automáticamente `database/schema.sql`.

Credenciales demo:

- `admin@fueltrack.local` / `Cambiar123!`
- `operador@fueltrack.local` / `Operador123!`
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
| GET/POST | `/api/vehicles` | Consulta/crea vehículos | Todos / Admin, Supervisor |
| GET/POST | `/api/stations` | Consulta/crea estaciones | Todos / Admin, Supervisor |
| GET/POST | `/api/operations` | Consulta/registra operaciones (estación de sesión) | Todos / Supervisor, Operator |
| GET/PATCH | `/api/cases` | Seguimiento de casos | Admin, Supervisor |
| GET | `/api/alerts` | Alertas y tercer carguío prioritario | Admin, Supervisor |
| GET | `/api/audit` | Bitácora inmutable | Admin |
| GET/POST | `/api/users`, `/api/user-stations` | Usuarios y asignaciones | Admin |
| GET/POST | `/api/stations/{id}/fuel-authorizations` | Combustibles permitidos por estación | Todos / Admin |

Usa `Authorization: Bearer <token>` en rutas protegidas. La documentación interactiva está en `/docs`.

Usa `Authorization: Bearer <token>` en rutas protegidas. La documentación interactiva está en `/docs`.

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
La exportación PDF no se incorpora para mantener el contenedor liviano; los endpoints paginados entregan los datos necesarios para reportes.

## Licencia

Proyecto académico. Revisa las licencias de las dependencias antes de redistribuirlo.
