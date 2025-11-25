import time
from grove.adc import ADC

def main():
    # Crear objeto ADC del Grove Base Hat
    adc = ADC()

    print("Leyendo Light Sensor v1.2 en A0 (Ctrl+C para parar)")
    while True:
        try:
            # Leer el canal analógico 0 (A0)
            value = adc.read(0)      # 0–4095 normalmente
            print("Valor crudo A0:", value, flush=True)

            # Si quieres, lo pasas a % (aprox)
            luz_pct = int(value / 40.95)  # 0–100 aprox
            print("Luz aproximada: {} %".format(luz_pct), flush=True)

            print("-" * 30, flush=True)
            time.sleep(1)

        except Exception as e:
            print("Error leyendo ADC:", e, flush=True)
            time.sleep(1)

if __name__ == "__main__":
    main()
