# IoT Classroom (Raspberry Pi 3B+)

Proyecto de aula para Raspberry Pi 3B+ con Grove Base Hat que integra sensores ambientales, radar ultrasónico por sectores e ingesta de datos en InfluxDB (v1/v2) para visualizarlos en Grafana. Incluye almacenamiento local en SQLite, modo simulación y despliegue como servicio systemd.

## Hardware requerido

- Raspberry Pi 3B+ con Raspberry Pi OS Lite (recomendado) y hat Grove Base para Pi.
- Sensores Grove/Seeed conectados por defecto a:
  - DHT11/DHT22 -> D5
  - Ultrasonidos (HC-SR04 / Grove Ultrasonic Ranger) -> D16
  - Luz (Grove Light v1.x) -> A0
  - Sonido (Grove Sound Sensor V1.6) -> A2
  - Gas (Grove Gas Sensor v1.5) -> A4
  - Servo (Grove Servo) -> D18 (BCM 12, PWM 50 Hz)
- Fuente de alimentación estable (>=2.5 A) y masa común entre servo y Pi.

## Software

- Python 3.11+ y venv.
- Librerías (ver requirements.txt): seeed-python-grove, seeed-python-dht, RPi.GPIO, influxdb (v1) / influxdb-client (v2), python-dotenv, pyyaml, apscheduler, sqlite-utils.

## Preparación del sistema

1. Actualiza la Pi y habilita I2C (para el ADC del hat):

        sudo apt update && sudo apt upgrade -y
        sudo raspi-config  # Interface Options -> I2C -> Enable

2. Clona el repositorio dentro de /home/pi:

        git clone <repo> iot-classroom
        cd iot-classroom

3. Crea el entorno virtual e instala dependencias:

        python3 -m venv .venv
        source .venv/bin/activate
        pip install -r requirements.txt

4. Copia .env.example a .env y completa los valores de InfluxDB (ver más abajo).

## Configuración

- config.yaml define:
  - room, device: etiquetas para Influx + SQLite.
  - simulate: fuerza modo simulación (también disponible vía SIMULATE=1 en .env).
  - Bloques sampling, radar, ports, influx, storage (incluye sampling.gas_s y ports.gas para el sensor de gas).
- Puertos pueden sobrescribirse (ej. ports.dht: "D6"). El ADC usa dirección 0x04; ajusta ports.adc_address si tu hat reporta otra.
- Variables .env:
  - Influx v1: INFLUX_HOST, INFLUX_PORT, INFLUX_DB, INFLUX_USER, INFLUX_PASSWORD, INFLUX_SSL.
  - Influx v2: INFLUX_URL, INFLUX_TOKEN, INFLUX_ORG, INFLUX_BUCKET.
  - SIMULATE=1 habilita generadores de datos (sensores + radar virtual con obstáculos en 2 sectores).

## Ejecución manual

        source .venv/bin/activate
        python main.py

El servicio registra en consola y logs/app.log. Si un sensor falla, se registra el error y el resto sigue activo. Cierres por Ctrl+C o señales SIGINT/SIGTERM detienen limpiamente PWM, GPIO y conexiones.

## InfluxDB + Grafana

- Selecciona la versión en config.yaml (influx.version: 1 o 2).
- Métricas:
  - env_sensors: temperature_c, humidity_pct, light_adc, sound_adc, sound_digital, gas_adc con tags room, device.
  - radar: sector_0_pct...sector_5_pct, min_distance_m, objects_count.
- Importa grafana/dashboard.json en Grafana e indica la data source de Influx al solicitar DS_INFLUX.

## Radar por sectores

- Servo barre automáticamente de 0°->180°->0° con paso configurable (radar.angle_step_deg).
- Por ángulo se toman radar.reads_per_angle lecturas ultrasonido, se calcula la mediana y se limita a radar.max_distance_m.
- radar.object_threshold_m define cuándo un punto cuenta como ocupado; la ocupación porcentual se calcula sectorizando los 180° según radar.sectors (6 por defecto) y los resultados se envían a Influx y SQLite.

## Almacenamiento local

- data/metrics.db guarda todas las muestras (env_samples, radar_samples).
- Cada ciclo de flush (config sampling.flush_s) también purga datos más antiguos que storage.retention_days (90 días por defecto).
- Si Influx no está disponible, los datos se almacenan en SQLite y el log reporta el incidente.

## Servicio systemd

1. Ajusta services/iot-classroom.service (usuario, rutas, entorno virtual).
2. Instala con el script:

        ./services/install_service.sh /home/pi/iot-classroom

3. Revisa el estado:

        systemctl status iot-classroom.service
        journalctl -u iot-classroom.service -f

## Seguridad en GPIO

- Comprueba dos veces el cableado antes de energizar.
- Servo y sensores deben compartir masa con la Pi.
- No manipules cables con la Pi encendida.
- Evita sobrecargas en 5 V; si el servo consume demasiado, aliméntalo externamente (con GND común).

## Modo simulación y tests

- Ejecuta SIMULATE=1 python main.py desde tu workstation para validar lógica sin hardware.
- Pruebas unitarias (no requieren hardware):

        source .venv/bin/activate
        pytest
