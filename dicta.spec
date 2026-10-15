# -*- mode: python ; coding: utf-8 -*-
r"""PyInstaller spec for dicta - onedir, windowed (no console), sin UAC.

Dos cosas que NO se pueden tocar sin romper el .exe congelado:

1) `dicta.exe.config` tiene que viajar en la RAIZ de dist/dicta (al lado del
   .exe), no dentro de _internal: .NET Framework lee <exe>.exe.config para
   sacar el interruptor loadFromRemoteSources. Sin el, clr_loader no puede
   cargar Python.Runtime.dll (LoadFrom de un fichero en la zona Internet/
   Intranet del sistema lanza NotSupportedException) y pywebview no abre: el
   panel caeria al respaldo de Chrome. COLLECT mete TODO lo DATA/BINARY en
   _internal, asi que el unico tipo con el que se puede escribir en la raiz es
   'EXECUTABLE' (ver _extra en COLLECT).

2) `uac_admin` va en False: es una aplicacion de bandeja portable que no
   necesita permisos de administrador. Con True el .exe ni arranca desde un
   proceso sin elevar (CreateProcess error 740) y el usuario tendria que
   aceptar un UAC.

Layout produced:

    dist/dicta/
        dicta.exe            <- sin consola y SIN elevacion (portable)
        dicta.exe.config     <- AL LADO del .exe (lo lee .NET)
        _internal/           <- bundle (sys._MEIPASS)
            panel/           <- served by the internal http.server
            whisper_bin/Release/whisper-cli.exe   (+ ggml*.dll, whisper.dll)
            whisper_vulkan/whisper-server.exe      (+ ggml-vulkan.dll, ...)
        models/              <- EXTERNAL, next to dicta.exe (se copia aparte)
        dicta_config.json    <- EXTERNAL
        dicta.log            <- EXTERNAL
        .tmp/                <- EXTERNAL

External data lives next to the exe because dicta.py resolves it with
DATA_DIR = os.path.dirname(sys.executable). Bundled engines stay inside
_internal so the app is always runnable and each whisper exe keeps its DLLs
in its own directory (Windows resolves them there first).

Build:  build_exe.bat     (uses .venv\Scripts\python.exe -m PyInstaller)
"""
import os
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

# SPECPATH is provided by PyInstaller: the directory holding this .spec file.
PROJECT = os.path.abspath(SPECPATH)

# ---------------------------------------------------------------- datas
# Bundled resources (read from sys._MEIPASS at runtime).
datas = [(os.path.join(PROJECT, "panel"), "panel")]

# El icono también se usa EN CALIENTE (icono de la ventana del panel), así que
# tiene que viajar en el bundle y no solo como icono del .exe.
for _f in ("dicta.ico",):
    _p = os.path.join(PROJECT, _f)
    if os.path.isfile(_p):
        datas.append((_p, "."))

# Ship every whisper backend that exists in the repo. whisper_cuda may be
# absent (it is on the dev machine); include it only when present.
for _dir in ("whisper_bin", "whisper_vulkan", "whisper_cuda"):
    _src = os.path.join(PROJECT, _dir)
    if os.path.isdir(_src):
        datas.append((_src, _dir))

# ------------------------------------------------- native audio runtime libs
# sounddevice imports _sounddevice_data (PortAudio DLLs) and soundfile imports
# _soundfile_data (libsndfile DLL) at import time; both must be copied verbatim
# or `import sounddevice/soundfile` explodes in the frozen build.
binaries = []
for _pkg in ("_sounddevice_data", "_soundfile_data"):
    datas += collect_data_files(_pkg, include_py_files=True)
    binaries += collect_dynamic_libs(_pkg)

# --------------------------------------------------------------- hidden imports
hiddenimports = [
    "sounddevice", "soundfile",
    "_sounddevice", "_soundfile",
    "_cffi_backend",
    "pystray._win32",
    # Módulos propios que se importan de forma diferida (dentro de funciones o
    # con try/except): si no se declaran aquí, el .exe congelado no los lleva.
    "dicta_ui", "dicta_icon", "dicta_capture", "dicta_layered",
    # pywebview (panel sin marco con WebView2). Se importa de forma diferida en
    # main(), así que PyInstaller no lo ve solo: van el backend de Windows y las
    # piezas de pythonnet/clr-loader que carga por reflexión.
    "webview", "webview.platforms.edgechromium", "webview.platforms.winforms",
    "clr", "clr_loader", "pythonnet",
]

# ---------------------------------------------------------------- analysis
a = Analysis(
    ["dicta.py"],
    pathex=[PROJECT],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "matplotlib", "scipy", "pandas", "IPython", "pytest",
        "pystray._gtk", "pystray._xorg", "pystray._darwin",
        "pystray._appindicator",
    ],
    noarchive=False,
)
pyz = PYZ(a.pure)

# console=False  -> no console window (equivalent to pythonw)
# uac_admin=False -> NO pide UAC: app de bandeja portable, arranca desde
#                    cualquier proceso sin elevar (ver nota de arriba).
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="dicta",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,                     # UPX + AV false positives + broken DLLs: no
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(PROJECT, "dicta.ico") if os.path.isfile(
        os.path.join(PROJECT, "dicta.ico")) else None,
    uac_admin=False,
)

# El .config de .NET va a la RAIZ de dist/dicta, al lado de dicta.exe: .NET lo
# busca como <exe>.exe.config y de ahi saca `loadFromRemoteSources`, que es lo
# que permite a clr_loader cargar Python.Runtime.dll del bundle (LoadFrom de un
# fichero en la zona Internet/Intranet revienta sin ese interruptor y el panel
# caeria a Chrome). COLLECT mete todo lo DATA en _internal, asi que el unico
# tipo que escribe en la raiz es 'EXECUTABLE'.
_extra = []
_dotnet_cfg = os.path.join(PROJECT, "dicta.exe.config")
if os.path.isfile(_dotnet_cfg):
    _extra.append(("dicta.exe.config", _dotnet_cfg, "EXECUTABLE"))

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    _extra,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="dicta",
)

