#!/usr/bin/env python3
"""dicta_ui — interfaz de dicta: bandeja del sistema y overlay de la muesca.

- Tray: icono en la bandeja de Windows; clic derecho abre menú con modelo,
  motor, micrófono, apariencia y salir.
- Overlay: una isla (Dynamic Island) en la parte inferior central con
  una onda de degradado que fluye con la voz, y una tarjeta debajo con la
  transcripción.
- El panel de ajustes es una ventana web aparte (carpeta ``panel/``).
"""

import os
import ctypes
import sys
import threading
import time
import traceback
import numpy as np
import pystray
from PIL import Image, ImageDraw
import tkinter as tk

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# El chrome flotante (ventana *layered* con alpha por píxel) vive en
# ``dicta_layered``: allí TODOS los prototipos Win32 de 64 bits están
# declarados y el DIB se gestiona con cerrojo. Reutilizarlo es justo lo que
# elimina las violaciones de acceso del código anterior, que declaraba
# ``ctypes.WinDLL`` sin ``argtypes``/``restype`` (en x64 eso trunca los
# HANDLE a 32 bits y ``CreateWindowExW`` reventaba con un puntero basura).
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)
try:
    import dicta_layered as _shell
except Exception:                                  # pragma: no cover
    _shell = None

# True si este proceso puede crear chrome flotante nativo.
_SHELL_OK = bool(_shell is not None and _shell.available())
# Base real de la isla: si dicta_layered no está, se degrada a object y
# IslandWindow queda inerte (open() devuelve False) en vez de romper el import.
_LayeredBase = _shell.LayeredWindow if _shell is not None else object

MODEL_NAMES = ("tiny", "base", "small", "medium", "turbo")
_TRAY_FILTER_PATCHED = False

# Cuerpo de la isla: SEMITRANSPARENTE (cristal esmerilado, el fondo se ve
# Cuerpo de la isla: SÓLIDO en ambos temas (sin transparencia).
# Grafito y blanco unificados con la superficie de la tarjeta (misma familia).
_ISLAND_BODY = (0.055, 0.059, 0.075)     # #0E0F13 (grafito)
_ISLAND_BODY_LIGHT = (1.000, 1.000, 1.000)   # blanco sólido
_CARD_TEXT = "#f5f5f7"
_CARD_TEXT_LIGHT = "#1b2330"

# Degradados de la onda (3 paradas) por PALETA. Cada preset trae su historia
# frío (escucha) / cálido (procesando) / apagado (cancelar) en los DOS temas,
# más el color del cuerpo (opcional). "grafito" es el preset de siempre.


def _p(listen, trans, cancel, listen_l, trans_l, cancel_l, body, body_l):
    return {"listen": listen, "trans": trans, "cancel": cancel,
            "listen_l": listen_l, "trans_l": trans_l, "cancel_l": cancel_l,
            "body": body, "body_l": body_l}


PALETTES = {
    # Grafito: la actual (teal→azul→violeta frío / ámbar→coral→rosa cálido).
    "grafito": _p(
        ((0.239, 0.851, 0.769), (0.357, 0.616, 1.000), (0.608, 0.482, 1.000)),
        ((1.000, 0.761, 0.290), (1.000, 0.478, 0.420), (1.000, 0.373, 0.635)),
        ((0.760, 0.300, 0.300), (0.700, 0.320, 0.400), (0.600, 0.330, 0.470)),
        ((0.047, 0.569, 0.494), (0.122, 0.498, 0.878), (0.427, 0.275, 0.839)),
        ((0.761, 0.463, 0.039), (0.839, 0.251, 0.184), (0.769, 0.118, 0.478)),
        ((0.720, 0.180, 0.200), (0.660, 0.200, 0.300), (0.560, 0.200, 0.360)),
        (0.055, 0.059, 0.075), (1.000, 1.000, 1.000)),
    # Océano: azules y cian.
    "oceano": _p(
        ((0.200, 0.700, 0.950), (0.160, 0.450, 0.920), (0.300, 0.280, 0.850)),
        ((0.350, 0.800, 0.950), (0.250, 0.550, 0.980), (0.450, 0.350, 0.950)),
        ((0.450, 0.400, 0.750), (0.400, 0.360, 0.660), (0.360, 0.340, 0.580)),
        ((0.060, 0.450, 0.700), (0.050, 0.300, 0.720), (0.200, 0.180, 0.650)),
        ((0.120, 0.520, 0.720), (0.100, 0.360, 0.780), (0.280, 0.240, 0.720)),
        ((0.300, 0.260, 0.550), (0.260, 0.220, 0.480), (0.220, 0.200, 0.420)),
        (0.030, 0.055, 0.095), (0.960, 0.980, 1.000)),
    # Ámbar: dorados y naranjas.
    "ambar": _p(
        ((1.000, 0.800, 0.300), (1.000, 0.600, 0.200), (0.950, 0.450, 0.150)),
        ((1.000, 0.700, 0.250), (1.000, 0.450, 0.200), (0.950, 0.300, 0.250)),
        ((0.750, 0.350, 0.250), (0.700, 0.320, 0.300), (0.620, 0.300, 0.340)),
        ((0.750, 0.500, 0.050), (0.820, 0.400, 0.030), (0.800, 0.300, 0.050)),
        ((0.780, 0.420, 0.030), (0.850, 0.250, 0.050), (0.800, 0.150, 0.100)),
        ((0.680, 0.220, 0.140), (0.620, 0.180, 0.180), (0.550, 0.160, 0.220)),
        (0.075, 0.060, 0.040), (1.000, 0.990, 0.970)),
    # Menta: verdes frescos.
    "menta": _p(
        ((0.300, 0.900, 0.600), (0.200, 0.800, 0.550), (0.150, 0.650, 0.600)),
        ((0.600, 0.950, 0.500), (0.350, 0.850, 0.450), (0.200, 0.700, 0.550)),
        ((0.550, 0.550, 0.450), (0.500, 0.480, 0.420), (0.450, 0.420, 0.380)),
        ((0.050, 0.600, 0.350), (0.050, 0.520, 0.350), (0.050, 0.440, 0.380)),
        ((0.300, 0.620, 0.150), (0.150, 0.550, 0.220), (0.060, 0.440, 0.340)),
        ((0.380, 0.340, 0.260), (0.340, 0.300, 0.260), (0.300, 0.270, 0.240)),
        (0.040, 0.075, 0.062), (0.970, 1.000, 0.990)),
    # Frambuesa: rosas y magentas.
    "frambuesa": _p(
        ((1.000, 0.400, 0.600), (1.000, 0.250, 0.450), (0.850, 0.200, 0.550)),
        ((1.000, 0.550, 0.550), (1.000, 0.350, 0.500), (0.900, 0.250, 0.600)),
        ((0.750, 0.300, 0.350), (0.700, 0.280, 0.380), (0.620, 0.260, 0.400)),
        ((0.750, 0.120, 0.350), (0.780, 0.080, 0.300), (0.620, 0.050, 0.380)),
        ((0.780, 0.200, 0.250), (0.820, 0.100, 0.300), (0.660, 0.060, 0.400)),
        ((0.660, 0.200, 0.240), (0.600, 0.180, 0.280), (0.540, 0.160, 0.300)),
        (0.078, 0.050, 0.062), (1.000, 0.980, 0.990)),
    # Violeta: púrpuras.
    "violeta": _p(
        ((0.700, 0.500, 1.000), (0.550, 0.350, 1.000), (0.850, 0.400, 0.950)),
        ((0.850, 0.550, 1.000), (0.700, 0.400, 1.000), (0.950, 0.350, 0.850)),
        ((0.600, 0.400, 0.650), (0.550, 0.370, 0.600), (0.480, 0.340, 0.550)),
        ((0.450, 0.220, 0.800), (0.350, 0.150, 0.780), (0.600, 0.180, 0.720)),
        ((0.550, 0.250, 0.800), (0.420, 0.150, 0.780), (0.650, 0.120, 0.680)),
        ((0.480, 0.260, 0.500), (0.420, 0.220, 0.460), (0.360, 0.200, 0.420)),
        (0.060, 0.050, 0.085), (0.990, 0.980, 1.000)),
}

