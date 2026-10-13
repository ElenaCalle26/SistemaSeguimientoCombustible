"""
Puente Serial USB para FuelTrack
Lee datos RFID enviados por el ESP32 a través del cable USB y los reenvía
al endpoint local del backend (/api/rfid/read).
"""

import sys
import glob
import time
import requests

try:
    import serial
except ImportError:
    print("Error: falta instalar 'pyserial'. Ejecuta: pip install pyserial requests")
    sys.exit(1)

URL_BACKEND = "http://localhost:8000/api/rfid/read"
BAUD_RATE = 115200


def detectar_puerto():
    """Detecta automáticamente el puerto COM o /dev/ttyUSB* / /dev/ttyACM*"""
    if len(sys.argv) > 1:
        return sys.argv[1]

    # En Linux
    puertos_linux = glob.glob("/dev/ttyUSB*") + glob.glob("/dev/ttyACM*")
    if puertos_linux:
        return puertos_linux[0]

    # En Windows
    for i in range(1, 20):
        nombre = f"COM{i}"
        try:
            s = serial.Serial(nombre)
            s.close()
            return nombre
        except (OSError, serial.SerialException):
            pass

    return "/dev/ttyUSB0" if sys.platform.startswith("linux") else "COM3"


def main():
    puerto = detectar_puerto()
    print("=" * 60)
    print("  PUENTE SERIAL USB - SISTEMA FUELTRACK")
    print(f"  Puerto seleccionado: {puerto}")
    print(f"  Velocidad: {BAUD_RATE} baudios")
    print(f"  Destino Backend: {URL_BACKEND}")
    print("=" * 60)

    try:
        ser = serial.Serial(puerto, BAUD_RATE, timeout=1)
        time.sleep(2)
        print(f"\n[OK] Conectado exitosamente al ESP32 por USB en {puerto}.")
        print("[INFO] Esperando lectura de tarjeta RFID...\n")
    except Exception as e:
        print(f"\n[ERROR] No se pudo abrir el puerto {puerto}: {e}")
        print("Sugerencias:")
        print("  1. Verifica que el Monitor Serie de Arduino esté cerrado.")
        print("  2. En Linux, si da 'Permission denied', ejecuta:")
        print("     sudo usermod -a -G dialout $USER")
        print("     o ejecuta: sudo python3 puente_usb.py")
        print(f"  3. Puedes especificar el puerto manualmente: python3 puente_usb.py {puerto}")
        sys.exit(1)

    while True:
        try:
            linea = ser.readline().decode("utf-8", errors="ignore").strip()

            if not linea or linea.startswith("[LOG]"):
                if linea.startswith("[LOG]"):
                    print(f"  {linea}")
                continue

            # Detectar si es el JSON enviado por el ESP32
            if linea.startswith("{") and linea.endswith("}"):
                print(f"\n[TARJETA LEIDA] Payload recibido por cable: {linea}")
                headers = {"Content-Type": "application/json"}
                
                try:
                    res = requests.post(URL_BACKEND, data=linea, headers=headers, timeout=5)
                    if res.status_code == 200:
                        datos = res.json()
                        msg = datos.get("message", "Operación exitosa")
                        veh = datos.get("vehicle", {})
                        placa = veh.get("plate", "N/A")
                        cupo = veh.get("remaining_quota", "N/A")
                        print(f"  -> [200 OK] Backend: {msg}")
                        print(f"  -> Vehículo: {placa} | Saldo restante: {cupo} L")
                    else:
                        print(f"  -> [HTTP {res.status_code}] Error del Servidor: {res.text}")
                except requests.exceptions.RequestException as req_err:
                    print(f"  -> [ERROR DE CONEXION] No se pudo conectar a {URL_BACKEND}: {req_err}")

                print("-" * 60)

        except KeyboardInterrupt:
            print("\nDeteniendo puente serial USB...")
            ser.close()
            break
        except Exception as err:
            print(f"[ERROR] {err}")


if __name__ == "__main__":
    main()
