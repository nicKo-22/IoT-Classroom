import time
import math
from grove.grove_sound_sensor import GroveSoundSensor
from influxdb_client import Point

SENSOR_PORT = 2      # A2
ADC_MAX = 4095       # Resolución típica de la Base Hat (12 bits)


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


def loop_sound(write_api, bucket, org):
    sensor = GroveSoundSensor(SENSOR_PORT)
    print("Midiendo sonido en dB relativos en A2 y enviando a InfluxDB (loop_sound)")

    try:
        while True:
            db = leer_db(sensor)
            print("Nivel de sonido: {:.1f} dB".format(db))

            p = (
                Point("sound_level")
                .tag("sensor", "sound_a2")
                .field("sound_db", float(db))
            )

            try:
                write_api.write(
                    bucket=bucket,
                    org=org,
                    record=p,
                )
            except Exception as e:
                print("Error enviando a InfluxDB (sound):", e)

            time.sleep(0.5)

    except Exception as e:
        print("Error en loop_sound:", e)