# Paleta activa (dicta la fija desde dicta.py al arrancar y en caliente).
_PALETTE = {"name": "grafito"}


def set_palette(name):
    """Fija la paleta de la isla; nombre desconocido -> 'grafito'."""
    key = str(name or "").strip().lower()
    _PALETTE["name"] = key if key in PALETTES else "grafito"


def _palette():
    return PALETTES.get(_PALETTE["name"], PALETTES["grafito"])


# Geometría de la isla: colgando del borde SUPERIOR (arriba recto, abajo
# SUPERIOR (área de trabajo), tamaño fijo y onda centrada.
ISLAND_H = 36
ISLAND_RADIUS = 18
ISLAND_PAD = 16
ISLAND_SHADOW = 9              # margen de la ventana para la sombra (px)
ISLAND_SHADOW_A = 0.0          # sin sombra (el autor la quitó)
ISLAND_SHADOW_A_LIGHT = 0.0    # sin sombra (el autor la quitó)
_ISLAND_SHADOW = (0.02, 0.02, 0.03)        # sombra: oscura, no un halo claro
_ISLAND_SHADOW_LIGHT = (0.05, 0.05, 0.07)
ISLAND_WAVE_W = 96              # 9 cápsulas: 6 de ancho con 5 de hueco
ISLAND_N_BARS = 9
# Forma: True = colgando del borde superior (arriba recto, abajo redondeado);
# False = píldora flotante con las cuatro esquinas redondas. Ahora depende de
# la POSICIÓN elegida (`island_pos`): arriba cuelga del borde (arriba recto),
# abajo es una píldora flotante con las cuatro esquinas redondas.
ISLAND_SQUARE_TOP = True        # (obsoleto: la verdad la da _square_top())
ISLAND_TOP_GAP = 0              # pegada al borde SUPERIOR (área de trabajo)
ISLAND_BOTTOM_GAP = 10          # separada del borde INFERIOR del área de trabajo

# Posición de la isla: "top" (colgando del borde superior; la tarjeta crece
# hacia abajo) o "bottom" (píldora flotante sobre el borde inferior; la tarjeta
# crece hacia arriba). El cuerpo va pegado al borde del fotograma que toca la
# pantalla y el margen de la sombra queda del lado opuesto.
_ISLAND_POS = {"name": "top"}


def set_position(name):
    """Fija la posición de la isla: 'top' | 'bottom' (por defecto 'top')."""
    _ISLAND_POS["name"] = ("bottom" if str(name or "").strip().lower() == "bottom"
                           else "top")


def _square_top():
    """True si la isla cuelga del borde superior (esquinas de arriba rectas)."""
    return _ISLAND_POS["name"] == "top"


def _at_top():
    return _ISLAND_POS["name"] == "top"


def round_window_corners(widget, radius=2):
    """Redondea una ventana sin bordes con la API DWM de Windows 11.
    radius: 0=default, 1=do not round, 2=round, 3=round small."""
    if os.name != "nt":
        return False
    try:
        hwnd = ctypes.windll.user32.GetParent(widget.winfo_id()) or widget.winfo_id()
        DWMWA_WINDOW_CORNER_PREFERENCE = 33
        pref = ctypes.c_int(radius)
        res = ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, DWMWA_WINDOW_CORNER_PREFERENCE, ctypes.byref(pref),
            ctypes.sizeof(pref))
        return res == 0
    except Exception:
        return False


