# DocumentGenerator.py

import os
from datetime import datetime

import matplotlib.pyplot as plt
import pandas as pd

# ================================
# SENSOR LIST CONFIGURATION
# ================================
# IMPORTANT: Adjust "measurement" and "field" to what you are
# actually writing into InfluxDB in your sensor scripts.

SENSORS = [
    {
        "name": "Gas Sensor (level %)",
        "measurement": "gas_mq2",
        "field": "gas_level_pct",   # field("gas_level_pct", ...)
        "unit": "%",                # percentage
    },
    {
        "name": "Light Sensor",
        "measurement": "light_sensor",
        "field": "light_level_pct",
        "unit": "unit",
    },
    {
        "name": "Occupancy",
        "measurement": "ultrasonic_occupancy",
        "field": "occupancy_pct",
        "unit": "cm",
    },
    {
        "name": "Sound",
        "measurement": "sound_level",
        "field": "sound_db",
        "unit": "dB",
    },
    {
        "name": "Humidity",
        "measurement": "tempHum",
        "field": "humidity",
        "unit": "%",
    },
    {
        "name": "Temperature",
        "measurement": "tempHum",
        "field": "temperature",
        "unit": "°C",
    },
]


def _consultar_sensor_df(client, bucket, org, measurement, field, horas=24):
    """
    Query the last `horas` hours of a sensor (measurement + field)
    and return a DataFrame with columns [_time, _value].
    """
    query_api = client.query_api()
    rango = f"-{horas}h"

    query = f'''
    from(bucket: "{bucket}")
      |> range(start: {rango})
      |> filter(fn: (r) => r._measurement == "{measurement}")
      |> filter(fn: (r) => r._field == "{field}")
      |> keep(columns: ["_time", "_value"])
      |> sort(columns: ["_time"])
    '''

    tables = query_api.query_data_frame(org=org, query=query)

    if isinstance(tables, list) and len(tables) > 0:
        df = pd.concat(tables, ignore_index=True)
    else:
        df = tables  # sometimes it already comes as a DataFrame

    if df is None or df.empty:
        return pd.DataFrame(columns=["_time", "_value"])

    df = df[["_time", "_value"]].dropna()
    return df


def _generar_grafica(df, sensor_name, unit, output_path):
    """Generate and save the plot of a sensor to output_path."""
    if df.empty:
        return False

    plt.figure(figsize=(8, 4))
    plt.plot(df["_time"], df["_value"])
    plt.title(f"{sensor_name} - Latest readings")
    plt.xlabel("Time")
    plt.ylabel(f"Value ({unit})")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
    return True


def generar_informe_sensores(
    client,
    bucket,
    org,
    horas_rango=24,
    output_html="informe_sensores.html",
):
    """
    Generate an analytical HTML report with:
      - Summary table with mean value per sensor
      - One plot per sensor

    It uses the InfluxDB client, bucket and org passed in
    (the same ones you use in main.py).
    """
    # Folder to store plots
    plots_dir = "plots"
    os.makedirs(plots_dir, exist_ok=True)

    resultados = []

    for sensor in SENSORS:
        name = sensor["name"]
        measurement = sensor["measurement"]
        field = sensor["field"]
        unit = sensor["unit"]

        df = _consultar_sensor_df(
            client,
            bucket,
            org,
            measurement,
            field,
            horas=horas_rango,
        )

        mean_value = float(df["_value"].mean()) if not df.empty else None

        plot_filename = f"{measurement}_{field}.png"
        plot_path = os.path.join(plots_dir, plot_filename)

        has_plot = _generar_grafica(df, name, unit, plot_path)

        resultados.append({
            "name": name,
            "measurement": measurement,
            "field": field,
            "unit": unit,
            "mean": mean_value,
            "plot_path": plot_path if has_plot else None,
            "num_samples": len(df),
        })

    # ============
    # HTML REPORT
    # ============
    now = datetime.now()
    title = "Sensor Analytics Report"
    date_str = now.strftime("%Y-%m-%d %H:%M:%S")

    html_parts = []

    html_parts.append(f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
        }}
        h1, h2 {{
            color: #333;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin-bottom: 30px;
        }}
        th, td {{
            border: 1px solid #ccc;
            padding: 8px;
            text-align: center;
        }}
        th {{
            background-color: #f2f2f2;
        }}
        .sensor-section {{
            margin-bottom: 40px;
        }}
        img {{
            max-width: 100%;
            height: auto;
            border: 1px solid #ddd;
            padding: 4px;
        }}
        .no-data {{
            color: #888;
            font-style: italic;
        }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    <p>Generated on: {date_str}</p>
    <p>Time range analysed: last {horas_rango} hours.</p>
    <hr>
""")

    # Summary table of means
    html_parts.append("""
    <h2>Summary of mean values per sensor</h2>
    <table>
        <tr>
            <th>Sensor</th>
            <th>Measurement</th>
            <th>Field</th>
            <th># Samples</th>
            <th>Mean</th>
            <th>Unit</th>
        </tr>
    """)

    for r in resultados:
        mean_str = f"{r['mean']:.2f}" if r["mean"] is not None else "N/A"
        html_parts.append(f"""
        <tr>
            <td>{r['name']}</td>
            <td>{r['measurement']}</td>
            <td>{r['field']}</td>
            <td>{r['num_samples']}</td>
            <td>{mean_str}</td>
            <td>{r['unit']}</td>
        </tr>
        """)

    html_parts.append("</table>")

    # Detailed section per sensor
    for r in resultados:
        html_parts.append(f"""
        <div class="sensor-section">
            <h2>{r['name']}</h2>
            <p><b>Measurement:</b> {r['measurement']} &nbsp; | &nbsp;
               <b>Field:</b> {r['field']} &nbsp; | &nbsp;
               <b>Samples:</b> {r['num_samples']}</p>
        """)

        if r["mean"] is not None:
            html_parts.append(
                f"<p><b>Mean of readings:</b> {r['mean']:.2f} {r['unit']}</p>"
            )
        else:
            html_parts.append(
                "<p class='no-data'>No data in the selected time range.</p>"
            )

        if r["plot_path"]:
            html_parts.append(f"""
            <p>Readings plot:</p>
            <img src="{r['plot_path']}" alt="Plot {r['name']}">
            """)
        else:
            html_parts.append(
                "<p class='no-data'>Could not generate plot (insufficient data).</p>"
            )

        html_parts.append("</div>")

    html_parts.append("""
</body>
</html>
""")

    html_final = "\n".join(html_parts)

    with open(output_html, "w", encoding="utf-8") as f:
        f.write(html_final)

    return os.path.abspath(output_html)


if __name__ == "__main__":
    print("This module is meant to be called from main.py")
