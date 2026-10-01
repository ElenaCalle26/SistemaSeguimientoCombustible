# Manual de Usuario - Sistema de Seguimiento de Combustible (FuelTrack)

## 1. Introducción
Bienvenido al **Sistema de Seguimiento de Combustible (FuelTrack)**. Este sistema ha sido diseñado para registrar, monitorear y analizar las operaciones de carguío de combustible en estaciones de servicio. Su objetivo principal es detectar y prevenir anomalías, como carguíos repetitivos inusuales en un mismo día (posible desvío o contrabando), asegurando un control eficiente y automatizado.

---

## 2. Acceso al Sistema
Para ingresar al sistema, siga estos pasos:
1. Abra su navegador web (se recomienda Google Chrome, Mozilla Firefox o Microsoft Edge).
2. Ingrese la dirección web proporcionada por su administrador (por ejemplo, `http://localhost:5173` en un entorno local).
3. Verá la pantalla de **Inicio de Sesión**. Ingrese su **Correo Electrónico** y **Contraseña**.
4. Haga clic en **Entrar**.

---

## 3. Roles de Usuario
El sistema se adapta a sus responsabilidades mostrando u ocultando ciertas opciones según su rol:

*   **Operador:** Personal de pista en la estación. Su tarea principal es despachar el combustible y registrar las ventas en el sistema utilizando tarjetas RFID o ingresando la placa del vehículo.
*   **Supervisor:** Encargado de una o más estaciones de servicio. Puede ver el historial de ventas, revisar casos sospechosos generados en su estación y visualizar gráficos de rendimiento.
*   **Administrador:** Tiene acceso total al sistema. Puede gestionar usuarios, crear nuevas estaciones, ver el comportamiento global de todas las sucursales y recibir alertas críticas por correo electrónico.

---

## 4. Guía para el Operador de Estación

Como operador, usted pasará la mayor parte del tiempo en la pantalla de **Operaciones**. Su responsabilidad es registrar cada venta de combustible.

### ¿Cómo registrar un carguío?
1. En el menú lateral, haga clic en **Operaciones**.
2. **Identificación del Vehículo:**
    *   **Con Tarjeta RFID/NFC:** Pídale al cliente que acerque su tarjeta o llavero NFC al lector físico de la estación. El sistema leerá automáticamente el código y cargará los datos del vehículo (Placa, Tipo, Código B-SISA) en la pantalla sin que usted tenga que escribir nada.
    *   **Manual:** Si el cliente no tiene tarjeta, puede buscar el vehículo escribiendo su número de **Placa** en el buscador desplegable.
3. Seleccione el tipo de **Combustible** (Gasolina, Diésel, GNV).
4. Ingrese la cantidad en **Litros** despachados.
5. Haga clic en el botón **Registrar Operación**.
6. Aparecerá un mensaje verde de éxito (Toast) indicando que el registro se ha guardado correctamente.

*Nota: El campo de "Estación" se llena automáticamente con la estación en la que usted está trabajando. Usted no puede registrar ventas para otras gasolineras.*

---

## 5. Guía para el Supervisor

Como Supervisor, su objetivo es monitorear el comportamiento de las estaciones a su cargo.

### 5.1. Panel de Control (Resumen)
Al iniciar sesión, verá gráficos e indicadores clave de rendimiento (KPIs):
*   Total de operaciones del día.
*   Volumen total de combustible despachado (en litros).
*   Cantidad de Alertas generadas por comportamientos inusuales.
*   Un gráfico con el flujo de ventas por hora.

### 5.2. Revisión de Casos y Alertas
El sistema detecta automáticamente si un vehículo carga combustible múltiples veces de forma inusual (por ejemplo, 3 o más veces en un lapso corto).
1. Vaya a la sección **Alertas** o **Casos**.
2. Verá una lista de vehículos marcados con banderas (Ej: *Prioridad Alta, Media*).
3. Puede hacer clic en un caso para ver el detalle de los carguíos de ese vehículo y, si procede, tomar medidas (como notificar a la ANH).

### 5.3. Historial de Operaciones
En la pestaña **Operaciones**, puede ver una tabla con todo el historial de ventas de su estación, quién lo despachó, a qué hora y a qué vehículo.

---

## 6. Guía para el Administrador

El Administrador tiene herramientas adicionales de gestión global del sistema.

### 6.1. Gestión de Usuarios
Para agregar a un nuevo empleado (Operador o Supervisor) o cambiar su correo:
1. Vaya a la pestaña **Usuarios**.
2. Verá la lista de todo el personal registrado.
3. Para crear uno nuevo, haga clic en **Añadir Usuario** (o botón similar), asigne su correo electrónico, una contraseña segura y el Rol correspondiente.
4. Si el usuario es un Operador, asegúrese de asignarle la Estación de Servicio correcta.

### 6.2. Notificaciones por Correo Electrónico
El sistema está configurado para enviarle un correo electrónico de forma automática cuando ocurre una infracción grave (por ejemplo, el 3er carguío de un mismo vehículo en un solo día).
*   Asegúrese de que su correo electrónico en la pestaña **Usuarios** esté actualizado para no perder estas alertas.

---

## 7. Preguntas Frecuentes y Solución de Problemas

**¿Qué hago si el lector RFID no lee la tarjeta?**
Asegúrese de que el lector esté conectado y encendido. Intente acercar la tarjeta nuevamente y espere 2 segundos. Si sigue sin funcionar, puede ingresar la placa del vehículo de forma manual seleccionándola en la lista.

**Apareció un cartel rojo diciendo "Error de Conexión". ¿Qué significa?**
Esto indica que el sistema perdió comunicación con el servidor central. Verifique su conexión a internet (o red local). Si el problema persiste, contacte al Administrador del sistema.

**¿Puedo corregir una operación si me equivoqué en la cantidad de litros?**
Por motivos de seguridad y auditoría, los operadores no pueden eliminar ni modificar un carguío una vez guardado. Si cometió un error, notifique inmediatamente a su Supervisor para que quede constancia del incidente.

**Olvidé mi contraseña, ¿cómo entro?**
Debe solicitar a su Administrador de sistema que restablezca o actualice su contraseña desde el panel de control de usuarios.

---
*Fin del documento.*