def _sd_box(x, y, cx, cy, hw, hh):
    """SDF con signo de un rectángulo alineado a ejes (negativo dentro)."""
    qx = np.abs(x - cx) - hw
    qy = np.abs(y - cy) - hh
    return np.sqrt(np.maximum(qx, 0.0) ** 2 + np.maximum(qy, 0.0) ** 2) \
        + np.minimum(np.maximum(qx, qy), 0.0)


_SCENE = {}          # geometría estática cacheada por tamaño (w, h, radius)


def _scene(w, h, radius, bw=None, bh=None):
    """Rejilla, SDF y máscara del cuerpo: constantes en cada fotograma.

    La rampa de anti-alias se escala con el DPI: 1 px LÓGICO, no 1 px físico.
    A 200 % un borde de 1 px físico se ve escalonado; con 2 px se ve liso."""
    bw = float(bw if bw else w)
    bh = float(bh if bh else h)
    at_top = _square_top()
    key = (w, h, radius, bw, bh, at_top)
    sc = _SCENE.get(key)
    if sc is None:
        ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
        x, y = xs + 0.5, ys + 0.5
        # Coordenadas DENTRO del cuerpo: el fotograma tiene margen para la
        # sombra en el lado CONTRARIO al borde de la pantalla. Arriba: el cuerpo
        # va pegado al borde superior del fotograma y el margen queda abajo.
        # Abajo: se voltea — el cuerpo pegado al borde inferior del fotograma y
        # el margen arriba (si no, la sombra saldría del lado equivocado).
        xv = x - (w - bw) / 2.0
        yv = y                                 # el cuerpo siempre arriba del fotograma
        r = float(radius)
        if at_top:
            # Colgando del borde: esquinas de arriba rectas (el cuerpo nace del
            # borde) y las de abajo redondeadas, intersectando la banda
            # inferior redondeada con una banda superior recta. Esa banda se
            # pasa 2 px POR ENCIMA del fotograma: si el canto cae justo en el
            # borde de la ventana, el antialias deja una línea translúcida
            # pegada al borde de la pantalla.
            # Intersección de SDF = max (con min sería la unión, y entonces el
            # redondeo no llegaría a las esquinas de abajo).
            recto = _sd_box(xv, yv, bw / 2.0, bh / 2.0, bw / 2.0, bh / 2.0)
            # Redondeado que sobresale r por ARRIBA del fotograma: así sus
            # esquinas redondas quedan fuera y solo redondean las de abajo.
            redondo = _sd_box(xv, yv, bw / 2.0, (bh - r) / 2.0,
                              bw / 2.0 - r, (bh - r) / 2.0) - r
            d_shape = np.maximum(recto, redondo)
        else:
            d_shape = _sd_box(xv, yv, bw / 2.0, bh / 2.0,
                              bw / 2.0 - r, bh / 2.0 - r) - r
        ramp = max(1.0, r / 17.0)              # ≈ escala DPI (ISLAND_RADIUS=17)
        mask = np.clip((0.5 * ramp - d_shape) / ramp, 0.0, 1.0)
        _SCENE.clear()
        _SCENE[key] = sc = {"x": x, "y": y, "xs": xs, "mask": mask, "d": d_shape,
                            "ramp": ramp, "body_top": 0.0}
    return sc


