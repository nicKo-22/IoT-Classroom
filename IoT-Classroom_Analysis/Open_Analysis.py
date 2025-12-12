import sys
import os
import mysql.connector
import webbrowser

# ============================
#  CONFIGURACIÓN MySQL
#  (este es el MySQL de tu PC)
# ============================
DB_CONFIG = {
    "host": "localhost",          # MySQL está en tu propio PC
    "user": "raspi11",
    "password": "adminRaspi11",
    "database": "IoTClassroom",
}

# Carpeta donde se reconstruirá el informe y las imágenes
BASE_OUTPUT_DIR = r"C:\Users\nicko\Desktop\UNI\CURSO4\Cuatri_1\Internet of Things\IoT-Classroom_Analysis\db_report"
HTML_FILENAME = "informe_sensores.html"
PLOTS_DIRNAME = "plots"


def elegir_informe_por_fecha(report_date: str):
    """
    Devuelve (id, created_at, nombre) del informe elegido por el usuario
    para la fecha dada (yyyy-MM-DD).
    """
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    try:
        query = """
            SELECT id, created_at, nombre
            FROM informes
            WHERE DATE(created_at) = %s
            ORDER BY created_at
        """
        cursor.execute(query, (report_date,))
        rows = cursor.fetchall()

        if not rows:
            print(f"No se han encontrado informes para la fecha {report_date}.")
            return None

        if len(rows) == 1:
            id_inf, created_at, nombre = rows[0]
            print(f"Se ha encontrado un único informe:")
            print(f"  [1] id={id_inf}  fecha_hora={created_at}  nombre={nombre}")
            print("Seleccionando ese informe...")
            return rows[0]

        # Hay varios informes el mismo día: preguntar cuál quiere
        print("Se han encontrado varios informes en esa fecha:")
        for idx, (id_inf, created_at, nombre) in enumerate(rows, start=1):
            print(f"  [{idx}] id={id_inf}  fecha_hora={created_at}  nombre={nombre}")

        while True:
            choice = input(f"Elige informe (1-{len(rows)}): ")
            try:
                choice_int = int(choice)
                if 1 <= choice_int <= len(rows):
                    return rows[choice_int - 1]
            except ValueError:
                pass
            print("Opción no válida, inténtalo de nuevo.")

    finally:
        cursor.close()
        conn.close()


def reconstruir_informe(informe_id: int):
    """
    Recupera el HTML y las imágenes de la BD para el informe_id,
    los guarda en disco y devuelve la ruta absoluta al HTML.
    """
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    try:
        # 1) Obtener HTML
        cursor.execute("SELECT html FROM informes WHERE id = %s", (informe_id,))
        row = cursor.fetchone()
        if row is None:
            print(f"No se ha encontrado el informe con id={informe_id}.")
            return None

        html_data = row[0]

        # Crear carpeta base y carpeta plots
        os.makedirs(BASE_OUTPUT_DIR, exist_ok=True)
        plots_dir = os.path.join(BASE_OUTPUT_DIR, PLOTS_DIRNAME)
        os.makedirs(plots_dir, exist_ok=True)

        # Guardar HTML
        html_path = os.path.join(BASE_OUTPUT_DIR, HTML_FILENAME)
        with open(html_path, "wb") as f:
            f.write(html_data)
        print(f"HTML reconstruido en: {html_path}")

        # 2) Obtener imágenes asociadas
        cursor.execute(
            "SELECT filename, image FROM informe_imagenes WHERE informe_id = %s",
            (informe_id,),
        )
        rows = cursor.fetchall()

        if not rows:
            print("No se han encontrado imágenes asociadas (tabla informe_imagenes).")
        else:
            for filename, img_data in rows:
                out_path = os.path.join(plots_dir, filename)
                with open(out_path, "wb") as f:
                    f.write(img_data)
                print(f"Imagen guardada: {out_path}")

        return html_path

    finally:
        cursor.close()
        conn.close()


def main():
    if len(sys.argv) < 2:
        print("Uso: python ver_informe.py yyyy-MM-DD")
        return

    report_date = sys.argv[1]

    # 1) Elegir informe por fecha (y, si hay varios, por índice)
    info = elegir_informe_por_fecha(report_date)
    if info is None:
        return

    informe_id, created_at, nombre = info
    print(f"\nHas elegido el informe id={informe_id}, fecha_hora={created_at}, nombre={nombre}")

    # 2) Reconstruir HTML + imágenes
    html_path = reconstruir_informe(informe_id)
    if html_path is None:
        return

    # 3) Abrir en el navegador
    print("\nAbriendo el informe en el navegador...")
    webbrowser.open(html_path)


if __name__ == "__main__":
    main()
