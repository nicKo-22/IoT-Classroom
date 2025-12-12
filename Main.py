# main.py

import time
import threading
import os
import signal
from datetime import datetime

from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import ASYNCHRONOUS

from Gas_Sensor import loop_gas
from Light_Sensor import loop_light
from ServoUltrasonic_Sensor import loop_servoUltrasonic
from Sound_Sensor import loop_sound
from TempHum_Sensor import loop_tempHum

from DocumentGenerator import generar_informe_sensores

import mysql.connector

# ============================
#  CONFIGURACIÓN INFLUXDB
# ============================
INFLUX_URL = "http://localhost:8086"
INFLUX_ORG = "Raspi11"
INFLUX_BUCKET = "bucket"
INFLUX_TOKEN = "MgfAXCYjqqsoakt5PoFizhILIasQXaqAe2ue9iuWNoRaLI264Hj8gz3qBJNsgQ_oiSTPtMkCJSrn2WbFaqL17g=="  # cambia esto por el tuyo

# ============================
#  CONFIGURACIÓN MySQL
# ============================
DB_CONFIG = {
    "host": "10.172.117.157",   # EJEMPLO: "10.172.117.50"
    "user": "raspi11",
    "password": "adminRaspi11",
    "database": "IoTClassroom",
}

# ============================
#  CONTROL DE PARADA
# ============================

stop_requested = False


def handle_stop(signum, frame):
    """
    Manejador de señales de parada.
    Marca la bandera para salir del bucle principal y generar el informe.
    """
    global stop_requested
    if not stop_requested:
        print(f"\nSeñal {signum} recibida. Parando sensores y preparando informe...")
    stop_requested = True


# Registramos manejadores para varias señales (según disponibilidad)
for sig_name in ("SIGINT", "SIGTERM", "SIGHUP"):
    if hasattr(signal, sig_name):
        signal.signal(getattr(signal, sig_name), handle_stop)


# ============================
#  FUNCIONES MySQL
# ============================

def guardar_informe_en_mysql(html_path: str,
                             plots_dir: str,
                             nombre_informe: str = "informe_sensores") -> None:
    """
    Guarda el informe HTML y todas las imágenes de la carpeta 'plots' en MySQL.

    Tablas usadas:

        CREATE TABLE informes (
            id INT AUTO_INCREMENT PRIMARY KEY,
            created_at DATETIME NOT NULL,
            nombre VARCHAR(255) NOT NULL,
            html LONGBLOB NOT NULL
        );

        CREATE TABLE informe_imagenes (
            id INT AUTO_INCREMENT PRIMARY KEY,
            informe_id INT NOT NULL,
            filename VARCHAR(255) NOT NULL,
            image LONGBLOB NOT NULL,
            FOREIGN KEY (informe_id) REFERENCES informes(id) ON DELETE CASCADE
        );
    """

    if not os.path.isfile(html_path):
        print(f"[MySQL] ERROR: No se encuentra el HTML en {html_path}")
        return

    # Leer el HTML como binario
    with open(html_path, "rb") as f:
        html_data = f.read()

    # Conexión a MySQL
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    try:
        # 1) Insertar el informe
        insert_informe_sql = """
            INSERT INTO informes (created_at, nombre, html)
            VALUES (%s, %s, %s)
        """
        now = datetime.now()
        cursor.execute(insert_informe_sql, (now, nombre_informe, html_data))
        informe_id = cursor.lastrowid

        print(f"[MySQL] Informe insertado con id={informe_id}")

        # 2) Insertar imágenes asociadas
        if os.path.isdir(plots_dir):
            for filename in os.listdir(plots_dir):
                full_path = os.path.join(plots_dir, filename)
                if not os.path.isfile(full_path):
                    continue

                # Opcional: filtrar extensiones de imagen
                if not filename.lower().endswith((".png", ".jpg", ".jpeg", ".gif")):
                    continue

                with open(full_path, "rb") as img_f:
                    img_data = img_f.read()

                insert_imagen_sql = """
                    INSERT INTO informe_imagenes (informe_id, filename, image)
                    VALUES (%s, %s, %s)
                """
                cursor.execute(insert_imagen_sql, (informe_id, filename, img_data))
                print(f"[MySQL]   Imagen '{filename}' guardada.")
        else:
            print(f"[MySQL] AVISO: No existe el directorio de plots: {plots_dir}")

        conn.commit()
        print("[MySQL] Informe e imágenes guardados correctamente.")

    except Exception as e:
        conn.rollback()
        print(f"[MySQL] ERROR guardando informe: {e}")

    finally:
        cursor.close()
        conn.close()


# ============================
#  MAIN
# ============================

def main():
    global stop_requested

    # Crear cliente de InfluxDB (el mismo que usará el generador de documento)
    client = InfluxDBClient(
        url=INFLUX_URL,
        token=INFLUX_TOKEN,
        org=INFLUX_ORG,
    )

    write_api = client.write_api(write_options=ASYNCHRONOUS)

    # Lanzar hilos de sensores
    threads = [
        threading.Thread(
            target=loop_gas,
            args=(write_api, INFLUX_BUCKET, INFLUX_ORG),
            daemon=True,
        ),
        threading.Thread(
            target=loop_light,
            args=(write_api, INFLUX_BUCKET, INFLUX_ORG),
            daemon=True,
        ),
        threading.Thread(
            target=loop_servoUltrasonic,
            args=(write_api, INFLUX_BUCKET, INFLUX_ORG),
            daemon=True,
        ),
        threading.Thread(
            target=loop_sound,
            args=(write_api, INFLUX_BUCKET, INFLUX_ORG),
            daemon=True,
        ),
        threading.Thread(
            target=loop_tempHum,
            args=(write_api, INFLUX_BUCKET, INFLUX_ORG),
            daemon=True,
        ),
    ]

    for t in threads:
        t.start()

    print("Sensores ejecutándose. Pulsa Ctrl + C (o cierra la sesión) para parar y generar el informe...")

    try:
        # Bucle principal para mantener el programa vivo
        while not stop_requested:
            time.sleep(1)

    except KeyboardInterrupt:
        # Por si Ctrl + C llega como KeyboardInterrupt directamente
        handle_stop(signal.SIGINT, None)

    finally:
        # Si se ha pedido parada, generamos informe y guardamos
        if stop_requested:
            print("\nGenerando informe analítico...")
            ruta_informe = generar_informe_sensores(
                client=client,
                bucket=INFLUX_BUCKET,
                org=INFLUX_ORG,
                horas_rango=24,               # cambia el rango de horas si quieres
                output_html="informe_sensores.html",
            )
            print(f"Informe generado en: {ruta_informe}")

            # === Guardar en MySQL ===
            html_path = ruta_informe
            # Asumimos que la carpeta 'plots' está en el mismo directorio que el HTML
            plots_dir = os.path.join(os.path.dirname(ruta_informe), "plots")

            print("Guardando informe e imágenes en MySQL...")
            guardar_informe_en_mysql(
                html_path=html_path,
                plots_dir=plots_dir,
                nombre_informe="informe_sensores",
            )

        # Cerrar cliente de InfluxDB al salir
        client.close()
        print("Cliente InfluxDB cerrado. Fin del programa.")


if __name__ == "__main__":
    main()