def render_island_rgba(w, h, wave, wave_w, radius, grad, light, phase=0.0,
                       body_w=None, body_h=None, body_dark=None,
                       body_light=None):
    """Un fotograma de la isla en BGRA premultiplicada (h, w, 4) uint8.

    Geometría cacheada y un único composite de las 9 cápsulas. El cuerpo es
    SÓLIDO en ambos temas, sin bordes y sin efectos 3D: se modela con un
    subtrazo interior muy tenue. La onda es plana y limpia (color + una luz
    vertical sutil) con un glow aditivo ACOTADO. La rampa de anti-alias se
    escala con el DPI para que los bordes no se vean escalonados. El color del
    cuerpo lo puede fijar la paleta (`body_dark`/`body_light`)."""
    sc = _scene(w, h, radius, body_w, body_h)
    bw = float(body_w if body_w else w)
    bh = float(body_h if body_h else h)
    x, y, mask, d_shape = sc["x"], sc["y"], sc["mask"], sc["d"]
    ramp = sc["ramp"]
    body_top = float(sc.get("body_top", 0.0))

    if light:
        body_rgb = body_light if body_light is not None else _ISLAND_BODY_LIGHT
    else:
        body_rgb = body_dark if body_dark is not None else _ISLAND_BODY
    body = np.asarray(body_rgb, np.float32)
    out_c = np.empty((h, w, 3), np.float32)
    # Premultiplicado desde el principio: fuera del cuerpo no puede quedar su
    # color con alfa 0, porque cualquier cosa que se componga encima (la sombra)
    # se mezclaría con él. En tema claro eso hacía que la sombra saliera clara.
    out_c[:] = body * mask[..., None]
    out_a = mask.copy()

    n = len(wave)
    if n:
        pad = max((bw - wave_w) / 2.0, 4.0) + (w - bw) / 2.0
        slot = wave_w / n
        bw = slot * 0.58
        bh_min = bw                            # silencio = punto redondo
        cy = body_top + bh / 2.0
        max_h = bh - max(6.0, bh * 0.22)
        sigma = max(bh, 1.0) * 0.35
        span = bw / 2.0 + sigma * 2.5
        x0 = max(int(pad - span), 0)
        x1 = min(int(pad + wave_w + span) + 1, w)
        sx = x1 - x0
        wl = sc["xs"][0, x0:x1] + 0.5
        ycol = sc["y"][:, 0] - 0.0             # (h,) — luz vertical 1D
        mask_s = mask[:, x0:x1]
        qy = np.abs(y[:, x0:x1] - cy)
        sl = (slice(None), slice(x0, x1))

        # Campo de color continuo a lo ancho de la onda (3 paradas). Al cubrir
        # TODAS las columnas, el glow y el eco nunca leen color sin definir.
        a0, a1, a2 = (np.asarray(c, np.float32) for c in grad)
        tt = np.clip((wl - pad) / max(wave_w, 1e-6), 0.0, 1.0)[..., None]
        colf = np.where(tt < 0.5, a0 + (a1 - a0) * (tt / 0.5),
                        a1 + (a2 - a1) * ((tt - 0.5) / 0.5)).astype(np.float32)[None]

        cov_all = np.zeros((h, sx), np.float32)
        illum = np.zeros((h, sx), np.float32)
        halo = np.zeros((h, sx), np.float32)
        for i, lvl in enumerate(wave):
            lvl = float(min(1.0, max(0.0, lvl)))
            bh = bh_min + (max_h - bh_min) * lvl
            rr = min(bw / 2.0, bh / 2.0)
            cx = pad + slot * (i + 0.5)
            qx_f = np.abs(wl - cx) - (bw / 2.0 - rr)
            qy_f = qy - (bh / 2.0 - rr)
            ox = np.maximum(qx_f[None, :], 0.0)
            oy = np.maximum(qy_f, 0.0)
            dist = np.sqrt(ox * ox + oy * oy) \
                + np.minimum(np.maximum(qx_f[None, :], qy_f), 0.0) - rr

            # Cobertura con la MISMA rampa AA que el cuerpo (lisa a 200 %).
            cov = mask_s * np.clip((0.5 * ramp - dist) / ramp, 0.0, 1.0)
            cov_all = np.maximum(cov_all, cov)

            # Halo por polinomio (≈ exp a ±0.08) en vez de np.exp.
            t = np.clip(1.0 - np.maximum(dist, 0.0) / (3.0 * sigma), 0.0, 1.0)
            halo += (t * t) * (1.0 - halo)      # unión: nunca satura

            # Luz PLANA y sutil (sin gloss/rim 3D): algo más claro arriba.
            vn_y = (cy - ycol) / (0.5 * bh)
            key = np.clip(0.5 + 0.5 * vn_y, 0.0, 1.0)[:, None]
            lit = 0.82 + 0.18 * key
            illum = np.maximum(illum, cov * lit)

        # Un solo composite para las nueve cápsulas.
        a = cov_all[..., None]
        out_c[sl] = colf * illum[..., None] + out_c[sl] * (1.0 - a)
        out_a[sl] = cov_all + out_a[sl] * (1.0 - cov_all)

        # Glow aditivo acotado y discreto.
        gmax = 0.075 if light else 0.055
        out_c[sl] += np.minimum(gmax, 0.08 * halo)[..., None] * colf

    # Cuerpo sin bordes: subtrazo interior superior + viñeta inferior (horneados).
    plate = sc.get("plate_l" if light else "plate_d")
    if plate is None:
        band = np.clip(1.0 - np.abs(d_shape + 1.0), 0.0, 1.0) * mask
        top = np.clip((body_top + bh * 0.46 - y) / (bh * 0.46), 0.0, 1.0)
        fade = np.clip((w * 0.5 - np.abs(x - w * 0.5)) / (w * 0.34), 0.0, 1.0)
        sheen_pl = band * top * fade
        vy = np.clip((y - (body_top + bh * 0.50)) / (bh * 0.50), 0.0, 1.0)
        vx = np.clip((np.abs(x - w * 0.5) - w * 0.20) / (w * 0.30), 0.0, 1.0)
        plate = (sheen_pl, vy * vx * mask)
        sc["plate_l" if light else "plate_d"] = plate
    sheen_pl, vig = plate
    out_c += (sheen_pl * (0.06 if light else 0.07))[..., None]
    out_c *= (1.0 - (0.02 if light else 0.12) * vig)[..., None]

    # Sombra suave de separación: fuera del cuerpo, de los lados y por abajo.
    # Arriba no hay (la isla nace del borde de la pantalla). El SDF la hace caer
    # con la distancia, así que no es una línea: un halo que se apaga.
    borde_sh = ISLAND_SHADOW * ramp
    # OJO: `clip(d, 0, borde)` vale lo mismo en el canto y DENTRO del cuerpo, así
    # que sin esta máscara la sombra se pinta también encima de la isla y se come
    # la onda (pasó: 40 % sobre todo el cuerpo).
    fuera = (d_shape > 0.0).astype(np.float32)
    t = np.clip(d_shape, 0.0, borde_sh) / borde_sh
    # Perfil smoothstep: entra y sale sin escalones (con una potencia se veían
    # bandas, que es justo lo que hace que parezca barato).
    perfil = 1.0 - t * t * (3.0 - 2.0 * t)
    # Pesa más abajo: una sombra de elevación no es simétrica. Arriba queda el
    # 55 %, abajo el 100 %.
    # Peso hacia ABAJO siempre (una sombra no se proyecta hacia arriba): arriba
    # pesa más abajo del pil y en la posición de abajo también, así no aparece
    # ningún manchón por encima.
    yrel = (y - body_top) / bh
    ynorm = np.clip(yrel, 0.0, 1.0)
    peso = 0.55 + 0.45 * ynorm
    tope = (ISLAND_SHADOW_A_LIGHT if light else ISLAND_SHADOW_A)
    sh = perfil * peso * tope * fuera
    if sh.max() > 0.002:
        col_sh = np.asarray(_ISLAND_SHADOW_LIGHT if light else _ISLAND_SHADOW,
                            np.float32)
        sbb = sh[..., None]
        out_c = col_sh * sbb + out_c * (1.0 - sbb)
        out_a = sh + out_a * (1.0 - sh)

    # Invariante de premultiplicado: nunca color > alfa (evita motas brillantes).
    out_c = np.minimum(out_c, out_a[..., None])
    bgra = np.empty((h, w, 4), np.uint8)
    bgra[..., 0] = np.clip(out_c[..., 2] * 255.0, 0, 255)   # B
    bgra[..., 1] = np.clip(out_c[..., 1] * 255.0, 0, 255)   # G
    bgra[..., 2] = np.clip(out_c[..., 0] * 255.0, 0, 255)   # R
    bgra[..., 3] = np.clip(out_a * 255.0, 0, 255)            # A
    return bgra


