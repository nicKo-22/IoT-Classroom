@echo off
setlocal

REM === CONFIGURACIÓN ===
set RPI_USER=pi
set RPI_NAME=raspi11

set RPI_HOME=/home/pi
set RPI_DIR=/home/pi/IoT-Classroom

echo ==============================
echo Paso 1: Resolver IP de %RPI_NAME%
echo ==============================
set RPI_HOST=

REM 1) Intentar con raspi11
echo Ejecutando: ping -4 -n 1 %RPI_NAME%
ping -4 -n 1 %RPI_NAME%
echo.

for /f "tokens=2 delims=[]" %%A in ('ping -4 -n 1 %RPI_NAME% ^| findstr "["') do (
    echo Encontrada IP en ping: %%A
    set RPI_HOST=%%A
)

echo.
echo Valor de RPI_HOST tras el FOR: "%RPI_HOST%"
pause

if not defined RPI_HOST (
    echo.
    echo No se ha podido obtener la IP de %RPI_NAME%.
    echo Asegurate de que la Raspberry esta encendida y en la misma red.
    pause
    exit /b 1
)

echo.
echo ==============================
echo Paso 2: Conectar por SSH
echo ==============================
echo IP de la Raspberry: %RPI_HOST%
echo Connecting to %RPI_USER%@%RPI_HOST% ...
echo.

echo When you want to stop the sensors and generate the document,
echo press Ctrl + C in this window. The signal will be sent to Main.py
echo on the Raspberry (KeyboardInterrupt).
echo.

REM Forzamos pseudo-terminal (-t) para que Ctrl+C se mande como SIGINT al proceso remoto
ssh -t %RPI_USER%@%RPI_HOST% "cd %RPI_HOME% && . venvs/grove/bin/activate && sleep 5 && cd %RPI_DIR% && python3 Main.py"

echo.
echo The remote Main.py has finished (either normally or after Ctrl + C).
echo Waiting 10 seconds for the document and graphics to generate...
timeout /t 10 /nobreak >nul

echo.
echo Everything ready. Press any key to close this window.
pause >nul

endlocal
