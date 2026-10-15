# PREdiseño — dicta

Propuesta de UI y de la isla. **No toca el código de la app**: son cuatro ficheros en
`assets\prediseno\`, HTML/CSS/JS puro, sin dependencias ni red (`file://`).

| Fichero | Qué es |
|---|---|
| `diccionario.html` | Catálogo: color, tipografía, iconos, controles, filas, estados, movimiento. Cada pieza con su nombre y para qué se usa. |
| `panel.html` | Maqueta navegable de la ventana de ajustes (1040×820) con datos de ejemplo, tema claro/oscuro y es/en. |
| `isla.html` | La isla en el borde superior, sus 4 estados, la onda simulada en JS y la geometría acotada. |
| `PREDISENO.md` | Esto. |

## Decisiones

**1 · El panel deja de ser una tirada de tarjetas.** Lo genérico no eran los colores, era la
estructura: ocho bloques de «título + un control + aire» se leen como una plantilla. Van fuera; entran
un **raíl de secciones** (Dictado · Diccionario · Reunión · Audios · Documentos · Atajos · Apariencia,
con recuento) y, dentro, **filas de ajuste agrupadas**: azulejo de icono, título y ayuda, control a la
derecha. Misma información, la mitad de alto, todo a un clic y siempre en el mismo sitio.

**2 · Sin bordes, con luz.** DESIGN.md ya lo dice para la isla; se extiende a todo. Ningún
contenedor lleva `border`: oscuro usa filo de luz (`inset 0 1px 0 rgba(255,255,255,.05)`), claro un
anillo hairline `0 0 0 1px rgba(0,0,0,.045)` — obligatorio, porque blanco sobre `#F2F2F5` está a
1,09:1 y sin anillo desaparece. El *hover* de un relleno es `--surface-3`, nunca un borde que se
aclara. Tres elevaciones y ni una más: fila, grupo, y lo que flota (menú, bloque de captura).

**3 · Una escala, no siete tamaños.** Fuera el solape de 11/12/13/14 px: **6 pasos** (22/16/14/13/
12/11) con un trabajo cada uno. Cifras siempre tabulares (el temporizador no baila).

**4 · La isla cuelga del borde superior.** Es el cambio que más se ve y el que menos código toca.

## Color

Se mantienen los tokens de DESIGN.md. Añadidos: `--surface-3` (hover de relleno), `--ok-sf`,
`--warn-sf`, `--err-sf` (celdas de estado), `--line-2` como separador de fila. Contraste medido, no
estimado (`diccionario.html` lo recalcula en vivo): texto 15,6:1 / 16,8:1 · secundario 8,45 / 7,74 ·
ayuda 5,66 / 5,62 · acento 6,24 / 5,57 · ok 8,41 / 5,13 · aviso 8,27 / 5,20 · error 4,99 / 5,38.

**Dos correcciones que salen de medir:** el pill **REC** actual usa blanco sobre `--err` oscuro =
**3,41:1, por debajo de AA** (en el prediseño el fondo es `#D70015` en ambos temas → **5,38:1**), y el
botón destructivo en oscuro tampoco puede ir con `--err`.

## Iconos

SVG en línea, **sin fuente ni sprite**. Un mapa JS (`ICONS`) construye cada `<svg>` en el DOM; si un
icono no está en el mapa, no existe. Reglas: rejilla **24×24** con área viva 2…22, trazo **1,8**,
**2 por debajo de 18 px** (pierde peso al reducir; es la misma corrección óptica que ya hace
`dicta_icon.wave_mark`), extremos y uniones redondeados, sin relleno, `currentColor`.
Set de 42 por dominio: **identidad** `wave` · **audio** `mic`, `mic-off`, `globe`, `chip`, `layers`,
`gauge`, `speaker`, `monitor`, `window`, `file-audio` · **datos** `file-text`, `folder`, `book`,
`keyboard`, `users` · **acciones** `play`, `pause`, `stop`, `plus`, `x`, `check`, `trash`, `download`,
`upload`, `copy`, `refresh`, `search`, `sliders`, `power`, `external-link`, `zap`, `sparkle` ·
**interfaz** `sun`, `moon`, chevrons, `info`, `alert-triangle`, `dots-*`, `settings`.

## Movimiento

Cuatro duraciones y tres curvas para todo el producto. La entrada tarda más que la salida.

| Token | Valor | Para qué | Curva |
|---|---|---|---|
| `--t-micro` | 120 ms | hover, foco, color de relleno | `--ease-out` `.2,.8,.2,1` |
| `--t-fast` | 180 ms | chip que aparece, pulgar del interruptor | `--ease-spring` `.34,1.32,.44,1` |
| `--t-base` | 240 ms | cambio de sección, progreso, interruptor de tema | `--ease-out` |
| `--t-slow` | 320 ms | **solo la isla**: entrada y ensanchado hacia el texto | `--ease-spring` (rebote 3 %) |