def _patch_optional_tray_filter():
    """pystray optionally whitelists WM_TASKBARCREATED for Explorer restarts.
    Some Windows runtimes deny that optional filter call; the tray icon itself
    still works, so tolerate only ERROR_ACCESS_DENIED for this notification."""
    global _TRAY_FILTER_PATCHED
    if _TRAY_FILTER_PATCHED or os.name != "nt":
        return
    import pystray._win32 as win32_backend
    api = win32_backend.win32
    original = api.ChangeWindowMessageFilterEx

    def safe_filter(*args):
        try:
            return original(*args)
        except OSError as exc:
            if getattr(exc, "winerror", None) == 5:
                return False
            raise

    api.ChangeWindowMessageFilterEx = safe_filter
    _TRAY_FILTER_PATCHED = True


def make_tray_image(size=64):
    """Icono de la bandeja: renderizador nuevo si está, si no el de respaldo.

    ``dicta_icon.render_icon(size, variant="mark", bg=False)`` es la marca de
    la identidad (la misma onda que la isla). Si el módulo no existe todavía
    o falla al renderizar, se cae al dibujo propio sin romper nada: el icono
    de bandeja no puede ser un requisito para que dicta arranque.
    """
    size = int(size)
    try:
        import dicta_icon
        # El degradado y el halo tienen que seguir el tema: en una barra de
        # tareas CLARA, el degradado del tema oscuro se queda en ~1,6:1.
        img = dicta_icon.render_icon(
            size, variant="mark", bg=False,
            theme=("light" if _is_light() else "dark"))
        if img is not None:
            return img if img.mode == "RGBA" else img.convert("RGBA")
    except Exception:
        pass
    return _tray_image_fallback(size)


def _tray_image_fallback(size=64):
    """Dibujo de respaldo del icono (no depende de ``dicta_icon``)."""
    size = int(size)
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for i in range(size // 2):
        t = i / (size // 2)
        r = int(0x5B + (0x9B - 0x5B) * t)
        g = int(0x9D + (0x7B - 0x9D) * t)
        b = 0xFF
        d.ellipse([i, i, size - 1 - i, size - 1 - i],
                  outline=(r, g, b, 255), width=1)
    bars = [0.35, 0.7, 1.0, 0.6, 0.85]
    bw = max(2, size // 9)
    gap = (size - len(bars) * bw) // (len(bars) + 1)
    x = gap
    cy = size // 2
    for f in bars:
        h = int(f * size * 0.42)
        d.rounded_rectangle([x, cy - h, x + bw, cy + h], radius=bw // 2,
                            fill=(255, 255, 255, 235))
        x += bw + gap
    return img


class Tray:
    """Icono de bandeja. Los callbacks llegan en un hilo de pystray y solo
    encolan acciones para el hilo de Tk."""

    def __init__(self, on_event, snapshot):
        self.on_event = on_event
        self.snapshot = snapshot      # callable -> dict(mics=[], mic=, model=)
        self.icon = None

    def _menu(self):
        snap = self.snapshot() or {}

        def model_item(name):
            def cb(_icon, _item):
                self.on_event(("model", name))
            return pystray.MenuItem(name, cb, radio=True,
                                    checked=lambda _item, n=name: n == snap.get("model"))

        def mic_item(idx, label):
            def cb(_icon, _item):
                self.on_event(("mic", idx))
            return pystray.MenuItem(label, cb, radio=True,
                                    checked=lambda _item, i=idx: i == snap.get("mic"))

        def theme_item(name):
            def cb(_icon, _item):
                self.on_event(("theme", name))
            return pystray.MenuItem(name.title(), cb, radio=True,
                                    checked=lambda _item, n=name:
                                    n == snap.get("theme", "dark"))

        def sensitivity_item(value):
            def cb(_icon, _item):
                self.on_event(("sens", value))
            return pystray.MenuItem(f"{value:.1f}", cb, radio=True,
                                    checked=lambda _item, v=value:
                                    abs(v - snap.get("sens", 1.0)) < 0.05)

        def engine_item(name):
            def cb(_icon, _item):
                self.on_event(("engine", name))
            labels = {"auto": "Automático", "vulkan": "GPU Vulkan",
                      "cuda": "GPU CUDA", "cpu": "CPU"}
            return pystray.MenuItem(labels.get(name, name), cb, radio=True,
                                    checked=lambda _item, n=name:
                                    n == snap.get("engine", "auto"))

        mics = [mic_item(i, f"{i}: {n[:30]}") for i, n in snap.get("mics", [])]
        if not mics:
            mics = [pystray.MenuItem("(sin micrófonos)", None, enabled=False)]

        engine_names = snap.get("engines", ["auto", "cpu"])

        return pystray.Menu(
            pystray.MenuItem("Abrir panel de ajustes",
                             lambda _i, _it=None: self.on_event("open_panel"),
                             default=True),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Modelo", pystray.Menu(*[model_item(n)
                                                      for n in MODEL_NAMES])),
            pystray.MenuItem("Motor", pystray.Menu(*[engine_item(n)
                                                     for n in engine_names])),
            pystray.MenuItem("Micrófono", pystray.Menu(*mics)),
            pystray.MenuItem("Sensibilidad", pystray.Menu(*[
                sensitivity_item(value) for value in
                (0.5, 0.8, 1.0, 1.2, 1.5, 2.0, 2.5)])),
            pystray.MenuItem("Apariencia", pystray.Menu(
                theme_item("dark"), theme_item("light"))),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Salir", lambda _i, _it=None: self.on_event("quit")),
        )

    def start(self):
        _patch_optional_tray_filter()

        def run():
            try:
                self.icon = pystray.Icon("dicta", make_tray_image(),
                                         "dicta — dictado por voz", self._menu())
                self.icon.run()
            except Exception as e:
                print(f"dicta tray error: {e!r}", flush=True)
                traceback.print_exc()
                self.icon = None

        threading.Thread(target=run, daemon=True, name="dicta-tray").start()

    def refresh(self):
        try:
            if self.icon:
                self.icon.update_menu()
        except Exception:
            pass

    def stop(self):
        try:
            if self.icon:
                self.icon.stop()
        except Exception:
            pass


