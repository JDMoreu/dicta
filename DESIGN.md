# DESIGN.md — Dicta

Sistema visual de Dicta. Un solo acento recorre la app: **azul de acción**.
La onda de voz usa la misma familia (frío al escuchar, cálido al procesar).
Principio: **sólido, sin bordes, minimal**. La forma se delimita con luz, no
con trazos.

## Tokens

| Token | Oscuro | Claro |
|---|---|---|
| `--bg` | `#141418` | `#F2F2F5` |
| `--surface` | `#1C1C1F` | `#FFFFFF` |
| `--surface-2` | `#26262A` | `#F5F5F7` |
| `--text` | `#F5F5F7` | `#1D1D1F` |
| `--text-2` | `#B6B6BF` | `#52525A` |
| `--text-3` | `#94949E` | `#6E6E73` |
| `--line` | `rgba(255,255,255,.09)` | `rgba(0,0,0,.10)` |
| `--accent` | `#5B9DFF` | `#0066CC` |
| `--accent-soft` | `#16294A` | `#E8F1FE` |
| `--accent-tx` | `#0B1220` | `#FFFFFF` |
| `--ok` | `#30D158` | `#2E7D32` |
| `--warn` | `#FF9F0A` | `#B25000` |
| `--err` | `#FF453A` | `#D70015` |
| `--surface-3` | `#2F2F34` | `#EBEBEF` |
| `--line-2` | `rgba(255,255,255,.06)` | `rgba(0,0,0,.06)` |
| `--ok-sf` · `--warn-sf` · `--err-sf` | `#12291A` · `#2C2113` · `#2E1517` | `#E7F3E9` · `#FBEFE1` · `#FCE8EA` |

Contraste AA verificado en todas las parejas texto/superficie (≥4.5:1) y en los
acentos sobre su superficie (≥3:1 gráfico).

Seis pasos tipográficos (`--fs-display` 22, `--fs-title` 16, `--fs-row` 14,
`--fs-body` 13, `--fs-secondary` 12, `--fs-micro` 11) y cuatro duraciones
(`--t-micro` 120, `--t-fast` 180, `--t-base` 240, `--t-slow` 320 ms) con tres
curvas (`--ease-out`, `--ease-in`, `--ease-spring`). Las superficies de estado
(`-sf`) existen porque el blanco sobre el verde/rojo de aviso no llega a AA.

## Onda de voz

Cuerpo de la isla **sólido** (grafito `#0E0F13` / blanco `#FFFFFF`), **sin
bordes**. La onda son 9 cápsulas planas (sin gloss ni 3D) con:

| Estado | Oscuro (3 paradas) | Claro (3 paradas) |
|---|---|---|
| Escuchando | `#3DD9C4` → `#5B9DFF` → `#9B7BFF` | `#0C917E` → `#1F7FE0` → `#6D46D6` |
| Transcribiendo | `#FFC24A` → `#FF7A6B` → `#FF5FA2` | `#C2760A` → `#D6402F` → `#C41E7A` |
| Cancelado | `#C24C4C` → `#B35266` → `#995478` | `#B82E33` → `#A8334D` → `#8F335C` |

Reglas de render (`dicta_ui.render_notch_rgba`):

- **1 px de imagen = 1 px físico** (proceso DPI-aware, `UpdateLayeredWindow`).
- **Anti-alias analítico con rampa escalada al DPI**: 1 px *lógico* (2 px a
  200 %). Una rampa de 1 px físico se ve escalonada en pantallas HiDPI.
- Luz plana: `lit = 0.82 + 0.18 * key` (algo más claro arriba). Sin brillos
  3D, sin eco, sin rim.
- Glow aditivo acotado (≤0.075 oscuro / ≤0.095 claro): realza color, no lava
  el cuerpo sólido.
- Premultiplicado: `out_c = min(out_c, out_a)` antes de BGRA.
- Geometría (SDF, máscara, rejilla) cacheada; un único composite de las 9
  barras. Presupuesto ~2.6–4 ms por fotograma (16 ms a 60 fps).

## Movimiento

- 9 cápsulas, tres senos con desfase por barra + un bulto que recorre la fila.
- Amplitud por nivel de voz (τ ataque 45 ms, caída 200 ms) → sube rápido, baja
  suave. En silencio quedan puntos redondos vivos.
- Al pegar el texto, la isla desaparece al instante. Al cancelar, colapsa a
  puntos con degradado rojo y se apaga en ~0.7 s.

## Interfaz

- Panel HTML/CSS (Chrome en modo aplicación, sin barra nativa del sistema: se
  elimina `WS_CAPTION` y se refuerza en cada tick).
