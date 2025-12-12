import os
from datetime import datetime
import mysql.connector

DB_CONFIG = {
    "host": "192.168.1.140",      # pon aquí la IP de tu PC
    "user": "raspi11",
    "password": "adminRaspi11",
    "database": "IoTClassroom",
}

def guardar_informe_en_mysql(html_path, plots_dir, nombre_informe="informe_sensores"):
    if not os.path.isfile(html_path):
        print(f"[MySQL] ERROR: No se encuentra el HTML en {html_path}")
        return

    with open(html_path, "rb") as f:
        html_data = f.read()

    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    try:
        insert_informe_sql = """
            INSERT INTO informes (created_at, nombre, html)
            VALUES (%s, %s, %s)
        """
        now = datetime.now()
        cursor.execute(insert_informe_sql, (now, nombre_informe, html_data))
        informe_id = cursor.lastrowid
        print(f"[MySQL] Informe insertado con id={informe_id}")

        if os.path.isdir(plots_dir):
            for filename in os.listdir(plots_dir):
                full_path = os.path.join(plots_dir, filename)
                if not os.path.isfile(full_path):
                    continue
                if not filename.lower().endswith((".png", ".jpg", ".jpeg", ".gif")):
                    continue

                with open(full_path, "rb") as img_f:
                    img_data = img_f.read()

                insert_imagen_sql = """
                    INSERT INTO informe_imagenes (informe_id, filename, image)
                    VALUES (%s, %s, %s)
                """
                cursor.execute(insert_imagen_sql, (informe_id, filename, img_data))
                print(f"[MySQL]   Imagen '{filename}' guardada.")

        conn.commit()
        print("[MySQL] Informe e imágenes guardados correctamente.")

    except Exception as e:
        conn.rollback()
        print(f"[MySQL] ERROR guardando informe: {e}")

    finally:
        cursor.close()
        conn.close()