_DPI = {"scale": 1.0}          # factor de la pantalla (1 = 100 %, 2 = 200 %)

# Tema de la UI sincronizado desde dicta (set_theme); la isla lo lee en su
# hilo y converte el cristal más degradados según claro/oscuro.
_UI_THEME = {"name": "dark"}


def set_theme(name):
    """Fija el tema de la interfaz (dicta llama esto al cambiar Apariencia)."""
    _UI_THEME["name"] = "light" if name == "light" else "dark"


def _is_light():
    return _UI_THEME["name"] == "light"


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


class IslandWindow(_LayeredBase):
    """Isla nativa: cáscara FINA sobre ``dicta_layered.LayeredWindow``.

    Aquí no hay Win32 propio. ``LayeredWindow`` ya declara los prototipos de
    64 bits, registra la clase de ventana, crea el DIB midiendo EXACTAMENTE lo
    que mide el fotograma, lo recrea si el tamaño cambia, lo libera bajo
    cerrojo (dejando ``_bits = None``, la carrera que reventaba en ``memmove``)
    y reafirma TOPMOST. Lo único que aporta esta clase es el CONTENIDO: la onda
    de la isla, fotograma a fotograma, desde ``render_island_rgba``.

    ``click_through=True``: la isla no roba clics (WS_EX_TRANSPARENT).
    """

    def __init__(self, overlay, x, y, w, h, radius):
        if _SHELL_OK:
            super().__init__(int(w), int(h), int(x), int(y),
                             click_through=True, title="dicta-isla")
        else:                                          # pragma: no cover
            self.w, self.h = int(w), int(h)
            self.x, self.y = int(x), int(y)
            self.hwnd = 0
            self.diag = "dicta_layered no disponible"
            self._dib_size = (0, 0)
        self.ov = overlay
        self.radius = int(radius)
        self._interval = 1.0 / 60.0        # redibuja a 60 fps mientras se ve
        self._t_prev = time.monotonic()

    # ---- ciclo de vida: la interfaz que consume VoiceOverlay
    def open(self):
        """Arranca la isla (idempotente: si ya vive, solo la vuelve a mostrar)."""
        if not _SHELL_OK:                              # pragma: no cover
            log("IslandWindow: dicta_layered no disponible")
            return False
        return self.start()

    def hide(self):
        if _SHELL_OK:
            super().hide()

    def destroy(self):
        if _SHELL_OK:
            self.stop()

    # ---- contenido
    def render(self):
        """Un fotograma BGRA premultiplicado con forma ``(h, w, 4)`` uint8.

        Aquí vive la animación: el nivel sigue la voz con constantes de tiempo
        reales (``dt`` medido, no un fps supuesto) para que sea estable aunque
        el bucle de dibujo se atrase. ``render_island_rgba`` ya devuelve los
        bytes en BGRA premultiplicado, así que no hay que recomponer nada.
        """
        ov = self.ov
        now = time.monotonic()
        dt = min(max(now - self._t_prev, 0.0), 0.1)
        self._t_prev = now
        busy = ov._state == "transcribing"
        gone = ov._state == "cancelled"
        if gone:
            # Progreso del barrido de cancelación (~0.45 s).
            if not getattr(ov, "_cancel_active", False):
                ov._cancel_active = True
                ov._cancel_p = 0.0
            ov._cancel_p = min(1.0, float(getattr(ov, "_cancel_p", 0.0))
                               + dt / 0.45)
        else:
            ov._cancel_active = False
        target_lvl = min(1.0, max(0.0, (float(ov._rms) / 0.035) ** 0.65))
        tau = 0.045 if target_lvl > ov._level else 0.20
        ov._level += (target_lvl - ov._level) * (1.0 - np.exp(-dt / tau))
        ov._phase += dt * (1.8 if busy else 2.4 + 2.8 * ov._level)
        light = _is_light()
        pal = _palette()
        if gone:
            grad = pal["cancel_l"] if light else pal["cancel"]
        elif busy:
            grad = pal["trans_l"] if light else pal["trans"]
        else:
            grad = pal["listen_l"] if light else pal["listen"]
        wave = ov._wave_shape()
        return render_island_rgba(self.w, self.h, wave, ov._island_w_px(),
                                 self.radius, grad, light, ov._phase,
                                 ov.BODY_W, ov.BODY_H,
                                 body_dark=pal["body"], body_light=pal["body_l"])


