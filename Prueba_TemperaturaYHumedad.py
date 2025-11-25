import time
from datetime import datetime
from seeed_dht import DHT

from influxdb_client import InfluxDBClient, Point, WritePrecision
import os

# ----- CONFIGURACIÓN INFLUXDB v2 -----
# Puedes dejar estas variables aquí en el código
INFLUX_URL = "http://http://10.172.117.124/:8086"
INFLUX_TOKEN = "MgfAXCYjqqsoakt5PoFizhILIasQXaqAe2ue9iuWNoRaLI264Hj8gz3qBJNsgQ_oiSTPtMkCJSrn2WbFaqL17g=="  # o pon el token directamente como string
INFLUX_ORG = "Raspi11"
INFLUX_BUCKET = "bucket"


def main():
    # Sensor DHT11 en pin 5
    TEMPHUM_PIN = 5
    sensor = DHT('11', TEMPHUM_PIN)

    # Cliente de InfluxDB
    client = InfluxDBClient(
        url=INFLUX_URL,
        token=INFLUX_TOKEN,
        org=INFLUX_ORG
    )
    write_api = client.write_api()

    while True:
        humi, temp = sensor.read()

        # A veces el DHT falla y devuelve None
        if humi is None or temp is None:
            print("Lectura inválida del sensor, reintentando...")
            time.sleep(0.5)
            continue

        print(f"temperature {temp} C, humidity {humi} %")

        # Creamos el punto para Influx
        point = (
            Point("aula")            # nombre del measurement (puedes cambiarlo)
            .tag("sensor", "dht11")  # etiqueta opcional
            .field("temperature", float(temp))
            .field("humidity", float(humi))
            .time(datetime.utcnow(), WritePrecision.MS)
        )

        try:
            write_api.write(
                bucket=INFLUX_BUCKET,
                org=INFLUX_ORG,
                record=point
            )
            # print("Dato enviado a Influx")
        except Exception as e:
            print("Error enviando a InfluxDB:", e)

        # Enviar cada 0.1 segundos
        time.sleep(0.5)


if __name__ == '__main__':
    main()
