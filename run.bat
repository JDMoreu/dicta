@echo off
cd /d "%~dp0"

:: Auto-elevación: si no somos administrador, relanzamos este mismo .bat
:: con permisos elevados (Windows mostrará el aviso de UAC). Es necesario
:: para poder inyectar texto/teclado en aplicaciones que corren elevadas
:: y para la automatización por UI Automation sobre ventanas protegidas.
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Solicitando permisos de administrador...
    powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -ArgumentList '%*' -Verb RunAs"
    exit /b
)

:: pythonw = sin ventana de consola. Los registros van a dicta.log.
start "" ".venv\Scripts\pythonw.exe" dicta.py %*
exit /b
