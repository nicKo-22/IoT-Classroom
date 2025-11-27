import time
from grove.adc import ADC
from influxdb_client import Point

GAS_CHANNEL = 4      # A4
ADC_MAX = 4095       # resolución típica del ADC de la Base Hat (12 bits)


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


def loop_gas(write_api, bucket, org):
    adc = ADC()

    print("Midiendo Gas Sensor v1.5 (MQ2) en A4 y enviando a InfluxDB (loop_gas)")
    try:
        while True:
            valor_crudo, nivel_pct = leer_gas(adc)
            print("Gas crudo: {:.0f} | Nivel relativo: {} %".format(valor_crudo, nivel_pct))

            point = (
                Point("gas_mq2")
                .tag("sensor", "mq2")
                .field("gas_raw", float(valor_crudo))
                .field("gas_level_pct", int(nivel_pct))
            )

            try:
                write_api.write(
                    bucket=bucket,
                    org=org,
                    record=point,
                )
            except Exception as e:
                print("Error enviando a InfluxDB (gas):", e)

            time.sleep(0.5)

    except Exception as e:
        print("Error en loop_gas:", e)
