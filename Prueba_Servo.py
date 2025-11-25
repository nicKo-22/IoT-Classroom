import RPi.GPIO as GPIO
import time

# D16 en la Grove Base Hat corresponde al pin BCM 16
SERVO_PIN = 18       # BCM 16
ANGULO_MAX = 120     # grados

# Convierte ángulo (0-180) a ciclo de trabajo para un servo estándar
def angulo_a_duty(angle):
    # Aproximación típica: 0º -> ~2.5, 180º -> ~12.5
    return 2.5 + (angle / 180.0) * 10.0

def main():
    # Usamos numeración BCM (no la física)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(SERVO_PIN, GPIO.OUT)

    # PWM a 50 Hz (servo estándar)
    pwm = GPIO.PWM(SERVO_PIN, 50)
    pwm.start(angulo_a_duty(0))   # empezamos en 0º
    time.sleep(1)

    print("Moviendo el servo entre 0º y 120º (Ctrl+C para parar)")

    try:
        while True:
            # 0º -> 120º
            for ang in range(0, ANGULO_MAX + 1, 5):
                pwm.ChangeDutyCycle(angulo_a_duty(ang))
                time.sleep(0.05)

            time.sleep(0.5)

            # 120º -> 0º
            for ang in range(ANGULO_MAX, -1, -5):
                pwm.ChangeDutyCycle(angulo_a_duty(ang))
                time.sleep(0.05)

            time.sleep(0.5)

    except KeyboardInterrupt:
        # Si paras con Ctrl+C, limpiamos
        print("\nParando y liberando GPIO...")
    finally:
        pwm.stop()
        GPIO.cleanup()

if __name__ == "__main__":
    main()
