#!/usr/bin/env python3
"""dicta_icon - identidad iconica de dicta.

La marca del icono es **sobria y geometrica**, como el resto de la interfaz de
la app: **un solo azul de acento**, formas simples, **trazo uniforme** y mucho
espacio negativo. Nada de degradados arcoiris ni de piezas troceadas.

Azulejo (se conserva tal cual, es lo que funciona): **OPACO** en todas partes
--blanco puro #FFFFFF en tema claro, grafito #0E0F13 en oscuro-- con esquinas
muy redondeadas y un **filo de luz** en lugar de un borde (mismo principio que
el cuerpo de la isla). La marca se dibuja a 8x y se reduce (anti-alias limpio) y
se recorta contra el azulejo, para que no asome por las esquinas redondeadas.

API publica (NO cambiar estas firmas; dicta.py y el panel las llaman tal cual):

    render_icon(size, variant="app", theme="dark", bg=True)  -> PIL.Image RGBA
    official_image(size, theme="light")    # el render oficial (bandeja, .exe)
    ico_render(size, theme="dark")         # idem, para el .ico y la ventana
    make_tray_image(size=64, theme=None)   # idem, para la bandeja
    write_ico(path, sizes, theme, variant)
    wave_mark(size, bars, light, level, phase)   # onda de la isla (isla/ui)
    icon_mark(size, bars, light)                 # marca del icono (oficial)
    verify(path) / build_sheet(path)

CUATRO PROPUESTAS. Cada una es su PROPIA funcion y dibuja un RGBA transparente
de size x size con su marca; `render_mark(nombre, size, theme)` la compone
sobre el azulejo. Para cambiar la oficial basta UNA linea: ``OFFICIAL_PROPOSAL``.

    1) mark_d_solid   - D solida y minimalista con una onda fina integrada.
    2) mark_d_stroke  - D de trazo uniforme y redondeado (solo contorno).
    3) mark_wave_bars - onda de barras de alturas limpias, en un solo color.
    4) mark_d_wave    - la inicial y la onda combinadas de forma geometrica.

`build_proposal_sheets()` escribe en .tmp/ la hoja comparativa (las 4 propuestas
a 16/32/64/128 px en claro y oscuro) y la hoja de detalle (cada una a 32 px
ampliada).
"""

import io
import os

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFont

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ICO_PATH = os.path.join(SCRIPT_DIR, "dicta.ico")

_GRAPHITE = (14, 15, 19)          # #0E0F13
_WHITE = (255, 255, 255)
_RIM_DARK = (255, 255, 255, 46)   # alfa medido: con 30 el azulejo desaparece
                                  # sobre una barra de tareas oscura
_RIM_LIGHT = (0, 0, 0, 34)

# UN solo acento: el token --accent de DESIGN.md (claro #0066CC / oscuro #5B9DFF).
# El azul de accion es el mismo en toda la app; en oscuro se aclara porque
# #0066CC sobre grafito #0E0F13 no llega a contraste de grafico.
_ACCENT_LIGHT = (0, 102, 204)     # #0066CC
_ACCENT_DARK = (91, 157, 255)     # #5B9DFF

ICON_BARS = 5                     # barras de la onda (propuesta 3)

# --- geometria del trazo de la letra -------------------------------------
_D_SOLID = 0.26   # trazo grueso y uniforme: la D se lee como una masa solida
_D_THIN = 0.140   # trazo fino y uniforme: contorno de la letra con aire
_D_MED = 0.175    # trazo medio (inicial + onda)


def _accent(light=False):
    """El azul de acento del tema (claro #0066CC / oscuro #5B9DFF)."""
    return _ACCENT_LIGHT if light else _ACCENT_DARK


def _d_geometry(size):
    """(alto, ancho) de la marca como fraccion del lado del azulejo.

    A tallas pequenas la marca ocupa mas: es lo unico que la hace legible a
    16-20 px. A tallas grandes vuelve a una proporcion de letra (mas alta que
    ancha) para dejar aire alrededor.
    """
    if size <= 20:
        return 0.88, 0.84
    if size <= 36:
        return 0.82, 0.80
    return 0.76, 0.78


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


