import time
import math
import os
from grove.grove_sound_sensor import GroveSoundSensor

from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import ASYNCHRONOUS

SENSOR_PORT = 2      # A2
ADC_MAX = 4095       # Resolución típica de la Base Hat (12 bits)

# --- Configuración InfluxDB v2 ---
URL    = "http://localhost:8086"
ORG    = "Raspi11"            # tu organización en InfluxDB
BUCKET = "bucket"             # tu bucket
TOKEN  = "MgfAXCYjqqsoakt5PoFizhILIasQXaqAe2ue9iuWNoRaLI264Hj8gz3qBJNsgQ_oiSTPtMkCJSrn2WbFaqL17g=="  # o tu token en texto plano


def leer_db(sensor, muestras=100, dt=0.002):
    """
    Lee varias muestras del sensor y calcula un nivel de dB relativo.
    No es un valor calibrado, pero sirve como 'más ruido / menos ruido'.
    """
    valores = []
    for _ in range(muestras):
        valores.append(sensor.sound)
        time.sleep(dt)

    v_max = max(valores)
    v_min = min(valores)
    amplitud = v_max - v_min

    if amplitud <= 0:
        return 0.0  # silencio

    # Normalizamos la amplitud a [0, 1]
    amp_norm = amplitud / ADC_MAX
    if amp_norm <= 0:
        return 0.0

    # dB relativos (logarítmico). 0 dB ≈ sin señal, 80 dB ≈ muy fuerte.
    db_rel = 20 * math.log10(amp_norm) + 80
    # Limitamos por si acaso
    db_rel = max(0.0, min(80.0, db_rel))
    return db_rel


def main():
    sensor = GroveSoundSensor(SENSOR_PORT)
    print("Midiendo sonido en dB relativos en A2 y enviando a InfluxDB (Ctrl+C para parar)")

    # Cliente InfluxDB
    client = InfluxDBClient(url=URL, token=TOKEN, org=ORG)
    write_api = client.write_api(write_options=ASYNCHRONOUS)

    try:
        while True:
            db = leer_db(sensor)
            print("Nivel de sonido: {:.1f} dB".format(db))

            # Crear punto para InfluxDB
            p = (
                Point("sound_level")            # nombre de la medida
                .tag("sensor", "sound_a2")      # etiqueta para filtrar
                .field("sound_db", float(db))   # nivel de sonido en dB relativos
            )

            # Enviar a InfluxDB
            write_api.write(bucket=BUCKET, org=ORG, record=p)

            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\nParado por el usuario.")
    finally:
        write_api.__del__()
        client.__del__()


if __name__ == '__main__':
    main()
