#!/usr/bin/env python3
"""dicta_icon - identidad iconica de dicta.

La marca es **onda y cursor**: tres capsulas de voz en el azul de acento que
terminan en un cursor de texto. La voz avanza de izquierda a derecha y acaba en
el punto de insercion, que es exactamente lo que hace la app. Asimetrica a
proposito: asi no se confunde con una onda generica.

El azulejo es **opaco** y sigue el tema --blanco puro #FFFFFF en claro, grafito
#0A0A0A en oscuro-- con esquinas muy redondeadas y un **filo de luz** en lugar
de un borde (el mismo principio que el cuerpo de la isla). La marca se dibuja a
8x y se reduce (anti-alias limpio) y se recorta contra el azulejo, para que no
asome por las esquinas redondeadas.

El icono se **adapta a cada talla** (no es un unico PNG reescalado):

* 16-27 px: geometria entera y sin supermuestreo, para que caiga en la rejilla
  de pixeles y no se emborrone en la barra de tareas.
* 28-47 px: barras y cursor mas gruesos y sin remates.
* 48 px en adelante: cursor con remates (I-beam) y trazo mas fino.

El .ico trae las tallas de los escalados de Windows (125 %, 150 %, 175 %,
200 %): pedir una talla que no existe obliga al sistema a reescalar y ahi se
pierde la nitidez.

API publica (NO cambiar estas firmas; dicta.py, dicta_ui.py y el panel las
llaman tal cual):

    render_icon(size, variant="app", theme="dark", bg=True)  -> PIL.Image RGBA
    official_image(size, theme="light")    # el render oficial (bandeja, .exe)
    ico_render(size, theme="dark")         # idem, para el .ico y la ventana
    make_tray_image(size=64, theme=None)   # idem, para la bandeja
    write_ico(path, sizes, theme, variant)
    wave_mark(size, bars, light, level, phase)   # onda de la isla (isla/ui)
    icon_mark(size, bars, light)                 # marca del icono (oficial)
    verify(path) / build_sheet(path)

La isla conserva su propia onda (`wave_mark`): el icono es la version impresa
de la misma idea, no el mismo dibujo.
"""

import io
import os

import numpy as np
from PIL import Image, ImageChops, ImageDraw

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ICO_PATH = os.path.join(SCRIPT_DIR, "dicta.ico")

_GRAPHITE = (10, 10, 10)          # #0A0A0A (un punto bajo --bg #141418)
_WHITE = (255, 255, 255)
_RIM_DARK = (255, 255, 255, 46)   # alfa medido: con 30 el azulejo desaparece
                                  # sobre una barra de tareas oscura
_RIM_LIGHT = (0, 0, 0, 34)

# UN solo acento: el token --accent de DESIGN.md (claro #0066CC / oscuro #5B9DFF).
# El azul de accion es el mismo en toda la app; en oscuro se aclara porque
# #0066CC sobre grafito #0A0A0A no llega a contraste de grafico.
_ACCENT_LIGHT = (0, 102, 204)     # #0066CC
_ACCENT_DARK = (91, 157, 255)     # #5B9DFF

ICON_BARS = 3                     # barras de la marca del icono

# Cursor de la marca: casi blanco en oscuro (el --text del tema) y casi negro
# en claro.
_CARET_DARK = (245, 245, 245)     # #F5F5F5
_CARET_LIGHT = (10, 10, 10)       # #0A0A0A


def _accent(light=False):
    """El azul de acento del tema (claro #0066CC / oscuro #5B9DFF)."""
    return _ACCENT_LIGHT if light else _ACCENT_DARK


def _caret(light=False):
    """El color del cursor del tema (claro #0A0A0A / oscuro #F5F5F5)."""
    return _CARET_LIGHT if light else _CARET_DARK


def _tile(size, theme, alpha=255, ss=8):
    """Azulejo redondeado con filo de luz, dibujado a 8x y reducido.

    ``alpha=255`` por defecto: el azulejo es **opaco** (blanco puro en claro,
    grafito en oscuro). Con 165 el blanco se leia gris sobre una barra de
    tareas oscura.
    """
    light = theme == "light"
    big = int(size) * ss
    img = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    pad = max(1, int(big * 0.015))
    radius = big * 0.225
    body = _WHITE if light else _GRAPHITE
    d.rounded_rectangle([pad, pad, big - pad - 1, big - pad - 1],
                        radius=radius, fill=body + (int(alpha),))
    d.rounded_rectangle([pad, pad, big - pad - 1, big - pad - 1],
                        radius=radius,
                        outline=(_RIM_LIGHT if light else _RIM_DARK),
                        width=max(1, int(ss * 0.9)))
    return img.resize((int(size), int(size)), Image.LANCZOS)


