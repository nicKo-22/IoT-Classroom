import time
import os
from grove.adc import ADC

from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import ASYNCHRONOUS

GAS_CHANNEL = 4      # A4
ADC_MAX = 4095       # resolución típica del ADC de la Base Hat (12 bits)

# --- Configuración InfluxDB v2 ---
URL    = "http://localhost:8086"
ORG    = "Raspi11"            # pon aquí tu ORG
BUCKET = "bucket"             # pon aquí tu bucket
TOKEN  = "MgfAXCYjqqsoakt5PoFizhILIasQXaqAe2ue9iuWNoRaLI264Hj8gz3qBJNsgQ_oiSTPtMkCJSrn2WbFaqL17g=="  # o tu token en texto plano (menos seguro)


def leer_gas(adc, channel=GAS_CHANNEL, muestras=50, dt=0.02):
    """
    Lee varias muestras del canal analógico y calcula:
      - valor medio crudo
      - un nivel relativo en %
    No son ppm reales, solo un indicador de 'más o menos gas'.
    """
    valores = []
    for _ in range(muestras):
        valor = adc.read(channel)
        valores.append(valor)
        time.sleep(dt)

    media = sum(valores) / len(valores)

    # Lo pasamos a un % aproximado 0–100
    nivel_pct = int((media / ADC_MAX) * 100)
    nivel_pct = max(0, min(100, nivel_pct))  # limitar entre 0 y 100

    return media, nivel_pct


def main():
    adc = ADC()

    # Cliente InfluxDB
    client = InfluxDBClient(url=URL, token=TOKEN, org=ORG)
    write_api = client.write_api(write_options=ASYNCHRONOUS)

    print("Midiendo Gas Sensor v1.5 (MQ2) en A4 y enviando a InfluxDB (Ctrl+C para parar)")
    try:
        while True:
            valor_crudo, nivel_pct = leer_gas(adc)
            print("Gas crudo: {:.0f} | Nivel relativo: {} %".format(valor_crudo, nivel_pct))

            # Crear punto para InfluxDB
            p = (
                Point("gas_mq2")                # nombre de la medida
                .tag("sensor", "mq2")           # etiqueta para filtrar
                .field("gas_raw", float(valor_crudo))
                .field("gas_level_pct", int(nivel_pct))
            )

            # Enviar a InfluxDB
            write_api.write(bucket=BUCKET, org=ORG, record=p)

            time.sleep(0.5)  # igual que en tu código original

    except KeyboardInterrupt:
        print("\nParado por el usuario.")
    finally:
        # Cerrar cliente
        write_api.__del__()
        client.__del__()


if __name__ == "__main__":
    main()
