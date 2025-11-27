import time
import RPi.GPIO as GPIO
from grove.grove_ultrasonic_ranger import GroveUltrasonicRanger
from influxdb_client import Point

# Sensor de ultrasonidos en D16
ULTRASONIC_PORT = 16

# Servo EN BCM 16 (D16 en la Grove Base Hat)
SERVO_PIN = 18        # <- corregido a 16
ANGULO_MAX = 120      # grados

# Umbral de distancia para considerar que hay obstáculo (en cm)
DIST_THRESHOLD_CM = 100.0

# Nº de lecturas que se usan para calcular el porcentaje
NUM_MUESTRAS = 40

# Estado global del servo (para no reiniciar en cada medición)
angulo_actual = 0
direccion_actual = 1   # 1: hacia ANGULO_MAX, -1: hacia 0


def angulo_a_duty(angle):
    """Convierte ángulo (0-180) a ciclo de trabajo aproximado para servo estándar."""
    return 2.5 + (angle / 180.0) * 10.0


def medir_porcentaje_ocupado(sensor,
                             pwm,
                             n_muestras=NUM_MUESTRAS,
                             threshold=DIST_THRESHOLD_CM,
                             delay=0.05,
                             paso=5):
    """
    Mueve el servo mientras toma n_muestras del sensor y calcula:
      - porcentaje de lecturas con obstáculo (distancia < threshold)
      - nº de lecturas bloqueadas
      - nº total de lecturas válidas

    El servo oscila continuamente entre 0º y ANGULO_MAX, SIN reiniciar a 0 cada vez.
    """
    global angulo_actual, direccion_actual

    total = 0
    bloqueadas = 0

    while total < n_muestras:
        # Mover servo al ángulo actual
        pwm.ChangeDutyCycle(angulo_a_duty(angulo_actual))
        time.sleep(delay)

        # Leer distancia
        dist = sensor.get_distance()  # en cm
        if dist > 0:                  # lectura válida
            total += 1
            if dist < threshold:
                bloqueadas += 1

        # Actualizar ángulo para siguiente muestra
        angulo_actual += direccion_actual * paso

        if angulo_actual >= ANGULO_MAX:
            angulo_actual = ANGULO_MAX
            direccion_actual = -1
        elif angulo_actual <= 0:
            angulo_actual = 0
            direccion_actual = 1

    if total == 0:
        return 0.0, 0, 0

    porcentaje = (bloqueadas / total) * 100.0
    return porcentaje, bloqueadas, total


def loop_servoUltrasonic(write_api, bucket, org):
    global angulo_actual, direccion_actual

    sensor = GroveUltrasonicRanger(ULTRASONIC_PORT)

    # Configuración del servo
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(SERVO_PIN, GPIO.OUT)
    pwm = GPIO.PWM(SERVO_PIN, 50)  # 50 Hz

    # Ir a 0º al principio
    angulo_actual = 0
    direccion_actual = 1
    pwm.start(angulo_a_duty(0))
    time.sleep(1)

    print("Calculando porcentaje de campo obstaculizado con servo y enviando a InfluxDB (loop_ultrasonic)")
    try:
        while True:
            porcentaje, bloqueadas, total = medir_porcentaje_ocupado(sensor, pwm)

            print(
                f"Campo obstaculizado: {porcentaje:.1f}%  "
                f"(lecturas bloqueadas {bloqueadas}/{total})"
            )

            p = (
                Point("ultrasonic_occupancy")
                .tag("sensor", "ultrasonic_d16")
                .field("occupancy_pct", float(porcentaje))
                .field("blocked_readings", int(bloqueadas))
                .field("total_readings", int(total))
            )

            try:
                write_api.write(
                    bucket=bucket,
                    org=org,
                    record=p,
                )
            except Exception as e:
                print("Error enviando a InfluxDB (ultrasonic):", e)

            # Si quieres que no haya pausas casi, puedes bajar este sleep
            time.sleep(0.1)

    except Exception as e:
        print("Error en loop_ultrasonic:", e)
    finally:
        pwm.stop()
        GPIO.cleanup()