def _mark_from_mask(size, mask_fn, color):
    """Pinta ``mask_fn(big)`` con ``color`` y reduce a ``size`` (anti-alias)."""
    size = int(size)
    if size <= 0:
        return Image.new("RGBA", (1, 1), (0, 0, 0, 0))
    ss = 8 if size <= 96 else 4
    big = size * ss
    mask = mask_fn(big)
    out = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    out.paste(Image.new("RGBA", (big, big), tuple(color) + (255,)), (0, 0),
              mask)
    return out.resize((size, size), Image.LANCZOS)


# ------------------------------------------------------------- la marca
# Proporciones (fraccion del lado) para la rejilla entera de < 28 px.
_CARET_BAR_H = (0.29, 0.53, 0.38)   # alturas de las 3 barras
_CARET_H = 0.62                     # altura del cursor
_CARET_GRID_MAX = 28                # por debajo: rejilla entera, sin reescalado


def _snap(v, size):
    """Entero con la misma paridad que ``size``: centra exacto en la rejilla."""
    h = int(round(v))
    if (int(size) - h) % 2:
        h += 1
    return max(h, 1 if int(size) % 2 else 2)


def mark_wave_caret(size, bars=ICON_BARS, light=False):
    """**Onda y cursor**: 3 barras de voz que terminan en un cursor de texto.

    La onda va en el azul de acento y el cursor en el neutro del tema (casi
    blanco en oscuro, casi negro en claro). La voz avanza de izquierda a derecha
    y acaba en el punto de insercion, que es lo que hace la app. Asimetrica a
    proposito: asi no se confunde con una onda generica.

    Tres geometrias, segun la talla: de 48 px en adelante el cursor lleva
    remates (I-beam); de 28 a 47 px, barras y cursor mas gruesos y sin remates;
    por debajo de 28 px, rejilla entera sin reescalado (anti-alias nulo).
    ``bars`` se conserva por compatibilidad de firma.
    """
    size = int(size)
    if size <= 0:
        return Image.new("RGBA", (1, 1), (0, 0, 0, 0))

    if size < _CARET_GRID_MAX:
        acc = _accent(light) + (255,)
        car = _caret(light) + (255,)
        # Reparto continuo: la marca ocupa ~70 % del lado en TODAS las tallas.
        # Antes cada pieza se redondeaba por su cuenta y a 20 px el conjunto se
        # quedaba en el 55 % del azulejo (se veia pequeno y pobre).
        unit = max(2.0, size * 0.70 / 5.5)
        bw = max(2, int(round(unit)))
        gap = max(1, int(round(unit * 0.55)))
        cg = max(2, int(round(unit * 0.82)))
        cw = max(1, int(round(unit * 0.55)))
        total = 3 * bw + 2 * gap + cg + cw
        x0 = (size - total) // 2
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        for i, f in enumerate(_CARET_BAR_H):
            hh = _snap(size * f, size)
            x = x0 + i * (bw + gap)
            top = (size - hh) // 2
            d.rectangle([x, top, x + bw - 1, top + hh - 1], fill=acc)
        hc = _snap(size * _CARET_H, size)
        xc = x0 + 3 * bw + 2 * gap + cg
        top = (size - hc) // 2
        d.rectangle([xc, top, xc + cw - 1, top + hc - 1], fill=car)
        return img

    full = size >= 48
    if full:
        xs, bw, hs = (30, 60, 90), 18, (48, 92, 64)
        sx, sw = 134, 8
    else:
        xs, bw, hs = (29, 63, 97), 22, (52, 96, 68)
        sx, sw = 139, 12

    def bars_mask(big):
        u = big / 180.0
        m = Image.new("L", (big, big), 0)
        d = ImageDraw.Draw(m)
        for x, h in zip(xs, hs):
            d.rounded_rectangle([x * u, (90 - h / 2.0) * u,
                                 (x + bw) * u - 1, (90 + h / 2.0) * u - 1],
                                radius=bw * u / 2.0, fill=255)
        return m

    def caret_mask(big):
        u = big / 180.0
        m = Image.new("L", (big, big), 0)
        d = ImageDraw.Draw(m)
        d.rounded_rectangle([sx * u, 34 * u, (sx + sw) * u - 1, 146 * u - 1],
                            radius=sw * u / 2.0, fill=255)
        if full:
            for y in (34, 140):
                d.rounded_rectangle([126 * u, y * u, 150 * u - 1,
                                     (y + 6) * u - 1],
                                    radius=3 * u, fill=255)
        return m

    wave = _mark_from_mask(size, bars_mask, _accent(light))
    caret = _mark_from_mask(size, caret_mask, _caret(light))
    return Image.alpha_composite(wave, caret)


