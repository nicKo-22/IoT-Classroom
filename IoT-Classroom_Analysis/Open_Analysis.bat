@echo off
setlocal

REM Carpeta donde estará el script Python
set BASE_DIR=C:\Users\nicko\Desktop\UNI\CURSO4\Cuatri_1\Internet of Things\IoT-Classroom_Analysis

echo Introduce la fecha del informe (formato yyyy-MM-DD):
set /p REPORT_DATE=Fecha: 

echo.
echo Buscando informes para la fecha %REPORT_DATE% ...
echo.

REM Ejecutar el script de Python que consulta MySQL y abre el informe
py "%BASE_DIR%\Open_Analysis.py" "%REPORT_DATE%"


echo.
echo Pulsa una tecla para cerrar esta ventana.
pause >nul

endlocal