- **Sin cabecera con marca**: el panel empieza DIRECTAMENTE en el raíl (el
  icono de la marca vive solo donde toca: ventana, bandeja y `.exe`). El tema
  se elige en Apariencia, en el segmentado claro/oscuro de la fila «Claro u
  oscuro» (sol ↔ luna, dos iconos y un pulgar deslizante).
- **Raíl de seis secciones** (Dictado, Diccionario, Reunión, Audios y
  documentos, Atajos de teclado, Apariencia) con el recuento de cada lista, y
  **filas agrupadas** dentro: azulejo de icono + título + ayuda, control a la
  derecha. Antes era una rejilla de tarjetas, y ocho bloques de «título + un
  control + aire» era justo lo que la hacía genérica: misma información, la
  mitad de alto y cada ajuste siempre en el mismo sitio.
- **42 iconos SVG en línea** (`ICONS` + `paintIcons()` en `app.js`), rejilla
  24×24 y trazo 1,8 — 2 por debajo de 18 px, la misma corrección óptica del
  icono de la app.
- Ninguna superficie se delimita con borde: filo de luz (`inset`) en oscuro y
  anillo *hairline* en claro, obligatorio porque el blanco sobre `#F2F2F5` está
  a 1,09:1.
- Arranque sin consola (`pythonw`); registro en `dicta.log`.

## La isla de dictado

**Cuerpo sólido** (grafito `#0E0F13` en oscuro, blanco en claro), **sin
bordes**: delimitar con luz y no con trazos. El aro de actividad late mientras
dictas. Es la **única** ventana flotante de la app: no hay burbuja ni panel
desplegable.

**Cuelga del borde superior** (no flota): esquinas de arriba rectas y las de
abajo redondeadas, para que se lea como una muesca del borde y no como una
pastilla suelta. La forma sale de intersectar (máximo de dos SDF) el
rectángulo recto con un rectángulo redondeado que sobresale por arriba del
fotograma; el redondeo solo afecta entonces a las esquinas de abajo.

| Medida | Valor | Por qué |
|---|---|---|
| Alto | 36 | a 34, arriba y sin barra de tareas que la ancle, se veía pequeña |
| Radio | 18 abajo · **0 arriba** | en el borde se lee como muesca |
| Relleno lateral | 16 | con 15 la onda tocaba el radio inferior |
| Onda | 96 (9 cápsulas de 6 con 5 de hueco) | a 84 el silencio parecía una raya |
| Ancho | 128 sin texto · hasta 440 con texto | el texto se recorta, nunca se parte |
| Distancia al borde | `y = work_area.top + 10` | respeta una barra de tareas arriba |

Medido sobre el fotograma a 100 %: esquina de arriba **0,97** (recta), de abajo
**0,00** (redondeada), 4470 píxeles opacos frente a 4332 de la variante
flotante. En pantalla: **128×36 centrada en x=960 sobre 1920**, a 10 px del
borde.

**Contraste (medido, no estimado).** Todo el texto pasa AA. Dos tokens del
sistema se corrigieron al medirlos: el texto sobre el acento **no es blanco en
oscuro** (blanco sobre `#5B9DFF` da 2,72:1; `--accent-tx` `#0B1220` da 6,88:1),
y el rojo/verde de estado **necesitan la variante clara** (`#D70015`, `#2E7D32`)
porque los del tema oscuro se quedan en 2,9:1 y 2,0:1 sobre blanco. El botón
secundario en tema claro lleva filo: su relleno está a 1,19:1 del fondo.

## Icono

La marca es **onda y cursor** (`dicta_icon.mark_wave_caret`): tres cápsulas de
voz en el azul de acento que terminan en un cursor de texto —la voz avanza hacia
el punto de inserción, que es lo que hace la app—. El cursor va en el neutro del
tema (`#F5F5F5` en oscuro, `#0A0A0A` en claro). Es asimétrica a propósito: así no
se lee como una onda genérica.

**Cada talla se redibuja**: por debajo de 28 px la geometría es entera y sin
reescalado, para que caiga en la rejilla de píxeles de la barra de tareas; de 28
a 47 px las barras y el cursor van más gruesos y sin remates; desde 48 px el
cursor lleva remates (I-beam). El `.ico` trae las tallas de los escalados de
Windows (16, 20, 24, 28, 32, 36, 40, 48, 56, 64, 96, 128 y 256) y la bandeja se
dibuja a `SM_CXSMICON` y se entrega 1:1: sin tallas exactas el sistema reescala
y el icono pierde nitidez. El azulejo es **opaco** —blanco puro en claro,
grafito `#0A0A0A` en oscuro, con filo de luz— y el mismo dibujo sirve a bandeja,
`.exe`, ventana del panel y favicon: no pueden divergir. La isla conserva
`dicta_icon.wave_mark` (su onda con degradado es movimiento, no marca).


## Referencias

- `DESIGN-apple.md` — análisis del sistema Apple usado como base de la paleta.
