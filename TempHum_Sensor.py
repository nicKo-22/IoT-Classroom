import time
from seeed_dht import DHT
from influxdb_client import Point

TEMPHUM_PIN = 5  # D5


def loop_tempHum(write_api, bucket, org):
    sensor = DHT("11", TEMPHUM_PIN)

    print("Midiendo temperatura y humedad (loop_tempHum)")
    try:
        while True:
            humi, temp = sensor.read()

            if humi is None or temp is None:
                print("Lectura inválida del sensor, reintentando...")
                time.sleep(0.5)
                continue

            print(f"temperature {temp} C, humidity {humi} %")

            point = (
                Point("tempHum")          # mismo measurement que tenías
                .tag("sensor", "dht11")
                .field("temperature", float(temp))
                .field("humidity", float(humi))
            )

            try:
                write_api.write(
                    bucket=bucket,
                    org=org,
                    record=point,
                )
            except Exception as e:
                print("Error enviando a InfluxDB (tempHum):", e)

            time.sleep(0.5)

    except Exception as e:
        print("Error en loop_tempHum:", e)