def _compose(size, theme):
    """La marca oficial sobre el azulejo del tema (lo que ve Windows)."""
    size = int(max(8, size))
    light = theme == "light"
    img = _tile(size, theme, alpha=255)
    mark = mark_wave_caret(size, light=light)
    # Recorte contra el azulejo: sin esto la marca asomaria por las esquinas.
    mark.putalpha(ImageChops.multiply(mark.split()[3], img.split()[3]))
    img.alpha_composite(mark, (0, 0))
    return img


def icon_mark(size, bars=ICON_BARS, light=False):
    """La marca del icono sobre lienzo transparente.

    Devuelve un RGBA de ``size`` x ``size``. Es el MISMO dibujo en bandeja,
    .ico, ventana del panel y favicon, porque todos salen de aqui.
    """
    return mark_wave_caret(int(size), light=light)


def render_icon(size, variant="app", theme="dark", bg=True):
    """Icono como PIL.Image RGBA del tamano pedido (la marca oficial).

    ``variant`` y ``bg`` se conservan por compatibilidad de firma: el azulejo es
    opaco SIEMPRE --blanco puro en claro, grafito en oscuro-- asi que bandeja,
    .exe, ventana y favicon no pueden divergir.
    """
    return _compose(size, theme)


def official_image(size, theme="light"):
    """El render OFICIAL de dicta sobre el azulejo opaco (blanco puro en claro).

    Es EL MISMO dibujo en la bandeja, el icono de la ventana/barra de tareas,
    la barra del panel y el favicon: todos llaman aqui (o a
    ``ico_render``/``make_tray_image``, que delegan en esta funcion). Unico
    punto de entrada -> las superficies no pueden mostrar identidades distintas.
    """
    return render_icon(size, variant="mark", theme=theme, bg=False)


def ico_render(size, theme="dark"):
    """Mismo dibujo que el de la bandeja (``official_image``).

    El icono del .exe, el de la ventana del panel y el de la bandeja tienen que
    ser el MISMO: si divergen, la app ensena dos identidades distintas.
    """
    return official_image(size, theme=theme)


def make_tray_image(size=64, theme=None):
    """Icono de la bandeja: el render oficial del tema dado.

    ``theme=None`` devuelve el tema oscuro.
    """
    return official_image(int(size), theme or "dark")


# ------------------------------------------------------- onda de la isla
# La isla conserva su onda ancha con degradado: es movimiento, no marca.
_GRAD_DARK = ((61, 217, 196), (91, 157, 255), (155, 123, 255))
_GRAD_LIGHT = ((12, 145, 126), (31, 127, 224), (109, 70, 214))


def _grad_color(t, light=False):
    g = _GRAD_LIGHT if light else _GRAD_DARK
    t = min(1.0, max(0.0, t))
    if t <= 0.5:
        a, b, u = g[0], g[1], t / 0.5
    else:
        a, b, u = g[1], g[2], (t - 0.5) / 0.5
    return tuple(int(a[i] + (b[i] - a[i]) * u) for i in range(3))


