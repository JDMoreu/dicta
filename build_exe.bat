@echo off
setlocal
cd /d "%~dp0"

set "PY=%~dp0.venv\Scripts\python.exe"

if not exist "%PY%" (
    echo [ERROR] No existe el venv: "%PY%"
    echo Crea el venv con: py -3.12 -m venv .venv
    exit /b 1
)

:: PyInstaller no viene en requirements.txt: se instala/actualiza solo aqui.
"%PY%" -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo Instalando PyInstaller en el venv...
    "%PY%" -m pip install --upgrade pip
    "%PY%" -m pip install --upgrade "pyinstaller>=6.6"
    if errorlevel 1 (
        echo [ERROR] No se pudo instalar PyInstaller.
        exit /b 1
    )
)

echo Limpiando build\ y dist\ ...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo Construyendo dicta.exe ...
"%PY%" -m PyInstaller --noconfirm --clean "dicta.spec"
if errorlevel 1 (
    echo [ERROR] La compilacion fallo. Revisa el log de arriba.
    exit /b 1
)

:: Carpeta externa de modelos junto al exe (vacia; los .bin se copian dentro).
if not exist "dist\dicta\models" mkdir "dist\dicta\models"

echo.
echo ============================================================
echo   Listo:  dist\dicta\dicta.exe
echo.
echo   Junto a dicta.exe (EXTERNO, no se empaqueta):
echo     models\            ^<- copia aqui los *.bin (o dejara descargarlos)
echo     dicta_config.json  ^<- se crea solo al ejecutar
echo     dicta.log / dicta_crash.log / .tmp\  ^<- se crean solos
echo.
echo   El bundle (panel\, whisper_bin\, whisper_vulkan\) vive en _internal\.
echo ============================================================
endlocal
exit /b 0
