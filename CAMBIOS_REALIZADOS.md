# Cambios realizados en FuelTrack

Este documento resume los cambios realizados en el proyecto, los archivos involucrados y la forma de ejecutar y verificar el sistema.

## 1. Corrección de la compilación del frontend con Docker

### Archivo agregado

- `frontend/.dockerignore`

### Cambio realizado

Se agregó un archivo `.dockerignore` para evitar que Docker copie dependencias locales dentro de la imagen:

```text
node_modules
dist
npm-debug.log*
```

### Motivo

La compilación fallaba con un error similar a:

```text
cannot replace to directory ... /app/node_modules/@vitejs/plugin-react with file
```

La causa era que la carpeta local `frontend/node_modules` se copiaba sobre los módulos instalados dentro del contenedor.

## 2. Corrección del login con el correo demo

### Archivo modificado

- `backend/app/schemas.py`

### Cambio realizado

El esquema de login dejó de utilizar `EmailStr` y pasó a utilizar `str` para el campo `email`.

También se ajustó `UserOut` para devolver el correo como texto.

### Motivo

El correo demo utiliza el dominio sintético `.local`:

```text
admin@fueltrack.local
```

El validador `EmailStr` rechazaba ese dominio y devolvía un error HTTP `422`, aunque el correo se usa intencionalmente para desarrollo local.

## 3. Corrección de la conexión a PostgreSQL

### Archivo modificado localmente

- `.env`

### Cambio realizado

Se corrigió `DATABASE_URL` para codificar correctamente caracteres especiales de la contraseña de PostgreSQL.

Una contraseña que contiene `@` debe representarse como `%40` dentro de una URL. Por ejemplo:

```text
Contraseña original: MiClave@123
Contraseña en DATABASE_URL: MiClave%40123
```

La URL debe tener esta estructura:

```env
DATABASE_URL=postgresql+psycopg://postgres:CONTRASEÑA_CODIFICADA@db:5432/combustible_db
```

### Motivo

La API estaba interpretando parte de la contraseña como si fuera el nombre del host y devolvía:

```text
Name or service not known
```

El archivo `.env` contiene datos sensibles y no debe publicarse ni subirse a un repositorio.

## 4. Corrección de compatibilidad entre Passlib y bcrypt

### Archivo modificado

- `backend/requirements.txt`

### Cambio realizado

Se fijó explícitamente la versión compatible:

```text
bcrypt==4.0.1
```

El archivo contiene actualmente:

```text
fastapi==0.115.6
uvicorn[standard]==0.34.0
sqlalchemy==2.0.36
psycopg[binary]==3.2.3
pydantic-settings==2.7.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
bcrypt==4.0.1
email-validator==2.2.0
```

### Motivo

La combinación de `passlib==1.7.4` con una versión reciente de `bcrypt` provocaba un error al generar la contraseña del usuario demo:

```text
ValueError: password cannot be longer than 72 bytes
```

Después del cambio se reconstruyó la imagen de la API y el login volvió a responder correctamente.

## 5. Creación automática de usuarios demo por rol

### Archivo modificado

- `backend/app/main.py`

### Cambio realizado

La función que creaba únicamente al administrador fue reemplazada por una función que crea tres cuentas demo si todavía no existen:

| Rol | Correo | Contraseña |
|---|---|---|
| Administrador | `admin@fueltrack.local` | `Cambiar123!` |
| Operador | `operador@fueltrack.local` | `Operador123!` |
| Supervisor | `supervisor@fueltrack.local` | `Supervisor123!` |

Las cuentas se crean durante el primer intento de login, sin duplicarlas si ya existen.

### Motivo

Permitir comprobar fácilmente el comportamiento de cada rol sin tener que insertar manualmente usuarios en PostgreSQL.

## 6. Ampliación de la interfaz web por rol

### Archivo modificado

- `frontend/src/main.jsx`

### Cambios realizados

Se reemplazó la interfaz inicial por una versión con permisos visibles según el rol:

### Administrador

Puede:

- Ver el resumen.
- Consultar operaciones.
- Registrar operaciones.
- Crear vehículos.
- Crear estaciones.
- Revisar y actualizar casos.

### Operador

Puede:

- Ver el resumen.
- Consultar operaciones.
- Registrar operaciones.

### Supervisor

Puede:

- Ver el resumen.
- Consultar operaciones.
- Crear vehículos.
- Crear estaciones.
- Revisar y actualizar casos.

### Formularios agregados

Se agregaron formularios para:

- Registrar operaciones.
- Crear vehículos.
- Crear estaciones.
- Cambiar el estado de un caso.
- Escribir la conclusión de un caso.

Los formularios llaman a la API y actualizan las tablas después de guardar.

## 7. Funciones de la API utilizadas por los formularios

La interfaz utiliza las rutas ya existentes en:

- `backend/app/main.py`

Rutas principales:

```text
POST  /api/auth/login
GET   /api/auth/me
GET   /api/dashboard
GET   /api/vehicles
POST  /api/vehicles
GET   /api/stations
POST  /api/stations
GET   /api/fuel-types
GET   /api/operations
POST  /api/operations
GET   /api/cases
PATCH /api/cases/{case_id}
```

Las rutas protegidas utilizan:

```text
Authorization: Bearer <token>
```

Los permisos se controlan en el backend, no solamente en la interfaz. Por eso un usuario no autorizado recibe un error `403` aunque intente llamar directamente a la API.

## 8. Persistencia de datos en PostgreSQL

Los formularios guardan los datos en la base de datos PostgreSQL mediante la API.

| Formulario | Tabla |
|---|---|
| Crear usuario demo | `users` |
| Crear vehículo | `vehicles` |
| Crear estación | `stations` |
| Registrar operación | `fuel_operations` |
| Crear caso automático | `review_cases` |
| Guardar razones de revisión | `case_reasons` |

La estructura está definida en:

- `database/schema.sql`

Los datos se conservan en el volumen Docker:

```text
proyecto_integrador_postgres_data
```

`docker compose down` no borra normalmente ese volumen.

No se debe ejecutar `docker compose down -v` si se desean conservar los datos.

## 9. Documentación actualizada

### Archivo modificado

- `README.md`

### Cambios realizados

Se documentaron las tres cuentas demo:

```text
admin@fueltrack.local / Cambiar123!
operador@fueltrack.local / Operador123!
supervisor@fueltrack.local / Supervisor123!
```

También se corrigió la indicación del encabezado de autorización para mostrar:

```text
Authorization: Bearer <token>
```

## 10. Comandos principales para ejecutar el sistema

Desde la carpeta raíz del proyecto:

```powershell
cd "C:\Users\Windows 11\Desktop\Proyecto_ Integrador"
```

Iniciar los servicios:

```powershell
docker compose up -d
```

Reconstruir después de cambiar dependencias o código:

```powershell
docker compose up -d --build
```

Ver el estado:

```powershell
docker compose ps
```

Abrir la aplicación:

```text
http://localhost:5173
```

Abrir la documentación de la API:

```text
http://localhost:8000/docs
```

Detener los servicios sin borrar los datos:

```powershell
docker compose down
```

## 11. Verificaciones realizadas

Se comprobó que:

- La imagen del frontend compila correctamente.
- La imagen de la API compila correctamente.
- PostgreSQL aparece como `healthy`.
- La web responde en el puerto `5173`.
- La API responde en el puerto `8000`.
- El administrador inicia como `ADMIN`.
- El operador inicia como `OPERATOR`.
- El supervisor inicia como `SUPERVISOR`.
- El login responde correctamente con HTTP `200`.

## 12. Recomendaciones antes de usar fuera del entorno local

Las credenciales incluidas son únicamente para demostración local. Antes de utilizar el sistema en otro entorno:

- Cambiar todas las contraseñas demo.
- Cambiar `SECRET_KEY`.
- Usar una contraseña segura para PostgreSQL.
- No publicar `.env`.
- Usar HTTPS.
- Crear usuarios reales con contraseñas individuales.
- Configurar copias de seguridad.
- Revisar permisos y auditoría.

