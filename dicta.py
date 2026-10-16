#!/usr/bin/env python3
"""dicta — dictado por voz local, ligero y rápido, estilo Eqho.

Arquitectura anti-cuelgues:
  - Motor: whisper.cpp (whisper-cli.exe) como subprocess con timeout duro.
    Si algo falla, muere el subprocess, nunca la app.
  - Hotkey: RegisterHotKey de Windows (toggle) o sondeo GetAsyncKeyState
    (hold). Sin hooks globales de pynput.
  - Hilos sin locks entre sí: Tk solo pinta, el hilo de teclado decide,
    el hilo de transcripción ejecuta. Nada pesado corre en el hilo GUI.

Uso:
  dicta.py                       Alt+Q empieza/para el dictado (toggle)
  dicta.py --mode hold           mantener pulsado mientras hablas
  dicta.py --hotkey ctrl+alt+d   otra combinación
  dicta.py --model turbo         tiny|base|small|medium|turbo (small por defecto)
  dicta.py --prompt "palabras"   vocabulario opcional
  dicta.py --file audio.flac     prueba: transcribe un archivo y sale
  dicta.py --list-mics           lista dispositivos de entrada
  dicta.py --no-gui              sin ventana
"""

import argparse
import atexit
import ctypes
import faulthandler
import re
import shutil
import uuid
from ctypes import wintypes
import json
import os
import queue
import socket
import subprocess
import sys
import threading
import time
import urllib.request

import numpy as np
import sounddevice as sd
import soundfile as sf
import tkinter as tk

# Estos interpreters (ctypes) resuelven las DLLs de forma PEREZOSA: si el
# primer acceso a ctypes.windll.* ocurre en un hilo secundario durante un
# GC, hace crashear el intérprete (violación de acceso). Los resolvemos
# UNA vez aquí, en el hilo principal, y los compartimos como globales.
_user32 = ctypes.windll.user32
_kernel32 = ctypes.windll.kernel32
_ole32 = ctypes.windll.ole32


def _declare_prototypes():
    """Declara argtypes/restype de lo que usa dicta.

    Sin esto, en x64 ctypes devuelve por defecto un `c_int` de 32 bits: un HWND
    o un HMODULE con los bits altos activos llega TRUNCADO (y con extensión de
    signo). Es la misma familia de fallo que reventaba la muesca con access
    violation; aquí `app.target_hwnd` es justo ese caso.
    """
    u = _user32
    P, B, U = ctypes.c_void_p, wintypes.BOOL, wintypes.UINT
    L = ctypes.c_ssize_t
    u.GetForegroundWindow.argtypes = []
    u.GetForegroundWindow.restype = P
    u.SetForegroundWindow.argtypes = [P]
    u.SetForegroundWindow.restype = B
    u.IsWindow.argtypes = [P]
    u.IsWindow.restype = B
    u.IsWindowVisible.argtypes = [P]
    u.IsWindowVisible.restype = B
    u.IsZoomed.argtypes = [P]
    u.IsZoomed.restype = B
    u.ShowWindow.argtypes = [P, ctypes.c_int]
    u.ShowWindow.restype = B
    u.DestroyWindow.argtypes = [P]
    u.DestroyWindow.restype = B
    u.PostMessageW.argtypes = [P, U, ctypes.c_size_t, L]
    u.PostMessageW.restype = B
    u.SendMessageW.argtypes = [P, U, ctypes.c_size_t, L]
    u.SendMessageW.restype = L
    u.SetWindowTextW.argtypes = [P, ctypes.c_wchar_p]
    u.SetWindowTextW.restype = B
    u.GetWindowTextW.argtypes = [P, ctypes.c_wchar_p, ctypes.c_int]
    u.GetWindowTextW.restype = ctypes.c_int
    u.GetClassNameW.argtypes = [P, ctypes.c_wchar_p, ctypes.c_int]
    u.GetClassNameW.restype = ctypes.c_int
    u.GetParent.argtypes = [P]
    u.GetParent.restype = P
    u.ReleaseCapture.argtypes = []
    u.ReleaseCapture.restype = B
    u.SendInput.argtypes = [U, P, ctypes.c_int]
    u.SendInput.restype = U
    u.LoadImageW.argtypes = [P, ctypes.c_wchar_p, U, ctypes.c_int,
                             ctypes.c_int, U]
    u.LoadImageW.restype = P
    u.GetAsyncKeyState.argtypes = [ctypes.c_int]
    u.GetAsyncKeyState.restype = ctypes.c_short
    u.UnregisterHotKey.argtypes = [P, ctypes.c_int]
    u.UnregisterHotKey.restype = B
    # kernel32: matar hijos por PID en el cierre (OpenProcess/TerminateProcess)
    k = _kernel32
    k.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    k.OpenProcess.restype = ctypes.c_void_p
    k.TerminateProcess.argtypes = [ctypes.c_void_p, wintypes.UINT]
    k.TerminateProcess.restype = B
    k.CloseHandle.argtypes = [ctypes.c_void_p]
    k.CloseHandle.restype = B


try:
    _declare_prototypes()
except Exception as _e:                       # nunca debe impedir arrancar
    pass


class _POINT(ctypes.Structure):
    _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]


class _WINDOWPLACEMENT(ctypes.Structure):
    """WINDOWPLACEMENT de Win32 (para leer el rectángulo de ventana normal).

    `rcNormalPosition` es dónde y con qué tamaño queda la ventana al
    RESTAURARLA: es justo la geometría que necesita el arrastre cuando la
    ventana está maximizada y hay que devolverla a modo ventana. El campo
    `length` lo valida Windows, así que se rellena con `sizeof`. (En Windows 10+
    el struct tiene un `rcDevice` opcional al final; se omite a propósito y
    Windows lo acepta porque manda `length`.)
    """
    _fields_ = [("length", wintypes.UINT),
                ("flags", wintypes.UINT),
                ("showCmd", wintypes.UINT),
                ("ptMinPosition", _POINT),
                ("ptMaxPosition", _POINT),
                ("rcNormalPosition", wintypes.RECT)]


class _MSG(ctypes.Structure):
    # Windows x64 MSG is 48 bytes. Keep the complete native layout: the
    # previous abbreviated struct let GetMessageW overwrite Python memory.
    _fields_ = [("hwnd", wintypes.HWND), ("message", wintypes.UINT),
                ("wParam", wintypes.WPARAM), ("lParam", wintypes.LPARAM),
                ("time", wintypes.DWORD), ("pt", _POINT),
                ("lPrivate", wintypes.DWORD)]


_RegisterHotKey = _user32.RegisterHotKey
_RegisterHotKey.argtypes = (wintypes.HWND, ctypes.c_int, wintypes.UINT, wintypes.UINT)
_RegisterHotKey.restype = wintypes.BOOL
_UnregisterHotKey = _user32.UnregisterHotKey
_UnregisterHotKey.argtypes = (wintypes.HWND, ctypes.c_int)
_UnregisterHotKey.restype = wintypes.BOOL
_GetAsyncKeyState = _user32.GetAsyncKeyState
_GetAsyncKeyState.argtypes = (ctypes.c_int,)
_GetAsyncKeyState.restype = ctypes.c_short
_GetMessageW = _user32.GetMessageW
_GetMessageW.argtypes = (ctypes.POINTER(_MSG), wintypes.HWND,
                         wintypes.UINT, wintypes.UINT)
_GetMessageW.restype = ctypes.c_int
_PeekMessageW = _user32.PeekMessageW
_PeekMessageW.argtypes = (ctypes.POINTER(_MSG), wintypes.HWND, wintypes.UINT,
                          wintypes.UINT, wintypes.UINT)
_PeekMessageW.restype = wintypes.BOOL

_WM_HOTKEY = 0x0312
_PM_REMOVE = 0x0001
_HOTKEY_ID = 47124


def _enable_dpi_awareness():
    """Activa DPI awareness en el hilo principal ANTES de crear ventanas.

    Sin esto Windows reescala las ventanas de Tk con el escalado del escritorio
    y, al usar transparencia por color-key (sin composición DWM), el reescalado
    sale con dientes de sierra. Con awareness, 1 píxel lógico = 1 píxel físico."""
    if not hasattr(ctypes, "windll"):
        return
    try:
        PER_MONITOR_V2 = ctypes.c_void_p(-4)     # DPI_AWARENESS_CONTEXT
        if ctypes.windll.user32.SetProcessDpiAwarenessContext(PER_MONITOR_V2):
            return
    except Exception:
        pass
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
        return
    except Exception:
        pass
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass


_enable_dpi_awareness()

def _frozen():
    return bool(getattr(sys, "frozen", False))


def resource_dir():
    """Recursos del bundle de PyInstaller (panel/, whisper_bin/, whisper_vulkan/).
    Normal: carpeta del .py. Congelado: sys._MEIPASS (_internal)."""
    if _frozen():
        return getattr(sys, "_MEIPASS",
                       os.path.dirname(os.path.abspath(sys.executable)))
    return os.path.dirname(os.path.abspath(__file__))


def data_dir():
    """Datos externos junto al .exe (models/, config, log, .tmp/).
    Normal: carpeta del .py. Congelado: carpeta del ejecutable."""
    if _frozen():
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


SCRIPT_DIR = data_dir()          # datos externos, junto a dicta.exe
RESOURCE_DIR = resource_dir()    # recursos incluidos en el bundle
CONFIG_FILE = os.path.join(SCRIPT_DIR, "dicta_config.json")
LOG_FILE = os.path.join(SCRIPT_DIR, "dicta.log")
# Log del MOTOR (stderr de whisper-server): se reescribe en cada arranque de
# motor y sirve para comprobar EN QUE dispositivo GPU carga el modelo (ggml
# imprime «using VulkanN backend»). Solo diagnostico; no afecta a la app.
SERVER_LOG = os.path.join(SCRIPT_DIR, "whisper_server.log")
# VERSION UNICA de la app. Es el UNICO sitio donde se cambia la version: de
# aqui sale `/state.version` (el panel la pinta como vX.Y.Z) y el log de
# arranque. El comparador de actualizaciones tambien la usa. `APP_VERSION` se
# conserva como alias por compatibilidad.
VERSION = "1.0.7"
APP_VERSION = VERSION
WHISPER_EXE = os.path.join(RESOURCE_DIR, "whisper_bin", "Release", "whisper-cli.exe")
# Motores GPU: cada backend vive en su carpeta con su whisper-server + DLLs.
#   vulkan (AMD/Intel/NVIDIA) y cuda (NVIDIA). CPU usa whisper-cli.
WHISPER_VULKAN = os.path.join(RESOURCE_DIR, "whisper_vulkan", "whisper-server.exe")
WHISPER_CUDA = os.path.join(RESOURCE_DIR, "whisper_cuda", "whisper-server.exe")
WHISPER_ROCM = os.path.join(RESOURCE_DIR, "whisper_rocm", "whisper-server.exe")
MODEL_DIR = os.path.join(SCRIPT_DIR, "models")
LOCK_PORT = 47123
SERVER_PORT = 47801
PANEL_PORT = 47810          # API local para el panel web (dicta_panel.py)
# Abrir el panel al arrancar: dicta vive en la bandeja y no tiene ventana
# propia, así que sin esto lanzarla no muestra NADA (parece que no arrancó).
# `--no-panel` lo desactiva (útil si se auto-inicia con Windows).
PANEL_ON_START = True

# Motores disponibles (se detectan al arrancar).
ENGINES = ("auto", "vulkan", "cuda", "rocm", "cpu")

SAMPLE_RATE = 16000
SILENCE_TIMEOUT = 1.05    # pausa que corta la escucha (config "--silence")
MIN_DURATION = 0.35       # ignora audio más corto (s)
MIN_RMS = 0.0015          # piso de ruido electrónico
VOICE_THRESHOLD_DEFAULT = 0.006   # RMS minimo (0..1) para considerar voz
SILENCE_WAIT_MIN, SILENCE_WAIT_MAX = 0.2, 600.0
CHUNK = int(SAMPLE_RATE * 0.05)  # 20 Hz UI/audio meter for the live waveform

MODELS = {
    "tiny": "ggml-tiny-q5_1.bin",
    "base": "ggml-base-q5_1.bin",
    "small": "ggml-small-q5_1.bin",
    "medium": "ggml-medium-q5_0.bin",
    "large": "ggml-large-v3-q5_0.bin",
    "turbo": "ggml-large-v3-turbo-q5_0.bin",
}

MODEL_LABELS = {
    "tiny": "Whisper Tiny", "base": "Whisper Base", "small": "Whisper Small",
    "medium": "Whisper Medium", "large": "Whisper Large v3",
    "turbo": "Whisper Large v3 Turbo",
}
ENGINE_LABELS = {"auto": "Automatico", "vulkan": "GPU (Vulkan)",
                 "cuda": "GPU (CUDA, NVIDIA)", "rocm": "GPU (ROCm, AMD)",
                 "cpu": "CPU"}


ARTIFACTS = {"audio en blanco", "blank audio", "gracias", "muchas gracias",
             "subtítulos", "música", "musica", "audio"}


def log(msg):
    """Consola (si la hay) y archivo: con pythonw no existe stdout."""
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    try:
        if sys.stdout is not None:
            print(line, flush=True)
    except Exception:
        pass
    try:
        if os.path.exists(LOG_FILE) and os.path.getsize(LOG_FILE) > 1_000_000:
            os.remove(LOG_FILE)              # rota al pasar de ~1 MB
        with open(LOG_FILE, "a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    except Exception:
        pass


def config_get(key, default=None):
    try:
        with open(CONFIG_FILE, encoding="utf-8") as f:
            v = json.load(f).get(key)
            return default if v is None else v
    except Exception:
        return default


def config_set(key, value):
    d = {}
    try:
        if os.path.isfile(CONFIG_FILE):
            with open(CONFIG_FILE, encoding="utf-8") as f:
                d = json.load(f)
        d[key] = value
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(d, f)
    except Exception:
        pass


# ------------------------------------------ actualizacion desde la propia app
# PROMESA DE PRODUCTO (NO NEGOCIABLE): el AUDIO y el TEXTO de dicta NUNCA salen
# del equipo. La UNICA cosa que puede salir a la red es la COMPROBACION DE
# VERSION, y es solo una peticion GET a la API PUBLICA de GitHub
# (releases/latest) del repo de dicta para leer la lista publica de versiones.
# Esa peticion NO lleva ningun dato del usuario: ni identificadores, ni
# telemetria, ni el estado de la app, ni el audio ni el texto; lo unico que
# viaja es la propia URL publica (un GET anonimo). Ademas es DESACTIVABLE: el
# ajuste `check_updates` de dicta_config.json, ACTIVADO de fabrica, la
# enciende/apaga; con el apagado, la funcion sale ANTES de tocar la red (no se
# abre ninguna conexion).
#
# El estado de la ultima comprobacion se publica en `/state.update`:
#   {available, latest, url, notes, checked_at, progress}
# y el ajuste REAL (lo que hay en dicta_config.json) en `/state.check_updates`.
# Se comprueba con POST {"action":"check_update"} (respeta el ajuste: si esta
# apagado no toca la red) o POST {"action":"check_update","value":{"force":true}}
# (consulta GitHub AUNQUE este apagado: es una accion EXPLICITA del usuario, el
# enlace «Actualizar» del panel). Se descarga/in instala con
# POST {"action":"update"}, que NO lo bloquea el ajuste (tambien es explicito).
# El ajuste se enciende/apaga con
# POST {"action":"check_updates","value":true|false} y PERSISTE en
# dicta_config.json.
UPDATE_REPO = "JDMoreu/dicta"
UPDATE_API = f"https://api.github.com/repos/{UPDATE_REPO}/releases/latest"
UPDATE_UA = "dicta-update-check"     # GitHub exige un User-Agent en su API
# Estado publicado en /state.update. 'enabled'/'error'/'applied' son extra (el
# panel puede ignorarlos); los cinco de la especificacion estan siempre.
# 'enabled' refleja el ajuste REAL (`check_updates`), igual que la clave
# `check_updates` de /state, para que no haya dos verdades distintas.
UPDATE_STATE = {"available": False, "latest": "", "url": "", "notes": "",
                "checked_at": "", "progress": 0,
                "enabled": False, "error": "", "applied": "",
                "asset_url": "", "asset_size": 0, "asset_sha256": "",
                "staged_dir": ""}
_UPDATE_LOCK = threading.Lock()


def update_enabled():
    """True si la comprobacion de version esta activa (`check_updates`).

    ACTIVADA de fabrica: es lo unico que puede salir a la red, no lleva ningun
    dato del usuario y se puede desactivar con el ajuste `check_updates`.
    """
    return bool(config_get("check_updates", True))


def _version_tuple(value):
    """('1.0.1') -> (1, 0, 1). Tolerante: 'v1.0', '1.0.1', '1' funcionan."""
    parts = []
    for chunk in str(value or "").strip().lstrip("vV").split("."):
        digits = ""
        for ch in chunk:
            if ch.isdigit():
                digits += ch
            else:
                break
        parts.append(int(digits) if digits else 0)
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts[:3])


def _pick_update_asset(assets):
    """(url, size, sha256) del ZIP portable de la release, o ('',0,'')."""
    best = None
    for a in assets or []:
        if not isinstance(a, dict):
            continue
        name = str(a.get("name") or "")
        if not name.lower().endswith(".zip"):
            continue
        if "portable" in name.lower():
            best = a
            break
        if best is None:
            best = a
    if not best:
        return "", 0, ""
    url = str(best.get("browser_download_url") or "")
    try:
        size = int(best.get("size") or 0)
    except (TypeError, ValueError):
        size = 0
    digest = str(best.get("digest") or "")
    sha = digest.split("sha256:")[-1].strip().lower() if "sha256" in digest \
        else ""
    return url, size, sha


def _update_blank(reason="", enabled=None):
    UPDATE_STATE.update({"available": False, "latest": "", "url": "",
                         "notes": "", "checked_at": "", "progress": 0,
                         "error": reason, "applied": "",
                         "asset_url": "", "asset_size": 0,
                         "asset_sha256": "", "staged_dir": ""})
    if enabled is not None:
        UPDATE_STATE["enabled"] = enabled
    return dict(UPDATE_STATE)


def check_update(force=False):
    """Consulta la ultima release de GitHub.

    Sin `force`, respeta el ajuste `check_updates`: si esta apagado NO toca la
    red (devuelve el estado con `enabled=False` y una nota). Con `force=True`
    -- POST {"action":"check_update","value":{"force":true}} -- consulta GitHub
    AUNQUE el ajuste este apagado: es una accion EXPLICITA del usuario (el
    enlace «Actualizar» del panel), no una comprobacion de fondo. En ambos
    casos es un GET anonimo a la API publica de GitHub y rellena
    `available/latest/url/notes/checked_at`; nunca envia datos del usuario.
    """
    if not force and not update_enabled():
        log("Actualizaciones: comprobacion desactivada; no se consulta la red.")
        return _update_blank("", enabled=False)
    _update_blank("", enabled=update_enabled())
    import urllib.request
    try:
        req = urllib.request.Request(
            UPDATE_API,
            headers={"User-Agent": UPDATE_UA,
                     "Accept": "application/vnd.github+json"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8", "replace"))
        tag = str(data.get("tag_name") or "").strip()
        latest = tag.lstrip("vV")
        url = str(data.get("html_url") or "")
        notes = str(data.get("body") or "")
        asset_url, asset_size, asset_sha = _pick_update_asset(
            data.get("assets") or [])
        available = _version_tuple(latest) > _version_tuple(VERSION)
        UPDATE_STATE.update({
            "enabled": update_enabled(), "available": available, "latest": latest,
            "url": url, "notes": notes,
            "checked_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "progress": 0, "error": "", "applied": "",
            "asset_url": asset_url, "asset_size": asset_size,
            "asset_sha256": asset_sha})
        log(f"Actualizaciones: ultima {latest} "
            f"({'hay version nueva' if available else 'ya al dia'}); "
            f"consulta anonima, sin datos del usuario.")
    except Exception as e:
        UPDATE_STATE.update({"error": str(e),
                             "checked_at": time.strftime("%Y-%m-%d %H:%M:%S")})
        log(f"Actualizaciones: no se pudo comprobar la version ({e}).")
    return dict(UPDATE_STATE)


def _sha256_file(path, progress=None):
    import hashlib
    h = hashlib.sha256()
    total = os.path.getsize(path)
    done = 0
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
            done += len(block)
            if progress and total:
                progress(done, total)
    return h.hexdigest()


def download_update():
    """Descarga el paquete de la release y VERIFICA su integridad.

    Devuelve (ruta_zip, staging_dir) tras comprobar tamano y -- si la release
    publica sha256 en su digest -- el hash. Lanza excepcion si algo no cuadra.
    """
    import urllib.request
    asset_url = UPDATE_STATE.get("asset_url") or ""
    if not asset_url:
        raise RuntimeError("no hay paquete de release (haz una comprobacion)")
    size_expected = int(UPDATE_STATE.get("asset_size") or 0)
    sha_expected = str(UPDATE_STATE.get("asset_sha256") or "").lower()
    tmp = os.path.join(SCRIPT_DIR, ".tmp", "update")
    os.makedirs(tmp, exist_ok=True)
    zip_path = os.path.join(tmp, os.path.basename(asset_url) or "dicta-update.zip")
    part = zip_path + ".part"
    log(f"Actualizaciones: descargando {os.path.basename(zip_path)}"
        f"{f' ({size_expected} B)' if size_expected else ''} ...")
    req = urllib.request.Request(asset_url, headers={"User-Agent": UPDATE_UA})
    with urllib.request.urlopen(req, timeout=30) as resp, \
            open(part, "wb") as out:
        total = int(resp.headers.get("Content-Length") or size_expected or 0)
        done = 0
        while True:
            block = resp.read(1024 * 1024)
            if not block:
                break
            out.write(block)
            done += len(block)
            if total:
                with _UPDATE_LOCK:
                    UPDATE_STATE["progress"] = int(done * 90 / total)
    if size_expected and os.path.getsize(part) != size_expected:
        raise RuntimeError("el tamano descargado no cuadra "
                           f"({os.path.getsize(part)} != {size_expected})")
    os.replace(part, zip_path)
    if sha_expected:
        got = _sha256_file(zip_path)
        if got != sha_expected:
            raise RuntimeError("sha256 no cuadra "
                               f"({got[:12]}... != {sha_expected[:12]}...)")
        log(f"Actualizaciones: sha256 verificado ({got[:16]}...).")
    else:
        log("Actualizaciones: la release no publica sha256; verificado el tamano.")
    return zip_path, tmp


def _oem_encoding():
    """Codepage OEM con la que cmd.exe lee un .bat (para rutas con acentos).

    El ayudante es un .bat y lo interpreta cmd.exe, que NO lee UTF-8: hay que
    escribirlo en la codepage OEM de la maquina o una ruta de usuario con
    acentos se corrompe. `ascii` (lo que habia) directamente revienta.
    """
    try:
        import ctypes
        return "cp%d" % int(ctypes.windll.kernel32.GetOEMCP())
    except Exception:
        return "cp850"


def _write_helper(path, lines):
    """Escribe el .bat ayudante con finales CRLF y en la codepage de cmd.exe."""
    text = "\r\n".join(lines) + "\r\n"
    enc = _oem_encoding()
    try:
        data = text.encode(enc, "replace")
    except LookupError:
        data = text.encode("ascii", "replace")
    with open(path, "wb") as fh:
        fh.write(data)


def _helper_script(staging, dest, exe, tmp, frozen, updlog, app_pid):
    """Lineas del .bat ayudante de actualizacion.

    El ayudante espera a que la app se CIERRE (por PID, con tope de tiempo),
    copia el paquete COMPLETO con robocopy (con reintentos) y vuelve a arrancar
    la app en su ruta nueva. Deja REGISTRO POR PASOS en `update.log`, junto a la
    app, para poder diagnosticarlo si algo falla.

    Dos detalles que son la diferencia entre funcionar y no funcionar:

    * `/E` sin `/PURGE` SOBREESCRIBE lo que trae el paquete pero NO borra nada
      mas, asi que la configuracion y los datos del usuario (audios, textos,
      subidas, modelos extra) sobreviven; y `/XF` impide que el paquete pise
      nunca `dicta_config.json` ni los registros.
    * La espera mira la COLUMNA del PID (`/FO CSV` y la 2a columna con
      `for /f`), no un `findstr` de subcadena: con `/NH` a secas el PID podia
      coincidir con los digitos de la columna de memoria, y ademas
      `findstr /C:,"PID",` NO casa nunca (comprobado: devuelve 1 contra una
      linea que contiene ese texto), asi que el ayudante creia que la app ya
      se habia cerrado y copiaba/relanzaba con la app viva.
    """
    L = [
        "@echo off",
        "rem Ayudante de actualizacion de dicta (generado por la app).",
        "rem Espera a que la app se cierre, sustituye los ficheros del paquete y",
        "rem la vuelve a arrancar. Deja registro por pasos en update.log.",
        "setlocal enableextensions",
        'set "LOG=%s"' % updlog,
        'set "SRC=%s"' % staging,
        'set "DST=%s"' % dest,
        'set "EXE=%s"' % exe,
        'set "APPPID=%d"' % app_pid,
        'set "TMPU=%s"' % tmp,
        'set "PIDCHK=%s"' % os.path.join(tmp, "pid_check.txt"),
    ]
    if not frozen:
        pyw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
        if not os.path.isfile(pyw):
            pyw = sys.executable
        L += ['set "PYW=%s"' % pyw,
              'set "SCRIPT=%s"' % os.path.abspath(__file__)]
    L += [
        '>>"%LOG%" echo [%DATE% %TIME%] == ayudante de actualizacion: iniciado '
        '(app pid %APPPID%) ==',
        '>>"%LOG%" echo [%DATE% %TIME%] paquete: %SRC%',
        '>>"%LOG%" echo [%DATE% %TIME%] destino: %DST%',
        "set /a W=0",
        ":wait_app",
        'set "ALIVE="',
        'tasklist /FI "PID eq %APPPID%" /FO CSV /NH > "%PIDCHK%" 2>nul',
        'for /f "usebackq tokens=2 delims=," %%a in ("%PIDCHK%") do '
        'if "%%~a"=="%APPPID%" set "ALIVE=1"',
        "if not defined ALIVE goto app_closed",
        "ping -n 2 127.0.0.1 >nul",
        "set /a W+=1",
        "if %W% GEQ 90 goto app_alive",
        "goto wait_app",
        ":app_closed",
        '>>"%LOG%" echo [%DATE% %TIME%] la app cerro (tras %W% s); copiando el '
        'paquete completo...',
        "set /a T=0",
        ":copy",
        'robocopy "%SRC%" "%DST%" /E /NFL /NDL /NJH /NJS /NP /R:3 /W:2 '
        '/XF dicta_config.json update.log dicta.log dicta_crash.log '
        '>>"%LOG%" 2>&1',
        'set "RC=%ERRORLEVEL%"',
        "set /a T+=1",
        '>>"%LOG%" echo [%DATE% %TIME%] copia intento %T%: robocopy rc=%RC%',
        "if %RC% GEQ 8 (",
        "  if %T% GEQ 5 goto copy_failed",
        "  ping -n 3 127.0.0.1 >nul",
        "  goto copy",
        ")",
        '>>"%LOG%" echo [%DATE% %TIME%] paquete sustituido; relanzando la app...',
    ]
    if frozen:
        L += ['start "" "%EXE%"',
              '>>"%LOG%" echo [%DATE% %TIME%] app relanzada: %EXE%']
    else:
        L += ['cd /d "%DST%"',
              'start "" "%PYW%" "%SCRIPT%"',
              '>>"%LOG%" echo [%DATE% %TIME%] app relanzada: %PYW% %SCRIPT%']
    L += [
        'start "" /b cmd /c "ping -n 4 127.0.0.1 >nul & rd /s /q ""%TMPU%"""',
        '>>"%LOG%" echo [%DATE% %TIME%] ayudante terminado.',
        "exit /b 0",
        ":copy_failed",
        '>>"%LOG%" echo [%DATE% %TIME%] ERROR: robocopy no pudo completar '
        '(rc=%RC%); NO se relanza.',
        "exit /b 1",
        ":app_alive",
        '>>"%LOG%" echo [%DATE% %TIME%] ERROR: la app (pid %APPPID%) sigue viva '
        'tras %W% s; no se toca nada.',
        "exit /b 1",
    ]
    return L


def _spawn_helper(helper, workdir):
    """Lanza el ayudante DESACOPLADO del proceso de la app. Devuelve su PID.

    Aqui estaban los DOS fallos que dejaban la actualizacion a medias:

    1) Los descriptores heredados. Si el ayudante hereda la consola o el
       registro al que esta redirigida la app, se queda colgado en cuanto la
       app se cierra (una orden con tuberia sobre un `stdout` ya roto no
       termina nunca): no copia nada ni la relanza. `stdin/stdout/stderr` van a
       NULO y el ayudante escribe su registro en un FICHERO, sin tuberias.
    2) `DETACHED_PROCESS` **NO** sirve para esto. Con DETACHED el ayudante se
       queda SIN CONSOLA y cualquier herramienta que consulte el sistema
       (`tasklist`) escribe en el VACIO: medido, devuelve **0 bytes** con
       codigo 0. La espera por PID creia entonces que la app ya se habia
       cerrado, copiaba con la app AUN VIVA (su `.exe` no se puede sustituir),
       y relanzaba mientras la instancia vieja tenia el candado puesto: la
       nueva salia con «dicta ya esta abierto» y se veia EXACTAMENTE «se
       cierra, no se sustituye nada y no vuelve a abrirse».
       `CREATE_NO_WINDOW` le da una consola PROPIA y OCULTA: `tasklist`
       funciona, no aparece ninguna ventana y no depende de la app.
       Ademas se intenta salir del job (`CREATE_BREAKAWAY_FROM_JOB`), con
       respaldo si el job no lo permite (da `WinError 5`).
    """
    base = 0x08000000 | 0x00000200     # CREATE_NO_WINDOW | CREATE_NEW_PROCESS_GROUP
    last = None
    for flags in (base | 0x01000000, base):   # + CREATE_BREAKAWAY_FROM_JOB
        try:
            p = subprocess.Popen(
                ["cmd", "/c", helper], creationflags=flags, close_fds=True,
                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL, cwd=workdir)
            log(f"Actualizaciones: ayudante lanzado desacoplado "
                f"(pid {p.pid}, flags 0x{flags:08x}).")
            return p.pid
        except OSError as e:
            last = e
    raise last if last is not None else RuntimeError("no se pudo lanzar")


def prepare_update(zip_path, tmp):
    """Extrae el paquete y deja listo el ayudante que sustituye los ficheros.

    El ayudante (`apply_update.cmd`) ESPERA a que esta app se cierre (no se
    puede reemplazar un .exe en caliente), copia el paquete sobre la carpeta de
    la app y la vuelve a arrancar. Devuelve la ruta del ayudante.
    """
    import zipfile
    staging = os.path.join(tmp, "new")
    if os.path.isdir(staging):
        shutil.rmtree(staging, ignore_errors=True)
    os.makedirs(staging, exist_ok=True)
    with zipfile.ZipFile(zip_path) as zf:
        bad = zf.testzip()
        if bad:
            raise RuntimeError(f"ZIP corrupto en {bad}")
        zf.extractall(staging)
    with _UPDATE_LOCK:
        UPDATE_STATE["staged_dir"] = staging
        UPDATE_STATE["progress"] = 95
    # Carpeta a sustituir y orden de arranque del ejecutable.
    dest = SCRIPT_DIR
    exe = os.path.join(dest, "dicta.exe")
    frozen = _frozen()
    helper = os.path.join(tmp, "apply_update.cmd")
    updlog = os.path.join(dest, "update.log")
    lines = _helper_script(staging, dest, exe, tmp, frozen, updlog, os.getpid())
    _write_helper(helper, lines)
    try:
        with open(updlog, "a", encoding="utf-8", errors="replace") as fh:
            fh.write("[%s] app: paquete preparado (%s -> %s); ayudante %s\n"
                     % (time.strftime("%Y-%m-%d %H:%M:%S"), staging, dest, helper))
    except Exception:
        pass
    with _UPDATE_LOCK:
        UPDATE_STATE["helper"] = helper
        UPDATE_STATE["portable"] = frozen
        UPDATE_STATE["update_log"] = updlog
    return helper


def apply_update(launch=True):
    """Descarga, verifica y aplica la actualizacion.

    Es una accion EXPLICITA del usuario (el enlace «Instalar» del panel), asi
    que NO la bloquea el ajuste `check_updates`: basta con que haya una version
    nueva conocida (`available`), aunque el ajuste este apagado y el estado lo
    haya rellenado una comprobacion FORZADA previa. En modo PORTABLE (exe
    congelado) lanza el ayudante y cierra la app para que la sustitucion ocurra
    en frio. En modo FUENTE (dicta.py) no puede sustituirse en marcha: deja el
    paquete verificado en `.tmp/update/new` y lo indica.
    """
    if not UPDATE_STATE.get("available"):
        return {"ok": False, "error": "no hay version nueva (comprueba antes)"}
    try:
        zip_path, tmp = download_update()
        helper = prepare_update(zip_path, tmp)
    except Exception as e:
        with _UPDATE_LOCK:
            UPDATE_STATE["progress"] = 0
            UPDATE_STATE["error"] = str(e)
        log(f"Actualizaciones: fallo al preparar la actualizacion ({e}).")
        return {"ok": False, "error": str(e)}
    with _UPDATE_LOCK:
        UPDATE_STATE["progress"] = 100
    frozen = bool(UPDATE_STATE.get("portable"))
    # Se aplica en LOS DOS MODOS. Antes el modo fuente se quedaba en
    # «descargado (modo fuente)» y quien probaba desde el codigo veia que «no
    # se actualiza»; el ayudante relanza el ejecutable congelado o, en modo
    # fuente, el interprete con este mismo script.
    try:
        hpid = _spawn_helper(helper, tmp)
    except Exception as e:
        with _UPDATE_LOCK:
            UPDATE_STATE["error"] = str(e)
        log(f"Actualizaciones: no se pudo lanzar el ayudante ({e}).")
        return {"ok": False, "error": str(e)}
    with _UPDATE_LOCK:
        UPDATE_STATE["applied"] = "reiniciando"
        UPDATE_STATE["helper_pid"] = hpid
    log(f"Actualizaciones: ayudante lanzado (pid {hpid}); la app se cerrara "
        f"para aplicar ({'portable' if frozen else 'fuente'}). "
        f"Registro: {UPDATE_STATE.get('update_log')}")
    if launch:
        def _quit_soon():
            time.sleep(1.2)              # dar tiempo a responder el POST
            try:
                if _control_ref is not None:
                    _control_ref.post_action("quit", None)   # cierre limpio (VRAM)
                else:
                    os._exit(0)
            except Exception:
                os._exit(0)
        threading.Thread(target=_quit_soon, daemon=True).start()
    return {"ok": True, "applied": True, "helper": helper}


# ------------------------------------------------------------------- ASR
def ensure_model(model_file: str) -> str:
    """Ruta del modelo; lo descarga si falta (solo la primera vez)."""
    path = os.path.join(MODEL_DIR, model_file)
    if os.path.isfile(path):
        return path
    os.makedirs(MODEL_DIR, exist_ok=True)
    url = f"https://huggingface.co/ggerganov/whisper.cpp/resolve/main/{model_file}"
    log(f"Descargando {model_file} (una sola vez)...")
    tmp = path + ".part"
    urllib.request.urlretrieve(url, tmp)
    os.replace(tmp, path)
    log("Modelo descargado.")
    return path


def transcribe(audio: np.ndarray, model_path: str, language: str,
               prompt: str = "", engine: str = None) -> str:
    """Transcribe float32 16k mono. Usa el motor configurado (auto/vulkan/
    cuda/cpu); si el GPU falla, cae al whisper-cli CPU. Nunca corre en el hilo
    de la GUI."""
    if audio.size == 0:
        return ""
    if engine is None:
        engine = pick_engine(config_get("engine", "auto"))
    # 1) GPU: servidor persistente (mucho más rápido).
    if engine in ("vulkan", "cuda"):
        srv = _get_server()
        text = srv.transcribe(audio, model_path, language, prompt, engine)
        if text is not None:
            return _clean_text(text)
        # Si falló, probamos el motor CPU como respaldo.
    # 2) CPU: whisper-cli por subprocess (trocea largos).
    return _transcribe_cpu(audio, model_path, language, prompt)


def _clean_text(text: str) -> str:
    return " ".join(text.split()).strip().strip('" ').strip()


def _transcribe_cpu(audio: np.ndarray, model_path: str, language: str,
                    prompt: str = "") -> str:
    chunks = [np.ascontiguousarray(audio, dtype=np.float32).reshape(-1)]
    if len(chunks[0]) > 30 * SAMPLE_RATE:
        chunks = []
        hop, overlap = int(26 * SAMPLE_RATE), int(0.5 * SAMPLE_RATE)
        start = 0
        while start < len(audio):
            chunks.append(np.ascontiguousarray(
                audio[start:start + hop], dtype=np.float32).reshape(-1))
            start += hop - overlap
    os.makedirs(os.path.join(SCRIPT_DIR, ".tmp"), exist_ok=True)
    wav = os.path.join(SCRIPT_DIR, ".tmp", f"in_{os.getpid()}.wav")
    out = []
    try:
        for c in chunks:
            sf.write(wav, c, SAMPLE_RATE, subtype="PCM_16")
            cmd = [WHISPER_EXE, "-m", model_path, "-l", language, "-nt",
                   "-bs", "1", "-t", str(max(4, (os.cpu_count() or 4) - 2)),
                   "-f", wav]
            if prompt:
                cmd += ["--prompt", prompt]
            flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            out_s, err_s, rc = _run_whisper_cli(cmd, flags, timeout=180)
            text = _clean_text(" ".join(l.strip() for l in out_s.splitlines()
                                        if l.strip()))
            if not text and rc != 0:
                errs = err_s.splitlines()
                log("whisper-cli falló: " + (errs[-1] if errs else "?"))
            if text:
                out.append(text)
    except FileNotFoundError:
        log(f"No está el motor: {WHISPER_EXE}")
    except subprocess.TimeoutExpired:
        log("whisper-cli tardó demasiado; subprocess terminado (la app sigue).")
    finally:
        try:
            os.remove(wav)
        except Exception:
            pass
    return " ".join(out)


# ------------------------------------------------------- detección de motor
_ENGINE_INFO = None


def detect_engines():
    """Detecta qué motores están disponibles en este equipo. Devuelve un dict:
    {'vulkan': bool, 'cuda': bool, 'gpus': [...]}. Se cachea."""
    global _ENGINE_INFO
    if _ENGINE_INFO is not None:
        return _ENGINE_INFO
    info = {"vulkan": os.path.isfile(WHISPER_VULKAN),
            "cuda": os.path.isfile(WHISPER_CUDA),
            "rocm": os.path.isfile(WHISPER_ROCM), "gpus": []}
    # NVIDIA: si hay nvidia-smi, hay GPU NVIDIA.
    try:
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        r = subprocess.run(["nvidia-smi", "--query-gpu=name",
                            "--format=csv,noheader"],
                           capture_output=True, text=True, timeout=4,
                           creationflags=flags)
        if r.returncode == 0 and r.stdout.strip():
            info["gpus"] = [l.strip() for l in r.stdout.splitlines() if l.strip()]
            info["nvidia"] = True
    except Exception:
        info["nvidia"] = False
    # Vulkan: si hay vulkan-1.dll, puede haber GPU AMD/Intel/NVIDIA vía Vulkan.
    vulkan_dll = os.path.join(os.environ.get("WINDIR", r"C:\Windows"),
                              "System32", "vulkan-1.dll")
    info["vulkan_runtime"] = os.path.isfile(vulkan_dll)
    _ENGINE_INFO = info
    return info


def pick_engine(pref: str) -> str:
    """Resuelve el motor a usar. pref en 'auto'|'vulkan'|'cuda'|'cpu'."""
    info = detect_engines()
    if pref in ("vulkan", "cuda", "rocm", "cpu"):
        # Si el pedido no está disponible, cae a auto.
        if pref == "vulkan" and not info["vulkan"]:
            return "cpu"
        if pref == "cuda" and not info["cuda"]:
            return "cpu"
        if pref == "rocm" and not info.get("rocm"):
            return "cpu"
        return pref
    # auto: NVIDIA+CUDA > Vulkan > CPU.
    if info.get("nvidia") and info["cuda"]:
        return "cuda"
    if info["vulkan"]:
        return "vulkan"
    return "cpu"


def engine_label(engine: str) -> str:
    return {"vulkan": "GPU (Vulkan)", "cuda": "GPU (CUDA)", "rocm": "GPU (ROCm)",
            "cpu": "CPU"}.get(engine, engine)


def _available_engines():
    """Motores que se pueden ofrecer en la UI según el hardware detectado."""
    info = detect_engines()
    out = ["auto"]
    if info["vulkan"] or info.get("vulkan_runtime"):
        out.append("vulkan")
    if info["cuda"]:
        out.append("cuda")
    if info.get("rocm"):
        out.append("rocm")
    out.append("cpu")
    return out


# Motivo, en lenguaje de usuario, de por que cada motor esta o no disponible
# en ESTE equipo. Nada de un "no compatible" seco: el autor tiene una GPU AMD y
# cree que ROCm es lo suyo, cuando en Windows nativo su GPU ya trabaja con
# Vulkan, que es la opcion optima aqui.
ENGINE_NOTE_BASE = (
    "Tu GPU AMD ya trabaja con Vulkan, que es la opcion optima en este "
    "equipo. ROCm aparece en la lista pero no se puede activar porque no "
    "funciona en Windows nativo con esta tarjeta (ROCm va por Linux/WSL y "
    "solo con GPUs soportadas), y CUDA es exclusivo de las GPU NVIDIA. No se "
    "te niega nada: Vulkan es la eleccion correcta en este equipo.")


def engine_reason(key, available):
    """Motivo de un motor, en lenguaje de usuario, segun su disponibilidad."""
    if key == "rocm":
        return ("ROCm no funciona en Windows nativo con esta tarjeta: va por "
                "Linux/WSL y solo con GPUs soportadas. No es cosa de tu "
                "equipo ni te quita nada.")
    if key == "cuda":
        if available:
            return "Usa tu GPU NVIDIA a traves de CUDA."
        return ("Es exclusivo de las GPU NVIDIA y este equipo no tiene una, "
                "por eso no se ofrece. No afecta a tu GPU AMD.")
    if key == "vulkan":
        if available:
            return ("Usa tu GPU AMD (tambien Intel/NVIDIA) a traves de "
                    "Vulkan: es la opcion optima en este equipo y la que ya "
                    "aprovecha tu tarjeta.")
        return ("Vulkan necesita el runtime de la GPU y no se detecto en "
                "este equipo.")
    if key == "cpu":
        return ("Siempre disponible. Mas lento que la GPU; se usa como "
                "respaldo cuando la GPU no puede.")
    return "Elige solo la mejor opcion disponible en este equipo."


# --- dispositivos GPU concretos -------------------------------------------
# El autor puede elegir no solo la TECNOLOGIA (Vulkan/CPU) sino QUE tarjeta,
# porque en este equipo hay DOS GPU Vulkan (una dedicada y una integrada) y
# quiere poder decidir en cual corre el modelo. whisper.cpp/ggml publica la
# lista REAL de dispositivos al inicializar el backend; se enumeran ejecutando
# el binario con `--help` (tarda ~0,2 s y no carga ningun modelo) y parseando
# las lineas «ggml_vulkan: N = NOMBRE | detalles». El resultado se CACHEA:
# /state se sondea muy a menudo y no se lanza un proceso por peticion.
_GPU_DEVICE_CACHE = {}

# Binario con backend GPU de cada tecnologia (solo Vulkan aqui: no hay CUDA ni
# ROCm). Las tecnologias sin binario no listan dispositivos.
ENGINE_SERVER_EXE = {"vulkan": WHISPER_VULKAN, "cuda": WHISPER_CUDA,
                     "rocm": WHISPER_ROCM}

_DEVICE_LINE_RE = re.compile(
    r"^\s*(?:ggml_)?(?:vulkan|cuda)[\w-]*:\s*(\d+)\s*=\s*(.+)$", re.IGNORECASE)


def list_gpu_devices(engine, force=False):
    """Dispositivos REALES del motor, tal cual los reporta el binario:
    [{'index': N, 'name': '...', 'desc': '...'}]. Lista vacia si la tecnologia
    no usa GPU (CPU) o no hay binario instalado. Cacheado (force reenumera)."""
    exe = ENGINE_SERVER_EXE.get(engine)
    if not exe or not os.path.isfile(exe):
        return []
    if not force and engine in _GPU_DEVICE_CACHE:
        return _GPU_DEVICE_CACHE[engine]
    devices = []
    try:
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        proc = subprocess.run([exe, "--help"], capture_output=True,
                              timeout=30, creationflags=flags)
        blob = ((proc.stderr or b"") + (proc.stdout or b"")).decode(
            "utf-8", "replace")
        for line in blob.splitlines():
            m = _DEVICE_LINE_RE.match(line)
            if not m:
                continue
            name, _, desc = m.group(2).strip().partition(" | ")
            devices.append({"index": int(m.group(1)), "name": name.strip(),
                            "desc": desc.strip()})
    except Exception as e:
        log(f"No se pudieron enumerar los dispositivos de {engine}: {e}")
    _GPU_DEVICE_CACHE[engine] = devices
    return devices


def gpu_device_pref(engine):
    """Preferencia de GPU guardada, normalizada: (pref, index) donde pref es
    'auto' o {'index': N} e index es el indice efectivo (None = auto). Si el
    indice guardado ya no existe entre los dispositivos del motor (otra
    tarjeta, otro equipo), cae a auto."""
    pref = config_get("gpu_device", "auto")
    index = None
    if isinstance(pref, dict):
        index = pref.get("index")
    elif isinstance(pref, (int, float)) and not isinstance(pref, bool):
        index = int(pref)
    if index is None:
        return "auto", None
    try:
        index = int(index)
    except (TypeError, ValueError):
        return "auto", None
    if any(d["index"] == index for d in list_gpu_devices(engine)):
        return {"index": index}, index
    return "auto", None


def engine_options():
    """Opciones de motor seleccionables + si estan disponibles AQUI, con un
    motivo en lenguaje de usuario por motor (lo pinta el panel) y la lista de
    dispositivos GPU concretos de cada tecnologia (vacia si no aplica)."""
    info = detect_engines()
    avail = {"auto": True,
             "vulkan": bool(info["vulkan"] or info.get("vulkan_runtime")),
             "cuda": bool(info["cuda"]),
             "rocm": bool(info.get("rocm")),
             "cpu": True}
    return [{"key": k, "label": ENGINE_LABELS.get(k, k),
             "available": avail.get(k, False),
             "reason": engine_reason(k, avail.get(k, False)),
             "devices": list_gpu_devices(k) if k in ENGINE_SERVER_EXE else []}
            for k in ENGINES]


def model_options():
    """Modelos conocidos con NOMBRE COMPLETO y si el fichero esta presente."""
    return [{"key": k, "name": MODEL_LABELS.get(k, k),
             "present": os.path.isfile(os.path.join(MODEL_DIR, f))}
            for k, f in MODELS.items()]


class WhisperServer:
    """Servidor whisper.cpp persistente (Vulkan o CUDA): carga el modelo una vez
    en la GPU y atiende cada dictado por HTTP. Reinicia solo si muere o cambia
    el modelo."""

    def __init__(self):
        self.proc = None
        self.model_path = None
        self.language = None
        self.engine = None
        self.device = None        # indice de GPU aplicado (None = auto)
        self._errfh = None        # handle del log del motor (stderr)
        self.lock = threading.Lock()

    def _server_exe(self, engine: str):
        return WHISPER_CUDA if engine == "cuda" else WHISPER_VULKAN

    def _http(self, path, data=None, timeout=120):
        import urllib.request
        url = f"http://127.0.0.1:{SERVER_PORT}{path}"
        req = urllib.request.Request(url, data=data)
        if data is not None:
            req.add_header("Content-Type",
                           "multipart/form-data; boundary=----dictaboundary")
        return urllib.request.urlopen(req, timeout=timeout)

    def _wait_ready(self, timeout=30.0):
        import urllib.request
        t0 = time.monotonic()
        while time.monotonic() - t0 < timeout:
            if self.proc.poll() is not None:
                return False
            try:
                self._http("/", timeout=1)
                return True
            except Exception:
                time.sleep(0.25)
        return False

    def ensure(self, model_path: str, language: str, engine: str) -> bool:
        """Arranca o reusa el servidor GPU para el modelo/idioma/motor dados.
        El dispositivo GPU concreto sale de la config (gpu_device)."""
        exe = self._server_exe(engine)
        if engine == "cpu" or not os.path.isfile(exe):
            return False
        _pref, device = gpu_device_pref(engine)
        if (self.proc is not None and self.proc.poll() is None
                and self.model_path == model_path and self.language == language
                and self.engine == engine and self.device == device):
            return True
        self.stop()
        try:
            flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            cmd = [exe, "-m", model_path, "--host", "127.0.0.1",
                   "--port", str(SERVER_PORT), "-l", language]
            if device is not None:
                # QUE tarjeta usar: el indice tal cual lo lista el motor. Sin
                # este flag, whisper.cpp usa el dispositivo 0 (la dedicada).
                cmd += ["--device", str(device)]
            if engine == "vulkan":
                # En Vulkan los "threads" controlan el offload; 0 = auto.
                cmd += ["-t", str(max(4, (os.cpu_count() or 4) - 2))]
            try:
                self._errfh = open(SERVER_LOG, "wb")   # log del motor (prueba)
            except Exception:
                self._errfh = None
            self.proc = subprocess.Popen(
                cmd, stdout=subprocess.DEVNULL,
                stderr=self._errfh if self._errfh is not None
                else subprocess.DEVNULL,
                creationflags=flags)
        except Exception as e:
            log(f"Servidor {engine_label(engine)} no arrancó: {e}")
            self.proc = None
            return False
        if not self._wait_ready():
            log(f"Servidor {engine_label(engine)} no respondió; uso CPU.")
            self.stop()
            return False
        self.model_path, self.language, self.engine = model_path, language, engine
        self.device = device
        where = ("auto (dispositivo 0)" if device is None
                 else f"dispositivo {device}")
        log(f"Motor {engine_label(engine)} listo ({where}).")
        return True

    def transcribe(self, audio, model_path, language, prompt="", engine="auto"):
        """Devuelve el texto o None si falla (para caer al CPU)."""
        with self.lock:
            if not self.ensure(model_path, language, engine):
                return None
            try:
                wav_bytes = _wav_bytes(audio)
            except Exception:
                return None
            # El servidor IGNORA el flag -l del arranque: el idioma y el prompt
            # solo se aplican si viajan como campos en cada petición.
            fields = [("language", language or "auto")]
            if prompt:
                fields.append(("prompt", prompt))
            body = b""
            for key, value in fields:
                body += (f'------dictaboundary\r\n'
                         f'Content-Disposition: form-data; name="{key}"\r\n\r\n'
                         f'{value}\r\n').encode("utf-8")
            body += (b'------dictaboundary\r\n'
                     b'Content-Disposition: form-data; name="file"; '
                     b'filename="a.wav"\r\nContent-Type: audio/wav\r\n\r\n'
                     + wav_bytes + b"\r\n------dictaboundary--\r\n")
            try:
                r = self._http("/inference", body, timeout=120)
                import json as _json
                data = _json.loads(r.read().decode("utf-8", "replace"))
                return data.get("text", "")
            except Exception as e:
                log(f"Fallo contra el servidor {engine_label(engine)}: {e}; uso CPU.")
                return None

    def stop(self):
        if self.proc is not None:
            try:
                self.proc.terminate()
                self.proc.wait(timeout=5)
            except Exception:
                try:
                    self.proc.kill()
                except Exception:
                    pass
            self.proc = None
        try:
            if self._errfh is not None:
                self._errfh.close()
        except Exception:
            pass
        self._errfh = None
        self.engine = None
        self.device = None


def _wav_bytes(audio: np.ndarray) -> bytes:
    """WAV PCM16 en memoria para enviar al servidor."""
    import io
    buf = io.BytesIO()
    sf.write(buf, np.ascontiguousarray(audio, dtype=np.float32).reshape(-1),
             SAMPLE_RATE, subtype="PCM_16", format="WAV")
    return buf.getvalue()


_SERVER = None


def _get_server():
    global _SERVER
    if _SERVER is None:
        _SERVER = WhisperServer()
    return _SERVER


# ------------------------------------------- hijos y CIERRE LIMPIO (VRAM)
# En Windows los subprocess NO mueren con su padre: si dicta termina, el
# whisper-server.exe (Vulkan/CUDA) sobrevive con el modelo cargado en la VRAM
# como proceso parásito. Se registran los hijos aquí para poder matarlos en el
# cierre y se hace un barrido extra por si alguno se resiste.
_TRANSIENT_PIDS = set()          # pids de whisper-cli (CPU) en curso
_TRANSIENT_LOCK = threading.Lock()
_SHUTDOWN_LOCK = threading.Lock()
_SHUTDOWN_DONE = False


def _register_child(pid):
    with _TRANSIENT_LOCK:
        _TRANSIENT_PIDS.add(pid)


def _unregister_child(pid):
    with _TRANSIENT_LOCK:
        _TRANSIENT_PIDS.discard(pid)


def _kill_pid(pid):
    """Mata un proceso por PID, sin shell y sin necesitar UAC."""
    try:
        PROCESS_TERMINATE = 0x0001
        h = _kernel32.OpenProcess(PROCESS_TERMINATE, False, int(pid))
        if h:
            try:
                _kernel32.TerminateProcess(h, 1)
            finally:
                _kernel32.CloseHandle(h)
    except Exception:
        pass


def _run_whisper_cli(cmd, flags, timeout=180):
    """whisper-cli por subprocess REGISTRANDO el pid.

    ``subprocess.run`` no deja matar el hijo a mitad de camino: si dicta cierra
    mientras transcribe, el whisper-cli.exe quedaría de huérfano. Con Popen se
    puede matar desde el cierre (``_kill_pid``).
    """
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         creationflags=flags)
    _register_child(p.pid)
    try:
        out, err = p.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        _kill_pid(p.pid)
        try:
            p.communicate(timeout=5)
        except Exception:
            pass
        raise
    finally:
        _unregister_child(p.pid)
    return (out.decode("utf-8", "replace"),
            err.decode("utf-8", "replace"), p.returncode)


def _reap_orphan_whisper(timeout=8):
    """Mata cualquier whisper-server/cli de ESTA instalación que siga vivo.

    Filtra por ruta (``RESOURCE_DIR/whisper_*``) para no tocar nada de otro
    programa. Sirve igual para el cierre normal y para limpiar al arrancar lo
    que dejó una ejecución que murió de golpe (kill, cuelgue).
    """
    try:
        base = os.path.join(RESOURCE_DIR, "whisper_").replace("'", "''")
        filt = ("Name='whisper-server.exe' or Name='whisper-cli.exe' or "
                "Name='whisper.exe'")
        ps = ("$p = @(Get-CimInstance Win32_Process -Filter \"" + filt +
              "\" | Where-Object { $_.ExecutablePath -like '" + base +
              "*' }); $n = 0; $p | ForEach-Object { try { Stop-Process -Id "
              "$_.ProcessId -Force -ErrorAction Stop; $n++ } catch {} }; $n")
        r = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                           capture_output=True, text=True, timeout=timeout,
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        n = (r.stdout or "").strip()
        if n and n not in ("0", ""):
            log(f"Cierre limpio: matados {n} proceso(s) whisper sueltos.")
        return n
    except Exception:
        return None


def shutdown_service(reason="salida"):
    """CIERRE LIMPIO: suelta el modelo de la GPU y mata todo hijo vivo.

    Idempotente. Lo llaman la bandeja (Salir), el botón del panel y el quit por
    POST ANTES de tocar la GUI. Sin esto, ``os._exit(0)`` dejaba vivo el
    whisper-server con el modelo cargado en la VRAM (el proceso parásito que
    vaciaba la memoria de la gráfica). También para los hilos de audio y de
    transcripción.
    """
    global _SHUTDOWN_DONE
    with _SHUTDOWN_LOCK:
        if _SHUTDOWN_DONE:
            return
        _SHUTDOWN_DONE = True
    log(f"Cierre limpio ({reason}): liberando GPU y parando servicios...")
    # 1) Transcripciones en curso (whisper-cli CPU): a la calle.
    with _TRANSIENT_LOCK:
        pend = list(_TRANSIENT_PIDS)
        _TRANSIENT_PIDS.clear()
    for pid in pend:
        _kill_pid(pid)
    # 2) Reunión en curso: para captura/mezcla y cierra el .wav/.md.
    try:
        if getattr(_meeting, "request_stop", None):
            _meeting.request_stop(cancel=False)
        if getattr(_meeting, "proc", None):
            _meeting.proc.join(timeout=6)
    except Exception:
        pass
    # 3) Cola de audios (decodifica/transcribe en su hilo daemon).
    try:
        _audio_queue.stop()
    except Exception:
        pass
    # 4) Micro del dictado y prueba de micro.
    try:
        if _mic is not None:
            _mic.stop()
    except Exception:
        pass
    try:
        _mictest.cancel()
        th = getattr(_mictest, "_thread", None)
        if th is not None:
            th.join(timeout=3)
    except Exception:
        pass
    # 5) MODELO FUERA DE LA GPU: termina el whisper-server (Vulkan/CUDA).
    try:
        _get_server().stop()
    except Exception:
        pass
    # 6) Barrido final: cualquier whisper que se haya resistido o quedara de
    #    una ejecución anterior.
    _reap_orphan_whisper()
    log("Cierre limpio: GPU liberada y sin procesos whisper vivos.")


# ------------------------------------------------------------- entrega
# Inserción primaria mediante Windows UI Automation; clipboard + SendInput
# Ctrl+V queda como fallback para controles sin patrón de valor editable.

_VK_CTRL, _VK_V = 0x11, 0x56


class _MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long), ("dy", ctypes.c_long),
                ("mouseData", ctypes.c_ulong), ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong), ("dwExtraInfo", ctypes.c_void_p)]