De la isla: onda con **ataque 45 ms / caída 200 ms**, 9 cápsulas con tres senos desfasados más un
bulto que recorre la fila, y en silencio **puntos redondos vivos** (nunca una raya).
**No se anima**: el fondo al cambiar de tema (los tokens saltan de golpe y solo se mueve el pulgar:
evita el flash), el texto del panel, el ancho de un botón (el spinner va dentro) y la apertura del
panel. Nada en bucle salvo el punto de estado, el REC y la onda. `prefers-reduced-motion` las deja
en 0,01 ms con una sola regla. El pegado de texto **no** se anima: desaparece en el fotograma.

## La isla arriba

**Ya implementado:** `_top_y()` con `ISLAND_TOP_GAP = 10` y el `_island_y` del `show()`. Quedan dos
formas de rematar, no incompatibles pero hay que elegir: **A · flotando** (gap 10, pill completo) o
**B · colgando** (gap 0, esquinas superiores rectas). La maqueta muestra la B; la tabla es común salvo eso.

| Medida | Valor | Hoy | Por qué |
|---|---|---|---|
| Alto | 36 | 34 | a 34, arriba —donde no hay barra de tareas que la ancle— la cápsula se ve pequeña |
| Radio | 18 abajo · **0 arriba (B)** | 17 en las 4 (A) | en B la forma nace del borde y se lee como muesca, no como pastilla suelta |
| Relleno lateral | 16 | 15 | con 15 la onda toca el radio inferior |
| Onda | 9 cápsulas de 6 con 5 de hueco = 96 | 84 | a 84 el silencio parece una raya; a 96 la onda pesa como la del icono |
| Ancho mínimo | 128 (16+96+16) | 114 | es el estado «sin texto» |
| Ancho máximo | 440 (42 % de la ventana de 1040) | ~440 | el texto se recorta, nunca se parte en dos líneas |
| Distancia al borde | 0 → `y = work_area.top + gap` | gap 10 | con la barra de tareas arriba deja de ser 0 |
| Físico | ×DPI tras escalar | igual | 128 → 160 a 125 %, 192 a 150 % |

En **A** no hay que tocar el dibujo: el SDF ya es de un solo radio y todo lo demás es cambiar
constantes. En **B** el filo de luz pasa a ir solo en el contorno visible (abajo y costados, alpha 46
en oscuro) y el radio necesita dos valores. Comunes a las dos: sombra hacia abajo
(`0 12px 30px rgba(0,0,0,.34)`) y aro de actividad inset de 1 px de acento latiendo 0,12↔0,55.
Pantallas **< 1180 px lógicas**: ancho mínimo 112 y sin texto (solo la onda), para no ocupar el
centro. Varios monitores: se coloca en el del foco y se reposiciona al cambiar de monitor, no al
mostrar. La isla sigue siendo *click-through* (`WS_EX_TRANSPARENT` + `HTTRANSPARENT`): tapar la
barra de pestañas no impide pinchar en ella.

## Implementación, en orden

1. **Hecho.** `dicta_ui.py`: `_top_y()` sobre `work_area()[1] + gap`, `ISLAND_TOP_GAP = 10`; `island_x`
   sigue siendo `(sw - W) // 2` y centra en el monitor primario.
2. **`dicta_ui.py` — geometría.** `ISLAND_H 34→36`, `ISLAND_PAD 15→16`, `ISLAND_WAVE_W 84→96`
   (verificar las 9 cápsulas a 96: BAR_W 6, hueco 5). Esta parte se aplica a A y a B.
3. **`dicta_ui.py` — forma, solo si se elige B.** `_sd_box` da un solo radio. Para «arriba recto,
   abajo redondo», intersectar el rectángulo redondeado de la banda inferior con la banda superior
   recta: `d = min(sd_box(x, y, cx=w/2, cy=(h+r)/2, hw=w/2, hh=(h-r)/2) - r, sd_box(x, y, cx=w/2, cy=r/2, hw=w/2, hh=r/2))`.
   Probar a 100/125/150 % y en `light`/`dark`.
4. **`dicta_ui.py` — caché, solo si se elige B.** `_SCENE` tiene clave `(w, h, radius)`: con dos
   radios, dos fotogramas distintos colisionan. Meter la forma en la clave. En A no se toca.
5. **`DESIGN.md` / `README.md`.** La prosa ya habla del borde superior; queda la tabla de geometría y el
   docstring de `dicta_ui.py` si aún dice «borde inferior».
6. **`panel/`** — la parte grande y todavía pendiente, sin backend nuevo (ya hay `GET /state` y
   `POST /rpc`): tokens en `style.css` (`--surface-3`, `-sf` de estado, `--line-2`, las 4 duraciones y
   3 curvas), el mapa de iconos y `paintIcons()`, el raíl con `hidden` por sección, las filas
   agrupadas sustituyendo `.card`, y el pill REC a `#D70015` (hoy blanco sobre `#FF453A` = 3,41:1,
   por debajo de AA). El interruptor de tema y el bloque de captura se conservan: ya funcionan.
   Las claves `data-i18n` existentes se mantienen y se añaden las de sección nueva
   (`ui.secDictation`, `ui.grpIsland`…).