# --------------------------------------------------- el trazo de la letra D
def _d_shape(big, mh, mw, tw, rw, stem_round=0.16):
    """Mascara L del trazo de la D: cuenco (elipse) + tallo, menos la
    contraforma.

    El contorno exterior es un tallo recto (izquierda) unido a una elipse
    (cuenco). La contraforma tiene **borde izquierdo recto** (el tallo) y
    **derecho curvo** (media elipse): es la contraforma de una D, no la de una
    O, y es lo que hace que la letra se lea como D a todas las tallas. Con
    ``tw == rw`` el trazo es **uniforme**; el grosor del trazo se elige con ese
    valor (fino = contorno, grueso = masa solida).
    """
    x0 = (big - mw) / 2.0
    y0 = (big - mh) / 2.0
    x1 = x0 + mw
    y1 = y0 + mh
    solid = Image.new("L", (big, big), 0)
    ds = ImageDraw.Draw(solid)
    ds.ellipse([x0, y0, x1, y1], fill=255)           # cuenco
    rr = min(tw, mh) * stem_round                   # esquina exterior suave
    ds.rounded_rectangle([x0, y0, x0 + tw, y1], radius=rr, fill=255)  # tallo

    xl = x0 + tw
    xr = x1 - rw
    cy = (y0 + y1) / 2.0
    ry = mh / 2.0 - tw
    rx = (xr - xl) / 2.0
    xc = xl + rx
    counter = Image.new("L", (big, big), 0)
    dc = ImageDraw.Draw(counter)
    dc.rectangle([xl, cy - ry, xc, cy + ry], fill=255)          # borde recto
    dc.ellipse([xc - rx, cy - ry, xc + rx, cy + ry], fill=255)  # curva derecha
    return ImageChops.subtract(solid, counter)


def _sine_cut_mask(big, mh, amp=0.20, thick=0.115, periods=1.0):
    """Mascara L de una **onda fina** horizontal (un seno) por el centro.

    Es la onda de voz integrada en la letra: se resta del trazo y deja una
    linea limpia que recorre la D. Al reducir, a 16 px desaparece sola y la
    letra se sigue leyendo como una D solida (degrada con elegancia).
    """
    mask = Image.new("L", (big, big), 0)
    d = ImageDraw.Draw(mask)
    cy = big / 2.0
    pts = []
    steps = 96
    for i in range(steps + 1):
        t = i / float(steps)
        pts.append((t * big, cy + np.sin(t * 2.0 * np.pi * periods) * mh * amp))
    d.line(pts, fill=255, width=int(max(1, mh * thick)), joint="curve")
    for p in (pts[0], pts[-1]):
        r = max(1, int(mh * thick / 2.0))
        d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=255)
    return mask


# ------------------------------------------------------- propuesta 1
def mark_d_solid(size, bars=ICON_BARS, light=False):
    """**D solida y minimalista** con una onda fina integrada.

    La letra es una masa solida de azul de acento (trazo grueso y uniforme) y
    una onda fina del color del azulejo la recorre a media altura: la voz esta
    *dentro* de la inicial, sin trocearla. A 16 px la onda desaparece y queda
    una D nitida.
    """
    hf, wf = _d_geometry(size)
    # Por debajo de 28 px la onda fina no tiene pixeles para leerse (se ve como
    # una grieta): la letra se queda SOLIDA y nitida, que es lo que a esa talla
    # pide una barra de tareas. De 28 px en adelante aparece la onda.
    cut = int(size) >= 28

    def mask(big):
        mh = big * hf
        sw = mh * _D_SOLID
        shape = _d_shape(big, mh, mh * wf, sw, sw)
        if not cut:
            return shape
        return ImageChops.subtract(shape, _sine_cut_mask(big, mh))

    return _mark_from_mask(size, mask, _accent(light))


# ------------------------------------------------------- propuesta 2
def mark_d_stroke(size, bars=ICON_BARS, light=False):
    """**D de trazo uniforme y redondeado**.

    Solo el contorno de la letra, con el mismo grosor en el tallo y en el
    cuenco y las esquinas exteriores suavizadas. La contraforma queda grande:
    mucho aire, cero ruido. Es la variante mas ligera y mas de sistema.
    """
    hf, wf = _d_geometry(size)

    def mask(big):
        mh = big * hf
        sw = mh * _D_THIN
        return _d_shape(big, mh, mh * wf, sw, sw, stem_round=0.45)

    return _mark_from_mask(size, mask, _accent(light))