class _KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", ctypes.c_ushort), ("wScan", ctypes.c_ushort),
                ("dwFlags", ctypes.c_ulong), ("time", ctypes.c_ulong),
                ("dwExtraInfo", ctypes.c_void_p)]


class _UNION(ctypes.Union):
    _fields_ = [("mi", _MOUSEINPUT), ("ki", _KEYBDINPUT)]


class _INPUT(ctypes.Structure):
    _anonymous_ = ("u",)
    _fields_ = [("type", ctypes.c_ulong), ("u", _UNION)]


def _send_key_event(vk=0, scan=0, flags=0):
    i = _INPUT()
    i.type = 1
    i.ki.wVk = vk
    i.ki.wScan = scan
    i.ki.dwFlags = flags
    if not _user32.SendInput(1, ctypes.byref(i), ctypes.sizeof(i)):
        err = _kernel32.GetLastError()
        log(f"SendInput falló (size={ctypes.sizeof(i)}, último error={err})")
        raise OSError("SendInput falló")


def _key(vk: int, up: bool = False, extended: bool = False):
    # KEYEVENTF_KEYUP (2) | KEYEVENTF_EXTENDEDKEY (1): Insert es tecla
    # extendida; sin el bit, algunas apps no la ven como Insert.
    _send_key_event(vk=vk, flags=(2 if up else 0) | (1 if extended else 0))


def clipboard_set(text: str) -> bool:
    CF_UNICODETEXT, GMEM_MOVEABLE = 13, 0x0002
    u, k = _user32, _kernel32
    # 64 bits: hay que declarar restype/argtypes, si no los HANDLE se truncam
    k.GlobalAlloc.restype = ctypes.c_void_p
    k.GlobalAlloc.argtypes = (ctypes.c_uint, ctypes.c_size_t)
    k.GlobalLock.restype = ctypes.c_void_p
    k.GlobalLock.argtypes = (ctypes.c_void_p,)
    k.GlobalUnlock.argtypes = (ctypes.c_void_p,)
    k.GlobalFree.argtypes = (ctypes.c_void_p,)
    u.SetClipboardData.argtypes = (ctypes.c_uint, ctypes.c_void_p)
    u.SetClipboardData.restype = ctypes.c_void_p
    data = ctypes.create_unicode_buffer(text)
    h = k.GlobalAlloc(GMEM_MOVEABLE, ctypes.sizeof(data))
    if not h:
        return False
    p = k.GlobalLock(h)
    if not p:
        k.GlobalFree(h)
        return False
    ctypes.memmove(p, data, ctypes.sizeof(data))
    k.GlobalUnlock(h)
    ok = False
    for _ in range(5):                 # maneja portapapeles ocupado por otra app
        if u.OpenClipboard(0):
            u.EmptyClipboard()
            ok = bool(u.SetClipboardData(CF_UNICODETEXT, h))
            u.CloseClipboard()
            break
        time.sleep(0.05)
    if not ok:
        k.GlobalFree(h)
    return ok


_UIA_SET_VALUE_PS = r"""
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
$hwnd = [IntPtr]([Int64]$env:DICTA_TARGET_HWND)
$uiaRoot = [System.Windows.Automation.AutomationElement]::RootElement
$titleCondition = New-Object System.Windows.Automation.PropertyCondition(
    [System.Windows.Automation.AutomationElement]::NameProperty,
    $env:DICTA_TARGET_TITLE)
$root = $uiaRoot.FindFirst([System.Windows.Automation.TreeScope]::Children, $titleCondition)
if ($null -ne $root -and $hwnd -ne [IntPtr]::Zero -and
    $root.Current.NativeWindowHandle -ne $hwnd.ToInt32()) { $root = $null }
if ($null -eq $root) {
    $condition = New-Object System.Windows.Automation.PropertyCondition(
    [System.Windows.Automation.AutomationElement]::NativeWindowHandleProperty,
    [int]$env:DICTA_TARGET_HWND)
    $root = $uiaRoot.FindFirst([System.Windows.Automation.TreeScope]::Children, $condition)
}
if ($null -eq $root) { $root = [System.Windows.Automation.AutomationElement]::FromHandle($hwnd) }
if ($null -eq $root) { throw 'No se pudo abrir la ventana destino en UI Automation' }
$target = $null
$editInfo = @()
for ($attempt = 0; $attempt -lt 5 -and $null -eq $target; $attempt++) {
    $items = $root.FindAll([System.Windows.Automation.TreeScope]::Descendants,
                           [System.Windows.Automation.Condition]::TrueCondition)
    $focusedEdit = $null
    for ($i = 0; $i -lt $items.Count; $i++) {
        $element = $items.Item($i)
        $current = $element.Current
        if ($current.ControlType -ne [System.Windows.Automation.ControlType]::Edit) { continue }
        $pattern = $null
        $hasValue = $element.TryGetCurrentPattern(
            [System.Windows.Automation.ValuePattern]::Pattern, [ref]$pattern)
        $editInfo += ("name='" + $current.Name + "' enabled=" + $current.IsEnabled + " value=" + $hasValue)
        if (-not $current.IsEnabled -or -not $hasValue) { continue }
        if ($pattern.Current.IsReadOnly) { continue }
        if ($current.Name -eq 'Prompt') { $target = $element; break }
        if ($current.HasKeyboardFocus) { $focusedEdit = $element }
    }
    if ($null -eq $target) { $target = $focusedEdit }
    if ($null -eq $target) { Start-Sleep -Milliseconds 60 }
}
if ($null -eq $target) {
    $info = $editInfo -join '; '
    throw ("No hay campo editable. hwnd=" + $hwnd + "; raíz='" + $root.Current.Name +
           "'; edits=" + $info)
}
$value = $target.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern)
$existing = $value.Current.Value
if ($existing -eq '?' -or $existing -eq [string][char]0x200B) { $existing = '' }
$separator = ''
if ($existing.Length -gt 0 -and $existing -notmatch '\s$') { $separator = ' ' }
$value.SetValue($existing + $separator + $env:DICTA_TEXT)
try { $target.SetFocus() } catch {}
[Console]::Write('DICTA_UIA_OK')
"""


_panel_host = None      # lo publica Overlay.__init__: lo usa el carril de entrega
_control_ref = None     # lo publica Overlay.__init__: lo usa la actualizacion
_ultimo_destino = 0     # última ventana NO de dicta que tuvo el foco
_ultimo_destino_titulo = ""


def _recordar_destino() -> None:
    """Apunta la última ventana ajena con el foco.

    Es el destino de rescate: si el usuario dicta con el panel delante, el
    destino grabado es el panel y el texto acabaría dentro de dicta. Con esto se
    pega donde estaba trabajando, que es lo que espera. Se llama en cada vuelta
    del bucle de servicio (unas 40 veces por segundo: son dos llamadas de
    Win32, sin enumerar ventanas).
    """
    global _ultimo_destino, _ultimo_destino_titulo
    try:
        hwnd = _user32.GetForegroundWindow()
    except Exception:
        return
    if not hwnd or hwnd == _ultimo_destino:
        return
    if _es_ventana_propia(hwnd):
        return
    _ultimo_destino = hwnd
    _ultimo_destino_titulo = _fg_title()


def _win_pid(hwnd) -> int:
    """PID del proceso dueño de la ventana (0 si no se puede averiguar)."""
    try:
        _user32.GetWindowThreadProcessId.argtypes = [
            wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
        _user32.GetWindowThreadProcessId.restype = wintypes.DWORD
        owner = wintypes.DWORD()
        _user32.GetWindowThreadProcessId(hwnd, ctypes.byref(owner))
        return int(owner.value)
    except Exception:
        return 0


def _esta_elevado(pid=None) -> bool:
    """True si el proceso (el nuestro, por defecto) corre como administrador."""
    try:
        pid = int(pid or os.getpid())
        _k32 = ctypes.WinDLL("kernel32", use_last_error=True)
        _adv = ctypes.WinDLL("advapi32", use_last_error=True)
        h = _k32.OpenProcess(0x1000, False, pid)      # QUERY_LIMITED_INFORMATION
        if not h:
            return False
        try:
            tok = wintypes.HANDLE()
            if not _adv.OpenProcessToken(h, 0x0008, ctypes.byref(tok)):
                return False
            try:
                dato = ctypes.c_int(0)
                dev = wintypes.DWORD()
                if _adv.GetTokenInformation(tok, 20, ctypes.byref(dato),
                                            ctypes.sizeof(dato),
                                            ctypes.byref(dev)):
                    return bool(dato.value)
                return False
            finally:
                _k32.CloseHandle(tok)
        finally:
            _k32.CloseHandle(h)
    except Exception:
        return False


def _destino_protegido(hwnd) -> bool:
    """True si NO podemos leer el proceso de esa ventana.

    Cuando una ventana es de un proceso elevado y dicta no lo está, Windows no
    deja ni consultarlo: eso mismo (UIPI) es lo que impide que llegue el Ctrl+V
    sintetizado, así que el pegado "no hace nada" aunque el log diga que se
    envió.
    """
    pid = _win_pid(hwnd)
    if not pid or pid == os.getpid():
        return False
    try:
        _k32 = ctypes.WinDLL("kernel32", use_last_error=True)
        h = _k32.OpenProcess(0x1000, False, pid)
        if not h:
            return True
        _k32.CloseHandle(h)
        return False
    except Exception:
        return False


def _forzar_primer_plano(hwnd) -> bool:
    """Trae `hwnd` al primer plano aunque no lo tengamos nosotros.

    Sin esto, `SetForegroundWindow` se ignora (Windows solo se lo permite a
    quien ya tiene el primer plano) y el Ctrl+V acaba en la ventana equivocada:
    el log lo cuenta como «No se restauró el foco». El truco clásico es
    engancharse al hilo del primer plano, pedirlo, y soltarse; si aún así no,
    un Alt simulado desbloquea (el proceso que "tiene" Alt sí puede).
    """
    if not hwnd or not _user32.IsWindow(hwnd):
        return False
    try:
        if _user32.GetForegroundWindow() == hwnd:
            return True
    except Exception:
        return False
    try:
        _user32.AttachThreadInput.argtypes = [wintypes.DWORD, wintypes.DWORD,
                                              wintypes.BOOL]
        actual = int(_kernel32.GetCurrentThreadId())
        primero = int(_user32.GetWindowThreadProcessId(
            _user32.GetForegroundWindow(), None))
        _user32.AttachThreadInput(actual, primero, True)
        _user32.BringWindowToTop(hwnd)
        ok = bool(_user32.SetForegroundWindow(hwnd))
        _user32.AttachThreadInput(actual, primero, False)
    except Exception:
        ok = False
    try:
        if not ok or _user32.GetForegroundWindow() != hwnd:
            _key(0x12)                    # Alt: habilita al "último con Alt"
            _key(0x12, up=True)
            ok = bool(_user32.SetForegroundWindow(hwnd))
    except Exception:
        pass
    try:
        return _user32.GetForegroundWindow() == hwnd
    except Exception:
        return ok


def _es_ventana_propia(hwnd) -> bool:
    """True si la ventana es de dicta: la isla, la bandeja o el panel.

    Sin esto, dictar con el panel en primer plano pega el texto DENTRO del panel
    (parece que no pegó nada: la grabación sí funcionó). La ventana del panel es
    de Chrome, otro proceso, así que comparar con el PID propio no basta.
    """
    if not hwnd:
        return False
    pid = _win_pid(hwnd)
    if pid and pid == os.getpid():
        return True                      # la isla y la bandeja son nuestras
    host = _panel_host
    if host is not None:
        for p in (getattr(host, "window_pid", 0),
                  getattr(getattr(host, "proc", None), "pid", 0)):
            if p and pid == p:
                return True              # la ventana app del panel
    try:
        buf = ctypes.create_unicode_buffer(64)
        _user32.GetClassNameW(hwnd, buf, 64)
        clase = buf.value
        if clase == "dicta-layered-window":
            return True                  # la isla
        if clase != "Chrome_WidgetWin_1":
            return False
        # Red de seguridad: la ventana app del panel se llama «dicta» (Chrome le
        # pisa el título único) o «dicta-panel-<pid>-<id>» antes de eso.
        n = _user32.GetWindowTextLengthW(hwnd)
        titulo = ctypes.create_unicode_buffer(n + 1)
        _user32.GetWindowTextW(hwnd, titulo, n + 1)
        t = titulo.value.strip()
        return t == "dicta" or t.startswith("dicta-panel-")
    except Exception:
        return False


def _uia_insert_text(text: str, target_hwnd=0, target_title=""):
    env = os.environ.copy()
    env['DICTA_TARGET_HWND'] = str(int(target_hwnd or 0))
    env['DICTA_TARGET_TITLE'] = target_title or ''
    env['DICTA_TEXT'] = text
    flags = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
    result = subprocess.run(
        ['powershell.exe', '-NoLogo', '-NoProfile', '-STA',
         '-Command', _UIA_SET_VALUE_PS],
        capture_output=True, text=True, encoding='utf-8', errors='replace',
        env=env, creationflags=flags, timeout=6)
    success = result.returncode == 0 and 'DICTA_UIA_OK' in result.stdout
    detail = (result.stderr or '').strip()[-400:]
    return success, detail


def start_delivery(text: str, target_hwnd=0, target_title="") -> None:
    """Pega la transcripción SIN demora: el carril rápido es Ctrl+V (el campo
    sigue con el foco tras dictar) y el carril UIA (SetValue) queda como
    reparación para el caso raro en que el pegado directo no proceda."""
    t0 = time.monotonic()
    if clipboard_set(text):
        log("Transcripción guardada en el portapapeles.")
    else:
        log("No se pudo actualizar el portapapeles; probaré UI Automation.")

    try:
        foreground = _user32.GetForegroundWindow()
    except Exception:
        foreground = 0
    # Ni el panel ni la isla valen como destino: el texto se quedaría dentro de
    # dicta. Si el panel tenía el foco al empezar a dictar, manda lo que el
    # usuario esté mirando AHORA (lo normal: cambia de ventana mientras habla);
    # y si sigue siendo nuestro, se pega donde esté el foco, sin forzar nada.
    if _es_ventana_propia(target_hwnd) or _es_ventana_propia(foreground):
        # El usuario cambió de ventana mientras hablaba: manda la que mira ahora.
        if foreground and not _es_ventana_propia(foreground):
            target_hwnd, target_title = foreground, _fg_title()
        else:
            # Sigue en el panel: se pega donde estaba trabajando antes.
            ultimo = _ultimo_destino
            if ultimo and not _es_ventana_propia(ultimo) and _user32.IsWindow(ultimo):
                target_hwnd, target_title = ultimo, _ultimo_destino_titulo
            else:
                target_hwnd, target_title = 0, ""
        log("Destino corregido (el panel no cuenta): "
            + (target_title or "(queda en el portapapeles)"))
    if not target_hwnd:
        # Ni el panel ni la isla valen: pegar aquí metería el texto dentro de
        # dicta. Se deja en el portapapeles y se avisa, en vez de fingir.
        log("El panel tiene el foco y no hay ventana ajena conocida: el texto "
            "queda en el portapapeles (Ctrl+V donde quieras).")
        try:
            app.status, app.status_color = "⚠ Pulsa Ctrl+V", "#ff9f0a"
            app.dismiss_overlay = True
            app.state = "idle"
        except Exception:
            pass
        return
    if (not _esta_elevado()) and target_hwnd and _destino_protegido(target_hwnd):
        log("El destino es de un proceso protegido/elevado y dicta no está "
            "elevado: el Ctrl+V no va a llegar. Arranca dicta como "
            "administrador (run.bat).")
    same = (not target_hwnd) or (foreground == target_hwnd)
    if same and fallback_paste(target_hwnd, text):
        log(f"Pegado inmediato en {(time.monotonic() - t0) * 1000:.0f} ms.")
        app.delivery_results.put((True, "", target_hwnd))
        return
    if not same:
        try:
            if _forzar_primer_plano(target_hwnd):
                time.sleep(0.12)
                if fallback_paste(target_hwnd, text):
                    log(f"Pegado tras restaurar foco en "
                        f"{(time.monotonic() - t0) * 1000:.0f} ms.")
                    app.delivery_results.put((True, "", target_hwnd))
                    return
        except Exception:
            pass
        log("No se restauró el foco; uso el carril UIA de reparación.")

    def worker():
        success, detail = False, ''
        try:
            success, detail = _uia_insert_text(text, target_hwnd, target_title)
        except Exception as e:
            detail = str(e)
        app.delivery_results.put((success, detail, target_hwnd))

    threading.Thread(target=worker, daemon=True, name='dicta-uia-delivery').start()


# ---------------------------------------------- pegado segun la ventana
# Pegar NO es lo mismo en todos los sitios, y elegir MAL el carril era lo que
# hacia que el texto no llegara. Hay que mirar la ventana destino ANTES de
# enviar nada:
#   conhost clasico (ConsoleWindowClass) -> se escribe en el BUFFER DE ENTRADA
#       de la consola (WriteConsoleInputW): es lo que lee un programa en modo
#       crudo (una TUI) y NO necesita el primer plano. Respaldo: Ctrl+V (en
#       conhost tambien pega).
#   ventana Chromium/Electron (Chrome_WidgetWin_1 + _CHROMIUM_HOST_EXES) ->
#       texto TECLEADO como entrada real: dentro de Chromium el pegado depende
#       del control que tenga el foco (un xterm.js pega con Ctrl+Shift+V, un
#       <textarea> con Ctrl+V) y desde fuera no se puede adivinar.
#   ventana Tauri/WebView2 (clase "Tauri Window", p. ej. Terax) -> tambien
#       texto TECLEADO: su terminal (xterm.js sobre canvas) no recibe ni Ctrl+V
#       ni Ctrl+Shift+V (medido), pero el tecleado como entrada real si llega.
#   Windows Terminal / VS Code / JetBrains / mintty / WezTerm / ... ->
#       Ctrl+Shift+V (su combinacion de pegado).
#   aplicaciones normales -> Ctrl+V (como siempre).
# Respaldo universal si algo no encaja o el envio falla: Shift+Insert, y como
# ultimo recurso los mensajes POSTEADOS (WM_PASTE + Ctrl+V).

_VK_SHIFT, _VK_INSERT = 0x10, 0x2D
# Valores aceptados por la opcion configurable `paste_mode` (`auto` = detectar).
# `type` fuerza el TEXTO TECLEADO como entrada real (el mecanismo que ya se usa
# en ventanas Chromium/Electron y ahora tambien en las Tauri, como Terax).
PASTE_MODES = ("auto", "ctrl+v", "ctrl+shift+v", "shift+insert", "type")

# Clases de ventana que son emuladores de terminal (Ctrl+V no pega ahi).
# conhost va aparte: es el unico emulador donde Ctrl+V SI pega de fabrica.
_CONHOST_CLASSES = {"consolewindowclass"}
_TERMINAL_CLASSES = {
    "cascadia_hosting_window_class": "Windows Terminal",
    "mintty": "mintty", "mintty-class": "mintty",
    "alacritty": "Alacritty", "org.alacritty.alacritty": "Alacritty",
    "wezterm": "WezTerm", "org.wezfurlong.wezterm": "WezTerm",
    "sunawtframe": "JetBrains", "sunawtdialog": "JetBrains",
    "virtualconsoleclass": "ConEmu",
    "tabbywindow": "Tabby",
    "ghostty": "Ghostty",
    "rio": "Rio",
    "fluentterminal": "FluentTerminal",
    "windowstopmostwindow": "Terminus",
    "mobaxterm": "MobaXterm",
}

# Ejecutables que alojan una terminal (la clase sola no basta: VS Code y sus
# derivados comparten `Chrome_WidgetWin_1` con los navegadores, que SI quieren
# Ctrl+V). Se compara en minusculas contra el nombre del .exe del proceso.
_TERMINAL_EXES = {
    "windowsterminal.exe", "openconsole.exe", "wt.exe",
    "code.exe", "code - insiders.exe", "cursor.exe", "windsurf.exe",
    "idea64.exe", "pycharm64.exe", "webstorm64.exe", "goland64.exe",
    "clion64.exe", "rider64.exe", "datagrip64.exe", "phpstorm64.exe",
    "rubymine64.exe", "rustrover64.exe", "studio64.exe", "aqua64.exe",
    "mintty.exe", "alacritty.exe", "wezterm-gui.exe", "wezterm.exe",
    "conemu64.exe", "conemu.exe", "tabby.exe", "hyper.exe", "kitty.exe",
    "ghostty.exe", "rio.exe", "mobaxterm.exe", "putty.exe",
    "fluentterminal.app.exe", "terminus.exe", "warp.exe",
}

# Ventanas Chromium/Electron que ALOJAN la terminal o el campo del agente
# (Hermes y OpenCode son Electron con terminal integrada tipo xterm.js). La
# clase es la misma que la de un navegador, asi que se mira el .exe. Ahi la
# combinacion de pegado depende del control con el foco y no se adivina
# desde fuera: se TECLEA el texto como entrada real.
_CHROMIUM_HOST_EXES = {
    "hermes.exe", "opencode.exe", "cursor.exe", "windsurf.exe",
    "claude.exe", "codex.exe", "kiro.exe", "zed.exe",
}

# Ventanas Tauri 2 / WebView2 que alojan una terminal emulada en un canvas
# (Terax y en general cualquier "ADE" Tauri). Comparten la clase generica
# "Tauri Window" (no la de Chromium) y su pegado por combinacion NO funciona:
# medido en Terax, Ctrl+V y Ctrl+Shift+V no meten nada en el PTY. Ahi se
# TECLEA el texto como entrada real, igual que en las ventanas Chromium.
_TAURI_CLASSES = {"tauri window", "tao thread event target"}
_TAURI_HOST_EXES = {
    "terax.exe",
}


def _win_class(hwnd) -> str:
    """Nombre de clase de la ventana ('' si no se puede leer)."""
    try:
        buf = ctypes.create_unicode_buffer(256)
        if _user32.GetClassNameW(hwnd, buf, 256):
            return buf.value
    except Exception:
        pass
    return ""


def _win_exe(pid) -> str:
    """Nombre (minusculas) del .exe dueño del PID; '' si no se puede leer."""
    if not pid:
        return ""
    try:
        k = _kernel32
        k.OpenProcess.restype = ctypes.c_void_p
        k.OpenProcess.argtypes = (ctypes.c_uint, wintypes.BOOL, ctypes.c_uint)
        k.QueryFullProcessImageNameW.restype = wintypes.BOOL
        k.QueryFullProcessImageNameW.argtypes = (
            ctypes.c_void_p, ctypes.c_uint, ctypes.c_wchar_p,
            ctypes.POINTER(wintypes.DWORD))
        k.CloseHandle.argtypes = (ctypes.c_void_p,)
        h = k.OpenProcess(0x1000, False, int(pid))   # QUERY_LIMITED_INFORMATION
        if not h:
            return ""
        try:
            buf = ctypes.create_unicode_buffer(1024)
            size = wintypes.DWORD(len(buf))
            if k.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(size)):
                return os.path.basename(buf.value).lower()
        finally:
            k.CloseHandle(h)
    except Exception:
        return ""
    return ""


