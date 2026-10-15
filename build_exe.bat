@echo off
setlocal
cd /d "%~dp0"

set "PY=%~dp0.venv\Scripts\python.exe"
:: Modelo que viaja en el paquete y usa la app de fabrica. Si no esta aqui, la
:: app lo descarga sola de HuggingFace en el primer arranque.
set "BUNDLED_MODEL=ggml-small-q5_1.bin"

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

:: El .config de .NET TIENE que quedar al lado del .exe: de ahi saca .NET el
:: interruptor loadFromRemoteSources, sin el cual clr_loader no puede cargar
:: Python.Runtime.dll (el fichero cae en la zona Internet/Intranet) y el panel
:: caeria al respaldo de Chrome. Lo pone ya dicta.spec; esto es un cinturon
:: extra por si alguien compila a mano sin el spec actualizado.
if exist "dicta.exe.config" copy /y "dicta.exe.config" "dist\dicta\dicta.exe.config" >nul

:: Modelo de fabrica junto al exe (EXTERNO: no se empaqueta en _internal).
if not exist "dist\dicta\models" mkdir "dist\dicta\models"
if exist "models\%BUNDLED_MODEL%" (
    echo Copiando modelo %BUNDLED_MODEL% ...
    copy /y "models\%BUNDLED_MODEL%" "dist\dicta\models\" >nul
) else (
    echo [AVISO] No esta models\%BUNDLED_MODEL%: el .exe lo descargara solo
    echo         la primera vez que transcriba algo.
)

echo.
echo ============================================================
echo   Listo:  dist\dicta\dicta.exe
echo.
echo   Al lado del .exe (EXTERNO, no se empaqueta):
echo     dicta.exe.config   ^<- .NET: loadFromRemoteSources (WebView2)
echo     models\            ^<- %BUNDLED_MODEL% (los demas se bajan solos)
echo     dicta_config.json  ^<- se crea solo al ejecutar
echo     dicta.log / dicta_crash.log / .tmp\  ^<- se crean solos
echo.
echo   El bundle (panel\, whisper_bin\, whisper_vulkan\) vive en _internal\.
echo   Windows 11 limpio: sin Python, sin Chrome y sin instalar nada.
echo ============================================================
endlocal
exit /b 0
