# -*- mode: python ; coding: utf-8 -*-
r"""PyInstaller spec for dicta — onedir, windowed (no console), UAC admin.

Layout produced:

    dist/dicta/
        dicta.exe            <- runs elevated, no console
        _internal/           <- bundle (sys._MEIPASS)
            panel/           <- served by the internal http.server
            whisper_bin/Release/whisper-cli.exe   (+ ggml*.dll, whisper.dll)
            whisper_vulkan/whisper-server.exe      (+ ggml-vulkan.dll, ...)
        models/              <- EXTERNAL, next to dicta.exe (817 MB, not bundled)
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
# uac_admin=True -> embed manifest requireAdministrator (UAC prompt, elevated)
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
    uac_admin=True,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="dicta",
)