def _clasificar_destino(hwnd):
    """('console'|'terminal'|'normal'|'unknown', etiqueta, combo por defecto).

    Mira la ventana destino (clase + .exe del proceso) para decidir con que se
    pega. La etiqueta va al log: es lo que permite diagnosticar un caso raro.
    """
    clase = _win_class(hwnd)
    pid = _win_pid(hwnd)
    exe = _win_exe(pid)
    quien = f"{clase or '?'} / {exe or '?'}"
    lc = clase.lower()
    if lc in _CONHOST_CLASSES:
        # Consola clasica: el texto entra por el BUFFER DE ENTRADA de la
        # consola (WriteConsoleInputW), que es lo que lee un programa en
        # modo crudo (una TUI). Ctrl+V tambien pega aqui, asi que sirve de
        # respaldo si la consola no se deja adjuntar.
        return "console", quien, "console"
    nombre = _TERMINAL_CLASSES.get(lc)
    if nombre:
        return "terminal", f"{nombre} [{quien}]", "ctrl+shift+v"
    if exe in _TERMINAL_EXES:
        return "terminal", f"{exe} [{quien}]", "ctrl+shift+v"
    if lc == "chrome_widgetwin_1" and exe in _CHROMIUM_HOST_EXES:
        # Chromium/Electron (Hermes, OpenCode, Cursor...): la terminal vive
        # DENTRO de la ventana, comparte clase con los navegadores y pegar
        # depende del control con el foco. Se teclea como entrada real.
        return "chromium", f"{exe} [{quien}]", "type"
    if lc in _TAURI_CLASSES or exe in _TAURI_HOST_EXES:
        # Tauri/WebView2 (Terax): la terminal es un xterm.js sobre canvas dentro
        # del WebView2 y ni Ctrl+V ni Ctrl+Shift+V llegan al PTY (medido). Se
        # teclea el texto como entrada real, que si llega completo.
        return "tauri", f"{exe} [{quien}]", "type"
    if not clase and not exe:
        # No se pudo averiguar NADA de la ventana: pegado mas universal posible.
        return "unknown", quien, "shift+insert"
    return "normal", quien, "ctrl+v"


def _paste_mode(hwnd):
    """(mecanismo, etiqueta) de entrega, respetando el forzado por config.

    El mecanismo sale de `_clasificar_destino` (`console` -> buffer de la
    consola, `type` -> texto tecleado, o una combinacion de teclas).
    `paste_mode` de dicta_config.json manda si no es `auto` y entonces SE
    FUERZA la combinacion: es la valvula para una ventana que se resista.
    """
    tipo, quien, mecanismo = _clasificar_destino(hwnd)
    forzado = str(getattr(app, "paste_mode", "auto") or "auto").strip().lower()
    if forzado in ("ctrl+v", "ctrl+shift+v", "shift+insert", "type"):
        return forzado, f"forzado por config ({tipo}: {quien})"
    return mecanismo, f"{tipo}: {quien}"


def _send_combo(mode: str) -> None:
    """Envia una combinacion de pegado conocida con SendInput."""
    if mode == "ctrl+v":
        _key(_VK_CTRL)
        _key(_VK_V)
        _key(_VK_V, up=True)
        _key(_VK_CTRL, up=True)
    elif mode == "ctrl+shift+v":
        _key(_VK_CTRL)
        _key(_VK_SHIFT)
        _key(_VK_V)
        _key(_VK_V, up=True)
        _key(_VK_SHIFT, up=True)
        _key(_VK_CTRL, up=True)
    elif mode == "shift+insert":
        _key(_VK_SHIFT)
        _key(_VK_INSERT, extended=True)
        _key(_VK_INSERT, up=True, extended=True)
        _key(_VK_SHIFT, up=True)
    else:
        raise ValueError(f"modo de pegado desconocido: {mode}")


# ------------------------------------------ entrega segun el destino
# Pegar NO es la misma operacion en todos los sitios, y elegir MAL la
# combinacion era justo lo que hacia que no llegara nada:
#   * consola real (conhost) -> el texto se escribe en el BUFFER DE ENTRADA de
#       la consola (WriteConsoleInputW): es lo que recibe un programa que lee el
#       teclado en crudo (una TUI). No depende del primer plano ni de la
#       combinacion de pegado del emulador.
#   * ventana Chromium/Electron (Hermes, OpenCode...): la terminal o el campo
#       viven DENTRO de la ventana y comparten clase con los navegadores. Ahi
#       Ctrl+V y Ctrl+Shift+V dependen del control con el foco (un xterm.js pega
#       con Ctrl+Shift+V, un <textarea> con Ctrl+V) y desde fuera no se puede
#       adivinar: se TECLEA el texto como entrada real.
#   * emulador de terminal -> Ctrl+Shift+V (su combinacion de pegado).
#   * aplicacion normal     -> Ctrl+V, como siempre.
# Ultimo recurso si el envio falla: mensajes POSTEADOS (WM_PASTE / Ctrl+V).

_KEYEVENTF_UNICODE = 0x0004
_WM_PASTE = 0x0302
_console_lock = threading.Lock()
_console_api_ready = False
# ---------------------------------------------- pegado segun la ventana (2)
#   * ventana Tauri / WebView2 (clase "Tauri Window", p. ej. Terax) -> la
#       terminal vive DENTRO de un WebView2 (xterm.js sobre canvas) y su pegado
#       por combinacion NO es fiable: medido en Terax, ni Ctrl+V ni Ctrl+Shift+V
#       meten nada en el PTY. Se TECLEA el texto como entrada real, que es lo
#       que si llega (y respeta espacios).


class _KEY_EVENT_RECORD(ctypes.Structure):
    _fields_ = [("bKeyDown", wintypes.BOOL),
                ("wRepeatCount", wintypes.WORD),
                ("wVirtualKeyCode", wintypes.WORD),
                ("wVirtualScanCode", wintypes.WORD),
                ("uChar", ctypes.c_wchar),
                ("dwControlKeyState", wintypes.DWORD)]


class _INPUT_RECORD_EV(ctypes.Union):
    _fields_ = [("KeyEvent", _KEY_EVENT_RECORD),
                ("_pad", ctypes.c_byte * 16)]


class _INPUT_RECORD(ctypes.Structure):
    _fields_ = [("EventType", wintypes.WORD), ("Event", _INPUT_RECORD_EV)]


def _utf16_units(ch: str):
    """Unidades UTF-16 de un caracter (fuera del BMP van en pareja)."""
    c = ord(ch)
    if c <= 0xFFFF:
        return (c,)
    c -= 0x10000
    return (0xD800 + (c >> 10), 0xDC00 + (c & 0x3FF))


def _type_text(text: str) -> bool:
    """Teclea el texto con entrada REAL (SendInput, KEYEVENTF_UNICODE).

    Es el mecanismo para ventanas Chromium/Electron: lo ve cualquier control que
    tenga el foco, sea un terminal integrado (xterm.js) o un campo de texto, sin
    depender de que combinacion tenga atada al pegado.
    """
    if not text:
        return False
    for ch in text:
        for unit in _utf16_units(ch):
            _send_key_event(vk=0, scan=unit, flags=_KEYEVENTF_UNICODE)
            _send_key_event(vk=0, scan=unit, flags=_KEYEVENTF_UNICODE | 2)
    return True


def _console_api() -> None:
    global _console_api_ready
    if _console_api_ready:
        return
    k = _kernel32
    k.FreeConsole.restype = wintypes.BOOL
    k.AttachConsole.argtypes = (wintypes.DWORD,)
    k.AttachConsole.restype = wintypes.BOOL
    k.CreateFileW.argtypes = (ctypes.c_wchar_p, wintypes.DWORD, wintypes.DWORD,
                              ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD,
                              ctypes.c_void_p)
    k.CreateFileW.restype = ctypes.c_void_p
    k.WriteConsoleInputW.argtypes = (ctypes.c_void_p,
                                     ctypes.POINTER(_INPUT_RECORD),
                                     wintypes.DWORD,
                                     ctypes.POINTER(wintypes.DWORD))
    k.WriteConsoleInputW.restype = wintypes.BOOL
    k.CloseHandle.argtypes = (ctypes.c_void_p,)
    _console_api_ready = True


def _console_inject(hwnd, text) -> bool:
    """Escribe el texto en el BUFFER DE ENTRADA de la consola de `hwnd`.

    Solo vale para consolas REALES (conhost). En ConPTY (Windows Terminal) el
    AttachConsole da ACCESS_DENIED y se devuelve False para caer al teclado. La
    consola del proceso es unica, asi que va bajo un lock y se suelta enseguida.
    """
    pid = _win_pid(hwnd)
    if not pid or not text:
        return False
    _console_api()
    k = _kernel32
    GENERIC_READ, GENERIC_WRITE = 0x80000000, 0x40000000
    with _console_lock:
        try:
            k.FreeConsole()
            if not k.AttachConsole(int(pid)):
                return False
        except Exception:
            return False
        try:
            h = k.CreateFileW("CONIN$", GENERIC_READ | GENERIC_WRITE, 3,
                              None, 3, 0, None)
            if not h or h == ctypes.c_void_p(-1).value:
                return False
            ok = False
            try:
                recs = []
                for ch in text:
                    down = _INPUT_RECORD()
                    down.EventType = 1
                    down.Event.KeyEvent.bKeyDown = True
                    down.Event.KeyEvent.wRepeatCount = 1
                    down.Event.KeyEvent.uChar = ch
                    recs.append(down)
                    up = _INPUT_RECORD()
                    up.EventType = 1
                    up.Event.KeyEvent.bKeyDown = False
                    up.Event.KeyEvent.wRepeatCount = 1
                    up.Event.KeyEvent.uChar = ch
                    recs.append(up)
                arr = (_INPUT_RECORD * len(recs))(*recs)
                written = wintypes.DWORD(0)
                ok = bool(k.WriteConsoleInputW(ctypes.c_void_p(h), arr,
                                               len(recs),
                                               ctypes.byref(written)))
            finally:
                k.CloseHandle(ctypes.c_void_p(h))
            return ok
        except Exception:
            return False
        finally:
            try:
                k.FreeConsole()
            except Exception:
                pass


def _post_paste(hwnd) -> bool:
    """Ultimo recurso: mensajes POSTEADOS a la ventana (WM_PASTE y Ctrl+V).

    Chromium/Electron no los ven, pero hay controles clasicos que solo atienden
    este carril; se usa cuando el envio de teclas ha fallado del todo.
    """
    if not hwnd:
        return False
    try:
        _user32.PostMessageW(hwnd, _WM_PASTE, 0, 0)
        _user32.PostMessageW(hwnd, 0x0100, _VK_CTRL, 0)      # WM_KEYDOWN ctrl
        _user32.PostMessageW(hwnd, 0x0100, _VK_V, 0)
        _user32.PostMessageW(hwnd, 0x0101, _VK_V, 0)         # WM_KEYUP v
        _user32.PostMessageW(hwnd, 0x0101, _VK_CTRL, 0)
        return True
    except Exception:
        return False


def fallback_paste(target_hwnd=0, text="") -> bool:
    """Entrega `text` al destino con el mecanismo que le corresponde.

    El mecanismo lo elige `_paste_mode` por tipo de ventana (ver el bloque de
    arriba): buffer de la consola para conhost, texto tecleado como entrada real
    para ventanas Chromium/Electron, Ctrl+Shift+V para emuladores de terminal y
    Ctrl+V para aplicaciones normales. Si el carril falla, se cae al teclado (y
    al final a los mensajes posteados). Devuelve True si envio el texto.
    """
    try:
        if target_hwnd and _user32.GetForegroundWindow() != target_hwnd:
            _forzar_primer_plano(target_hwnd)
            time.sleep(0.12)
        hwnd = target_hwnd or _user32.GetForegroundWindow()
        modo, etiqueta = _paste_mode(hwnd)
        if modo == "type":
            if _type_text(text):
                log(f"Pegado (texto tecleado) enviado a [{etiqueta}].")
                return True
            log(f"El tecleado no salio en [{etiqueta}]; pruebo Ctrl+V.")
            modo = "ctrl+v"
        elif modo == "console":
            if _console_inject(hwnd, text):
                log(f"Pegado (buffer de consola) enviado a [{etiqueta}].")
                return True
            log(f"No se pudo escribir en el buffer de [{etiqueta}] "
                "(ConPTY o consola inaccesible); pruebo el teclado.")
            modo = "ctrl+v"
        try:
            _send_combo(modo)
        except Exception as e:
            # SendInput bloqueado para el combo elegido: no queda otra que el
            # respaldo universal.
            if modo == "shift+insert":
                raise
            log(f"Pegado {modo} no se pudo enviar ({e}); pruebo Shift+Insert.")
            _send_combo("shift+insert")
            modo = "shift+insert"
        log(f"Pegado ({modo}) enviado a [{etiqueta}].")
        return True
    except Exception as e:
        log(f"Pegado automatico bloqueado ({e}); pulsa el pegado a mano.")
        try:
            if target_hwnd and _post_paste(target_hwnd):
                log("Pegado posteado (WM_PASTE) enviado al destino.")
                return True
        except Exception:
            pass
        return False


def _fg_title() -> str:
    try:
        u = _user32
        hwnd = u.GetForegroundWindow()
        n = u.GetWindowTextLengthW(hwnd)
        buf = ctypes.create_unicode_buffer(n + 1)
        u.GetWindowTextW(hwnd, buf, n + 1)
        return buf.value.strip()
    except Exception:
        return ""


# ------------------------------------------------------------------ mic
class Mic:
    """InputStream continuo: mide nivel SIEMPRE y graba mientras dictas.
    Sin locks: atributos planos + GIL bastan para lo que hacemos."""

    def __init__(self):
        self.stream = None
        self.device = config_get("mic")
        self.sens = float(config_get("sens", 1.0))
        self._chunks = []
        self._buf_dur = 0.0

    def start(self, device=None) -> bool:
        self.stop()
        if device is not None:
            self.device = device
        self._chunks, self._buf_dur = [], 0.0
        try:
            self.stream = sd.InputStream(
                samplerate=SAMPLE_RATE, channels=1, dtype="float32",
                blocksize=CHUNK, device=self.device, callback=self._cb)
            self.stream.start()
        except Exception as e:
            app.mic_error = f"Micro no disponible: {e}"
            log(f"Micro: {e}")
            return False
        app.mic_error = ""
        return True

    def stop(self):
        if getattr(self, "stream", None):
            try:
                self.stream.stop()
                self.stream.close()
            except Exception:
                pass
            self.stream = None

    def _cb(self, indata, frames, t, status):
        mono = indata[:, 0]
        rms = float(np.sqrt(np.mean(mono ** 2)))
        if app.noise is None or rms < app.noise:
            app.noise = rms
        else:
            app.noise += (rms - app.noise) * 0.02
        thr = float(getattr(app, "voice_threshold", VOICE_THRESHOLD_DEFAULT)) / max(0.2, self.sens)
        app.thr = thr
        app.rms = rms
        usable = (len(mono) // 8) * 8
        if usable:
            bins = np.mean(np.abs(mono[:usable].reshape(8, -1)), axis=1)
            app.wave_data = (app.wave_data + tuple(float(v) for v in bins))[-160:]
        if rms > thr:
            app.last_voice = time.monotonic()
        if app.state == "recording":
            self._chunks.append(mono.copy())
            self._buf_dur += len(mono) / SAMPLE_RATE

    def take_audio(self):
        a = np.concatenate(self._chunks) if self._chunks else np.zeros(0, np.float32)
        dur = self._buf_dur
        self._chunks, self._buf_dur = [], 0.0
        return a, dur


# ---------------------------------------------- bandas de frecuencia (panel)
# 12 bandas log-espaciadas de grave a agudo para que el panel dibuje la onda
# REAL de cada pista (antes todo se veia como una raya plana). Coste
# despreciable: una FFT por bloque de audio (~0,25 s).
LEVEL_BANDS = 12
LEVEL_FMIN = 40.0
LEVEL_FMAX = 16000.0
LEVEL_FLOOR_DB = -80.0
LEVEL_CEIL_DB = -3.0
# Umbral de silencio (RMS lineal): por debajo de esto no hay audio real y el
# panel debe AVISAR en vez de pintar una onda.
SILENT_RMS = 8e-4

_LEVEL_EDGES = np.logspace(np.log10(LEVEL_FMIN), np.log10(LEVEL_FMAX),
                           LEVEL_BANDS + 1)


def _band_energies(x, sr=SAMPLE_RATE, n_bands=LEVEL_BANDS):
    """Energia por bandas de frecuencia (grave->agudo, 0..1) del bloque ``x``.

    Devuelve ``(valores, rms)``: ``valores`` es la lista de ``n_bands`` niveles
    (0..1, banda 0 = la mas grave) y ``rms`` el RMS total del bloque (para
    decidir si es silencio real). Ventana de Hann + FFT; sin dependencias. Si
    el bloque no llega a 64 muestras devuelve ceros.
    """
    x = np.asarray(x, dtype=np.float32).reshape(-1)
    n = len(x)
    if n < 64:
        return [0.0] * n_bands, 0.0
    w = np.hanning(n).astype(np.float64)
    X = np.fft.rfft(x.astype(np.float64) * w)
    # Densidad de potencia corregida por la ventana: sum(P) = RMS^2 del bloque.
    P = (np.abs(X) ** 2) / (float(n) * n) / float(np.mean(w * w))
    f = np.fft.rfftfreq(n, 1.0 / float(sr))
    out = []
    for i in range(n_bands):
        lo, hi = _LEVEL_EDGES[i], _LEVEL_EDGES[i + 1]
        m = (f >= lo) & (f < hi)
        e = float(P[m].sum()) if m.any() else 0.0
        db = 20.0 * np.log10(max(np.sqrt(e), 1e-9))
        lvl = (db - LEVEL_FLOOR_DB) / (LEVEL_CEIL_DB - LEVEL_FLOOR_DB)
        out.append(float(min(1.0, max(0.0, lvl))))
    return out, float(np.sqrt(P.sum()))


def _envelope_peaks(x, n_points=200):
    """Envolvente de ``x`` (pico por tramo) en ``n_points`` valores >= 0."""
    x = np.asarray(x, dtype=np.float32).reshape(-1)
    if len(x) == 0:
        return [0.0] * n_points
    idx = np.linspace(0, len(x), n_points + 1).astype(int)
    out = []
    for i in range(n_points):
        a, b = int(idx[i]), int(idx[i + 1])
        seg = x[a:b] if b > a else x[a:a + 1]
        out.append(float(np.max(np.abs(seg))) if len(seg) else 0.0)
    return out


class MicTest:
    """Prueba de MICROFONO de verdad: graba ~5 s publicando un nivel EN VIVO.

    El nivel (0..1) se mide por bloque con el mismo RMS que usa el dictado y
    ``peak`` guarda el maximo desde el inicio, asi que en ``/state`` se ve subir
    al hablar. Al terminar, el .wav se normaliza con ``_normalize_wav`` (la
    misma del .wav de reunion) para que se oiga y se sirve en
    ``/panel/mictest.wav``. Solo una prueba a la vez."""

    DURATION = 5.0
    WAV = os.path.join(SCRIPT_DIR, ".tmp", "mictest.wav")

    def __init__(self):
        self.active = False
        self.done = False
        self.level = 0.0           # nivel instantaneo 0..1
        self.peak = 0.0            # maximo nivel desde el inicio
        self.wav = None            # ruta del .wav ya normalizado (o None)
        self.error = ""
        self.duration = float(self.DURATION)   # segundos que dura la prueba
        self.elapsed = 0.0         # segundos transcurridos (para el panel)
        self.peaks = []            # envolvente 0..1 de lo capturado (~200 vals)
        self.silent = False        # True si lo capturado es silencio real
        self._stop = None
        self._thread = None

    def snapshot(self):
        return {"active": bool(self.active), "level": round(self.level, 4),
                "peak": round(self.peak, 4), "done": bool(self.done),
                "duration": round(self.duration, 2),
                "elapsed": round(self.elapsed, 2),
                "peaks": list(self.peaks),
                "silent": bool(self.silent),
                "wav": ("/panel/mictest.wav" if (self.done and self.wav)
                        else None),
                "error": self.error}

    def start(self):
        if self.active:
            return True
        self.active, self.done = True, False
        self.level = self.peak = 0.0
        self.error = ""
        self.elapsed = 0.0
        self.peaks = []
        self.silent = False
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True,
                                        name="dicta-mictest")
        self._thread.start()
        return True

    def cancel(self):
        if self._stop is not None:
            self._stop.set()

    def _run(self):
        dev = config_get("mic")
        chunks = []
        frames = 0
        sr = SAMPLE_RATE
        try:
            info = (sd.query_devices(dev, "input") if dev is not None
                    else sd.query_devices(kind="input"))
            sr = int(float(info.get("default_samplerate") or SAMPLE_RATE))
        except Exception:
            sr = SAMPLE_RATE
        block = max(256, int(sr * 0.05))          # ~50 ms por lectura
        limit = int(self.DURATION * sr)           # tope DURO de fotogramas
        try:
            with sd.InputStream(samplerate=sr, channels=1, dtype="float32",
                                device=dev, blocksize=block) as st:
                while frames < limit and not self._stop.is_set():
                    data, _ov = st.read(block)
                    mono = np.asarray(data, dtype=np.float32).reshape(-1)
                    if len(mono):
                        rms = float(np.sqrt(np.mean(mono ** 2)))
                        # La voz normal ronda RMS 0,02-0,06 (medido en este
                        # equipo); 0,08 = fondo de escala.
                        level = min(1.0, rms / 0.08)
                        self.level = level
                        if level > self.peak:
                            self.peak = level
                        chunks.append(mono.copy())
                        frames += len(mono)
                        self.elapsed = frames / float(sr) if sr else 0.0
        except Exception as e:
            self.error = f"Micro no disponible: {e}"
            log(f"Prueba de micro: {e}")
        else:
            if chunks:
                try:
                    audio = np.concatenate(chunks)
                    # Envolvente (0..1) de lo capturado para que el panel dibuje
                    # la onda REAL en vez de una linea recta. Se calcula sobre el
                    # audio CRUDO (antes de _normalize_wav) y se detecta el
                    # silencio real para poder avisar en lugar de pintar ruido.
                    env = _envelope_peaks(audio, 200)
                    raw_peak = (float(np.max(np.abs(audio))) if len(audio)
                                else 0.0)
                    raw_rms = (float(np.sqrt(np.mean(np.square(audio))))
                               if len(audio) else 0.0)
                    # "Silencio real" = RMS por debajo del umbral (misma regla
                    # que usa la reunion). Asi el panel puede AVISAR en vez de
                    # pintar una raya, y no se convierte ruido de fondo en onda.
                    self.silent = bool(raw_peak <= 0 or raw_rms < SILENT_RMS)
                    if self.silent or raw_peak <= 0:
                        self.peaks = [0.0] * 200
                    else:
                        self.peaks = [round(min(1.0, v / raw_peak), 4)
                                      for v in env]
                    os.makedirs(os.path.dirname(self.WAV), exist_ok=True)
                    sf.write(self.WAV, audio, sr, subtype="PCM_16")
                    _normalize_wav(self.WAV)
                    self.wav = self.WAV
                except Exception as e:
                    self.error = f"No se pudo guardar el audio: {e}"
                    log(f"Prueba de micro (guardar): {e}")
        finally:
            self.active = False
            self.done = True
            self.level = 0.0

    def wav_path(self):
        return self.WAV if (self.done and self.wav) else None


_mictest = MicTest()


# --------------------------------------------------- audios, reunión y docs
AUDIOS_DIR = os.path.join(SCRIPT_DIR, "audios")
DOCS_DIR = os.path.join(SCRIPT_DIR, "textos")
# Subidas del autor: carpeta PROPIA y persistente (no temporal). Cada audio
# que se sube a la cola se guarda aqui y su ficha (nombre visible, tamano,
# documento, estado) en uploads.json, para que la lista sobreviva a reinicios.
UPLOADS_DIR = os.path.join(SCRIPT_DIR, "uploads")
UPLOADS_FILE = os.path.join(UPLOADS_DIR, "uploads.json")

_STOPWORDS = set("""de la que el en y a los se del las un por con no una su para es al lo como
más pero sus le ya o este sí porque esta entre cuando muy sin sobre también me hasta hay
desde lo que si según todo del los y a vano el mismo por sobre si ya yo otro está eso
the of and to in a is that for on with as it are be this was from or an at by have had not
que no se si lo su por con para una es del al lo un más pero ya me si». Ella""".split())


def _resample(data: np.ndarray, sr: float, target=SAMPLE_RATE) -> np.ndarray:
    if data.ndim > 1:
        data = data.mean(axis=1)
    if abs(sr - target) > 1e-3:
        data = np.interp(
            np.linspace(0, len(data), int(len(data) * target / sr)),
            np.arange(len(data)), data)
    return data.astype(np.float32)


def _normalize_wav(path: str, target_dbfs: float = -3.0,
                   floor_peak: float = 0.01, max_gain: float = 20.0) -> dict:
    """Sube el .wav de la reunion a un nivel de escucha normal, en UNA pasada.

    La grabacion salia a pico 0,063 (-24 dBFS): con el volumen del sistema al
    100 % apenas se oia. Aqui se lee el fichero entero, se calcula UNA sola
    ganancia para que el PICO quede en `target_dbfs` (-3 dBFS) y se reescribe con
    soundfile. No se toca la transcripcion (se hace en vivo sobre la mezcla).

    Dos topes evitan amplificar el silencio/ruido:
    - `floor_peak`: si el pico ya es menor que esto, es una sala en silencio y se
      deja el fichero TAL CUAL (ganancia 1,0).
    - `max_gain`: tope absoluto de ganancia (una grabacion real de este equipo,
      pico 0,063, necesita ~11x; con 20x hay margen de sobra).

    Devuelve un dict con la medida (util para verificar): peak/rms de entrada y
    salida en valor lineal y en dBFS, y la ganancia aplicada.
    """
    import math
    data, sr = sf.read(path, dtype="float32", always_2d=True)
    if len(data) == 0:
        return {"applied": False, "gain": 1.0, "reason": "vacio"}
    peak_in = float(np.max(np.abs(data)))
    rms_in = float(np.sqrt(np.mean(np.square(data))))
    target = 10.0 ** (target_dbfs / 20.0)          # -3 dBFS -> 0,7079
    if peak_in < floor_peak:
        # Sala en silencio: no hay nada que subir; se deja como esta.
        return {"applied": False, "gain": 1.0, "reason": "silencio",
                "peak_in": peak_in, "rms_in": rms_in,
                "peak_out": peak_in, "rms_out": rms_in,
                "peak_in_db": 20.0 * math.log10(max(peak_in, 1e-12)),
                "peak_out_db": 20.0 * math.log10(max(peak_in, 1e-12)),
                "rms_out_db": 20.0 * math.log10(max(rms_in, 1e-12))}
    gain = min(target / peak_in, max_gain)
    out = np.clip(data * gain, -1.0, 1.0).astype(np.float32)
    sf.write(path, out, sr, subtype="PCM_16")
    peak_out = float(np.max(np.abs(out)))
    rms_out = float(np.sqrt(np.mean(np.square(out))))
    return {"applied": True, "gain": float(gain), "reason": "ok",
            "peak_in": peak_in, "rms_in": rms_in,
            "peak_out": peak_out, "rms_out": rms_out,
            "peak_in_db": 20.0 * math.log10(max(peak_in, 1e-12)),
            "peak_out_db": 20.0 * math.log10(max(peak_out, 1e-12)),
            "rms_out_db": 20.0 * math.log10(max(rms_out, 1e-12))}


