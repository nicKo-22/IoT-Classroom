# CozyCampus 🏫🌿  
**IoT classroom monitoring on Raspberry Pi (MVP)**

CozyCampus is an IoT monitoring system focused on classrooms. It continuously collects environmental data (temperature, humidity, gas/air quality, noise, light) and estimates classroom occupancy using an ultrasonic sensor (optionally assisted by a servo sweep). Data is streamed to a time-series backend (InfluxDB) for real-time visualization in Grafana, and an HTML analytics report can be generated and stored for later review. :contentReference[oaicite:0]{index=0} :contentReference[oaicite:1]{index=1}

This repository contains the MVP developed during the course:
- Continuous data capture from sensors
- Real-time visualization of time series in Grafana (via InfluxDB)
- Report generation with plots + persistence (stored in MySQL in this MVP) :contentReference[oaicite:2]{index=2}

---

## Concept & real-life scenario

In an educational center, classrooms can vary greatly in occupancy, noise, temperature, and air quality during the day. Usually, these variables are not measured systematically, making it hard to:
- Detect uncomfortable conditions (too hot, excessive noise, poor ventilation)
- Analyze whether classroom usage is related to noise or occupancy
- Make informed decisions about ventilation, room capacity, schedules, and group distribution

With CozyCampus, each equipped classroom:
- Continuously measures:
  - Temperature & humidity → thermal comfort :contentReference[oaicite:3]{index=3}
  - Gas / air quality (relative) → indicator of gases (not calibrated ppm) :contentReference[oaicite:4]{index=4}
  - Sound (relative dB) → ambient noise :contentReference[oaicite:5]{index=5}
  - Light (relative %) → illumination level :contentReference[oaicite:6]{index=6}
  - Occupancy estimation (ultrasonic-based proxy) :contentReference[oaicite:7]{index=7}
- Sends data to Grafana where it is visualized as:
  - Real-time graphs per classroom/time slot/day (extendable using tags)
  - Daily/weekly trends
  - Comparisons between classrooms
- Stores historical data for later analysis and review

**Who benefits**
- Students: quieter, more comfortable spaces  
- Staff (library/university): monitor room usage and comfort remotely  
- University: sustainability and well-being through smart spaces  

> Note: The original concept mentions SQLite for persistence, but the current MVP codebase **stores time-series data in InfluxDB** and **stores generated reports (HTML + images) in MySQL**. :contentReference[oaicite:8]{index=8} :contentReference[oaicite:9]{index=9}

---

## What this MVP does

### ✅ Continuous sensor capture (multi-threaded)
`Main.py` starts one thread per sensor loop and continuously streams readings to InfluxDB. :contentReference[oaicite:10]{index=10}

### ✅ Real-time visualization in Grafana (via InfluxDB)
The sensor scripts write to InfluxDB measurements such as:
- `gas_mq2` (`gas_raw`, `gas_level_pct`) :contentReference[oaicite:11]{index=11}  
- `light_sensor` (`light_raw`, `light_level_pct`) :contentReference[oaicite:12]{index=12}  
- `sound_level` (`sound_db`) :contentReference[oaicite:13]{index=13}  
- `tempHum` (`temperature`, `humidity`) :contentReference[oaicite:14]{index=14}  
- `ultrasonic_occupancy` (`occupancy_pct`, `blocked_readings`, `total_readings`) :contentReference[oaicite:15]{index=15}  

### ✅ HTML analytics report + plots
On stop (Ctrl+C), the system generates a standalone HTML report (default: `informe_sensores.html`) and saves plots under `plots/`. The report is built by querying InfluxDB for the last hours of data. :contentReference[oaicite:16]{index=16} :contentReference[oaicite:17]{index=17}

### ✅ Report persistence in MySQL (HTML + plot images)
After generating the report, `Main.py` stores:
- The HTML (as blob) in `informes`
- Each plot image (as blob) in `informe_imagenes` :contentReference[oaicite:18]{index=18}  
A helper module exists in `db_utils.py` for saving the report content and images. :contentReference[oaicite:19]{index=19}

### ✅ Rebuild & open reports on a Windows PC (offline review)
`Open_Analysis.py` is a utility to **retrieve a stored report from MySQL by date**, rebuild the HTML + images on disk, and open it in your browser. It:
- Accepts `yyyy-MM-DD` as CLI argument
- Lists all reports on that date (lets you choose if there are multiple)
- Writes `informe_sensores.html` and a `plots/` folder into a configured output directory
- Opens the HTML in the default browser :contentReference[oaicite:20]{index=20}

---

## Hardware & sensors (current wiring in code)

- **MQ-2 Gas sensor** → ADC **A4** (`GAS_CHANNEL = 4`) :contentReference[oaicite:21]{index=21}  
- **Light sensor** → ADC **A0** (`SENSOR_CHANNEL = 0`) :contentReference[oaicite:22]{index=22}  
- **Sound sensor** → ADC **A2** (`SENSOR_PORT = 2`) :contentReference[oaicite:23]{index=23}  
- **DHT11 Temperature/Humidity** → **D5** (`TEMPHUM_PIN = 5`) :contentReference[oaicite:24]{index=24}  
- **Ultrasonic ranger** → **D16** (`ULTRASONIC_PORT = 16`) :contentReference[oaicite:25]{index=25}  
- **Servo** → GPIO **BCM 18** (`SERVO_PIN = 18`) :contentReference[oaicite:26]{index=26}  

