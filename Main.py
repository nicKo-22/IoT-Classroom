# main.py

import time
import os
import threading

from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import ASYNCHRONOUS

from Gas_Sensor import loop_gas
from Light_Sensor import loop_light
from ServoUltrasonic_Sensor import loop_servoUltrasonic
from Sound_Sensor import loop_sound
from TempHum_Sensor import loop_tempHum


INFLUX_URL    = "http://localhost:8086"
INFLUX_ORG    = "Raspi11"
INFLUX_BUCKET = "bucket"
INFLUX_TOKEN  = "MgfAXCYjqqsoakt5PoFizhILIasQXaqAe2ue9iuWNoRaLI264Hj8gz3qBJNsgQ_oiSTPtMkCJSrn2WbFaqL17g=="  # o pon tu token en texto plano


def main():
    client = InfluxDBClient(
        url=INFLUX_URL,
        token=INFLUX_TOKEN,
        org=INFLUX_ORG,
    )
    write_api = client.write_api(write_options=ASYNCHRONOUS)

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

    print("Sensores en marcha (Ctrl+C para parar main.py)")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nParando main.py...")
    finally:
        write_api.__del__()
        client.__del__()


if __name__ == "__main__":
    main()