# ------------------------------------------------------- propuesta 3
def mark_wave_bars(size, bars=ICON_BARS, light=False):
    """**Onda de barras de alturas limpias**, en un solo color.

    Capsulas verticales de anchura y hueco uniformes, alturas simetricas
    (perfil de coseno: la del centro manda) y un unico azul de acento. Es la
    onda de la bandeja, sin degradado y sin el troceado de la marca anterior.
    Por debajo de 40 px van 3 barras mas gruesas (con 5 no habria hueco) y por
    debajo de 28 px la geometria es entera y sin reescalado, para que a 16 px
    las barras caigan en la rejilla de pixeles y no se emborronen.
    """
    size = int(size)
    if size <= 0:
        return Image.new("RGBA", (1, 1), (0, 0, 0, 0))
    n = max(1, int(bars) if size >= 40 else 3)
    col = _accent(light) + (255,)
    if size < 28:
        # Tallas de barra de tareas: geometria ENTERA y sin reescalado. El
        # supermuestreo daria bordes suaves que, a 2 px de barra, embarran el
        # hueco; aqui cada barra cae en la rejilla de pixeles y se ve nitida.
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        bw = max(1, int(round(size * 0.72 / (n + (n - 1) * 0.85))))
        gap = max(1, int(round(bw * 0.85)))
        total = n * bw + (n - 1) * gap
        x0 = int(round((size - total) / 2.0))
        cy = size / 2.0
        maxh = size * 0.68
        c = (n - 1) / 2.0
        for i in range(n):
            u = abs(i - c) / max(1.0, c)
            hh = max(2, int(round(maxh * (0.45 + 0.55
                                           * np.cos(u * np.pi / 2.0)))))
            x = x0 + i * (bw + gap)
            top = int(round(cy - hh / 2.0))
            d.rectangle([x, top, x + bw - 1, top + hh - 1], fill=col)
        return img
    # De 28 px en adelante: como el resto de la marca, a 8x y se reduce
    # (anti-alias limpio), y de 40 px en adelante 5 barras (a menos no hay
    # hueco).
    ss = 8 if size <= 96 else 4
    big = size * ss
    avail = big * 0.72
    bw = avail / (n + (n - 1) * 0.85)
    gap = bw * 0.85
    total = n * bw + (n - 1) * gap
    x0 = (big - total) / 2.0
    cy = big / 2.0
    maxh = big * 0.68
    c = (n - 1) / 2.0
    img = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for i in range(n):
        u = abs(i - c) / max(1.0, c)
        hh = maxh * (0.45 + 0.55 * np.cos(u * np.pi / 2.0))
        x = x0 + i * (bw + gap)
        top, bot = cy - hh / 2.0, cy + hh / 2.0
        d.rounded_rectangle([x, top, x + bw - 1, bot],
                            radius=(bw - 1) / 2.0, fill=col)
    return img.resize((size, size), Image.LANCZOS)


# ------------------------------------------------------- propuesta 4
def mark_d_wave(size, bars=3, light=False):
    """**La inicial y la onda, combinadas de forma geometrica**.

    El contorno de la D (trazo uniforme, como la propuesta 2) con una onda de
    3 barras **alojada dentro de la contraforma**: la misma anchura de trazo y
    el mismo azul, alineada con la letra. La inicial enmarca la voz.
    """
    hf, wf = _d_geometry(size)
    # A menos de 28 px las barras de dentro se fundirian con el trazo: la letra
    # se queda sola (degrada a la propuesta 2, que es limpia a esa talla).
    n = max(1, int(bars)) if int(size) >= 28 else 0

    def mask(big):
        mh = big * hf
        mw = mh * wf
        sw = mh * _D_MED
        shape = _d_shape(big, mh, mw, sw, sw, stem_round=0.40)
        if not n:
            return shape
        x0 = (big - mw) / 2.0
        xl, xr = x0 + sw, x0 + mw - sw
        cy = big / 2.0
        ry = mh / 2.0 - sw
        avail = (xr - xl) * 0.70
        bw = max(1.0, avail / (n + (n - 1) * 0.8))
        gap = bw * 0.8
        total = n * bw + (n - 1) * gap
        x = xl + ((xr - xl) - total) / 2.0
        layer = Image.new("L", (big, big), 0)
        dl = ImageDraw.Draw(layer)
        c = (n - 1) / 2.0
        for i in range(n):
            u = abs(i - c) / max(1.0, c)
            hh = 2.0 * ry * 0.62 * (0.45 + 0.55 * np.cos(u * np.pi / 2.0))
            top = cy - hh / 2.0
            if bw <= 2.2:
                dl.rectangle([x, top, x + bw - 1, top + hh], fill=255)
            else:
                dl.rounded_rectangle([x, top, x + bw - 1, top + hh],
                                     radius=(bw - 1) / 2.0, fill=255)
            x += bw + gap
        return ImageChops.lighter(shape, layer)

    return _mark_from_mask(size, mask, _accent(light))


# ------------------------------------------------------------ las propuestas
PROPOSALS = {
    "d_solid": mark_d_solid,
    "d_stroke": mark_d_stroke,
    "wave_bars": mark_wave_bars,
    "d_wave": mark_d_wave,
}
PROPOSAL_ORDER = ("d_solid", "d_stroke", "wave_bars", "d_wave")

