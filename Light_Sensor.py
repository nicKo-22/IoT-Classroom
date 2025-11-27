import time
from grove.adc import ADC
from influxdb_client import Point

SENSOR_CHANNEL = 0   # A0
ADC_MAX = 4095       # resolución típica del ADC de la Base Hat (12 bits)


def loop_light(write_api, bucket, org):
    # Crear objeto ADC del Grove Base Hat
    adc = ADC()

    print("Leyendo Light Sensor v1.2 en A0 y enviando a InfluxDB (loop_light)")
    try:
        while True:
            try:
                # Leer el canal analógico 0 (A0) → 0–4095 normalmente
                value = adc.read(SENSOR_CHANNEL)
                print("Valor crudo A0:", value, flush=True)

                # Pasar a % aprox
                luz_pct = int(value / 40.95)  # 0–100 aprox
                luz_pct = max(0, min(100, luz_pct))
                print("Luz aproximada: {} %".format(luz_pct), flush=True)

                print("-" * 30, flush=True)

                # Crear punto para InfluxDB
                p = (
                    Point("light_sensor")
                    .tag("sensor", "light_v1_2")
                    .field("light_raw", float(value))
                    .field("light_level_pct", int(luz_pct))
                )

                # Enviar a InfluxDB
                write_api.write(
                    bucket=bucket,
                    org=org,
                    record=p,
                )

                time.sleep(1)

            except Exception as e:
                print("Error leyendo ADC (light):", e, flush=True)
                time.sleep(1)

    except Exception as e:
        print("Error en loop_light:", e)
