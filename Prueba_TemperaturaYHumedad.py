import time
import os
from seeed_dht import DHT
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import ASYNCHRONOUS

INFLUX_URL    = "http://localhost:8086"
INFLUX_ORG    = "Raspi11"
INFLUX_BUCKET = "bucket"
INFLUX_TOKEN  = "MgfAXCYjqqsoakt5PoFizhILIasQXaqAe2ue9iuWNoRaLI264Hj8gz3qBJNsgQ_oiSTPtMkCJSrn2WbFaqL17g=="

TEMPHUM_PIN = 5  # D5

def main():
    sensor = DHT("11", TEMPHUM_PIN)

    client = InfluxDBClient(
        url=INFLUX_URL,
        token=INFLUX_TOKEN,
        org=INFLUX_ORG,
    )
    write_api = client.write_api(write_options=ASYNCHRONOUS)

    print("Midiendo temperatura y humedad (Ctrl+C para parar)")
    try:
        while True:
            humi, temp = sensor.read()

            if humi is None or temp is None:
                print("Lectura inválida del sensor, reintentando...")
                time.sleep(0.5)
                continue

            print(f"temperature {temp} C, humidity {humi} %")

            point = (
                Point("tempHum")
                .tag("sensor", "dht11")
                .field("temperature", float(temp))
                .field("humidity", float(humi))
            )

            try:
                write_api.write(
                    bucket=INFLUX_BUCKET,
                    org=INFLUX_ORG,
                    record=point,
                )
            except Exception as e:
                print("Error enviando a InfluxDB:", e)

            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\nParado por el usuario.")

if __name__ == '__main__':
    main()