# >>> cambiar la marca oficial es cambiar ESTA linea <<<
OFFICIAL_PROPOSAL = "wave_bars"


def icon_mark(size, bars=ICON_BARS, light=False):
    """**La marca del icono** (la propuesta oficial) sobre lienzo transparente.

    Devuelve un RGBA de ``size`` x ``size``. Es el MISMO dibujo en bandeja,
    .ico, ventana del panel y favicon, porque todos salen de aqui.

    ``bars`` se conserva por compatibilidad de firma (la onda de la propuesta 3
    lo usa; las de letra lo ignoran).
    """
    return PROPOSALS[OFFICIAL_PROPOSAL](int(size), light=light)


def render_mark(name, size, theme="dark"):
    """Icono de UNA propuesta sobre el azulejo opaco.

    Sirve para las hojas comparativas y para previsualizar una propuesta sin
    tocar la oficial.
    """
    size = int(max(8, size))
    light = theme == "light"
    img = _tile(size, theme, alpha=255)
    mark = PROPOSALS[name](size, light=light)
    mark.putalpha(ImageChops.multiply(mark.split()[3], img.split()[3]))
    img.alpha_composite(mark, (0, 0))
    return img


def render_icon(size, variant="app", theme="dark", bg=True):
    """Icono como PIL.Image RGBA del tamano pedido (la propuesta oficial).

    ``variant`` y ``bg`` se conservan por compatibilidad de firma: el azulejo es
    opaco (alfa 255) SIEMPRE --blanco puro en tema claro, grafito en oscuro--
    asi que bandeja, .exe, ventana y favicon no pueden divergir.

    La marca se **recorta contra el azulejo** (se multiplica su alfa por la del
    azulejo): sin el recorte asomaria por las esquinas redondeadas.
    """
    return render_mark(OFFICIAL_PROPOSAL, size, theme)


def official_image(size, theme="light"):
    """El render OFICIAL de dicta sobre el azulejo **opaco** (blanco puro en
    claro), exactamente lo que dibuja la bandeja.

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
# Se conserva tal cual: la isla (y cualquier consumidor existente) sigue
# obteniendo la misma onda ancha con degradado. El ICONO ya no la usa.
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
def write_ico(path=ICO_PATH, sizes=(16, 24, 32, 48, 64, 128, 256),
              theme="dark", variant="mark"):
    """Escribe el .ico multirresolucion, redibujando CADA tamano.

    Se construye el contenedor a mano: el plugin ICO de Pillow no respeta una
    lista de imagenes ya dibujadas (reducia todo al primer tamano), y aqui cada
    talla tiene que dibujarse con su propia geometria. Formato ICO con PNG
    embebido, que Windows Vista+ lee a cualquier tamano y conserva el alfa.
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
def _label_font(px):
    for p in (r"C:/Windows/Fonts/segoeui.ttf", r"C:/Windows/Fonts/arial.ttf"):
        try:
            return ImageFont.truetype(p, px)
        except Exception:                        # noqa: BLE001
            pass
    return ImageFont.load_default()


def _paste(sheet, im, x, y, bg):
    if im.mode != "RGBA":
        im = im.convert("RGBA")
    cell = Image.new("RGB", im.size, bg)
    cell.paste(im, (0, 0), im)
    sheet.paste(cell, (x, y))


def build_comparativa(path=None):
    """Hoja comparativa: una fila por propuesta y tema, con la marca a 16, 32,
    64 y 128 px (ampliada por un factor entero con NEAREST, para juzgar la
    legibilidad real; la de 128 va a tamano real, 1:1)."""
    path = path or os.path.join(SCRIPT_DIR, ".tmp",
                                "icon_propuestas_comparativa.png")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    font, font_s = _label_font(15), _label_font(13)
    sizes = (16, 32, 64, 128)
    scale = {16: 6, 32: 4, 64: 2, 128: 1}
    pad, label_w, header_h = 16, 330, 28
    col_x, x = {}, label_w + pad
    for s in sizes:
        col_x[s] = x
        x += s * scale[s] + pad
    width = x
    row_h = 128 + pad
    rows = [(n, t) for n in PROPOSAL_ORDER for t in ("light", "dark")]
    height = header_h + row_h * len(rows) + pad
    sheet = Image.new("RGB", (width, height), (48, 48, 54))
    d = ImageDraw.Draw(sheet)
    d.text((pad, 6),
           "dicta - propuestas de icono (azul de acento, azulejo opaco)",
           fill=(255, 255, 255), font=font)
    for s in sizes:
        d.text((col_x[s] + 2, 6), "%dpx" % s, fill=(198, 198, 206), font=font_s)
    y = header_h
    for name, theme in rows:
        bg = (242, 242, 245) if theme == "light" else (20, 20, 24)
        d.rectangle([0, y, label_w - pad, y + row_h - pad], fill=(36, 36, 42))
        d.text((pad, y + 30), "%d) %s" % (PROPOSAL_ORDER.index(name) + 1, name),
               fill=(255, 255, 255), font=font)
        d.text((pad, y + 54),
               "tema %s%s" % ("claro" if theme == "light" else "oscuro",
                              "  * OFICIAL" if name == OFFICIAL_PROPOSAL else ""),
               fill=(150, 196, 255), font=font_s)
        for s in sizes:
            img = render_mark(name, s, theme)
            if scale[s] != 1:
                img = img.resize((s * scale[s], s * scale[s]), Image.NEAREST)
            _paste(sheet, img, col_x[s], y + (row_h - pad - s * scale[s]) // 2,
                   bg)
        y += row_h
    sheet.save(path)
    return path