def _wave_bars(size, n=5, light=False, level=0.0, phase=0.0,
               width=0.74, gap_ratio=1.35):
    """Marca de onda de la isla (barras redondeadas con degradado) sobre un
    lienzo RGBA transparente. La amplitud depende solo de la distancia al
    centro, asi que el simbolo es SIEMPRE simetrico."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if n % 2 == 0:
        n += 1
    bw = max(1, int(round(size * width / (n + (n - 1) * gap_ratio))))
    gap = max(1, int(round(bw * gap_ratio)))
    total = n * bw + (n - 1) * gap
    x0 = (size - total) / 2.0
    cy = size / 2.0
    c = (n - 1) / 2.0
    for i in range(n):
        k = abs(i - c) / max(1.0, c)
        prof = 0.46 + 0.54 * (1.0 - k)
        wob = 0.055 * np.sin(phase * 2.6 - k * 2.2)
        hh = size * (0.15 + 0.32 * prof * (1.0 + 0.60 * level)) * (1.0 + wob)
        hh = min(hh, size * 0.92)
        x = x0 + i * (bw + gap)
        col = _grad_color((i + 0.5) / n, light) + (255,)
        top, bot = cy - hh / 2.0, cy + hh / 2.0
        if bw <= 2:
            d.rectangle([x, top, x + bw - 1, bot], fill=col)
        else:
            d.rounded_rectangle([x, top, x + bw - 1, bot],
                                radius=(bw - 1) / 2.0, fill=col)
    return img


def wave_mark(size, bars=5, light=False, level=0.0, phase=0.0):
    """Onda de dicta (el simbolo de la isla): barras simetricas con degradado."""
    return _wave_bars(size, n=bars, light=light, level=level, phase=phase)


# ------------------------------------------------------------------- .ico
def write_ico(path=ICO_PATH,
              sizes=(16, 20, 24, 28, 32, 36, 40, 48, 56, 64, 96, 128, 256),
              theme="dark", variant="mark"):
    """Escribe el .ico multirresolucion, redibujando CADA tamano.

    La lista cubre las tallas que piden Windows y sus escalados (125 %, 150 %,
    175 %, 200 %): si la talla exacta no esta, el sistema reescala y el icono
    sale borroso. Se construye el contenedor a mano: el plugin ICO de Pillow no
    respeta una lista de imagenes ya dibujadas (reducia todo al primer tamano),
    y aqui cada talla tiene que dibujarse con su propia geometria. Formato ICO
    con PNG embebido, que Windows Vista+ lee a cualquier tamano y conserva el
    alfa.
    """
    import struct
    frames = []
    for s in sorted(sizes):
        img = ico_render(s, theme=theme)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        frames.append((int(s), buf.getvalue()))
    header = struct.pack("<HHH", 0, 1, len(frames))
    offset = 6 + 16 * len(frames)
    entries, blobs = b"", b""
    for s, data in frames:
        dim = 0 if s >= 256 else s            # 0 significa 256 en el formato
        entries += struct.pack("<BBBBHHII", dim, dim, 0, 0, 1, 32,
                               len(data), offset)
        offset += len(data)
        blobs += data
    with open(path, "wb") as fh:
        fh.write(header + entries + blobs)
    return path


def verify(path=ICO_PATH):
    """Tamanos que contiene el .ico y si todos son cuadrados."""
    im = Image.open(path)
    got = sorted(im.ico.sizes())
    return got, all(s[0] == s[1] for s in got)


# --------------------------------------------------------------- hojas
def build_sheet(path=None):
    """Hoja de comprobacion de la marca: ampliado por tamano, los dos temas y a
    tamano real (1:1). Es lo que se revisa antes de tocar el .ico."""
    path = path or os.path.join(SCRIPT_DIR, "assets", "_icon_check.png")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    zooms = (16, 20, 24, 32, 48)
    rows = [("dark", "oscuro", (24, 24, 28)),
            ("light", "claro", (242, 242, 245))]
    pad, label_w, scale = 14, 92, 6
    cw = sum(s * scale + pad for s in zooms) + pad
    rh = max(zooms) * scale + pad * 2
    real = (16, 20, 24, 28, 32, 40, 48, 64, 96, 128)
    real_w = sum(s + 12 for s in real) + 32
    sheet = Image.new("RGB", (max(label_w + cw, label_w + real_w),
                              pad + rh * len(rows) + 96), (128, 128, 132))
    d = ImageDraw.Draw(sheet)
    y = pad
    for theme, label, bgc in rows:
        d.text((pad, y + 4), label, fill=(255, 255, 255))
        x = label_w
        for s in zooms:
            cell = Image.new("RGB", (s * scale, s * scale), bgc)
            ic = ico_render(s, theme=theme).resize(
                (s * scale, s * scale), Image.NEAREST)
            cell.paste(ic, (0, 0), ic)
            sheet.paste(cell, (x, y))
            x += s * scale + pad
        y += rh
    d.text((pad, y + 12), "real", fill=(255, 255, 255))
    x = label_w
    for s in real:
        ic = ico_render(s, theme="dark")
        cell = Image.new("RGB", (s + 8, s + 8), (60, 60, 66))
        cell.paste(ic, (4, 4), ic)
        sheet.paste(cell, (x, y + 8))
        x += s + 12
    sheet.save(path)
    return path


if __name__ == "__main__":
    import hashlib
    out = write_ico()
    sizes, allsquare = verify(out)
    print("marca: onda y cursor (mark_wave_caret)")
    print("escrito:", out)
    print("tamanos en el .ico:", sizes, "| todos cuadrados:", allsquare)
    print("hoja oficial:", build_sheet())
    for s in (16, 24, 32, 48, 64, 128, 256):
        for theme in ("dark", "light"):
            a = np.asarray(ico_render(s, theme=theme))
            op = int((a[:, :, 3] > 200).sum())
            h = hashlib.sha1(a.tobytes()).hexdigest()[:8]
            print("  %3dpx %-5s sha=%s opacos=%6d/%d"
                  % (s, theme, h, op, s * s))
