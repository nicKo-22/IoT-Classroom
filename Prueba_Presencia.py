import time
from grove.grove_ultrasonic_ranger import GroveUltrasonicRanger

# Sensor de ultrasonidos en D16
ULTRASONIC_PORT = 16

# Umbral de distancia para considerar que hay obstáculo (en cm)
DIST_THRESHOLD_CM = 100.0   # cambia esto si quieres más/menos sensibilidad

# Nº de lecturas que se usan para calcular el porcentaje
NUM_MUESTRAS = 40          # ajusta según lo rápido que gire tu servo


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

    print("Calculando porcentaje de campo obstaculizado (Ctrl+C para parar)")
    while True:
        porcentaje, bloqueadas, total = medir_porcentaje_ocupado(sensor)
        print(f"Campo obstaculizado: {porcentaje:.1f}%  "
              f"(lecturas bloqueadas {bloqueadas}/{total})")
        time.sleep(0.5)


if __name__ == "__main__":
    main()
