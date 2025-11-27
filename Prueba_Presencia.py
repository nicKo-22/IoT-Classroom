import time
import os
from grove.grove_ultrasonic_ranger import GroveUltrasonicRanger

from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import ASYNCHRONOUS

# Sensor de ultrasonidos en D16
ULTRASONIC_PORT = 16

# Umbral de distancia para considerar que hay obstáculo (en cm)
DIST_THRESHOLD_CM = 100.0   # cambia esto si quieres más/menos sensibilidad

# Nº de lecturas que se usan para calcular el porcentaje
NUM_MUESTRAS = 40          # ajusta según lo rápido que gire tu servo

# --- Configuración InfluxDB v2 ---
URL    = "http://localhost:8086"
ORG    = "Raspi11"            # tu organización
BUCKET = "bucket"             # tu bucket
TOKEN  = "MgfAXCYjqqsoakt5PoFizhILIasQXaqAe2ue9iuWNoRaLI264Hj8gz3qBJNsgQ_oiSTPtMkCJSrn2WbFaqL17g=="  # o token en texto plano (menos seguro)


def medir_porcentaje_ocupado(sensor,
                             n_muestras=NUM_MUESTRAS,
                             threshold=DIST_THRESHOLD_CM,
                             delay=0.05):
    """
    Toma n_muestras lecturas del sensor y calcula:
      - porcentaje de lecturas con obstáculo (distancia < threshold)
      - nº de lecturas bloqueadas
      - nº total de lecturas válidas
    """
    total = 0
    bloqueadas = 0

    for _ in range(n_muestras):
        dist = sensor.get_distance()  # en cm

        if dist > 0:                  # lectura válida
            total += 1
            if dist < threshold:
                bloqueadas += 1

        time.sleep(delay)

    if total == 0:
        return 0.0, 0, 0

    porcentaje = (bloqueadas / total) * 100.0
    return porcentaje, bloqueadas, total


def main():
    sensor = GroveUltrasonicRanger(ULTRASONIC_PORT)

    # Cliente InfluxDB
    client = InfluxDBClient(url=URL, token=TOKEN, org=ORG)
    write_api = client.write_api(write_options=ASYNCHRONOUS)

    print("Calculando porcentaje de campo obstaculizado y enviando a InfluxDB (Ctrl+C para parar)")
    try:
        while True:
            porcentaje, bloqueadas, total = medir_porcentaje_ocupado(sensor)

            print(
                f"Campo obstaculizado: {porcentaje:.1f}%  "
                f"(lecturas bloqueadas {bloqueadas}/{total})"
            )

            # Crear punto para InfluxDB
            p = (
                Point("ultrasonic_occupancy")            # nombre de la medida
                .tag("sensor", "ultrasonic_d16")         # etiqueta para filtrar
                .field("occupancy_pct", float(porcentaje))
                .field("blocked_readings", int(bloqueadas))
                .field("total_readings", int(total))
            )

            # Enviar a InfluxDB
            write_api.write(bucket=BUCKET, org=ORG, record=p)

            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\nParado por el usuario.")
    finally:
        write_api.__del__()
        client.__del__()


if __name__ == "__main__":
    main()
