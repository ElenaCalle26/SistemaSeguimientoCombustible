# FuelTrack - Seguimiento de Operaciones de Combustible

Prototipo académico para centralizar el registro, la consulta y el seguimiento de operaciones de carguío de combustible. Usa exclusivamente datos sintéticos o anonimizados.

> Importante: FuelTrack identifica señales para revisión mediante criterios transparentes. No determina irregularidades, no emite sanciones y no se conecta con B-SISA, ANH ni estaciones de servicio reales.

## Funcionalidades

- Autenticación con JWT y perfiles `ADMIN`, `OPERATOR` y `SUPERVISOR`.
- Gestión de vehículos y estaciones de servicio.
- Registro y consulta filtrable de operaciones de carguío.
- Reglas explicables para volumen elevado, carguíos muy próximos y uso de múltiples estaciones.
- Casos de revisión con estado y conclusión manual.
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

Las cuentas demo se crean automáticamente en el primer inicio de sesión; cámbialas o elimínalas antes de cualquier uso no local.

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
| GET/POST | `/api/operations` | Consulta/registra operaciones | Todos / Admin, Operator |
| GET/PATCH | `/api/cases` | Seguimiento de casos | Admin, Supervisor |

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
- Antes de producción, añade auditoría, pruebas de integración, gestión de usuarios, limitación de tasa y revisión de seguridad.

## Licencia

Proyecto académico. Revisa las licencias de las dependencias antes de redistribuirlo.