def _ffmpeg_decode(path: str):
    """Fallback con ffmpeg para mp3/m4a si existe en el sistema."""
    if shutil.which("ffmpeg") is None:
        return None
    import tempfile
    out = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    out.close()
    try:
        r = subprocess.run(["ffmpeg", "-y", "-i", path, "-ac", "1",
                            "-ar", str(SAMPLE_RATE), out.name],
                           capture_output=True, timeout=600,
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        if r.returncode != 0:
            return None
        data, sr = sf.read(out.name, dtype="float32")
        return data, sr
    except Exception:
        return None
    finally:
        try:
            os.unlink(out.name)
        except Exception:
            pass


def _decode_audio(path: str):
    """(data 16k mono, sr) o una excepción con el motivo."""
    try:
        data, sr = sf.read(path, dtype="float32")
        return _resample(data, sr)
    except Exception:
        r = _ffmpeg_decode(path)
        if r is None:
            raise ValueError("formato no soportado (usa wav/flac/ogg/mp3)")
        return _resample(r[0], r[1])


_PEAKS_CACHE = {}
_SOURCES_CACHE = {"t": 0.0, "v": []}


def _peaks(path: str, n: int = 600) -> dict:
    """Envolvente de picos para dibujar la onda en la vista previa del panel.

    Se calcula el pico absoluto por bloque (no la media): una onda dibujada con
    medias se ve plana y no se parece a lo que suena. Cachea por (ruta, mtime,
    tamaño), así la vista previa no redecodea el audio en cada repintado.
    """
    key = None
    try:
        st = os.stat(path)
        key = (path, st.st_mtime_ns, st.st_size, n)
        hit = _PEAKS_CACHE.get(key)
        if hit is not None:
            return hit
    except OSError:
        pass
    audio = _decode_audio(path)
    dur = len(audio) / SAMPLE_RATE
    if len(audio) == 0:
        out = {"name": os.path.basename(path), "dur": 0.0, "peaks": []}
    else:
        step = max(1, len(audio) // n)
        m = (len(audio) // step) * step
        blk = audio[:m].reshape(-1, step)
        vals = np.abs(blk).max(axis=1)
        mx = float(vals.max()) or 1.0
        out = {"name": os.path.basename(path), "dur": round(dur, 2),
               "peaks": np.round(vals / mx, 3).tolist()}
    if key is not None:
        if len(_PEAKS_CACHE) > 40:      # memoria acotada: es solo una caché
            _PEAKS_CACHE.clear()
        _PEAKS_CACHE[key] = out
    return out


def _audio_ctype(name: str) -> str:
    """Tipo MIME REAL del audio por su extension.

    El navegador solo reproduce por URL lo que reconoce: servir todo como
    ``application/octet-stream`` obligaba al panel a bajarse el fichero entero a
    un blob (22 MB) antes de poder sonar.
    """
    return _AUDIO_CTYPE.get(os.path.splitext(name)[1].lstrip(".").lower(),
                            "application/octet-stream")


_AUDIO_CTYPE = {
    "wav": "audio/wav", "wave": "audio/wav", "mp3": "audio/mpeg",
    "m4a": "audio/mp4", "m4b": "audio/mp4", "aac": "audio/aac",
    "flac": "audio/flac", "ogg": "audio/ogg", "oga": "audio/ogg",
    "opus": "audio/ogg", "weba": "audio/webm", "webm": "audio/webm",
    "mp4": "video/mp4", "m4v": "video/mp4", "mov": "video/quicktime",
    "mkv": "video/x-matroska", "avi": "video/x-msvideo",
}


def _audio_sources(maxn: int = 6) -> list:
    """Fuentes de audio elegibles para grabar: todo el sistema o una app.

    Enumerar sesiones de audio es una llamada COM (MediaFoundation), así que la
    lista se cachea unos segundos: esto lo consulta el render de la isla.
    """
    now = time.monotonic()
    if _SOURCES_CACHE["v"] and now - _SOURCES_CACHE["t"] < 4.0:
        return _SOURCES_CACHE["v"]
    out = [{"key": "all", "label": "Todo el sistema", "playing": True}]
    try:
        import dicta_capture
        import re as _re
        for a in dicta_capture.list_audio_apps():
            if len(out) >= maxn:
                break
            pid = int(a.get("pid") or 0)
            name = str(a.get("name") or a.get("exe") or "").strip()
            # Windows devuelve entradas basura del tipo "AudioSrv.Dll,-202"
            # (nombre de recurso del servicio de audio): no son una app.
            if pid <= 0 or not name or _re.search(r"\.dll,-?\d+$", name, _re.I):
                continue
            name = os.path.basename(name) or name
            if any(x["label"] == name for x in out):
                continue
            out.append({"key": str(pid), "label": name,
                        "playing": bool(a.get("playing"))})
    except Exception as e:
        log(f"Fuentes de audio no disponibles aún: {e}")
    _SOURCES_CACHE.update(t=now, v=out)
    return out


def _source_label(selected: str = None) -> str:
    sel = str(config_get("meeting_source", "all") if selected is None
              else selected)
    if sel == "all":
        return "Todo el sistema"
    for s in _audio_sources():
        if s["key"] == sel:
            return s["label"]
    return "Todo el sistema"


def _merge_chunks(prev_text: str, cur_text: str) -> str:
    """Une trozos desechando la repetición del solape (0,5 s)."""
    pw, cw = prev_text.split(), cur_text.split()
    for n in range(min(6, len(pw), len(cw)), 0, -1):
        if [w.lower().strip('.,;:¡!¿?"\'') for w in pw[-n:]] == \
           [w.lower().strip('.,;:¡!¿?"\'') for w in cw[:n]]:
            cur_text = " ".join(cw[n:])
            return (prev_text + " " + cur_text).strip()
    return (prev_text + " " + cur_text).strip()


def _keywords(text: str, max_n=12):
    freq = {}
    for w in text.split():
        w = w.strip('.,;:¡!¿?()[]\'"').lower()
        if len(w) < 4 or w in _STOPWORDS or not w.isalpha():
            continue
        freq[w] = freq.get(w, 0) + 1
    return [w for w, _ in sorted(freq.items(), key=lambda kv: -kv[1])[:max_n]]


def _doc_name(label: str) -> str:
    """Nombre del .md a partir del audio de origen.

    Subes "Reunion miercoles.mp4" y el documento sale "Reunion miercoles.md":
    hereda el nombre del audio (sin extension) en vez de un identificador
    interno. Se limpian los caracteres que Windows no admite en un nombre de
    fichero y, si ya existe uno igual, se numera para no pisarlo.
    """
    base = os.path.splitext(os.path.basename(str(label or "audio")))[0]
    base = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", base).strip(" .") or "audio"
    base = base[:80]
    cand, n = base, 2
    while os.path.exists(os.path.join(DOCS_DIR, cand + ".md")):
        cand = f"{base} ({n})"
        n += 1
    return cand + ".md"


class TranscribeQueue:
    """Cola de audios. Un hilo procesa en orden: decodifica, trocea en
    ventanas de 30 s con solape y escribe un documento .md en textos/.
    La vista previa crece mientras transcurre (sirve también para revisar)."""

    def __init__(self):
        self.items = []               # {id,label,status,progress,doc,key,duration}
        self.lock = threading.Lock()
        self.thread = None
        self._stopping = False        # lo pone el cierre limpio
        self.on_change = None         # callback(item) al cambiar una ficha

    def add(self, src_path: str, label: str = None, key: str = None):
        os.makedirs(AUDIOS_DIR, exist_ok=True)
        uid = uuid.uuid4().hex[:10]
        ext = os.path.splitext(src_path)[1]
        dst = os.path.join(AUDIOS_DIR, f"{uid}{ext}")
        shutil.copyfile(src_path, dst)
        nombre = label or os.path.basename(src_path)
        doc = os.path.join(DOCS_DIR, _doc_name(nombre))
        with self.lock:
            self.items.append({"id": uid, "label": nombre,
                               "status": "en cola", "progress": 0.0,
                               "src": dst, "key": key, "duration": 0.0,
                               "doc": doc})
        self._notify(uid)
        self._wake()
        return uid

    def _wake(self):
        if self._stopping:
            return
        if self.thread is None or not self.thread.is_alive():
            self.thread = threading.Thread(target=self._run, daemon=True,
                                           name="dicta-audios")
            self.thread.start()

    def stop(self, timeout=6):
        """Cierre limpio: no acepta más trabajos y espera al hilo."""
        self._stopping = True
        th = self.thread
        if th is not None and th.is_alive():
            th.join(timeout=timeout)
        self.thread = None

    def snapshot(self):
        with self.lock:
            return [dict(i) for i in self.items]

    def _set(self, uid, **kw):
        with self.lock:
            for i in self.items:
                if i["id"] == uid:
                    i.update(kw)
                    break
        self._notify(uid)

    def _notify(self, uid):
        """Avisa al registro de subidas del cambio (si lo hay)."""
        cb = self.on_change
        if cb is None:
            return
        with self.lock:
            item = next((dict(i) for i in self.items if i["id"] == uid), None)
        if item is None:
            return
        try:
            cb(item)
        except Exception:
            pass

    def _run(self):
        while not self._stopping:
            with self.lock:
                job = next((i for i in self.items if i["status"] == "en cola"),
                           None)
            if job is None:
                return
            uid = job["id"]
            try:
                self._transcribe_job(uid)
            except Exception as e:
                self._set(uid, status=f"error — {e}")
            time.sleep(0.05)

    def _transcribe_job(self, uid: str):
        with self.lock:
            meta = next(i for i in self.items if i["id"] == uid)
            path = next(
                os.path.join(AUDIOS_DIR, f) for f in os.listdir(AUDIOS_DIR)
                if f.startswith(uid))
            doc = meta["doc"]
        self._set(uid, status="transcribiendo")
        audio = _decode_audio(path)             # lanza si no soporta
        dur = len(audio) / SAMPLE_RATE
        self._set(uid, duration=dur)
        os.makedirs(DOCS_DIR, exist_ok=True)
        full_text = ""
        chunk = int(26 * SAMPLE_RATE)
        hop = int(26 * SAMPLE_RATE) - int(0.5 * SAMPLE_RATE)
        n_win = max(1, -(-(len(audio) - chunk) // hop)) if len(audio) > chunk else 1
        n_done = 0
        t0 = time.monotonic()
        with open(doc, "w", encoding="utf-8") as fh:
            fh.write("# Audio\n\n")
            start = 0
            while start < len(audio) and not (start and start >= len(audio)):
                seg = np.ascontiguousarray(audio[start:start + chunk])
                text = transcribe(seg, ensure_model(MODELS.get(
                    app.model or "small", MODELS["small"])),
                    app.language, app.prompt) if dur > 0 else ""
                full_text = _merge_chunks(full_text, text) if full_text else text
                n_done += 1
                self._set(uid, progress=min(99.0, 100.0 * n_done / n_win))
                if start + chunk >= len(audio):
                    break
                start += hop
            mins, secs = divmod(int(dur), 60)
            fh.write(f"*Duración {mins}:{secs:02d} · transcribido en "
                     f"~{time.monotonic() - t0:.0f}s*\n\n## Transcripción\n\n"
                     f"{full_text or '(audio sin voz)'}\n\n## Temas\n\n"
                     + "\n".join(f"- {k}" for k in _keywords(full_text)))
        self._set(uid, status="listo", progress=100.0, doc=doc)


def _safe_upload_name(name: str) -> str:
    """Nombre VISIBLE de una subida, siempre sin rutas ni separadores.

    Se queda solo con el ultimo componente (por si el navegador manda una
    ruta), quita lo que Windows no admite en un nombre de fichero y evita
    ``.`` / ``..``. Nunca se usa para construir rutas de disco: el fichero en
    disco lleva un nombre interno generado por la app.
    """
    base = os.path.basename(str(name or "").replace("\\", "/"))
    base = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", base).strip(" .")
    return base or "audio"


def _audio_upload_ref(name: str) -> str:
    """Nombre del audio reproducible de una subida, si sigue en ``audios/``.

    Las subidas guardan su copia en ``audios/<uid>.<ext>`` (lo hace
    ``TranscribeQueue.add``). Aqui se acepta solo el NOMBRE (nunca una ruta) y
    se comprueba que el fichero exista todavia: si ya no esta, la referencia
    deja de publicarse para no ofrecer un reproductor muerto.
    """
    b = os.path.basename(str(name or "").replace("\\", "/")).strip()
    if not b or b in (".", "..") or ":" in b:
        return ""
    return b if os.path.isfile(os.path.join(AUDIOS_DIR, b)) else ""


def _audios_ref(name: str) -> str:
    """Ruta en ``audios/`` de un fichero dado por NOMBRE (nunca una ruta).

    La usa el BORRADO para limpiar la copia de trabajo emparejada. Acepta solo
    el nombre (sin separadores ni ``..``) y devuelve la ruta solo si el fichero
    existe; si no, "".
    """
    b = os.path.basename(str(name or "").replace("\\", "/")).strip()
    if (not b or b in (".", "..") or ".." in b or ":" in b
            or "/" in b or "\\" in b):
        return ""
    p = os.path.join(AUDIOS_DIR, b)
    return p if os.path.isfile(p) else ""


def _remove_file(path: str, tries: int = 5, delay: float = 0.4) -> bool:
    """Borra un fichero con reintentos cortos.

    En Windows no se puede borrar un fichero que otro hilo tiene abierto (la
    cola de transcripcion puede estar leyendo el audio justo al quitarlo). Unos
    pocos reintentos evitan que la copia de trabajo sobreviva por una carrera.
    Devuelve True si el fichero ya no esta al terminar.
    """
    if not path:
        return False
    for i in range(tries):
        try:
            if not os.path.isfile(path):
                return True
            os.remove(path)
            return True
        except Exception as e:
            if i == tries - 1:
                log(f"No se pudo borrar {path}: {e}")
                return False
            time.sleep(delay)
    return False


def audio_orphans():
    """Audios de ``audios/`` que ya no emparejan con ningun documento ni subida.

    El emparejamiento es por NOMBRE BASE (el mismo que usan ``doc.rename`` y
    ``/download``): un documento ``textos/X.md`` reclama ``audios/X.wav`` y cada
    subida reclama el audio que guarda en su ficha. Lo que quede suelto es un
    huerfano, PERO AQUI NO SE BORRA NADA: solo se lista (accion
    ``audio.orphans``) para que el autor decida. El borrado es una accion aparte
    (``audio.clean``) que exige confirmacion explicita.
    """
    refs = set()
    try:
        for f in os.listdir(DOCS_DIR):
            if f.lower().endswith(".md"):
                refs.add(os.path.splitext(f)[0] + ".wav")
    except Exception:
        pass
    try:
        with _uploads.lock:
            for i in _uploads.items:
                a = str(i.get("audio") or "")
                if a:
                    refs.add(a)
    except Exception:
        pass
    out = []
    try:
        for f in os.listdir(AUDIOS_DIR):
            if f in refs:
                continue
            p = os.path.join(AUDIOS_DIR, f)
            if os.path.isfile(p):
                out.append({"name": f, "size": os.path.getsize(p)})
    except Exception:
        pass
    out.sort(key=lambda x: x["name"])
    return out


class UploadStore:
    """Registro PERSISTENTE de los audios que el autor sube a la cola.

    Cada fichero se guarda en ``uploads/`` (carpeta propia, NO temporal) y su
    ficha -- nombre visible, tamano, documento, estado y la referencia de su
    audio reproducible (``audio``: el fichero de ``audios/``, que puede
    aparecer despues de la subida) -- en ``uploads.json``, de modo que la lista
    ``uploads`` de ``/state`` sobrevive a cerrar y abrir la app. Estados:
    pendiente / transcribiendo / listo / error.
    """

    STATES = ("pendiente", "transcribiendo", "listo", "error")

    def __init__(self):
        self.lock = threading.Lock()
        self.items = []          # {id,name,stored,size,doc,duration,state}
        self._load()

    # ---- persistencia
    def _load(self):
        try:
            with open(UPLOADS_FILE, "r", encoding="utf-8") as fh:
                data = json.load(fh)
        except Exception:
            data = []
        items = []
        for it in (data if isinstance(data, list) else []):
            try:
                stored = str(it.get("stored") or "")
                path = os.path.join(UPLOADS_DIR, stored)
                if not stored or not os.path.isfile(path):
                    continue         # ficha huerfana: el fichero ya no esta
                st = str(it.get("state") or "pendiente")
                if st not in self.STATES:
                    st = "pendiente"
                if st == "transcribiendo":
                    st = "pendiente"  # nada sigue corriendo tras un reinicio
                items.append({
                    "id": str(it.get("id") or uuid.uuid4().hex[:10]),
                    "name": str(it.get("name") or stored),
                    "stored": stored,
                    "size": int(it.get("size") or os.path.getsize(path)),
                    "doc": str(it.get("doc") or ""),
                    "duration": float(it.get("duration") or 0.0),
                    "audio": _audio_upload_ref(it.get("audio")),
                    "state": st})
            except Exception:
                continue
        self.items = items
        self._save()

    def _save(self):
        try:
            os.makedirs(UPLOADS_DIR, exist_ok=True)
            tmp = UPLOADS_FILE + ".tmp"
            with open(tmp, "w", encoding="utf-8") as fh:
                json.dump(self.items, fh, ensure_ascii=False, indent=2)
            os.replace(tmp, UPLOADS_FILE)
        except Exception as e:
            log(f"No se pudo guardar uploads.json: {e}")

    # ---- altas
    def _unique(self, name):
        with self.lock:
            taken = {i["name"] for i in self.items}
        base, ext = os.path.splitext(name)
        cand, n = name, 2
        while cand in taken:
            cand = f"{base} ({n}){ext}"
            n += 1
        return cand

    def add(self, name, data: bytes):
        """Guarda los bytes en uploads/ y devuelve la ficha (dict)."""
        visible = self._unique(_safe_upload_name(name))
        uid = uuid.uuid4().hex[:10]
        stored = f"{uid}{os.path.splitext(visible)[1] or '.bin'}"
        os.makedirs(UPLOADS_DIR, exist_ok=True)
        with open(os.path.join(UPLOADS_DIR, stored), "wb") as fh:
            fh.write(data)
        entry = {"id": uid, "name": visible, "stored": stored,
                 "size": len(data), "doc": "", "duration": 0.0,
                 "audio": "", "state": "pendiente"}
        with self.lock:
            self.items.append(entry)
        self._save()
        return dict(entry)

    def path_of(self, entry):
        return os.path.join(UPLOADS_DIR, entry["stored"])

    def pending(self):
        with self.lock:
            return [dict(i) for i in self.items
                    if i["state"] in ("pendiente", "transcribiendo")]

    # ---- cambios
    def set(self, uid, **kw):
        with self.lock:
            hit = next((i for i in self.items if i["id"] == uid), None)
            if hit is None:
                return
            hit.update(kw)
        self._save()

    def apply_queue_update(self, item):
        """Sincroniza una ficha con el estado de la cola de transcripcion."""
        key = item.get("key")
        if not key:
            return
        status = str(item.get("status") or "")
        if status == "listo":
            st = "listo"
        elif status == "transcribiendo":
            st = "transcribiendo"
        elif status == "en cola":
            st = "pendiente"
        elif status.startswith("error"):
            st = "error"
        else:
            st = "pendiente"
        doc = ""
        if item.get("doc"):
            doc = os.path.splitext(os.path.basename(item["doc"]))[0]
        # La cola es la UNICA fuente del nombre del audio de una subida
        # (audios/<uid>.<ext>): se guarda aqui para que la tarjeta conserve su
        # reproductor aunque la app se reinicie y la cola (de sesion) se pierda.
        audio = _audio_upload_ref(item.get("src"))
        extra = {"audio": audio} if audio else {}
        self.set(key, state=st, doc=doc,
                 duration=round(float(item.get("duration") or 0.0), 2), **extra)

    def audio_entries(self, skip_ids=()):
        """Entradas de cola SINTETICAS para las subidas ya resueltas.

        El panel indexa el audio por NOMBRE leyendo ``/state.queue[].src``; esa
        cola es de la SESION, asi que tras reiniciar se queda vacia y la tarjeta
        del documento (que sustituye a la ficha de la subida al transcribirse)
        se quedaba sin reproductor. Aqui se recrean esas referencias desde el
        manifiesto persistente: NO toca la cola real de transcripcion, solo
        alimenta lo que se publica en ``/state.queue``.
        """
        skip = set(skip_ids or ())
        out = []
        with self.lock:
            for i in self.items:
                if not i.get("audio") or i["id"] in skip:
                    continue
                out.append({"id": i["id"], "label": i["name"], "status": "listo",
                            "progress": 100.0, "src": i["audio"], "key": i["id"],
                            "duration": float(i["duration"] or 0.0),
                            "doc": (i["doc"] + ".md") if i["doc"] else ""})
        return out

    def rename_doc(self, old_base: str, new_base: str):
        """Sigue el rastro de un documento renombrado (empareja por NOMBRE BASE).

        Sin esto, renombrar la transcripción dejaba la subida apuntando al nombre
        viejo: dejaban de emparejarse —el emparejamiento es por nombre base— y el
        panel volvía a pintar DOS tarjetas del mismo audio: una con el nombre
        nuevo (el documento) y otra con el viejo (la subida).
        """
        old_base = str(old_base or "")
        new_base = str(new_base or "")
        if not old_base or not new_base or old_base == new_base:
            return
        with self.lock:
            hit = [i for i in self.items
                   if str(i.get("doc") or "") == old_base]
            for i in hit:
                i["doc"] = new_base
                name = str(i.get("name") or "")
                if name and os.path.splitext(name)[0] == old_base:
                    i["name"] = new_base + os.path.splitext(name)[1]
        if hit:
            self._save()

    def remove(self, name):
        """Quita la ficha por su NOMBRE visible y borra su fichero del disco.

        El nombre es solo una etiqueta: NUNCA se usa para construir la ruta
        (se borra la ruta guardada, generada por la app), asi que no admite
        rutas ni travesia de directorios (devuelve False).
        """
        nm = str(name or "").strip()
        if (not nm or nm != os.path.basename(nm)
                or nm in (".", "..") or ".." in nm
                or "/" in nm or "\\" in nm):
            return False
        with self.lock:
            hit = next((i for i in self.items if i["name"] == nm), None)
            if hit is None:
                return False
            self.items.remove(hit)
            path = os.path.join(UPLOADS_DIR, hit["stored"])
            audio = str(hit.get("audio") or "")
        self._save()
        # Se borran el fichero de uploads/ Y su copia de trabajo en audios/ (la
        # que dejo TranscribeQueue.add al encolar). Sin esto la copia quedaba
        # huerfana para siempre: no habia ninguna accion que la borrara.
        for p in (path, _audios_ref(audio)):
            _remove_file(p)
        return True

    def snapshot(self):
        with self.lock:
            return [{"name": i["name"], "size": int(i["size"]),
                     "doc": i["doc"],
                     "duration": int(round(i["duration"] or 0)),
                     # `src` = la MISMA forma que el panel ya lee en queue[].src:
                     # es el audio reproducible de la subida en audios/.
                     "src": i.get("audio") or "",
                     "state": i["state"], "id": i["id"]}
                    for i in self.items]


class MeetingTranscriber:
    """Captura el audio del SISTEMA (loopback WASAPI) Y del MICRÓFONO a la vez.

    - Dos productores (loopback + micrófono por defecto) alimentan un mezclador
      que escribe un **archivo .wav estéreo real** (canal L: sistema, R: micro)
      en `audios/` y transcribe en ventanas de 26 s con solape 0,5 s al .md.
    - Estados: activa | pausada (descarta audio y no transcribe, la sesión
      sigue viva) | guardada | cancelada (borra el .md y el .wav parciales).
    """

    SR = 48000                            # loopback WASAPI va a 48 kHz
    BLOCK = int(48000 * 0.25)             # lectura por productor (~0,25 s)

    def __init__(self):
        self.proc = None                  # hilo mezclador/transcriptor
        self._producers = []              # hilos de captura (loopback, micro)
        self._stop_evt = None
        self.doc = None                   # .md en textos/
        self.wav = None                   # .wav estéreo en audios/
        self.started = None
        self.status = ""
        self.paused = False
        self.mic_on = bool(config_get("meeting_mic", True))
        self.last = ""                    # última intervención transcrita
        # Niveles para la vista previa (0..1): por pista y el mix.
        self.level = self.level_sys = self.level_mic = 0.0
        self._lvl_sys = self._lvl_mic = 0.0
        # Bandas de frecuencia por pista (grave->agudo, 0..1) para el panel.
        self.levels_sys = [0.0] * LEVEL_BANDS
        self.levels_mic = [0.0] * LEVEL_BANDS
        self.sys_silent = True
        self.mic_silent = True
        self._lock = threading.Lock()
        self._sys_buf = []                # frames pendientes del sistema
        self._mic_buf = []                # frames pendientes del micro
        self._paused_total = 0.0
        self._cancelled = False
        self._mic_gain = 1.0              # ganancia automática del micro
        self._mix_gain = 1.0              # ganancia automática de la mezcla
        self.mic_device = None            # dispositivo del micro en uso
        self.level_note = None            # medida de la normalización del .wav

    @property
    def active(self):
        return self.proc is not None and self.proc.is_alive()

    def _running_seconds(self):
        if not self.started:
            return 0
        return max(0, time.monotonic() - self.started - self._paused_total)

    def snapshot(self):
        return {"active": self.active, "paused": self.paused,
                "mic_on": bool(self.mic_on),
                "doc": self.doc, "wav": self.wav,
                "status": self.status, "last": self.last,
                "level": round(self.level, 4),
                "level_sys": round(self.level_sys, 4),
                "level_mic": round(self.level_mic, 4),
                "mic": self.mic_device,
                "levels": self.levels(),
                "seconds": int(self._running_seconds())}

    def levels(self):
        """Bandas (grave->agudo) por pista para el panel + aviso de silencio.

        ``{"sys": [...12...], "mic": [...12...], "sys_silent": bool,
        "mic_silent": bool, "active": bool}``. Fuera de una reunion activa van
        a cero y ``*_silent`` a True (el panel no debe pintar onda).
        """
        if not self.active:
            return {"active": False, "sys": [0.0] * LEVEL_BANDS,
                    "mic": [0.0] * LEVEL_BANDS,
                    "sys_silent": True, "mic_silent": True}
        return {"active": True,
                "sys": [round(float(v), 4) for v in self.levels_sys],
                "mic": [round(float(v), 4) for v in self.levels_mic],
                "sys_silent": bool(self.sys_silent),
                "mic_silent": bool(self.mic_silent)}

    def start(self) -> bool:
        import soundcard as sc_dev
        # La enumeración de dispositivos usa MediaFoundation: necesita COM
        # inicializado EN EL HILO ACTUAL (este hilo es el del servidor HTTP).
        com_ok = False
        try:
            com_ok = (_ole32.CoInitializeEx(None, 0x2) == 0)  # RPC, este hilo
        except Exception:
            pass
        try:
            all_devs = sc_dev.all_microphones(include_loopback=True)
        except Exception as e:
            self.status = f"error detectando audio: {e}"
            return False
        finally:
            if com_ok:
                try:
                    _ole32.CoUninitialize()
                except Exception:
                    pass
        loops = [m for m in all_devs if m.isloopback]
        mics = [m for m in all_devs if not m.isloopback]
        # "Audio del sistema" es el del altavoz POR DEFECTO. La lista de
        # soundcard no viene ordenada por relevancia: loops[0] eran unos
        # auriculares desconectados y la reunion grababa silencio (medido: nivel
        # 0,00 mientras sonaba el altavoz por defecto).
        try:
            spk = sc_dev.default_speaker()
        except Exception:
            spk = None
        sys_loop = None
        if spk is not None:
            sys_loop = next((m for m in loops if m.name == spk.name), None)
        if sys_loop is None and loops:
            sys_loop = loops[0]
        # Fuente elegida: "all" = audio del sistema completo; si no, el PID de
        # una aplicación concreta (WASAPI process loopback).
        source = str(config_get("meeting_source", "all") or "all")
        src_pid = 0
        if source not in ("", "all"):
            try:
                src_pid = int(source)
            except ValueError:
                src_pid = 0
        if not loops and not mics and not src_pid:
            self.status = "sin audio disponible (no hay loopback ni micrófono)"
            return False
        os.makedirs(DOCS_DIR, exist_ok=True)
        os.makedirs(AUDIOS_DIR, exist_ok=True)
        stamp = time.strftime("%Y%m%d-%H%M%S")
        self.doc = os.path.join(DOCS_DIR, f"reunion-{stamp}.md")
        self.wav = os.path.join(AUDIOS_DIR, f"reunion-{stamp}.wav")
        self.started = time.monotonic()
        self._paused_total = 0.0
        self._cancelled = False
        self.paused = False
        self.last = ""
        self.status = "iniciando"
        self._stop_evt = threading.Event()
        self.level = self.level_sys = self.level_mic = 0.0
        self._lvl_sys = self._lvl_mic = 0.0
        self.levels_sys = [0.0] * LEVEL_BANDS
        self.levels_mic = [0.0] * LEVEL_BANDS
        self.sys_silent = self.mic_silent = True
        self._sys_buf, self._mic_buf = [], []
        self._producers = []
        t_ref = time.time()
        window_n = int(26 * self.SR)
        hop = window_n - int(0.5 * self.SR)

        def producer(device, is_loopback):
            # MediaFoundation (soundcard) necesita COM inicializado EN ESTE hilo.
            try:
                _ole32.CoInitializeEx(None, 0x0)
            except Exception:
                pass
            try:
                with device.recorder(samplerate=self.SR, channels=1) as rec:
                    while not self._stop_evt.is_set():
                        try:
                            data = rec.record(numframes=self.BLOCK)
                        except Exception:
                            break
                        if data is None or len(data) == 0:
                            continue
                        mono = np.asarray(data, dtype=np.float32).reshape(-1)
                        self._note_level(mono, is_loopback)
                        with self._lock:
                            (self._sys_buf if is_loopback
                             else self._mic_buf).append(mono)
            except Exception as e:
                # Un `{e}` vacío no dice nada: se registra también el tipo.
                log(f"Reunión captura "
                    f"({'sistema' if is_loopback else 'micro'}): "
                    f"{type(e).__name__}: {e!r}")
            finally:
                try:
                    _ole32.CoUninitialize()
                except Exception:
                    pass

        def sd_mic_producer():
            """Micro del sistema con PortAudio, no con soundcard.

            soundcard solo sabe leer dispositivos cuyo formato de mezcla sea
            IEEE float: con un micro PCM (el de este equipo) aborta con
            `assert wFormatTag == 0xFFFE` y la reunion se quedaba sin voz. Es el
            mismo motor que ya usa el dictado, asi que esta probado.

            Sigue el MISMO micro que el dictado (`config_get("mic")`): cuando
            el autor cambia de dispositivo, este MISMO hilo cierra el stream
            viejo y abre el nuevo, asi que nunca queda capturando del anterior.
            """
            stream = None
            sr = float(self.SR)
            block = max(1024, int(self.SR * 0.25))
            cur_dev = object()      # centinela: fuerza abrir en el 1er giro
            try:
                while not self._stop_evt.is_set():
                    try:
                        dev = config_get("mic")
                    except Exception:
                        dev = None
                    if dev != cur_dev:
                        if stream is not None:
                            try:
                                stream.stop()
                                stream.close()
                            except Exception:
                                pass
                            stream = None
                        cur_dev = dev
                        try:
                            info = (sd.query_devices(dev, "input")
                                    if dev is not None
                                    else sd.query_devices(kind="input"))
                            sr = float(info.get("default_samplerate") or self.SR)
                            block = max(1024, int(sr * 0.25))
                            stream = sd.InputStream(
                                samplerate=sr, channels=1, dtype="float32",
                                device=dev, blocksize=block)
                            stream.start()
                            self.mic_device = dev
                            log(f"Reunión: micro del dictado -> indice {dev} "
                                f"({info.get('name', '?')})")
                        except Exception as e:
                            stream = None
                            log(f"Reunión captura (micro): {type(e).__name__}: "
                                f"{e!r}; reintento en 0,5 s")
                            self._stop_evt.wait(0.5)
                            continue
                    if stream is None:
                        self._stop_evt.wait(0.3)
                        continue
                    try:
                        data, _ov = stream.read(block)
                    except Exception:
                        try:
                            stream.stop()
                            stream.close()
                        except Exception:
                            pass
                        stream = None
                        self._stop_evt.wait(0.3)
                        continue
                    mono = _resample(np.asarray(data)[:, 0], sr, self.SR)
                    self._note_level(mono, False)
                    with self._lock:
                        self._mic_buf.append(mono)
            except Exception as e:
                log(f"Reunión captura (micro): {type(e).__name__}: {e!r}")
            finally:
                if stream is not None:
                    try:
                        stream.stop()
                        stream.close()
                    except Exception:
                        pass

        def app_producer(pid):
            """Captura SOLO el audio de esa aplicación (process loopback).

            Es la pieza "graba esta ventana y no el resto": si falla, se avisa
            en el estado y la reunión sigue con el micrófono, nunca se cae.
            """
            try:
                import dicta_capture
            except Exception as e:
                log(f"Captura por aplicación no disponible: {e}")
                self.status = "sin captura por aplicación (módulo ausente)"
                return
            cap = None
            try:
                try:
                    _ole32.CoInitializeEx(None, 0x2)      # MTA, hilo propio
                except Exception:
                    pass
                cap = dicta_capture.ProcessLoopbackCapture(pid,
                                                           samplerate=self.SR)
                if not cap.start():
                    log(f"Process loopback no arrancó: {cap.error}")
                    self.status = f"sin audio de esa aplicación: {cap.error}"
                    return
                log(f"Capturando solo el audio del PID {pid}")
                self.status = "grabando (aplicación)"
                # Los primeros ~0,25 s de un process loopback no son fieles
                # (medido: correlación 0,935 en esa ventana, 1,0000 después):
                # se descartan para no meter ese transitorio en la reunión.
                skip = int(0.25 * self.SR)
                while not self._stop_evt.is_set():
                    data = cap.read(0.25)
                    if data is None:
                        continue
                    mono = np.asarray(data, dtype=np.float32)
                    if mono.ndim > 1:
                        mono = mono.mean(axis=1)
                    mono = mono.reshape(-1)
                    if skip > 0:
                        if len(mono) <= skip:
                            skip -= len(mono)
                            continue
                        mono = mono[skip:]
                        skip = 0
                    self._note_level(mono, True)
                    with self._lock:
                        self._sys_buf.append(mono)
            except Exception as e:
                log(f"Captura por aplicación: {e}")
                self.status = f"error captura app: {e}"
            finally:
                if cap is not None:
                    try:
                        cap.stop()
                    except Exception:
                        pass

        def run():
            # MediaFoundation necesita COM inicializado EN ESTE hilo.
            try:
                _ole32.CoInitializeEx(None, 0x0)
            except Exception:
                pass
            finished = False
            try:
                # Productores: la aplicación elegida O el sistema completo, y
                # el micrófono (si existe).
                if src_pid:
                    t = threading.Thread(target=app_producer, args=(src_pid,),
                                         daemon=True,
                                         name="dicta-meeting-app")
                    t.start()
                    self._producers.append(t)
                elif sys_loop is not None:
                    t = threading.Thread(target=producer,
                                         args=(sys_loop, True), daemon=True,
                                         name="dicta-meeting-sys")
                    t.start()
                    self._producers.append(t)
                # El micro va aparte, por PortAudio: soundcard no puede leerlo.
                # Se puede desactivar (Ajustes) si solo quieres el audio del
                # sistema, p. ej. una conferencia en la que no hablas.
                self.mic_on = bool(config_get("meeting_mic", True))
                if self.mic_on:
                    t = threading.Thread(target=sd_mic_producer, daemon=True,
                                         name="dicta-meeting-mic")
                    t.start()
                    self._producers.append(t)
                os.makedirs(DOCS_DIR, exist_ok=True)
                fh = open(self.doc, "w", encoding="utf-8")
                fh.write("# Reunión\n\n")
                sfh = sf.SoundFile(self.wav, "w", samplerate=self.SR,
                                   channels=2, subtype="PCM_16")
                buf = np.zeros(0, np.float32)      # mezcla mono para transcribir
                offset_ref = 0.0
                paused_mark = None
                try:
                    acc_sys = np.zeros(0, np.float32)
                    acc_mic = np.zeros(0, np.float32)
                    avisado_muda = False
                    # --- Parrafos naturales -------------------------------------
                    # Cada ventana de 26 s se transcribia con SU marca de tiempo,
                    # cortando el texto en lineas de 26 s aunque la frase siguiera
                    # (se perdia el contexto del parrafo). Ahora los fragmentos
                    # consecutivos se AGRUPAN en un parrafo (se unen con espacios,
                    # sin resumir) con UNA sola marca de tiempo al principio. El
                    # parrafo se cierra en un corte natural: un silencio al final
                    # de la ventana, o al llegar a PARA_MAX segundos.
                    para = []            # fragmentos del parrafo en curso
                    para_ts = None       # marca de tiempo (una) del parrafo
                    para_dur = 0.0       # segundos acumulados en el parrafo
                    rms_ref = 0.0        # nivel de voz de referencia (silencio)
                    PARA_MAX = 60.0      # cierre forzoso para no hacer un parrafo
                    #                      eterno si nunca hay silencio.

                    def flush_para():
                        nonlocal para, para_ts, para_dur
                        if para:
                            fh.write(f"**[{para_ts}]** "
                                     + " ".join(para) + "\n\n")
                            fh.flush()
                        para = []
                        para_ts = None
                        para_dur = 0.0

                    while not self._stop_evt.is_set():
                        if self.paused:
                            # Descarta lo capturado durante la pausa y sigue.
                            with self._lock:
                                self._sys_buf.clear()
                                self._mic_buf.clear()
                            acc_sys = np.zeros(0, np.float32)
                            acc_mic = np.zeros(0, np.float32)
                            if paused_mark is None:
                                paused_mark = time.monotonic()
                            self.status = "en pausa"
                            self._stop_evt.wait(0.1)
                            continue
                        if paused_mark is not None:
                            self._paused_total += time.monotonic() - paused_mark
                            paused_mark = None
                        with self._lock:
                            sys_frames, self._sys_buf = self._sys_buf, []
                            mic_frames, self._mic_buf = self._mic_buf, []
                        if sys_frames or mic_frames:
                            sys_all = (np.concatenate(sys_frames)
                                       if sys_frames else np.zeros(0, np.float32))
                            mic_all = (np.concatenate(mic_frames)
                                       if mic_frames else np.zeros(0, np.float32))
                            n = max(len(sys_all), len(mic_all))
                            if n:
                                # Acumular lo que llega de cada pista y consumir
                                # solo lo que existe en LAS DOS. Rellenar con
                                # silencio la que va corta metía huecos de 0,25 s
                                # en la voz (los tirones que se oían).
                                acc_sys = np.concatenate([acc_sys, sys_all])
                                acc_mic = np.concatenate([acc_mic, mic_all])
                                if max(len(acc_sys), len(acc_mic)) > 3 * self.SR:
                                    # Una pista muda >3 s (productor muerto): se
                                    # rellena para no parar la grabación.
                                    faltan = abs(len(acc_sys) - len(acc_mic))
                                    cero = np.zeros(faltan, np.float32)
                                    if len(acc_sys) < len(acc_mic):
                                        acc_sys = np.concatenate([acc_sys, cero])
                                    else:
                                        acc_mic = np.concatenate([acc_mic, cero])
                                    if not avisado_muda:
                                        avisado_muda = True
                                        log("Reunión: una pista lleva >3 s muda; "
                                            "se rellena para no parar la grabación.")
                                k = min(len(acc_sys), len(acc_mic))
                                if k:
                                    sys_s = acc_sys[:k]
                                    mic_s = acc_mic[:k]
                                    acc_sys = acc_sys[k:]
                                    acc_mic = acc_mic[k:]
                                    # RMS CRUDO de cada pista (antes de ganancia)
                                    # para decidir si de verdad hay silencio.
                                    r_raw_sys = float(np.sqrt(np.mean(
                                        np.square(sys_s)))) if k else 0.0
                                    r_raw_mic = float(np.sqrt(np.mean(
                                        np.square(mic_s)))) if k else 0.0
                                    # El micro de este equipo entra bajo (RMS 0,001
                                    # frente a 0,82 del sistema), así que hay que
                                    # subirlo; pero el RMS se mide sobre las muestras
                                    # REALES (`mic_all`, sin el relleno de silencio del
                                    # `_pad`): midiéndolo sobre el relleno salía
                                    # hundido, la ganancia se disparaba y al entrar voz
                                    # saturaba con recorte duro → sonaba entrecortado.
                                    # Objetivo moderado, tope bajo y adaptación lenta.
                                    rms = (float(np.sqrt(np.mean(np.square(mic_all))))
                                           if len(mic_all) else 0.0)
                                    if rms > 1e-4:
                                        # Adaptacion lenta hacia el nivel de voz. Sin
                                        # umbral que adivine: si hay algo (no silencio
                                        # digital), la ganancia se mueve; el limitador
                                        # suave de abajo impide que sature nunca.
                                        objetivo = min(0.12 / max(rms, 1e-9), 12.0)
                                        self._mic_gain += (objetivo
                                                           - self._mic_gain) * 0.15
                                    else:
                                        self._mic_gain = max(1.0,
                                                             self._mic_gain * 0.95)
                                    # Limitador SUAVE (tanh) en vez de recorte duro: el
                                    # recorte se oye como entrecortado.
                                    mic_s = np.tanh(mic_s * self._mic_gain)
                                    # Ganancia de MEZCLA: la grabación salía a
                                    # -24 dBFS (inaudible con el volumen al 100 %),
                                    # así que se sube de forma adaptativa y LENTA
                                    # (0,05: no bombea), con tope y limitador suave.
                                    suma = sys_s + mic_s
                                    # Bandas de frecuencia (grave->agudo) del
                                    # ultimo bloque, para que el panel dibuje la
                                    # onda REAL de cada pista en vez de una raya.
                                    # El micro va MUY bajo en crudo (RMS ~0,001),
                                    # asi que sus bandas se miden sobre la señal
                                    # YA GANADA (la que se oye); el silencio se
                                    # decide sobre el RMS CRUDO.
                                    try:
                                        _seg = int(0.5 * self.SR)
                                        self.levels_sys, _ = _band_energies(
                                            sys_s[-_seg:])
                                        self.levels_mic, _ = _band_energies(
                                            mic_s[-_seg:])
                                        self.sys_silent = r_raw_sys < SILENT_RMS
                                        self.mic_silent = r_raw_mic < SILENT_RMS
                                    except Exception:
                                        pass
                                    rms_mix = float(np.sqrt(np.mean(np.square(suma))))
                                    if rms_mix > 1e-4:
                                        obj_mix = min(0.08 / rms_mix, 6.0)
                                        self._mix_gain += (obj_mix
                                                           - self._mix_gain) * 0.05
                                    # El .wav guarda la MEZCLA en los dos canales:
                                    # con L=sistema y R=micro, escucharlo suena por
                                    # un solo oído y la voz propia no aparece.
                                    mezcla = np.tanh(suma * self._mix_gain)
                                    sfh.write(np.stack([mezcla, mezcla], axis=1))
                                    buf = np.concatenate([buf, mezcla])
                            self.status = f"grabando · {len(buf) / self.SR:.0f} s"
                        # Ventanas de 26 s con solape; transcribe en vivo y agrupa
                        # el texto en PARRAFOS con una sola marca de tiempo.
                        while len(buf) >= window_n:
                            mono = _resample(buf[:window_n], self.SR)
                            t_stamp = t_ref + offset_ref
                            lt = time.localtime(t_stamp)
                            ts = (f"{lt.tm_hour:02d}:{lt.tm_min:02d}:"
                                  f"{lt.tm_sec:02d}")
                            try:
                                text = transcribe(mono, ensure_model(MODELS.get(
                                    app.model or "small", MODELS["small"])),
                                    app.language, app.prompt)
                            except Exception as e:
                                log(f"Reunión transcribe: {e}")
                                text = ""
                            # Silencio al FINAL de la ventana = corte natural de
                            # frase. Se mide contra el nivel de voz de referencia
                            # (este micro entra muy bajo: un umbral fijo no vale).
                            r = (float(np.sqrt(np.mean(np.square(mono))))
                                 if len(mono) else 0.0)
                            rms_ref = max(rms_ref * 0.999, r)
                            cola = mono[-int(2 * SAMPLE_RATE):] if len(mono) else mono
                            r_cola = (float(np.sqrt(np.mean(np.square(cola))))
                                      if len(cola) else 0.0)
                            corte = (rms_ref > 1e-3 and r_cola < 0.15 * rms_ref)
                            if text:
                                if not para:
                                    para_ts = ts
                                para.append(text.strip())
                                self.last = (f"[{lt.tm_hour:02d}:{lt.tm_min:02d}]"
                                             f" {text}")
                            if para:
                                para_dur += window_n / self.SR
                                if corte or para_dur >= PARA_MAX:
                                    flush_para()
                            offset_ref += window_n / self.SR
                            buf = buf[hop:]
                        self._stop_evt.wait(0.05)
                    # Cierre: transcribe el remanente y finaliza el .wav / .md.
                    if len(buf) >= int(0.5 * self.SR):
                        mono = _resample(buf, self.SR)
                        try:
                            text = transcribe(mono, ensure_model(MODELS.get(
                                app.model or "small", MODELS["small"])),
                                app.language, app.prompt)
                        except Exception:
                            text = ""
                        if text:
                            t_stamp = t_ref + offset_ref
                            lt = time.localtime(t_stamp)
                            if not para:
                                para_ts = (f"{lt.tm_hour:02d}:{lt.tm_min:02d}:"
                                           f"{lt.tm_sec:02d}")
                            para.append(text.strip())
                            self.last = (f"[{lt.tm_hour:02d}:{lt.tm_min:02d}]"
                                         f" {text}")
                    # Cierra el ultimo parrafo antes de cerrar el fichero.
                    flush_para()
                finally:
                    try:
                        sfh.close()
                    except Exception:
                        pass
                    try:
                        fh.close()
                    except Exception:
                        pass
                # Normaliza el .wav a nivel de escucha (una pasada, pico ~-3
                # dBFS). La transcripcion es en vivo, no la afecta.
                if not self._cancelled and self.wav and os.path.isfile(self.wav):
                    try:
                        norm = _normalize_wav(self.wav)
                        log(f"Reunión nivel: pico {norm.get('peak_in_db', 0):.1f}"
                            f" -> {norm.get('peak_out_db', 0):.1f} dBFS "
                            f"(x{norm.get('gain', 1):.1f}, {norm.get('reason')})")
                        self.level_note = norm
                    except Exception as e:
                        log(f"Reunión normalizar: {type(e).__name__}: {e!r}")
                dur = self._running_seconds()
                mins, secs = divmod(int(dur), 60)
                temas = _keywords(" ".join(
                    line[line.find("** ") + 3:] if "** " in line else line
                    for line in open(self.doc, encoding="utf-8")))
                fh2 = open(self.doc, "a", encoding="utf-8")
                fh2.write(f"\n*Duración {mins}:{secs:02d} · grabación: "
                          f"{os.path.basename(self.wav)}*\n\n## Temas\n\n"
                          + "\n".join(f"- {k}" for k in temas))
                fh2.close()
                finished = True
            except Exception as e:
                self.status = f"error: {e}"
                log(f"Reunión: {e}")
            finally:
                try:
                    _ole32.CoUninitialize()
                except Exception:
                    pass
                self._finish(self._cancelled)
                for t in self._producers:
                    t.join(timeout=2)
                self._producers = []

        self.proc = threading.Thread(target=run, daemon=True, name="dicta-meeting")
        self.proc.start()
        return True

    def pause(self):
        self.paused = True
        self.status = "en pausa"

    def resume(self):
        self.paused = False
        self.status = "grabando"

    def _note_level(self, mono, is_loopback):
        """Nivel de captura para la vista previa en vivo.

        Ataque rapido y caida lenta (como el oido): con caida rapida la onda
        parpadea. Se guarda por pista y el mix es la mayor de las dos.
        """
        try:
            v = float(np.sqrt(np.mean(np.square(mono)))) if len(mono) else 0.0
        except Exception:
            return
        v = min(1.0, v / 0.15)            # 0,15 de RMS = reunion ya muy alta
        prev = self._lvl_sys if is_loopback else self._lvl_mic
        cur = v if v > prev else prev * 0.82
        if is_loopback:
            self._lvl_sys = cur
            self.level_sys = cur
        else:
            self._lvl_mic = cur
            self.level_mic = cur
        self.level = max(self._lvl_sys, self._lvl_mic)

    def dismiss(self):
        """Olvida el resumen de la ultima reunion (cierra la tarjeta del panel).

        El .md y el .wav NO se borran: siguen en textos/ y audios/ y aparecen en
        la lista de Documentos. Solo se limpia el estado que pinta el panel, que
        es lo que hacia que la tarjeta reapareciera al pulsar Cerrar.
        """
        if self.active:
            return False
        self.status = ""
        self.doc = None
        self.wav = None
        self.last = ""
        self.started = None
        return True

    def request_stop(self, cancel: bool = False):
        """Marca detención; cabe llamarlo desde cualquier hilo."""
        self._cancelled = cancel
        if self._stop_evt:
            self._stop_evt.set()
        try:
            if cancel:
                self.paused = False
        except Exception:
            pass

    def _finish(self, cancelled: bool):
        self.proc = None
        self.paused = False
        self.level = self.level_sys = self.level_mic = 0.0
        self.levels_sys = [0.0] * LEVEL_BANDS
        self.levels_mic = [0.0] * LEVEL_BANDS
        self.sys_silent = self.mic_silent = True
        if cancelled:
            for p in (self.doc, self.wav):
                try:
                    if p and os.path.isfile(p):
                        os.remove(p)
                except Exception:
                    pass
            self.doc = self.wav = None
            self.status = "cancelada"
        else:
            if not self.status or self.status.startswith("error"):
                pass
            else:
                self.status = "guardada"

    def stop(self):
        """Detiene y guarda (o cancela según el flag interno)."""
        self.request_stop(cancel=False)
        if self.proc:
            self.proc.join(timeout=20)
        self._stop_evt = None

    def cancel(self):
        """Detiene y descarta la reunión en curso (borra .md y .wav)."""
        self.request_stop(cancel=True)
        if self.proc:
            self.proc.join(timeout=20)
        self._stop_evt = None


# ------------------------------------------- exportar (Guardar como...)
# El panel NO puede bajar ficheros por navegacion. La ventana del panel es un
# WebView2 incrustado (pywebview) y su anfitrion NO gestiona DownloadStarting:
# el clic del usuario arranca la descarga, el motor recibe los bytes enteros y
# la CANCELA en silencio (medido por CDP en la ventana real: Page.downloadWillBegin
# -> Page.downloadProgress (receivedBytes = totalBytes) -> state "canceled", sin
# dialogo, sin fichero y sin ningun error). En Chrome eso mismo guarda el
# fichero y por eso la verificacion anterior «pasaba». Asi que «descargar» en el
# panel es una ACCION DEL BACKEND: dialogo NATIVO de Windows (Guardar como...)
# y el fichero lo escribe la app en la ruta que el usuario elija.
_OFN_EXPLORER = 0x00080000
_OFN_OVERWRITEPROMPT = 0x00000002
_OFN_PATHMUSTEXIST = 0x00000800
_OFN_NOCHANGEDIR = 0x00000008
_OFN_HIDEREADONLY = 0x00000004
_OFN_DONTADDTORECENT = 0x02000000


class _OPENFILENAMEW(ctypes.Structure):
    """OPENFILENAMEW de comdlg32 (el dialogo del sistema)."""
    _fields_ = [
        ("lStructSize", wintypes.DWORD),
        ("hwndOwner", wintypes.HWND),
        ("hInstance", wintypes.HINSTANCE),
        ("lpstrFilter", wintypes.LPCWSTR),
        ("lpstrCustomFilter", wintypes.LPWSTR),
        ("nMaxCustFilter", wintypes.DWORD),
        ("nFilterIndex", wintypes.DWORD),
        ("lpstrFile", wintypes.LPWSTR),
        ("nMaxFile", wintypes.DWORD),
        ("lpstrFileTitle", wintypes.LPWSTR),
        ("nMaxFileTitle", wintypes.DWORD),
        ("lpstrInitialDir", wintypes.LPCWSTR),
        ("lpstrTitle", wintypes.LPCWSTR),
        ("Flags", wintypes.DWORD),
        ("nFileOffset", wintypes.WORD),
        ("nFileExtension", wintypes.WORD),
        ("lpstrDefExt", wintypes.LPCWSTR),
        ("lCustData", ctypes.c_void_p),
        ("lpfnHook", ctypes.c_void_p),
        ("lpTemplateName", wintypes.LPCWSTR),
        ("pvReserved", ctypes.c_void_p),
        ("dwReserved", wintypes.DWORD),
        ("FlagsEx", wintypes.DWORD),
    ]


_EXPORT_EXTS = (".md", ".txt", ".wav")


def _export_source(name, kind):
    """Origen y nombre de salida de lo que se exporta.

    Misma resolucion que GET /download: md/txt -> textos/<base>.md,
    wav -> audios/<base>.wav. Devuelve (origen, nombre_salida) o (None, motivo).

    OJO: la extension se quita solo si es una de las conocidas. Con
    `os.path.splitext` un nombre con punto propio se partia por el ULTIMO punto
    («¿Cuanto costaria correr Claude Opus 5.5 en Local.md» -> base «…Opus 5»),
    y ni el guardado ni /download encontraban el fichero.
    """
    base = str(name or "").strip()
    if (not base or base in (".", "..") or ".." in base or "/" in base
            or "\\" in base or os.path.basename(base) != base):
        return None, "bad doc"
    kind = str(kind or "").strip().lower()
    if kind not in ("md", "txt", "wav"):
        return None, "bad kind"
    low = base.lower()
    for ext in _EXPORT_EXTS:
        if low.endswith(ext):
            base = base[:-len(ext)]
            break
    if kind == "wav":
        return os.path.join(AUDIOS_DIR, base + ".wav"), base + ".wav"
    if kind == "txt":
        return os.path.join(DOCS_DIR, base + ".md"), base + ".txt"
    return os.path.join(DOCS_DIR, base + ".md"), base + ".md"


def _export_ctype(out_name):
    """Tipo real del fichero exportado (por su extension de salida)."""
    ext = os.path.splitext(str(out_name))[1].lower()
    if ext == ".wav":
        return "audio/wav"
    if ext == ".txt":
        return "text/plain; charset=utf-8"
    return "text/markdown; charset=utf-8"


def _save_as_dialog(default_name, owner=0):
    """Dialogo nativo «Guardar como...» de Windows.

    Devuelve la ruta elegida o None si se cancela (cancelar NO es un error).
    Se apoya en comdlg32, el mismo dialogo del sistema: el anfitrion de
    WebView2 no puede enseñarlo por su cuenta, y por eso el backend lo abre
    aqui, con la propia ventana del panel como dueña.
    """
    try:
        comdlg = ctypes.windll.comdlg32
        comdlg.GetSaveFileNameW.argtypes = [ctypes.POINTER(_OPENFILENAMEW)]
        comdlg.GetSaveFileNameW.restype = wintypes.BOOL
        comdlg.CommDlgExtendedError.restype = wintypes.DWORD
    except Exception as e:
        log(f"Guardar como: sin dialogo del sistema ({e}).")
        return None
    ext = (os.path.splitext(str(default_name))[1].lstrip(".").lower()
           or "txt")
    es = str(getattr(app, "language", "es") or "es").lower() != "en"
    desc = {"md": ("Documento Markdown", "Markdown document"),
            "txt": ("Texto", "Text"),
            "wav": ("Audio WAV", "WAV audio")}.get(
                ext, ("Fichero", "File"))[0 if es else 1]
    todos = "Todos los ficheros (*.*)" if es else "All files (*.*)"
    # El filtro lleva una descripcion y su patron, y termina en doble NUL.
    filtro = f"{desc} (*.{ext})\0*.{ext}\0{todos}\0*.*\0\0"
    titulo = "Guardar como" if es else "Save as"
    inicio = os.path.join(os.path.expanduser("~"), "Downloads")
    if not os.path.isdir(inicio):
        inicio = os.path.expanduser("~")
    buf = ctypes.create_unicode_buffer(1024)
    buf.value = str(default_name)
    ofn = _OPENFILENAMEW()
    ofn.lStructSize = ctypes.sizeof(_OPENFILENAMEW)
    ofn.hwndOwner = wintypes.HWND(int(owner or 0))
    ofn.lpstrFilter = filtro
    ofn.nFilterIndex = 1
    ofn.lpstrFile = ctypes.cast(buf, wintypes.LPWSTR)
    ofn.nMaxFile = len(buf)
    ofn.lpstrInitialDir = inicio
    ofn.lpstrTitle = titulo
    ofn.lpstrDefExt = ext
    ofn.Flags = (_OFN_EXPLORER | _OFN_OVERWRITEPROMPT | _OFN_PATHMUSTEXIST
                 | _OFN_NOCHANGEDIR | _OFN_HIDEREADONLY
                 | _OFN_DONTADDTORECENT)
    ole = ctypes.windll.ole32
    hr = ole.CoInitializeEx(None, 0x2)          # APARTMENTTHREADED
    try:
        ok = bool(comdlg.GetSaveFileNameW(ctypes.byref(ofn)))
    finally:
        # 0/1 = lo inicializamos nosotros; S_FALSE no exige desinicializar
        # dos veces, asi que solo se suelta el que es nuestro.
        if hr == 0:
            ole.CoUninitialize()
    if not ok:
        err = int(comdlg.CommDlgExtendedError())
        if err:
            log(f"Guardar como: el dialogo fallo ({err:#x}).")
        return None
    return buf.value or None


def _export_save(name, kind, owner=0):
    """Guarda una copia con «Guardar como...» y confirma la ruta elegida.

    Devuelve el JSON que el panel enseña: {ok, path, bytes} al guardar,
    {ok: True, canceled: True} si el usuario cancela (no rompe nada ni da
    error) y {ok: False, error} si no se pudo.
    """
    src, out_name = _export_source(name, kind)
    if src is None:
        log(f"Guardar como: nombre o formato no validos ({name!r}, {kind!r}).")
        return {"ok": False, "error": out_name}
    if not os.path.isfile(src):
        log(f"Guardar como: no existe {src}.")
        return {"ok": False, "error": "missing",
                "file": os.path.basename(src)}
    dest = _save_as_dialog(out_name, owner=owner)
    if not dest:
        log(f"Guardar como: cancelado ({out_name}).")
        return {"ok": True, "canceled": True}
    try:
        # Primero se lee ENTERO y luego se escribe: si el usuario elige la
        # misma ruta que el original, el fichero no se trunca a medias.
        with open(src, "rb") as fh:
            raw = fh.read()
        with open(dest, "wb") as fh:
            fh.write(raw)
    except Exception as e:
        log(f"Guardar como: no se pudo escribir en {dest} ({e}).")
        return {"ok": False, "error": str(e)}
    log(f"Guardar como: {out_name} -> {dest} ({len(raw)} bytes).")
    return {"ok": True, "path": dest, "bytes": len(raw),
            "file": os.path.basename(dest)}


def _export_owner():
    """Ventana del panel para que el dialogo salga encima de ella (o 0)."""
    try:
        hwnd = int(getattr(_panel_host, "hwnd", 0) or 0)
    except Exception:
        hwnd = 0
    if hwnd and not _user32.IsWindow(wintypes.HWND(hwnd)):
        hwnd = 0
    return hwnd


# ------------------------------------------------------------ estado
class ControlServer:
    """Servidor local del panel de ajustes.

        GET  /panel[/style.css|/app.js]  -> interfaz
        GET  /state                       -> estado actual en JSON
        POST /rpc                         -> {"action": ..., "value": ...}

    Escucha solo en 127.0.0.1. Servir la UI desde aquí la deja en el mismo
    origen que la API, así el panel puede usar fetch sin CORS. Los cambios se
    encolan en ui_events para que los aplique el hilo principal de Tk (sus
    handlers tocan widgets)."""

    PANEL_FILES = {"/panel": "index.html", "/panel/": "index.html",
                   "/panel/style.css": "style.css", "/panel/app.js": "app.js",
                   # Barra de ventana integrada: solo la pide el backend de
                   # WebView2, que la inyecta al cargar (panel/desktop.js).
                   "/panel/desktop.js": "desktop.js"}

    def __init__(self, port, get_state, post_action):
        self.port = port
        self.get_state = get_state
        self.post_action = post_action
        self.httpd = None
        self.thread = None

    def start(self):
        import http.server
        import socketserver

        control = self
        panel_dir = os.path.join(RESOURCE_DIR, "panel")

        class Handler(http.server.BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"
            def log_message(self, *a):
                pass

            def _send(self, code, body: bytes, ctype="application/json"):
                self.send_response(code)
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                try:
                    self.wfile.write(body)
                except Exception:
                    pass

            def do_GET(self):
                path = self.path.split("?", 1)[0]
                if path == "/panel/icon.png":
                    # Icono de la barra: el MISMO dibujo que la bandeja y el
                    # .exe, renderizado al tamaño que pida la página.
                    import urllib.parse
                    qs = urllib.parse.parse_qs(
                        urllib.parse.urlparse(self.path).query)
                    try:
                        size = int((qs.get("size") or ["24"])[0])
                    except (TypeError, ValueError):
                        size = 24
                    theme = (qs.get("theme") or [""])[0].strip().lower()
                    if theme not in ("light", "dark"):
                        theme = None            # None = tema de la app
                    png = _panel_icon_png(size, theme)
                    if not png:
                        self._send(404, b"not found", "text/plain")
                        return
                    self.send_response(200)
                    self.send_header("Content-Type", "image/png")
                    self.send_header("Content-Length", str(len(png)))
                    # Sin caché de navegador: si cambia el tema, el icono tiene
                    # que cambiar ya (la página añade ?v= por si acaso).
                    self.send_header("Cache-Control", "no-store")
                    self.end_headers()
                    try:
                        self.wfile.write(png)
                    except Exception:
                        pass
                    return
                if path == "/panel/mictest.wav":
                    # Audio de la ultima prueba de micro (para escucharlo).
                    raw = b""
                    try:
                        with open(_mictest.WAV, "rb") as fh:
                            raw = fh.read()
                        ok = bool(raw)
                    except Exception:
                        ok = False
                    if not ok:
                        self._send(404, b"not found", "text/plain")
                        return
                    self.send_response(200)
                    self.send_header("Content-Type", "audio/wav")
                    self.send_header("Content-Length", str(len(raw)))
                    self.send_header("Cache-Control", "no-store")
                    self.send_header(
                        "Content-Disposition",
                        'inline; filename="mictest.wav"')
                    self.end_headers()
                    try:
                        self.wfile.write(raw)
                    except Exception:
                        pass
                    return
                name = ControlServer.PANEL_FILES.get(path)
                if name:
                    f = os.path.join(panel_dir, name)
                    try:
                        with open(f, "rb") as fh:
                            body = fh.read()
                    except Exception:
                        self._send(404, b"not found", "text/plain")
                        return
                    ctype = ("text/html; charset=utf-8" if name.endswith(".html")
                             else "text/css; charset=utf-8" if name.endswith(".css")
                             else "text/javascript; charset=utf-8")
                    self._send(200, body, ctype)
                    return
                if path == "/state":
                    try:
                        body = json.dumps(control.get_state()).encode("utf-8")
                    except Exception as e:
                        body = json.dumps({"error": str(e)}).encode("utf-8")
                    self._send(200, body)
                elif path == "/doc":
                    import urllib.parse
                    qs = urllib.parse.parse_qs(
                        urllib.parse.urlparse(self.path).query)
                    name_doc = (qs.get("doc") or [""])[0]
                    if ".." in name_doc or "\\" in name_doc or not name_doc:
                        self._send(400, b'{"error":"bad doc"}')
                        return
                    f = os.path.join(DOCS_DIR, name_doc)
                    try:
                        with open(f, "r", encoding="utf-8") as fh:
                            content = fh.read()
                    except Exception:
                        self._send(404, b"not found", "text/plain")
                        return
                    if "download" in qs:
                        raw = content.encode("utf-8")
                        self.send_response(200)
                        self.send_header("Content-Type",
                                         "application/octet-stream")
                        self.send_header("Content-Length", str(len(raw)))
                        self.send_header(
                            "Content-Disposition",
                            f'attachment; filename="{name_doc}"')
                        self.end_headers()
                        try:
                            self.wfile.write(raw)
                        except Exception:
                            pass
                        return
                    self._send(200, content.encode("utf-8"), "text/plain; charset=utf-8")
                elif path == "/audio":
                    # Audio (wav de reunión o original subido) en audios/. Se
                    # sirve con su TIPO REAL y con RANGOS: el navegador empieza a
                    # sonar con el primer trozo y puede saltar sin bajarse el
                    # fichero entero. Antes iba como octet-stream y sin rangos, y
                    # el panel tenía que descargar 22 MB a un blob antes de sonar
                    # (eso es lo que se notaba como «se traba» en audios largos).
                    import urllib.parse
                    qs = urllib.parse.parse_qs(
                        urllib.parse.urlparse(self.path).query)
                    name_audio = (qs.get("name") or [""])[0]
                    if ".." in name_audio or "\\" in name_audio or not name_audio:
                        self._send(400, b'{"error":"bad name"}')
                        return
                    f = os.path.join(AUDIOS_DIR, name_audio)
                    try:
                        total = os.path.getsize(f)
                        fh = open(f, "rb")
                    except Exception:
                        self._send(404, b"not found", "text/plain")
                        return
                    disp = "inline" if "download" not in qs else "attachment"
                    start, end, partial = 0, max(0, total - 1), False
                    rng = str(self.headers.get("Range") or "").strip()
                    if rng.startswith("bytes="):
                        spec = rng[6:].split(",")[0].strip()
                        a, _, b = spec.partition("-")
                        try:
                            if a == "":
                                start = max(0, total - int(b))
                                end = total - 1
                            else:
                                start = int(a)
                                end = int(b) if b else total - 1
                            partial = True
                        except ValueError:
                            partial = False
                    if partial:
                        start = max(0, min(start, max(0, total - 1)))
                        end = max(start, min(end, max(0, total - 1)))
                    else:
                        start, end = 0, max(0, total - 1)
                    length = end - start + 1
                    self.send_response(206 if partial else 200)
                    self.send_header("Content-Type", _audio_ctype(name_audio))
                    self.send_header("Content-Length", str(length))
                    self.send_header("Accept-Ranges", "bytes")
                    self.send_header("Cache-Control", "no-store")
                    if partial:
                        self.send_header("Content-Range",
                                         f"bytes {start}-{end}/{total}")
                    self.send_header(
                        "Content-Disposition",
                        f'{disp}; filename="{name_audio}"')
                    self.end_headers()
                    try:
                        # Se manda por trozos: nunca se carga el fichero entero
                        # en memoria (un wav de reunión puede pasar de 60 MB).
                        fh.seek(start)
                        left = length
                        while left > 0:
                            chunk = fh.read(min(262144, left))
                            if not chunk:
                                break
                            self.wfile.write(chunk)
                            left -= len(chunk)
                    except Exception:
                        pass
                    finally:
                        fh.close()
                    return
                elif path == "/peaks":
                    # Envolvente de la onda para la vista previa de audio.
                    import urllib.parse
                    qs = urllib.parse.parse_qs(
                        urllib.parse.urlparse(self.path).query)
                    name_audio = (qs.get("name") or [""])[0]
                    if ".." in name_audio or "\\" in name_audio or not name_audio:
                        self._send(400, b'{"error":"bad name"}')
                        return
                    try:
                        body = json.dumps(_peaks(
                            os.path.join(AUDIOS_DIR, name_audio))).encode("utf-8")
                    except Exception as e:
                        self._send(404, json.dumps(
                            {"error": str(e)}).encode("utf-8"))
                        return
                    self._send(200, body)
                elif path == "/download":
                    # Descarga directa de un documento para el panel:
                    #   ?doc=NOMBRE_BASE&kind=md|wav|txt
                    #   md  -> textos/NOMBRE_BASE.md   (tal cual, markdown)
                    #   wav -> audios/NOMBRE_BASE.wav  (audio de la reunión)
                    #   txt -> el mismo texto en texto plano, extensión .txt
                    # Siempre con Content-Disposition: attachment para que el
                    # navegador lo BAJE en vez de abrirlo. Nombre validado (sin
                    # rutas); 404 si no existe.
                    import urllib.parse
                    qs = urllib.parse.parse_qs(
                        urllib.parse.urlparse(self.path).query)
                    target, down = _export_source(
                        (qs.get("doc") or [""])[0],
                        (qs.get("kind") or ["md"])[0])
                    if target is None:
                        self._send(400, json.dumps(
                            {"error": down}).encode("utf-8"))
                        return
                    ctype = _export_ctype(down)
                    try:
                        with open(target, "rb") as fh:
                            raw = fh.read()
                    except Exception:
                        self._send(404, b"not found", "text/plain")
                        return
                    self.send_response(200)
                    self.send_header("Content-Type", ctype)
                    self.send_header("Content-Length", str(len(raw)))
                    self.send_header("Content-Disposition",
                                     f'attachment; filename="{down}"')
                    self.send_header("Cache-Control", "no-store")
                    self.end_headers()
                    try:
                        self.wfile.write(raw)
                    except Exception:
                        pass
                    return
                else:
                    self._send(404, b'{"error":"not found"}')

            def do_POST(self):
                ctype = self.headers.get("Content-Type", "")
                if "multipart/form-data" in ctype:
                    # Subida de audios (multipart): se guarda en uploads/
                    # (persistente) y se encola para transcripcion.
                    try:
                        n = int(self.headers.get("Content-Length") or 0)
                        raw = self.rfile.read(n)
                        boundary = ctype.split("boundary=")[-1].strip('"')
                        saved = []
                        for part in raw.split(f"--{boundary}".encode()):
                            if b"filename=" not in part:
                                continue
                            _crlf = bytes((13, 10))
                            head, _, body = part.partition(_crlf * 2)
                            payload = body[:-2] if body.endswith(_crlf) else body
                            if not payload.strip(_crlf):
                                continue
                            import re
                            base = re.search(rb'filename="([^"]+)"', head)
                            orig = (base.group(1).decode("utf-8", "replace")
                                    if base else "audio")
                            entry = _uploads.add(orig, payload)
                            _audio_queue.add(_uploads.path_of(entry),
                                             entry["name"], key=entry["id"])
                            saved.append(entry["name"])
                        self._send(200, json.dumps(
                            {"ok": True, "saved": len(saved),
                             "names": saved,
                             "uploads": _uploads.snapshot()}).encode("utf-8"))
                    except Exception as e:
                        self._send(500, json.dumps(
                            {"error": str(e)}).encode("utf-8"))
                    return
                try:
                    n = int(self.headers.get("Content-Length") or 0)
                    raw = self.rfile.read(n) if n else b"{}"
                    msg = json.loads(raw.decode("utf-8", "replace") or "{}")
                except Exception:
                    self._send(400, b'{"error":"bad json"}')
                    return
                action = msg.get("action")
                if action == "check_update":
                    # Comprueba si hay version nueva. Sin `force` respeta el
                    # ajuste `check_updates` (si esta apagado, NO toca la red).
                    # Con force -- {"action":"check_update","value":{"force":
                    # true}} -- consulta GitHub AUNQUE este apagado: es una
                    # accion EXPLICITA del usuario (el enlace «Actualizar» del
                    # panel), no una comprobacion de fondo.
                    try:
                        val = msg.get("value")
                        force = (bool(val.get("force"))
                                 if isinstance(val, dict) else False)
                        result = check_update(force=force)
                        ran = bool(force or result.get("enabled"))
                        self._send(200, json.dumps(
                            {"ok": ran and not bool(result.get("error")),
                             "force": force,
                             "update": result}).encode("utf-8"))
                    except Exception as e:
                        self._send(500, json.dumps(
                            {"error": str(e)}).encode("utf-8"))
                    return
                if action == "update":
                    # Descarga, verifica e instala el paquete de la release. Es
                    # una accion EXPLICITA del usuario (el enlace «Instalar»
                    # del panel): NO la bloquea el ajuste `check_updates`. Con
                    # la comprobacion automatica apagada, una busqueda FORZADA
                    # previa (check_update con force) ya relleno el estado, y
                    # este POST sigue valiendo. El trabajo pesado va en un
                    # hilo: responde ya y el avance se sigue por
                    # /state.update.progress.
                    try:
                        if not UPDATE_STATE.get("available"):
                            self._send(200, json.dumps(
                                {"ok": True, "accepted": True, "started": False,
                                 "note": "no hay version nueva (comprueba antes)",
                                 "update": dict(UPDATE_STATE)}).encode("utf-8"))
                            return
                        threading.Thread(target=apply_update,
                                         kwargs={"launch": True},
                                         daemon=True).start()
                        self._send(202, json.dumps(
                            {"ok": True, "accepted": True, "started": True,
                             "update": dict(UPDATE_STATE)}).encode("utf-8"))
                    except Exception as e:
                        self._send(500, json.dumps(
                            {"error": str(e)}).encode("utf-8"))
                    return
                if action == "upload.remove":
                    # Quita una subida de la lista y borra su fichero del disco.
                    try:
                        ok = _uploads.remove(msg.get("value"))
                        self._send(200 if ok else 404, json.dumps(
                            {"ok": ok, "uploads": _uploads.snapshot()}
                        ).encode("utf-8"))
                    except Exception as e:
                        self._send(500, json.dumps(
                            {"error": str(e)}).encode("utf-8"))
                    return
                if action == "audio.orphans":
                    # SOLO LEE: lista los audios de audios/ que ya no emparejan
                    # con ningun documento ni subida. No borra nada.
                    try:
                        orphans = audio_orphans()
                        self._send(200, json.dumps(
                            {"ok": True, "count": len(orphans),
                             "orphans": orphans}).encode("utf-8"))
                    except Exception as e:
                        self._send(500, json.dumps(
                            {"error": str(e)}).encode("utf-8"))
                    return
                if action == "audio.clean":
                    # Borra los huerfanos de audios/ SOLO a proposito: exige
                    # {"action":"audio.clean","value":"confirmar"}. Nunca se
                    # ejecuta sola (los 35 .wav que ya habia siguen intactos
                    # hasta que el autor lo pida).
                    try:
                        if str(msg.get("value") or "").strip().lower() not in (
                                "confirmar", "confirm"):
                            self._send(400, json.dumps(
                                {"ok": False,
                                 "error": "confirmacion requerida"}
                            ).encode("utf-8"))
                            return
                        removed = []
                        for o in audio_orphans():
                            p = os.path.join(AUDIOS_DIR, o["name"])
                            try:
                                os.remove(p)
                                removed.append(o["name"])
                            except Exception as e:
                                log(f"No se pudo borrar el audio huerfano "
                                    f"{p}: {e}")
                        log(f"Audios huerfanos borrados: {len(removed)}")
                        self._send(200, json.dumps(
                            {"ok": True, "removed": len(removed),
                             "names": removed}).encode("utf-8"))
                    except Exception as e:
                        self._send(500, json.dumps(
                            {"error": str(e)}).encode("utf-8"))
                    return
                if action == "doc.save":
                    # Guardado del documento editado en la vista previa.
                    try:
                        name_doc = msg.get("doc", "")
                        if ".." in name_doc or "\\" in name_doc or not name_doc:
                            self._send(400, b'{"error":"bad doc"}')
                            return
                        with open(os.path.join(DOCS_DIR, name_doc), "w",
                                  encoding="utf-8") as fh:
                            fh.write(msg.get("content", ""))
                        self._send(200, b'{"ok":true}')
                    except Exception as e:
                        self._send(500, json.dumps(
                            {"error": str(e)}).encode("utf-8"))
                    return
                if action == "export":
                    # «Descargar» del panel: lo guarda el BACKEND con el
                    # dialogo nativo «Guardar como...» (WebView2 cancela en
                    # silencio las descargas por navegacion; ver el bloque de
                    # _export_save). value = {name|doc, kind: md|txt|wav}.
                    try:
                        val = msg.get("value") or {}
                        if not isinstance(val, dict):
                            val = {}
                        res = _export_save(val.get("name") or val.get("doc"),
                                           val.get("kind"),
                                           owner=_export_owner())
                        self._send(200, json.dumps(res).encode("utf-8"))
                    except Exception as e:
                        log(f"Guardar como: fallo inesperado ({e}).")
                        self._send(500, json.dumps(
                            {"ok": False, "error": str(e)}).encode("utf-8"))
                    return
                if action == "meeting":
                    try:
                        v = msg.get("value")
                        if v == "start":
                            ok = _meeting.start()
                            self._send(200, json.dumps(
                                {"ok": ok,
                                 "status": _meeting.status}).encode("utf-8"))
                        elif v in ("pause", "resume"):
                            (_meeting.pause if v == "pause"
                             else _meeting.resume)()
                            self._send(200, json.dumps(
                                {"ok": True, "paused": _meeting.paused,
                                 "status": _meeting.status}).encode("utf-8"))
                        elif v == "cancel":
                            _meeting.cancel()
                            self._send(200, json.dumps(
                                {"ok": True, "status": _meeting.status}
                            ).encode("utf-8"))
                        elif v == "dismiss":
                            self._send(200, json.dumps(
                                {"ok": bool(_meeting.dismiss()),
                                 "status": _meeting.status}).encode("utf-8"))
                        else:
                            _meeting.stop()
                            self._send(200, json.dumps(
                                {"ok": True, "status": _meeting.status,
                                 "doc": _meeting.doc}).encode("utf-8"))
                    except Exception as e:
                        self._send(500, json.dumps(
                            {"error": str(e)}).encode("utf-8"))
                    return
                if action == "dictation":
                    # Control del dictado por API (panel y pruebas): _mic lo
                    # fija main(). start reclama la grabacion; stop la cierra
                    # (transcribe) y cancel la descarta.
                    try:
                        v = str(msg.get("value") or "").strip().lower()
                        m = _mic
                        if m is None:
                            self._send(503, json.dumps(
                                {"ok": False, "error": "mic no listo"}).encode("utf-8"))
                            return
                        if v == "start":
                            if app.state == "idle":
                                start_recording(m)
                            ok = (app.state == "recording")
                        elif v == "cancel":
                            cancel_recording(m)
                            ok = True
                        else:
                            finish_recording(m)
                            ok = True
                        self._send(200, json.dumps(
                            {"ok": bool(ok), "st": app.state}).encode("utf-8"))
                    except Exception as e:
                        self._send(500, json.dumps(
                            {"error": str(e)}).encode("utf-8"))
                    return
                if action in ("doc.delete", "doc.open"):
                    # doc.delete: elimina el documento; doc.open: lo abre.
                    try:
                        name_doc = msg.get("doc", "")
                        if (".." in name_doc or "\\" in name_doc
                                or "/" in name_doc or not name_doc):
                            self._send(400, b'{"error":"bad doc"}')
                            return
                        target = os.path.join(DOCS_DIR, name_doc)
                        if not os.path.isfile(target):
                            self._send(404, b'{"error":"not found"}')
                            return
                        if action == "doc.delete":
                            base = os.path.splitext(name_doc)[0]
                            os.remove(target)
                            # La copia de trabajo del audio en audios/ se va con
                            # el documento (para una reunion, la grabacion
                            # original: audios/reunion-<sello>.wav). Se empareja
                            # por NOMBRE BASE, igual que doc.rename y /download.
                            wav = _audios_ref(base + ".wav")
                            if wav:
                                _remove_file(wav)
                            self._send(200, b'{"ok":true}')
                        else:
                            with open(target, "r", encoding="utf-8") as fh:
                                body = fh.read()
                            self._send(200, body.encode("utf-8"),
                                       "text/plain; charset=utf-8")
                    except Exception as e:
                        self._send(500, json.dumps(
                            {"error": str(e)}).encode("utf-8"))
                    return
                if action == "doc.rename":
                    # Renombra el documento y su .wav emparejado: se cambia
                    # solo el nombre base, las extensiones se conservan. Avisa
                    # (409 exists) si ya hay un fichero con ese nombre.
                    try:
                        old_doc = msg.get("doc", "")
                        new_base = (msg.get("name") or "").strip()
                        if (".." in old_doc or "\\" in old_doc or "/" in old_doc
                                or not old_doc):
                            self._send(400, b'{"error":"bad doc"}')
                            return
                        src = os.path.join(DOCS_DIR, old_doc)
                        if not os.path.isfile(src):
                            self._send(404, b'{"error":"not found"}')
                            return
                        # El nombre base es lo unico que cambia: si el autor
                        # teclea la extension, se descarta.
                        new_base = os.path.splitext(new_base)[0]
                        bad = set('<>:"/\\|?*') | {chr(c) for c in range(32)}
                        if (not new_base or new_base in (".", "..")
                                or any(c in bad for c in new_base)
                                or new_base.rstrip() != new_base):
                            self._send(400, b'{"error":"bad name"}')
                            return
                        old_base = os.path.splitext(old_doc)[0]
                        ext = os.path.splitext(old_doc)[1]
                        if new_base == old_base:
                            self._send(200, json.dumps(
                                {"ok": True, "name": old_doc}).encode("utf-8"))
                            return
                        new_doc = new_base + ext
                        dst_md = os.path.join(DOCS_DIR, new_doc)
                        dst_wav = os.path.join(AUDIOS_DIR, new_base + ".wav")
                        if os.path.exists(dst_md) or os.path.exists(dst_wav):
                            self._send(409, b'{"error":"exists"}')
                            return
                        src_wav = os.path.join(AUDIOS_DIR, old_base + ".wav")
                        os.replace(src, dst_md)
                        if os.path.isfile(src_wav):
                            os.replace(src_wav, dst_wav)
                        log(f"Documento renombrado: {old_doc} -> {new_doc}")
                        # La subida emparejada sigue el rastro del renombrado:
                        # sin esto dejaban de emparejarse y volvían a salir DOS
                        # tarjetas del mismo audio.
                        try:
                            _uploads.rename_doc(old_base, new_base)
                        except Exception as e:
                            log(f"No se pudo seguir el renombrado en subidas: {e}")
                        self._send(200, json.dumps(
                            {"ok": True, "name": new_doc}).encode("utf-8"))
                    except Exception as e:
                        self._send(500, json.dumps(
                            {"error": str(e)}).encode("utf-8"))
                    return
                try:
                    result = control.post_action(action, msg.get("value"))
                    if not isinstance(result, dict):
                        result = {"ok": True}
                    self._send(200, json.dumps(result).encode("utf-8"))
                except Exception as e:
                    self._send(500, json.dumps({"error": str(e)}).encode("utf-8"))

        class Server(socketserver.ThreadingTCPServer):
            # SO_REUSEADDR en Windows permite el DOBLE bind silencioso: dos
            # dictas se casan con el mismo puerto y el panel habla con un
            # proceso distinto del que pinta la isla. Sin él, un puerto
            # ocupado falla de forma limpia y pasamos al siguiente.
            allow_reuse_address = False
            daemon_threads = True

        # Busca el primer puerto libre desde PANEL_PORT (hasta +12).
        try:
            for port in range(self.port, self.port + 12):
                try:
                    self.httpd = Server(("127.0.0.1", port), Handler)
                    self.port = port
                    break
                except OSError:
                    continue
        except Exception as e:
            self.httpd = None
            log(f"Servidor de control no arrancó: {e}")
            return
        if self.httpd is None:
            log(f"Servidor de control: sin puerto libre en el rango de {self.port - 12}..{self.port}")
            return
        self.thread = threading.Thread(target=self.httpd.serve_forever,
                                       kwargs={"poll_interval": 0.5}, daemon=True)
        self.thread.start()
        log(f"Panel: control en 127.0.0.1:{self.port}")

    def stop(self):
        try:
            if self.httpd:
                self.httpd.shutdown()
                self.httpd.server_close()
        except Exception:
            pass


def _panel_window_cmd(hwnd: int, cmd: str):
    """Acciones de la barra integrada del panel (arrastre, maximizar)."""
    _HTCAPTION = 2
    _WM_NCLBUTTONDOWN = 0x00A1
    _SW_MINIMIZE, _SW_MAXIMIZE, _SW_RESTORE = 6, 3, 9
    try:
        if cmd == "drag":
            _user32.ReleaseCapture()
            _user32.SendMessageW(hwnd, _WM_NCLBUTTONDOWN, _HTCAPTION, 0)
        elif cmd == "minimize":
            _user32.ShowWindow(hwnd, _SW_MINIMIZE)
        elif cmd == "maximize":
            if _user32.IsZoomed(hwnd):
                _user32.ShowWindow(hwnd, _SW_RESTORE)
            else:
                _user32.ShowWindow(hwnd, _SW_MAXIMIZE)
    except Exception as e:
        log(f"Acción de ventana no disponible: {e}")


def _clear_stale_panel(profile_dir):
    """Cierra el navegador del panel que quedó de una instancia anterior.

    Si dicta muere de golpe (kill, cuelgue) su Chrome sobrevive y, como el
    perfil del panel es exclusivo suyo, al abrirlo otra vez Chrome reutiliza
    ESE proceso y aparece una ventana más (dos paneles a la vez). Se busca por
    perfil y no por título, porque el título es precisamente lo que dicta
    cambia a «dicta» y ya no distingue la ventana vieja de la nueva.
    """
    try:
        nombres = ("Name='chrome.exe' or Name='msedge.exe' or "
                   "Name='brave.exe' or Name='chrome_proxy.exe'")
        ps = ("$p = @(Get-CimInstance Win32_Process -Filter \"" + nombres +
              "\" | Where-Object { $_.CommandLine -like '*" + profile_dir +
              "*' }); $p | ForEach-Object { Stop-Process -Id $_.ProcessId -Force "
              "-ErrorAction SilentlyContinue }; $p.Count")
        r = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                           capture_output=True, timeout=25,
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        salida = r.stdout.decode("ascii", "replace").strip().splitlines()
        n = int(salida[-1]) if salida and salida[-1].strip().isdigit() else 0
        if n:
            time.sleep(0.4)
        return n
    except Exception as e:
        log(f"Panel: no se pudo limpiar el navegador anterior ({e}).")
        return 0


def _panel_hwnd(window_title: str, pid: int = 0):
    """Localiza la ventana app del panel, por título único o por proceso.

    El título único solo vale para encontrarla la PRIMERA vez: en cuanto se
    renombra a «dicta», Chrome lo pisa con el de la página. Por eso también se
    acepta la ventana cuyo proceso dueño es el del panel.
    """
    found = []
    Proc = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
    _user32.GetWindowThreadProcessId.argtypes = [
        wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    _user32.GetWindowThreadProcessId.restype = wintypes.DWORD

    def cb(h, _):
        if not _user32.IsWindowVisible(h):
            return True
        buf = ctypes.create_unicode_buffer(64)
        _user32.GetClassNameW(h, buf, 64)
        if buf.value != "Chrome_WidgetWin_1":
            return True
        if pid:
            owner = wintypes.DWORD()
            _user32.GetWindowThreadProcessId(h, ctypes.byref(owner))
            if owner.value == pid:
                found.append(h)
                return True
        title = ctypes.create_unicode_buffer(160)
        _user32.GetWindowTextW(h, title, len(title))
        if title.value == window_title:
            found.append(h)
        return True

    _user32.EnumWindows(Proc(cb), 0)
    return found[0] if found else 0


PANEL_TITLE = "dicta \u2014 Ajustes"     # título de la ventana del panel


# ------------------------------------------------ backend de la ventana
def _webview2_presente():
    """True si hay runtime de WebView2 (Windows 11 lo trae de serie)."""
    try:
        import glob
        base = os.path.join(
            os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"),
            "Microsoft", "EdgeWebView", "Application")
        if glob.glob(os.path.join(base, "*", "msedgewebview2.exe")):
            return True
    except Exception:
        pass
    try:
        import winreg
        clave = ("SOFTWARE\\WOW6432Node\\Microsoft\\EdgeUpdate\\Clients\\"
                 "{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}")
        for hive in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
            try:
                with winreg.OpenKey(hive, clave) as h:
                    if winreg.QueryValueEx(h, "pv")[0]:
                        return True
            except Exception:
                continue
    except Exception:
        pass
    return False


def _own_top_hwnd():
    """HWND de la ventana de nivel superior de ESTE proceso (la del panel).

    La crea pywebview/WinForms dentro de dicta, así que basta enumerar por pid
    y quedarse con la visible de mayor área (la del panel; no las ventanas
    auxiliares ocultas que WinForms mantiene). Es la clave para redondear las
    esquinas: la ventana es del propio proceso y `DwmSetWindowAttribute` sí
    funciona (con la de Chrome, de otro proceso, fallaba con E_HANDLE).
    """
    if not hasattr(ctypes, "windll"):
        return 0
    pid = os.getpid()
    mejor = [0, 0]
    Proc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    def cb(h, _):
        try:
            owner = wintypes.DWORD()
            _user32.GetWindowThreadProcessId(h, ctypes.byref(owner))
            if owner.value != pid or not _user32.IsWindowVisible(h):
                return True
            r = wintypes.RECT()
            _user32.GetWindowRect(h, ctypes.byref(r))
            area = max(0, r.right - r.left) * max(0, r.bottom - r.top)
            if area > mejor[1]:
                mejor[0], mejor[1] = int(h), area
        except Exception:
            pass
        return True

    try:
        _user32.EnumWindows(Proc(cb), 0)
    except Exception:
        return 0
    return mejor[0]


def _preparar_prototipos_ventana():
    """Prototipos de las llamadas de ventana que usa el arrastre (una vez)."""
    global _prototipos_ventana
    if _prototipos_ventana:
        return
    _prototipos_ventana = True
    try:
        _user32.GetCursorPos.argtypes = (ctypes.POINTER(_POINT),)
        _user32.GetCursorPos.restype = wintypes.BOOL
        _user32.GetWindowRect.argtypes = (wintypes.HWND,
                                          ctypes.POINTER(wintypes.RECT))
        _user32.GetWindowRect.restype = wintypes.BOOL
        _user32.IsZoomed.argtypes = (wintypes.HWND,)
        _user32.IsZoomed.restype = wintypes.BOOL
        _user32.SetWindowPos.argtypes = (wintypes.HWND, wintypes.HWND,
                                         ctypes.c_int, ctypes.c_int,
                                         ctypes.c_int, ctypes.c_int,
                                         wintypes.UINT)
        _user32.SetWindowPos.restype = wintypes.BOOL
        # Para el arrastre de una ventana maximizada: hay que leer la
        # geometría de ventana normal (rcNormalPosition) y restaurarla.
        _user32.GetWindowPlacement.argtypes = (
            wintypes.HWND, ctypes.POINTER(_WINDOWPLACEMENT))
        _user32.GetWindowPlacement.restype = wintypes.BOOL
        _user32.ShowWindow.argtypes = (wintypes.HWND, ctypes.c_int)
        _user32.ShowWindow.restype = wintypes.BOOL
    except Exception:
        pass


_prototipos_ventana = False


def _round_window_corners(hwnd, log_ok=True):
    """Esquinas redondeadas de Windows 11 en la ventana del panel.

    `DWMWA_WINDOW_CORNER_PREFERENCE` (33) = `DWMWCP_ROUND` (2). Se puede hacer
    porque la ventana es de ESTE proceso (pywebview); con la de Chrome fallaba
    con E_HANDLE. Se añade `DWMWA_BORDER_COLOR` (34) = `DWMWA_COLOR_NONE`
    (0xFFFFFFFE) para quitar el filo de 1 px y que la forma la delimite solo el
    redondeo. Se reaplica el marco con SWP_FRAMECHANGED para que DWM lo
    recalcule. Devuelve True si DWM aceptó la preferencia.
    """
    if not hwnd:
        return False
    try:
        pref = ctypes.c_int(2)                      # DWMWCP_ROUND
        hr = ctypes.windll.dwmapi.DwmSetWindowAttribute(
            wintypes.HWND(hwnd), 33, ctypes.byref(pref), ctypes.sizeof(pref))
        borde = wintypes.DWORD(0xFFFFFFFE)          # DWMWA_COLOR_NONE
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            wintypes.HWND(hwnd), 34, ctypes.byref(borde), ctypes.sizeof(borde))
    except Exception as e:
        log(f"Panel: no se pudieron redondear las esquinas ({e}).")
        return False
    if hr != 0:
        if log_ok:
            log(f"Panel: DWM rechazó el redondeo (hr=0x{hr & 0xffffffff:08x}).")
        return False
    try:
        set_pos = _user32.SetWindowPos
        set_pos.argtypes = (wintypes.HWND, wintypes.HWND, ctypes.c_int,
                            ctypes.c_int, ctypes.c_int, ctypes.c_int,
                            wintypes.UINT)
        set_pos.restype = wintypes.BOOL
        set_pos(wintypes.HWND(hwnd), None, 0, 0, 0, 0,
                0x0001 | 0x0002 | 0x0004 | 0x0020)   # NOSIZE|NOMOVE|NOZORDER|FRAMECHANGED
    except Exception:
        pass
    if log_ok:
        log("Panel: esquinas redondeadas (DWM, Windows 11).")
    return True


# ---- Redimensionado de la ventana del panel (sin marco) --------------------
# La ventana del panel NO se puede redimensionar hoy, y la causa es doble y
# MEDIDA:
#   1. Al ser sin marco (`frameless=True`), Windows no dibuja la franja de
#      borde y el form no tiene el estilo de tamaño (WS_THICKFRAME): no hay
#      bordes que agarrar. La barra superior SÍ arrastra porque ese gesto se
#      implementó a mano (`start_drag`), pero eso solo MUEVE.
#   2. La vía habitual para devolver los bordes —responder WM_NCHITTEST con
#      HTLEFT/HTRIGHT/... en la franja del borde— TAMPOCO sirve en ESTA
#      ventana, y está medido por qué: el control de WebView2 (clase
#      `Chrome_RenderWidgetHostHWND`) CUBRE TODO el cliente, de borde a borde,
#      así que `WindowFromPoint` en CUALQUIER punto del borde devuelve ESE hijo
#      y nunca el form de nivel superior. Los mensajes de ratón no llegan al
#      form, así que su WM_NCHITTEST no se dispara jamás.
# Solución: la barra (panel/desktop.js) detecta la franja del borde con unas
# tiras invisibles y pide aquí el redimensionado; el host lleva entonces el bucle
# de tamaño él mismo (igual que ya lleva el de ARRASTRE), siguiendo al ratón con
# SetWindowPos. Se probó ANTES la vía «nativa» de mandar WM_NCLBUTTONDOWN con el
# código HT del borde (el mismo truco que mueve una ventana por HTCAPTION) y se
# MIDIÓ que NO redimensiona esta ventana (arrastrando los cuatro bordes y una
# esquina: dW=dH=dX=dY=0): sin WS_THICKFRAME Windows no entra en el bucle modal
# de tamaño. Por eso el bucle lo lleva el host, que además aplica el mínimo del
# diseño (y `_install_panel_min_size` lo refuerza en WM_GETMINMAXINFO).

# Bordes que puede pedir la barra (una esquina combina dos).
EDGES = ("left", "right", "top", "bottom",
         "topleft", "topright", "bottomleft", "bottomright")

WM_GETMINMAXINFO = 0x0024
_PANEL_MIN_W, _PANEL_MIN_H = 800, 520      # suelo del diseño (ver create_...)


class _MINMAXINFO(ctypes.Structure):
    """MINMAXINFO de Win32: lleva el tamaño mínimo que respeta el bucle de tamaño."""
    _fields_ = [("ptReserved", _POINT), ("ptMaxSize", _POINT),
                ("ptMaxPosition", _POINT), ("ptMinTrackSize", _POINT),
                ("ptMaxTrackSize", _POINT)]


# WNDPROC: LRESULT CALLBACK (HWND, UINT, WPARAM, LPARAM). En x64 el puntero de
# la función vieja y el resultado son de 64 bits (c_ssize_t), o el HWND llega
# truncado con extensión de signo (la misma familia de fallo que el resto del
# fichero).
_WNDPROC = ctypes.WINFUNCTYPE(ctypes.c_ssize_t, wintypes.HWND, wintypes.UINT,
                              wintypes.WPARAM, wintypes.LPARAM)
_panel_wndprocs = {}        # hwnd -> (proc_viejo, proc_nuevo)  (evita el GC)


def _install_panel_min_size(hwnd):
    """Fija el TAMAÑO MÍNIMO de la ventana del panel subclasificando su WndProc.

    Intercepta SOLO WM_GETMINMAXINFO (mensaje benigno que SÍ llega al form, al
    contrario que WM_NCHITTEST) y garantiza ptMinTrackSize >= 800x520, para que
    el redimensionado nativo no pueda colapsar el diseño por debajo del suelo.
    Encadena al WndProc original con CallWindowProcW; idempotente por hwnd.
    Devuelve True si quedó instalado.
    """
    if not hwnd:
        return False
    key = int(hwnd)
    if key in _panel_wndprocs:
        return True
    try:
        u = _user32
        hw = wintypes.HWND(hwnd)
        u.GetWindowLongPtrW.argtypes = [wintypes.HWND, ctypes.c_int]
        u.GetWindowLongPtrW.restype = ctypes.c_void_p
        u.SetWindowLongPtrW.argtypes = [wintypes.HWND, ctypes.c_int,
                                        ctypes.c_void_p]
        u.SetWindowLongPtrW.restype = ctypes.c_void_p
        u.CallWindowProcW.argtypes = [ctypes.c_void_p, wintypes.HWND,
                                      wintypes.UINT, wintypes.WPARAM,
                                      wintypes.LPARAM]
        u.CallWindowProcW.restype = ctypes.c_ssize_t
        GWLP_WNDPROC = -4
        old = u.GetWindowLongPtrW(hw, GWLP_WNDPROC)

        def _proc(h, msg, wp, lp):
            if msg == WM_GETMINMAXINFO:
                try:
                    mmi = ctypes.cast(lp, ctypes.POINTER(_MINMAXINFO)).contents
                    if mmi.ptMinTrackSize.x < _PANEL_MIN_W:
                        mmi.ptMinTrackSize.x = _PANEL_MIN_W
                    if mmi.ptMinTrackSize.y < _PANEL_MIN_H:
                        mmi.ptMinTrackSize.y = _PANEL_MIN_H
                except Exception:
                    pass
            return u.CallWindowProcW(old, h, msg, wp, lp)

        func = _WNDPROC(_proc)
        u.SetWindowLongPtrW(hw, GWLP_WNDPROC, ctypes.cast(func, ctypes.c_void_p))
        _panel_wndprocs[key] = (old, func)
        log(f"Panel: tamaño mínimo {_PANEL_MIN_W}x{_PANEL_MIN_H} fijado "
            f"(WM_GETMINMAXINFO).")
        return True
    except Exception as e:
        log(f"Panel: no se pudo fijar el tamaño mínimo ({e}).")
        return False


_DOTNET_CONFIG = (
    '<?xml version="1.0" encoding="utf-8"?>\n'
    "<configuration>\n"
    "  <runtime>\n"
    '    <loadFromRemoteSources enabled="true" />\n'
    "  </runtime>\n"
    "</configuration>\n"
)


def ensure_dotnet_config():
    """Deja `<exe>.exe.config` al lado del ejecutable si falta.

    La ventana del panel es pywebview -> pythonnet -> clr_loader, y clr_loader
    carga `Python.Runtime.dll` con `Assembly.LoadFrom`. .NET Framework LANZA
    `NotSupportedException` ("An attempt was made to load an assembly from a
    network location...", HRESULT 0x80131515) cuando el fichero cae en la zona
    Internet/Intranet del sistema — que es lo que pasa con los ficheros del
    bundle y con los que se descomprimen de un ZIP bajado de internet (la
    marca MOTW viaja con el fichero). Sin el interruptor
    `loadFromRemoteSources`, el .exe congelado no podia cargar pythonnet y el
    panel caia al respaldo de Chrome.

    .NET lo lee de `<exe>.exe.config`, AL LADO del ejecutable, antes de
    inicializar el CLR; o sea, antes de que nada importe pywebview aqui. El
    fichero ya viaja creado en dist/ (lo pone dicta.spec), asi que esto solo
    cubre el caso de que falte. Best-effort: si no se puede escribir (carpeta
    de solo lectura) se sigue; el panel usaria el navegador.
    """
    if not _frozen():
        return False
    path = os.path.join(SCRIPT_DIR, os.path.basename(sys.executable) + ".config")
    try:
        if os.path.isfile(path):
            return True
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(_DOTNET_CONFIG)
        log(f"Escrito {os.path.basename(path)} (loadFromRemoteSources, para "
            f"que WebView2 pueda cargar Python.Runtime.dll).")
        return True
    except Exception as e:
        log(f"No se pudo escribir {os.path.basename(path)} ({e}); si WebView2 "
            f"no arranca, el panel se abrira con el navegador.")
        return False


def panel_backend():
    """Backend de la ventana del panel: "webview" (WebView2) o "chrome".

    Clave `panel_backend` de dicta_config.json: webview | chrome | auto.
    «auto» (por defecto) usa pywebview si está instalado y hay runtime de
    WebView2; si no, cae al navegador en modo aplicación, que es como se abría
    antes. Con «webview» forzado se avisa en el log y se cae igualmente si
    falta algo — la app nunca se queda sin panel.
    """
    pref = str(config_get("panel_backend", "auto") or "auto").strip().lower()
    if pref in ("chrome", "edge", "browser", "navegador"):
        return "chrome"
    forzado = pref in ("webview", "webview2", "pywebview")
    try:
        import webview                                  # noqa: F401
    except Exception as e:
        if forzado:
            log(f"panel_backend={pref} pero pywebview no está ({e}); "
                f"el panel se abrirá con Chrome.")
        return "chrome"
    if not _webview2_presente():
        if forzado:
            log(f"panel_backend={pref} pero no hay runtime de WebView2; "
                f"el panel se abrirá con Chrome.")
        return "chrome"
    return "webview"


class PanelJS:
    """API que la barra integrada llama como `pywebview.api.<metodo>()`.

    Métodos expuestos a `panel/desktop.js`: **minimize()**, **restore()**,
    **maximize()** (alterna: maximiza si no lo está), **close()** (cierra la
    ventana del panel; la app sigue viva), **isMaximized()** (para que el botón
    enseñe el icono de lo que hará ahora) y **drag_window()** (arrastre de la
    barra).

    El arrastre: pywebview trae el suyo con la clase `pywebview-drag-region`
    (`webview.DRAG_REGION_SELECTOR`), pero en este montaje su puente
    (`pywebviewMoveWindow`) no mueve la ventana —medido: la llamada llega al
    backend y `window.move()` no hace nada—, así que la barra pide el arrastre
    por aquí (`drag_window`) y lo lleva el bucle clásico de Win32. La clase
    sigue puesta en los mismos elementos como marca de la zona.

    Arrastrar una ventana MAXIMIZADA: al pulsar la barra estando maximizada, el
    backend la RESTAURA a modo ventana y deja el puntero agarrado al MISMO punto
    relativo de la barra (sin saltos), como hacen las aplicaciones normales; a
    partir de ahí sigue el arrastre igual. No hace falta que el panel cambie
    nada: `drag_window()` sigue sin argumentos (el backend lee el cursor con
    `GetCursorPos`).
    """

    def __init__(self, host):
        self._host = host

    def minimize(self):
        return self._host.window_command("minimize")

    def restore(self):
        return self._host.window_command("restore")

    def maximize(self):
        return self._host.window_command("maximize")

    def close(self):
        return self._host.window_command("close")

    def drag_window(self):
        """Arranca el arrastre de la ventana (lo pide la barra al pulsarla)."""
        return self._host.start_drag()

    def resize_window(self, edge):
        """Arranca el REDIMENSIONADO NATIVO por el borde `edge` («left»,
        «right», «top», «bottom» y las cuatro esquinas). Lo pide la barra
        (panel/desktop.js) cuando se pulsa una de sus tiras de borde invisibles;
        ver la nota de `_HIT_EDGE` para por qué no puede hacerse por
        WM_NCHITTEST en esta ventana.
        """
        return self._host.resize_window(edge)

    def isMaximized(self):
        return bool(self._host.maximized)


class WebViewPanelHost:
    """Panel SIN MARCO con WebView2 (pywebview) y barra dibujada en la página.

    Misma interfaz que `PanelHost` (open/close/poll/is_open) para que el resto
    de la app no sepa cuál está detrás. La ventana la crea `main()` antes de
    `webview.start()` (pywebview obliga), así que aquí llega ya creada y solo
    se carga la URL cuando el servidor de control ya tiene puerto.

    Sin barra nativa: `panel/desktop.js` (inyectado al cargar) pinta
    «dicta — Ajustes» y los botones de minimizar/maximizar/cerrar.
    """

    def __init__(self, window=None):
        self.win = window
        self.port = 0
        self.hwnd = 0                 # lo rellena `_own_top_hwnd()`
        self.maximized = False
        self._visible = False
        self._loaded = False
        self._hooked = False
        self._polished = False
        self._dragging = False
        self._resizing = False
        self._quitting = False

    # ---- ciclo de vida (interfaz de PanelHost)
    def set_port(self, port):
        self.port = port

    def url(self):
        return f"http://127.0.0.1:{self.port}/panel"

    def attach_events(self):
        """Engancha la carga (inyección de la barra) y el cierre de la ventana."""
        if self._hooked or self.win is None:
            return
        self._hooked = True
        try:
            self.win.events.loaded += self._on_loaded
            self.win.events.closing += self._on_closing
        except Exception as e:
            log(f"Panel (webview): no se pudieron enganchar los eventos ({e}).")

    def _on_loaded(self):
        """Al cargar la página, inyecta la barra propia (panel/desktop.js)."""
        try:
            self.win.evaluate_js(
                "(function(){if(document.getElementById('dtbar'))return;"
                "var s=document.createElement('script');"
                "s.src='/panel/desktop.js';document.head.appendChild(s);})()")
            log("Panel: barra integrada inyectada (panel/desktop.js).")
        except Exception as e:
            log(f"Panel (webview): no se pudo inyectar la barra ({e}).")
        self._polish_window()

    def _polish_window(self):
        """Redondea las esquinas de la ventana (es del propio proceso).

        La ventana la crea pywebview al arrancar `webview.start()`, así que
        puede no existir todavía: se espera hasta ~10 s por si acaso. Idempotente.
        """
        if self._polished:
            return
        self._polished = True
        if self._hwnd_resuelto():
            _round_window_corners(self.hwnd)
            _install_panel_min_size(self.hwnd)
            _wm_set_icon(self.hwnd, getattr(app, "theme", "light"))
            return

        def work():
            for _ in range(40):                 # ~10 s
                h = _own_top_hwnd()
                if h:
                    self.hwnd = h
                    _round_window_corners(h)
                    _install_panel_min_size(h)
                    # Icono OFICIAL (el de la bandeja) en la ventana/barra de
                    # tareas: el mismo render que la bandeja y la barra.
                    _wm_set_icon(h, getattr(app, "theme", "light"))
                    return
                time.sleep(0.25)
            log("Panel: no se encontró la ventana propia para redondearla.")
        threading.Thread(target=work, daemon=True).start()

    def _hwnd_resuelto(self):
        if not self.hwnd:
            return False
        try:
            return bool(_user32.IsWindow(wintypes.HWND(self.hwnd)))
        except Exception:
            return False

    # ---- arrastre de la barra (js_api.drag_window)
    def start_drag(self):
        """Arrastra la ventana siguiendo al cursor mientras siga pulsado el botón.

        pywebview trae su propio arrastre por `pywebview-drag-region`, pero en
        este montaje su puente (`pywebviewMoveWindow`) no mueve la ventana: la
        llamada llega al backend (comprobado con los eventos del propio
        pywebview) y `window.move()` no cambia la posición. Así que el arrastre
        lo lleva aquí el bucle clásico de Win32: se guardan rectángulo y cursor
        al empezar y, mientras `VK_LBUTTON` siga pulsado, la ventana se coloca
        en rect + (cursor − cursor0).
        """
        if self._dragging:
            return True
        self._dragging = True
        threading.Thread(target=self._drag_loop, daemon=True).start()
        return True

    # ---- redimensionado de los bordes (js_api.resize_window)
    def resize_window(self, edge):
        """Redimensiona la ventana SIGUIENDO al ratón desde el borde `edge`.

        `edge` es «left», «right», «top», «bottom» o una esquina («topleft»,
        «topright», «bottomleft», «bottomright»). Lo pide la barra
        (panel/desktop.js) cuando se pulsa una de sus tiras de borde invisibles.
        El host lleva el bucle él mismo (bucle clásico de Win32, como el de
        ARRASTRE): guarda rectángulo y cursor al empezar y, mientras el botón
        siga pulsado, coloca la ventana moviendo SOLO los lados de ese borde,
        con el mínimo 800x520. Ver la nota de `EDGES` para por qué no vale la vía
        nativa (WM_NCHITTEST no llega al form; WM_NCLBUTTONDOWN/SC_SIZE no
        arranca sin WS_THICKFRAME → medido, no redimensiona).
        """
        e = str(edge).lower()
        if e not in EDGES or self.win is None:
            return False
        if self._resizing:
            return True
        hwnd = self.hwnd if self._hwnd_resuelto() else _own_top_hwnd()
        if not hwnd:
            return False
        self.hwnd = hwnd
        self._resizing = True
        log(f"Panel: redimensionado por «{e}».")
        threading.Thread(target=self._resize_loop, args=(hwnd, e),
                         daemon=True).start()
        return True

    def _resize_loop(self, hwnd, edge):
        """Bucle de redimensionado: mueve los lados del borde `edge` con el ratón.

        Réplica del bucle de ARRASTRE pero cambiando de tamaño: los lados que
        toca `edge` siguen al cursor; los demás se quedan. El ancho/alto nunca
        baja de 800x520 (se recorta por el lado que se arrastra, para que el lado
        fijo no se menee). Una ventana MAXIMIZADA no se redimensiona (se
        restauraría de golpe): para eso está el botón de la barra.
        """
        try:
            hw = wintypes.HWND(hwnd)
            if _user32.IsZoomed(hw):
                return
            _preparar_prototipos_ventana()
            r = wintypes.RECT()
            if not _user32.GetWindowRect(hw, ctypes.byref(r)):
                return
            p0 = _POINT()
            if not _user32.GetCursorPos(ctypes.byref(p0)):
                return
            mv_l = "left" in edge
            mv_r = "right" in edge
            mv_t = "top" in edge
            mv_b = "bottom" in edge
            l0, t0, r0, b0 = r.left, r.top, r.right, r.bottom
            flags = 0x0004 | 0x0010             # NOZORDER | NOACTIVATE
            VK_LBUTTON = 0x01
            while _user32.GetAsyncKeyState(VK_LBUTTON) & 0x8000:
                p = _POINT()
                if not _user32.GetCursorPos(ctypes.byref(p)):
                    break
                dx, dy = p.x - p0.x, p.y - p0.y
                nl, nt, nr, nb = l0, t0, r0, b0
                if mv_l:
                    nl = l0 + dx
                if mv_r:
                    nr = r0 + dx
                if mv_t:
                    nt = t0 + dy
                if mv_b:
                    nb = b0 + dy
                if nr - nl < _PANEL_MIN_W:
                    if mv_l:
                        nl = nr - _PANEL_MIN_W
                    else:
                        nr = nl + _PANEL_MIN_W
                if nb - nt < _PANEL_MIN_H:
                    if mv_t:
                        nt = nb - _PANEL_MIN_H
                    else:
                        nb = nt + _PANEL_MIN_H
                _user32.SetWindowPos(hw, None, nl, nt, nr - nl, nb - nt, flags)
                time.sleep(0.008)
        except Exception as e:
            log(f"Panel: el redimensionado por «{edge}» falló ({e}).")
        finally:
            self._resizing = False

    def _normal_rect(self, hw):
        """Rectángulo que tendrá la ventana al restaurarla (rcNormalPosition)."""
        try:
            wp = _WINDOWPLACEMENT()
            wp.length = ctypes.sizeof(_WINDOWPLACEMENT)
            if not _user32.GetWindowPlacement(hw, ctypes.byref(wp)):
                return None
            n = wp.rcNormalPosition
            if (n.right - n.left) <= 0 or (n.bottom - n.top) <= 0:
                return None
            return n
        except Exception:
            return None

    def _restore_and_anchor(self, hw, r_max, p0):
        """Restaura una ventana MAXIMIZADA y deja el puntero agarrado al mismo
        punto relativo de la barra —como hacen las aplicaciones normales.

        Réplica del gesto de Windows: al pulsar la barra de una ventana
        maximizada y arrastrar, la ventana vuelve a su tamaño de VENTANA y sigue
        al cursor SIN saltos. Para eso se mide el punto del cursor como fracción
        (fx, fy) de la ventana maximizada, se restaura a la geometría normal
        (`rcNormalPosition`) y se coloca de modo que ese mismo punto relativo
        quede bajo el cursor. Devuelve el rectángulo base ya restaurado (el
        origen del arrastre) o None si no se pudo restaurar.

        Usa SW_RESTORE + SetWindowPos (no `win.restore()` de pywebview) porque
        el bucle corre en su propio hilo y aquí ya se tiene el HWND.
        """
        norm = self._normal_rect(hw)
        if norm is None:
            return None
        w_max = max(1, r_max.right - r_max.left)
        h_max = max(1, r_max.bottom - r_max.top)
        fx = (p0.x - r_max.left) / float(w_max)
        fy = (p0.y - r_max.top) / float(h_max)
        fx = 0.0 if fx < 0.0 else (1.0 if fx > 1.0 else fx)
        fy = 0.0 if fy < 0.0 else (1.0 if fy > 1.0 else fy)
        nw = norm.right - norm.left
        nh = norm.bottom - norm.top
        if nw <= 0 or nh <= 0:
            return None
        _user32.ShowWindow(hw, 9)                       # SW_RESTORE
        # Colocada para que el cursor siga sobre el MISMO punto relativo de la
        # barra: nada de saltos. (NOSIZE | NOZORDER | NOACTIVATE)
        left = int(round(p0.x - fx * nw))
        top = int(round(p0.y - fy * nh))
        _user32.SetWindowPos(hw, None, left, top, 0, 0,
                             0x0001 | 0x0004 | 0x0010)
        self.maximized = False
        self._notify_maximize_state(False)
        base = wintypes.RECT()
        base.left, base.top = left, top
        base.right, base.bottom = left + nw, top + nh
        return base

    def _notify_maximize_state(self, is_max):
        """Deja el botón maximizar/restaurar de la barra a juego con la ventana.

        Cuando el arrastre restaura una ventana maximizada, el icono del botón
        (clase `is-max` que pinta `panel/desktop.js`) tiene que volver al de
        «maximizar». Se hace con `evaluate_js` en un hilo aparte para no
        bloquear el bucle de arrastre; si el backend no puede (o el panel no
        está), no pasa nada. No se toca ningún fichero del panel.
        """
        if is_max or self.win is None:
            return
        w = self.win
        js = ("try{var b=document.querySelectorAll('.dtbtn[data-cmd=\"maximize\"]');"
              "for(var i=0;i<b.length;i++)b[i].classList.remove('is-max');}catch(e){}")

        def work():
            try:
                w.evaluate_js(js)
            except Exception:
                pass
        threading.Thread(target=work, daemon=True).start()

    def _drag_loop(self):
        try:
            hwnd = self.hwnd if self._hwnd_resuelto() else _own_top_hwnd()
            if not hwnd:
                return
            _preparar_prototipos_ventana()
            hw = wintypes.HWND(hwnd)
            r = wintypes.RECT()
            if not _user32.GetWindowRect(hw, ctypes.byref(r)):
                return
            p0 = _POINT()
            if not _user32.GetCursorPos(ctypes.byref(p0)):
                return
            # Maximizada: no se puede arrastrar tal cual -> se restaura a modo
            # ventana y se re-ancla el cursor al mismo punto relativo de la
            # barra; a partir de ahí el arrastre sigue igual que en modo normal.
            if _user32.IsZoomed(hw):
                base = self._restore_and_anchor(hw, r, p0)
                if base is None:
                    return                # no se pudo restaurar: no se arrastra
                r = base
            VK_LBUTTON = 0x01
            flags = 0x0001 | 0x0004 | 0x0010    # NOSIZE | NOZORDER | NOACTIVATE
            while _user32.GetAsyncKeyState(VK_LBUTTON) & 0x8000:
                p = _POINT()
                if not _user32.GetCursorPos(ctypes.byref(p)):
                    break
                _user32.SetWindowPos(hw, None,
                                     r.left + p.x - p0.x, r.top + p.y - p0.y,
                                     0, 0, flags)
                time.sleep(0.008)
        except Exception as e:
            log(f"Panel: el arrastre falló ({e}).")
        finally:
            self._dragging = False

    def _on_closing(self):
        """Alt+F4 o «Cerrar» de la barra de tareas: se oculta, no mata dicta."""
        if self._quitting:
            return True          # salida de la app: el cierre sí pasa
        log("Panel: cerrado (queda en la bandeja; no cierra la app).")
        self._visible = False
        try:
            self.win.hide()
        except Exception:
            pass
        return False          # cancela el cierre real: el servicio sigue vivo

    def open(self):
        """Muestra el panel. La URL se carga la primera vez que se abre."""
        w = self.win
        if w is None:
            log("Panel (webview): sin ventana; usa la bandeja.")
            return
        if not self._loaded:
            self._loaded = True
            self.attach_events()
            try:
                w.load_url(self.url())
                self._visible = True
                log(f"Panel abierto (WebView2, sin barra nativa): {self.url()}")
            except Exception as e:
                log(f"Panel (webview): no se pudo cargar {self.url()} ({e}).")
            return
        try:
            w.show()
            self._visible = True
        except Exception as e:
            log(f"Panel (webview): no se pudo mostrar la ventana ({e}).")

    def close(self):
        """Cierra la ventana del panel. La app sigue viva en la bandeja."""
        self.window_command("close")

    def shutdown(self):
        """Cierra la ventana DE VERDAD (al salir de la app)."""
        self._quitting = True        # el veto del cierre ya no aplica
        try:
            if self.win is not None:
                self.win.destroy()
        except Exception:
            pass
        self._visible = False

    def poll(self):
        """El backend de WebView2 conserva la ventana: no hay nada que olvidar."""
        return

    def is_open(self):
        return bool(self._visible)

    # ---- barra integrada: los métodos del js_api acaban aquí
    def window_command(self, cmd):
        w = self.win
        if w is None:
            return False
        try:
            if cmd == "minimize":
                w.minimize()
            elif cmd == "restore":
                w.restore()
                self.maximized = False
            elif cmd == "maximize":
                if self.maximized:
                    w.restore()
                    self.maximized = False
                else:
                    w.maximize()
                    self.maximized = True
            elif cmd == "close":
                w.hide()
                self._visible = False
                log("Panel: ventana cerrada con el botón de la barra.")
            else:
                return False
            return True
        except Exception as e:
            log(f"Panel (webview): acción «{cmd}» no disponible ({e}).")
            return False


def _panel_bg(theme=None):
    """Color de fondo del panel (los mismos tokens --bg de panel/style.css)."""
    t = (theme or app.theme or config_get("theme", "light") or "light").lower()
    return "#141418" if t == "dark" else "#F2F2F5"


_ICON_CACHE = {}                 # (tamaño, tema) -> PNG en memoria


def _panel_icon_png(size, theme=None):
    """PNG del icono REAL de dicta, para la barra del panel.

    Es el MISMO render que el de la bandeja y el del .exe:
    ``dicta_icon.render_icon(size, variant="mark", bg=False)`` —las 5 líneas
    sobre el azulejo **opaco** (blanco puro en tema claro)—, con el mismo tema
    que usa ``make_tray_image`` (tema de la app). Así la barra del panel no
    puede divergir del icono de la bandeja: es literalmente el mismo dibujo.

    ``theme=None`` sigue el tema de la app. El resultado se cachea en memoria
    por (tamaño, tema): la barra se repinta en cada carga y no hay que volver a
    renderizar (el render es PIL a 8x, caro para una petición de icono).
    """
    try:
        size = int(size)
    except (TypeError, ValueError):
        size = 24
    size = max(8, min(256, size))
    if theme is None:
        theme = ("light" if str(getattr(app, "theme", "light")).lower()
                 == "light" else "dark")
    key = (size, theme)
    hit = _ICON_CACHE.get(key)
    if hit is not None:
        return hit
    try:
        import io
        import dicta_icon
        img = dicta_icon.render_icon(size, variant="mark", bg=False,
                                     theme=theme)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        png = buf.getvalue()
    except Exception as exc:                       # noqa: BLE001
        log(f"Panel: no se pudo renderizar el icono ({exc})")
        png = b""
    _ICON_CACHE[key] = png
    return png


_ICON_VERSION_SIZE = 64     # tamano FIJO del render que versionea el icono


def icon_version():
    """Hash corto del PNG del icono (a tamano FIJO) para el cache-busting.

    El panel pide ``GET /panel/icon.png?...&v=<este valor>``: si el dibujo del
    icono cambia (o cambia el tema), el hash cambia y el navegador deja de
    servir el favicon viejo cacheado. Se calcula sobre el PNG ya cacheado en
    memoria (``_ICON_CACHE``), asi que no vuelve a renderizar.
    """
    try:
        import hashlib
        png = _panel_icon_png(_ICON_VERSION_SIZE, None)
        if not png:
            return ""
        return hashlib.sha1(png).hexdigest()[:12]
    except Exception:                       # noqa: BLE001
        return ""


_ICON_ICO_CACHE = {}             # tema -> ruta del .ico OFICIAL
_ICON_ICO_VER = "6"              # versión del dibujo oficial (nombre del .ico)


def _official_icon_ico(theme=None):
    """Ruta de un .ico con EL MISMO dibujo que la bandeja (icono oficial).

    ``dicta_icon.write_ico(theme=...)`` redibuja cada talla con
    ``dicta_icon.official_image`` (las 5 líneas sobre el azulejo opaco: blanco
    puro en claro): el mismo render que la bandeja y la barra del panel. Se
    escribe uno por tema y se cachea; la barra de tareas (WM_SETICON) y el
    parámetro ``icon=`` de WebView2 leen de aquí. Antes se cargaba el
    ``dicta.ico`` estático (tema oscuro): con el tema claro la ventana mostraba
    el icono oscuro mientras la bandeja cambiaba, es decir DOS identidades.

    El nombre lleva ``_ICON_ICO_VER``: el .ico se cachea en disco y solo se
    reescribe si falta, así que SIN la versión en el nombre un cambio de dibujo
    seguiría enseñando el icono viejo en la ventana tras reiniciar.
    """
    theme = ("light" if str(theme or getattr(app, "theme", "light")).lower()
             == "light" else "dark")
    hit = _ICON_ICO_CACHE.get(theme)
    if hit and os.path.isfile(hit):
        return hit
    path = os.path.join(SCRIPT_DIR, ".tmp",
                        f"dicta-icon-{theme}-{_ICON_ICO_VER}.ico")
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        import dicta_icon
        dicta_icon.write_ico(path, theme=theme, variant="mark")
        _ICON_ICO_CACHE[theme] = path
        return path
    except Exception as exc:                          # noqa: BLE001
        log(f"Icono oficial: no se pudo escribir el .ico ({exc})")
        legacy = os.path.join(RESOURCE_DIR, "dicta.ico")
        return legacy if os.path.isfile(legacy) else None


def _wm_set_icon(hwnd, theme=None):
    """WM_SETICON (ICON_SMALL + ICON_BIG) con el icono OFICIAL para ese tema.

    Es literalmente el render de la bandeja puesto a la ventana: la barra de
    tareas y el Alt-Tab muestran el mismo dibujo que la bandeja.
    """
    if not hwnd:
        return False
    ico = _official_icon_ico(theme)
    if not ico or not os.path.isfile(ico):
        return False
    try:
        IMAGE_ICON, LR_LOADFROMFILE = 1, 0x0010
        ok = False
        for which, size in ((0, 16), (1, 32)):       # ICON_SMALL, ICON_BIG
            h = _user32.LoadImageW(None, ico, IMAGE_ICON, size, size,
                                   LR_LOADFROMFILE)
            if h:
                _user32.SendMessageW(int(hwnd), 0x0080, which, h)
                ok = True
        return ok
    except Exception as exc:                          # noqa: BLE001
        log(f"No se pudo poner el icono oficial a la ventana: {exc}")
        return False


def create_webview_panel(webview):
    """Crea la ventana del panel SIN MARCO (WebView2) y devuelve su host.

    pywebview obliga a crear la ventana ANTES de `webview.start()`, pero el
    puerto del panel no se sabe hasta que arranca el servidor de control (que
    vive en Overlay). Así que la ventana nace con una página de relleno del
    color del tema y el host carga la URL de verdad en cuanto la sabe
    (`host.open()`, ya con el servidor en pie).

    Sin barra nativa: el tercer argumento es `frameless=True`; la barra
    (título + minimizar/maximizar/cerrar) la dibuja `panel/desktop.js`, que se
    inyecta al cargar la página.
    """
    bg = _panel_bg()
    relleno = ("<!doctype html><html><head><meta charset=\"utf-8\">"
               f"<title>{PANEL_TITLE}</title><style>html,body{{margin:0;"
               f"height:100%;background:{bg};overflow:hidden}}</style></head>"
               "<body></body></html>")
    host = WebViewPanelHost()
    win = webview.create_window(
        PANEL_TITLE,
        html=relleno,
        js_api=PanelJS(host),
        width=1040, height=820,
        # Tamaño MÍNIMO del diseño: el panel se probó cómodo a 900x600 y
        # 800x520, así que el suelo son 800x520 (antes 720x560, por debajo del
        # ancho que el diseño necesita). Lo refuerza además el manejador de
        # WM_GETMINMAXINFO que instala `_install_panel_min_size`, para que el
        # bucle NATIVO de redimensionado no pueda colapsar el contenido.
        min_size=(800, 520),
        # CLAVE del arreglo: la ventana es SIN MARCO pero SÍ redimensionable.
        # `resizable=True` es el valor por defecto, pero se deja explícito
        # porque el redimensionado de verdad lo aporta el host (ver la nota de
        # `_HIT_EDGE`): la franja del borde la detecta panel/desktop.js y el
        # host arranca el bucle de tamaño nativo de Windows.
        resizable=True,
        frameless=True,            # sin barra de Windows: la pone la página
        # El arrastre lo llevan SOLO los elementos con la clase
        # `pywebview-drag-region` (el título y el hueco vacío de la barra): con
        # easy_drag=True pywebview engancha mousedown en TODA la ventana y
        # arrastrar el ratón por encima del panel (seleccionar texto, mover el
        # deslizador) movería la ventana en vez de hacer lo suyo.
        easy_drag=False,
        # shadow=False quita el filo de 1 px que Windows pinta alrededor de una
        # ventana sin marco (medido: con sombra, la primera fila sale gris
        # oscuro (55,59,63); sin ella, la primera fila es el fondo del panel
        # (242,242,245) de borde a borde). A cambio se pierde la sombra
        # proyectada, que es justo lo que pide el diseño: la forma se delimita
        # con luz, no con borde.
        shadow=False,
        background_color=bg,
        text_select=True,          # el panel tiene campos de texto
    )
    host.win = win
    return host, win


class PanelHost:
    """Abre el panel en una ventana de navegador en modo aplicación (Chrome/Edge).

    Se lanza como proceso separado con su propio perfil para no tocar el
    navegador del usuario. Para ocultarlo basta con cerrar el proceso."""

    BROWSERS = (
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
    )

    def __init__(self, port):
        self.port = port
        self.proc = None
        self.exe = next((b for b in self.BROWSERS if os.path.isfile(b)), None)
        self.profile_dir = os.path.join(SCRIPT_DIR, ".tmp", "panel-profile")
        self.window_title = f"dicta-panel-{os.getpid()}-{id(self):x}"
        self.hwnd = 0
        self.window_pid = 0           # proceso dueño de la ventana del panel
        self.launcher_pid = 0

    def _alive(self):
        return self.proc is not None and self.proc.poll() is None

    def open(self):
        """Muestra el panel. Lo lanza si no está corriendo."""
        hwnd = self.hwnd or _panel_hwnd(self.window_title, self.window_pid)
        if hwnd:
            self.hwnd = hwnd
            _user32.ShowWindow(hwnd, 9)  # SW_RESTORE; also brings back minimized panel
            _user32.SetForegroundWindow(hwnd)
            return
        if self._alive():
            return
        if not self.exe:
            log("No se encontró Chrome ni Edge para el panel; usa la bandeja.")
            return
        restos = _clear_stale_panel(self.profile_dir)
        if restos:
            log(f"Panel: cerrado el navegador de una instancia anterior "
                f"({restos} procesos).")
        profile = self.profile_dir
        os.makedirs(profile, exist_ok=True)
        cmd = [self.exe,
               f"--app=http://127.0.0.1:{self.port}/panel?window={self.window_title}",
               f"--user-data-dir={profile}",
               # El sandbox de Chromium no arranca en entornos de escritorio
               # restringidos (STATUS_BREAKPOINT); el panel solo sirve UI
               # local. --test-type suprime el aviso de "indicador de línea
               # de comandos no admitido" que Chrome muestra con --no-sandbox.
               "--no-sandbox",
               "--test-type",
               "--window-size=1040,820",
               "--no-first-run",
               "--no-default-browser-check",
               "--disable-features=Translate,TranslateUI",
               "--disable-session-crashed-bubble",
               "--hide-crash-restore-bubble"]
        try:
            flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            self.proc = subprocess.Popen(cmd, cwd=SCRIPT_DIR,
                                         stdout=subprocess.DEVNULL,
                                         stderr=subprocess.DEVNULL,
                                         creationflags=flags)
            self.launcher_pid = self.proc.pid
            log("Panel abierto.")
            threading.Thread(target=self._integrate, daemon=True).start()
        except Exception as e:
            log(f"No se pudo abrir el panel: {e}")

    def _integrate(self):
        """Se conserva la barra nativa de Windows (cierra/minimiza/maximiza)."""
        hwnd = 0
        for _ in range(50):                 # ~8 s como mucho
            time.sleep(0.16)
            hwnd = _panel_hwnd(self.window_title)
            if hwnd:
                break
        if hwnd:
            self.hwnd = hwnd
            try:
                owner = wintypes.DWORD()
                _user32.GetWindowThreadProcessId(hwnd, ctypes.byref(owner))
                self.window_pid = owner.value
            except Exception:
                self.window_pid = 0
            self._set_window_icon(hwnd)
            # La barra de Windows no se pinta desde aquí: la ventana es de
            # Chrome y DwmSetWindowAttribute falla con E_HANDLE desde otro
            # proceso (comprobado). Chrome la dibuja según el `color-scheme` y
            # el <meta name="theme-color"> de la página del panel.
            # El título único solo sirve para LOCALIZAR la ventana: en la barra
            # de tareas tiene que leerse «dicta — Ajustes», no
            # "dicta-panel-1234-7f3a".
            # Chrome lo pisa con el de la página al acabar de cargar, así que
            # hay que volver a aplicarlo hasta que la ventana se asiente.
            for _ in range(30):                 # ~15 s
                try:
                    if not _user32.IsWindow(int(hwnd)):
                        break
                    t = ctypes.create_unicode_buffer(160)
                    _user32.GetWindowTextW(int(hwnd), t, len(t))
                    if t.value != PANEL_TITLE:
                        _user32.SetWindowTextW(int(hwnd), PANEL_TITLE)
                except Exception:
                    break
                time.sleep(0.5)
            log("Panel: ventana con barra nativa de Windows.")

    def _set_window_icon(self, hwnd: int):
        """Pone el icono OFICIAL (el de la bandeja) a la ventana del panel."""
        self._icon_hwnd = hwnd
        _wm_set_icon(hwnd, getattr(app, "theme", "light"))

    def close(self):
        # Cierra primero el HWND exacto del panel, por su título de instancia.
        hwnd = self.hwnd or _panel_hwnd(self.window_title, self.window_pid)
        if hwnd:
            _user32.PostMessageW(int(hwnd), 0x0010, 0, 0)  # WM_CLOSE
            time.sleep(0.15)
        # Si el lanzador aún conserva el proceso, limpiar solo su árbol.
        if self.launcher_pid:
            try:
                subprocess.run(["taskkill", "/PID", str(self.launcher_pid), "/T", "/F"],
                               capture_output=True, timeout=8,
                               creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            except Exception:
                pass
        if self._alive():
            try:
                self.proc.kill()
            except Exception:
                pass
        self.proc = None
        self.hwnd = 0
        self.launcher_pid = 0

    def shutdown(self):
        """Al salir de la app: cierra el panel y mata el navegador.

        Mismo efecto que ``close()``; existe para que el cierre limpio llame a
        lo mismo con cualquier backend (WebView2 usa shutdown() para destruir
        la ventana en vez de ocultarla).
        """
        self.close()

    def poll(self):
        """Si el usuario cerró la ventana del panel, se olvida el estado."""
        if not self.is_open():
            self.proc = None
            self.hwnd = 0
            self.launcher_pid = 0

    def is_open(self):
        """True si sigue viva la ventana con el título único del panel."""
        if self.hwnd and _user32.IsWindow(self.hwnd):
            return True
        self.hwnd = _panel_hwnd(self.window_title, self.window_pid)
        return bool(self.hwnd) or self._alive()


class App:
    """Estado global de la app (atributos planos, GIL basta)."""

    def __init__(self):
        self.state = "idle"        # idle | recording | transcribing
        self.rms = 0.0
        self.thr = MIN_RMS
        self.noise = None
        self.last_voice = 0.0
        self.mic_error = ""
        self.txt = ""              # último texto dictado
        self.status = "Cargando modelo…"
        self.status_color = "#888"
        self.sens = float(config_get("sens", 1.0))
        self.voice_threshold = float(
            config_get("voice_threshold", VOICE_THRESHOLD_DEFAULT))
        self.silence_wait = float(
            config_get("silence_wait", SILENCE_TIMEOUT))
        # Combinacion de pegado: `auto` detecta la ventana (Ctrl+V normal,
        # Ctrl+Shift+V en terminales); el resto la fuerza (valvula de escape).
        self.paste_mode = str(
            config_get("paste_mode", "auto") or "auto").strip().lower()
        if self.paste_mode not in PASTE_MODES:
            self.paste_mode = "auto"
        self.language = config_get("language", "es")
        self.prompt = config_get("prompt", "")
        self.dictionary = config_get("dictionary", []) or []
        self.hotkey_label = "alt+q"
        self.cancel_key_label = ""          # atajo de cancelar (config al arrancar)
        self.panel_key_label = "ctrl+alt+p"  # atajo para abrir el panel
        self.meeting_key_label = "ctrl+alt+r"  # atajo iniciar/parar reunion
        self.meeting_stop_key_label = "ctrl+alt+s"  # atajo detener (guardar)
        self.panel_request = False           # lo pone el atajo; lo aplica Tk
        self.mode = "toggle"
        self.model = ""
        self.last_fire = 0.0
        self.hotkey_fired = 0
        self.target_hwnd = 0       # ventana con foco al empezar a dictar
        self.target_title = ""
        self.current_transcript = ""
        self.wave_data = (0.0,) * 160
        self.gen = 0               # generación de la sesión: anula huérfanos
        self.theme = config_get("theme", "light")   # claro por defecto
        self.island_pos = config_get("island_pos", "top")       # top | bottom
        self.island_palette = config_get("island_palette", "grafito")
        self.engine = config_get("engine", "auto")   # auto|vulkan|cuda|cpu
        self.engine_resolved = ""                     # motor efectivo
        self.engine_note = ""                         # aviso motor no disponible
        # QUE GPU concreta usa el motor: 'auto' (dispositivo 0 del motor, la
        # dedicada) o {'index': N}. En este equipo hay dos GPU Vulkan (una
        # dedicada y una integrada) y el autor quiere poder elegir cual.
        self.gpu_device = config_get("gpu_device", "auto")
        self.gpu_device_resolved = "auto"             # indice efectivo o 'auto'
        self.gpu_device_note = ""                     # aviso del dispositivo
        self.results = queue.SimpleQueue()
        self.hotkey_events = queue.SimpleQueue()
        self.delivery_results = queue.SimpleQueue()
        self.dismiss_overlay = False  # la isla se va al instante
        self.cancel_until = 0.0       # fin del cierre visual de cancelación


app = App()
_audio_queue = TranscribeQueue()
_uploads = UploadStore()          # audios subidos por el autor (persistentes)
_audio_queue.on_change = _uploads.apply_queue_update
_meeting = MeetingTranscriber()


def queue_for_state():
    """Lo que se publica en ``/state.queue``: la cola real MAS las referencias
    de audio de las subidas ya resueltas (reconstruidas desde el manifiesto).

    La cola es de la SESION; sin esta union, tras reiniciar el panel perdia el
    reproductor de un audio subido ya transcrito (su audio solo vivia en
    ``queue[].src``). No altera la cola de transcripcion en si.
    """
    live = _audio_queue.snapshot()
    return live + _uploads.audio_entries([q.get("key") for q in live])

_mic = None                    # lo fija main(); el cierre limpio lo para
_crash_log_file = None


# ------------------------------------------------------------- dictado
def start_recording(mic: Mic):
    mic._chunks, mic._buf_dur = [], 0.0
    app.current_transcript = ""
    app.wave_data = (0.0,) * 160
    app.state = "recording"
    app.gen += 1                       # invalida resultados de sesiones viejas
    app.status, app.status_color = "Escuchando…", "#4caf50"
    app.last_voice = time.monotonic()
    app.target_hwnd = _user32.GetForegroundWindow()
    app.target_title = _fg_title()
    log(f"ESCUCHANDO (sens {mic.sens:.1f}) — destino: {app.target_title or '(sin título)'}")
    if _es_ventana_propia(app.target_hwnd):
        log("(El destino es una ventana de dicta; se pegará en la que mires al "
            "terminar.)")


def cancel_recording(mic: Mic):
    """Descarta lo dictado (atajo de cancelar) y muestra un cierre visual."""
    if app.state == "idle":
        return
    app.gen += 1                       # el resultado en vuelo queda huérfano
    mic._chunks, mic._buf_dur = [], 0.0
    app.current_transcript = ""
    app.wave_data = (0.0,) * 160
    app.state = "cancelled"            # la isla colapsa y se apaga
    app.cancel_until = time.monotonic() + 0.45
    app.status, app.status_color = "Cancelado", "#e5606b"
    log("Dictado cancelado.")


def finish_recording(mic: Mic):
    if app.state != "recording":
        return
    app.state = "transcribing"
    app.status, app.status_color = "Transcribiendo…", "#ffb74d"
    audio, dur = mic.take_audio()
    model_file = MODELS.get(app.model or "small", MODELS["small"])
    gen = app.gen
    log(f"Transcribiendo {dur:.1f}s…")

    def work():
        try:
            t0 = time.monotonic()
            text = ""
            if dur >= MIN_DURATION:
                text = transcribe(audio, ensure_model(model_file),
                                  app.language, app.prompt)
            dt = time.monotonic() - t0
            if text and text.lower() in ARTIFACTS and len(text.split()) <= 3:
                text = ""
            app.results.put((gen, text, dt, ""))
        except Exception as e:
            app.results.put((gen, "", 0.0, str(e)))

    threading.Thread(target=work, daemon=True).start()


def app_status_ready():
    return "Listo para escuchar"


# ------------------------------------------------- (vista previa retirada)
# Se probó streaming en vivo (sliding window + LocalAgreement-2) pero el texto
# parcial de Whisper inventa/cambia palabras, así que mostramos solo la
# animación mientras hablas y escribimos el texto completo al terminar.


def preview_text() -> str:
    """Sin vista previa en vivo: el overlay no muestra palabras durante el
    dictado, solo la animación de estado."""
    return ""


# -------------------------------------------------------------- hotkeys
VK = {"alt": 0x12, "ctrl": 0x11, "shift": 0x10, "cmd": 0x5B}
MOD_FLAGS = {"alt": 0x1, "ctrl": 0x2, "shift": 0x4, "cmd": 0x8}


def list_input_devices():
    """Devuelve [(índice_real, nombre)] de las entradas de audio.

    El índice es el de PortAudio (``sd.query_devices``), que es el que hay que
    pasar a ``sd.InputStream``: la posición dentro de esta lista NO sirve como
    índice de dispositivo."""
    out = []
    try:
        for i, d in enumerate(sd.query_devices()):
            if d.get("max_input_channels", 0) > 0:
                out.append((i, str(d.get("name", f"Entrada {i}")).strip()))
    except Exception as e:
        log(f"No se pudieron listar micrófonos: {e}")
    return out


def hotkey_pump_toggle(spec: str, stop: threading.Event,
                       ready: threading.Event, result: dict,
                       hk_id: int = _HOTKEY_ID, event: str = "toggle"):
    """Registra y lee WM_HOTKEY en EL MISMO hilo (requisito de Windows).

    RegisterHotKey(hwnd=None) entrega WM_HOTKEY a la cola del hilo que hizo
    el registro; separar registro y PeekMessage hacía que Alt+Q nunca llegara
    al bucle lector."""
    mods, main = parse_hotkey(spec)
    vk = main_vk(main)
    if vk is None:
        result.update(ok=False, error="invalid")
        ready.set()
        return

    flags = 0x4000  # MOD_NOREPEAT
    for mod in mods:
        flags |= MOD_FLAGS[mod]

    # Crear la cola de mensajes ANTES de registrar el hotkey.
    msg = _MSG()
    _PeekMessageW(ctypes.byref(msg), None, 0, 0, 0)  # PM_NOREMOVE
    if not _RegisterHotKey(None, hk_id, flags, vk):
        error = int(_kernel32.GetLastError())
        result.update(ok=False, error="unavailable", winerror=error)
        ready.set()
        log(f"No se pudo registrar {spec} (error {error}); prueba otra combinación.")
        return

    result.update(ok=True, error="")
    ready.set()
    log(f"Hotkey global {spec} registrada.")
    try:
        while not stop.is_set():
            if _PeekMessageW(ctypes.byref(msg), None, 0, 0, _PM_REMOVE):
                if msg.message == _WM_HOTKEY and msg.wParam == hk_id:
                    app.hotkey_events.put(event)
            else:
                stop.wait(0.01)
    finally:
        _UnregisterHotKey(None, hk_id)


def hotkey_poll_hold(spec: str, stop: threading.Event,
                     ready: threading.Event, result: dict):
    """Hold listener queues edge events; state transitions stay on Tk thread."""
    mods, main = parse_hotkey(spec)
    vk = main_vk(main)
    if vk is None:
        result.update(ok=False, error="invalid")
        ready.set()
        return

    def combo_down():
        for mod in mods:
            if not (_GetAsyncKeyState(VK[mod]) & 0x8000):
                return False
        return bool(_GetAsyncKeyState(vk) & 0x8000)

    result.update(ok=True, error="")
    ready.set()
    log(f"Hotkey {spec} (hold) lista.")
    down_old = False
    while not stop.is_set():
        stop.wait(0.015)
        down = combo_down()
        if down and not down_old:
            app.hotkey_events.put("down")
        elif not down and down_old:
            app.hotkey_events.put("up")
        down_old = down


class HotkeyManager:
    """Registra el atajo y permite cambiarlo en caliente."""

    def __init__(self, mode, hk_id=None, event="toggle", label_attr=None):
        self.mode = mode
        self.hk_id = hk_id or _HOTKEY_ID
        self.event = event
        self.label_attr = label_attr        # atributo de App que refleja el atajo
        self.stop = None
        self.thread = None
        self.spec = None
        self.last_error = ""

    def apply(self, spec):
        """Cambia en caliente. Devuelve False y restaura el anterior si falla."""
        norm, err = validate_hotkey(spec or "")
        if err:
            self.last_error = err
            log(f"Atajo no válido: '{spec}' ({err})")
            return False
        spec = norm
        if spec == self.spec and self.thread is not None and self.thread.is_alive():
            self.last_error = ""
            return True
        old_spec = self.spec
        self.release()
        if self._start(spec):
            self.spec = spec
            if self.label_attr:
                setattr(app, self.label_attr, spec)
            self.last_error = ""
            return True

        self.last_error = self.last_error or "unavailable"
        if old_spec and self._start(old_spec):
            self.spec = old_spec
            if self.label_attr:
                setattr(app, self.label_attr, old_spec)
        elif old_spec:
            self.spec = None
            if self.label_attr:
                setattr(app, self.label_attr, "")
        return False

    def _start(self, spec):
        stop = threading.Event()
        ready = threading.Event()
        result = {}
        target = hotkey_poll_hold if self.mode == "hold" else hotkey_pump_toggle
        if target is hotkey_pump_toggle:
            args = (spec, stop, ready, result, self.hk_id, self.event)
        else:
            args = (spec, stop, ready, result)
        thread = threading.Thread(target=target, args=args,
                                  daemon=True,
                                  name=f"dicta-hotkey-{self.hk_id}")
        thread.start()
        if not ready.wait(2.0):
            stop.set()
            thread.join(timeout=0.5)
            self.last_error = "timeout"
            return False
        if not result.get("ok"):
            stop.set()
            thread.join(timeout=0.5)
            self.last_error = result.get("error", "unavailable")
            return False
        self.stop, self.thread = stop, thread
        if self.label_attr:
            setattr(app, self.label_attr, spec)
        return True

    def release(self):
        if self.stop is not None:
            self.stop.set()
        if self.thread is not None:
            self.thread.join(timeout=1.0)
        self.stop = None
        self.thread = None
        self.spec = None


_hotkeys = HotkeyManager("toggle", label_attr="hotkey_label")
_CANCEL_KEY_ID = 47125
_cancel = HotkeyManager("toggle", hk_id=_CANCEL_KEY_ID,
                        event="cancel", label_attr="cancel_key_label")
# Tercer atajo: abrir el panel. dicta no tiene ventana propia y el icono de
# bandeja puede quedar escondido por Windows, asi que hace falta una puerta de
# entrada que no dependa de ver el icono.
_PANEL_KEY_ID = 47126
_panelshot = HotkeyManager("toggle", hk_id=_PANEL_KEY_ID, event="panel",
                           label_attr="panel_key_label")
# Cuarto atajo: modo REUNION (iniciar/parar) sin abrir la app.
_MEETING_KEY_ID = 47127
_meetingshot = HotkeyManager("toggle", hk_id=_MEETING_KEY_ID, event="meeting",
                             label_attr="meeting_key_label")
# Quinto atajo: DETENER (guardar) la reunion sin pasar por iniciar/parar.
_MEETING_STOP_KEY_ID = 47128
_meetingstop = HotkeyManager("toggle", hk_id=_MEETING_STOP_KEY_ID,
                             event="meeting_stop",
                             label_attr="meeting_stop_key_label")


def _toggle_meeting():
    """Inicia/para el modo reunion. Lo usan el atajo global y el panel.

    Se ejecuta en su propio hilo: ``_meeting.stop()`` une el hilo mezclador
    (hasta 20 s) y no puede bloquear el hilo de Tk que reparte los atajos."""
    try:
        if _meeting.active:
            _meeting.stop()
            log("Reunion: parada por el atajo global.")
        else:
            ok = _meeting.start()
            log(f"Reunion: inicio por el atajo global ({'ok' if ok else 'no'}).")
    except Exception as e:
        log(f"Reunion (atajo): {type(e).__name__}: {e!r}")


def _stop_meeting():
    """Detiene (guarda) la reunion con el atajo dedicado, sin iniciarla.

    Idempotente: si no hay reunion activa no hace nada. En su propio hilo
    porque ``_meeting.stop()`` une el hilo mezclador (hasta 20 s)."""
    try:
        if _meeting.active:
            _meeting.stop()
            log("Reunion: parada por el atajo dedicado.")
        else:
            log("Reunion: atajo de parada sin reunion activa (nada que hacer).")
    except Exception as e:
        log(f"Reunion (parada): {type(e).__name__}: {e!r}")


def main_vk(key):
    """Código de tecla virtual (VK) para la tecla principal del atajo.
    Acepta a-z, 0-9, f1-f24, space, tab y por nombre alguna más."""
    if not key:
        return None
    k = key.lower()
    if len(k) == 1 and k.isalnum():
        return ord(k.upper())
    if k.startswith("f") and k[1:].isdigit():
        n = int(k[1:])
        if 1 <= n <= 24:
            return 0x70 + (n - 1)          # VK_F1 = 0x70
    return {"space": 0x20, "tab": 0x09, "enter": 0x0D, "backspace": 0x08,
            "insert": 0x2D, "delete": 0x2E, "home": 0x24, "end": 0x23,
            "pageup": 0x21, "pagedown": 0x22,
            "left": 0x25, "up": 0x26, "right": 0x27, "down": 0x28}.get(k)


def parse_hotkey(spec):
    mods, main = [], None
    for p in (x.strip().lower() for x in spec.split("+")):
        if p in ("ctrl", "control"):
            mods.append("ctrl")
        elif p in ("alt", "shift", "cmd", "win"):
            mods.append("cmd" if p == "win" else p)
        elif p:
            main = p
    return mods, main


MOD_ORDER = ("ctrl", "alt", "shift", "cmd")


def validate_hotkey(spec):
    """Valida/normaliza un atajo de 1, 2 o 3 teclas simultaneas.

    Devuelve ``(normalizado, "")`` si es valido o ``(None, motivo)``.
    Reglas: 1..3 teclas; UNA sola tecla principal; modificadores
    distintos (ctrl/alt/shift/cmd); sin partes vacias."""
    raw = str(spec or "").strip()
    if not raw:
        return None, "empty"
    parts = [p.strip().lower() for p in raw.split("+")]
    if any(not p for p in parts):
        return None, "empty part"
    if len(parts) > 3:
        return None, "too many keys (max 3)"
    mods, main = [], None
    for p in parts:
        if p in ("ctrl", "control", "alt", "shift", "cmd", "win"):
            m = {"control": "ctrl", "win": "cmd"}.get(p, p)
            if m in mods:
                return None, "duplicate modifier: " + m
            mods.append(m)
        elif main_vk(p) is not None:
            if main is not None:
                return None, "only one main key allowed"
            main = p
        else:
            return None, "unknown key: " + p
    if main is None:
        return None, "missing main key"
    ordered = [m for m in MOD_ORDER if m in mods]
    return "+".join(ordered + [main]), ""


def hotkey_spec_error(code):
    """Mensaje legible (panel) a partir del motivo de validate_hotkey."""
    if code.startswith("unknown key"):
        return "Tecla no valida: " + code.split(":")[-1].strip()
    if code.startswith("duplicate modifier"):
        return "Modificador repetido: " + code.split(":")[-1].strip()
    return {"empty": "El atajo no puede estar vacio",
            "empty part": "Hay una tecla vacia (sobra un +)",
            "too many keys (max 3)": "Como maximo 3 teclas simultaneas",
            "only one main key allowed": "Solo una tecla principal",
            "missing main key": "Falta la tecla principal"}.get(code, code)


def service_app(mic: Mic, mode: str):
    """Process hotkey, VAD and ASR results on the main thread only."""
    _recordar_destino()
    if app.state == "cancelled" and time.monotonic() >= app.cancel_until:
        app.state = "idle"
        app.dismiss_overlay = True     # cierra la isla al terminar el barrido
        app.status, app.status_color = app_status_ready(), "#888"
    while True:
        try:
            event = app.hotkey_events.get_nowait()
        except queue.Empty:
            break
        app.hotkey_fired += 1
        if event == "panel":
            # Se encola para el hilo de Tk (aqui no se toca la ventana).
            app.panel_request = True
            continue
        if event == "meeting":
            # Iniciar/parar la reunion sin abrir la app (atajo global).
            threading.Thread(target=_toggle_meeting, daemon=True).start()
            continue
        if event == "meeting_stop":
            # Detener (guardar) la reunion con su atajo dedicado.
            threading.Thread(target=_stop_meeting, daemon=True).start()
            continue
        if mode == "toggle" and event == "toggle":
            if app.state == "idle":
                start_recording(mic)
            elif app.state == "recording":
                finish_recording(mic)
        elif event == "cancel":
            cancel_recording(mic)
        elif mode == "hold":
            if event == "down" and app.state == "idle":
                start_recording(mic)
            elif event == "up" and app.state == "recording":
                finish_recording(mic)

    if (mode == "toggle" and app.state == "recording" and app.last_voice
            and time.monotonic() - app.last_voice >= getattr(app, "silence_wait",
                                                             SILENCE_TIMEOUT)):
        finish_recording(mic)

    while True:
        try:
            gen, text, elapsed, error = app.results.get_nowait()
        except queue.Empty:
            break
        if gen != app.gen:          # sesión cancelada; resultado huérfano
            continue
        if error:
            app.state = "idle"
            log(f"Error de transcripción: {error}")
            app.status, app.status_color = f"⚠ Error — {error}", "#e53935"
            continue
        if not text:
            app.state = "idle"
            log(f"(audio vacío o artificio, {elapsed:.1f}s)")
            app.status, app.status_color = app_status_ready(), "#888"
            continue
        app.txt = text
        app.current_transcript = text
        app.status, app.status_color = "Transcripción lista", "#0a8"
        log(f"Texto ({elapsed:.1f}s): {text}")
        start_delivery(text, app.target_hwnd, app.target_title)

    while True:
        try:
            success, detail, target_hwnd = app.delivery_results.get_nowait()
        except queue.Empty:
            break
        if success:
            log("Texto insertado automáticamente en el campo.")
            app.status, app.status_color = "Texto insertado", "#4caf50"
            app.dismiss_overlay = True    # la isla se va al pegar
        else:
            if detail:
                log(f"UI Automation no disponible: {detail}")
            texto = getattr(app, "current_transcript", "") or ""
            if fallback_paste(target_hwnd, texto):
                app.dismiss_overlay = True  # pegado manual/enviado: se va igual
        app.state = "idle"


# ------------------------------------------------------------------ GUI
class Overlay:
    """Compone bandeja del sistema + overlay flotante + panel de ajustes.
    El hilo de Tk es el único que toca la UI; los eventos del tray se encolan."""

    def __init__(self, mic: Mic, panel=None):
        import dicta_ui
        self.ui = dicta_ui
        self.mic = mic
        self.root = tk.Tk()
        self.root.withdraw()                    # sin ventana principal visible
        self.root.title("dicta")
        self.ui_events = queue.SimpleQueue()    # eventos del tray -> Tk
        self._last_state = ("idle", False)
        self._overlay_auto_hide = None

        self.overlay = dicta_ui.VoiceOverlay(self.root)
        dicta_ui.set_theme(app.theme)          # isla + tarjeta en el tema fijo
        dicta_ui.set_position(app.island_pos)  # arriba / abajo
        dicta_ui.set_palette(app.island_palette)
        self.tray = dicta_ui.Tray(on_event=self._tray_event,
                                  snapshot=self._tray_snapshot)

        # El panel de ajustes es una ventana propia: WebView2 (pywebview, sin
        # marco y con barra en la página) o el navegador en modo aplicación.
        # La elige main() y llega ya creada; si no, se usa el navegador.
        self.control = ControlServer(PANEL_PORT, self.panel_state,
                                     self._panel_rpc)
        self.control.start()
        self.panel = panel if panel is not None else PanelHost(self.control.port)
        if hasattr(self.panel, "set_port"):
            self.panel.set_port(self.control.port)   # el mismo puerto real
        # Se publica para el carril de entrega (no pegar nunca dentro del
        # panel): el Overlay es local de main() y desde una función de módulo
        # no se alcanza.
        global _panel_host, _control_ref
        _panel_host = self.panel
        _control_ref = self.control          # lo usa apply_update() para cerrar
        atexit.register(self.panel.close)

    # ---- configuración (mismos setters que antes)
    def on_mic(self, idx):
        try:
            self.mic.start(idx)
            config_set("mic", idx)
        except Exception:
            pass

    def on_model(self, name):
        app.model = name
        config_set("model", name)
        log(f"Modelo seleccionado: {name}")

    def on_sens(self, value):
        try:
            app.sens = float(value)
            self.mic.sens = app.sens
            config_set("sens", app.sens)
        except Exception:
            pass

    def on_voice_threshold(self, value):
        """Umbral de voz 0..1 (RMS minimo): por debajo es silencio."""
        try:
            v = float(value)
        except (TypeError, ValueError):
            return
        app.voice_threshold = min(1.0, max(0.0, v))
        config_set("voice_threshold", app.voice_threshold)
        log(f"Umbral de voz: {app.voice_threshold:.4f}")

    def on_silence_wait(self, value):
        """Pausa (s) antes de cerrar el dictado: 0.2..600, sin tope real."""
        try:
            v = float(value)
        except (TypeError, ValueError):
            return
        app.silence_wait = min(SILENCE_WAIT_MAX, max(SILENCE_WAIT_MIN, v))
        config_set("silence_wait", app.silence_wait)
        log(f"Espera antes de transcribir: {app.silence_wait:.2f} s")

    def on_paste_mode(self, value):
        """Fuerza (o deja en auto) la combinacion del pegado automatico.

        `auto` detecta la ventana destino en cada pegado; `ctrl+v`,
        `ctrl+shift+v`, `shift+insert` y `type` la fuerzan: es la valvula de
        escape para una terminal que se resista a la deteccion (`type` teclea el
        texto como entrada real, sin depender de la combinacion ni del
        portapapeles). Persiste en dicta_config.json y se publica en /state.
        """
        v = str(value or "auto").strip().lower()
        if v not in PASTE_MODES:
            return {"ok": False, "error": "modo invalido",
                    "paste_mode": getattr(app, "paste_mode", "auto")}
        app.paste_mode = v
        config_set("paste_mode", v)
        log(f"Modo de pegado forzado: {v}")
        return {"ok": True, "paste_mode": v}

    def on_check_updates(self, value):
        """Enciende/apaga la comprobacion de version (ajuste `check_updates`).

        ACTIVADA de fabrica. Mientras lo este, lo UNICO que sale a la red es una
        peticion GET anonima a la API publica de GitHub (sin ningun dato del
        usuario). Al activarla se lanza una comprobacion en segundo plano (para
        no bloquear el hilo HTTP) y el resultado se sigue en /state.update. Al
        apagarla se limpia el estado y se deja de tocar la red. El ajuste
        PERSISTE en dicta_config.json igual que los demas (config_set).
        """
        enabled = bool(value) if not isinstance(value, str) \
            else value.strip().lower() in ("1", "true", "on", "si", "sí", "yes")
        config_set("check_updates", enabled)
        log(f"Comprobacion de actualizaciones: {'activada' if enabled else 'desactivada'}")
        if enabled:
            threading.Thread(target=check_update, daemon=True).start()
        else:
            _update_blank("", enabled=False)
        return {"ok": True, "check_updates": enabled,
                "update": dict(UPDATE_STATE)}

    def on_theme(self, name):
        app.theme = "light" if name == "light" else "dark"
        config_set("theme", app.theme)
        log(f"Tema: {app.theme}")
        try:
            import dicta_ui
            dicta_ui.set_theme(app.theme)     # isla + tarjeta de transcripción
            if self.overlay:
                self.overlay.refresh_theme()
            # La BANDEJA también redibuja su icono con el tema nuevo: sin esto,
            # la bandeja quedaba con el dibujo viejo y la barra de tareas con el
            # nuevo (dos identidades). `icon.icon` es el PIL que usa pystray.
            icon = getattr(self.tray, "icon", None)
            if icon is not None:
                icon.icon = dicta_ui.make_tray_image()
        except Exception:
            pass
        # El icono OFICIAL de la ventana (WM_SETICON) sigue el mismo tema que la
        # bandeja: mismo render, sin reimportar el .ico estático.
        try:
            hwnd = getattr(self.panel, "hwnd", 0)
            if hwnd:
                _wm_set_icon(hwnd, app.theme)
        except Exception:
            pass
        self.tray.refresh()

    def on_island_pos(self, name):
        """Posición de la isla (arriba/abajo): aplica en caliente y persiste."""
        name = "bottom" if str(name or "").strip().lower() == "bottom" else "top"
        app.island_pos = name
        config_set("island_pos", name)
        log(f"Isla: {name}")
        try:
            self.ui.set_position(name)
            if self.overlay:
                self.overlay.apply_position()
        except Exception:
            pass

    def on_island_palette(self, name):
        """Paleta de la isla: aplica en caliente y persiste."""
        name = str(name or "").strip().lower() or "grafito"
        if name not in self.ui.PALETTES:
            name = "grafito"
        app.island_palette = name
        config_set("island_palette", name)
        log(f"Paleta de la isla: {name}")
        try:
            self.ui.set_palette(name)
            if self.overlay:
                self.overlay.refresh_palette()
        except Exception:
            pass

    def on_cancel_key(self, spec):
        """Aplica el atajo de cancelar en caliente y lo persiste."""
        spec = "+".join(part.strip().lower() for part in str(spec or "").split("+"))
        if not _cancel.apply(spec):
            return {"ok": False, "error": _cancel.last_error or "unavailable",
                    "cancel_key": app.cancel_key_label}
        config_set("cancel_key", app.cancel_key_label)
        log(f"Atajo de cancelar: {app.cancel_key_label}")
        return {"ok": True, "cancel_key": app.cancel_key_label}

    def on_panel_key(self, spec):
        """Aplica y persiste el atajo que abre el panel."""
        spec = "+".join(part.strip().lower()
                        for part in str(spec or "").split("+"))
        if not _panelshot.apply(spec):
            return {"ok": False,
                    "error": _panelshot.last_error or "unavailable",
                    "panel_key": app.panel_key_label}
        config_set("panel_key", app.panel_key_label)
        log(f"Atajo del panel: {app.panel_key_label}")
        return {"ok": True, "panel_key": app.panel_key_label}

    def on_meeting_key(self, spec):
        """Aplica y persiste el atajo que inicia/para el modo reunion."""
        spec = "+".join(part.strip().lower()
                        for part in str(spec or "").split("+"))
        if not _meetingshot.apply(spec):
            return {"ok": False,
                    "error": _meetingshot.last_error or "unavailable",
                    "meeting_key": app.meeting_key_label}
        config_set("meeting_key", app.meeting_key_label)
        log(f"Atajo de reunion: {app.meeting_key_label}")
        return {"ok": True, "meeting_key": app.meeting_key_label}

    def on_meeting_stop_key(self, spec):
        """Aplica y persiste el atajo que detiene (guarda) la reunion."""
        spec = "+".join(part.strip().lower()
                        for part in str(spec or "").split("+"))
        if not _meetingstop.apply(spec):
            return {"ok": False,
                    "error": _meetingstop.last_error or "unavailable",
                    "meeting_stop_key": app.meeting_stop_key_label}
        config_set("meeting_stop_key", app.meeting_stop_key_label)
        log(f"Atajo de parada de reunion: {app.meeting_stop_key_label}")
        return {"ok": True, "meeting_stop_key": app.meeting_stop_key_label}

    def on_language(self, code):
        # El idioma viaja en cada petición al servidor, así que no hace falta
        # reiniciarlo: el cambio surte efecto en el siguiente dictado.
        app.language = code
        config_set("language", code)
        log(f"Idioma: {code}")

    def on_dictionary(self, value):
        """Diccionario de transcripcion (initial_prompt de Whisper).

        Acepta una LISTA o un TEXTO con las palabras separadas por coma,
        punto y coma o salto de linea: carga en lote."""
        if isinstance(value, str):
            raw = (value.replace("\r", "\n").replace("\n", ",")
                   .replace(";", ",").split(","))
        else:
            raw = []
            for item in (value or []):
                raw.extend(str(item).replace("\r", "\n")
                           .replace("\n", ",").replace(";", ",").split(","))
        words, seen = [], set()
        for w in raw:
            w = w.strip()
            if w and w.lower() not in seen:
                seen.add(w.lower())
                words.append(w)
        app.dictionary = words
        app.prompt = ", ".join(words)
        config_set("dictionary", words)
        log(f"Diccionario: {len(words)} palabras ({chr(44).join(words)})")

    def on_hotkey(self, spec):
        """Aplica y persiste el atajo; no confirma si Windows lo rechazó."""
        spec = "+".join(part.strip().lower() for part in str(spec or "").split("+"))
        if not _hotkeys.apply(spec):
            error = _hotkeys.last_error or "unavailable"
            return {"ok": False, "error": error, "hotkey": app.hotkey_label}
        config_set("hotkey", app.hotkey_label)
        log(f"Atajo actualizado: {app.hotkey_label}")
        return {"ok": True, "hotkey": app.hotkey_label}

    def on_engine(self, name):
        """Cambia el motor (auto/vulkan/cuda/cpu), reinicia el servidor GPU."""
        if name not in ENGINES:
            return
        app.engine = name
        config_set("engine", name)
        avail = {o["key"]: o["available"] for o in engine_options()}
        if name != "auto" and not avail.get(name, False):
            app.engine_note = (f"{ENGINE_LABELS.get(name, name)} no se puede "
                               f"usar en este equipo, asi que se seguira con "
                               f"{engine_label(pick_engine(name))}. "
                               f"{engine_reason(name, False)}")
            log("Motor: " + app.engine_note)
        else:
            app.engine_note = ""
            log(f"Motor: {name}")

        def work():
            try:
                _get_server().stop()          # fuerza reinicio con el nuevo motor
                resolved = pick_engine(name)
                app.engine_resolved = resolved
                _p, gi = gpu_device_pref(resolved)
                app.gpu_device_resolved = gi if gi is not None else "auto"
                model_path = ensure_model(MODELS.get(app.model or "small",
                                                     MODELS["small"]))
                if resolved in ("vulkan", "cuda"):
                    _get_server().ensure(model_path, app.language, resolved)
                app.status, app.status_color = app_status_ready(), "#4caf50"
                log(f"Motor activo: {engine_label(resolved)}")
            except Exception as e:
                log(f"No se pudo cambiar el motor: {e}")

        threading.Thread(target=work, daemon=True).start()
        self.tray.refresh()

    def rpc_gpu_device(self, value):
        """POST {action:'gpu_device', value:{index:N}} o value:'auto': elige QUE
        GPU concreta usa el motor (no la tecnologia). Guarda en config y
        relanza el motor como on_engine. Si el indice no existe, cae a auto."""
        engine = pick_engine(app.engine)
        idx = None
        if isinstance(value, dict):
            idx = value.get("index")
        elif isinstance(value, (int, float)) and not isinstance(value, bool):
            idx = int(value)
        elif isinstance(value, str) and value.strip().lower() != "auto":
            try:
                idx = int(value.strip())
            except (TypeError, ValueError):
                idx = None
        if idx is not None:
            try:
                idx = int(idx)
            except (TypeError, ValueError):
                idx = None
        devs = (list_gpu_devices(engine)
                if engine in ("vulkan", "cuda", "rocm") else [])
        stored, resolved, note = "auto", "auto", ""
        if idx is not None and any(d["index"] == idx for d in devs):
            stored, resolved = {"index": idx}, idx
            dev = next(d for d in devs if d["index"] == idx)
            note = f"GPU elegida: {dev['name']} (dispositivo {idx})."
        elif idx is not None:
            note = (f"El dispositivo {idx} no existe entre los disponibles; "
                    f"se usara Automatico.")
        app.gpu_device = stored
        app.gpu_device_resolved = resolved
        app.gpu_device_note = note
        config_set("gpu_device", stored)
        log(f"Dispositivo GPU: {stored}" + (f" - {note}" if note else ""))
        self.ui_events.put(("gpu_device", None))     # relanza en el hilo de Tk
        return {"ok": True, "gpu_device": stored, "gpu_device_resolved": resolved,
                "gpu_device_note": note, "engine": app.engine,
                "engine_resolved": engine,
                "devices": devs}

    def apply_gpu_device(self):
        """Relanza el motor para APLICAR el dispositivo GPU elegido. Igual que
        on_engine: no cambia la tecnologia, solo QUE tarjeta usa."""
        def work():
            try:
                _get_server().stop()
                resolved = pick_engine(app.engine)
                app.engine_resolved = resolved
                _p, gi = gpu_device_pref(resolved)
                app.gpu_device_resolved = gi if gi is not None else "auto"
                model_path = ensure_model(MODELS.get(app.model or "small",
                                                     MODELS["small"]))
                if resolved in ("vulkan", "cuda"):
                    _get_server().ensure(model_path, app.language, resolved)
                app.status, app.status_color = app_status_ready(), "#4caf50"
                log(f"Dispositivo GPU aplicado en {engine_label(resolved)} "
                    f"(dispositivo {app.gpu_device_resolved}).")
            except Exception as e:
                log(f"No se pudo aplicar el dispositivo GPU: {e}")

        threading.Thread(target=work, daemon=True).start()
        self.tray.refresh()

    def test(self):
        threading.Thread(target=self.probe_test_input, daemon=True).start()

    def probe_test_input(self):
        hwnd = app.target_hwnd or _user32.GetForegroundWindow()
        start_delivery("prueba dicta 123", hwnd, app.target_title or _fg_title())

    def quit(self):
        # CIERRE LIMPIO **antes** de tocar la GUI: suelta el modelo de la GPU
        # (whisper-server), para los hilos de audio/transcripción y mata los
        # hijos. Sin esto, os._exit(0) dejaba vivo el whisper-server con el
        # modelo cargado en la VRAM (el proceso parásito). Idempotente.
        try:
            shutdown_service("salida")
        except Exception as e:
            log(f"Cierre limpio: {e!r}")
        for hk in (_hotkeys, _cancel, _panelshot, _meetingshot, _meetingstop):
            try:
                hk.release()
            except Exception:
                pass
        try:
            # La ventana del panel se DESTRUYE (no se oculta): la app se va.
            if hasattr(self.panel, "shutdown"):
                self.panel.shutdown()
            else:
                self.panel.close()
        except Exception:
            pass
        try:
            self.control.stop()
        except Exception:
            pass
        try:
            self.tray.stop()
        except Exception:
            pass
        try:
            self.root.destroy()
        finally:
            os._exit(0)

    # ---- puente tray <-> Tk
    def _tray_event(self, event):
        self.ui_events.put(event)

    def _tray_snapshot(self):
        return {"mics": list_input_devices(), "mic": self.mic.device,
                "model": app.model,
                "theme": app.theme, "sens": app.sens, "engine": app.engine,
                "engines": _available_engines()}

    # ---- puente con el panel web
    def panel_state(self):
        """Instantánea para el panel. Se llama desde el hilo del servidor HTTP,
        así que solo lee estado plano (nunca toca widgets)."""
        mics = [{"idx": i, "name": n} for i, n in list_input_devices()]
        status = getattr(app, "status", "") or ""
        kind = ""
        st = app.state
        if st == "recording":
            status, kind = "Escuchando…", "busy"
        elif st == "transcribing":
            status, kind = "Transcribiendo…", "busy"
        elif app.mic_error:
            status, kind = app.mic_error, "err"
        return {"model": app.model or config_get("model", "small"),
                "engine": app.engine,
                "engine_resolved": app.engine_resolved or pick_engine(app.engine),
                "engine_note": (getattr(app, "engine_note", "")
                                or ENGINE_NOTE_BASE),
                "engines": _available_engines(),
                "engine_options": engine_options(),
                # Que GPU CONCRETA usa el motor (no la tecnologia): preferencia
                # guardada ('auto' o {'index':N}), indice efectivo y aviso.
                "gpu_device": getattr(app, "gpu_device", "auto"),
                "gpu_device_resolved": getattr(app, "gpu_device_resolved", "auto"),
                "gpu_device_note": getattr(app, "gpu_device_note", ""),
                "icon_version": icon_version(),
                "models": model_options(),
                "language": app.language, "sens": app.sens, "theme": app.theme,
                "voice_threshold": round(float(app.voice_threshold), 6),
                "silence_wait": round(float(app.silence_wait), 3),
                "paste_mode": str(getattr(app, "paste_mode", "auto")),
                # Valores validos de paste_mode (documentado en /state): auto
                # detecta; ctrl+v / ctrl+shift+v / shift+insert fuerzan la
                # combinacion; type TECLEA el texto como entrada real.
                "paste_modes": list(PASTE_MODES),
                "rms": round(float(getattr(app, "rms", 0.0)), 6),
                "thr": round(float(getattr(app, "thr", 0.0)), 6),
                "voice": bool(getattr(app, "rms", 0.0) >
                              getattr(app, "thr", 1.0)),
                "island_pos": getattr(app, "island_pos", "top"),
                "island_palette": getattr(app, "island_palette", "grafito"),
                "mic": self.mic.device if self.mic else None,
                "mics": mics, "dictionary": list(app.dictionary),
 "sources": _audio_sources(),
 "meeting_source": str(config_get("meeting_source", "all")),
                "hotkey": app.hotkey_label, "cancel_key": app.cancel_key_label,
                "panel_key": app.panel_key_label,
                "meeting_key": app.meeting_key_label,
                "meeting_stop_key": app.meeting_stop_key_label,
                # Agrupados para el panel: hotkeys.<nombre>.
                "hotkeys": {"dictation": app.hotkey_label,
                            "cancel": app.cancel_key_label,
                            "panel": app.panel_key_label,
                            "meeting": app.meeting_key_label,
                            "meeting_stop": app.meeting_stop_key_label},
                "mic_test": _mictest.snapshot(),
                "meeting_mic": bool(config_get("meeting_mic", True)),
                "status": status, "status_kind": kind, "st": st,
                "version": VERSION,
                # Actualizacion desde la app: la comprobacion esta ACTIVADA de
                # fabrica (`check_updates`) porque es lo unico que puede salir a
                # la red, no lleva datos del usuario y es desactivable. Si esta
                # apagada, `enabled` es False y no se ha consultado nada a la
                # red; `progress` es 0..100.
                "update": dict(UPDATE_STATE),
                # Ajuste REAL de la comprobacion automatica: lo que hay ahora
                # mismo en dicta_config.json. Se publica aparte para que el panel
                # no tenga que espejar /state.update.enabled, que solo se
                # rellena tras la PRIMERA comprobacion (y por eso mentia al
                # arrancar: salia «off» con el ajuste encendido).
                "check_updates": bool(config_get("check_updates", True)),
                "queue": queue_for_state(),
                "uploads": _uploads.snapshot(),
                "meeting": _meeting.snapshot(),
                # Bandas de frecuencia de la reunion en curso (grave->agudo),
                # 0..1, por pista, para que el panel dibuje la onda de verdad.
                "levels": _meeting.levels(),
                "docs": [{"name": f,
                          "size": os.path.getsize(os.path.join(DOCS_DIR, f)),
                          "mtime": os.path.getmtime(os.path.join(DOCS_DIR, f)),
                          "audio": (os.path.basename(w) if os.path.isfile(w)
                                    else None),
                          # Peso del audio PROPIO del documento (el .wav de la
                          # reunion, que se llama como el). El panel lo usa para
                          # la cabecera de la tarjeta sin tener que decodificar
                          # nada; 0 si no hay audio emparejado.
                          "audio_size": (os.path.getsize(w)
                                         if os.path.isfile(w) else 0)}
                         for f in (os.listdir(DOCS_DIR)
                                   if os.path.isdir(DOCS_DIR) else [])
                         for w in [os.path.join(
                             AUDIOS_DIR,
                             os.path.splitext(f)[0] + ".wav")]]}

    def _panel_rpc(self, action, value):
        """Llega desde el hilo HTTP: encola para aplicarlo en el hilo de Tk."""
        if action == "quit":
            self.ui_events.put("quit")
            return
        if action == "test":
            self.ui_events.put("test")
            return
        if action == "open_panel":
            # Lo usa un segundo lanzamiento del .exe/.bat: dicta no tiene
            # ventana propia, así que volver a abrirla tiene que ENSEÑAR algo
            # (el panel) en vez de morir en silencio.
            self.ui_events.put("open_panel")
            return
        if action == "mic.test":
            # Prueba de micro de verdad: captura ~5 s y publica el nivel.
            if str(value or "").strip().lower() in ("stop", "cancel"):
                _mictest.cancel()
            else:
                _mictest.start()
            return {"ok": True, "mic_test": _mictest.snapshot()}
        if action == "hotkey" and isinstance(value, dict):
            # POST {action:"hotkey", value:{"name":"meeting","keys":"..."}}:
            # elige por nombre cuál de los cuatro atajos se cambia.
            name = str(value.get("name") or "").strip().lower()
            evname = {"dictation": "hotkey_rpc", "cancel": "cancel_rpc",
                      "panel": "panel_key_rpc",
                      "meeting": "meeting_key_rpc",
                      "meeting_stop": "meeting_stop_rpc"}.get(name)
            if evname is None:
                return {"ok": False, "error": "unknown name",
                        "hotkeys": {"dictation": app.hotkey_label,
                                    "cancel": app.cancel_key_label,
                                    "panel": app.panel_key_label,
                                    "meeting": app.meeting_key_label,
                                    "meeting_stop": app.meeting_stop_key_label}}
            reply = queue.Queue(maxsize=1)
            self.ui_events.put((evname, str(value.get("keys") or ""), reply))
            try:
                return reply.get(timeout=5.0)
            except queue.Empty:
                return {"ok": False, "error": "timeout"}
        # set_hotkey / set_cancel_key se aplican en el hilo de Tk y responden.
        for act, evname in (("set_hotkey", "hotkey_rpc"),
                            ("hotkey", "hotkey_rpc"),
                            ("set_cancel_key", "cancel_rpc"),
                            ("set_panel_key", "panel_key_rpc")):
            if action == act:
                reply = queue.Queue(maxsize=1)
                self.ui_events.put((evname, value, reply))
                try:
                    return reply.get(timeout=5.0)
                except queue.Empty:
                    return {"ok": False, "error": "timeout"}
        if action == "check_updates":
            # Interruptor del panel: enciende/apaga la comprobacion de version
            # (ajuste `check_updates`, APAGADO de fabrica). Al activarlo se
            # lanza una comprobacion en segundo plano; al apagarlo, dicta deja
            # de tocar la red y limpia el estado.
            return self.on_check_updates(value)
        if action == "check_update":
            # Boton "Comprobar ahora" del panel (equivale al POST de nivel
            # superior): respeta el ajuste; con value.force consulta igualmente
            # aunque este apagado (accion explicita del usuario).
            val = value
            force = bool(val.get("force")) if isinstance(val, dict) else False
            r = check_update(force=force)
            ran = bool(force or r.get("enabled"))
            return {"ok": ran and not bool(r.get("error")), "force": force,
                    "update": r}
        if action == "paste_mode":
            # POST {action:"paste_mode", value:"auto|ctrl+v|ctrl+shift+v|
            # shift+insert"}: fuerza la combinacion del pegado automatico para
            # terminales que no se dejen detectar. Persistente en config.
            return self.on_paste_mode(value)
        if action == "hide":
            try:
                self.panel.close()
            except Exception:
                pass
            return
        if action == "window" and value:
            # La barra integrada del panel (panel/desktop.js) usa la API de
            # pywebview, pero la página también puede pedir estos comandos por
            # POST: con WebView2 los atiende el propio host.
            if hasattr(self.panel, "window_command"):
                self.panel.window_command(str(value))
                return
            hwnd = self.panel.hwnd or _panel_hwnd(self.panel.window_title)
            if hwnd:
                self.panel.hwnd = hwnd
                _panel_window_cmd(hwnd, str(value))
            return
        if action == "gpu_device":
            # POST {action:"gpu_device", value:{"index":N}} o value:"auto":
            # elige QUE GPU concreta usa el motor (no la tecnologia). Persiste
            # y relanza el motor como al cambiar de motor.
            try:
                return self.rpc_gpu_device(value)
            except Exception as e:
                return {"ok": False, "error": str(e)}
        if action in ("model", "engine", "language", "theme", "sens", "mic",
                      "dictionary", "meeting_source", "meeting_mic",
                      "island_pos", "island_palette", "voice_threshold",
                      "silence_wait"):
            self.ui_events.put((action, value))

    def open_panel(self):
        self.panel.open()

    def _drain_events(self):
        while True:
            try:
                ev = self.ui_events.get_nowait()
            except queue.Empty:
                break
            if ev == "open_panel":
                self.panel.open()
            elif ev == "quit":
                self.quit()
            elif ev == "test":
                self.test()
            elif isinstance(ev, tuple) and len(ev) == 3 \
                    and ev[0] in ("hotkey_rpc", "cancel_rpc", "panel_key_rpc",
                                  "meeting_key_rpc", "meeting_stop_rpc"):
                _, value, reply = ev
                handler = {"cancel_rpc": self.on_cancel_key,
                           "panel_key_rpc": self.on_panel_key,
                           "meeting_key_rpc": self.on_meeting_key,
                           "meeting_stop_rpc": self.on_meeting_stop_key}.get(
                               ev[0], self.on_hotkey)
                try:
                    reply.put(handler(value), block=False)
                except Exception as e:
                    try:
                        reply.put({"ok": False, "error": str(e)}, block=False)
                    except Exception:
                        pass
                self.tray.refresh()
            elif isinstance(ev, tuple):
                kind, value = ev
                if kind == "model":
                    self.on_model(value)
                elif kind == "mic":
                    self.on_mic(value)
                elif kind == "theme":
                    self.on_theme(value)
                elif kind == "island_pos":
                    self.on_island_pos(value)
                elif kind == "island_palette":
                    self.on_island_palette(value)
                elif kind == "sens":
                    self.on_sens(value)
                elif kind == "voice_threshold":
                    self.on_voice_threshold(value)
                elif kind == "silence_wait":
                    self.on_silence_wait(value)
                elif kind == "engine":
                    self.on_engine(value)
                elif kind == "gpu_device":
                    self.apply_gpu_device()
                elif kind == "language":
                    self.on_language(value)
                elif kind == "dictionary":
                    self.on_dictionary(value or [])
                elif kind == "meeting_source":
                    config_set("meeting_source", str(value or "all"))
                    log(f"Fuente de audio de reunión: "
                        f"{_source_label(str(value or 'all'))}")
                elif kind == "meeting_mic":
                    config_set("meeting_mic", bool(value))
                    log(f"Micrófono en la reunión: "
                        f"{'sí' if value else 'no'}")
                self.tray.refresh()

    # ---- ciclo de vida
    def tick(self):
        service_app(self.mic, app.mode)
        if app.dismiss_overlay:            # pegado/cancelado: animación fuera YA
            app.dismiss_overlay = False
            self._last_state = ("idle", False)
            self._cancel_hide()
            self.overlay.hide()
        self._drain_events()
        if app.panel_request:
            app.panel_request = False
            self.panel.open()
        self.panel.poll()
        st = app.state
        meet = _meeting.snapshot()
        meeting_on = bool(meet.get("active"))
        # La isla sirve a las dos cosas: dictado y reunion (manda el dictado).
        dictating = st in ("recording", "transcribing", "cancelled")
        key = (st, meeting_on)
        if key != self._last_state:
            if dictating:
                self.overlay.show(app.current_transcript, state=st)
            elif meeting_on:
                self.overlay.show(meet.get("last") or "", state="recording")
            else:
                self._schedule_hide(4800)
            self._last_state = key
        if dictating or meeting_on:
            if dictating:
                live = (preview_text() if st == "recording"
                        else app.current_transcript)
                self.overlay.set_text(live)
                self.overlay.draw(app.rms, st, app.wave_data)
            else:
                # Vista previa de la reunion: la onda sigue lo que se captura.
                # El nivel va normalizado 0..1 y la isla divide por 0,035, asi
                # que se devuelve a esa escala para no saturarla.
                self.overlay.set_text(meet.get("last") or "")
                self.overlay.draw(float(meet.get("level") or 0.0) * 0.035,
                                  "recording")
            self._cancel_hide()
        self.root.after(40, self.tick)

    def _enforce_frameless(self):
        """Obsoleto: la ventana del panel conserva la barra nativa de Windows."""
        return

    def _schedule_hide(self, ms):
        self._cancel_hide()
        self._overlay_auto_hide = self.root.after(ms, self.overlay.hide)

    def _cancel_hide(self):
        if self._overlay_auto_hide is not None:
            try:
                self.root.after_cancel(self._overlay_auto_hide)
            except Exception:
                pass
            self._overlay_auto_hide = None

    def start(self):
        self.tray.start()
        self.root.after(80, self.tick)
        if PANEL_ON_START:
            self.ui_events.put("open_panel")

    def run(self):
        self.root.mainloop()


# ------------------------------------------------------------------ main
def single_instance():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(("127.0.0.1", LOCK_PORT))
        s.listen(1)
        return s
    except OSError:
        return None


def _wake_running_instance(action="open_panel"):
    """Le pide una acción a la instancia que ya está corriendo.

    El puerto del panel no es fijo (se coge el primero libre desde
    PANEL_PORT), así que se recorre el mismo rango, y antes de mandar nada se
    comprueba que quien responde ahi sea dicta: si no, se le estaría
    escribiendo a otro programa que casualmente tenga ese puerto.
    """
    import urllib.request
    body = json.dumps({"action": action}).encode("utf-8")
    for port in range(PANEL_PORT, PANEL_PORT + 12):
        base = f"http://127.0.0.1:{port}"
        try:
            with urllib.request.urlopen(base + "/state", timeout=0.7) as r:
                st = json.loads(r.read().decode("utf-8", "replace"))
            if not (isinstance(st, dict) and "version" in st and "queue" in st):
                continue
            req = urllib.request.Request(
                base + "/", data=body,
                headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=2.0) as r:
                r.read()
            return True
        except Exception:
            continue
    return False


def main():
    global _crash_log_file, PANEL_ON_START, _mic
    # ANTES de tocar pywebview/pythonnet: .NET lee <exe>.exe.config al
    # inicializar el CLR, asi que el interruptor tiene que estar ya en disco.
    ensure_dotnet_config()
    try:
        _crash_log_file = open(os.path.join(SCRIPT_DIR, "dicta_crash.log"),
                               "w", encoding="utf-8")
        faulthandler.enable(_crash_log_file)
    except Exception:
        pass
    ap = argparse.ArgumentParser(description="dicta — dictado por voz local")
    ap.add_argument("--model", default=None, choices=list(MODELS))
    ap.add_argument("--language", default=None)
    ap.add_argument("--hotkey", default=None)
    ap.add_argument("--silence", type=float, default=None,
                    help="segundos de pausa que cortan la escucha (0.2-600)")
    ap.add_argument("--mode", default="toggle", choices=["toggle", "hold"])
    ap.add_argument("--engine", default=None, choices=list(ENGINES),
                    help="auto | vulkan (AMD/Intel/NVIDIA) | cuda (NVIDIA) | cpu")
    ap.add_argument("--file", default=None)
    ap.add_argument("--no-panel", action="store_true",
                    help="no abrir el panel de ajustes al arrancar")
    ap.add_argument("--list-mics", action="store_true")
    ap.add_argument("--no-gui", action="store_true")
    args = ap.parse_args()

    if args.list_mics:
        for i, d in enumerate(sd.query_devices()):
            if d["max_input_channels"] > 0:
                print(f"{i}: {d['name']}")
        return

    if args.model:
        app.model = args.model
        config_set("model", args.model)
    else:
        app.model = config_get("model", "small")
    if args.language:
        app.language = args.language
        config_set("language", args.language)
    # El prompt de Whisper se construye con el diccionario del usuario.
    if app.dictionary:
        app.prompt = ", ".join(app.dictionary)
    app.mode = args.mode
    if args.engine:
        app.engine = args.engine
        config_set("engine", args.engine)
    if args.no_panel:
        PANEL_ON_START = False
    if args.file:
        data, sr = sf.read(args.file, dtype="float32")
        if sr != SAMPLE_RATE:
            data = np.interp(
                np.linspace(0, len(data), int(len(data) * SAMPLE_RATE / sr)),
                np.arange(len(data)), data).astype(np.float32)
        log(f"Archivo {args.file} ({len(data)/SAMPLE_RATE:.1f}s)")
        print(">>> " + transcribe(data, ensure_model(MODELS[app.model]),
                                  app.language, app.prompt))
        return

    lock = single_instance()
    if lock is None:
        # Ya hay una instancia. Como dicta vive en la bandeja y no tiene
        # ventana propia, relanzarlo no mostraría nada: se le pide que abra el
        # panel, y así «volver a abrirlo» siempre hace algo visible.
        if _wake_running_instance("open_panel"):
            log("dicta ya estaba abierto: se le pidió a la instancia en curso "
                "que abra el panel.")
            sys.exit(0)
        log("dicta ya está abierto (otra instancia, y no responde al panel).")
        sys.exit(1)

    mic = Mic()
    mic.start()
    _mic = mic                    # el cierre limpio lo para

    # Backend de la ventana del panel: WebView2 (pywebview, sin marco, barra
    # dibujada por la página) o el navegador en modo aplicación. La clave
    # `panel_backend` de dicta_config.json puede forzarlo; «auto» prefiere
    # WebView2 y cae a Chrome si falta pywebview o el runtime de WebView2.
    webview_mod = None
    panel_host = None
    panel_win = None
    if not args.no_gui and panel_backend() == "webview":
        try:
            import webview as webview_mod
        except Exception as e:
            log(f"pywebview no disponible ({e}); el panel se abrirá con Chrome.")
            webview_mod = None
    if webview_mod is not None:
        # La ventana se crea aquí (pywebview lo exige antes de start()); su
        # host se le pasa al Overlay, que es quien le da el puerto real.
        try:
            panel_host, panel_win = create_webview_panel(webview_mod)
            log("Panel: backend WebView2 (pywebview) — ventana sin marco, "
                "barra integrada en la página.")
        except Exception as e:
            log(f"No se pudo crear la ventana de WebView2 ({e}); "
                f"el panel se abrirá con Chrome.")
            webview_mod = panel_host = panel_win = None

    # Motor: precarga (descarga del modelo si no está) fuera de la GUI, y
    # arranca el servidor GPU Vulkan + una inferencia de calentamiento para que
    # el primer dictado ya vaya rápido (compila los shaders una vez).
    def preload():
        # Barrido de ARRANQUE, antes de nada: si una ejecución anterior murió
        # de golpe, su whisper-server sigue vivo con el modelo en la VRAM y
        # además ocupa el puerto del servidor GPU (47801), así que el nuevo no
        # podría arrancar. Se mata aquí (sincrónico, sin carrera con el nuevo).
        _reap_orphan_whisper()
        try:
            model_path = ensure_model(MODELS.get(app.model or "small", MODELS["small"]))
            engine = pick_engine(app.engine)
            app.engine_resolved = engine
            _p, gi = gpu_device_pref(engine)
            app.gpu_device_resolved = gi if gi is not None else "auto"
            log(f"Motor seleccionado: {engine_label(engine)} " +
                ("(auto)" if app.engine == "auto" else ""))
            srv = _get_server()
            if srv.ensure(model_path, app.language, engine):
                # Warmup con 1 s de silencio: compila shaders y deja el modelo
                # residente, así el primer dictado real ya va a tope.
                srv.transcribe(np.zeros(SAMPLE_RATE, np.float32),
                               model_path, app.language, engine=engine)
            app.status, app.status_color = app_status_ready(), "#4caf50"
        except Exception as e:
            log(f"Error al preparar el modelo: {e}")
            app.status, app.status_color = f"⚠ Error de carga — {e}", "#e53935"

    def serve(gui):
        """Arranca el servicio (y la GUI si la hay).

        Se ejecuta en el hilo principal con el backend de Chrome. Con WebView2
        es `webview.start(func=...)` quien la llama en un hilo aparte, porque el
        hilo principal se lo queda el bucle de WebView2 (y el de Tk, que es
        quien mueve la isla y la bandeja, tiene que ser el MISMO hilo que creó
        el intérprete de Tk: por eso el Overlay se construye aquí dentro).
        """
        threading.Thread(target=preload, daemon=True).start()

        atexit.register(lambda: shutdown_service("atexit"))

        # Audios subidos que quedaron a medias en una ejecucion anterior: se
        # reencolan para que la cola siga donde estaba tras el reinicio.
        try:
            for _it in _uploads.pending():
                _uploads.set(_it["id"], state="pendiente")
                _audio_queue.add(_uploads.path_of(_it), _it["name"],
                                 key=_it["id"])
        except Exception as e:
            log(f"No se pudieron reencolar las subidas pendientes: {e}")

        # Atajo: CLI manda; si no, el guardado en config; si no, alt+q.
        app.hotkey_label = args.hotkey or config_get("hotkey", "alt+q")
        _hotkeys.mode = args.mode
        _hotkeys.apply(app.hotkey_label)
        # Silencio que corta la escucha, rápido por defecto (0,8 s).
        _sw = (args.silence if args.silence is not None
               else config_get("silence_wait",
                               config_get("silence", SILENCE_TIMEOUT)))
        app.silence_wait = min(SILENCE_WAIT_MAX,
                               max(SILENCE_WAIT_MIN, float(_sw)))
        # Atajo de cancelar dictado; de fábrica Alt+E.
        _cancel.mode = args.mode
        if not _cancel.apply(config_get("cancel_key", "alt+e")):
            log("Atajo de cancelar no disponible; se queda sin registrar.")
        # Atajo para abrir el panel (por si el icono de la bandeja esta escondido).
        _panelshot.mode = args.mode
        if not _panelshot.apply(config_get("panel_key", "ctrl+alt+p")):
            log("Atajo del panel no disponible; se queda sin registrar.")
        # Atajo del modo REUNION (iniciar/parar sin abrir la app); de fabrica
        # Ctrl+Alt+R.
        _meetingshot.mode = args.mode
        if not _meetingshot.apply(config_get("meeting_key", "ctrl+alt+r")):
            log("Atajo de reunion no disponible; se queda sin registrar.")
        # Quinto atajo: detener (guardar) la reunion; de fabrica Ctrl+Alt+S.
        _meetingstop.mode = args.mode
        if not _meetingstop.apply(config_get("meeting_stop_key", "ctrl+alt+s")):
            log("Atajo de parada de reunion no disponible; se queda sin registrar.")

        try:
            _cfg_disk = {}
            if os.path.isfile(CONFIG_FILE):
                with open(CONFIG_FILE, encoding="utf-8") as _f:
                    _cfg_disk = json.load(_f)
        except Exception:
            _cfg_disk = {}
        for _k, _v in (("voice_threshold", app.voice_threshold),
                       ("silence_wait", app.silence_wait),
                       ("paste_mode", getattr(app, "paste_mode", "auto")),
                       ("meeting_stop_key", app.meeting_stop_key_label),
                       # Comprobacion de version: ACTIVADA de fabrica (es lo
                       # unico que puede salir a la red, sin datos del usuario
                       # y desactivable).
                       ("check_updates", bool(config_get("check_updates", True)))):
            if _k not in _cfg_disk:
                config_set(_k, _v)
        elevado = _esta_elevado()
        log(f"dicta {APP_VERSION} listo — {app.hotkey_label}, modo {args.mode}, "
            f"idioma {app.language}, cancelar {app.cancel_key_label} "
            f"(elevado: {'sí' if elevado else 'no'})")
        if not elevado:
            log("AVISO: sin administrador el texto no se pegará en ventanas "
                "elevadas (otras consolas o apps como administrador). Arranca "
                "dicta con run.bat si dictas ahí.")

        if gui:
            gui.start()
            gui.run()
        else:
            try:
                while True:
                    service_app(mic, args.mode)
                    time.sleep(0.025)
            except KeyboardInterrupt:
                try:
                    shutdown_service("ctrl-c")
                except Exception:
                    pass
                log("Adiós.")

    # El servicio se arranca UNA vez, sea por WebView2 (hilo aparte) o por el
    # camino de siempre (hilo principal). `serve_once` evita que un fallo a
    # mitad deje dos bucles y dos paneles.
    started = {"n": 0}

    def serve_once(gui):
        if started["n"]:
            return
        started["n"] += 1
        serve(gui)

    def chrome_overlay():
        """Overlay con el panel de siempre (navegador en modo aplicación)."""
        log("Panel: backend Chrome/Edge (ventana en modo aplicación).")
        try:
            return Overlay(mic)
        except Exception as e:
            log(f"Sin GUI ({e}); modo consola.")
            return None

    if not args.no_gui and webview_mod is not None and panel_host is not None:
        # WebView2: el bucle de la ventana se queda el hilo principal; el
        # servicio (Tk + isla + bandeja) pasa al hilo que deja libre start().
        def _serve_webview():
            # La ventana de WebView2 ya existe: redondea sus esquinas cuanto
            # antes (es del propio proceso, DWM sí atiende).
            panel_host._polish_window()
            try:
                overlay = Overlay(mic, panel=panel_host)
            except Exception as e:
                log(f"Sin GUI ({e}); modo consola.")
                overlay = None
            serve_once(overlay)

        try:
            # El arrastre solo desde los elementos con la clase de la barra
            # (no desde sus descendientes ni desde el resto de la página).
            webview_mod.settings["DRAG_REGION_DIRECT_TARGET_ONLY"] = True
            # Puerto de depuración de WebView2, solo si se pide por entorno
            # (DICTA_WEBVIEW_DEBUG_PORT): permite comprobar la ventana real por
            # CDP sin tocar la configuración del usuario.
            _dbg = os.environ.get("DICTA_WEBVIEW_DEBUG_PORT")
            if _dbg:
                webview_mod.settings["REMOTE_DEBUGGING_PORT"] = int(_dbg)
                log(f"Panel: depuración de WebView2 en 127.0.0.1:{_dbg}")
            webview_mod.start(_serve_webview, gui="edgechromium",
                              private_mode=False,
                              storage_path=os.path.join(SCRIPT_DIR, ".tmp",
                                                        "webview-profile"),
                              icon=_official_icon_ico(getattr(app, "theme",
                                                             "light")))
        except Exception as e:
            # Sin WebView2 no hay ventana: se cae al navegador, que no falla.
            log(f"WebView2 no arrancó ({e}); el panel se abrirá con Chrome.")
            serve_once(chrome_overlay())
            while True:
                time.sleep(3600)
        # El bucle ha terminado: o se cerró la app (quit -> os._exit) o se
        # destruyó la última ventana. En el segundo caso el servicio sigue vivo
        # en su hilo: no se mata la app por cerrar el panel.
        log("Panel (webview): bucle de ventana terminado; dicta sigue vivo.")
        while True:
            time.sleep(3600)

    serve_once(chrome_overlay() if not args.no_gui else None)


if __name__ == "__main__":
    main()