def build_detalle(path=None):
    """Hoja de detalle: cada propuesta a 32 px ampliada 10x (NEAREST), en claro
    y en oscuro."""
    path = path or os.path.join(SCRIPT_DIR, ".tmp",
                                "icon_propuestas_detalle32.png")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    font, small = _label_font(15), _label_font(13)
    detail, zoom, pad, label_h = 32, 10, 20, 30
    cs = detail * zoom
    names = PROPOSAL_ORDER
    themes = ("light", "dark")
    width = pad + len(names) * (cs + pad)
    height = label_h * 2 + pad + len(themes) * (label_h + cs + pad)
    sheet = Image.new("RGB", (width, height), (48, 48, 54))
    d = ImageDraw.Draw(sheet)
    d.text((pad, 8), "dicta - detalle de cada propuesta a 32 px (x10)",
           fill=(255, 255, 255), font=font)
    for r, theme in enumerate(themes):
        for c, name in enumerate(names):
            x = pad + c * (cs + pad)
            y = label_h * 2 + pad + r * (label_h + cs + pad)
            bg = (242, 242, 245) if theme == "light" else (20, 20, 24)
            d.text((x, y - label_h + 6),
                   "%d) %s - %s" % (c + 1, name,
                                    "claro" if theme == "light" else "oscuro"),
                   fill=(255, 255, 255), font=small)
            img = render_mark(name, detail, theme)
            _paste(sheet, img.resize((cs, cs), Image.NEAREST), x, y, bg)
    sheet.save(path)
    return path


def build_proposal_sheets():
    """Escribe las dos hojas de .tmp/ y devuelve (comparativa, detalle)."""
    return build_comparativa(), build_detalle()


def build_sheet(path=None):
    """Hoja de comprobacion de la marca OFICIAL: ampliado por tamano, los dos
    temas, y a tamano real."""
    path = path or os.path.join(SCRIPT_DIR, "assets", "_icon_check.png")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    zooms = (16, 24, 32, 48)
    rows = [("oscuro", (24, 24, 28)), ("claro", (242, 242, 245))]
    pad, label_w, scale = 14, 92, 6
    cw = sum(s * scale + pad for s in zooms) + pad
    rh = max(zooms) * scale + pad * 2
    real_w = sum(s + 12 for s in (16, 24, 32, 48, 64, 128)) + 32
    sheet = Image.new("RGB", (max(label_w + cw, label_w + real_w),
                              pad + rh * len(rows) + 96), (128, 128, 132))
    d = ImageDraw.Draw(sheet)
    y = pad
    for theme, bgc in rows:
        d.text((pad, y + 4), theme, fill=(255, 255, 255))
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
    for s in (16, 24, 32, 48, 64, 128):
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
    print("oficial:", OFFICIAL_PROPOSAL)
    print("escrito:", out)
    print("tamanos en el .ico:", sizes, "| todos cuadrados:", allsquare)
    comp, det = build_proposal_sheets()
    print("comparativa:", comp)
    print("detalle:", det)
    print("hoja oficial:", build_sheet())
    for name in PROPOSAL_ORDER:
        print("-- %s" % name)
        for s in (16, 20, 32, 64, 128):
            a = np.asarray(render_mark(name, s, "dark"))
            op = int((a[:, :, 3] > 200).sum())
            h = hashlib.sha1(a.tobytes()).hexdigest()[:8]
            print("  %3dpx  sha=%s opacos=%6d/%d" % (s, h, op, s * s))