class VoiceOverlay:
    """Isla (Dynamic Island) en la parte inferior central.

    Toda la superficie tiene bordes redondos y no toca el borde inferior.
    Sin texto: la propia onda lo dice. Al escuchar corre un degradado frío
    (teal → azul → violeta) y al transcribir uno cálido (ámbar → coral → rosa),
    con la amplitud y la velocidad siguiendo la voz. Tamaño SIEMPRE fijo; la
    transcripción aparece en una tarjeta redondeada debajo. Render a resolución
    física con anti-alias analítico: 1 px de imagen = 1 px del monitor."""

    FRAME_MS = 16
    PANEL_MAX_W = 620
    WRAP = 540
    MAX_TEXT = 220

    def __init__(self, root):
        try:
            _DPI["scale"] = max(1.0, float(root.winfo_fpixels("1i")) / 96.0)
        except Exception:
            _DPI["scale"] = 1.0
        s = self.s = _DPI["scale"]
        self.SH = round(ISLAND_SHADOW * s)       # margen para la sombra
        self.BODY_H = round(ISLAND_H * s)        # alto del cuerpo
        self.R = round(ISLAND_RADIUS * s)
        self.PAD = round(ISLAND_PAD * s)
        self.WW = round(ISLAND_WAVE_W * s)
        self.BODY_W = self.PAD * 2 + self.WW     # ancho del cuerpo
        # La ventana lleva el cuerpo + el margen de la sombra (a los lados y
        # por abajo; por arriba no, que nace del borde de la pantalla).
        self.W = self.BODY_W + self.SH * 2
        self.H = self.BODY_H + self.SH

        # La muesca es una ventana nativa con alpha por píxel: cristal
        # semitransparente de verdad y bordes redondos con AA analítico.
        self._island = None

        # Tarjeta de transcripción justo debajo de la isla; sigue el tema.
        self.panel = tk.Toplevel(root)
        self.panel.overrideredirect(True)
        self.panel.attributes("-topmost", True)
        try:
            self.panel.attributes("-alpha", 0.94)
        except Exception:
            pass
        self.panel_label = tk.Label(
            self.panel, text="", anchor="center", justify="center",
            wraplength=round(self.WRAP * s),
            font=("Segoe UI", 12), padx=round(16 * s), pady=round(10 * s))
        self.panel_label.pack(fill="both", expand=True)
        self._card_style()
        self.panel.withdraw()

        self._visible = False
        self._panel_shown = False
        self._phase = 0.0
        self._last_tick = time.monotonic()
        self._render_job = None
        self._text = ""
        self._state = "idle"
        self._wave = (0.0,) * 160
        self._bands = np.zeros(ISLAND_N_BARS, np.float32)   # espectro suavizado
        self._level = 0.0                                  # volumen suavizado
        self._rms = 0.0
        self._island_x = 0

    # ---- geometría que la ventana nativa consulta en su hilo
    def _island_w_px(self):
        return self.WW

    def _card_style(self):
        """Tono de la tarjeta de transcripción según el tema (unificado con
        el cuerpo de la isla: grafito #0E0F13 / blanco)."""
        light = _is_light()
        bg = "#ffffff" if light else "#0e0f13"
        fg = _CARD_TEXT_LIGHT if light else _CARD_TEXT
        self.panel.configure(bg=bg)
        self.panel_label.configure(bg=bg, fg=fg)

    def refresh_theme(self):
        self._card_style()

    def refresh_palette(self):
        """La paleta la lee el bucle de dibujo en cada fotograma; basta con
        pedir un redibujado inmediato para que se aplique en caliente."""
        try:
            if self._island is not None:
                self._island.invalidate()
        except Exception:
            pass

    def apply_position(self):
        """Recoloca la isla tras cambiar de posición (arriba <-> abajo).

        Cambia el anclaje, el lado del margen de la sombra y la forma del
        cuerpo, así que la ventana se recrea: destruir + volver a mostrar."""
        was = self._visible
        self.hide()
        if self._island is not None:
            self._island.destroy()
            self._island = None
        if was:
            self.show(self._text, self._state)

    # ---- mostrar / ocultar
    def show(self, text="", state="recording"):
        self._state = state
        self._text = text or ""
        try:
            sw = self.panel.winfo_screenwidth()
            self._island_x = (sw - self.W) // 2
            self._island_y = self._top_y() if _at_top() else self._bottom_y()
            if not self._visible:
                self._visible = True
                self._phase = 0.0
                self._last_tick = time.monotonic()
                self._bands[:] = 0.0
                self._level = 0.0
                if self._island is None:
                    # IslandWindow es una cáscara sobre dicta_layered.LayeredWindow:
                    # trae los prototipos de 64 bits, el DIB con cerrojo y
                    # click_through para no robar clics.
                    self._island = IslandWindow(self, self._island_x,
                                              self._island_y,
                                              self.W, self.H, self.R)
                self._island.open()
            elif self._island is not None:
                self._island.set_pos(self._island_x, self._island_y)
            self._set_text(self._text)
        except Exception:
            pass

    def _top_y(self):
        """Y de la isla: pegada al borde SUPERIOR del área de trabajo.

        Va arriba (como la isla de un móvil) para que se vea de reojo sin tapar
        lo que estás leyendo abajo, que es donde está el contenido. Se mide
        sobre el área de trabajo real (SPI_GETWORKAREA = 0x0030) y no sobre el
        alto de la pantalla, así respeta una barra de tareas puesta arriba.
        """
        gap = round(ISLAND_TOP_GAP * self.s)
        if os.name != "nt":
            return gap
        if _shell is not None:
            try:
                wa = _shell.work_area()
                return max(0, int(wa[1]) + gap)
            except Exception:
                pass
        return gap

    def _bottom_y(self):
        """Y de la isla: píldora flotante sobre el borde INFERIOR del área de
        trabajo, separada ~10 px (ISLAND_BOTTOM_GAP). Se mide sobre el área de
        trabajo real (SPI_GETWORKAREA), así respeta una barra de tareas abajo.
        El cuerpo va pegado al borde INFERIOR del fotograma, de modo que la
        ventana mide lo mismo que arriba pero el ancla se calcula desde abajo."""
        gap = round(ISLAND_BOTTOM_GAP * self.s)
        if os.name != "nt":
            return gap
        if _shell is not None:
            try:
                wa = _shell.work_area()
                return max(0, int(wa[3]) - gap - self.BODY_H)
            except Exception:
                pass
        return gap

    def hide(self):
        self._visible = False
        if self._island is not None:
            self._island.hide()
        self._hide_panel()

    def close(self):
        """Destruye la ventana nativa (al salir de la app)."""
        if self._island is not None:
            self._island.destroy()
            self._island = None
        self._hide_panel()

    def set_text(self, text):
        self._text = text
        self._set_text(text)

    def draw(self, rms, state, wave_data=()):
        self._state = state
        self._rms = float(rms or 0.0)
        if wave_data:
            self._wave = wave_data

    # ---- animación
    def _wave_shape(self):
        """Onda orgánica que SIEMPRE viaja, con la voz dando la amplitud.

        Tres senos con desfase por barra + un bulto que recorre la fila: en
        silencio queda una fila de puntos vivos y al hablar crece y acelera.
        El espectro del micro solo añade matiz (normalizado)."""
        n = ISLAND_N_BARS
        idx = np.arange(n, dtype=np.float32)
        if self._state == "cancelled":
            # Barrido de cancelación: cada barra colapsa a un punto cuando el
            # frente (progreso 0→1) la alcanza, de izquierda a derecha.
            p = float(getattr(self, "_cancel_p", 1.0))
            keep = np.clip(1.0 - (p * (n + 1.5) - idx), 0.0, 1.0)
            return (0.06 + 0.42 * keep * (1.0 - p)).astype(np.float32)
        if self._state == "transcribing":
            lvl = 0.62
        else:
            src = np.asarray(self._wave[-8:], dtype=np.float32)
            if src.size < 8:
                src = np.pad(src, (8 - src.size, 0))
            tgt = np.interp(np.linspace(0.0, 7.0, n), np.arange(8.0), src)
            tgt = np.clip(tgt / 0.05, 0.0, 1.0) ** 0.75
            self._bands += (tgt - self._bands) * 0.22
            lvl = 0.14 + 0.86 * self._level
        base = (0.46
                + 0.32 * np.sin(self._phase * 2.6 - idx * 0.78)
                + 0.22 * np.sin(self._phase * 4.1 + idx * 1.25 + 1.05)
                + 0.12 * np.sin(self._phase * 6.6 - idx * 1.75 + 2.15))
        # Bulto que recorre la fila de izquierda a derecha (viaje visible).
        env = 0.76 + 0.24 * np.cos(2.0 * np.pi * (idx + 0.5) / n
                                   - 0.50 * self._phase)
        amp = 0.10 + 0.95 * lvl
        bn = np.clip(self._bands / (float(self._bands.max()) + 1e-3), 0.15, 1.0)
        shape = 0.68 + 0.32 * bn
        wave = amp * env * base * shape
        return np.clip(wave, 0.06, 1.0).astype(np.float32)

    # ---- tarjeta de transcripción
    def _set_text(self, text):
        content = (text or "").strip()
        if not content:
            self._hide_panel()
            return
        s = self.s
        tail = content if len(content) <= self.MAX_TEXT else "…" + content[-(self.MAX_TEXT - 1):]
        try:
            self.panel_label.config(text=tail)
            self.panel.update_idletasks()
            w = min(max(self.panel_label.winfo_reqwidth()
                        + round(32 * s), round(220 * s)),
                    round(self.PANEL_MAX_W * s))
            h = self.panel_label.winfo_reqheight() + round(20 * s)
            cx = self._island_x + self.W // 2
            x = cx - w // 2
            gap = round(8 * s)
            if _at_top():
                # Colgando arriba: la tarjeta crece hacia ABAJO, justo debajo.
                y = self._island_y + self.BODY_H + gap
            else:
                # Píldora abajo: la tarjeta crece hacia ARRIBA, justo encima.
                # El cuerpo nace en `_island_y + SH` (margen de la sombra arriba).
                y = self._island_y + self.SH - gap - h
            self.panel.geometry(f"{w}x{h}+{x}+{y}")
            round_window_corners(self.panel, 2)
            if sys.platform.startswith("win"):
                try:
                    hwnd = ctypes.windll.user32.GetParent(self.panel.winfo_id())
                    rr = round(18 * self.s)
                    rgn = ctypes.windll.gdi32.CreateRoundRectRgn(0, 0, w + 1, h + 1,
                                                                 rr, rr)
                    ctypes.windll.user32.SetWindowRgn(hwnd, rgn, True)
                except Exception:
                    pass
            if not self._panel_shown:
                self.panel.deiconify()
                self.panel.lift()
                self._panel_shown = True
        except Exception:
            pass

    def _hide_panel(self):
        if self._panel_shown:
            try:
                self.panel.withdraw()
            except Exception:
                pass
            self._panel_shown = False

