import time
import os
from grove.adc import ADC

from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import ASYNCHRONOUS

# --- Configuración InfluxDB v2 ---
URL    = "http://localhost:8086"
ORG    = "Raspi11"            # tu organización en InfluxDB
BUCKET = "bucket"             # tu bucket
TOKEN  = "MgfAXCYjqqsoakt5PoFizhILIasQXaqAe2ue9iuWNoRaLI264Hj8gz3qBJNsgQ_oiSTPtMkCJSrn2WbFaqL17g=="  # o tu token en texto plano (menos seguro)

def main():
    # Crear objeto ADC del Grove Base Hat
    adc = ADC()

    # Cliente InfluxDB
    client = InfluxDBClient(url=URL, token=TOKEN, org=ORG)
    write_api = client.write_api(write_options=ASYNCHRONOUS)

    print("Leyendo Light Sensor v1.2 en A0 y enviando a InfluxDB (Ctrl+C para parar)")
    try:
        while True:
            try:
                # Leer el canal analógico 0 (A0) → 0–4095 normalmente
                value = adc.read(0)
                print("Valor crudo A0:", value, flush=True)

                # Pasar a % aprox
                luz_pct = int(value / 40.95)  # 0–100 aprox
                luz_pct = max(0, min(100, luz_pct))
                print("Luz aproximada: {} %".format(luz_pct), flush=True)

                print("-" * 30, flush=True)

                # Crear punto para InfluxDB
                p = (
                    Point("light_sensor")                 # nombre de la medida
                    .tag("sensor", "light_v1_2")         # etiqueta para filtrar
                    .field("light_raw", float(value))    # valor crudo ADC
                    .field("light_level_pct", int(luz_pct))  # nivel en %
                )

                # Enviar a InfluxDB
                write_api.write(bucket=BUCKET, org=ORG, record=p)

                time.sleep(1)

            except Exception as e:
                print("Error leyendo ADC:", e, flush=True)
                time.sleep(1)

    except KeyboardInterrupt:
        print("\nParado por el usuario.")
    finally:
        write_api.__del__()
        client.__del__()


if __name__ == "__main__":
    main()