---

## Repository structure

- `Main.py` — entry point: starts sensor threads, handles stop, generates report, stores to MySQL :contentReference[oaicite:27]{index=27}  
- `Gas_Sensor.py` — MQ2 loop → InfluxDB :contentReference[oaicite:28]{index=28}  
- `Light_Sensor.py` — Light loop → InfluxDB :contentReference[oaicite:29]{index=29}  
- `Sound_Sensor.py` — Sound loop → InfluxDB :contentReference[oaicite:30]{index=30}  
- `TempHum_Sensor.py` — DHT11 loop → InfluxDB :contentReference[oaicite:31]{index=31}  
- `ServoUltrasonic_Sensor.py` — servo sweep + ultrasonic occupancy proxy → InfluxDB :contentReference[oaicite:32]{index=32}  
- `DocumentGenerator.py` — queries InfluxDB and builds `informe_sensores.html` + plots :contentReference[oaicite:33]{index=33}  
- `db_utils.py` — MySQL helpers to store report/images :contentReference[oaicite:34]{index=34}  
- `Open_Analysis.py` — Windows/PC utility: rebuild report from MySQL and open in browser :contentReference[oaicite:35]{index=35}  
- `Prueba_Servo.py` — standalone servo test :contentReference[oaicite:36]{index=36}  
- `Sensors_Launch.bat` / `Open_Analysis.bat` — optional Windows helper scripts to run the system/utilities (batch wrappers)

---

## Tech stack

- **Raspberry Pi** + Grove/Seeed sensors
- **Python**
- **InfluxDB 2.x** for time-series storage :contentReference[oaicite:37]{index=37}
- **Grafana** for dashboards (connected to InfluxDB)
- **MySQL** for storing generated reports (HTML + images) :contentReference[oaicite:38]{index=38}

---

## Setup

### 1) Python dependencies
Install core libraries:
```bash
pip3 install influxdb-client mysql-connector-python pandas matplotlib


Sensor-specific packages depend on your Grove/Seeed setup.

### 2) InfluxDB configuration

In `Main.py`, configure:

* `INFLUX_URL`
* `INFLUX_ORG`
* `INFLUX_BUCKET`
* `INFLUX_TOKEN` 

**Security tip:** don’t hardcode tokens/passwords in commits. Prefer environment variables.

### 3) Grafana configuration

* Add **InfluxDB** as a data source
* Build panels using the measurements/fields listed above

### 4) MySQL tables (for report storage)

`Main.py` documents the required schema:

```sql
CREATE TABLE informes (
  id INT AUTO_INCREMENT PRIMARY KEY,
  created_at DATETIME NOT NULL,
  nombre VARCHAR(255) NOT NULL,
  html LONGBLOB NOT NULL
);

CREATE TABLE informe_imagenes (
  id INT AUTO_INCREMENT PRIMARY KEY,
  informe_id INT NOT NULL,
  filename VARCHAR(255) NOT NULL,
  image LONGBLOB NOT NULL,
  FOREIGN KEY (informe_id) REFERENCES informes(id) ON DELETE CASCADE
);
```



---

## Run on Raspberry Pi

Start streaming all sensors:

```bash
python3 Main.py
```



Stop with **Ctrl+C** to trigger:

1. HTML report + plots generation (`DocumentGenerator.py`) 
2. Save HTML + plot images into MySQL (`informes`, `informe_imagenes`) 

---

## Open saved reports on your PC (Windows)

`Open_Analysis.py` rebuilds a report stored in MySQL and opens it locally. 

### 1) Configure MySQL access (PC side)

In `Open_Analysis.py`, edit `DB_CONFIG` if needed (defaults to `host=localhost`, database `IoTClassroom`). 

### 2) Configure output folder

`BASE_OUTPUT_DIR` is currently an absolute Windows path. Change it to where you want the report to be reconstructed. 

### 3) Run by date (yyyy-MM-DD)

```bash
python Open_Analysis.py 2025-12-12
```

If multiple reports exist for that date, you will be prompted to choose one. Then the tool rebuilds:

* `db_report/informe_sensores.html`
* `db_report/plots/*`
  and opens the HTML automatically. 

---

## How occupancy is estimated (MVP logic)

The ultrasonic sensor measures distance while the servo sweeps. The system computes the percentage of readings where an obstacle is detected under a threshold (`occupancy_pct`). This is **not a direct people count**, but a useful proxy for presence/space blockage. 

---

## Troubleshooting

* **No data in Grafana:** confirm InfluxDB URL/token/org/bucket and that panels query the correct measurement/fields. 
* **Servo not moving / wrong pin:** verify wiring and `SERVO_PIN = 18` (BCM). 
* **MySQL connection errors (Pi or PC):** check `DB_CONFIG.host/user/password/database` and ensure MySQL is reachable.  
* **PC report opens but images missing:** ensure the `plots/` folder exists next to the HTML (the script rebuilds it automatically when images exist in `informe_imagenes`). 

---

## Roadmap (next improvements)

* Add **SQLite persistence** for raw readings to match the original concept (local historical store).
* Add `classroom_id` tags to all measurements for multi-room deployments.
* Calibrate sensors (especially gas/noise) for more meaningful units.
* Add alerting rules (high noise, poor air quality, low light) via Grafana.
