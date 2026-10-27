# Registro de modificaciones — Dicta (reuniones, documentos y UI)

Fecha: 2026-07-10 · Acompañado del skill Impeccable (v4.5.0) para el diseño de UI.

Cada cambio incluye la validación concreta que lo confirmó.

## v1.0.10 — 26 de octubre de 2026

**El icono pasa a ser el completo en todas las tallas.**

- Hasta ahora la marca se simplificaba por debajo de 48 px: de 28 a 47 px el
  cursor iba **sin remates** y por debajo de 28 px las barras y el cursor eran
  **rectángulos secos**.
- Ahora las barras son **cápsulas** (radio `bw/2`) en todas las tallas y el
  cursor lleva su asta y **sus dos remates** en las tres geometrías: 1 px en la
  rejilla pequeña (donde entran en el reparto, o el cursor se sale y el
  conjunto queda descentrado), 24 unidades centradas en el asta de 28 a 47 px y
  el remate de siempre de 48 px en adelante —con el asta fina da 126..150, el
  mismo que ya llevaba la talla grande, así que ahí no cambia ni un píxel.
- `_ICON_ICO_VER` 9 → **10**: cambian el nombre del `.ico` cacheado y la URL del
  favicon, así que la ventana y el panel no siguen enseñando el dibujo viejo.

Validación. Hoja `assets/_icon_check.png` (16/20/24/32/48 px en los dos temas y
la fila a tamaño real) y comprobación automática contra `HEAD`:

| Comprobación | Resultado |
|---|---|
| `official_image` (9 tallas × 2 temas) | cuadrado, esquina transparente, azulejo opaco |
| `wave_mark` (la onda de la isla) | **idéntico** a HEAD en 16/20/24/32/64/128 px |
| Remates del cursor | presentes en 16, 20, 24, 28, 32, 40, 48, 64, 128 y 256 px |
| Barras | cápsula (la punta mide menos que el centro) en 24 px y más |
| `.ico` | 13 capas cuadradas; **cambian** 16/24/32/40 y salen **idénticas** 48/64/256 |

## v1.0.9 — 25 de octubre de 2026

**La isla cambia de forma según el borde y el tema.**

- **Arriba y en oscuro** la isla es la muesca del SVG del diseño: los hombros
  son cóncavos —el cuerpo se ensancha en la primera fila y la curva se abre
  HACIA AFUERA, como una rampa que se vuelve plana— y llevan 7 px, porque a 32
  de alto los 12/113 del SVG (3,4 px) se leían como un escalón. Las esquinas
  de abajo se quedan en 45/113 (12,7 px). El hombro se resta como un cuarto de
  disco tangente por los dos extremos, así que no hay esquina viva.
- **Arriba y en claro** no lleva hombros: el canto va recto pegado al borde de
  la pantalla y el redondeo queda solo abajo.
- **En posición Abajo** deja de ser muesca: es una pastilla de 128×32 con 16
  de radio, centrada en la misma ventana para no moverse al cambiar de
  posición.
- La **vista previa de Apariencia** usa la misma geometría: camino SVG con
  `clip-path` en oscuro y `border-radius` en claro y en la pastilla. La
  pastilla ya no se pega al canto del recuadro: flota 10 px, como en pantalla.

Validación, perfil del canto medido por filas sobre el fotograma a 100 %:

| Caso | Primeras filas | Última fila |
|---|---|---|
| Arriba, oscuro | 136 · 134 · 132 · 130 · **128** | 110 |
| Arriba, claro | **128** desde la primera (recto) | 110 |
| Abajo (pastilla) | 104 · 110 · 114 · 118 → **128** al centro | 104 |

## v1.0.8 — 24 de octubre de 2026

**Identidad nueva, panel React y reunión reconstruida.**

**Identidad**
- Marca **onda y cursor** (`dicta_icon.mark_wave_caret`): tres cápsulas en el
  azul de acento que acaban en un cursor de texto. Sustituye a las cinco
  propuestas anteriores, que se eliminaron con sus hojas de prueba.
- `.ico` con **13 capas** (16, 20, 24, 28, 32, 36, 40, 48, 56, 64, 96, 128 y
  256) para cubrir los escalados de Windows, y bandeja dibujada a
  `SM_CXSMICON` y entregada 1:1: se quitó el doble reescalado que la veía
  borrosa.
- El nombre visible pasa a **Dicta** en títulos, bandeja y textos; las rutas y
  los identificadores internos siguen en minúscula.

**Panel (React)**
- Selectores de una sola pieza: mismo ancho que el botón, sin corte al
  desplegar, siempre hacia abajo con scroll y texto recortado con puntos
  suspensivos. La línea divisoria va bajo el valor del botón, no bajo la
  opción marcada.
- Arreglado el salto de la ventana al abrir un desplegable: el hueco de la
  barra pasó del `body` al shell, así que el documento ya no tiene recorrido.
- Sección «Dictado» renombrada a **Ajuste** y subtítulo corregido.
- Píldoras de valor centradas de verdad (medido: 5 px arriba y 5 abajo).

**Reunión**
- Tarjeta única y compacta, con controles de reproductor (pausa, detener y
  cancelar en iconos) y sin pie.
- Medidores Sistema y Micrófono en una fila: 32 rayas finas con rampa de seis
  colores (verde → amarillo → rojo), alimentadas por los **dBFS reales**.
- El micrófono ya captura: el «Asignador de sonido Microsoft» devolvía silencio
  en WASAPI compartido y se usa el dispositivo predeterminado real; además los
  bloques son de 50 ms (antes 250) y la caída es por tiempo, así el medidor se
  mueve siempre.
- Transcripción **completa** en el panel, con scroll, autoscroll y caja
  redimensionable.
- Corregido el cierre tras cancelar (`expected str... not NoneType`) y el panel
  ya se refresca sin tener el foco.

**Isla**
- Onda de **16 barras reactivas a la voz** (amplitud y espectro), cuerpo sólido
  blanco/negro y sin borde ni sombra.
- Retirada la tarjeta flotante con el texto: la isla queda solo con la onda.

**Limpieza**
- Eliminados el panel clásico (`panel/index.html`, `app.js`, `style.css`), el
  prototipo `assets/prediseno/` y los restos de plantilla del panel React.
- `desktop.js` sigue siendo la barra de ventana integrada.

---

## 1. Grabación de reunión: ahora graba de verdad (sistema + micrófono)

**Problema reportado:** *"no veo que grabe nada realmente"*.

**Diagnóstico:** el antiguo `MeetingTranscriber` solo leía el loopback WASAPI
para **transcribir en vivo**, pero **nunca escribía un archivo de audio**;
además ignoraba por completo el micrófono. Sin loopback, además, la sesión
fallaba entera.

**Cambios (dicta.py):**
- `MeetingTranscriber` reescrito: dos **productores** (loopback del sistema +
  micrófono por defecto) alimentan un mezclador que:
  - escribe un **`.wav` estéreo real** en `audios/` (canal L = sistema,
    canal R = micrófono, 48 kHz PCM_16);
  - mezcla ambas pistas para transcribir en vivo en ventanas de 26 s con
    solape 0,5 s al documento `textos/reunion-*.md`.
- Si no hay loopback, arranca igual con el micrófono solo (y al revés). Solo
  falla si no hay ninguna fuente de audio.
- **Se arregló un bug de COM**: la enumeración de dispositivos (MediaFoundation
  de `soundcard`) ahora inicializa COM en el hilo HTTP desde el que se inicia
  (`0x800401f0` = COM sin inicializar). Este bug hacía fallar `Iniciar` de
  forma intermitente — causa probable principal del "no graba nada".
- Los documentos de reunión guardan una línea final con **duración**,
  **nombre de la grabación** y **temas**.

**Validación:** prueba E2E real en vivo: `start → pause → resume → cancel`
(no quedó ni `.md` ni `.wav`); `start → stop` produjo
`reunion-20261007-*.md` (166 B con líneas con hora) y
`reunion-20261007-*.wav` (7,1 MB, verificado con `soundfile`:
**channels=2, samplerate=48000, PCM_16**). El panel en vivo mostró
transcripción real "[14:19] Gracias."

## 2. Pausar / reanudar la reunión

**Cambios (dicta.py + panel):**
- `MeetingTranscriber.pause()/resume()`: mientras está pausada descarta el
  audio capturado y no transcribe; la sesión sigue viva y el temporizador no
  acumula el tiempo de pausa.
- RPC `meeting` acepta ahora `start | pause | resume | stop | cancel`.
- Botón **Pausar/Reanudar** en el hub; el pill REC pasa a ámbar y la
  transcripción queda atenuada ("Última intervención — …").

**Validación:** navegador (agent-browser) contra el panel real: clic Pausar →
`recPill.className = "rec-pill paused"`, botón "Reanudar", caja "muted"; clic
Reanudar → vuelve a grabar.

## 3. Cancelar la reunión (descarta grabación y transcripción)

**Cambios (dicta.py + panel):**
- RPC `meeting=cancel` → `_meeting.cancel()` detiene, **borra el `.md` y el
  `.wav` parciales** y deja el estado `cancelada`.
- Botón **Cancelar** en el hub con **doble confirmación** (texto "¿Cancelar
  reunión?").

**Validación:** E2E: tras cancelar, `status=="cancelada"`, `doc=None`,
`wav=None` y no quedó ningún archivo en disco. En el navegador el flujo de
doble clic confirmó y mostró "Reunión cancelada".

## 4. Guardar y terminar la reunión (antes: "Detener")

**Cambios (dicta.py + panel):**
- RPC `meeting=stop` finaliza: transcribe el remanente, cierra y completa el
  `.md`, cierra el `.wav`, estado `guardada`.
- El hub muestra el resumen con **"Abrir documento"**, **"Descargar
  grabación"** y **Cerrar** (vuelve al inicio).

**Validación:** E2E + navegador: "Reunión guardada · reunion-*.md", botones
"Abrir documento" y "Descargar grabación" visibles; abrir documento cargó el
editor con el contenido.

## 5. Eliminar documentos

**Cambios (dicta.py + panel):**
- Nuevo RPC `doc.delete` (con validación anti-traversal `..`/`\`).
- Botón **Eliminar** en cada fila de documento con **doble confirmación**
  ("¿Eliminar?" → "Eliminar") y en el editor. Si el documento abierto se
  borra, se cierra el editor.

**Validación:** RPC directo (`doc.delete` → 200, doc desaparece → 404;
traversal `../dicta.py` → 400). En navegador: clic 1 muestra "¿Eliminar?",
clic 2 borra el archivo y lo quita de la lista.

## 6. Descarga del audio grabado y de los originales subidos

**Cambios (dicta.py + panel):**
- Nuevo endpoint `GET /audio?name=…` para servir WAV de reunión y audios
  originales desde `audios/` (inline o `download=1`, anti-traversal).
- Los ítems de la cola (`TranscribeQueue`) exponen su ruta `src`; cada fila
  tiene botón **Audio** para descargar el original.
- Cada documento de reunión expone su `.wav` hermano (`docs[].audio`) y el
  hub lo usa para **"Descargar grabación"**.

**Validación:** `/audio?name=reunion-…wav` → 200 con cabecera RIFF correcta;
`audio` aparece en `/state` enlazado al mismo nombre base; botón visible en
la UI.

## 7. UI del panel rediseñada (skill Impeccable)

**Cambios (panel/index.html, panel/app.js, panel/style.css):**
- **Hub de reunión** con tres caras: **inicio** (héroe con icono, título,
  descripción y botón Iniciar), **en vivo** (pill REC animado, temporizador
  monoespaciado, niveles decorativos, caja de transcripción en vivo, botones
  Pausar/Reanudar + Guardar y terminar + Cancelar) y **resumen** (guardada /
  cancelada con acciones).
- **Documentos**: filas con nombre, tamaño y acciones (Descargar, Audio,
  Eliminar); editor con Guardar, `.md`, `.txt`, Eliminar y Cerrar.
- Estilos nuevos (`meet-*`, `d-acts`, `.confirm`) sobre el sistema visual
  existente de DESIGN.md (tokens, radios, espaciado 4/8), respetando el
  craft-floor: estados hover/focus/disabled, contraste AA (REC blanco sobre
  rojo ≈ 9:1, texto secundario sobre `--surface` ≥ 4,5:1), sin modales
  innecesarios, iconos SVG consistentes (stroke 1.8–2.2, linecap round).
- i18n es/en completo para todos los textos nuevos.

**Validación:** navegador contra backend real: estado inicial idle; Iniciar →
live (REC + temporizador + transcripción en vivo); pausa/reanudar; guardar →
resumen; cancelar → "Reunión cancelada"; documentos: abrir, editar + guardar
(el contenido editado persistió en disco), eliminar; tema claro/oscuro con
tokens correctos (`--bg` #141418 / #F2F2F5). `node --check` y verificación
de que todos los `id` usados en JS existen en HTML.

## 8. Estado del backend (`/state`) ampliado

**Cambios (dicta.py `panel_state`):**
- `meeting` incluye ahora `paused`, `wav` y `last` además de
  `active/doc/status/seconds`.
- Cada `docs[]` incluye `audio` (nombre del `.wav` hermano si existe).
- Los ítems de `queue[]` incluyen `src`.

**Validación:** `/state` real con todas las claves nuevas; verificación de
que el frontend usa exclusivamente estas claves.

## 9. La isla no aparecía nunca: `HINSTANCE` truncado (access violation)

**Problema reportado:** dictar funcionaba, pero **la isla no se veía**.

**Diagnóstico:** `dicta_ui.py` declaraba `ctypes.WinDLL("user32")` etc. **sin
`argtypes`/`restype`**. En x64 ctypes devuelve por defecto un `c_int` de 32
bits, así que `GetModuleHandleW` entregaba `0xffffffffdb4e0000` en lugar de
`0x7ff6db4e0000` (extensión de signo de un puntero válido). Con ese `hInstance`
basura, `RegisterClassExW` y `CreateWindowExW` provocaban *access violation*:
`dicta_crash.log` acumulaba **21 violaciones** (19 en la línea de
`CreateWindowExW`, 2 en la de `RegisterClassExW`), cada una matando el hilo
`dicta-notch` y dejando la app viva pero sin isla.

**Cambios:** todo el Win32 de ventana se movió a `dicta_shell.py` (clase
`LayeredWindow`) **con todos los prototipos declarados**; `NotchWindow` se
redujo a una subclase que solo aporta el fotograma.

**Validación:** antes, 12 de 12 arranques fallaban; después, **12/12 sin una
sola violación**, con hwnd creado. La captura de escritorio por `BitBlt` (las
capturas "compuestas" no incluyen ventanas *layered*) confirma que la isla se
pinta encima y que **no se solapa con la barra de tareas**.

## 10. Carrera al liberar el DIB (segunda access violation)

**Problema:** la isla se cerraba y a veces el hilo de dibujo moría.

**Diagnóstico:** `hide()`/`destroy()` (hilo de Tk) liberaban el DIB mientras el
bucle de animación hacía `ctypes.memmove` sobre él, y `_release_dib()` no ponía
`_bits = None`. Además, al **cambiar de tamaño** el fotograma crecía pero el DIB
no, así que `memmove` escribía fuera del búfer: reproducido al abrir la lista de
fuentes del notch nuevo (`OSError: access violation writing …`).

**Cambios:** el DIB se recrea siempre con **el tamaño exacto del fotograma**,
`_release_dib()` deja `_bits = None`, y todo el ciclo está bajo un cerrojo.

**Validación:** ciclo `show → draw → hide → show` repetido sin violaciones; el
notch cambia de alto (122 → 176 px) pasando de cerrado a grabando sin fallar.

## 11. Burbuja flotante + notch rápido (chrome nuevo)

**Cambios:** `dicta_shell.py` añade `OrbWindow` (orbe arrastrable con hover y
anillo de actividad) y `QuickPanelWindow` (notch anclado a la burbuja: reunión,
fuente de audio, tiempo y niveles, última frase, Archivo/Panel/Ocultar), con
`WM_DROPFILES` para encolar audios arrastrándolos. `dicta.py` los conecta a
`ui_events` (el hilo de Tk sigue siendo el único que toca la app) y `config`
guarda `bubble` y `bubble_pos`.

**Validación:** clic real (SendInput en coordenadas absolutas) sobre la burbuja
de la app → `Chrome: acción «toggle_panel»` y el notch visible en pantalla con
**4742 píxeles de marca** medidos por `BitBlt`; segundo clic → cerrado. El orbe
se ve en su sitio con **193 píxeles de marca**.

**Lecciones aplicadas:** `SendInput` exige `cbSize == sizeof(INPUT)` (40 en
x64) exacto, y un `WM_LBUTTONUP` perdido dejaba el arrastre pegado (ahora se
comprueba el estado real del botón); la posición guardada se limita al área de
trabajo.

## 12. Grabar SOLO una aplicación (captura por proceso)

**Cambios:** `dicta_capture.py` (ctypes puro, sin dependencias) implementa
WASAPI *process loopback*; `MeetingTranscriber` acepta una fuente
(`meeting_source`: `all` o el PID de una app) y, si falla, **la reunión sigue
con el micrófono** en vez de caerse. El notch y el panel permiten elegirla.

**Validación E2E con audio real:** un proceso que reproduce un tono de 440 Hz y
0,35 de amplitud como fuente de una reunión de 12 s → `.wav` de 2,30 MB,
48 kHz, 2 canales, con **RMS 0.2471 y pico 0.350 en el canal de la aplicación**
(lo esperado para ese tono) y **RMS 0.0000 en el del micrófono**: se capturó
solo esa aplicación, sin sangrado.

## 13. Identidad: icono y marca única

**Problema:** el `.exe` no tenía icono y el de la bandeja era un dibujo suelto
sin relación con la app.

**Cambios:** `dicta_icon.py` genera `dicta.ico` (16-256 px) y el icono de
bandeja a partir de **la misma función que dibuja la onda de la isla y de la
burbuja** (`dicta_shell.wave_mark`). Cada talla se **redibuja**: 5 barras desde
40 px y 3 barras más gruesas por debajo. El `.ico` se construye a mano porque el
plugin de Pillow reducía todo al primer tamaño. La ventana del panel recibe el
icono y su título pasa a ser **dicta** (el identificador interno solo se usa
para localizarla).

**Validación:** tamaños presentes `16, 24, 24, 32, 48, 64, 128, 256` todos
cuadrados; a 16 px se miden **3 barras de 3 px** y a 48 px **5 barras de 4 px**
(antes, a 32 px las cinco barras de 1 px se fundían en **un solo tramo de
10 px**); los dos temas con azulejo correcto (blanco en claro, grafito en
oscuro) y filo de luz.

## 14. Vista previa de audio

**Cambios:** `GET /peaks?name=…` devuelve la envolvente (pico absoluto por
bloque, ~600 valores) con caché por mtime, y `GET /audio` ya servía el fichero;
el panel dibuja la onda y reproduce desde la propia fila de la cola.

**Validación:** `/peaks?name=test.flac` responde JSON con `dur` coherente y
cientos de picos en 0..1; un nombre inexistente devuelve 404 sin romper.

## 15. Interruptor de la burbuja en la bandeja

**Cambios:** el menú de la bandeja gana **Burbuja flotante**, con marca de
verificación ligada al estado real; encola `("bubble", not estado)`, que
`dicta.py` aplica y persiste. El icono de bandeja pasa a seguir el tema (iba
siempre en oscuro).

**Validación:** llamando al menú de verdad (no leyendo el código), con
`bubble=True` sale marcado y encola `("bubble", False)`, y con `bubble=False` al
revés. Contraste medido del icono de bandeja: **6,11:1** sobre barra oscura y
**4,04:1** sobre clara (antes, en claro, se quedaba en ~1,6:1); el azulejo es a
propósito un halo casi invisible (1,07:1) para no pintar un cuadrado opaco
sobre la barra.

## 16. La cola etiquetaba con el nombre temporal del subido

**Problema:** al subir `reunion-equipo.flac` la fila mostraba `e2eaeb667fef.flac`.

**Diagnóstico:** el manejador multipart guarda el archivo en `.tmp/` con un
nombre `uuid`, y `TranscribeQueue.add()` usaba `os.path.basename(src_path)` como
etiqueta. El nombre original estaba ahí mismo, en la cabecera `filename=`.

**Cambios:** `add(path, label=None)` acepta la etiqueta y subida le pasa el
nombre original.

**Validación:** subiendo un archivo llamado `reunion-equipo.flac`, la cola
muestra exactamente `reunion-equipo.flac`.

## 17. Panel: vista previa verificada en navegador real

**Validación (Chrome headless por CDP, sin tocar el navegador del usuario):**
el panel carga (`readyState=complete`, sin excepciones y consola vacía), la fila
de la cola dibuja la onda en un `<canvas>` de **365×32 con 1686 píxeles
pintados**, muestra **00:10** de duración (el archivo dura 10,44 s) y al pulsar
play el audio **reproduce** (`paused=false`, `currentTime=1.92`,
`duration=10.44`). El selector de fuente lista las fuentes del backend, el
interruptor de burbuja refleja `state.bubble` y no queda ningún texto sin
traducir.

## 18. Compilación del ejecutable con el icono

**Validación:** `PyInstaller --clean dicta.spec` termina con **exit 0**; el
registro dice `Copying icon to EXE`; `dist/dicta/dicta.exe` (7,0 MB) lleva
dentro el icono **idéntico píxel a píxel** al que renderiza `dicta_icon.py`
(diferencia media **0,00/255**, 960 píxeles opacos en ambos, extraído con
`ExtractAssociatedIcon`). El paquete incluye `_internal/dicta.ico`,
`_internal/panel/` con el panel actual y los dos motores; los cuatro módulos
propios aparecen en el índice del ejecutable.

Es la prueba de que los `hiddenimports` de `dicta.spec` bastan: al abrir el
`.exe` no debería salir `Sin burbuja flotante (falta dicta_shell)` en el log.

## 19. Lanzar Dicta no mostraba nada

**Problema:** con `pythonw.exe` no hay consola y la app no abría ninguna
ventana, así que «abrir dicta» no daba ninguna señal visible. Peor: si ya
estaba corriendo, el segundo lanzamiento moría con `dicta ya está abierto (otra
instancia)` — el propio registro lo recoge dos veces (10:41:35 y 10:42:18).

**Cambios:** al arrancar se encola `open_panel` (el panel es la cara visible de
la app). Si ya hay instancia, `_wake_running_instance()` le pide por HTTP
`{"action": "open_panel"}` —recorriendo el rango de puertos y comprobando con
`/state` que quien responde es Dicta, para no escribirle a otro programa— y
`_panel_rpc` lo aplica. `--no-panel` lo desactiva.

**Validación:** con otra instancia viva, relanzar imprime «dicta ya estaba
abierto: se le pidió a la instancia en curso que abra el panel» y el panel
aparece en primer plano.

## 20. La ventana del panel se llamaba `dicta-panel-13956-1fc82525880`

**Diagnóstico:** `_integrate()` renombraba la ventana a «dicta», pero Chrome la
pisa con el título de la página al acabar de cargar. Comprobado enumerando
ventanas: `Chrome_WidgetWin_1 | pid 10856 | 'dicta-panel-13956-1fc82525880'`.

**Cambios:** se guarda el PID dueño de la ventana y el renombrado se reaplica
hasta que se asienta (~15 s); `_panel_hwnd()` acepta también ese PID, porque el
título único deja de servir en cuanto la ventana se renombra.

**Validación:** la ventana queda titulada `dicta`.

## 21. Paneles acumulados de instancias muertas

**Diagnóstico:** si Dicta muere de golpe, su Chrome sobrevive. Como el perfil es
el mismo, al abrir el panel otra vez Chrome **reutiliza ese proceso** y aparece
una ventana más: se midieron dos a la vez, una `dicta` y otra `dicta-panel-…`.
Limpiar por título no sirve, porque el Dicta anterior ya se había renombrado.

**Cambios:** `_clear_stale_panel(profile_dir)` mata los procesos de navegador
cuyo `CommandLine` lleva el perfil del panel (exclusivo suyo) antes de abrir uno
nuevo, e informa cuántos cerró.

**Validación:** tras reiniciar, una sola ventana `Chrome_WidgetWin_1` titulada
`dicta`.

## 22. El notch quedaba inalcanzable sin la burbuja

**Cambios:** entrada **Panel rápido** en el menú de la bandeja, que encola
`("shell", "toggle_panel")`. Si la burbuja está oculta y nunca se colocó, el
notch se ancla a la esquina por defecto en vez de a las coordenadas (0, 0).

## Nota sobre el icono de la bandeja (no es un fallo de Dicta)

En `HKCU\Control Panel\NotifyIconSettings` hay tres entradas de Dicta —una de
ellas del ejecutable de un Dicta ANTIGUO en `Documents\Voice to text\dicta\
dist\`— y **ninguna con `IsPromoted`**: Windows 11 las deja en el desplegable
de la flechita. Para tenerlo a la vista: **Configuración → Personalización →
Barra de tareas → Otros iconos de la bandeja del sistema → dicta**.

## 23. Fuera la burbuja y el notch

**Petición:** eliminar la burbuja y el panel desplegable, y en Ajustes todo lo
que los mencionara; dejar solo la isla que aparece al dictar.

**Cambios:** se van la clase `OrbWindow`, la clase `QuickPanelWindow`, el
estado y la config de la burbuja (`bubble`, `bubble_pos`), la entrada de bandeja
*Burbuja flotante*, el interruptor del panel, y las acciones `hide_bubble`,
`toggle_panel`, `pick_files`, `source:` y `meet_*` que solo llegaban del notch
(en el panel siguen existiendo como acciones HTTP). `dicta_shell.py` pasa a
`dicta_layered.py` **solo con lo que la isla necesita** (la base
`LayeredWindow` y la geometría del escritorio): 1423 → 866 líneas. La onda
(`wave_mark`) se muda a `dicta_icon.py`, que ya no depende de nadie.

**Validación:** `dicta_layered.available()` sigue siendo `True`, `prepare()`
devuelve vacío (la clase de ventana se registra) y `dicta_ui` importa la isla
con `_SHELL_OK=True`. El icono renderizado **no cambió**: mismo sha1
(`0a4ff103`) antes y después de mover la onda, y el `.ico` es idéntico al de la
bandeja (misma imagen, 961 píxeles opacos).

## 24. Cerrar la reunión, y onda en vivo mientras graba

**Síntoma 1 (fallo):** grabando una reunión, al pulsar **Cerrar** la tarjeta del
resumen desaparecía y volvía a aparecer.

**Diagnóstico:** el botón solo limpiaba el estado **local** del panel
(`state.meeting.status = ""`); el sondeo de `/state` lo repintaba desde el
backend, que seguía diciendo `guardada`/`cancelada`.

**Cambios:** `MeetingTranscriber.dismiss()` olvida el resumen en el backend
(el `.md` y el `.wav` NO se borran: siguen en Documentos y la lista), la acción
`meeting: dismiss` la expone por HTTP y el botón la usa antes de repintar.

**Validación:** iniciar reunión → cancelar → pulsar Cerrar: la tarjeta vuelve a
*Iniciar* y sigue así a los 2,6 s y a los 5 s (antes reaparecía al primer
sondeo).

**Síntoma 2 (petición):** grabando una reunión no se veía ninguna onda.

**Cambios:** la reunión publica el nivel RMS de cada pista (`level_sys`,
`level_mic` y el mix) en `/state`, medido en los dos productores con ataque
rápido y caída lenta; la isla se queda en pantalla mientras la reunión graba,
con la onda siguiendo ese nivel; y el panel deja de fingir con un pulso: sus dos
barras son el nivel real de cada canal.

**Validación:** con una reunión en marcha y audio sonando por el altavoz, la isla
se ve en (903, 992, 1017, 1026) con 10 979 píxeles cambiados por `BitBlt`, y el
nivel de sistema pasa de 0,00 a **0,82** siguiendo el audio (0,14 → 0,82 → 0,67 →
0,45 → 0,30 → 0,74).

**Dos fallos de captura encontrados al verificar lo anterior** (la reunión
grababa silencio y sin voz):

1. *«Audio del sistema» cogía el dispositivo equivocado.* Se usaba `loops[0]` de
   `soundcard`, que en este equipo son unos **auriculares desconectados**; el
   altavoz por defecto era el `[1]`. Ahora se busca el loopback del altavoz por
   defecto (`default_speaker()`), con el primero como último recurso.
2. *El micrófono reventaba con `AssertionError`.* `soundcard` solo lee
   dispositivos cuyo formato de mezcla sea IEEE float
   (`assert wFormatTag == 0xFFFE`) y el de este equipo no lo es: la reunión se
   quedaba sin voz **siempre**. El micro pasa a capturarse con **PortAudio**
   (`sounddevice`), el mismo motor que ya usa el dictado, remuestreando si el
   dispositivo no va a 48 kHz.

**Validación de los dos:** con audio sonando, `level_sys` llega a **0,82** y
`level_mic` da 0,001 (silencio de sala, pero vivo); en el registro **no hay
ninguna línea `Reunión captura (micro)`** desde el arreglo (antes: una cada vez).

## 25. Isla arriba, atajo para abrir el panel, micro en la reunión y nombres

**Petición del usuario:** (1) la animación del audio en la parte **superior**;
(2) una configuración para grabar también el micrófono mezclado con el sistema;
(3) que el documento herede el nombre del audio; (4) una puerta de entrada
fiable, porque cerró el panel con *Listo* y se quedó sin encontrar la app.

**La isla pasa arriba.** `ISLAND_TOP_GAP = 10`, `_top_y()` mide sobre el área de
trabajo real (0x0030) y la tarjeta de la transcripción crece hacia **abajo** en
vez de hacia arriba.

*Validación:* inyectando `WM_HOTKEY(47124)` (lo mismo que hace Windows al pulsar
Alt+Q) la isla aparece en **(903, 10, 1017, 44)**: centrada en x=960 sobre 1920 y
a 10 px del borde superior. `WM_HOTKEY(47125)` (Alt+E) la oculta y el estado
vuelve a `idle`.

**Atajo Ctrl+Alt+P para abrir los ajustes.** Tercer `HotkeyManager` con su
propio id (47126), evento `panel`, editable desde el panel como los otros dos.
El registro confirma `Hotkey global ctrl+alt+p registrada`.

*Validación:* inyectando `WM_HOTKEY(47126)` en los hilos del proceso el panel se
abre («Panel abierto» en el log). La inyección por `SendInput` de este entorno
no es fiable (falla también con Alt+Q, que el usuario sí usa a diario), así que
la comprobación se hace por el mismo mensaje que manda Windows.

**Micrófono en la reunión, con interruptor.** El mix ya existía
(`(sistema + micro) * 0.5` para transcribir y un .wav estéreo L/R), pero el
micro **nunca** sonaba: `soundcard` aborta con `assert wFormatTag == 0xFFFE` con
un micro que no sea IEEE float. Ahora se captura con PortAudio y se puede
desactivar en Ajustes (`meeting_mic`, expuesto como `meeting_mic` en `/state`).

*Validación:* apagado y encendido desde el panel cambian `/state.meeting_mic`
(False/True) y quedan en el log.

**Los documentos heredan el nombre del audio.** `_doc_name()` limpia lo que
Windows no admite en un nombre de fichero y numera si ya existe.

*Validación:* subiendo `reunion miercoles.flac` el documento sale
**`reunion miercoles.md`** (antes: `audio-<uuid>.md`).

**Icono de bandeja promocionado.** Las tres entradas de Dicta en
`HKCU\Control Panel\NotifyIconSettings` tenían `IsPromoted` vacío (Windows 11
las esconde); ahora valen 1.

## 26. Rediseño: la isla nueva

**Petición:** aplicar el prediseño de `assets/prediseno/`.

**Isla.** Geometría del prediseño (`ISLAND_H 34→36`, `ISLAND_PAD 15→16`,
`ISLAND_WAVE_W 84→96`, onda de 9 cápsulas de 6 con 5 de hueco) y **forma B**:
cuelga del borde superior con las esquinas de arriba rectas. Se obtiene
intersectando dos SDF (`max`), con el redondeado sobresaliendo por encima del
fotograma para que solo afecte a las esquinas de abajo.

**Error que se corrigió al medir:** la primera versión usaba `min` (unión) y las
esquinas de abajo salían rectas (1,00 en vez de 0,00). La intersección de SDF es
`max`, no `min`.

**Validación:** sobre el fotograma, esquina de arriba **0,97** y de abajo
**0,00**; 4470 píxeles opacos frente a 4332 de la variante flotante. En pantalla,
la isla aparece en **128×36 centrada en x=960 sobre 1920 y a 10 px del borde**
(inyectando `WM_HOTKEY(47124)`, lo mismo que manda Windows al pulsar Alt+Q), y
`WM_HOTKEY(47125)` (Alt+E) la oculta y deja el estado en `idle`.

`ISLAND_SQUARE_TOP = False` vuelve a la píldora flotante sin tocar nada más.

## 27. Rediseño: el panel de ajustes

**Petición:** aplicar el prediseño de `assets/prediseno/` a la ventana de ajustes.

**Qué cambió.** `panel/index.html` y `panel/style.css` reescritos; `panel/app.js`
solo en lo imprescindible (mapa `ICONS` de 42 iconos + `paintIcons()`,
`showSection()`, recuentos del raíl, segmentado de tema, las 37 claves i18n
nuevas en es/en). Raíl de siete secciones y filas agrupadas sustituyendo la
rejilla de tarjetas `.card`; tokens nuevos (`--surface-3`, `--line-2`,
`--ok-sf`/`--warn-sf`/`--err-sf`); seis pasos tipográficos y cuatro duraciones
con tres curvas; el pill REC pasa a `#D70015` (5,38:1) porque el blanco sobre
`#FF453A` estaba a 3,41:1.

**Ninguna acción enviada al backend cambia** (`model`, `meeting`,
`set_panel_key`… siguen iguales): el rediseño es de cliente.

**Validación.** Tres comprobaciones, todas en verde, y repetidas después por
fuera del cambio:
1. `node --check panel/app.js` → sin salida.
2. Las **72** referencias `$("#id")` de `app.js` existen en `index.html`: no
   falta ninguna (los 67 de siempre más 5 nuevos).
3. El panel cargado en Chrome por CDP: `readyState` *complete*, raíl de 7
   secciones, 41 iconos pintados, los 5 desplegables rellenos (6 idiomas, 3
   motores, 5 modelos, 9 micrófonos, 1 fuente), **0 textos sin traducir** (texto
   y `aria-label`), **0 excepciones y 0 errores de consola**. Pulsando el raíl
   las 7 secciones cambian; el interruptor del micro mueve `/state.meeting_mic`
   de verdad (`true → false → true`); el capturador de atajos abre y cancela; el
   tema cambia a claro y vuelve. Contraste medido en los dos temas: todo el texto
   ≥4,5:1 y los gráficos ≥3:1.

**No aplicado, a propósito:** los controles de la isla (posición y
click-through), el arrastrar-y-soltar de Audios, «probar micrófono» en la propia
página y el segmentado de «modo de dictado» / «parada por pausa» salen como
**filas informativas** o no salen, porque el backend no tiene acción para ellos:
antes un interruptor falso que información verdadera.

## 28. El dictado se pegaba dentro del propio panel

**Síntoma:** «Alt+Q no auto-pega». En el log hay 6 dictadas con
`destino: dicta` y **en las 6 la línea anterior es «Panel abierto.»**: cuando la
ventana del panel tiene el foco, el texto se pega **dentro del panel**. La
grabación y la transcripción van bien, y el usuario no ve nada aparecer en su
aplicación (tampoco se veía el fallo: el log decía «Texto insertado
automáticamente en el campo»).

**Causa:** `app.target_hwnd = GetForegroundWindow()` al empezar a dictar y la
entrega fuerza ese destino. La primera versión del arreglo no servía:
`self.panel` vive en `Overlay` (local de `main()`), **no en `App`**, así que
`app.panel` no existía y la comprobación de «ventana propia» no acertaba nunca.

**Arreglo.** El host del panel se publica en `_panel_host` desde
`Overlay.__init__`; `_es_ventana_propia()` reconoce el panel por PID (y por
título como red: Chrome le pisa el título único) y la isla por clase. En la
entrega:

1. Si la ventana que el usuario mira ahora no es de Dicta, se pega **ahí** (cambió
   de ventana mientras hablaba).
2. Si sigue en el panel, se pega en **la última ventana ajena recordada**
   (`_recordar_destino()`, en cada vuelta del bucle de servicio: dos llamadas de
   Win32, sin enumerar ventanas).
3. Si no hay ninguna, el texto **queda en el portapapeles** y se avisa, en vez de
   colarse dentro del panel.

**Validación.** Con el panel en primer plano y el código instrumentado,
`_es_ventana_propia()` informa `clase='Chrome_WidgetWin_1' titulo='dicta'
host=True` y la entrega registra «Destino corregido (el panel no cuenta)»: antes
pegaba en el panel, ahora no. Una dictada real (Alt+Q inyectado + voz) se
transcribió y se pegó sin tocar el carril de reparación por UI Automation.
**Sin verificar de punta a punta** el paso 2 (que el rescate coja la última
ventana ajena): Windows no deja que un proceso cualquiera traiga el panel al
primer plano, así que hay que probarlo a mano — abrir el panel con Ctrl+Alt+P y
dictar **sin hacer clic en otra ventana**.

**Nota de entorno:** `Stop-Process` sobre la app puede fallar en silencio y la
copia nueva morir en el «ya está abierto»; se cierra con `POST
{"action":"quit"}`. Y una app que llevaba horas abierta sigue con el código
viejo en memoria: para comprobar cualquier arreglo hay que mirar la hora de
arranque del PROCESO contra la fecha del fichero.

## 29. El pegado necesita que Dicta corra elevada (y avisos nuevos)

**Diagnóstico del autor, confirmado:** el texto no se pegaba porque Dicta estaba
corriendo **sin** administrador; con `run.bat` (elevada) sí pegaba. No es un
efecto del rediseño: es UIPI. Windows no deja que un proceso de integridad media
mande entrada sintetizada (el Ctrl+V del carril rápido) a una ventana de un
proceso elevado, así que el pegado «no hace nada» aunque el log diga que se
envió. La instancia se había relanzado a mano, sin UAC, y con eso se rompió el
pegado en las apps donde el autor dicta.

**Comprobado:** al consultar el proceso de esas ventanas, `OpenProcess` **falla**
(no se puede ni leer su línea de comandos), que es la firma de que están por
encima de dicta.

**Cambios.**

- `_esta_elevado()` (token del propio proceso) y `_destino_protegido(hwnd)`: si
  no se puede abrir el proceso del destino, es que está protegido o elevado.
- En el arranque: `dicta 1.0 listo — … (elevado: sí/no)` y, si no lo está, un
  **AVISO** de que el texto no llegará a las ventanas elevadas y que se arranque
  con `run.bat`.
- En el pegado: si el destino es protegido y Dicta no está elevada, se registra
  el motivo exacto en vez de un «Pegado (Ctrl+V) enviado» que engaña.
- `_forzar_primer_plano()` (AttachThreadInput + Alt simulado): `SetForegroundWindow`
  a secas se ignoraba desde Dicta, y por eso el Ctrl+V acababa en otra ventana.

**Isla:** `ISLAND_TOP_GAP` 10 → **0**: el borde de arriba queda pegado al borde
de la pantalla, sin hueco (la forma ya tenía las esquinas de arriba rectas, que
es lo que hace que se lea como una muesca y no como una pastilla suelta).

**Validación:** `[14:59:29] dicta 1.0 listo — alt+q, modo toggle, idioma es,
cancelar alt+e (elevado: sí)` y ninguna línea de aviso; el pegado se comprobó
antes con una ventana de prueba propia: una dictada real del autor acabó dentro
de su campo de texto (Ctrl+V correcto), y el enrutado eligió la ventana ajena
correcta con el panel en primer plano (`raíz='DICTA_PRUEBA'`).

## 30. Canto de la isla, barra de la ventana y audio de la reunión

**Canto de la isla.** `ISLAND_EDGE_W` (1,4 px), `ISLAND_EDGE_A` (0,85) y un filo
claro en oscuro / oscuro en claro, calculado del SDF que ya está cacheado: sigue
cualquier forma (muesca arriba, redondeo abajo) y no engorda la ventana. Se
aplica justo antes del invariante de premultiplicado, encima del cuerpo y de la
onda. Medido sobre el fotograma: en oscuro el canto da (70,76,91) frente al
cuerpo (16,19,26); en claro (189,191,200) sobre el blanco. El color se subió de
(0,30) a (0,44) porque sobre un fondo claro el filo apenas se distinguía.

**Barra de la ventana del panel.** El título pasa a **«dicta — Ajustes»** (antes
se leía `dicta-panel-<pid>-<id>`, que es solo la clave interna para localizar la
ventana). Comprobado sobre la ventana real: `titulo: «dicta — Ajustes»`.

**Hallazgo: la barra no se puede pintar desde dicta.** `DwmSetWindowAttribute`
falla con **E_HANDLE** porque la ventana es de Chrome, otro proceso (comprobado
intentando pintarla de rojo a lo bruto). Sí se puede leer: el flag de barra
oscura está a **1** con el panel en tema claro, que es exactamente el desajuste
que se ve. Chrome la dibuja según el `color-scheme` y el
`<meta name="theme-color">` de la página del panel, así que esto se arregla en
el panel (CSS/HTML) y no en Python.

**Audio de la reunión.** Dos fallos reales, los dos del mismo sitio:

- El `.wav` se guardaba con **L = sistema, R = micrófono**. Escuchándolo se oye
  por un solo oído cuando no hay audio del sistema (el caso normal al grabarse
  uno mismo) y la voz propia casi no aparece. Ahora los dos canales llevan **la
  mezcla**. Verificado sobre un `.wav` real: **diferencia entre canales
  0,000000**, 2 canales, 48 kHz.
- El micro de este equipo entra muy bajo: **RMS 0,001** frente a **0,82** del
  sistema. Se añade ganancia automática hacia nivel de voz (objetivo 0,10 de
  RMS, tope ×16, suavizado 0,7/0,3 para que no bombeen el ruido ni se note el
  ajuste) antes de mezclar. Verificado en la misma grabación: RMS del micro
  **0,0162**, o sea ×16 clavado.

Los restos de esa prueba (el `.wav` y el `.md`) se borraron.

## 31. Sombra de la isla, ventana sin marco y panel plano

**Sombra de la isla (ida y vuelta).** Primero se probó un **canto** de 1,4 px
derivado del SDF; el autor lo rechazó («pierde la sutileza»), así que se quitó.
La vía que pidió es una **sombra suave**: halo claro en oscuro y sombra discreta
en claro, **solo a los lados y por abajo** (arriba no: nace del borde de la
pantalla), que se apaga en 8 px. Para tener sitio, la ventana de la isla creció a
**144×44** (cuerpo 128×36 + margen) y el cuerpo se dibuja dentro.

Dos fallos reales de este cambio, los dos míos:

- La primera fórmula daba la sombra también **dentro** del cuerpo: `clip(d, 0, w)`
  vale lo mismo en el canto que dentro, así que pintaba un 40 % de opacidad
  sobre toda la isla y se comía la onda. Se veía en la pantalla del autor y
  también en mis propias medidas (cuerpo 36,40,51 cuando debía ser 17,20,28) y
  no lo vi. Se arregla multiplicando por una máscara de «fuera» (`d > 0`).
- El cuerpo **no estaba premultiplicado**: `out_c[:] = body` dejaba su color bajo
  todos los píxeles de alfa 0, así que en tema claro la sombra se componía sobre
  blanco y salía **clara** en vez de oscura (y en el canto antialias quedaba una
  franja más brillante). Ahora `out_c = body * mask`.

Medido sobre el fotograma contra un fondo de color parecido: en oscuro el halo
sube **+47** niveles desde el fondo y en claro baja **−49**; el cuerpo queda
intacto (17,20,28 / blanco puro). La primera versión, con 6-10 niveles, no se
distinguía.

**Ventana del panel: WebView2 sin marco.** La barra nativa no se puede estilar
desde Dicta (DwmSetWindowAttribute falla con E_HANDLE: la ventana es de Chrome) ni
se puede quitar (Chrome la repone), y el `window-controls-overlay` de Chrome solo
vale para PWAs instaladas. Así que el panel pasó a **pywebview/WebView2**:
`frameless=True`, sin barra del sistema, con barra propia inyectada
(`panel/desktop.js`) y el **backend de Chrome como respaldo** (clave
`panel_backend`: `auto`/`webview`/`chrome`). Verificado sobre la ventana real:
clase `WindowsForms10.Window…`, `WS_CAPTION = false`, **fila 0 = 98,8 % del fondo
del panel** (0 % de gris de Windows), minimizar/restaurar/maximizar comprobados
con clic real y `IsIconic`/`IsZoomed`, cerrar deja la app viva (`/state` 200).

- **Esquinas redondeadas** (Windows 11): `DwmSetWindowAttribute(hwnd, 33,
  DWMWCP_ROUND)`; ahora sí funciona porque **la ventana es del propio proceso**
  (con Chrome era imposible). Leído de vuelta: `hr=0, valor=2`.
- **La barra sustituye a la cabecera**: icono + «Dicta» (D mayúscula) + la
  pastilla de estado, y el `.app-head` del panel oculto (fuera «Ajustes /
  Dictado por voz, 100% local y privado» y el selector de tema, que ya está en
  Apariencia). `#themeSwitch` sigue existiendo como nodo oculto: sin él se
  romperían las 72 referencias de `app.js`.
- **Arrastre**: la clase de pywebview (`pywebview-drag-region`) no movía la
  ventana en este montaje (medido: 0 px, aunque la llamada llegaba al backend),
  así que hay un bucle Win32 propio (`GetCursorPos` + `SetWindowPos` mientras el
  botón izquierdo siga pulsado). Arrastrar por la barra mueve (dx 70/dy 40);
  arrastrar dentro de la página no.
- **Estados en lenguaje humano**: `app_status_ready()` → «Listo para escuchar»,
  «Cargando modelo…», «Escuchando…», «Transcribiendo…», «Transcripción lista»,
  «Texto insertado», «Cancelado».

**Panel: oscuro plano y desplegables propios.** El autor decía que el oscuro se
veía «muy 3D, con sombras» frente al claro. Ahora el oscuro no usa ni una sombra
con desenfoque: se delimita con filos `inset 0 0 0 1px rgba(255,255,255,.06–.10)`.
Y los desplegables nativos (cuyo popup no se puede estilar) pasaron a un
**componente propio** (botón + lista flotante con los tokens del panel, teclado y
foco visible) que mantiene los cinco `<select>` en el DOM como fuente de verdad:
al elegir, actualiza el select y le dispara su `change`, así que `app.js` no
cambió. Contraste medido: opción 13,84:1 (oscuro) / 15,46:1 (claro); elegida
5,32:1 / 4,89:1.

---

## 32. La isla: arriba o abajo, y paleta de color (Apariencia)

**Pedido:** poder elegir si la isla aparece ARRIBA (colgando del borde, como
hoy) o ABAJO (pastilla flotante con la tarjeta creciendo hacia arriba), y una
paleta de color con varios presets, ambas persistidas y aplicadas en caliente.

**Cambios:**
- Claves nuevas en `dicta_config.json`: **`island_pos`** (`top`|`bottom`, por
  defecto `top`) e **`island_palette`** (`grafito`|`oceano`|`ambar`|`menta`|
  `frambuesa`|`violeta`, por defecto `grafito`).
- `dicta_ui.py`: `set_position()` / `set_palette()` + `_square_top()`/`_at_top()`
  (la forma ya no la fija la constante `ISLAND_SQUARE_TOP`, que entra en la
  clave de la caché de `_scene`), `_bottom_y()` (pareja de `_top_y()`, a
  `ISLAND_BOTTOM_GAP = 10`), `PALETTES` (6 presets con sus tres degradados —
  escucha/transcribir/cancelar— en los DOS temas, más el color del cuerpo) y
  `render_island_rgba(..., body_dark, body_light)`. En la posición `bottom` el
  cuerpo va pegado al borde INFERIOR del fotograma y el margen de la sombra
  pasa ARRIBA (margen y anclaje volteados), y la tarjeta crece hacia arriba.
- `dicta.py`: `app.island_pos` / `app.island_palette`; `on_island_pos()` (recrea
  la isla con `overlay.apply_position()`) y `on_island_palette()`
  (`overlay.refresh_palette()`), acciones RPC `island_pos`/`island_palette` y las
  dos claves en `/state`.
- `panel/*`: en **Apariencia** las dos filas `.tag` informativas de la isla se
  sustituyen por controles reales — un segmentado Arriba/Abajo y un desplegable
  de paleta (el propio del panel) — con las claves i18n es/en
  (`ui.posBottom`, `ui.islandPalette`, `ui.islandPaletteHint`, `pal.*`). Los 72
  ids de `app.js` no se tocan: los controles se localizan por atributo
  (`[data-island-pos-val]`, `select[data-island-palette]`).

**Validación (medida):**
- Posición: inyectando `WM_HOTKEY(47124)` (Alt+Q) con `PostThreadMessage` y
  cancelando con 47125. `work_area=(0,0,1920,1080)`; ventana de la isla 146×45.
  **Arriba**: rect `(887,0,1033,45)` → `top = 0` = borde superior. **Abajo**:
  rect `(887,1025,1033,1070)` → `bottom = 1070` = 1080 − 10. Alfa del
  fotograma (`render_island_rgba`): arriba el cuerpo opaco está en la PRIMERA
  fila (máx 247-255) y la sombra cae en la última (≤63); abajo se invierte
  (última fila 247, primera ≤51) → sombra del lado correcto.
- Paleta: fotograma por preset en ambos temas; color central de la onda
  oscuro/claro — grafito #5490EB/#1E77D3, oceano #2669D8/#0C47AC, ambar
  #EB8C2E/#C55F07, menta #2EBB81/#0C7C54, frambuesa #EB3A6A/#BB1348, violeta
  #8252EB/#5424BB. 6/6 frames distintos por md5 en cada tema.
- Panel (CDP, WebView2 real): 0 excepciones, 0 textos sin traducir; clic en
  Arriba/Abajo cambia `/state.island_pos`; elegir «Violeta» en el desplegable
  propio cambia `/state.island_palette`. Persistencia comprobada tras reiniciar
  la app. `dicta_crash.log` 0 B.

---


## 33. El panel dejaba un hueco vacío abajo (el pie se estiraba)

**Reportado:** el pie («Salir / v1.0 / Probar micrófono / Listo») quedaba a
~663 px sobre una ventana de 781 y por debajo había ~120 px de nada.

**Diagnóstico (medido por CDP sobre la ventana real):** el backend WebView2
inyecta su barra y **oculta `.app-head`** (`display:none`). Como las filas del
`.shell` iban por ORDEN (`grid-template-rows: auto minmax(0,1fr) auto`), al
desaparecer la cabecera los items se corrían una fila: `.app-body` caía en la
fila `auto` y `.app-foot` en la `1fr`, así que el pie se tragaba todo el hueco
—medido: pie de **188 px** sobre 781 y de **227 px** sobre 820, con el cuerpo
clavado en 557—. No era que faltara `height:100%`: la ventana se llenaba, pero
la fila que crecía era la equivocada.

**Cambio (`panel/style.css`):** `.app-head/.app-body/.app-foot` llevan
`grid-row: 1/2/3` explícito, así que ocultar la cabecera ya no desplaza nada.

**Validación (CDP, ventana real, tras el arreglo):** `grid-template-rows` =
`0px 727px 57px` @1040×820 y `0px 507px 57px` @1040×600; pie de **57 px** fijo
en los dos y a **0 px** del borde inferior (hueco por debajo = 0, no 120).

## 36. Audio de la reunión: dos fallos reales (tirones y saturación)

El autor reportó que el audio grabado del micro sonaba **entrecortado** y, antes,
**muy bajo**.

**1. La ganancia del micro satu­raba.** La ganancia automática medía el RMS sobre
el trozo **ya rellenado con silencio**, así que salía hundido, la ganancia se
disparaba hasta **×16** y al entrar voz de verdad el recorte duro (`np.clip ±1`)
la saturaba: eso suena a tirones. Ahora el RMS se mide **solo sobre las muestras
reales** del micro, la ganancia es adaptativa (sin umbrales que adivinen), el tope
baja a **×6** y el recorte duro se cambia por un **limitador suave** (`tanh`) que
no puede crujir. Simulado con los valores de este equipo: silencio → ×1 (no sube
el ruido); voz baja (RMS 0,004) → ×4,1 con pico 0,06; voz normal (0,020) → ×3,3 con
pico 0,28; golpe fuerte (0,40) → pico 1,0 limitado, nunca recortado.

**2. El mezclador metía huecos de 0,25 s.** Medido sobre un `.wav` real: **83
tramos de CERO EXACTO, el mayor de 251 ms** — justo el bloque de 0,25 s. El micro
y el audio del sistema entregan bloques de 0,25 s que llegan **desfasados**, y el
mezclador rellenaba con silencio la pista que iba corta en cada vuelta: la voz del
micro se cortaba a trozos. Ahora cada pista se **acumula** y se consume
`min(len(sys), len(mic))`, o sea solo la parte donde existen **las dos**: no se
inventa audio. Si una pista se queda muda más de 3 s (productor muerto) se
rellena para no parar la grabación, y queda dicho en el registro.

**Validación (la misma prueba que lo detectó):** `.wav` de 8 s antes y después,
contando tramos de cero exacto > 1 ms y saltos bruscos entre muestras.

| | antes | después |
|---|---|---|
| sistema (L) | 83 tramos (mayor 251 ms) | **0** |
| micro (R) | 83 tramos (mayor 251 ms) | **0** |
| clics (saltos bruscos) | 0 | 0 |
| RMS / pico del micro | 0,0001 / 0,0010 | 0,0067 / 0,0631 |

**Icono unificado (lo pidió el autor).** El de la barra del panel era un **SVG
dibujado a mano** (5 barras) mientras la bandeja, el `.ico` y la barra de tareas
salían del render real (`wave_mark`, 3 barras): dos dibujos distintos. Ahora la
app sirve el render **real** por HTTP (`GET /panel/icon.png?size=&theme=`, con
caché por tamaño y tema) y lo usan la barra y el favicon. Comprobado **píxel a
píxel** contra el render de la bandeja: md5 idénticos y diferencia máxima de canal
**0**, a 18 y 36 px y en los dos temas (`3f0a3e2264cc`, `64cff2d7c08a`,
`41d99de17120`, `41621d849315`).

## 38. Panel: 25 acciones pasan de texto a icono

El autor pidió apoyarse en iconos en vez de prosa para acciones como descargar,
eliminar o cerrar. Se convierten **25 botones** (19 estáticos en `index.html` y 6
que genera `app.js`), todos del mapa `ICONS` que ya existía: rejilla 24×24,
`stroke-width` 2 por debajo de 18 px y 1,8 por encima, remates redondeados,
`currentColor` y sin relleno, con un constructor único (`iconSVG`). **Ni una
librería, ni un glifo nuevo, ni un id nuevo**: los 72 ids que usa `app.js` siguen
existiendo.

Cada icono lleva `aria-label` y `title` (el de texto se ve al pasar el ratón; el
de accesibilidad lo leen los lectores de pantalla), también en los 6 dinámicos.
Piezas nuevas en `app.js`: `iconSVG`, `paintIcons` (idempotente), `setIcon`,
`confirmState`, `paintSaveBtn` y `data-i18n-title` (ES/EN). CSS: `.btn-icon`
cuadrado y su variante en las filas.

**Siguen con texto a propósito**: los `.md`/`.txt` (son formatos, no acciones) y
los cuatro botones de los segmentados «Claro/Oscuro» y «Arriba/Abajo» (son
valores, no acciones).

Verificado con 31 capturas de Chrome headless en tema claro y oscuro (incluida la
vista real del backend WebView2), 0 excepciones de consola, 0 textos sin traducir
en ES y EN, y **0 botones de icono sin `aria-label`+`title`**. Interacciones
comprobadas de verdad por clic: guardar (`is-saved`, icono verde, revierte a
1,2 s) y eliminar (`¿Eliminar?` con relleno rojo, conservando los dos clics).

## 45. Los ficheros subidos quedan guardados y son fichas propias

Antes, lo que el autor subía (audio, vídeo o cualquier formato) iba a una zona
pasajera y desaparecía al cerrar la app. Ahora vive en una carpeta propia
`uploads/` con su manifiesto `uploads/uploads.json` (escritura atómica), expuesta
en `/state` como `uploads` con nombre, peso, documento asociado, duración y estado
(pendiente/transcribiendo/listo/error), y se quita con
`POST {"action":"upload.remove"}` (valida el nombre: rutas y `..` dan 404; los
nombres duplicados se renumeran para que quitarlos sea inequívoco).

En el panel, cada fichero subido es **su propia ficha**, con la misma piel que las
tarjetas de Documentos, separada de la carta de «Añadir audios»: azulejo según el
tipo, nombre real, peso y duración, etiqueta de estado y barra solo mientras
transcribe. La acción es **quitar** (en dos pasos), no descargar: el autor ya
tiene el fichero. Si ese fichero ya tiene transcripción, un acceso lleva a la
ficha de ese documento y la despliega, sin duplicar el texto.

Comprobado con la app viva: subir un `.wav` → aparece en `uploads`; **reiniciar la
app** → vuelve idéntico (mismo id, peso, documento y estado); quitarlo → 200 y el
fichero desaparece del disco. Guardas: `../dicta_config.json` → 404 sin tocar nada.

---

## 46. Umbral de voz, espera antes de transcribir, diccionario en lote, micro de la reunion, atajo de parada y motores/modelos en /state

Seis cambios pedidos por el autor, cada uno con su medicion contra la app viva
(puerto 47810). Todo se cambio en `dicta.py`; no se toco `panel/*`.

### (1) Umbral de voz: `voice_threshold` (0..1)

**Que hacia `sens` de verdad.** `sens` NO era un umbral: era un **divisor** que
bajaba el suelo del detector adaptativo de ruido
(`thr = max(MIN_RMS, ruido*3) / max(0.2, sens)`). Es decir, subir `sens` bajaba
el liston, pero el liston seguia dependiendo del ruido de fondo: no habia un
umbral de voz claro ni absoluto.

Ahora el umbral lo fija el usuario y se aplica a la deteccion de voz del
dictado (`Mic._cb`): hay voz cuando `rms > thr`, con
`thr = voice_threshold / max(0.2, sens)`. `sens` sigue afinando (sigue
dividiendo) pero ya no decide el suelo.
- `voice_threshold` en `dicta_config.json` y en `/state` (0..1, RMS lineal);
  por defecto **0,006**. `POST {action:"voice_threshold", value}` lo cambia y
  lo persiste.
- `/state` publica ademas `rms`, `thr` y `voice` (bool) para verlo en vivo.

**Medicion** (misma senal ambiente del micro; solo cambia el umbral):

| `voice_threshold` | `thr` = vt/sens | `rms` ambiente | `voice` |
|---|---|---|---|
| 0,000005 | 0,000004 | 0,000046 | **true** (el ambiente dispara) |
| 0,00002 | 0,000014 | 0,000038 | **true** |
| 0,001 | 0,000714 | 0,000149 | **false** (el ambiente no dispara) |
| 0,05 | 0,035714 | 0,000142 | **false** |

### (2) Espera antes de transcribir: `silence_wait` (0,2 s .. 600 s)

El corte del dictado por silencio tenia un tope duro de 0,4-3 s (~1 s). Ahora
`silence_wait` se admite de **0,2 s a 600 s (10 minutos)**: se puede dejar una
pausa larga para pensar sin que se corte la idea. Publicado en
`/state.silence_wait`; `POST {action:"silence_wait", value}`.
El dictado cierra cuando
`now - last_voice >= silence_wait` (hilo de servicio, cada 40 ms).

**Medicion** (dictado arrancado por API, `voice_threshold` alto para que el
ambiente no cuente como voz; se mide cuanto tarda el estado en dejar de ser
`recording`):

| `silence_wait` | dejo de "recording" a los | nota |
|---|---|---|
| 0,5 s | **0,52 s** | — |
| 12,0 s | **12,02 s** | a los 4,0 s seguia en `recording` |
| 1000 (pedido) | 600,0 | tope maximo aplicado |
| 0,0 (pedido) | 0,2 | suelo minimo aplicado |

### (3) Diccionario en lote

`POST {action:"dictionary", value}` acepta ahora **una lista O un texto** con
las palabras separadas por **coma, punto y coma o salto de linea**. Se
normalizan, se quitan duplicados (sin distinguir mayusculas) y se convierten en
el `initial_prompt` de Whisper (campo `prompt` del servidor GPU; `--prompt` en
el camino CPU). Se aplica igual al dictado, a los audios subidos y a la reunion.

Ejemplo medido: un solo POST con el texto
`"Zafirok\nOtraPalabra, tercera, IoT"` deja
`/state.dictionary = ["Zafirok","OtraPalabra","tercera","IoT"]`.

**Medicion** del efecto real (audio TTS con la palabra inventada "Zafirok"):

| `dictionary` | transcripcion de "…se llama Zafirok…" |
|---|---|
| `[]` | "…se llama **Zafiroki**…"  (mal) |
| `["Zafirok", …]` (en lote) | "…se llama **Zafirok**…"  (bien) |

### (4) El microfono de la REUNION usa el mismo micro que el dictado (y lo sigue)

**Diagnostico.** El productor de micro de la reunion leia
`config_get("mic")` **una sola vez**, al arrancar la sesion; si el autor
cambiaba de microfono (ajuste del dictado), la reunion seguia capturando del
dispositivo viejo. Ademas guardaba el stream abierto, sin reaccionar.

**Arreglo.** `sd_mic_producer` ahora **consulta `config_get("mic")` en cada
giro (~0,25 s)** y, cuando cambia, **cierra el stream viejo y abre el nuevo en
el MISMO hilo** (nunca queda un hilo antiguo capturando del dispositivo
anterior). El dispositivo en uso se publica en `/state.meeting.mic`.

**Medicion** (reunion activa; se cambia el micro del dictado con `POST mic`):

| evento | `mic` dictado | `meeting.mic` | `level_mic` observado |
|---|---|---|---|
| inicio reunion | 1 | **1** | 0,0010-0,0022 |
| tras `POST mic=0` → cambio en **0,25 s** | 0 | **0** | 0,0025-0,0057 |

En `dicta.log`: `Reunion: micro del dictado -> indice 1 (Microfono (Webcam
AC410))` y, al cambiar, `-> indice 0 (Asignador de sonido Microsoft - Input)`.

### (5) Atajo dedicado a DETENER la reunion + atajos libres (1, 2 o 3 teclas)

- Quinto atajo **`meeting_stop`**, de fabrica **ctrl+alt+s**: detiene (guarda)
  la reunion sin pasar por el iniciar/parar (ctrl+alt+r) y es idempotente (si
  no hay reunion activa, no hace nada). Igual que los demas, corre en su hilo.
- Todos los atajos aceptan **1, 2 o 3 teclas simultaneas** y se validan:
  se rechaza la combinacion invalida con un motivo claro, sin tocar el atajo
  vigente. `POST {action:"hotkey", value:{"name":NOMBRE,"keys":"..."}}` con
  `NOMBRE` en `dictation|cancel|panel|meeting|meeting_stop`.
- `/state.hotkeys` publica los cinco:
  `{dictation, cancel, panel, meeting, meeting_stop}` (y `meeting_stop_key`).

**Medicion** (contra la app viva):

| keys | valido | resultado |
|---|---|---|
| `f9` | si | 1 tecla, aceptada |
| `alt+f9` | si | 2 teclas, aceptada |
| `ctrl+alt+j` | si | 3 teclas, aceptada |
| `a+b` | no | `only one main key allowed` |
| `ctrl+ctrl+a` | no | `duplicate modifier: ctrl` |
| `ctrl+alt+shift+f5` | no | `too many keys (max 3)` |
| `xyz` | no | `unknown key: xyz` |
| `` (vacio) | no | `empty` |
| `ctrl+alt` | no | `missing main key` |
| `ctrl++a` | no | `empty part` |

Tras las pruebas, `meeting_stop` vuelve a `ctrl+alt+s` y los cinco quedan:
`dictation=alt+q, cancel=ctrl+e, panel=ctrl+alt+p, meeting=ctrl+alt+r,
meeting_stop=ctrl+alt+s`.

### (6) Modelos (nombre completo) y motores (vulkan / cuda / cpu / rocm) en /state

- **`/state.models`**: lista con `key`, **`name` completo** y `present` (si el
  fichero esta descargado). Se anadio el modelo `large`.
- **`/state.engine_options`**: las opciones seleccionables con etiqueta y
  **`available`** segun el hardware de este equipo. `engines` sigue siendo la
  lista de las disponibles (lo que pinta el panel).
- Selector guardado en config: `POST {action:"engine", value}`. Si el motor
  pedido **no esta disponible**, se guarda igual, `/state.engine` lo refleja y
  `/state.engine_note` da un **mensaje claro** de a que se cae.

| key | name | present |
|---|---|---|
| tiny | Whisper Tiny | true |
| base | Whisper Base | true |
| small | Whisper Small | true |
| medium | Whisper Medium | false |
| large | Whisper Large v3 | false |
| turbo | Whisper Large v3 Turbo | true |

| motor | etiqueta | disponible aqui |
|---|---|---|
| auto | Automatico | true |
| vulkan | GPU (Vulkan) | **true** (el de este equipo) |
| cuda | GPU (CUDA, NVIDIA) | false (seleccionable para un usuario NVIDIA) |
| rocm | GPU (ROCm, AMD) | false (seleccionable; no hay binario ROCm aqui) |
| cpu | CPU | true |

**Medicion** de la seleccion con aviso:

| POST engine | `/state.engine` | `engine_resolved` | `engine_note` |
|---|---|---|---|
| cuda | cuda | cpu | "GPU (CUDA, NVIDIA) no esta disponible en este equipo; se usara CPU." |
| rocm | rocm | cpu | "GPU (ROCm, AMD) no esta disponible en este equipo; se usara CPU." |
| cpu | cpu | cpu | (vacio) |
| vulkan | vulkan | vulkan | (vacio) |

`dicta_config.json` guarda `engine` (quedo en `vulkan`) junto a las nuevas
claves `voice_threshold`, `silence_wait` y `meeting_stop_key`.

### Notas

- El orden/indice de dispositivos de PortAudio **cambia entre arranques** en
  este equipo: el micro guardado (indice 2) dejo de abrir
  (`Invalid number of channels`). Se ajusto el micro del dictado al primer
  indice valido de la "Webcam AC410" (**indice 1**), que captura de verdad
  (medido `rms ~ 1,4e-05`). No se cambio el codigo de enumeracion.
- No se toco: `panel/*`, `dicta_icon.py`, la clase de reunion (ganancia,
  mezclador alineado por tiempo, `_normalize_wav`, parrafos con `PARA_MAX`),
  `/state.levels` (12 bandas sys/mic), `MicTest`, `doc.rename`/`doc.delete`,
  `GET /panel/icon.png`, `GET /download`, las subidas persistentes
  (`uploads/`), el cierre limpio con `shutdown_service`, ni la instancia unica.
- Los cuatro atajos de siempre siguen igual (alt+q, ctrl+e, ctrl+alt+p,
  ctrl+alt+r); solo se anade ctrl+alt+s.
- La app quedo **viva** (`GET /state` 200), micro funcionando y `st=idle`.

---

## Archivos tocados

| Archivo | Cambio |
|---|---|
| `dicta_shell.py` | **NUEVO.** Ventanas layered con prototipos Win32 correctos; burbuja, notch rápido, `wave_mark` |
| `dicta_capture.py` | **NUEVO.** WASAPI *process loopback* en ctypes puro |
| `test_capture.py` | **NUEVO.** Prueba E2E de la captura por aplicación (tono real por PID) |
| `dicta_icon.py` | **NUEVO.** Renderizador del icono a partir de la marca única |
| `dicta.ico` | **NUEVO.** Icono multirresolución 16-256 px |
| `dicta_ui.py` | `NotchWindow` sobre `LayeredWindow`; `SPI_GETWORKAREA` 0x0030; icono de bandeja |
| `dicta.py` | Burbuja y notch conectados; fuente de audio por aplicación; `GET /peaks`; prototipos Win32; título e icono del panel |
| `panel/*` | Vista previa de audio, selector de fuente, burbuja y coherencia visual |
| `dicta.spec` | `dicta.ico` en el bundle y módulos propios en `hiddenimports` |
| `README.md`, `CHANGES.md`, `DESIGN.md` | Documentación de todo lo anterior |
| `dicta.py` | MeetingTranscriber v2 (sistema+micro, WAV, pausa/cancelar/guardar), RPC `meeting` ampliado, `doc.delete`, `doc.open`, `GET /audio`, `src` en cola, `audio` en docs, fix COM en `start()` |
| `panel/index.html` | Hub de reunión (inicio/vivo/resumen), acciones de documentos |
| `panel/app.js` | Estados del hub, doc.delete, descargas de audio, i18n es/en |
| `panel/style.css` | Estilos del hub, acciones de fila, confirmaciones, pulido general |
| `README.md` | Documentación de grabación, pausa, cancelar, eliminar y descargas |

## 34. El `.exe` congelado arranca, pero el WebView2 congelado no: cae a Chrome

**Qué se probó:** el build congelado nunca se había arrancado desde que el panel
pasó a pywebview + pythonnet. El `.exe` lleva `uac_admin=True`, así que lanzarlo
sin elevar da **WinError 740**; la comprobación se hizo con el MISMO `dicta.spec`
y `uac_admin` apagado (el binario se diferencia solo en el manifiesto, +158 B).

**Resultado (`dist/dicta/dicta.exe`, 7.716.658 B, 17:48):**
- Arranca y sirve: `GET /state` 200 en 47810, `dicta_crash.log` **0 bytes**,
  `dicta 1.0 listo — … (elevado: no)`, motor Vulkan listo, panel abierto.
- El WebView2 **congelado falla**: `WebView2 no arrancó (Failed to resolve
  Python.Runtime.Loader.Initialize from _internal/pythonnet/runtime/Python.Runtime.dll)`
  y el panel sale por el respaldo:
  `Panel: backend Chrome/Edge (ventana en modo aplicación)`.
- **No es de Dicta**: una app congelada mínima reproduce lo mismo. El
  `Python.Runtime.dll` del bundle es el del venv (md5 `fba31f75…`), el .NET puro
  lo carga desde las tres rutas con `Assembly.LoadFrom`, y el shim de
  `clr_loader` 0.3.1 (`pyclr_get_function`) solo resuelve
  `Python.Runtime.Loader.Initialize` cuando la ruta es exactamente
  `.venv/Lib/site-packages/pythonnet/runtime/Python.Runtime.dll`: una copia en
  `_internal`, en `.tmp` o con otro nombre en el mismo directorio devuelve
  puntero nulo.
- Ficheros tocados: **ninguno** (`dicta.spec` intacto); datos crudos en
  `.tmp/steps/dicta_exe_run.log`, `verify_final.txt`, `panel_exe.png`.

**Pendiente:** el WebView2 en build congelado (parece bug de clr_loader/pythonnet
en proceso frozen). El respaldo de Chrome funciona y se activa solo.

## 35. El icono de la barra del panel es el icono REAL (bandeja/.exe)

**Problema reportado:** *«que los iconos sean consistentes: el icono dentro de la
aplicación, al lado del título en el panel, debe ser el mismo que el de la
bandeja de Windows»* y *«me gusta más cómo se ve el de la bandeja»*.

**Diagnóstico:** la bandeja, el `.ico` del `.exe` y el icono de la barra de
tareas salían los tres de `dicta_icon` (la onda, `variant="mark"`, azulejo
translúcido) — consistentes entre sí. El que divergía era el de la **barra del
panel**: `panel/desktop.js` dibujaba un **SVG en línea escrito a mano** (5 trazos
de 1,4 px), una aproximación de la onda, no el dibujo real.

**Cambios:**
- `dicta.py`: ruta nueva **`GET /panel/icon.png?size=<px>&theme=light|dark`**.
  Llama a `_panel_icon_png()`, que renderiza con **los mismos parámetros que la
  bandeja** (`dicta_icon.render_icon(size, variant="mark", bg=False, theme=…)`,
  el azulejo translúcido incluido) y **cachea el PNG en memoria** por
  (tamaño, tema). Cabeceras `Content-Type: image/png` y `Cache-Control: no-store`.
- `panel/desktop.js`: el `<span class="dtbar-brand">` pasa de un SVG en línea a
  un **`<img src="/panel/icon.png?size=…&theme=…&v=1">`** de **18 px CSS**
  (pedido al doble —36 px— según `devicePixelRatio`, con tope 2, para que quede
  nítido en pantallas con escalado). Un `MutationObserver` sobre
  `data-theme` vuelve a pedir el icono al cambiar de tema; si el PNG no llegara,
  cae al SVG de respaldo (no deja hueco). El resto de la barra (título, pil,
  botones) no se toca.
- `panel/index.html`: el **favicon** deja de ser un SVG en línea y pasa a
  `/panel/icon.png?size=32&v=1` (el mismo dibujo).

**Validación (píxeles, no a ojo):**
- PNG servido vs. imagen EXACTA de la bandeja (`dicta_ui.make_tray_image`), a
  18 px, **los dos temas**: md5 del PNG **idéntico** (oscuro
  `3f0a3e2264ccbf20de3602619367b945`, claro
  `41d99de171203288aa7c2f11ee01a61c`), md5 del RGBA idéntico y **diferencia
  máxima de canal = 0**.
- Captura de la **ventana real** (ctypes `GetWindowRect` + `ImageGrab` con
  `SetProcessDpiAwareness(2)`): el icono está en **(x=12, y=9), 18×18** (padding
  `--sp-3`=12 px, centrado en la barra de 36). Su **máscara de onda coincide al
  100 % (IoU = 1,00)** con el render real de 18 px, tiene **3 barras** (el SVG
  viejo tenía 5) y el título «Dicta» empieza a su derecha (x≈39). Capturas:
  `.tmp/panel_window.png`, `.tmp/bar_left.png`, `.tmp/bar_icon_zoom.png`.
- `node --check panel/desktop.js` OK; los **72** `$("#id")` de `app.js` siguen
  existiendo en `index.html`; `GET /state` **200**; `dicta_crash.log`
  **0 bytes**.

## Notas
- Los `.tmp/*.py` de prueba se eliminaron al terminar (queda solo
  `.tmp/panel-profile`, el perfil de Chrome que usa el panel en caliente).
- `reunion-190037.md` y `reunion-190057.md` (14 B) ya existían antes de este
  trabajo y no se han tocado.
- La instancia de la app se relanzó para que el backend nuevo quede activo en
  `127.0.0.1:47810`.
- `assets/` guarda solo material de diseño: `_icon_check.png` (el icono que va
  montado, a tamaño real y ampliado, en los dos temas), `_icon_bw16.png`
  (legibilidad sin color) y `_candidates.png` con los cuatro conceptos
  alternativos (`cand-a…d.png` a 512 px) por si algún día se quiere cambiar.
- `audios/test.flac` es la copia que hace reproducible la comprobación
  `GET /peaks?name=test.flac`.

---

## 37. Reunión: el .wav se oye a nivel normal (pico -3 dBFS) y el .md sale en párrafos

**1. La grabación sonaba muy baja.** Palabras del autor: *«cuando grabas el audio
de las reuniones y del micro se escucha todo muy bajo incluso subiendo al 100 %
el volumen de mis altavoces y de windows todo al 100 % se escucha demasiado bajo,
no se entiende»*. Medición real del `.wav` de entonces: **pico 0,0631 (-24 dBFS),
RMS 0,0067**.

**Solución:** al cerrar la reunión (y solo para escuchar; la transcripción es en
vivo sobre la mezcla, no le afecta) se pasa **una vez** por el `.wav` con la
función nueva `_normalize_wav()`: lee el fichero, calcula **UNA** ganancia para
que el **pico** quede en **-3 dBFS** y reescribe con `soundfile` (PCM_16). Dos
topes evitan amplificar el silencio/ruido:
- `floor_peak=0,01`: si el pico ya es menor, es una sala en silencio y el fichero
  se deja **tal cual** (ganancia ×1).
- `max_gain=20`: tope absoluto (una grabación como la de este equipo necesita
  ~×11; 20 da margen de sobra).

Se conserva la ganancia adaptativa en vivo de la mezcla (`_mix_gain`/`tanh`) que
ya existía; la normalización del cierre la redondea hasta el nivel de escucha.

**Validación A (función aislada, ficheros sintéticos de pico conocido):**

| pico entrada | dBFS entrada | ganancia | pico salida | dBFS salida |
|---|---|---|---|---|
| 0,050 | -26,02 | ×14,16 | 0,7079 | **-3,00** |
| 0,200 | -13,98 | ×3,54 | 0,7079 | **-3,00** |
| 0,600 | -4,44 | ×1,18 | 0,7079 | **-3,00** |
| 0,003 (silencio) | -50,48 | ×1,00 | 0,003 | -50,48 (**sin tocar**) |
| **0,0631 (caso real)** | **-24,00** | **×11,22** | **0,7079** | **-3,00** |

**Validación B (reunión real con la app, POST `meeting start/stop` a 47810),
midiendo el `.wav` con `soundfile`+`numpy`:** dos reuniones grabadas (se
reprodujo por el altavoz por defecto un `.wav` de voz para que el loopback
tuviera audio y whisper transcribiera de verdad, ~105 s y ~69 s):

| reunión | pico | dBFS | RMS | dBFS |
|---|---|---|---|---|
| `reunion-…-184008.wav` | 0,7079 | **-3,00** | 0,0678 | -23,38 |
| `reunion-…-184221.wav` | 0,7079 | **-3,00** | 0,0773 | -22,24 |

El registro de la app lo confirma: `Reunión nivel: pico … -> -3.0 dBFS (ok)`.

**2. La transcripción se cortaba en líneas de 26 s.** Palabras del autor: *«el
formato de transcripción no es tan natural para la lectura… pones marcas de
tiempo y los vas cortando por saltos de línea pero se pierde el contexto de ese
párrafo»*. Antes, cada ventana de 26 s se escribía con **su** `**[HH:MM:SS]**` y
un salto: una marca de tiempo cada 26 s, partiendo frases a la mitad.

**Solución (dicta.py, `MeetingTranscriber`):** los fragmentos **consecutivos** se
**agrupan en un párrafo** (se unen con espacios, **sin resumir ni perder nada**)
y el párrafo lleva **UNA sola marca de tiempo al principio**. El párrafo se cierra
en un **corte natural**: silencio al final de la ventana (se mide la cola de 2 s
contra un nivel de voz de referencia, porque el micro de este equipo entra muy
bajo y un umbral fijo no sirve) o al llegar a `PARA_MAX` = 60 s (tope para que
nunca quede un párrafo eterno si no hay silencio). El remanente final se une al
último párrafo y se cierra al terminar.

**Validación:** el `.md` de la reunión real pasó de una marca por ventana a
**3 párrafos con 3 marcas** (`**[18:40:08]**`, `**[18:41:26]**`, `**[18:41:52]**`)
sobre ~105 s de voz continua, con el texto unido (español intacto). Ejemplo:
`**[18:40:08]** la que está en la emisión durante 7 minutos…` (un párrafo largo,
natural, con su única marca al inicio).

**Archivos tocados:** `dicta.py` (`_normalize_wav`, llamada en el cierre de la
reunión, agrupación en párrafos; `self.level_note`) y este `CHANGES.md`. No se
tocó `panel/*`, `dicta_ui.py` ni `dicta_icon.py`.

**Limpieza:** los `.wav` y `.md` de prueba de las dos reuniones y los scripts
temporales (`test_norm.py`, `player.py`) se borraron al terminar. `dicta_crash.log`
**0 bytes**. La app quedó **ARRANCADA y viva** en `127.0.0.1:47810` (`GET /state`
**200**).

---

## 39. Panel · Documentos: cartas separadas, flecha, formatos distintos y renombrado en línea

**Problema reportado (cuatro cosas):** (1) dos grabaciones parecían **una sola
carta**; (2) faltaba una **flecha** que dijera que la fila se puede desplegar y
leer; (3) los dos botones de descarga eran **el mismo icono** y el formato
(`.md` / `.wav`) solo estaba en el tooltip; (4) no se veía el **nombre real** del
fichero ni se podía **renombrar**.

**Cambios (`panel/style.css`, `panel/app.js`, `dicta.py`):**
- Cada documento es una **CARTA** (`--surface-2` + `--lift-1` + `--r-control`),
  con hueco entre cartas. Antes solo había un `border-top` y dos filas contiguas
  se leían como una sola.
- **Flecha** (`chevron-right`) en cada carta que **gira 90°** al desplegar
  (`aria-expanded` + `transform: rotate(90deg)`). El cuerpo desplegable enseña el
  reproductor del `.wav` y un **sondeo de la transcripción** (primeros ~500
  caracteres) + botón **«Abrir transcripción»**.
- Las **dos descargas** llevan **iconos distintos** (`file-text` para el `.md`,
  `file-audio` para el `.wav`) y **el formato a la vista** en la propia fila
  (`.md` / `.wav`), no solo en el tooltip. Se conserva el enfoque de iconos
  (`iconSVG`/`paintIcons`) y cada botón su `aria-label` + `title`.
- El **nombre REAL** del fichero se muestra en la fila; **doble clic** lo vuelve
  un campo **en línea, sin modal**, con su extensión como etiqueta fija. `Enter`
  guarda, `Escape` sale, perder el foco guarda. Si el nombre ya existe, el campo
  se marca en rojo y sale el aviso.
- **`dicta.py` · `POST {action:"doc.rename", doc, name}`** (mismo patrón que
  `doc.delete`): renombra el `.md` y su `.wav` **emparejado**, con el mismo nombre
  base y **las extensiones intactas** (`os.replace`, atómico en el mismo volumen);
  valida el nombre (sin `..`, `\`, `/`, caracteres prohibidos ni espacios
  finales) y responde **409 `exists`** si ya hay un `.md` **o** un `.wav` con ese
  nombre. Deja en el log `Documento renombrado: <old> -> <new>`. NO se tocó el
  audio de la reunión (clase `Meeting`).

**Validación con cifras:**
- Renombrado real por la **UI** (doble clic → campo en línea → Enter) contra la
  app viva: `/state` pasó de `prueba-renombrada.md` a `prueba-por-ui.md` y en
  disco quedaron **`textos/prueba-por-ui.md`** **y** **`audios/prueba-por-ui.wav`**
  (extensión conservada en los dos). Aviso de nombre repetido:
  **`409 {"error":"exists"}`** y en la fila **«Ya existe un fichero con ese
  nombre.»** con el campo en rojo, sin renombrar.
- Chrome headless (CDP) contra `http://127.0.0.1:47810/panel`, **claro y oscuro**:
  dos cartas con rects separados (`[135,185]` y `[193,243]`, **8 px** de hueco),
  **formato visible** en cada fila (`.md`, `.wav`), flecha con
  `transform: matrix(0,1,-1,0,0,0)` (= 90°) al desplegar, cuerpo desplegado con
  sondeo y reproductor, y **0 `Runtime.exceptionThrown`**. Capturas en
  `.tmp/shots-docs/docs-{claro,oscuro,renombrando,existe}.png`.
- `node --check panel/app.js` y `ast.parse(dicta.py)` OK. `dicta_crash.log`
  **0 bytes**.

**Limpieza:** el documento de prueba y su `.wav` se borraron por **nombre
exacto**; no quedan restos en `textos/` ni en `audios/`. Los `.bak` del panel
viven en `.tmp/`.

---

## 40. Icono oficial único, tema claro por defecto, atajo global de reunión y prueba de micrófono

Cuatro cambios de backend (`dicta.py`, `dicta_icon.py`, `dicta_config.json`).

**(1) Tema por defecto = claro.**
- `App.__init__` y `_panel_icon_png` pasan a `config_get("theme", "light")`;
  `dicta_config.json` queda con `"theme": "light"`. Un usuario que ya eligió
  oscuro lo conserva (el valor se lee de config): solo cambia el de fábrica.

**(2) Un solo icono oficial: el render de la bandeja.**
- Nuevo `dicta_icon.official_image(size, theme)` = `render_icon(size,
  variant="mark", bg=False, theme=theme)` (la marca `wave_mark` sobre el azulejo
  translúcido); `ico_render` delega en él. Es el ÚNICO dibujo del aplicativo.
- `dicta.py` añade `_official_icon_ico(theme)` (escribe un `.ico` por tema con
  `write_ico(..., variant="mark")`) y `_wm_set_icon(hwnd, theme)` (WM_SETICON
  ICON_SMALL + ICON_BIG). La ventana/barra de tareas, el `icon=` de WebView2 y
  la barra del panel + favicon salen todos de ahí; `on_theme` re-aplica el icono
  de la ventana y re-renderiza el de la bandeja (`icon.icon =
  make_tray_image()`). Antes la ventana cargaba el `dicta.ico` estático
  (oscuro) y divergía de la bandeja con el tema claro.

**Validación (píxeles/md5):** 2 temas × 5 tamaños, bandeja
(`dicta_ui.make_tray_image`), barra del panel (`official_image`), fotograma del
`.ico` y favicon servido por `GET /panel/icon.png?size=&theme=` dan el MISMO md5
(claro 32 px → `0566e10b`), y los bytes PNG embebidos del `.ico` son idénticos
al PNG del render. Extrayendo el **HICON real** de la ventana (`WM_GETICON` +
`GetDIBits`): 32 px `0566e10b` y 16 px `afb3473d`, iguales al render oficial
claro. (`.tmp/verify_icon.py`, `.tmp/hicon_check.py`)

**(3) Atajo global del modo reunión (Ctrl+Alt+R).**
- Cuarto `HotkeyManager` (`hk_id=47127`, evento `"meeting"`), registrado en
  `serve()` desde `config_get("meeting_key", "ctrl+alt+r")` y liberado en
  `quit()`. `service_app` lo atiende y llama a `_toggle_meeting()` en un hilo
  (start/stop sin bloquear Tk).
- `/state` publica `hotkeys.{dictation,cancel,panel,meeting}`.
- POST `{action:"hotkey", value:{"name":"meeting","keys":"..."}}` cambia y
  persiste el atajo (nombres dictation/cancel/panel/meeting; nombre inválido →
  `{"ok":false,"error":"unknown name"}`).

**Validación:** el log muestra *"Hotkey global ctrl+alt+r registrada"*. El
sandbox no deja inyectar teclado sintético (`SendInput` retorna 1 pero las
teclas no llegan a este escritorio), así que se provocó el **WM_HOTKEY(47127)**
real al hilo del atajo: `/state` pasó de `meeting.active=false` a `true` con
`status="iniciando"`→`"grabando · 3 s"` y documento creado, y un segundo disparo
lo dejó en `false`/`"guardada"`. Cambiar el atajo por POST a `ctrl+alt+m` se
reflejó en `/state` y en `dicta_config.json`, y se restauró a `ctrl+alt+r`.
(`.tmp/hotkey_post.py`, `.tmp/hotkey_cfg.py`)

**(4) Prueba de micrófono de verdad.**
- Clase `MicTest`: captura ~5 s con `sd.InputStream`, publica `level` (0..1) en
  vivo por bloque y `peak` máximo; usa el **sample rate nativo del dispositivo**
  (antes 16 kHz fijo, que algunos dispositivos devolvían en silencio) y un tope
  DURO de fotogramas. Al terminar normaliza el `.wav` con `_normalize_wav` (la
  misma del `.wav` de reunión).
- POST `{action:"mic.test", value:"start"}` → `/state.mic_test={active, level,
  peak, done, wav}`; `GET /panel/mictest.wav` sirve lo capturado.

**Validación:** prueba real sobre el micro por defecto → `done=true`,
`peak=0.011` y `mictest.wav` de **5.00 s @ 44100 Hz** (441 KB, no el fichero
gigante de la primera versión). "El nivel sube con sonido" medido con la MISMA
fórmula (`level=min(1, rms/0.08)`) sobre audio real del loopback del sistema:
silencio `rms=0.0000 → level=0.000`; tono 1 kHz `rms=0.6465 → level=1.000`.
(`.tmp/mic_dev1.py`, `.tmp/level_loopback.py`)

Nota de entorno: aquí el único dispositivo de entrada usable es el headset
Bluetooth (que al reproducir pasa a A2DP y silencia su micro) y los Realtek no
son usables por PortAudio, por eso el "sube con sonido" se midió sobre audio
real del loopback con la misma fórmula.

**No se tocó** el audio de la reunión (`MeetingTranscriber`), `doc.rename`/
`doc.delete`, `GET /panel/icon.png` ni los atajos previos.

---

## 41. Onda REAL en el panel: energía por bandas y envolvente (se acabaron las líneas planas)

**Problema reportado:** *"todo se ve como líneas planas y no se entiende si se
está captando audio"*. El panel solo tenía un número de nivel (RMS) por pista,
así que dibujaba una raya.

**Cambios (`dicta.py`, backend):**

**(1) Bandas de frecuencia de la reunión → `/state.levels`.**
- Nuevo `_band_energies(x, sr)` (numpy): ventana de Hann + `rfft`, **12 bandas
  log-espaciadas de 40 Hz a 16 kHz** (bordes 40, 65, 108, 178, 294, 485, 800,
  1318, 2171, 3577, 5894, 9711, 16000), densidad de potencia corregida por la
  ventana (`sum(P) = RMS²`) y cada banda mapeada a 0..1 en escala dB
  (−80..−3 dB). Coste despreciable (una FFT por bloque).
- `MeetingTranscriber` calcula, en el bucle del mezclador y sobre el **último
  bloque** (~0,25 s), `levels_sys` y `levels_mic`. Publica `levels()` en
  **`/state.levels`** y también en `/state.meeting.levels`:
  `{"active", "sys":[12], "mic":[12], "sys_silent", "mic_silent"}`.
- El **micro de este equipo entra muy bajo** (RMS crudo ~0,001), así que sus
  bandas se miden sobre la señal YA GANADA (la misma que se oye en el `.wav`);
  el **silencio se decide sobre el RMS CRUDO**, no sobre la ganada.

**(2) Prueba de micrófono (`/state.mic_test`) → `duration` y `peaks`.**
- `duration` (5,0 s) se publica **desde el arranque** (antes de terminar) y
  `elapsed` va contando, para poder avisar al usuario del tiempo restante.
- `peaks`: **200 valores 0..1** con la envolvente (pico por tramo) del audio
  grabado, normalizada por su propio pico → el panel dibuja la onda de lo que se
  grabó en vez de una recta.

**(3) Silencio real explícito.** `silent: true` en `mic_test` y
`sys_silent`/`mic_silent` en `levels` cuando el RMS está por debajo de
`SILENT_RMS = 8e-4` (−62 dBFS). En ese caso `peaks` = 200 ceros, para que el
panel AVISE en vez de amplificar ruido y pintar una onda falsa.

**Validación (medición REAL contra la app viva, audio por el altavoz por
defecto vía loopback WASAPI):**
- **Sistema, en silencio:** `sys` = 12 ceros, `sys_silent=true`.
- **Sistema, tono multibanda 300/900/2500/6000 Hz:**
  `[0.222, 0.825, 0.246, 0.309, 0.825, 0.175, 0.804, 0.779, 0.084, 0, 0, 0]` →
  **9 valores distintos**, max−min **0,825**, `sys_silent=false`.
- **Sistema, `test.flac` (voz/música real):**
  `[0.568, 0.639, 0.604, 0.369, 0.249, 0.483, 0.446, 0.254, 0, 0, 0, 0]` →
  9 distintos, `level_sys=0.37`, `sys_silent=false`.
- **Micrófono, en silencio:** `mic_silent=true`, `level_mic=0.001`.
- **Micrófono, ruido fuerte por altavoces (acoplamiento acústico):**
  `[0.197, 0.306, 0.299, 0.214, 0.271, 0.300, 0.341, 0.262, 0.169, 0, 0, 0]`
  → suma **2,36** frente a **0,08** en silencio (**×29,7**), `level_mic=0.0087`,
  **`mic_silent` pasa a `false`**, 10 valores distintos.
- **`mic.test` en silencio:** `duration=5.0` desde el arranque,
  `elapsed` 0 → 1,25 → 5,0, `silent=true`, `peaks` = 200 valores **todos 0**.
- **`mic.test` con ruido:** `silent=false`, `peak=0.066`, `peaks` de 200 valores
  con **max 1,0, min 0,002, los 200 > 0,001** y 64–93 distintos → **no es una
  recta**.
- (``.tmp/probe_bands.py`, `.tmp/verify_sys.py`, `.tmp/verify_mic.py`,
  `.tmp/verify_mictest2.py`)

Nota de entorno: el único micro usable es el headset (`TA82`, RMS de reposo
~0,00003–0,001). No se puede "hablar" al micro sin el autor delante, así que la
reactividad del micro se midió con **estímulo acústico real** (ruido + tonos
fuertes por los altavoces, acoplados al micro); con el ruido sonando las bandas
suben ×29,7 y el flag de silencio se apaga. El habla normal entra aún más alto.

**No se tocó:** `panel/*`, `dicta_ui.py`, `dicta_icon.py`, la clase de reunión
(ganancia del micro, mezclador alineado por tiempo con `acc_sys`/`acc_mic`,
transcripción en párrafos), `_normalize_wav`, `doc.rename`/`doc.delete`,
`GET /panel/icon.png`, los atajos ni el `.wav`/servido de la prueba de micro.

---

## 42. El icono oficial: azulejo blanco OPACO y las 5 líneas de la bandeja

**Problema reportado:** *"el icono de la aplicación desde el panel y la
aplicación en general veo que el blanco es como un tono grisáceo, me gustaría
que el background fuera blanco para que resaltara más el icono, y que usara el
icono de la bandeja, que tiene como más líneas, entonces se ve como más
elaborado, que este que solo tiene tres líneas de colorcitos"*.

**(1) Antes de tocar nada: qué icono había de verdad.** Se extrajo el **HICON
real** de la ventana viva del panel (`WM_GETICON` + `GetIconInfo` +
`GetDIBits`) y los fotogramas del `.ico` que escribía la app, y se midió cada
uno (nº de líneas resueltas por columnas con color, y color/alfa del azulejo):

| superficie | tamaño | líneas | fondo | md5 (píxeles) |
|---|---|---|---|---|
| HICON vivo (ventana) | 32 px | **3** | `#FFFFFF` **alfa 165** | `0566e10b` |
| `.ico` viejo / 16 px | 16 px | **3** | `#FFFFFF` alfa 165 | `afb3473d` |
| `.ico` viejo / 64 px | 64 px | 5 | `#FFFFFF` alfa 165 | `2eda43a6` |
| barra del panel (`size=18`, dpr=1) | 18 px | **3** | `#FFFFFF` alfa 165 | — |
| bandeja (`make_tray_image(64)`) | 64 px | 5 | `#FFFFFF` alfa 165 | — |

O sea: el autor tenía razón en las dos cosas. **Su bandeja enseñaba la variante
de 5 líneas** (la bandeja renderiza a 64 px, que era el único tamaño que ya
dibujaba 5 barras), mientras la **barra del panel (18 px), el favicon (32 px) y
la barra de tareas/ventana (32 px)** dibujaban **3 barras**: `_small_geometry`
bajaba a 3 por debajo de 40 px. Y el azulejo iba a **alfa 165** en todas, así
que el blanco no era blanco: se mezclaba con lo que hubiera detrás (la barra de
tareas oscura de Windows lo dejaba gris).

**(2) Cambios (`dicta_icon.py`).**
- **Azulejo OPACO (alfa 255) en todas las tallas y temas**: blanco puro
  `#FFFFFF` en claro, grafito `#0E0F13` en oscuro. `bg=False` (lo que pasa la
  bandeja) se conserva por compatibilidad de firma pero ya no cambia el alfa.
- **Siempre 5 líneas**: nueva `icon_mark(size, bars=5)`, la marca del icono, con
  hueco fino (0,5 × ancho de barra) y la marca al 0,86 del lado. `wave_mark`
  (la onda ancha de la isla, 0,74 / 1,35) **no cambia**. `_small_geometry`
  devuelve 5 barras en todos los tamaños: se midió que a 16 px (2 px de barra,
  1 de hueco) las cinco líneas se resuelven bien.
- **Bug de Pillow corregido**: `rounded_rectangle` incluye los DOS extremos, así
  que `[x, .., x + bw, ..]` dibujaba barras de `bw+1` px y a 16 px los huecos de
  1 px desaparecían (las cinco líneas se leían como una sola mancha). Ahora la
  barra es exactamente `bw` px (rectángulo si `bw <= 2`, redondeado si no).
- `render_icon` pasa a 5 barras + azulejo opaco (afecta a bandeja, `.ico`,
  ventana y `ico_render` de una vez, que es el punto).

**(3) Cambios (`dicta.py`).**
- `_official_icon_ico` escribe el `.ico` cacheado con **versión en el nombre**
  (`dicta-icon-<tema>-6.ico`, `_ICON_ICO_VER`). El `.ico` se cachea en disco y
  solo se reescribía si faltaba: sin la versión, un cambio de dibujo seguiría
  enseñando el icono viejo en la ventana tras reiniciar el `.exe`/app. Los
  docstrings que decían "fondo translúcido" ahora dicen 5 líneas + azulejo
  opaco.
- **`GET /panel/icon.png?size=&theme=` NO cambia de contrato** (mismos
  parámetros, mismos límites 8..256, misma cabecera `no-store`): sigue sirviendo
  `official_image(size, theme)`, que ahora es el azulejo opaco con 5 líneas. La
  barra y el favicon del panel lo cogen sin tocar `panel/*`.

**Validación (medición real contra la app viva, reiniciada para cargar el
código nuevo; `.tmp/verify_icon2.py`, `.tmp/capture_light.py`).**

- **Las 4 superficies dan el MISMO md5 de píxeles** en 7 tamaños × 2 temas:
  bandeja (`dicta_ui.make_tray_image`), render oficial (`official_image`),
  **lo servido por HTTP** (`GET /panel/icon.png?size=&theme=`) y el fotograma del
  `.ico`; y los **bytes PNG embebidos del `.ico` son idénticos** al PNG del
  render. Tema claro (bandeja/oficial/http/ico):

  | px | líneas | fondo | md5 |
  |---|---|---|---|
  | 16 | 5 | `#FFFFFF` alfa **255** | `eb370edb` |
  | 18 | 5 | `#FFFFFF` alfa 255 | `4e1035d1` |
  | 20 | 5 | `#FFFFFF` alfa 255 | `c6099101` |
  | 24 | 5 | `#FFFFFF` alfa 255 | `0f03b68e` |
  | 32 | 5 | `#FFFFFF` alfa 255 | `76c0fd7b` |
  | 48 | 5 | `#FFFFFF` alfa 255 | `c4a432e8` |
  | 64 | 5 | `#FFFFFF` alfa 255 | `d3428c7b` |

  (tema oscuro, 32 px: `b6abb32c`, grafito opaco alfa 255.)
- **HICON REAL de la ventana viva igual al render oficial del tema activo**:
  con la app en claro, HICON 32 px = `76c0fd7b` = `official_image(32,"light")` =
  HTTP = fotograma del `.ico`; con la app en oscuro, HICON 32 px = `b6abb32c` =
  render oscuro. (Extraído con `WM_GETICON`/`GLC_HICON` + `GetDIBits` — ojo:
  `GetDIBits` devuelve **BGRA**, leerlo como RGBA intercambia R y B y hace creer
  que el icono oscuro es otro.)
- **Lo viejo NO se usa**: el `.ico` cacheado antiguo (`.tmp/dicta-icon-light.ico`)
  sigue en disco con **3 líneas / alfa 165** (`afb3473d` a 32 px) y se dejó ahí a
  propósito: la app ya escribe/lee `dicta-icon-light-6.ico` (5 líneas, alfa 255).
- **Captura real**: la sesión de escritorio está **bloqueada**, así que
  `ImageGrab`/captura de pantalla devuelve negro y la **bandeja no se puede
  fotografiar**. Sí funciona `PrintWindow(PW_RENDERFULLCONTENT)` de la ventana
  del panel: en la captura se ve la barra con el icono de **5 líneas sobre
  azulejo blanco** junto a "Dicta", y el recorte del icono de la barra coincide
  con el PNG servido por HTTP a `size=18` (mismas 5 barras, mismos colores,
  mismo fondo blanco). (`.tmp/icon_probe/panel_bar_zoom.png`,
  `panel_light_bar_zoom.png`, `compare_bar_vs_served.png`.)
- **La bandeja** (imagen que pystray convierte a HICON) se verificó por su
  entrada: `dicta_ui.make_tray_image(n)` == render oficial en 16/18/20/24/32/48/64
  px en ambos temas, es decir la bandeja enseña ya el mismo dibujo (5 líneas,
  azulejo opaco).
- Hoja de comprobación regenerada: `assets/_icon_check.png` (`dicta_icon.py`
  como script). La app quedó **viva** (`GET /state` 200) con el tema **claro**
  (el valor de `dicta_config.json`; se había quedado en oscuro y se devolvió a
  claro por POST para no dejar el icono en grafito).

**No se tocó:** `panel/*`, `dicta_ui.py`, la ruta `GET /panel/icon.png` (mismo
contrato), el audio de la reunión, `doc.rename`/`doc.delete`, los atajos,
`mic.test`, `/state.levels` ni el `.ico` estático `dicta.ico` (solo lo usa
`build_exe.bat`/`dicta.spec` para el icono del fichero `.exe` en el Explorador;
la app en marcha escribe el suyo por tema en `.tmp`).

---

## 43. Cierre limpio: el modelo sale de la VRAM y no sobrevive ningún proceso

**Problema reportado:** *«cuando cerremos la app … creo que quedan procesos en
la VRAM … la idea es que cuando se cierre se cierre el proceso del whisper o el
modelo que este cargado en la VRAM también, para que no quede en segundo plano
o un proceso parásito consumiendo recursos innecesariamente cuando no se están
usando»*.

**Diagnóstico (medido).** El motor GPU es un `whisper-server.exe` (whisper.cpp,
**Vulkan** en este equipo; no hay NVIDIA, así que **no es CUDA**) persistente:
carga el modelo una vez y **lo mantiene en la VRAM**. `App.quit()` terminaba
con `os._exit(0)`: eso mata el intérprete de golpe y **salta TODOS los
`atexit`** (incluido el `_get_server().stop()` que registraba `main()`). Como
en Windows un hijo **no muere con su padre**, al cerrar quedaba vivo el
`whisper-server.exe` con **887,8 MB de VRAM** y el puerto 47801 ocupado.
Reproducido antes del arreglo: `POST / {"action":"quit"}` → fuera los dos
`pythonw.exe`, pero el `whisper-server.exe` (PID 10352) seguía con **917,7 MB**
y escuchando en 47801. Peor: al relanzar, ese huérfano ocupaba el puerto del
servidor GPU y el nuevo no llegaba a arrancar.

**Cambios (`dicta.py`):**
- `shutdown_service(reason)`: **cierre limpio idempotente**, en orden —
  (1) mata los `whisper-cli` en curso; (2) para la reunión (`request_stop` +
  join acotado) y la cola de audios (`TranscribeQueue.stop()`, nuevo);
  (3) para el micro y la prueba de micro; (4) **termina el `whisper-server`
  (`_get_server().stop()`) → suelta el modelo de la VRAM**; (5) barrido final
  de procesos whisper.
- `App.quit()` (bandeja *Salir*, botón del panel, `POST quit`) llama a
  `shutdown_service("salida")` **antes** de tocar la GUI. La ventana del panel
  se **destruye** (`panel.shutdown()`), ya no se oculta: la app se va.
- `_run_whisper_cli()`: el `whisper-cli` de CPU deja de ser `subprocess.run` y
  pasa a `Popen` **con el PID registrado**, para poder matarlo a mitad si se
  cierra mientras transcribe (antes quedaba huérfano).
- `_reap_orphan_whisper()`: mata cualquier `whisper-server`/`whisper-cli` **de
  esta instalación** (filtra por `RESOURCE_DIR/whisper_*`). Se llama en el
  cierre **y al arrancar** (`preload()`, antes de levantar el servidor: así el
  huérfano de un cuelgue anterior no bloquea el 47801).
- El `atexit` del servicio pasa a `shutdown_service("atexit")`; en `--no-gui`,
  `Ctrl+C` también cierra limpio.

**Ruta nueva `GET /download`** (la usará el panel): `?doc=NOMBRE_BASE&kind=md|wav|txt`
- `md`  → `textos/NOMBRE_BASE.md` (tal cual), `text/markdown`;
- `wav` → `audios/NOMBRE_BASE.wav`, `audio/wav`;
- `txt` → el mismo texto del `.md`, `text/plain`, extensión `.txt`.

Todas con `Content-Disposition: attachment; filename="…"` para que el navegador
lo **baje**. El nombre se valida (ni `/`, ni `\`, ni `..`) → **400** si es
inválido o si `kind` no es `md|wav|txt`; **404** si el fichero no existe.

**Validación (medida).** GPU **AMD Radeon RX 9070**, motor Vulkan, modelo
`turbo`. VRAM dedicada leída con los contadores de Windows
`\GPU Adapter Memory(*)\Dedicated Usage` y `\GPU Process Memory(*)`
(`nvidia-smi` **no existe** en este equipo → no es CUDA; si el motor fuera CPU
se mediría RAM, pero aquí carga en la gráfica). Baseline **sin app: 1124,9 MB**.
Tres vueltas completas de *arrancar → modelo en la GPU → `POST quit`*:

| vuelta | VRAM total antes | VRAM app viva + modelo | whisper-server | VRAM total tras cerrar |
|---|---|---|---|---|
| 1 | 1124,9 MB | 2071,0 MB | 887,8 MB | **1125,6 MB** |
| 2 | 1121,4 MB | 2063,0 MB | 887,8 MB | **1121,4 MB** |
| 3 | 1125,4 MB | 2065,0 MB | 887,8 MB | **1125,4 MB** |

Las tres vuelven al nivel inicial (±4 MB, ruido del escritorio). Tras cada
cierre: **cero** procesos `whisper*` **y cero `pythonw.exe`** —los **dos** que
monta el shim del `.venv`: lanzador + intérprete, medido con `tasklist`— y
**47810/47801 libres** (`netstat`). Log real de la corrida:
`Cierre limpio (salida): liberando GPU y parando servicios...` →
`Cierre limpio: GPU liberada y sin procesos whisper vivos.`

**Resistencia a un cierre sin limpieza.** Matando el proceso a lo bruto
(`Stop-Process -Force`, simula cuelgue) el `whisper-server` **sí** queda
huérfano (esperado: no corre código alguno); al relanzar, el barrido lo mata
antes de levantar el nuevo → `Cierre limpio: matados 1 proceso(s) whisper
sueltos.` y el servidor nuevo toma el 47801. Sin acumulación entre vueltas.

**`/download` verificado** contra la app viva (`Prueba_1`): `md` → 200
`text/markdown`, 1270 B, sha `fe6fd9b6c8df` = el `.md` de origen; `wav` → 200
`audio/wav`, 14 112 044 B, sha `2f729c2f2491` = el `.wav` de origen; `txt` →
200 `text/plain`, 1270 B, mismo sha que el `.md`,
`filename="Prueba_1.txt"`. `doc=NoExiste` → **404**; `doc=..%2Fdicta.py` →
**400**; `kind=xyz` → **400**.

**No se tocó:** `panel/*`, `dicta_ui.py`, la clase de reunión (ganancia,
mezclador, `_normalize_wav`, párrafos), `/state.levels` (12 bandas sys/mic),
`MicTest`, `doc.rename`/`doc.delete`, `GET /panel/icon.png`, los atajos
(alt+q, ctrl+e, ctrl+alt+p, ctrl+alt+r) ni el arranque en instancia única.

La app quedó **viva** (`GET /state` 200).

---

## 44. Audios subidos persistentes: lista `uploads` en /state y `upload.remove`

**Problema reportado:** *«que queden guardados los archivos [que] voy subiendo
de audio, video o el formato que sea»*, poder **quitar** uno de la cola y que el
panel pinte cada subida como **ficha independiente**.

**Que cambio (`dicta.py`):**

- Carpeta propia **`uploads/`** junto al `.py`/`.exe` (NO en `.tmp`): cada
  fichero subido se guarda ahi y su ficha en `uploads/uploads.json` (escritura
  atomica temporal + `os.replace`). Nueva clase `UploadStore`.
- `/state` expone **`uploads`**: lista con `name` (nombre visible), `size`
  (bytes), `doc` (nombre base del `.md` si ya se transcribio, o cadena vacia),
  `duration` (segundos, o 0) y `state` (`pendiente` | `transcribiendo` |
  `listo` | `error`). El estado lo sincroniza la propia cola al cambiar cada
  item (callback `on_change`), sin sondeo.
- `POST {"action":"upload.remove","value":"NOMBRE"}` quita la ficha **y borra su
  fichero del disco**. El nombre es solo una etiqueta: el borrado va contra la
  ruta interna guardada (generada por la app), asi que **no admite rutas ni
  `..`** (responde sin tocar nada). Los nombres repetidos se renumeran
  (`notas.wav` -> `notas (2).wav`) para que quitar por nombre sea inequivoco.
- `POST /upload` ya no escribe en `.tmp` ni borra el temporal: guarda en
  `uploads/` y encola. Al arrancar, las fichas que quedaron
  `pendiente`/`transcribiendo` se **reencolan** para que la cola siga donde
  estaba tras el reinicio.

**Verificacion (medida, contra la app viva en 47810):**

- Subida de `reunion de prueba.wav` (48 044 B) -> `uploads`:
  `[{"name":"reunion de prueba.wav","size":48044,"doc":"reunion de prueba",`
  `"duration":2,"state":"listo","id":"9664da1bf6"}]`; en disco
  `uploads/9664da1bf6.wav` (48 044 B) + `uploads/uploads.json`.
- **Reinicio** (POST quit + relanzar): `uploads` **identico** (mismo `id`,
  `size`, `doc`, `duration`, `state`) -> los ficheros **persisten**.
- `upload.remove` de `reunion de prueba.wav` -> HTTP **200**
  `{"ok":true,"uploads":[]}`; el fichero desaparece de `uploads/` (queda solo
  `uploads.json`).
- Guardas: `../dicta_config.json` y `..\dicta_config.json` -> **404**,
  `uploads` intacto. Duplicado `notas.wav`+`notas.wav` -> la 2a entra como
  `notas (2).wav`; quitar ambas -> `uploads: []`. Estado final de la app:
  `uploads: []`, `GET /state` **200** (viva).

**Nota:** quitar una ficha no cancela una transcripcion que ya este corriendo
(el `.md` puede llegar a escribirse); solo desaparece de la lista y se borra el
fichero subido.

**No se toco:** `panel/*`, `dicta_ui.py`, `dicta_icon.py`, la clase de reunion
(ganancia, mezclador, `_normalize_wav`, parrafos), `/state.levels` (12 bandas
sys/mic), `MicTest`, `doc.rename`/`doc.delete`, `GET /panel/icon.png`,
`/download`, los atajos (alt+q, ctrl+e, ctrl+alt+p, ctrl+alt+r) ni el arranque
en instancia unica.



---

## 47. Mensaje de motor claro en /state y version del icono para el cache

**Problema reportado:** el autor ve **ROCm** en la lista de motores, no puede
activarlo y no lo entiende: tiene una GPU AMD y cree que ROCm es lo suyo.
Ademas, al cambiar el dibujo del icono el panel seguia enseñando el favicon
viejo cacheado por el navegador.

**Que cambio (`dicta.py`): dos cosas.**

**(1) Mensaje de motor claro (`/state.engine_note` y motivo por motor).**
- Nueva constante `ENGINE_NOTE_BASE`, en lenguaje de usuario: **su GPU AMD ya
  trabaja con Vulkan**, que es la opcion optima en este equipo; **ROCm no se
  puede activar** porque *no funciona en Windows nativo con esta tarjeta*
  (ROCm va por Linux/WSL y solo con GPUs soportadas) y **CUDA es de NVIDIA**.
  Cierra con «No se te niega nada: Vulkan es la eleccion correcta en este
  equipo».
- `panel_state()` publica `engine_note`: el aviso puntual del usuario si lo
  hay y, si no, `ENGINE_NOTE_BASE`. Asi `/state` **siempre** lleva la
  explicacion, no una cadena vacia.
- Nueva funcion `engine_reason(key, available)` y `engine_options()` añade el
  campo **`reason`** a cada opcion (auto, vulkan, cuda, rocm, cpu): un motivo
  por motor en lenguaje de usuario, nada de un «no compatible» seco.
- `on_engine` reescribe el aviso cuando el autor pide un motor no disponible.

**(2) Version del icono para el cache (`/state.icon_version`).**
- Nueva funcion `icon_version()`: **hash corto (sha1, 12 hex)** del PNG del
  icono renderizado a un **tamaño FIJO** (`_ICON_VERSION_SIZE = 64`,
  `_panel_icon_png(64, None)`), sobre el PNG ya cacheado en memoria. Cambia en
  cuanto cambia el dibujo (o el tema) del icono.
- `panel_state()` publica `icon_version`; el panel puede pedir
  `GET /panel/icon.png?size=..&theme=..&v=<icon_version>` y el navegador deja
  de servir el favicon viejo. El endpoint `GET /panel/icon.png` **no cambia**:
  sigue dando 200 image/png con su contrato de siempre.

**Verificacion (medida, contra la app viva en 47810):**

- `/state.engine_note` = `Tu GPU AMD ya trabaja con Vulkan, que es la opcion
  optima en este equipo. ROCm aparece en la lista pero no se puede activar
  porque no funciona en Windows nativo con esta tarjeta (ROCm va por Linux/WSL
  y solo con GPUs soportadas), y CUDA es exclusivo de las GPU NVIDIA. No se te
  niega nada: Vulkan es la eleccion correcta en este equipo.`
- `engine_options[].reason`: vulkan -> «Usa tu GPU AMD (tambien
  Intel/NVIDIA)… la opcion optima… y la que ya aprovecha tu tarjeta»; cuda ->
  «…exclusivo de las GPU NVIDIA y este equipo no tiene una…»; rocm -> «ROCm no
  funciona en Windows nativo con esta tarjeta…»; cpu -> «…respaldo cuando la
  GPU no puede».
- `POST {action:"engine", value:"rocm"}` -> `engine=rocm`,
  `engine_resolved=cpu` y `engine_note` = «GPU (ROCm, AMD) no se puede usar en
  este equipo, asi que se seguira con CPU. ROCm no funciona en Windows nativo
  con esta tarjeta…»; restaurado a vulkan, el aviso vuelve a
  `ENGINE_NOTE_BASE`.
- `icon_version`: origen (tema **dark**) = `71662caa7d46`; tras
  `POST theme=light` = `092c66633ce4` (**cambia**); restaurado a dark =
  `71662caa7d46` (**vuelve**). Coincide exacto con el `sha1` del render directo
  `dicta_icon.render_icon(64, variant="mark", bg=False, theme=<activo>)`. Dos
  renders distintos a 64 (light vs dark) dan dos hashes distintos.
- `GET /panel/icon.png?size=32&theme=dark` -> **200** `image/png`, 1244 B;
  `theme=light` -> 200, 1063 B; sin query -> 200, 484 B. Contrato intacto.

**No se toco:** `panel/*`, `dicta_ui.py`, `dicta_icon.py`, la clase de reunion
(ganancia, mezclador, `_normalize_wav`, parrafos), `/state.levels` (12 bandas
sys/mic), `MicTest`, `doc.rename`/`doc.delete`, `GET /panel/icon.png`,
`/download`, las subidas persistentes, el cierre limpio con `shutdown_service`,
los atajos (alt+q, ctrl+e, ctrl+alt+p, alt+r, alt+t) ni el arranque en
instancia unica.

La app quedo **viva** (`GET /state` 200).


## 48. La ventana del panel se puede MOVER aunque este MAXIMIZADA (como Windows)

**Que pasaba.** Con la ventana del panel maximizada (el autor la usa a pantalla
completa), pulsar la barra superior y arrastrar no movia nada: en
`WebViewPanelHost._drag_loop` habia un corte explicito —`if IsZoomed(hwnd):
return  # una ventana maximizada no se arrastra`—. Otras aplicaciones de Windows
si dejan: al arrastrar la barra de una ventana maximizada, la ventana vuelve a
modo ventana y sigue al cursor, con el puntero agarrado en el mismo punto de la
barra.

**Como se hace el arrastre (sin cambiar nada del panel).** La barra la inyecta
`panel/desktop.js` y cada elemento de arrastre llama, en el `mousedown`,
`pywebview.api.drag_window()` (sin argumentos). Ese metodo entra en
`PanelJS.drag_window()` -> `WebViewPanelHost.start_drag()` -> `_drag_loop`, que
ya lleva el bucle clasico de Win32 (`GetCursorPos` + `SetWindowPos` siguiendo al
cursor mientras `VK_LBUTTON` siga pulsado). El backend lee el cursor el mismo con
`GetCursorPos`, asi que **la interfaz no cambia**: `drag_window()` sigue sin
argumentos. **No hay que tocar `panel/desktop.js`.**

**Que se cambio (solo `dicta.py`).** En `_drag_loop`, cuando la ventana esta
maximizada ya no se sale: se llama a `_restore_and_anchor(hw, r_max, p0)`, que
replica el gesto de Windows:

1. Mide el cursor como **fraccion** (`fx`, `fy`) de la ventana maximizada
   (`r_max` via `GetWindowRect`).
2. Lee la geometria de ventana normal con `GetWindowPlacement`
   (`rcNormalPosition`, struct nuevo `_WINDOWPLACEMENT`).
3. `ShowWindow(hw, SW_RESTORE)` la devuelve a tamaño de **ventana**.
4. `SetWindowPos` la coloca en `left = p0.x - fx*nw`, `top = p0.y - fy*nh`, de
   modo que el cursor quede sobre el **mismo punto relativo de la barra** (nada
   de saltos); `(NOSIZE|NOZORDER|NOACTIVATE)`.
5. Marca `self.maximized = False` y avisa al boton de la barra por
   `evaluate_js` (en un hilo aparte; quita la clase `is-max`) para que el icono
   diga «maximizar» otra vez. Best-effort: si el backend no puede, no pasa nada.

A partir de ahi, el bucle sigue igual que en modo normal: `base` (el rect ya
restaurado) es el origen del arrastre. Arrastrar estando ya **normal** no se
toca: se comporta como siempre.

**Interfaz con el panel (definida).** Sin cambios: el panel sigue llamando
`pywebview.api.drag_window()` (sin argumentos) en el `mousedown` de la zona de
arrastre; el backend se encarga de restaurar/anclar/arrastrar. El panel tambien
puede forzarlo por control: `POST {action:"window", value:"drag"}` (no usado
para esto).

**Que no se toco:** el cierre limpio con `shutdown_service`, la instancia unica,
los 5 atajos, `/state` (con levels, uploads, engine_options, engine_note,
icon_version, voice_threshold, silence_wait, rms/thr/voice), `/panel/icon.png`,
`/download`, `doc.rename`/`doc.delete`, `upload.remove`, `MicTest`, la clase de
reunion (ganancia, mezclador, `_normalize_wav`, parrafos). Ni `panel/*`,
`dicta_ui.py` ni `dicta_icon.py`.

**Verificacion (MEDIDA, contra la app viva en 47810; `GetWindowRect`:**
`[left, top, right, bottom]`). Pantalla primaria 1920x1080, DPI 100%:

- **Maximizada:** rect `[0, 0, 1920, 1080]`, `IsZoomed = true`.
  Punto de pulsacion (45% del ancho): `(864, 16)`.
- **Al pulsar y arrastrar estando maximizada (delta pedido +180,+90):**
  - Rect **al restaurar/anclar** (cursor aun quieto en `(864,16)`):
    `[403, 4, 1427, 785]`, `IsZoomed = false` — **dejo de estar maximizada**.
    Comprobacion del anclaje: fraccion del cursor en la barra **antes** = 0.4500,
    **despues** = 0.4502 (delta 0.0002) -> el puntero quedo en el **mismo punto
    relativo**, **sin salto**.
  - Rect **tras arrastrar**: `[583, 94, 1607, 875]`, `IsZoomed = false`.
    Desplazamiento desde el ancla = **+180,+90** (exacto al pedido).
- **Arrastrar OTRA VEZ ya en estado normal (delta pedido +120,+60):**
  de `[583, 94, 1607, 875]` a `[703, 154, 1727, 935]`, `IsZoomed = false`.
  Desplazamiento = **+120,+60** (exacto). Sigue funcionando igual.

La app quedo **viva** (`GET /state` 200).


## 49. El .exe CONGELADO abre la ventana con WebView2 de verdad (ya no cae a Chrome) y se publica como paquete portable autonomo

**Que pasaba.** Compilado con PyInstaller, Dicta arrancaba pero el panel caia
al respaldo de Chrome: dentro del .exe fallaba `import webview`. El error real,
cazado con un **binario de sonda congelado** (mismo spec, mismo bundle):

    RuntimeError: Failed to resolve Python.Runtime.Loader.Initialize from
    ...\_internal\pythonnet\runtime\Python.Runtime.dll
    (clr_loader\netfx.py, _get_callable: pyclr_get_function devolvia NULL)

**Causa raiz (medida, no supuesta).** `clr_loader` carga `Python.Runtime.dll`
con `Assembly.LoadFrom`, y .NET Framework se NIEGA a cargar asi un fichero que
caiga en la zona Internet/Intranet: lanza `NotSupportedException` — «An attempt
was made to load an assembly from a network location…» (HRESULT 0x80131515) —
salvo que este habilitado `loadFromRemoteSources`. Medido con
`System.Security.Policy.Zone.CreateFromUrl`:

    MyComputer | .venv\Lib\site-packages\pythonnet\runtime\Python.Runtime.dll
    Internet   | cualquier COPIA: _internal\pythonnet\runtime\..., .tmp\*...

Los bytes eran IDENTICOS (mismo sha256 `2ebd4492e28442ef1f1af587afe5b3a0`) y el
mismo Python del venv resolvia la DLL del bundle cuando ya estaba cargada, o
sea que **no** era la ruta, ni la version de pythonnet/clr-loader
(3.2.1 / 0.3.1), ni un binario corrupto, ni el shim de clr_loader: era la ZONA
del fichero. Y no es un artefacto de este equipo: un ZIP descargado de internet
deja la marca MOTW en lo que se descomprime, asi que le pasaria igual al usuario
que se baje la release (por eso el arreglo va en el paquete, no en el equipo).

**Arreglo (4 piezas).**
- **`dicta.exe.config`**, fichero NUEVO del repo, con
  `<runtime><loadFromRemoteSources enabled="true"/></runtime>`. .NET lo lee de
  `<exe>.exe.config`, **al lado del ejecutable**, antes de inicializar el CLR.
  `dicta.spec` lo coloca en la RAIZ de `dist/dicta` — no en `_internal` —, cosa
  que COLLECT solo permite con el tipo `'EXECUTABLE'` (todo lo DATA/BINARY va a
  `_internal`). `build_exe.bat` lo vuelve a copiar por si alguien compila a mano.
- **`ensure_dotnet_config()`** en `dicta.py`: si el `.config` falta, se escribe
  al arrancar ANTES de tocar pywebview/pythonnet (best-effort: si la carpeta no
  es escribible, se registra en el log y el panel usaria el navegador).
- **`uac_admin=False`** en el spec. Antes el .exe llevaba manifest
  `requireAdministrator` y **ni arrancaba** desde un proceso sin elevar
  (CreateProcess error 740); el autor no puede aceptar un UAC. Manifest actual:
  `asInvoker` (comprobado en los strings del .exe).
- **Paquete portable**: `build_exe.bat` deja junto al .exe el `.config` y
  `models\ggml-small-q5_1.bin` (190 085 487 B, el modelo por defecto), de modo
  que **transcribe de fabrica**; los demas modelos se siguen bajando solos la
  primera vez (via `ensure_model`, sin cambios).

**Verificacion (MEDIDA).** .exe congelado copiado a una carpeta LIMPIA
(`.tmp/reltest/dicta`) y lanzado con el entorno saneado (sin `PYTHONPATH`,
`VIRTUAL_ENV`, `PYTHONHOME`…) y, en el arranque final, con
`PATH='C:\Windows\system32;C:\Windows'`:

- **Ventana con WebView2 (no Chrome).** Log: `Panel: backend WebView2
  (pywebview) — ventana sin marco, barra integrada en la página`,
  `Panel abierto (WebView2, sin barra nativa): http://127.0.0.1:47810/panel`,
  `Panel: esquinas redondeadas (DWM, Windows 11)`, `Panel: barra integrada
  inyectada (panel/desktop.js)`. Arbol de procesos: `dicta.exe` (pid 4188) →
  `msedgewebview2.exe` (pid 13568, `C:\Program Files (x86)\Microsoft\
  EdgeWebView\Application\155.0.4283.45` = **runtime del sistema**, no se
  instala nada) y **0 hijos `chrome.exe`**. Por CDP
  (`DICTA_WEBVIEW_DEBUG_PORT=9333`) el navegador se identifica como
  `Edg/155.0.4283.45` y sirve la página.
- **Respaldo en runtime (sin `.config`)**: arrancando una copia LIMPIA a la que
  le borre `dicta.exe.config`, el log registra `Escrito dicta.exe.config
  (loadFromRemoteSources…)` a las 14:06:54 y la ventana WebView2 abre igual
  (`Panel: backend WebView2`, `/state` 200): el .exe se auto-repara si le falta
  el fichero (p. ej. si alguien copia solo el ejecutable).
- **`GET /state` → HTTP 200**: `{"version":"1.0","model":"small",
  "engine":"auto","engine_resolved":"vulkan","language":"es",
  "status":"Listo para escuchar"}`. Log: `Motor seleccionado: GPU (Vulkan)
  (auto)` y `Motor GPU (Vulkan) listo.` (calentamiento ya hecho).
- **Transcripcion REAL de punta a punta.** `POST /upload` (multipart) con
  `test.flac` (183 318 B, 10 s) → `200 {"ok":true,"saved":1,"names":
  ["test.flac"], …}`; la cola paso a `listo 100.0` y aparecio el documento
  **`textos/test.md`** (391 B) con la transcripcion («Me esperaba que hubiera
  sido stew para el dinner, turnips…») y sus temas, mas el audio en
  `audios\a1a368a76c.flac`. **Ninguna descarga**: el modelo era el `small` que
  viaja en el paquete y `models/` no cambio de tamaño ni aparecieron lineas
  `Descargando …` en el log.
- **No necesita Python instalado ni el venv.** Corre con `PATH` de system32 y
  sin variables `PYTHON*`; el interprete viaja dentro
  (`_internal\python312.dll`, 6 983 144 B) y no hay ningun `python.exe` en su
  arbol de procesos. Ficheros `.dll`/`.exe`/`.pyd` en el paquete: **95**.
- **Cierre limpio liberando la VRAM.** `POST {"action":"quit"}` → `200
  {"ok":true}`; despues **0 procesos** del paquete (el `dicta.exe`, los 6
  `msedgewebview2.exe` y el `whisper-server.exe` Vulkan que tenia el modelo en
  la GPU) y `GET /state` → `HTTP 000`. Log: `Cierre limpio (salida): liberando
  GPU y parando servicios…` y `Cierre limpio: GPU liberada y sin procesos
  whisper vivos.`

**Tamano del paquete final** (lo que hay que subir a la release):

    dist/dicta/                            392 MB   (1077 ficheros)
      dicta.exe                          7 741 646 B
      dicta.exe.config                       1 192 B
      _internal/                             204 MB  (python312.dll, panel/,
                                              pythonnet+clr_loader, whisper_bin/
                                              Release/, whisper_vulkan con
                                              ggml-vulkan.dll de 57,9 MB, DLLs
                                              nativas de numpy/soundfile/sounddevice)
      models/                                182 MB  (ggml-small-q5_1.bin)

    dist/dicta-portable-1.0-windows-x64.zip  249,3 MB  (261 426 552 B)

Un solo fichero, muy por debajo del limite de 2 GB por fichero de una release
de GitHub. El ZIP se creo con la carpeta limpia (antes del ultimo arranque), asi
que no lleva datos de ejecucion; al quedar la app viva en `dist/dicta` esa
carpeta tiene ya `dicta_config.json`, `dicta.log`, `dicta_crash.log`, `.tmp/` y
`uploads/` (datos de ejecucion, gitignored).

**No se toco:** `panel/*` (la barra sigue llamando `pywebview.api.drag_window()`
sin argumentos, etc.), `dicta_ui.py`, `dicta_icon.py`, la clase de reunion, los
5 atajos, `/state` (levels, uploads, engine_options, engine_note, icon_version,
voice_threshold, silence_wait, rms/thr/voice), `/panel/icon.png`, `/download`,
`doc.rename`/`doc.delete`, `upload.remove`, `MicTest` y las subidas
persistentes. Del spec solo cambiaron `uac_admin`, el `.config` de la raiz y los
comentarios.

La app quedo **viva** (`GET /state` 200), esta vez corriendo el **.exe
congelado** de `dist/dicta` (sin elevar).

## 50. El pegado automático ya funciona DENTRO de las terminales: mira la ventana destino y elige Ctrl+V / Ctrl+Shift+V / Shift+Insert

**Que pasaba.** El pegado automático mandaba SIEMPRE `Ctrl+V`. En una terminal
el emulador se queda esa combinación (la necesita el shell), así que el texto no
llegaba y el autor tenía que pegar a mano con `Ctrl+Shift+V`. La combinación
correcta depende del **emulador**, no del programa que corre dentro.

**Arreglo.** Antes de enviar nada, `fallback_paste` clasifica la ventana destino
con `GetForegroundWindow` + `GetClassNameW` + `GetWindowThreadProcessId` +
`QueryFullProcessImageNameW` (clase **y** .exe del proceso, nuevos helpers
`_win_class`, `_win_exe`, `_clasificar_destino`, `_paste_mode`, `_send_combo`) y
elige la combinación:

- `ConsoleWindowClass` (conhost clásico, cmd/powershell en ventana propia) →
  `Ctrl+V` (es el único emulador donde Ctrl+V pega de fábrica).
- Emuladores de terminal (clase `CASCADIA_HOSTING_WINDOW_CLASS` = Windows
  Terminal, o .exe `code.exe`/`cursor.exe`/`idea64.exe`/`pycharm64.exe`/`mintty.exe`/
  `wezterm-gui.exe`/`alacritty.exe`/`windowsterminal.exe`/…, porque VS Code y sus
  derivados comparten `Chrome_WidgetWin_1` con los navegadores) → `Ctrl+Shift+V`.
- Cualquier otra aplicación → `Ctrl+V`, **como siempre**.
- Si no se puede leer ni clase ni proceso, o si el envío del combo falla
  (SendInput bloqueado), se recurre a `Shift+Insert`, que es el pegado que más
  terminales cubre.

Además:

- **Opción configurable** `paste_mode` en `dicta_config.json`
  (`auto` por defecto = detectar; `ctrl+v`, `ctrl+shift+v`, `shift+insert` la
  fuerzan) para una terminal que se resista. Se publica en `/state` como
  `paste_mode` y se cambia con
  `POST /rpc {"action":"paste_mode","value":"shift+insert"}` (valores inválidos
  → `{"ok":false,"error":"modo invalido"}`). Se lee en cada pegado, sin reiniciar.
- **Log de diagnóstico**: cada pegado registra la clase, el .exe y la
  combinación usada, p. ej.
  `Pegado (ctrl+shift+v) enviado a [terminal: Windows Terminal [CASCADIA_HOSTING_WINDOW_CLASS / windowsterminal.exe]].`
- **Bug latente arreglado** en `_forzar_primer_plano`: usaba un `k32` que no
  existe (NameError silenciado por el `except`), así que el camino
  `AttachThreadInput` **nunca** corría y el foco se "restauraba" solo con el Alt
  simulado. Ahora usa `_kernel32`.
- `_key` acepta `extended=True` (bit `KEYEVENTF_EXTENDEDKEY`) para enviar
  `Insert`, que es tecla extendida.

**Verificación (MEDIDA en este equipo).**

- Clases y procesos reales (`EnumWindows` + `GetClassNameW` +
  `QueryFullProcessImageNameW`) y la combinación que elige el detector:

  | ventana | clase | .exe | tipo | combo |
  |---|---|---|---|---|
  | Windows Terminal | `CASCADIA_HOSTING_WINDOW_CLASS` | `windowsterminal.exe` | terminal | **Ctrl+Shift+V** |
  | consola clásica (cmd) | `ConsoleWindowClass` | `cmd.exe` | console | **Ctrl+V** |
  | Brave / Hermes / explorador / Tk / panel | `Chrome_WidgetWin_1`, `TkTopLevel`, `CabinetWClass`, … | `brave.exe`, `hermes.exe`, … | normal | **Ctrl+V** |

- **Punta a punta en una terminal de verdad.** Se lanzó una terminal con un
  programa que captura lo que recibe (`cmd /k` con `set /p` → cada línea a un
  fichero) y se provocó el pegado automático:
  - conhost (`ConsoleWindowClass`/`cmd.exe`), combo elegido `ctrl+v`: el fichero
    recibió `dictado conhost uno`.
  - **Windows Terminal** (`CASCADIA_HOSTING_WINDOW_CLASS`/`windowsterminal.exe`),
    combo elegido `ctrl+shift+v`: el fichero recibió
    `dictado windows terminal dos`.
  - **La app real** con `POST /rpc {"action":"test"}` y la ventana de Windows
    Terminal al frente: el log dijo
    `Pegado (ctrl+shift+v) enviado a [terminal: Windows Terminal [CASCADIA_HOSTING_WINDOW_CLASS / windowsterminal.exe]].`
    y `Pegado inmediato en 15 ms.`; al pulsar Enter, el fichero de la terminal
    recibió `prueba dicta 123` (el texto de la prueba de Dicta).
- **Aplicación normal intacta.** `POST {"action":"test"}`… con un campo de texto
  normal (Entry de Tk) al frente: clasificado `normal: TkTopLevel / python.exe`,
  combo `ctrl+v`, y el campo recibió `dictado normal app tres`.
- **Opción forzada.** `POST {"action":"paste_mode","value":"shift+insert"}` →
  `{"ok":true,"paste_mode":"shift+insert"}`, reflejado en `/state` y en
  `dicta_config.json`; repetido el pegado contra Windows Terminal, el log dijo
  `Pegado (shift+insert) enviado a [forzado por config (terminal: Windows Terminal […])]`
  y el texto llegó. `value:"ctrl+Q"` → `{"ok":false,"error":"modo invalido"}`.
  Al terminar se dejó en `auto`.
- **Matiz honesto medido**: en esta versión de Windows Terminal `Ctrl+V`
  *también* pega (WT lo intercepta), y en conhost cocido `Ctrl+V` pega. Pero en un
  programa que lee la entrada en crudo dentro de conhost, `Ctrl+V` **no** pega:
  llega como el byte `0x16` (se comprobó con un lector `msvcrt.getwch`). Es justo
  el caso de las CLI tipo OpenCode/Claude, y por eso el detector usa
  `Ctrl+Shift+V` en los emuladores y `Shift+Insert` como respaldo.

**No se tocó:** el pegado en aplicaciones normales (sigue siendo Ctrl+V), el
cierre limpio con `shutdown_service` (VRAM liberada; comprobado tras `quit`),
la instancia única, los atajos, `/state` (`levels`, `uploads`,
`engine_options`, `icon_version`, `voice_threshold`, `silence_wait`,
`rms`/`thr`/`voice`…), `/panel/icon.png` (200), `/download`,
`doc.rename`/`doc.delete`, `upload.remove`, `MicTest` ni la clase de reunión.
Solo cambiaron `dicta.py` y este `CHANGES.md`. Nada depende de elevar.

La app quedó **viva** (`GET /state` 200), corriendo el `dicta.py` parcheado con
el intérprete del venv (`pythonw.exe`, sin elevar), con `paste_mode` = `auto`.




## 51. Reempaquetado portable 1.0.1: el pegado en terminales va DENTRO del `.exe` (verificado de punta a punta)

**Que se hizo.** Recompilar el ejecutable portable con el codigo de AHORA (incluye
el arreglo del pegado en terminales de la entrada 50) y publicar el paquete
autonomo `1.0.1`, conservando todo lo que ya funcionaba del `1.0.0` (WebView2 en
el congelado con `dicta.exe.config`, sin elevacion, modelo `small` embebido, sin
instalar nada aparte). **No se toco** el ZIP anterior
(`dist/dicta-portable-1.0-windows-x64.zip`, 261 426 552 B): sigue intacto.

**Compilacion.** Con el venv, por el modulo (el shim `pyinstaller.exe` esta roto):
`./.venv/Scripts/python.exe -m PyInstaller --noconfirm --clean dicta.spec`
(PyInstaller **6.22.3**), **16,8 s**. Resultado en `dist/dicta`:
**1077 ficheros, 408 705 735 B**. Raices: `dicta.exe` (7 745 547 B),
`dicta.exe.config`, `_internal/` y `models/ggml-small-q5_1.bin`
(**190 085 487 B**).

`_internal/` lleva `python312.dll`, `whisper.dll`, `ggml-vulkan.dll` (57 946 112 B),
`whisper_bin/Release/` (motor CPU), `whisper_vulkan/` (`whisper-server.exe`),
`panel/`, `pythonnet` + `clr_loader`, y las nativas de `numpy`/`soundfile`/
`sounddevice`. DLLs en la raiz de `_internal`: `python312.dll`, `whisper.dll`,
`ggml.dll`, `ggml-base.dll`, `ggml-cpu.dll`, `ggml-vulkan.dll`,
`libcrypto-3-x64.dll`, `libssl-3-x64.dll`, `libffi-8.dll`, `tcl86t.dll`,
`tk86t.dll`, `MSVCP140.dll`, `VCOMP140.DLL`, `VCRUNTIME140.dll`,
`VCRUNTIME140_1.dll`.

**`build_exe.bat`** ya no borra `dist\` entero: solo `dist\dicta`, para no
llevarse por delante los ZIP de release ya publicados que viven en `dist\`.

**Paquete.**

    dist/dicta-portable-1.0.1-windows-x64.zip
      261 415 062 B  (249,3 MB)
      sha256  528cde2d4c32f7cd31c635c434afa6f1da6156b47983ff9011eea599a82b3465
      1077 entradas  ·  testzip (integridad) OK

Dentro va el contenido de `dist/dicta` tal cual: `dicta.exe` + `dicta.exe.config`
+ `_internal/` + `models/`. El `dicta.exe.config` lleva
`<loadFromRemoteSources enabled="true"/>` (comprobado leyendolo del propio ZIP).

**Verificacion (MEDIDA).**

- **(a) El `.exe` congelado abre con WebView2 desde una carpeta LIMPIA y con el
  entorno SANEADO.** El ZIP se extrajo a `.tmp/testrun101` y se arranco
  `dicta.exe` con `PYTHONPATH`, `VIRTUAL_ENV` (y todo lo de Hermes) fuera del
  entorno. `GET /state` -> **200**; el log dice
  `Panel: backend WebView2 (pywebview)`; el puerto de depuracion
  `DICTA_WEBVIEW_DEBUG_PORT=47899` responde
  `"Browser": "Edg/155.0.4283.45"` -> **WebView2 de verdad** (no Chrome); el log
  de arranque: `(elevado: no)` -> arranca **sin UAC**.
- **(b) Transcripcion REAL de un audio, de punta a punta, sin descargar nada.**
  Se genero una locucion en espanol (SAPI, WAV de 442 028 B) y se subio por
  `/upload`. El `.exe` congelado la transcribio con el **modelo `small`
  embebido** (motor Vulkan) y genero `textos/prueba_dicta_101.md` (duracion
  0:10) con el texto correcto: «La reunion del equipo empieza a las 9 y 30 de la
  manana. Necesitamos revisar el presupuesto trimestral y confirmar la fecha de
  entrega del proyecto.». Nada se descargo (todo salio del paquete).
- **(c) Cierre limpio.** `POST {"action":"quit"}`: `/state` deja de responder, el
  puerto 47810 se libera y **no queda ningun proceso** (`dicta.exe` ni
  `whisper-server.exe`). La VRAM dedicada (contadores de Windows) baja de
  **2 551,6 MB a 1 923,2 MB** -> el modelo sale de la GPU (-628,4 MB).
- **(d) PEGADO AUTOMATICO EN TERMINALES desde el `.exe` CONGELADO** (lo nuevo,
  imprescindible). Se abrieron ventanas reales con un lector (`cmd /k` con
  `set /p` y bash `read` escribiendo a un fichero) y se provoco el pegado con
  `POST {"action":"test"}` (texto `prueba dicta 123`):

  | ventana destino | clase / .exe | combo elegido (log) | texto recibido |
  |---|---|---|---|
  | conhost (`cmd /k`) | `ConsoleWindowClass` / `cmd.exe` | **ctrl+v** | `prueba dicta 123` |
  | app normal (Tk) | `TkTopLevel` / `pythonw.exe` | **ctrl+v** | `prueba dicta 123` |
  | Windows Terminal | `CASCADIA_HOSTING_WINDOW_CLASS` / `windowsterminal.exe` | **ctrl+shift+v** | `prueba dicta 123` |

  Log literal del caso terminal:
  `Pegado (ctrl+shift+v) enviado a [terminal: Windows Terminal [CASCADIA_HOSTING_WINDOW_CLASS / windowsterminal.exe]].`
  Es decir: en conhost y en apps normales sigue siendo Ctrl+V, y en el emulador
  de terminal usa **Ctrl+Shift+V** — el arreglo de la entrada 50 viaja dentro del
  `.exe` congelado.
- **(e) Contenido e integridad del ZIP.** Contiene `dicta.exe`,
  `dicta.exe.config`, `_internal/` (con `_internal/panel/index.html`) y
  `models/ggml-small-q5_1.bin`; **NO** contiene datos del usuario
  (`audios/`, `textos/`, `uploads/`, `dicta.log`, `dicta_crash.log`,
  `dicta_config.json`, `.tmp/`, `uploads.json`, `webview-profile`) ni ficheros
  `.bak`/`.tmp`. `testzip()` no encuentra ninguna entrada corrupta.

Los datos de ejecucion del `.exe` vivo (`dicta_config.json`, `dicta.log`,
`uploads/`, `.tmp/`) quedan en `dist/dicta` (gitignored), nunca en el ZIP, que se
creo desde la carpeta recien compilada antes de arrancar nada.

**No se toco:** `panel/*`, `dicta_ui.py`, `dicta_icon.py`, `dicta.py` (el codigo
es el que se empaqueta tal cual), la clase de reunion, los 5 atajos, `/state`,
`/download`, `MicTest`, `upload.remove` ni los documentos heredados. Del spec no
cambio nada. Solo cambiaron `build_exe.bat` (limpieza segura de `dist\`) y este
`CHANGES.md`.

La app quedo **viva** (`GET /state` 200), esta vez corriendo el **`.exe`
congelado** de `dist/dicta` (WebView2 `Edg/155.0.4283.45`, sin elevar).

## 52. El pegado automático funciona DENTRO de los agentes de terminal: mecanismo por destino (buffer de consola / texto tecleado / combinación / posteado)

**Qué fallaba, medido y no supuesto.** El autor lo reportó tras la entrada 50:
«en OpenCode, Claude y Pi no auto-pega; me toca dar Ctrl+Shift+V». Las tres
hipótesis y lo que dio cada una:

1. **Mecanismo de envío de teclas.** El código NO usa mensajes posteados:
   `_send_key_event` llama a **`SendInput` (entrada real)** desde la entrada 50.
   La hipótesis «la tecla va posteada y Electron la ignora» no aplica a este
   código; se comprobó que `PostThreadMessageW`/`WM_KEYDOWN` no aparece en
   `dicta.py`. (Aun así, el posteado se añade como último recurso, ver abajo.)
2. **Portapapeles.** Dicta pone el texto en el portapapeles y **no lo restaura**
   (no existe ninguna ruta de restauración en `dicta.py`). La hipótesis «se
   restaura demasiado pronto» queda descartada por ausencia: no hay restauración.
3. **Detección del destino: AQUÍ ESTABA EL FALLO.** En el `dicta.log` de la
   propia sesión del autor, las 15:59:19: dictó «Estoy probando el auto pegado en
   PI y no funciona» con `destino: Hermes`, y la entrega fue
   `Pegado (ctrl+v) enviado a [normal: Chrome_WidgetWin_1 / hermes.exe].`
   Los agentes corren en una **terminal integrada dentro de una ventana
   Chromium/Electron** (Hermes y OpenCode escritorio son Electron con terminal
   tipo xterm.js): clase `Chrome_WidgetWin_1`, .exe `hermes.exe`, que el
   clasificador trataba como **«normal» -> Ctrl+V**. Dentro de un xterm.js el
   pegado está atado a **Ctrl+Shift+V** (un `<textarea>` sí pega con Ctrl+V), así
   que Ctrl+V no hacía nada: el texto no llegaba y Dicta decía «Texto insertado».

**Medidas del mecanismo viejo y del nuevo** (con un lector en modo crudo real,
`msvcrt.getwch` byte a byte a un fichero, que es el caso exacto de una TUI):

| conhost + lector crudo (`ConsoleWindowClass` / `python.exe`) | lo que llega |
|---|---|
| **con la ventana EN PRIMER PLANO**: `ctrl+v` | `DICTASETCTRLVQ` (pega) |
| **con la ventana EN PRIMER PLANO**: `ctrl+shift+v` | `'\x16'` -> NO pega (conhost solo ata Ctrl+V) |
| **con la ventana EN PRIMER PLANO**: `shift+insert` | `DICTASETSHIFTINSERTQ` (pega) |
| **con la ventana EN PRIMER PLANO**: una letra suelta | `y` (el teclado llega) |
| **con la consola SIN el primer plano**: `ctrl+v` | `''` (no llega nada) |
| **con la consola SIN el primer plano**: `ctrl+shift+v` | `''` (no llega nada) |
| **con la consola SIN el primer plano**: buffer de consola (**nuevo**) | `NUEVOTEXTO3` completo |

Es decir: el mecanismo viejo **depende del primer plano** (si el foco está en
otra ventana, el `SendInput` se va a esa otra y no llega nada), y en una consola
la combinación de pegado puede no existir. El mecanismo nuevo (escribir en el
**buffer de entrada de la consola**) llega **con o sin primer plano**.

**Windows Terminal: lo que NO se pudo verificar.** En este equipo Windows
Terminal (`CASCADIA_HOSTING_WINDOW_CLASS` / `windowsterminal.exe`), con la
ventana comprobada como `GetForegroundWindow`, **ni `ctrl+v`, ni `ctrl+shift+v`,
ni `shift+insert` ni una letra suelta llegaron** al lector crudo de su pty (en un
caso aislado sí llegó una `a`, o sea que el envío a WT es cuando menos
inestable aquí). Causa del entorno medida: el primer plano se lo robaba
continuamente una pestaña del navegador (una llamada continua a `window.focus()`:
`GetForegroundWindow` volvía a la ventana de Brave en menos de un segundo) y este
equipo tiene `SPI_GETFOREGROUNDLOCKTIMEOUT = 2147483647` (**INFINITO**: ninguna
otra cosa que el primer plano puede poner el foco; solo lo da un clic real o la
creación de la ventana). Y el **buffer de consola tampoco vale para WT**: su
cliente corre bajo un ConPTY y `AttachConsole` responde **ACCESS_DENIED** (medido,
pid del cliente del pty). Por eso el pegado de WT se queda como estaba: depende
de que WT reciba de verdad el `Ctrl+Shift+V` de la entrada 50.

**El arreglo (mecanismo elegido POR DESTINO, en `dicta.py`).** El clasificador
`_clasificar_destino` deja de devolver una combinación y devuelve el **mecanismo**:

| tipo | cuándo | mecanismo |
|---|---|---|
| `console` | clase `ConsoleWindowClass` (conhost real) | **`WriteConsoleInputW`**: el texto se escribe en el BUFFER DE ENTRADA de la consola (lo que lee una TUI); si la consola no se deja adjuntar (ConPTY) cae a Ctrl+V |
| `chromium` | clase `Chrome_WidgetWin_1` y .exe de la lista nueva `_CHROMIUM_HOST_EXES` (`hermes.exe`, `opencode.exe`, `cursor.exe`, `windsurf.exe`, `claude.exe`, `codex.exe`, `kiro.exe`, `zed.exe`) | **texto TECLEADO con entrada real** (`SendInput` `KEYEVENTF_UNICODE`): dentro de Chromium el pegado depende del control con el foco (xterm.js pega con Ctrl+Shift+V, un `<textarea>` con Ctrl+V) y desde fuera no se adivina; tecleado entra siempre |
| `terminal` | emulador (`CASCADIA_HOSTING_WINDOW_CLASS`, `windowsterminal.exe`, `code.exe`, `mintty.exe`…) | **Ctrl+Shift+V** (como la entrada 50) |
| `normal` | lo demás (navegadores, apps normales) | **Ctrl+V** (sin cambios) |
| último recurso | si el carril falla | **posteado**: `WM_PASTE` + `WM_KEYDOWN/UP` de Ctrl+V |

Se conserva **`paste_mode`** (`auto`|`ctrl+v`|`ctrl+shift+v`|`shift+insert`) y
`/state`: si no es `auto`, se FUERZA la combinación y se salta el mecanismo
elegido (válvula de escape intacta). El respaldo `Shift+Insert` sigue ahí.

**Verificado de punta a punta (con un AGENTE de terminal real).**
- **`pi` v0.85.1** (TUI que lee el teclado en crudo) abierto en una consola real:
  leyendo la pantalla de su consola (`ReadConsoleOutputCharacterW`) la línea de
  entrada del prompt pasó de `hola dicta prueba uno dos` a
  **`hola dicta prueba uno doshola dicta prueba uno dos`** al entregar el texto
  con `fallback_paste` — **el texto dictado aparece en el prompt del agente**.
  `pi` arrancó con avisos `EPERM` (no puede crear sus `~/.pi/agent/*.lock`) pero
  su prompt acepta entrada. OpenCode y Claude Code **no están en PATH** (sí la
  app de escritorio de OpenCode, que es Electron) — `pi` hizo de agente real.
- **Punta a punta por la API viva**: `POST {"action":"test"}` con la consola del
  lector delante -> el lector crudo recibió `prueba dicta 123` letra a letra y el
  log dejó `[16:31:14] Pegado (buffer de consola) enviado a [console:
  ConsoleWindowClass / python.exe].`
- **Clasificación viva**: `Chrome_WidgetWin_1 / hermes.exe` -> **`chromium` /
  `type`** (el caso del autor); `brave.exe` -> `normal` / `ctrl+v` (sin cambios).
- **Entrada real tecleada** (`SendInput` Unicode) con la ventana en primer plano
  -> `TECLEADOFG1` llega al lector crudo.
- **Carril de siempre** `ctrl+v` con la ventana en primer plano -> `PEGADOFG2`
  llega (sin regresión en aplicaciones normales).
- **`/state` 200** con todas sus claves (`levels`, `uploads`, `engine_options`,
  `icon_version`, `voice_threshold`, `silence_wait`, `rms`/`thr`/`voice`,
  `paste_mode`, `hotkeys`, `mics`, `models`, `docs`, `meeting`, `mic_test`),
  `/panel/icon.png` 200 `image/png`, `/download` con nombre invalido 404,
  `dicta_crash.log` en **0 bytes**.

**Cubre / no cubre.**
- **Cubre**: consolas reales (conhost) -> buffer de entrada; ventanas
  Chromium/Electron con terminal integrada (Hermes, OpenCode, Cursor…) -> texto
  tecleado; emuladores de terminal -> Ctrl+Shift+V; aplicaciones normales ->
  Ctrl+V; último recurso posteado.
- **No cubre**: (a) Windows Terminal/ConPTY en este equipo, por lo dicho arriba
  (no se pudo aislar si es del entorno o real); (b) si en una ventana Chromium el
  foco NO está en la terminal del agente sino en otro campo (p. ej. el cuadro de
  chat), ningún mecanismo de teclado lo arregla: el texto entra donde esté el
  foco; (c) los agentes CLI que no estén instalados aquí (OpenCode/Claude Code no
  están en PATH).

**No se tocó:** `panel/*` (ni el HTML/CSS/JS), `dicta_ui.py`, `dicta_icon.py`, el
cierre limpio (`shutdown_service`), la instancia única, los 5 atajos, `/download`,
`doc.rename`/`delete`, `upload.remove`, `MicTest` ni la clase de reunión. Solo
cambian `dicta.py` y este `CHANGES.md`.

La app queda **viva** (`GET /state` 200, WebView2, motor Vulkan). **Aviso:** al no
estar el autor delante NO se pudo relanzar elevada, así que esta instancia **no
pega en ventanas elevadas** hasta que se reinicie con `run.bat` o el `.exe`.

## 53. El pegado automático funciona en la terminal del autor (Terax): se TECLEA como entrada real, y `paste_mode` gana el modo forzado `type`

**Qué terminal es, identificada y no supuesta.** El autor la llamaba «terax» y NO
era Tera Term. En el menú Inicio del usuario está `Terax.lnk` ->
`C:\Users\JDMoreu\AppData\Local\Terax\terax.exe` (vivo, PID 16452). Ventana: clase
**`Tauri Window`**, .exe **`terax.exe`**. Es **Terax**, un terminal «ADE» de ~7 MB
hecho con **Tauri 2 + Rust + React** (terax.app, crynta/Terax-AI): backend PTY
nativo (`portable-pty` -> ConPTY en Windows) y frontend **xterm.js sobre canvas
WebGL dentro de WebView2**. Sus shells (pestañas) son **PowerShell** con
`profile.ps1` de integración, y en la del autor corre **`pi`** (pi-coding-agent),
que es el caso que él reporta. No hay Tera Term/WezTerm/PuTTY/Alacritty/Cmder/
ConEmu/Tabby/Hyper instalados: `where` solo encontró `wt.exe` (Windows Terminal de
la Store).

**Qué le pasaba, medido con receptor.** El clasificador miraba clase + .exe:
`Tauri Window` / `terax.exe` no estaban en ninguna lista, así que caía a
**«normal» -> Ctrl+V**. Medido con la ventana de Terax en primer plano (enviando
desde un proceso de integridad MEDIA, porque el tecleado sintético de un proceso
de integridad baja no atraviesa UIPI) y leyendo el resultado en la propia shell
del terminal —«echo AAA BBB CCC» se ejecutó y devolvió el error con la cadena
exacta, prueba de que la shell la recibió—:

| mecanismo enviado a Terax (xterm.js) | lo que llegó |
|---|---|
| `type` (SendInput `KEYEVENTF_UNICODE`) | **llega**: la cadena aparece **exacta** en la entrada (`ZZTEST123` y `ALFA BETA GAMMA`, **con espacios**) |
| `Ctrl+V` | **NO llega nada** (pantalla sin cambios, dos pruebas) |
| `Ctrl+Shift+V` | **NO llega nada** de forma fiable |
| `Shift+Insert` | **sí pega** (el token del portapapeles apareció en la entrada) |

Elegir MAL el carril era justo lo que hacía que no llegara: **Ctrl+V no pega en el
xterm.js de Terax**; el **tecleado como entrada real sí**, y es el mismo camino
que ya se usa para las ventanas Chromium/Electron.

**El arreglo.** (1) `_clasificar_destino` gana el caso **Tauri/WebView2**: clases
`tauri window` / `tao thread event target` (`_TAURI_CLASSES`) o .exe en
`_TAURI_HOST_EXES` (`terax.exe`) -> **`tauri` / mecanismo `type`** (texto
tecleado), igual que Chromium. (2) `paste_mode` acepta el valor forzado **`type`**
(teclear el texto, sin depender de la combinación ni del portapapeles) además de
`ctrl+v` / `ctrl+shift+v` / `shift+insert`; la lista se publica en **`/state`
(`paste_modes`)**. (3) `PASTE_MODES` y los comentarios lo documentan.

**Verificado.**
- Clasificación con el **código real** de `dicta.py` (extraído con `ast`, contra la
  ventana viva): `Tauri Window / terax.exe` -> **`tauri` / `type`**. Sin regresión:
  `Chrome_WidgetWin_1 / hermes.exe` -> `chromium` / `type` (antes y ahora) y
  `Chrome_WidgetWin_1 / brave.exe` -> `normal` / `ctrl+v` (sin cambios).
- `python -m py_compile dicta.py` OK.
- Punta a punta del mecanismo en ESA terminal: con las cadenas tecleadas
  (`ZZTEST123`, `ALFA BETA GAMMA`) el terminal de Terax las exhibió **exactas**,
  incluidas las que llevan espacios.
- `GET /state` 200 con todas sus claves.

**Cubre / no cubre.**
- **Cubre**: consolas reales (conhost) -> buffer de entrada; Chromium/Electron
  (Hermes, OpenCode...) -> tecleado; **Tauri/WebView2 (Terax) -> tecleado** (nuevo);
  emuladores de terminal genéricos -> Ctrl+Shift+V; normales -> Ctrl+V.
- **No cubre**: (a) Terax con la shell en `cmd.exe` (aquí arranca PowerShell) no
  medido; (b) si el foco está en otro campo del WebView y no en la terminal, el
  texto entra donde esté el foco (igual que en Chromium); (c) `Ctrl+Shift+V`
  quedó como no fiable en Terax, por eso el carril elegido es el tecleado.

**No se tocó:** `panel/*`, `dicta_ui.py`, `dicta_icon.py`, el cierre limpio
(`shutdown_service`), la instancia única, los atajos, `/download`,
`doc.rename`/`delete`, `upload.remove`, `MicTest` ni la clase de reunión. Solo
cambian `dicta.py` y este `CHANGES.md`.

**Aviso sobre la instancia en curso.** La app sigue **viva** (`GET /state` 200,
WebView2, Vulkan), pero el proceso en ejecución (PID 13056, `pythonw.exe`,
integridad ALTA = elevado) se arrancó ANTES de este cambio y todavía no incluye el
carril `tauri`/`type` ni `paste_modes`. Al relanzar con `run.bat` (o el `.exe`),
que se auto-eleva, quedará activo. No se relanzó aquí a propósito: el autor no está
delante para aceptar UAC y un relanzamiento desde este entorno en segundo plano
degradaría la app a integridad BAJA y dejaría de pegar en TODAS las ventanas.
Mientras tanto, sin relanzar, `POST {"action":"paste_mode","value":"shift+insert"}`
ya pega en Terax (medido).

## 54. Actualización desde la propia app: avisa de versión nueva y la descarga, con la comprobación APAGADA de fábrica (nada sale del equipo)

**Qué pide el autor.** (1) Poder enterarse y actualizar **desde la propia app**
sin bajar de nuevo el ZIP de GitHub («que aparezca que hay una nueva versión
disponible»). (2) Un `CHANGELOG.md` público que explique, versión por versión,
qué cambió, por qué y qué se solucionó. (3) Que las versiones anteriores sigan
en GitHub.

**PROMESA DE PRODUCTO (no negociable): nada sale del equipo.** La comprobación de
versión es lo ÚNICO que puede abrir la red, y SOLO si el autor la activa a mano.
El ajuste **`check_updates`** de `dicta_config.json` viene **APAGADO de fábrica**.
Con él activo, Dicta hace **una petición GET anónima** a la API pública de GitHub
(`repos/JDMoreu/dicta/releases/latest`) con un `User-Agent` de la app; esa
petición **no lleva ningún dato del usuario** (ni identificadores, ni telemetría,
ni el estado de la app): lo único que viaja es la propia URL pública. Con el
ajuste apagado, `check_update()` **sale ANTES de tocar la red** y no se abre
ninguna conexión.

**Cambios (dicta.py, dicta_config.json).**

- **Versión única.** Nueva constante **`VERSION = "1.0.0"`** (la que el panel
  muestra como `v1.0.0`); `APP_VERSION` pasa a ser un alias de ella. Es el ÚNICO
  sitio donde se cambia la versión: de ahí salen `/state.version`, el log de
  arranque y el comparador de actualizaciones.
- **`/state.version`** sale ahora de `VERSION` (antes `APP_VERSION = "1.0"`).
- **`/state.update`** nuevo:
  `{available, latest, url, notes, checked_at, progress}` (+ `enabled`, `error`,
  `applied`, `asset_url/size/sha256`, `staged_dir`). Arranca con
  `enabled=false`, todo vacío y `progress=0`.
- **`POST {"action":"check_update"}`**: consulta la última release **solo si el
  ajuste está activo**. Si no, responde `{"ok":false}` con el estado limpio y
  **sin red**. Si está activo rellena `available/latest/url/notes/checked_at`
  (y de la release saca el ZIP portable: `asset_url`, `asset_size` y, si GitHub
  publica `digest` `sha256:…`, `asset_sha256`).
- **`POST {"action":"update"}`**: descarga el ZIP de la release, **verifica su
  integridad** (tamaño siempre; `sha256` si la release lo publica), lo extrae a
  una carpeta temporal y **lanza un ayudante `.cmd`** que espera a que la app se
  cierre, sustituye los ficheros con `robocopy /E` (que **no borra** los datos
  del usuario: `dicta_config.json`, `uploads/`, modelos extra…) y vuelve a
  arrancar la app. El trabajo pesado va en un hilo: el POST responde ya y el
  avance se sigue por `/state.update.progress`. **No se intenta reemplazar el
  `.exe` en caliente.**
- **`POST {"action":"check_updates","value":true|false}`**: interruptor que el
  panel usará para encender/apagar la comprobación (persiste en
  `dicta_config.json`). Al activarlo lanza una comprobación en segundo plano; al
  apagarlo limpia el estado y Dicta deja de tocar la red.
- **`dicta_config.json`**: nueva clave `check_updates: false` y se siembra sola
  al arrancar si falta (mismo patrón que `paste_mode`/`silence_wait`).

**Interfaz para el panel (NO tocada aquí; otro agente trabaja en `panel/*`).**
El panel puede: leer `state.version` y `state.update`; enviar
`{"action":"check_updates","value":<bool>}` para el interruptor;
`{"action":"check_update"}` para «Comprobar ahora»; y `{"action":"update"}` para
actualizar. No se ha modificado ningún fichero de `panel/`.

**Verificación (MEDIDA en este equipo).**

- **APAGADO no sale a la red (demostrado).** Con `urllib.request.urlopen`
  monkeypatcheado para contar y **lanzar error si se le llama**, `check_update()`
  con `check_updates=false` devolvió el estado limpio con **0 llamadas** a
  `urlopen` y la línea de log `Actualizaciones: comprobacion desactivada; no se
  consulta la red.` En vivo, `POST check_update` con el ajuste apagado →
  `{"ok":false, ...,"enabled":false,"latest":""}` y `POST update` → rechazado con
  `{"ok":false,"error":"comprobacion desactivada"}`.
- **ACTIVADO detecta la release.** `check_update()` con el ajuste activo →
  `latest="1.0.1"`, `url="https://github.com/JDMoreu/dicta/releases/tag/v1.0.1"`,
  `notes` con el cuerpo de la release, `checked_at` con fecha, `available=true`.
  En vivo, tras `POST {"action":"check_updates","value":true}`, `/state.update`
  trajo `latest=1.0.1`, la url y las notas.
- **Comparador de versiones:** `1.0.1>1.0.0`, `1.0.0==1.0.0`, `v1.0==1.0.0`,
  `1.2>1.1.9`, `1.0.10>1.0.9` → todos correctos.
- **Descarga y verificación REALES contra la release v1.0.1.** `download_update()`
  bajó `dicta-portable-1.0.1-windows-x64.zip` (**261 415 062 B**, 4,7 s) y
  verificó el sha256 contra el `digest` de la release:
  `528cde2d4c32f7cd31c635c434afa6f1da6156b47983ff9011eea599a82b3465` → **cuadra**.
  `POST {"action":"update"}` en vivo: `progress` subió 22→73→90→100 y el log
  registró `sha256 verificado`. (Como la instancia viva corre en **modo fuente**,
  no el `.exe` congelado, la app reportó `applied:"descargado (modo fuente)"` y
  **no se aplicó**: ver límite abajo.)
- **Extracción y ayudante.** `prepare_update()` extrajo el ZIP real (raíz
  `dicta.exe` + `dicta.exe.config` + `_internal/` con `panel/index.html` +
  `models/ggml-small-q5_1.bin`) y generó `apply_update.cmd` con `SRC`/`DST`/`EXE`
  y el bucle `tasklist`/`findstr` de espera. **Mecanismo probado en un banco de
  arena** (con la MISMA plantilla): con un proceso simulando la app viva, el
  ayudante **no tocó nada en 4 s**; al matar el proceso, copió el fichero nuevo,
  **conservó** `keep_user_data.txt` y `dicta_config.json` (los datos del usuario)
  y **arrancó** de nuevo. `_sha256_file` coincide con `hashlib`.
- **`py_compile dicta.py` OK.** `GET /state` **200** con `version="1.0.0"` y
  `update` presente; el resto de claves intactas (`levels`, `uploads`,
  `engine_options`, `icon_version`, `voice_threshold`, `silence_wait`,
  `rms`/`thr`/`voice`, `paste_mode`, `queue`, `docs`, `mic_test`, `hotkeys`);
  `/panel/icon.png` **200**, `/panel/` **200**.

**Límite honesto (el único).** La sustitución en caliente (ayudante que espera al
cierre y reemplaza los ficheros) **solo se puede llevar a cabo desde el `.exe`
congelado** (el paquete portable). Corriendo en **modo fuente** (`dicta.py`, como
esta instancia) no hay `.exe` que sustituir: Dicta **descarga, verifica y deja el
paquete listo** en `.tmp/update/new`, y lo indica (`applied:"descargado (modo
fuente)"`) en vez de intentar reemplazar el código en marcha. Es el
comportamiento seguro; el camino automático completo se activa en el portable.

**CHANGELOG.md público.** Nuevo fichero en la raíz, en español, de la versión más
nueva a la más antigua: **v1.0.1** (pegado en terminales) y **v1.0.0** (primera
pública), más lo que queda para la **próxima versión** (pegado en agentes/Terax y
esta comprobación de actualizaciones). Contenido sacado de este `CHANGES.md`
(entradas 49–53), **sin inventar nada**.

**No se tocó:** `panel/*`, `dicta_ui.py`, `dicta_icon.py`, el cierre limpio
(`shutdown_service`: sigue liberando la VRAM), la instancia única, los atajos,
`/state` (el resto de claves), `/panel/icon.png`, `/download`,
`doc.rename`/`delete`, `upload.remove`, `MicTest` ni la clase de reunión. Solo
cambian `dicta.py`, `dicta_config.json`, este `CHANGES.md` y el nuevo
`CHANGELOG.md`.

**Aviso sobre la instancia en curso.** La app quedó **viva** (`GET /state` 200,
`version="1.0.0"`, `update` con la comprobación **apagada**). Se relanzó con el
intérprete del venv (`pythonw.exe`, **sin elevar**), porque no se pudo relanzar
elevada sin el autor delante: esta instancia **no pega en ventanas elevadas**
hasta que se reinicie con `run.bat` o el `.exe`.

## 55. Reempaquetado portable 1.0.2: el pegado por destino, la sección única «Audios y documentos» y la actualización desde la app van DENTRO del `.exe` (verificado de punta a punta)

**Qué se publica.** El paquete **`dist/dicta-portable-1.0.2-windows-x64.zip`**
sube **`VERSION` a `"1.0.2"`** (la ÚNICA constante de versión). Lleva ya el código
de hoy: (1) el **pegado automático por destino** (consola → buffer de la consola,
Chromium/Electron → texto tecleado como entrada real, Tauri/WebView2 como Terax →
texto tecleado, emulador de terminal → Ctrl+Shift+V, aplicación normal → Ctrl+V);
(2) la sección única **«Audios y documentos»** del panel (viaja dentro del bundle,
en `_internal/panel/`); y (3) la **actualización desde la propia app**
(`/state.update`, `check_update`/`update`, el ayudante `.cmd` que espera al cierre
y sustituye con `robocopy` conservando los datos del usuario) con el ajuste
**`check_updates` APAGADO de fábrica**.

**Compilación (receta medida).** `.venv/Scripts/python.exe -m PyInstaller
--noconfirm --clean dicta.spec` (el shim `pyinstaller.exe` está roto; hay que usar
`-m PyInstaller`). Salida en `dist/dicta/`: `dicta.exe` + `dicta.exe.config` (al
lado del `.exe`, TOC `EXECUTABLE` para que .NET lea `loadFromRemoteSources`) +
`_internal/` + `models/` (con `ggml-small-q5_1.bin`). `dicta.py` reescribe
`dicta.exe.config` al arrancar si falta (`ensure_dotnet_config`).

**Contenido del ZIP (1077 ficheros, 261 434 121 bytes).** `dicta.exe`,
`dicta.exe.config`, `_internal/` (con `_internal/panel/`) y `models/` con
`ggml-small-q5_1.bin` dentro. **Sin** datos del usuario (ni `audios/`, `textos/`,
`uploads/`, `dicta.log`, `dicta_config.json`, `.tmp/`). `testzip` → OK.
`sha256 = 61bc2de78255f1bd2fa2aa807495d2bbdac7983bdc46e442d69d76539d1a1edb`.
Los ZIP 1.0.0 y 1.0.1 NO se tocan.

**Verificado (esta entrada).**

- **(a) Arranque congelado en carpeta limpia y entorno saneado** (sin
  `PYTHONPATH`/`VIRTUAL_ENV` heredados): `GET /state` **200** con
  `version="1.0.2"`; el log dice **«Panel: backend WebView2 (pywebview)»** y
  «Panel abierto (WebView2, sin barra nativa)». **Sin elevación** (`elevado: no`;
  manifest `asInvoker`).
- **(b) Transcripción real** de un `.wav` subido por la API: cola `listo`, `.md`
  generado en `textos/` con la transcripción; modelo `small` **del propio
  paquete** (nada descargado).
- **(c) Cierre limpio** (`POST {"action":"quit"}`): puerto libre, `dicta.exe` y
  `whisper-server.exe` **muertos** (VRAM liberada, ninguna retenida).
- **(d) Pegado desde el `.exe` congelado**, con receptor fiable: en una **consola
  en modo crudo** llegó el texto (log: «Pegado (buffer de consola) enviado a
  [console: …]»); en una **ventana normal** (Tk) llegó por Ctrl+V (log: «Pegado
  (ctrl+v) enviado a [normal: …]»). En ambos casos el texto recibido fue
  `prueba dicta 123`.
- **(e) ZIP**: contiene `dicta.exe`, `dicta.exe.config`, `_internal/` y `models/`;
  NO contiene datos del usuario; `testzip` correcto (ver arriba).
- **(f) Sin red con la app congelada y `check_updates` apagado**: `/state.update`
  queda con `enabled=false` y `latest=""` (la comprobación sale ANTES de tocar la
  red).

**No se tocó:** `panel/*`, `dicta_ui.py`, `dicta_icon.py`, el cierre limpio
(`shutdown_service`), la instancia única, los atajos ni el resto de `/state`. Solo
cambian `dicta.py` (la constante `VERSION`) y este `CHANGES.md`.

---

## 56. El reproductor de un audio SUBIDO sobrevive al reinicio (`uploads[].src`), el interruptor `check_updates` PERSISTE, y la privacidad queda EXACTA (la comprobación de versión va ACTIVADA por defecto)

**Qué cambia.** Tres arreglos pequeños en `dicta.py` (+ `README.md` y
`CHANGELOG.md`). No se tocan `panel/*`, `dicta_ui.py` ni `dicta_icon.py`.

**(1) El audio de cada subida se persiste y se publica con la MISMA forma que el
panel ya entiende.** El nombre del audio de una subida (el fichero de `audios/`,
`audios/<uid>.<ext>`) solo vivía en `queue[].src`, y `queue` es de la SESIÓN: al
reiniciar se perdía y la tarjeta del documento (que sustituye a la ficha de la
subida al transcribirse) se quedaba sin reproductor. Ahora `UploadStore` guarda la
referencia en el manifiesto (`uploads/uploads.json`, campo interno `audio`) y la
publica en `**/state.uploads[].src**` —el mismo campo que el panel ya lee—, así
que **no hay que tocar el panel**. Además, para que el índice por nombre del panel
(que lee `/state.queue[].src`) siga casando el documento con su audio tras el
reinicio, `queue_for_state()` añade a `queue` entradas SINTÉTICAS de las subidas
ya resueltas (no toca la cola real de transcripción). Una subida aún sin
transcribir sigue apareciendo con su estado.

**(2) El interruptor `check_updates` PERSISTE.** `POST {action:"check_updates",
value:…}` llamaba a `config_set("check_updates", …)`, el mismo camino que el
resto de ajustes. Se dejan consistentes los valores por defecto del CÓDIGO
(`update_enabled()` y el relleno de arranque) a `True`, que es el valor decidido.

**(3) Textos de privacidad EXACTOS.** El README gana una sección **Privacidad**
que dice con precisión que **el audio y el texto nunca salen del equipo** y que lo
único que la app puede sacar por su cuenta es la **consulta de la lista pública de
versiones** de GitHub (`api.github.com/repos/JDMoreu/dicta/releases/latest`), que
**no lleva ningún dato del usuario** y es **desactivable**. El CHANGELOG recoge el
cambio de comportamiento en la sección «Próxima versión»: la comprobación pasa a
ir **encendida por defecto**, con su porqué. Las notas publicadas de v1.0.2 no se
tocan (son correctas para ese binario, que la lleva apagada).

**Medido (esta entrada).** App de desarrollo (`.venv/Scripts/python.exe dicta.py`).

- **(1) Subida real → transcripción → REINICIO.** `POST /upload` de un `.wav` de 4 s
  (`prueba_subida_dicta.wav`, id `359c815489`): `uploads.json` queda con
  `"audio": "f811b24627.wav"` y `/state.uploads[0].src = "f811b24627.wav"`. Tras
  `POST {"action":"quit"}` y reabrir: `GET /state` **200**, `uploads[0].src =
  "f811b24627.wav"` **sigue** y `queue` trae la entrada sintética
  `{id:"359c815489", src:"f811b24627.wav", doc:"prueba_subida_dicta.md", status:"listo"}`,
  de modo que el índice del panel resuelve el audio del documento.
- **(2) Interruptor.** `POST check_updates false` → `dicta_config.json` queda
  `"check_updates": false` y `/state.update.enabled=false`; cerrar y reabrir →
  sigue **`false`** en el fichero y `enabled=false`. Se devuelve a `true` (valor
  por defecto decidido) y queda persistido.
- **(3) `/state` completo y sano.** `GET /state` **200** con TODAS sus claves
  (`levels`, `uploads`, `engine_options`, `icon_version`, `voice_threshold`,
  `silence_wait`, `rms`/`thr`/`voice`, `paste_mode`, `version`, `update`, `docs`,
  `queue`, `hotkeys`…); `dicta_crash.log` en **0 bytes**. Nota de entorno: la
  instancia que estaba viva al empezar era el **portable `dicta.exe` 1.0.2** (que
  sirve SUS copias y escribe SU `dicta_config.json` en `Downloads/`): por eso un
  POST sobre esa instancia no se veía en el `dicta_config.json` del proyecto.

**No se tocó:** `panel/*`, `dicta_ui.py`, `dicta_icon.py`, el cierre limpio
(`shutdown_service`), la instancia única, los atajos, `/panel/icon.png`,
`/download`, `doc.rename/delete`, `upload.remove`, `MicTest`, la clase de reunión
(ganancia, mezclador, `_normalize_wav`, párrafos) ni el pegado por destino.

---

## 57. Reempaquetado portable 1.0.3: el audio de los SUBIDOS, la franja de versión del pie, la comprobación de versiones ACTIVADA y la privacidad van DENTRO del `.exe` (verificado de punta a punta)

**Qué se publica.** El paquete **`dist/dicta-portable-1.0.3-windows-x64.zip`**
sube **`VERSION` a `"1.0.3"`** (la ÚNICA constante de versión; `APP_VERSION` la
sigue). Lleva ya el código de hoy: (1) el **reproductor de un audio SUBIDO**
(la tarjeta muestra su audio con la transcripción debajo); (2) la **referencia
del audio de cada subida persistida en el manifiesto** y publicada en
`/state.uploads[].src`; (3) la **franja de versión del pie** (Actualizado /
Actualización disponible / Actualización pendiente); (4) la **comprobación de
actualizaciones ACTIVADA de fábrica** (`check_updates`); y (5) los **textos de
privacidad** actualizados.

**Compilación (receta medida, sin cambios).**
`.venv/Scripts/python.exe -m PyInstaller --noconfirm --clean dicta.spec` (el shim
`pyinstaller.exe` del venv está roto). `build_exe.bat` borra SOLO `dist\dicta`, no
`dist\` entero, para no llevarse los ZIP publicados. Salida en `dist/dicta/`:
`dicta.exe` (7 760 552 B) + `dicta.exe.config` (1 192 B, AL LADO del `.exe` por el
TOC `EXECUTABLE` del spec, que es de donde .NET saca `loadFromRemoteSources`) +
`_internal/` (1 074 entradas) + `models/ggml-small-q5_1.bin` (190 085 487 B).
`uac_admin=False`: manifest `asInvoker`. La carpeta se **regenera limpia** (los
restos que había —`uploads/`, `.tmp/`, `dicta.log`, `dicta_config.json`— los borra
el `rmdir dist\dicta` previo; comprobado: en la raíz solo hay los 4 elementos).

**Contenido del ZIP (1077 entradas, 261 437 696 B).** Raíz:
`dicta.exe`, `dicta.exe.config`, `_internal/` (con `_internal/panel/`, 4 ficheros)
y `models/ggml-small-q5_1.bin`. **Sin** datos del usuario (ni `audios/`, `textos/`,
`uploads/`, `dicta.log`, `dicta_config.json`, `.tmp/`). `testzip` → **OK**.
Sin deriva: ni un fichero solo en el ZIP ni solo en `dist/dicta`, y el
`sha256(dicta.exe)` del ZIP es idéntico al del disco.
`sha256 = 9013c86e9c29b57283037b41525f6d45fe13abc5126c4237092ef04361356d94`.
Los ZIP 1.0.0, 1.0.1 y 1.0.2 NO se tocan.

**Verificado (esta entrada).** El `.exe` **del propio ZIP**, extraído a una carpeta
limpia (`.tmp/clean103/`) y arrancado con el **entorno saneado** (`PYTHONPATH` y
`VIRTUAL_ENV` sin heredar).

- **(a) Arranque.** `GET /state` **200** con `version="1.0.3"`, `st="idle"`,
  `model="small"`, `engine_resolved="vulkan"`; log: «dicta 1.0.3 listo … (elevado:
  **no**)» y «Panel: backend **WebView2** (pywebview)». WebView2 comprobado de
  verdad por `DICTA_WEBVIEW_DEBUG_PORT=47477`: `…/json/version` responde
  **`Edg/155.0.4283.45`**. `uploads[].src` presente con subida:
  `/state.uploads[0].src = "b2f21b6427.wav"` y el fichero existe en `audios/`.
- **(b) Transcripción real de punta a punta, sin descargar nada.** El audio lo
  sintetizó la **voz local de Windows** (Sabina, es-MX, 16 kHz mono,
  `prueba103.wav` 289 646 B) y se subió por `POST /upload` (200, `saved:1`).
  Modelo `small` **del propio paquete**. En **3 s** la ficha queda `listo` y el
  documento `textos/prueba103.md` (313 B) sale con la transcripción real:
  «Esta es una prueba de transcripción real de dicta versión 1 .03. El documento
  se genera solo, sin salir del equipo.» y su sección de temas.
- **(c) Cierre limpio** (`POST {"action":"quit"}`): `/state` deja de responder en
  **3,5 s**; **0** procesos `dicta.exe`/`whisper-server.exe`, puertos **47810 y
  47801 libres** y la **VRAM dedicada por proceso del `whisper-server`
  (553 MB) liberada** (el `pid_1744` desaparece del contador
  `\GPU Process Memory(*)\Dedicated Usage`); el resto de pids del escritorio
  intactos.
- **(d) Pegado desde el `.exe` congelado**, con receptores fiables:
  **lector en modo CRUDO en una consola** (`ConsoleWindowClass / python.exe`):
  llegó el texto por el **buffer de la consola** («Pegado (buffer de consola)
  enviado a [console: …]») y el receptor leyó **16 chars = `prueba dicta 123`**
  exactos; y una **aplicación normal** (ventana Win32 con control `EDIT` nativo,
  clase `DictaRecv103` → clasificada `normal`): «Pegado (**ctrl+v**) enviado a
  [normal: DictaRecv103 / python.exe]», **16 chars idénticos**.
- **(e) ZIP**: contiene `dicta.exe`, `dicta.exe.config`, `_internal/` y `models/`;
  NO contiene datos del usuario; `testzip` OK (arriba).
- **(f) Con `check_updates` ACTIVADO (valor de fábrica) el `.exe` SÍ consulta y NO
  se anuncia a sí mismo.** `POST /rpc {"action":"check_update"}` → **200** con
  `available=false`, `latest="1.0.2"` (la release publicada más reciente),
  `url=…/releases/tag/v1.0.2`, `enabled=true` y `checked_at` relleno; log:
  «Actualizaciones: ultima 1.0.2 (**ya al dia**); consulta anonima, sin datos del
  usuario.» Con 1.0.3 publicado, `/state.update` quedará `available=false` con
  `latest="1.0.3"`.
- **(g) `dicta.exe.config` viaja DENTRO del ZIP al lado del `.exe`** (raíz del ZIP,
  1 192 B) y `dicta.py` lo reescribe al arrancar si falta
  (`ensure_dotnet_config`).
- **(extra) Persistencia tras REINICIO**: cerrada y reabierta la instancia limpia,
  `/state` **200** con `uploads[0].src="b2f21b6427.wav"` **sigue** y la cola trae
  la entrada sintética `{id:"65c82221a0", src:"b2f21b6427.wav",
  doc:"prueba103.md", status:"listo"}`; `dicta_crash.log` en **0 bytes**.

**No se tocó:** `panel/*`, `dicta_ui.py`, `dicta_icon.py`, `README.md`,
`CHANGELOG.md`, `dicta.spec`, `build_exe.bat`, el cierre limpio
(`shutdown_service`), la instancia única, los atajos ni el pegado por destino.
Solo cambian `dicta.py` (la constante `VERSION`) y este `CHANGES.md`.

## 58. La actualización desde la app YA SE APLICA: el ayudante sobrevive, sustituye el paquete completo y relanza la app

**Qué pedía el autor.** «Cuando le doy actualizar, descarga y me cierra el
aplicativo pero no vuelve y se abre, y tampoco al volverlo a abrir se actualiza:
la actualización no está funcionando realmente.» Descargar y verificar ya iban
bien; lo que fallaba era **aplicar**.

**Los fallos, medidos (no supuestos).** El ayudante `.cmd` que espera al cierre,
sustituye los ficheros y relanza la app nunca llegaba a hacer su trabajo:

1. **Heredaba los descriptores de la app y se colgaba.** Un ayudante de prueba
   (misma plantilla, lanzado con `DETACHED_PROCESS`) seguía VIVO minutos después
   del cierre de su padre, atascado en la orden con tubería
   `tasklist | findstr`: con el `stdout` heredado ya roto, esa orden no termina
   nunca. Con los tres flujos a NULO y **sin tuberías** (todo por fichero) el
   mismo ayudante llegó hasta el final.
2. **`DETACHED_PROCESS` deja al ayudante SIN CONSOLA y `tasklist` escribe en el
   VACÍO:** medido, **0 bytes con código 0**. Se probaron 4 variantes de flags:
   `DETACHED` → 0 B; `CREATE_NO_WINDOW`, `CREATE_NEW_CONSOLE` y sin flag → 89 B
   (la línea «no hay tareas…»). `netstat` y `powershell` se comportan igual que
   `tasklist`; solo los comandos internos (`ver`) contestan. Consecuencia
   exacta: la espera por PID daba «la app ya cerró» **en el acto**, robocopy
   copiaba **con la app aún viva** (su `.exe` no se puede sustituir) y relanzaba
   mientras la instancia vieja tenía el candado puesto → la nueva salía con
   «dicta ya estaba abierto» y se cerraba. Eso es literalmente «se cierra, no se
   sustituye nada y no vuelve a abrirse».
3. **`findstr /C:,"15000",` NO casa nunca** contra una línea que contiene
   `,"15000",` (devuelve **1**): la espera habría saltado siempre aunque hubiera
   consola. Ahora la comprobación lee la **2ª columna** del `tasklist /FO CSV`
   con `for /f "usebackq tokens=2 delims=,"`.
4. **`set "ALIVE="` estaba FUERA del bucle:** en cuanto se veía vivo una vez, ya
   no se reiniciaba y el ayudante esperaba de más y no aplicaba nada. Medido:
   `ERROR: la app (pid 20972) sigue viva tras 90 s` con el proceso ya muerto.

**Cambios (`dicta.py`).**

- **`_spawn_helper()`**: lanza el ayudante DESACOPLADO —
  `CREATE_NO_WINDOW | CREATE_NEW_PROCESS_GROUP` (+ `CREATE_BREAKAWAY_FROM_JOB`
  con respaldo, porque si el job no lo permite da `WinError 5`) y
  `stdin/stdout/stderr` a NULO. Registra el PID y los flags. **Ya no se usa
  `DETACHED_PROCESS`.**
- **`_helper_script()` / `_write_helper()` / `_oem_encoding()`**: el `.bat`
  ayudante se genera aparte y deja **registro por pasos en `update.log`, junto a
  la app** (inicio, paquete, destino, cierre de la app, cada intento de copia con
  su código de robocopy, relanzado, fin, o el error exacto). Espera por PID
  **con tope** (90 s) y, si la app no cierra, lo dice y **no toca nada**.
- **Copia**: `robocopy /E` (paquete COMPLETO y recursivo, no solo el `.exe`) con
  `/R:3 /W:2` **y hasta 5 rondas**, y `/XF dicta_config.json update.log dicta.log
  dicta_crash.log`. `/E` sin `/PURGE` sobreescribe lo que trae el paquete pero
  **no borra nada más**: la configuración y los datos del usuario sobreviven, y
  el paquete no puede pisar el config ni los registros.
- **Relanzado**: `start "" "%EXE%"` apuntando al ejecutable en su ruta; en modo
  fuente, `pythonw` con este script. Limpieza del temporal al terminar.
- **El `.bat` se escribe en la codepage OEM** (`_oem_encoding` → `cp850` aquí):
  antes iba en `ascii`, así que una ruta de usuario con acentos reventaba.
- **Modo fuente**: antes se quedaba en «descargado (modo fuente)» y **no aplicaba
  nunca**; ahora también aplica. El camino del portable del autor no cambia.

**Demostración de punta a punta (banco de pruebas, SIN publicar nada).** Copia de
la app en `.tmp/uptest/bench/install` (VERSION **1.0.3**, puertos
57123/57801/57810 para no chocar con la instancia del autor) + servidor local
que imita `releases/latest` + paquete «nuevo» **real** (ZIP con VERSION **1.0.4**,
testigos y un `dicta_config.json` DECOY):

- `POST check_update` → **200**, `available=true`, `latest=1.0.4`,
  `asset_size=81269`, `asset_sha256=8008cbf8d33ba019…`.
- `POST update` → **202** y log de la app: descarga (el servidor registra
  `GET /dicta-portable-1.0.4-windows-x64.zip -> 200 (81269 B)`),
  `sha256 verificado (8008cbf8d33ba019...)`,
  `ayudante lanzado desacoplado (pid 17940, flags 0x09000200)`.
- **Registro del ayudante**: iniciado → «la app cerró (tras 3 s)» →
  `copia intento 1: robocopy rc=3` → «paquete sustituido; relanzando la app» →
  «app relanzada» → terminado.
- La app **VIEJA (pid 9768) desaparece** y la **NUEVA (pid 22336)** responde sola
  en el mismo puerto con **`version: "1.0.4"`** y
  **`update.testigo: "paquete-nuevo-1.0.4"`** — el testigo viaja en el código, así
  que el proceso que contesta ES el nuevo, no solo un fichero cambiado.
- **Testigos en disco**: `testigo_nuevo.txt` («PAQUETE NUEVO 1.0.4 OK»),
  `subcarpeta/anidado/testigo_anidado.txt` (prueba de `/E` recursivo) y
  `panel/index.html` con `<!-- TESTIGO PANEL 1.0.4 -->` (contenido no ejecutable).
- **Datos del usuario intactos**: `hotkey=ctrl+alt+k` y `silence_wait=42` (el
  DECOY del paquete **no** se aplicó), `audios/` (2 ficheros),
  `textos/documento_usuario.md`, `uploads/`, `models/ggml-tiny-q5_1.bin` y
  `testigo_viejo.txt` (robocopy no purga).
- **Reintentos con un fichero EN USO** (el caso del `.exe` bloqueado en el
  portable): con `panel/index.html` bloqueado en exclusiva 12 s, el registro
  enseña `copia intento 1: robocopy rc=11` con cuatro `ERROR 32 … utilizado por
  otro proceso` y `copia intento 2: robocopy rc=3` → sustituido igualmente.

**Límite honesto.** El ciclo completo se demostró con la app corriendo **desde el
código** (modo fuente), que es donde el banco puede cambiar de versión y volver a
contestar `/state`. En el portable del autor el único tramo distinto es la orden
de relanzado: el ayudante generado en modo portable (volcado en la verificación)
apunta a `start "" "%EXE%"` con `%EXE% = …\dicta.exe` y `DST` = la carpeta del
ejecutable. La sustitución de un `.exe` en uso queda cubierta por los reintentos
medidos arriba.

**No se tocó:** `panel/*`, `dicta_ui.py`, `dicta_icon.py`, el cierre limpio
(`shutdown_service` sigue liberando la VRAM; el quit sigue pasando por él), la
instancia única, los atajos, `/state` (las claves de siempre siguen; solo se
**añaden** `update.update_log` y `update.helper_pid`), `/panel/icon.png`,
`/download`, `doc.rename`/`delete`, `upload.remove`, `MicTest`, la clase de
reunión, el pegado por destino ni la comprobación de versión (sigue activada por
defecto y sin enviar datos del usuario).

**Aviso.** La app quedó **viva** (`GET /state` **200**) con el código anterior al
cambio cargado (solo cambia el camino de actualización, que se ejecuta al pulsar
«Actualizar»). Restos de la prueba: `.tmp/uptest/` (banco, paquete y registros).
No se publicó ninguna release ni se hizo push.

## 59. Reempaquetado portable 1.0.4: el arreglo del ACTUALIZADOR, el dialogo de actualizacion con scroll y las cartas de audio/documento rehechas van DENTRO del `.exe` (verificado de punta a punta)

Esta entrada NO cambia comportamiento nuevo: empaqueta en el `.exe` portable lo
ya medido en la entrada 58 y lo deja verificado de punta a punta. **El unico
cambio en el codigo es la version**: `VERSION` pasa de **"1.0.3"** a **"1.0.4"**
en `dicta.py` (linea 229), que es el unico sitio donde se versiona la app.

**Que viaja dentro del `.exe` 1.0.4** (sin cambios de codigo respecto a la
58):

- El **arreglo del actualizador**: el ayudante se lanza **desacoplado**
  (`CREATE_NO_WINDOW | CREATE_NEW_PROCESS_GROUP`, con intento de
  `CREATE_BREAKAWAY_FROM_JOB`), **espera a que la app cierre por PID con tope**
  de 90 s, sustituye el paquete con **robocopy `/E`** con reintentos
  (`/R:3 /W:2`) y exclusiones (`/XF dicta_config.json update.log dicta.log
  dicta_crash.log`), deja **registro por pasos** en `update.log` y **relanza la
  app** en la ruta nueva.
- El **dialogo de actualizacion** con **scroll en el cuerpo** y **botones
  siempre visibles** (no se empujan fuera de la ventana).
- Las **cartas de audio/documento rehechas**: cabecera -> reproductor con
  **onda real** -> **transcripcion debajo con scroll** -> descargas `.md` /
  `.txt` / `.wav`.

**Receta de build (medida, sin cambios).** `dicta.spec` con PyInstaller onedir,
`console=False` y **`uac_admin=False`** (asInvoker: no pide UAC); `dicta.exe.config`
(`loadFromRemoteSources`) viaja en la **RAIZ** de `dist/dicta` como tipo
`EXECUTABLE` (lo lee .NET al lado del `.exe`); `models/ggml-small-q5_1.bin`
**externo** junto al `.exe`. Se compilo con
`.venv/Scripts/python.exe -m PyInstaller --noconfirm --clean dicta.spec`
(rc=0). `dist/dicta` se regenero **limpio** (se borro entero antes): solo
`dicta.exe`, `dicta.exe.config`, `_internal/` y `models/`, con **una sola**
copia de `panel/` (dentro de `_internal/panel/`).

**Paquete.** `dist/dicta-portable-1.0.4-windows-x64.zip` — **261.439.228 bytes**,
`sha256 = d8baee382ca5a14bdee71f6f98cc06acf6a5a9c18fed9ebaf4279e0beb73101d`.
`testzip` **OK**, 1077 entradas, raiz exactamente
`dicta.exe + dicta.exe.config + _internal/ + models/`. Los ZIP 1.0/1.0.1/1.0.2/1.0.3
**no se tocaron**.

**Verificacion (a)-(g), hecha sobre el `.exe` congelado recien compilado:**

- **(a) Arranque limpio.** ZIP descomprimido en una carpeta LIMPIA
  (`.tmp/clean104`) y arrancado con **entorno saneado** (`PYTHONPATH` y
  `VIRTUAL_ENV` quitados). `GET /state` -> **200** con **`version: "1.0.4"`**,
  `model: "small"`, `engine_resolved: "vulkan"`. La ventana es **WebView2 real**
  (puerto de depuracion CDP): **`Edg/155.0.4283.45`**, no el respaldo de Chrome.
- **(b) Transcripcion REAL de punta a punta.** `POST /upload` (multipart) de un
  wav de 10 s -> cola `listo` -> documento generado en
  `textos/prueba_1_0_4.md` con transcripcion coherente:
  «La reunion del equipo empieza a las 9 y 30 de la manana…» + seccion de temas.
- **(c) Cierre limpio.** Con la app viva (`/state` 200) y `whisper-server.exe`
  cargado: `POST {action:"quit"}` -> **`{"ok": true}`**; despues **`/state`
  deja de responder** (conexion rechazada), **cero procesos** `dicta.exe` /
  `whisper-server.exe` y **VRAM liberada**: 12.722,1 MB -> 12.097,9 MB
  (~624 MB del modelo/motor devueltos a la GPU).
- **(d) Pegado automatico desde el `.exe` congelado.** Carril de entrega del
  propio ejecutable (`POST {action:"test"}`):
  - **Consola en modo crudo** (lector `msvcrt.getwch` en su propia consola):
    recibio **«prueba dicta 123»**; el log dice
    `Pegado (buffer de consola) enviado a [console: ConsoleWindowClass]`.
  - **Aplicacion normal** (ventana Win32 con EDIT nativo en primer plano):
    recibio **«prueba dicta 123»**; el log dice
    `Pegado (ctrl+v) enviado a [normal: DictaRecv104]`.
- **(e) Integridad y contenido del ZIP.** `testzip` **OK**; contiene
  `dicta.exe` (7.764.000 bytes), `dicta.exe.config` (1.192), `_internal/`
  (1074 entradas) y `models/ggml-small-q5_1.bin` (190.085.487). **Ningun dato
  del usuario**: ni `audios/`, ni `textos/`, ni `uploads/`, ni `.tmp/`, ni
  `dicta.log`, ni `dicta_config.json`, ni `update.log`. El ZIP coincide
  exactamente con `dist/dicta` (sin deriva) y su `dicta.exe` es **identico** al
  de disco; el `dicta.exe.config` lleva `loadFromRemoteSources`.
- **(f) El AYUDANTE generado en el paquete es el nuevo.** Volcado el ayudante
  portable generado por `dicta.py` (frozen=True, 50 lineas): espera por PID con
  tope (`if %W% GEQ 90 goto app_alive`), **robocopy `/E` … `/R:3 /W:2 /XF …`**,
  **registro por pasos** (`iniciado`, `la app cerro`, `copia intento N:
  robocopy rc=`, `paquete sustituido; relanzando…`, `app relanzada`, `ayudante
  terminado`) y relanzado `start "" "%EXE%"` apuntando a `dicta.exe`. El lanzado
  es **desacoplado**: medido en vivo con un ayudante inocuo,
  `flags 0x09000200` (CREATE_NO_WINDOW | CREATE_BREAKAWAY_FROM_JOB |
  CREATE_NEW_PROCESS_GROUP) y el ayudante **se ejecuto**. No se aplico ninguna
  actualizacion real.
- **(g) Comprobacion de versiones activada, consulta GitHub y NO se anuncia a si
  mismo.** Con `check_updates` activo, `POST {action:"check_update"}` ->
  `{"ok": true, "enabled": true}` y `/state.update` con la release publicada
  mas reciente (`latest: "1.0.3"`, `checked_at`, `asset_url` del ZIP de la
  1.0.3). Como `1.0.3 < 1.0.4`, **`available: false`**: el ejecutable **no se
  anuncia a si mismo** una version nueva. La consulta es el GET anonimo de
  siempre, sin datos del usuario.

**No se tocó:** `panel/*`, `dicta_ui.py`, `dicta_icon.py`, el cierre limpio
(`shutdown_service` sigue liberando la VRAM), la instancia unica, los atajos,
`/state` (las claves de siempre siguen), `/upload`, `doc.*`,
`upload.remove`, `MicTest`, la clase de reunion, el pegado por destino (solo se
verifico) ni la comprobacion de version (sigue activada por defecto y sin
enviar datos del usuario).

**Aviso.** No se publico ninguna release ni se hizo push. La app quedo
**ARRANCADA y viva** desde `.tmp/clean104` (el `.exe` 1.0.4 congelado):
`GET /state` **200**, `version="1.0.4"`. Restos de la prueba en `.tmp/`
(`clean104/`, `helper_104_portable.cmd`, registros y receptores).

## 60. Borrar un documento o una subida limpia TAMBIÉN su audio de trabajo en `audios/` (antes quedaba huérfano para siempre)

**Problema.** Al borrar un documento o una subida, la tarjeta y sus ficheros
borrables desaparecían, pero la **copia de trabajo del audio** que vive en
`audios/` se quedaba **huérfana para siempre**: el backend no exponía ninguna
acción que la borrara. `upload.remove` solo tocaba `uploads/` y `doc.delete`
solo tocaba `textos/`. Medido en el equipo del autor: `audios/` con **35 `.wav`**
frente a **1 documento** en `textos/`. Basura acumulada que el autor no podía
quitar desde la app.

**Cambio (solo `dicta.py`).**

- `doc.delete` ahora borra el `.md` de `textos/` **y** su audio emparejado por
  nombre base en `audios/` (`<base>.wav`) — para una reunión, la grabación
  original. Mismo criterio de emparejamiento que ya usaban `doc.rename` y
  `/download`.
- `upload.remove` ahora borra el fichero de `uploads/` **y** la copia de trabajo
  de esa subida en `audios/` (la que dejó `TranscribeQueue.add`), tomada de la
  propia ficha persistente (campo `audio`).
- Nuevo helper `_audios_ref(nombre)`: acepta **solo un nombre** (sin separadores
  ni `..`; devuelve `""` si el fichero no existe) — nunca una ruta. La validación
  de `doc.delete` se refuerza con `"/"`.
- Nuevo helper `_remove_file(ruta)`: borra con unos pocos reintentos cortos,
  porque en Windows no se puede borrar un fichero que otro hilo tiene abierto
  (la cola de transcripción puede estar leyendo el audio justo al quitarlo).
- **Acciones nuevas, a propósito** (no automáticas): `POST
  {action:"audio.orphans"}` **solo lista** los audios de `audios/` que ya no
  emparejan con ningún documento ni subida (`{ok,count,orphans}`), y `POST
  {action:"audio.clean", value:"confirmar"}` los borra; sin `"confirmar"`
  responde **400 "confirmacion requerida"**. **Los huérfanos que YA existían NO
  se tocan** hasta que el autor lo pida expresamente: podrían ser grabaciones
  suyas sin documento. Solo se limpia de ahora en adelante.

**Verificación (a)–(d), con borrados reales y listados antes/después.**

- Inicial: `audios/` **45 ficheros** (**35 `.wav`**), `textos/` **1** documento,
  `uploads/` 1 mp3 + `uploads.json`.
- **(a) Documento de reunión.** Creados `textos/zz-reunion-test60.md` +
  `audios/zz-reunion-test60.wav`: `doc.delete` → **200**; el `.md` **y** el
  `.wav` desaparecieron de `textos/` y `audios/`.
- **(b) Subida ya transcrita.** Subido un wav real por multipart → cola `listo`
  → documento `textos/zz-subida-test60.md`, fichero `uploads/03181b4bc9.wav` y
  copia `audios/604b933350.wav`. `doc.delete` + `upload.remove` → **200/200**;
  se fueron el `.md`, el fichero de `uploads/` **y** la copia de `audios/`.
- **(c) Subida pendiente.** Subido un wav largo y quitado mientras la ficha
  estaba **`transcribiendo`**: `upload.remove` → **200**; desaparecieron el
  fichero de `uploads/` **y** su copia de `audios/`. (Matiz honesto: si la
  transcripción ya había terminado en ese instante, su `.md` queda como un
  documento normal y se borra con `doc.delete`, que es lo que hace el panel.)
- **(d) Preexistentes intactos.** Antes y después: **35 `.wav`**, **0
  desaparecidos**. `audio.orphans` listó **44** huérfanos **sin borrar ninguno**;
  `audio.clean` sin confirmación → **400** y el recuento de `.wav` **sin
  cambios**.

**Comprobado además que no se rompe:** `GET /state` **200** con **todas** sus
claves (`uploads`, `docs`, `queue`, `update`, `meeting`, `levels`, `hotkeys`,
`mic_test`, `version`, `st`, `status`… y la referencia `src` del audio),
`/panel/icon.png` (PNG, 200), `/download?kind=md` (200), `/audio` (200),
`doc.rename` ida y vuelta (mueve `.md` **y** `.wav`), validación de nombres
(`doc.delete`/`upload.remove` con travesía → **400/404**).

**No se tocó.** `panel/*`, `dicta_ui.py`, `dicta_icon.py`, el cierre limpio
(`shutdown_service` libera la VRAM), la instancia única, los atajos, `/state`,
`MicTest`, la clase de reunión (ganancia, mezclador, `_normalize_wav`,
párrafos), el pegado por destino ni la comprobación de versión (activada por
defecto y sin enviar datos del usuario).

**Aviso.** No se publicó ninguna release ni se hizo push. La app quedó
**ARRANCADA y viva** desde el **código fuente**
(`.venv/Scripts/pythonw.exe dicta.py`): `GET /state` **200**, `version="1.0.4"`.
Restos de la prueba en `.tmp/` (`restart60*.py`, `verify60*.py`, `verify61.py`,
`smoke62.py`, `dicta.py.bak_60`, `*_out.json`). En paralelo había otro agente
trabajando en `panel/*`; no se tocó nada de ahí.

---

## 61. Buscar e instalar actualizaciones A MANO aunque la comprobación automática esté apagada; `/state` publica el ajuste REAL y el interruptor del panel ya no miente al arrancar

**Problema.** El autor quiere poder **buscar e instalar actualizaciones a mano**
con el enlace «Actualizar» del panel **aunque la comprobación automática esté
apagada** (literalmente su caso: «actualización automática desactivada»). Pero
el motor lo impedía de raíz, medido: con `check_updates` apagado,
`check_update()` devolvía `_update_blank(enabled=False)` **sin hacer ni una
llamada de red**, y `POST {action:"update"}` respondía
`{ok:false,error:"comprobacion desactivada"}`. El enlace manual no podía ni
buscar ni instalar. Además `/state` **no publicaba** el ajuste automático: el
panel espejaba `update.enabled`, que sale en **`off`** (False) hasta la PRIMERA
comprobación **aunque el ajuste esté ACTIVADO de fábrica**, así que el
interruptor mentía al arrancar.

**Cambio (solo `dicta.py` y `panel/app.js`).**

- **Búsqueda forzada.** `check_update(force=False)` acepta un modo FORZADO:
  `POST {action:"check_update","value":{"force":true}}` consulta la API pública
  de GitHub **aunque el ajuste esté apagado** (acción EXPLÍCITA del autor, no
  una comprobación de fondo). Sin `force` el comportamiento NO cambia: con el
  ajuste apagado sigue saliendo ANTES de tocar la red. El handler de `POST` lee
  ahora `value.force` (antes ignoraba cualquier `value`) y devuelve `ok`,
  `force` y `update`.
- **Instalación manual siempre aceptada.** `POST {action:"update"}` (y
  `apply_update()`) ya **no** se bloquean por el ajuste: es explícito. Solo exige
  que haya una versión nueva conocida (`available`), que puede haber rellenado
  una búsqueda forzada previa. Sin versión nueva responde **200
  `{ok:true,accepted:true,started:false,note:"no hay version nueva…"}`**
  (aceptado, sin instalar nada).
- **`/state` con la verdad del ajuste.** `panel_state` publica la clave nueva
  **`check_updates`** (lo que hay en `dicta_config.json`), y
  `UPDATE_STATE["enabled"]` pasa a reflejar también ese ajuste real (una sola
  verdad).
- **Panel (`app.js`).** `updEnabled()` lee `/state.check_updates` (con respaldo
  local `state.check_updates`, defecto `true`, solo antes del primer `/state`)
  en vez de espejar `update.enabled`; el interruptor ya no miente al arrancar.
  El enlace «Actualizar» (`runUpdateSearch`) llama a `check_update` **con
  `force:true`**. No se rediseñó nada.

**Verificación, con medidas; config del autor RESTAURADO a ACTIVADO.**

Con el ajuste **APAGADO** (`POST check_updates false` → `/state.check_updates=false`):

- Búsqueda FORZADA `{"force":true}` → **200**, `ok:true`, `force:true`, latencia
  **0.417 s** (salida real a GitHub), `latest:"1.0.4"`, `available:false`,
  `error:""` → **al día** (la app va por **1.0.5**).
- Búsqueda NORMAL (sin `force`) con el ajuste apagado → `ok:false`, latencia
  **0.002 s**, `latest:""`, `checked_at:""` → **NO toca la red**.
- `POST {action:"update"}` → **200** `{ok:true,accepted:true,started:false,
  note:"no hay version nueva…"}`, **sin** `"comprobacion desactivada"`; la app
  sigue viva y `applied:""` (no instaló nada).

Con el ajuste **ENCENDIDO** (restaurado): búsqueda normal → **200**, `ok:true`,
latencia **0.294 s**, `latest:"1.0.4"`, `error:""` → comportamiento intacto;
`POST update` → mismo criterio aceptado.

`/state`: `check_updates=true` con el ajuste encendido y `=false` apagado (al
arrancar ya aparece el valor real, no un espejo). **DOM** (Chrome headless
propio por CDP, cargando `/panel/`): `#updSwitch[aria-checked]` = **"true"** con
el ajuste encendido y **"false"** apagado, coincidiendo con
`/state.check_updates` y con `updEnabled()`; probado además que con
`update.enabled=false` y el ajuste ON el interruptor queda en **"true"** (el
fallo original queda cerrado). Título de página: «dicta — Ajustes».

**Comprobado que no se rompe:** `GET /state` **200** con **todas** sus claves
(`update`, la nueva `check_updates`, `queue`, `uploads`, `meeting`, `levels`,
`mic_test`, `version`…), `/download?doc=…&kind=md|txt` (**200**, con
`Content-Disposition`), `/audio?name=…` (**200**), `/panel/icon.png` (**200**),
`audio.orphans` (**200**, solo lee), `mic_test` publicado.

**No se tocó.** El resto de `panel/*` (solo se editó `app.js`), `dicta_ui.py`,
`dicta_icon.py`, la franja de versión y su diálogo de notas, el diálogo de
apagado, el medidor horizontal, el botón de apagar, el borrado de documentos y
subidas con su limpieza de audios, `audio.orphans`/`audio.clean`, el cierre
limpio con VRAM, la instancia única, los atajos, el pegado, `MicTest`,
`doc.rename`, `/download` ni `/audio`.

**Aviso.** No se publicó ninguna release ni se hizo push. La app quedó
**ARRANCADA y viva** desde el **código fuente**
(`.venv/Scripts/pythonw.exe dicta.py`): `GET /state` **200**, `version="1.0.5"`,
`check_updates=true` (como estaba). `dicta_config.json` quedó **idéntico** al de
partida (copia en `.tmp/dicta_config.bak_task`). Restos de la prueba en `.tmp/`
(`verify_task.py`, `verify_task_out.json`, `dom_check.py`, `dom_probe.py`,
`dom_out.json`).

---

## 62. Elegir QUÉ GPU concreta usa el motor (no solo la tecnología): dos GPU Vulkan en el equipo y el autor quiere decidir en cuál corre el modelo

**Problema reportado:** *"en el motor puedo seleccionar entre las tecnologías de
la GPU (Vulkan, no CUDA, CPU), pero no puedo seleccionar si tengo dos gráficas,
una integrada y una dedicada, y quiero que el modelo se ejecute en la integrada
y no en la dedicada; no tengo esa opción"*.

**Diagnóstico:** `/state.engine_options` solo ofrecía la TECNOLOGÍA
(Automático/Vulkan/CUDA/ROCm/CPU). El motor (whisper.cpp, `whisper-server.exe`
con backend Vulkan) arrancaba SIEMPRE con su dispositivo por defecto —el `0`, la
GPU **dedicada**— porque nunca se le pasaba un dispositivo. En este equipo hay
**dos** GPU Vulkan, así que faltaba poder elegir cuál.

**Cambios (dicta.py):**
- **Enumeración real de dispositivos.** `list_gpu_devices(engine)` ejecuta el
  binario del motor con `--help` (≈0,2 s, no carga modelo) y parsea las líneas
  que ggml imprime al inicializar el backend (`ggml_vulkan: N = NOMBRE |
  detalles`). Devuelve `[{index, name, desc}]`. **Cacheado** (`/state` se
  sondea muy a menudo: no se lanza un proceso por petición).
- **`/state`.** Cada opción de `engine_options` lleva ahora su lista
  **`devices`** (vacía en las que no aplican: CUDA/ROCm/CPU/Automático) además
  de las claves nuevas **`gpu_device`** (preferencia guardada: `"auto"` o
  `{"index":N}`), **`gpu_device_resolved`** (índice efectivo o `"auto"`) y
  **`gpu_device_note`**.
- **Acción nueva.** `POST {"action":"gpu_device","value":{"index":N}}` y también
  `{"value":"auto"}`: guarda en `dicta_config.json` (`gpu_device`) y **relanza
  el motor** igual que al cambiar de motor (mismo camino que `on_engine`). Si el
  índice **no existe** entre los dispositivos reales, **cae a `auto`** y lo dice
  en `gpu_device_note`.
- **Aplicarlo DE VERDAD al arrancar el motor.** `WhisperServer.ensure` pasa
  **`--device N`** al `whisper-server` cuando `gpu_device` no es `auto` (sin el
  flag, el motor usa su dispositivo `0`). El stderr del motor se guarda en
  `whisper_server.log` (prueba de en qué GPU carga). *Se comprobó que la vía
  fiable con este binario es el flag `--device N`* (también funciona
  `GGML_VK_VISIBLE_DEVICES=N`, verificado; se usa el flag, que nombra el backend
  en el log). `auto` **no cambia el comportamiento actual** (dispositivo 0).

**Verificación, con medidas.**

- **(a) Listado real = `/state`.** `--help` del binario reporta **2** GPU
  Vulkan; `/state.engine_options[vulkan].devices` publica exactamente las
  mismas: `0 = AMD Radeon RX 9070 (AMD proprietary driver) | uma: 0` (dedicada)
  y `1 = AMD Radeon(TM) Graphics (AMD proprietary driver) | uma: 1` (integrada).
  La línea «uma: 1» identifica la integrada.
- **(b) Elegir la INTEGRADA y demostrar la carga ahí.** `POST gpu_device
  {"index":1}` → `gpu_device_resolved=1`; el **log del motor**
  (`whisper_server.log`) pasa a: `whisper_init_with_params_no_state: gpu_device
  = 1` y `whisper_backend_init_gpu: using Vulkan1 backend` (antes, en `auto`,
  `using Vulkan0 backend`). **Rendimiento medido** (misma entrada, modelo
  `large-v3-turbo`, audio de prueba 113 s): dedicada **1,58 s**
  (~72× tiempo real) vs integrada **37,6–41,6 s** (~2,8× tiempo real), o sea
  **~24× más lenta**. **VRAM por tarjeta medida** con el contador de Windows
  `\GPU Adapter Memory(*)\Dedicated Usage`: el adaptador de la dedicada pasa de
  **13.177 MB (modelo en la dedicada) a 12.292 MB (modelo en la integrada)**,
  **−886 MB**, que aparecen (+850 MB) en el adaptador de la integrada. Es decir,
  la dedicada **libera el modelo** al no usarse (medible: sí se puede por
  tarjeta con ese contador; se da el delta, no un mapa de nombre↔LUID porque el
  contador usa LUIDs opacos).
- **(c) Transcripción REAL con la integrada.** El modelo **SÍ carga y
  transcribe** en la integrada (sin error de memoria; UMA = RAM del sistema).
  Texto real (audio `Prueba_1.wav`, 73,5 s): *"A ver, probando la transcripción,
  tiempo real, vamos a ver acá. Falta 100% lo que vamos a ver hoy, ni siquiera
  100% lo real, sino usando NGAM… una herramienta de Jentman Programming…"* →
  legible. **Aviso honesto:** en audio largo (113 s, una sola pasada) la
  integrada entró en **bucle de repetición** ("…el mismo uso de gp…" repetido),
  mientras que la dedicada dio la transcripción limpia; y en `Prueba_1.wav`
  hubo sustituciones ("Dipsy" por "DeepSync"). O sea: **funciona, pero con más
  latencia y peor calidad** en este equipo —es el precio real de forzar la
  integrada—. No se forzó nada: es el resultado medido.
- **(d) Vuelta a `auto`.** `POST gpu_device "auto"` → `gpu_device_resolved="auto"`,
  log de vuelta a **`using Vulkan0 backend`**, y el rendimiento vuelve al de la
  dedicada (55 s → **0,49–0,50 s**; 73 s → **0,90–0,93 s**). `dicta_config.json`
  queda con `gpu_device:"auto"`.
- **(e) Fallback.** `POST {"index":9}` → `gpu_device:"auto"`,
  `gpu_device_note:"El dispositivo 9 no existe entre los disponibles; se usara
  Automatico."`.

**Comprobado que no se rompe:** `GET /state` **200** con **todas** sus claves
(`uploads`, `docs`, `queue`, `check_updates`, `engine_options`, `meeting`,
`levels`, `mic_test`, `version`, y las nuevas `gpu_device*`);
**cierre limpio que libera VRAM** (`POST quit` → puerto 47810 caído, sin
`whisper-server` de Dicta vivo, VRAM de la dedicada **14.064 → 12.170 MB**);
**instancia única** (segundo lanzamiento → «dicta ya estaba abierto» y sale);
**atajos**, **pegado**, **MicTest** (`mic.test start/stop` OK), **doc.rename**
(md + wav emparejado), **`/download`** md/txt (**200**, 10.391 B), **`/audio`**
(**200**, 96.044 B), **búsqueda manual forzada** (`check_update {"force":true}`
→ **200**, 0,37 s, `latest:"1.0.4"`) y **borrado con limpieza de audios**
(`doc.delete` → desaparecen el `.md` y su `.wav`; `audio.orphans` sigue
funcionando).

**No se tocó.** `panel/*`, `dicta_ui.py`, `dicta_icon.py`, y el resto del motor
(solo se añadió la elección de dispositivo y su enumeración).

**Aviso.** No se publicó ninguna release ni se hizo push. La app quedó
**ARRANCADA y viva** desde el **código fuente**
(`.venv/Scripts/pythonw.exe dicta.py`): `GET /state` **200**, `version="1.0.5"`,
motor `vulkan` en `auto` (`using Vulkan0 backend`, la dedicada) y
`gpu_device:"auto"`. `dicta_config.json` quedó **igual que al partir** (copia en
`.tmp/dicta_config.bak_gpudev`) más la clave nueva `gpu_device:"auto"`. Restos de
la prueba en el scratch (`devtest.sh`, `dev_bench.py`).

---

## 63. La ventana del PANEL se puede REDIMENSIONAR con el ratón por los BORDES y las ESQUINAS (sin perder el aspecto sin marco ni la barra propia)

**Problema reportado:** *«La ventana no deja redimensionarla, ¿por qué?»* (la del
panel de ajustes, la que abre Ctrl+Alt+P).

**Diagnóstico (con el código delante y medido):**
- La ventana la crea `create_webview_panel()` (dicta.py) con
  `webview.create_window(...)`: `frameless=True`, `easy_drag=False`,
  `shadow=False` y `min_size=(720,560)`. **No había NINGÚN flag de redimensionado
  activo y, al ser sin marco, Windows no dibuja la franja de borde ni el form
  tiene el estilo de tamaño (`WS_THICKFRAME`)**: no había bordes que agarrar. El
  arrastre desde la barra SÍ funcionaba porque está hecho a mano
  (`WebViewPanelHost.start_drag` / `_drag_loop`), pero eso solo MUEVE.
- La vía «recomendada» para devolver los bordes —contestar `WM_NCHITTEST` con
  `HTLEFT/HTRIGHT/...` en la franja del borde— **no puede funcionar en ESTA
  ventana, y está medido**: el control de WebView2 (clase
  `Chrome_RenderWidgetHostHWND`) cubre TODO el cliente, de borde a borde, así que
  `WindowFromPoint` en los cuatro bordes y las cuatro esquinas devuelve ESE hijo
  y nunca el form de nivel superior: los mensajes de ratón no llegan al form y su
  `WM_NCHITTEST` no se dispara jamás.
- Se probó además la vía «nativa» de mandar `WM_NCLBUTTONDOWN` con el código HT
  del borde (el truco clásico del movimiento por `HTCAPTION`): **medido, NO
  redimensiona esta ventana** (arrastrando los cuatro bordes y una esquina:
  ΔW=ΔH=ΔX=ΔY=**0**): sin `WS_THICKFRAME` Windows no entra en su bucle modal de
  tamaño.

**Cambios:**
- **dicta.py — `create_webview_panel()`:** `min_size=(800,520)` (antes 720×560,
  por debajo del ancho que el diseño necesita) y `resizable=True` explícito, con
  el porqué. Nada más cambia en la creación de la ventana.
- **dicta.py — `WebViewPanelHost.resize_window(edge)` + `_resize_loop`:** el host
  lleva el bucle de tamaño él mismo (igual que ya lleva el de ARRASTRE): guarda
  rectángulo y cursor al empezar y, mientras el botón siga pulsado, coloca la
  ventana moviendo SOLO los lados de ese borde con `SetWindowPos`, con el
  **mínimo 800×520** (recortado por el lado que se arrastra, para que el lado
  fijo no se menee). Una ventana maximizada se deja como está (redimensionarla la
  desmaximizaría de golpe).
- **dicta.py — `_install_panel_min_size(hwnd)`:** subclasifica el WndProc del form
  (`SetWindowLongPtrW` + `CallWindowProcW`) para garantizar en `WM_GETMINMAXINFO`
  un mínimo de 800×520 — mensaje que SÍ llega al form, al contrario que
  `WM_NCHITTEST`.
- **panel/desktop.js — `buildResizeEdges()`:** ocho tiras INVISIBLES
  (`position:fixed`, 6 px, z-index 70) en los bordes del viewport, cada una con su
  cursor CSS (`n-resize`, `e-resize`, `nwse-resize`…); su `mousedown` pide el
  redimensionado por ese borde (`pywebview.api.resize_window(edge)`). Son
  `position:fixed`, así que **no entran en el flujo del documento**.

**Verificación (medida, no «debería»).**

1. **Las tiras existen y es donde se pulsa.** En el DOM real de WebView2 (medido
   con un gancho temporal, ya retirado), `document.querySelectorAll('.dtresize').length`
   = **8**, y `elementFromPoint` en los 8 puntos del borde devuelve
   `dtresize#left`, `#right`, `#top`, `#bottom`, `#topleft`, `#topright`,
   `#bottomleft`, `#bottomright`. Quitando las tiras, esos mismos puntos devuelven
   los elementos de debajo (`rail`, `dtbar`, `app-foot`, `pane`), lo que confirma
   que las tiras están EXACTAMENTE en el filo.

2. **Cableado JS→backend por los 8 bordes.** Un `mousedown` real sobre cada tira
   llega al host: `dicta.log` registra **`Panel: redimensionado por «left» /
   «right» / «top» / «bottom» / «topleft» / «topright» / «bottomleft» /
   «bottomright»`** (los ocho).

3. **Redimensionado real y mínimo (arrastre con el ratón, coordenadas
   GetWindowRect ANTES → DESPUÉS, ventana 1100×760 en (300,140)):**

   | borde arrastrado | antes | después | ΔW | ΔH | ΔX | ΔY |
   |---|---|---|---|---|---|---|
   | inferior | (300,140,1400,900) | (300,140,1400,990) | 0 | **+90** | 0 | 0 |
   | esquina inf. der. | (300,140,1400,900) | (300,140,1510,980) | **+110** | **+80** | 0 | 0 |
   | esquina sup. izq. | (300,140,1400,900) | (190,60,1400,900) | **+110** | **+80** | **−110** | **−80** |
   | mover desde la barra | (300,140,1400,900) | (390,200,1490,960) | 0 | 0 | **+90** | **+60** |

   Mínimo: arrastrando el borde derecho hacia dentro → ancho **clavado en 800**;
   por abajo → alto **clavado en 520**; por la esquina inf. der. → **800×520**
   exactos (no baja de ahí). Maximizar/restaurar intacto: normal
   `(300,140,1324,921)` → maximizada `(0,0,1920,1080)` → restaurada
   `(300,140,1324,921)`.
   *(Los cuatro arrastres con ratón son de la primera pasada; al repetir el robot
   más tarde la inyección sintética de este host dejó de registrarse —medido:
   `SendInput` devuelve 1 pero `GetAsyncKeyState` no ve nunca el botón—, así que
   el cableado de los 8 bordes se re-verificó de forma determinista con el
   `mousedown` sobre cada tira del punto 2. La app y el código son los mismos.)*

4. **El diseño NO cambia (mismo tamaño, con tiras → sin tiras):** todas las
   referencias salen IDÉNTICAS byte a byte. Raíl `[0,36,212,689]` (**212 px de
   ancho**, igual a 800, 1024 y 1500 px de ventana); pie `[0,725,1024,56]` (alto
   **56**); espera: carril `160×8`, tramo `160×8`, tirador `2×18` (solo carril +
   tramo + tirador); medidor de umbral `[555,591,349,26]` con barras `341×18` y
   perilla `2×20`; botón de apagar `[20,737,32,32]` con fondo
   `rgba(0,0,0,0)`, borde `0px` e icono `rgb(215,0,21)`; selector del motor y
   tarjeta gráfica, AMBOS en el mismo raíl `x=758, ancho=216`. **Ninguna cambia.**
   *(La referencia 248/1128 que citabas no coincide con lo que mide el panel hoy:
   el raíl es 212 px y es fijo —no depende del ancho—; probablemente venga de otra
   anchura de ventana o sesión. Lo que importa: es IDÉNTICO antes y después.)*

5. **Reacomodo a otros tamaños:** a **800×520**, ningún elemento rebasa el ancho
   (espera acaba en 691, medidor en 680, selector en 750; raíl 0–212) y el pie
   queda fijo abajo `[0,464,800,56]`; la sección se desplaza en vertical, como ya
   hacía cuando falta altura. A **1500×1000**, el raíl sigue en 212 y el pie en
   56, sin que nada se solape (medido). El cambio de tamaño no rompe el contenido.

**Comprobado que no se rompe.** Arranque desde el **código fuente**
(`.venv/Scripts/pythonw.exe dicta.py`): log `Panel: tamaño mínimo 800x520 fijado
(WM_GETMINMAXINFO)`, `Panel: esquinas redondeadas (DWM)`, `Panel: barra integrada
inyectada`, los **cinco atajos** registrados (`alt+q`, `ctrl+e`, `ctrl+alt+p`,
`ctrl+alt+r`, `ctrl+alt+t`), `GET /state` **200** y el raíl con sus **6
secciones**. La barra propia sigue pintada y su arrastre sigue moviendo la ventana
(+90/+60, sin cambiar de tamaño). El `mousedown` de la barra (`dtbar-drag`) sigue
llamando a `drag_window`.

**No se tocó.** `panel/index.html` (mtime 10:54), `panel/style.css` (10:55),
`panel/app.js` (11:00) y `dicta_ui.py` / `dicta_icon.py`: **sin cambios** —
sus marcas de tiempo son ANTERIORES a esta sesión (que empezó ~11:20), así que no
los he rozado. Los únicos ficheros que toqué son `dicta.py`, `panel/desktop.js` y
`CHANGES.md`. El único JS tocado es `panel/desktop.js` y solo AÑADE las tiras
(posición fija, fuera del flujo). El gancho temporal de medición en el servidor
de control se retiró: no queda ningún `jsdbg` en `dicta.py`.

**Nota (borde superior y botones de la barra).** La tira superior va por encima de
la barra (z-index 70 > 60), así que los **6 px de arriba** de los botones de
minimizar/maximizar/cerrar empiezan un REDIMENSIONADO en vez de pulsarlos — igual
que en Windows, donde el filo de arriba de la barra de título es el borde de
tamaño. El resto de cada botón (30 de sus 36 px) se pulsa con normalidad, y la
zona de arrastre de la barra queda por debajo, intacta.

**Aviso.** No se publicó nada ni se hizo push. La app quedó **ARRANCADA y viva**
desde el código fuente: `GET /state` **200**, `version="1.0.5"`.

---

## 64. Reempaquetado portable 1.0.5: ventana WebView2, transcripción de punta a punta, cierre limpio, pegado en consola y app normal, y el AYUDANTE nuevo van DENTRO del `.exe` (verificado de punta a punta)

**Objetivo.** Recompilar el ejecutable portable con el código (ya terminado) de
esta tanda y dejar listo el paquete `dicta-portable-1.0.5-windows-x64.zip`, sin
volver a subir la versión (ya era `1.0.5`) y sin tocar los ZIP anteriores.

**Cambios:**

- **`dicta.py`:** NINGUNO. `VERSION = "1.0.5"` (línea 233) ya era la correcta;
  comprobado antes y después: `GET /state` publica `version="1.0.5"`. No se subió
  la versión otra vez.
- **Build:** `./.venv/Scripts/python.exe -m PyInstaller --noconfirm --clean
  dicta.spec` (el shim `pyinstaller.exe` sigue roto). `uac_admin=False`
  (`asInvoker`), `console=False`. `dicta.exe.config` viaja en la RAÍZ de
  `dist/dicta` (TOC `EXECUTABLE` del spec) para que .NET cargue
  `loadFromRemoteSources` y WebView2 arranque. El modelo de fábrica
  (`models/ggml-small-q5_1.bin`, 190.085.487 B) se copia al lado del `.exe`.
- **`dicta.spec` / `build_exe.bat`:** sin cambios (la receta que ya funcionaba).

**Verificación (medida, no «debería»).**

1. **Limpieza previa.** Se mataron las instancias sueltas de intentos
   anteriores. Se hizo por la vía limpia: `POST {"action":"quit"}` a la API de la
   instancia que estaba en curso (el `quit` por la ruta `/quit` NO es más que una
   acción vacía: hay que mandar `{"action":"quit"}`, que es lo que dispara
   `os._exit` tras `shutdown_service`). Tras el quit no quedaban procesos
   `dicta.exe`/`whisper-server.exe` ni sockets en `47123`/`47801`/`47810`.

2. **Carpeta limpia y entorno saneado.** El `.exe` se arrancó desde una copia
   limpia del paquete en `%TEMP%\dicta_clean` con
   `env -u PYTHONPATH -u VIRTUAL_ENV -u PYTHONHOME …`. `dicta.log`:
   `Panel: backend WebView2 (pywebview) — ventana sin marco, barra integrada en
   la página`, `Panel abierto (WebView2, sin barra nativa)`, y seis procesos
   `msedgewebview2` hijos. `GET /state` **200**, `version="1.0.5"`,
   `engine_resolved="vulkan"`, `st="idle"`, `elevado: no`.

3. **Transcripción REAL de punta a punta.** `POST` multipart con un `.wav`
   → `{"ok":true,"saved":1}`; el estado de la subida recorre
   **`pendiente` → `transcribiendo` → `listo`** (el `pendiente` se ve en la
   instantánea que devuelve la subida; luego la traza por id captura
   `transcribiendo` y `listo`). Documento generado en `textos/`:
   **«El sistema interno se llama SAFIROK y guarda notas de la reunión.»**
   (audio guardado en `audios/<id>.wav`, entrada en `uploads/`).

4. **Cierre limpio.** `POST {"action":"quit"}` → `dicta.log`:
   `Cierre limpio (salida): liberando GPU y parando servicios...` y
   `Cierre limpio: GPU liberada y sin procesos whisper vivos.`. En ~4 s no
   quedaba ningún proceso `dicta`/`whisper` y los puertos `47123`/`47801`/`47810`
   quedaron libres (sin `whisper-server` residente, la VRAM se suelta).

5. **Pegado automático (dos carriles).**
   - **Consola en modo crudo.** Un lector con `SetConsoleMode` sin
     `ENABLE_LINE_INPUT`/`ENABLE_PROCESSED_INPUT`/`ENABLE_ECHO_INPUT`, en una
     `ConsoleWindowClass`. Con esa ventana en primer plano, `POST test` →
     `dicta.log`: `Pegado (buffer de consola) enviado a [console:
     ConsoleWindowClass / python.exe]` y el lector recibió **`prueba dicta 123`**
     en su buffer de entrada.
   - **Aplicación normal.** Una ventana Win32 estándar con un control `EDIT`
     (clase ajena a consola/terminal/Chromium → carril `ctrl+v`). Con ella en
     primer plano, `POST test` → `dicta.log`: `Pegado (ctrl+v) enviado a
     [normal: DictaPasteTestWnd6 / python.exe]`, y el control leyó
     **`prueba dicta 123`** (`WM_GETTEXT`). *(Primera pasada: el control se creó
     con el bit `ES_READONLY` por un error de estilo del banco de pruebas, así que
     rechazaba el pegado; corregido el estilo, el texto entra. Las teclas sí
     llegaban desde el primer momento: el `EDIT` recibía `WM_KEYDOWN` de
     Ctrl (0x11) y V (0x56) y `WM_CHAR 0x16`.)*

6. **`dist/dicta` y `_internal/panel`.** El paquete contiene EXACTAMENTE
   `dicta.exe` + `dicta.exe.config` + `_internal/` + `models/ggml-small-q5_1.bin`,
   con **una sola** copia de `panel/` (en `_internal/panel/`) y sin copias
   viejas. Los cuatro ficheros del panel COINCIDEN (md5) entre disco y paquete:

   | fichero | md5 (disco == `_internal/panel/`) |
   |---|---|
   | `index.html` | `ea69ede5285aa923a9b56c4384cf2ccd` |
   | `app.js` | `2f71724d75ae9c44e335b6739694274f` |
   | `style.css` | `e60b4de4cc8d55479dd49bec0bbcc62f` |
   | `desktop.js` | `30b963c5a2654899c54ae2d83ee91c1a` |

7. **Resizable (bordes del panel).** En el `.exe` congelado, el árbol de
   accesibilidad del panel muestra las **OCHO tiras invisibles** del
   redimensionado (elementos `Group` de 6 px en `top`/`bottom`/`left`/`right` y
   las cuatro esquinas), y un `mousedown` real sobre la tira derecha dispara el
   cableado JS→backend: `dicta.log` registra `Panel: redimensionado por «right».`
   **Lo que NO se pudo medir aquí:** el cambio de tamaño por arrastre con el
   ratón. En esta sesión (sin autor delante, escritorio no interactivo) la
   inyección de ratón no mantiene el botón pulsado dentro de WebView2
   (`SendInput` reporta éxito pero el `mousedown` del DOM no llega durante el
   arrastre; `GetAsyncKeyState` no ve el botón), así que `GetWindowRect` no
   cambia: `(408,107,1432,888)` antes y después. El cableado y las tiras SÍ se
   verificaron (punto anterior); el arrastre geométrico ya quedó medido en la
   entrada **63**.

8. **AYUDANTE DE ACTUALIZACIÓN (volcado, sin aplicarlo).** El paquete lleva el
   ayudante NUEVO: `_helper_script(...)` genera un `.cmd` **desacoplado** (espera
   a que la app cierre por `tasklist /FI "PID eq <pid>"`, con tope de 90 s),
   sustituye el paquete con `robocopy /E /XF dicta_config.json update.log dicta.log
   dicta_crash.log`, relanza el `.exe` y **deja registro por pasos en
   `update.log`** (iniciado / paquete / destino / app cerrada / copia intento N
   rc= / sustituido / relanzada / terminado, y las ramas `copy_failed` y
   `app_alive`). Se volcó íntegro (50 líneas) solo para comprobarlo; **no se
   aplicó** ninguna actualización.

9. **Comprobación de versiones.** Con el ajuste activado, el `.exe` consulta la
   API pública de GitHub y `dicta.log` anota:
   `Actualizaciones: ultima 1.0.4 (ya al dia); consulta anonima, sin datos del
   usuario.` — la última release es `1.0.4`, así que **no se anuncia a sí mismo**
   ninguna actualización (está en `1.0.5`).

10. **ZIP de release.** `dist/dicta-portable-1.0.5-windows-x64.zip` contiene el
    contenido del paquete (1077 entradas): `dicta.exe`, `dicta.exe.config`,
    `_internal/` y `models/` (con `models/ggml-small-q5_1.bin`). `testzip` sin
    entradas corruptas. **Sin datos del usuario**: ni `audios/`, `textos/`,
    `uploads/`, `.tmp/`, ni `dicta.log`, `whisper_server.log`, `update.log`,
    `dicta_crash.log` ni `dicta_config.json`. Los ZIP anteriores (1.0, 1.0.1,
    1.0.2, 1.0.3, 1.0.4) no se tocaron.

    | ruta | tamaño (bytes) | sha256 |
    |---|---|---|
    | `dist/dicta-portable-1.0.5-windows-x64.zip` | 261.461.757 | `018a99e6c809aa26bf9ea87bb08d4094f75a82ad88b88f9f67eda79598faf7b1` |

**No se tocó.** `panel/*`, `dicta_ui.py`, `dicta_icon.py`, `README.md`,
`CHANGELOG.md` y los ZIP anteriores. Los únicos ficheros modificados son los
permitidos: `dicta.py` (solo comprobado, sin cambios), `dicta.spec`,
`build_exe.bat` (sin cambios) y `CHANGES.md`.

**Aviso.** No se publicó nada ni se hizo push. Al terminar queda **UNA sola
instancia VIVA** del `.exe` congelado, arrancada desde la carpeta limpia:
`GET /state` **200**, `version="1.0.5"`.

---

## 65. UNA sola carta por audio (el `.md` ya no se pinta como una segunda pista), la flecha de la transcripción despliega de verdad, la reproducción no se traba y mientras transcribe se ve «Transcribiendo…» con su progreso

**Problema reportado (grabando un vídeo de demostración):** *«al subir un audio se
duplica, sale el audio solo y luego abajo otra carta del mismo audio pero que en
lugar de terminar en `.mp3` termina en `.md` pero contiene la misma pista:
debería ser una sola. Arregla la transcripción, que no se trabe, que no se
bugee, y si se está transcribiendo que vaya diciendo que está transcribiendo y
que muestre un progreso. Y quiero que sea rápido.»* Con el caso real del autor
(captura): arriba `¿Cuánto costaría correr Claude Opus 5.5 en Local.mp3` (21,9 MB
· 0:15:58) y debajo `¿Cuánto costaría correr Claude Opus 5.5 en Local.md`
(15 KB) **con la duración y el reproductor del audio prestados**.

### 65.1 La duplicación: el nombre base se cortaba por el ÚLTIMO PUNTO

**Diagnóstico (reproducido en el DOM real, 2 tarjetas):** el panel empareja una
subida con su documento por **nombre base** (`docStem`), y `docStem` quitaba la
extensión con `/\.[^.]+$/`. Con un nombre que lleva un punto en medio
—`… Claude Opus 5.5 en Local`— ese patrón no quita `.mp3`/`.md`: quita
`5 en Local`, así que la subida quedaba como `… Opus 5` y el documento como
`… Opus 5.5 en Local`. **No emparejaban**, la subida no se deduplicaba y salían
las dos tarjetas; la del `.md` heredaba además `play` del índice de la cola
(`queueAudioMap`) y con él la duración y el reproductor del audio. Estado real
del panel antes del arreglo:

```json
"items": [
 {"kind":"upload","name":"¿Cuánto costaría correr Claude Opus 5.5 en Local.mp3","state":"listo"},
 {"kind":"doc","name":"¿Cuánto costaría correr Claude Opus 5.5 en Local.md","play":"28798f06be.mp3"}]
"cards": [ {"name":"…Local.mp3","meta":"21.9 MB  ·  0:15:58"}, {"name":"…Local.md","meta":"15 KB","pvTime":"00:00 / 15:57"} ]
```

**Cambios (`panel/app.js`):**
- `FILE_EXT` + `stripExt()`: se quita **UNA extensión real** (wav, mp3, m4a, md,
  txt…), nunca lo que hay tras el último punto. `docStem`, `withExt`,
  `downloadDoc`, `beginRename` y `loadTranscript` usan esa única regla (antes,
  además, descargar un documento con punto en medio bajaba el fichero
  equivocado).
- Con subida emparejada, **la carta es la del AUDIO** que el autor añadió: su
  nombre, su peso y su duración (`u.name` / `u.size` / `u.duration`) y dentro su
  transcripción, sus descargas `.md`/`.txt` y su botón de borrado (que ya quitaba
  las dos cosas). Una reunión grabada, que no tiene subida, enseña el `.wav` de
  la grabación (su audio propio) y su peso real (`/state.docs[].audio_size`, nuevo).
- **Un documento sin audio propio y sin subida que lo respalde NO pinta
  reproductor ni duración** (`play` vacío ⇒ `.m-pv:empty` no ocupa).

**Cambios (`dicta.py`):** `Uploads.rename_doc()` y su llamada desde
`doc.rename`: al renombrar la transcripción la subida emparejada sigue su
rastro (`doc` y su etiqueta). Sin esto, renombrar rompía el emparejamiento y
las dos tarjetas volvían.

**Validación:** mismo audio real subido por `POST /upload` (nombre con punto en
medio) y DOM del panel:

```json
{"nCards":2,"items":[{"key":"doc:Prueba 5.5 en Local.md","kind":"doc","name":"Prueba 5.5 en Local.mp3","play":"0458261525.mp3"},
                     {"key":"doc:base2min.md","kind":"doc","name":"base2min.wav","play":"5e91b82663.wav"}],
 "cards":[{"name":"Prueba 5.5 en Local.mp3","meta":"14.6 MB  ·  0:16:00","pvTime":"00:00 / 16:00","tools":[".md",".txt"]},
          {"name":"base2min.wav","meta":"3.7 MB  ·  0:02:00","pvTime":"00:00 / 02:00","tools":[".md",".txt"]}]}
```

Dos audios distintos ⇒ **dos cartas** (1:1 con `/state.uploads`), y ninguna
segunda carta `.md`. En la reunión de prueba, la carta final es
`reunion-20261016-135838.wav · 5.9 MB · 00:32` con `.md`/`.txt`/`.wav`.

### 65.2 La flecha no hacía nada: la transcripción se quedaba VACÍA y el hueco vacío no ocupa

**Diagnóstico:** el texto se pedía **una sola vez** por tarjeta y, si la petición
fallaba (el `.md` se está escribiendo en ese momento), se marcaba como cargada
dejando el hueco **vacío para siempre**; con `.m-transcript:empty { display:none }`
desplegar no enseñaba nada y parecía que la flecha no hacía nada.

**Cambios:** `loadTranscript` **reintenta** (6 intentos cada 900 ms) y el hueco
dice «Cargando la transcripción…» mientras llega (y «No se pudo cargar la
transcripción…» si se agota), de modo que desplegar SIEMPRE enseña algo. La
flecha sigue siendo el único desplegable de la carta (no había copia duplicada
del componente: `makeMediaCard` es el único constructor de cartas).

**Validación (clic REAL de ratón por CDP en el botón, coordenadas 1155,275):**

```json
"before": {"aria":"false","trHidden":true,"trHeight":0}
"open":   {"aria":"true","hidden":false,"clientH":345,"scrollH":3111,"textLen":15144,"ownScroll":true,"overflowY":"auto"}
"closed": {"aria":"false","hidden":true,"clientH":0,"rowH":129}
"reopened":{"aria":"true","hidden":false,"clientH":345,"textLen":15144}
```

Abre (aria-expanded `true`), muestra la transcripción entera con su propio
desplazamiento (3111 px de contenido en 345 px de hueco), y vuelve a cerrar.
**0 errores de consola, 0 peticiones fallidas** en todas las tandas.

### 65.3 La reproducción: se bajaba el fichero ENTERO antes de sonar y la carta se repintaba mientras suena

**Diagnóstico (medido):** `/audio` servía **todo** como
`application/octet-stream` y **sin rangos**, así que el panel tenía que
descargar el fichero completo (15–22 MB) a un `ArrayBuffer` y montar un `Blob`
con el MIME corregido **antes** de empezar a sonar. Y el sondeo de `/state`
(800 ms; 150 ms con algo capturando) llamaba a `paintMediaCard` en **cada
vuelta**, también mientras suena: `paint: 7 · paintMedia: 7 · paintMediaCard: 7`
en 6 s de reproducción.

**Cambios (`dicta.py`, `panel/app.js`):**
- `/audio` sirve el **tipo MIME real** por extensión (`_audio_ctype`) y
  **soporta `Range`** (`206 Partial Content` + `Content-Range` +
  `Accept-Ranges` + `no-store`), y escribe el fichero **por trozos de 256 KB**
  (nunca 60 MB en memoria).
- El panel usa la **URL directa** del audio (el navegador empieza con el primer
  trozo y salta sin bajarse el fichero entero); el blob queda solo para tipos que
  el navegador no reproduce por URL.
- `mediaSig()`: la tarjeta se repinta **solo si cambia de verdad**. El tiempo que
  corre lo pinta el propio reproductor por sus eventos (`play`/`timeupdate`).

**Validación (clic real de reproducción en la carta de 16:00, 15,4 MB):**

| medida | antes | ahora |
|---|---|---|
| `src` del audio | `blob:` (fichero entero en memoria) | `http://127.0.0.1:47810/audio?name=0458261525.mp3` |
| primer sonido | — (blob completo antes de sonar) | **92 ms** |
| avance en 6 s de reloj | — | **6,00 s** (0 % de retraso) |
| `waiting` / `stalled` | — | 1 (arranque) / **0** |
| `paintMediaCard` durante la reproducción | 7 | **0** |
| peticiones a `/peaks` o `/audio` durante la reproducción | — | **0** (onda ya dibujada y cacheada) |

Ondas medidas: `/peaks` en frío de un mp3 de 16 min = **1,17 s** (una vez por
fichero, cacheado por ruta+mtime+tamaño), `/audio` 15,4 MB = **21 ms**,
`/state` = **3,5 ms**.

### 65.4 «Transcribiendo…» con su progreso (por ESTADO, nunca por «existe el fichero»)

**Diagnóstico:** el `.md` **nace en cuanto empieza a escribir**, así que «existe
el documento» no distingue nada. Peor: la reunión EN CURSO se pintaba como carta
TERMINADA (su `.md` y su `.wav` ya existen durante la grabación), con reproductor
y descargas.

**Cambios:** la carta en curso decide por `/state.uploads[].state` y por el
progreso de la cola (`queue[].progress` emparejado por nombre base) y pinta
**«Transcribiendo… XX %»** con su barra (también «En espera» mientras está en
cola, con la barra a 0). Mientras una reunión está viva, su carta es la del
estado en curso —**sin reproductor** (el `.wav` se está escribiendo) y sin
descargas— con la duración grabada en vivo.

**Validación (línea de tiempo real de `/state`, audio de 16 min):**

```
 t=0,34 s  estado=transcribiendo  progreso=0,0 %     (en cola: 100 %  →  a los 10,69 s: listo)
 t=1,60 s  estado=transcribiendo  progreso=2,7 %     .md ya existe y NO se pinta como terminado
 t=3,14 s  estado=transcribiendo  progreso=21,6 %
 t=10,69 s estado=listo           progreso=100 %
```

Reunión en curso (DOM real, a los 27 s de grabar):

```json
{"name":"reunion-20261016-135838.wav","meta":"0:00:26","tag":"Transcribiendo…","hasPv":false,"tools":[]}
```

y su `.md` (0 bytes en ese instante) **no** aparece como carta aparte. Al
guardarla: `status=guardada · reunion-20261016-135838.md · audio_size=6.192.044`.
**No se quedó colgada ninguna transcripción** (el registro no tiene errores de
cola; los `pendiente` se reencolan al arrancar).

### 65.5 Que sea RÁPIDO: medido con la dedicada, sin recargar el modelo por fichero

**Medido (mismo equipo, motor en Vulkan, dispositivo 0 = AMD Radeon RX 9070):
16:00 de audio (`Prueba 5.5 en Local.mp3`, 15,4 MB) ⇒ transcrito y `listo` en
10,69 s ≈ 90× tiempo real ≈ 0,67 s por minuto de audio** (el propio `.md` del
backend anota `transcribido en ~9s`); un `wav` de 2:00 ⇒ 2,09 s (arranque
incluido, ≈ 1,05 s/min). El registro del servidor de voz confirma la dedicada y
una única carga de modelo:

```
ggml_vulkan: 0 = AMD Radeon RX 9070 (AMD proprietary driver) | uma: 0 ...
whisper_init_with_params_no_state: gpu_device = 0
whisper_backend_init_gpu: using Vulkan0 backend
```

No hay recarga por fichero: un proceso `whisper-server` por sesión y la cola
procesa en serie (`dicta.log`: `Motor GPU (Vulkan) listo (auto (dispositivo 0))`
una sola vez por arranque).

### 65.6 Qué instancia viva (y de qué carpeta)

Antes de tocar nada se comprobó la instancia viva: **`GET /state` 200 en
`127.0.0.1:47810` con las rutas reales del proyecto**
(`C:\Users\JDMoreu\Documents\dicta\audios\…`, `…\textos\…`), servida desde
`Documents\dicta\panel` (el `app.js` servido es **idéntico** al del disco:
`sha256 b9f83b7f…`). El ejecutable de prueba congelado desde `Temp\dicta_clean`
**ya no estaba corriendo** (su `dicta.log` cierra a las 13:01 con «Cierre
limpio»), así que todos los ficheros de esta sesión son los del autor. La app se
reinició una vez (`POST {"action":"quit"}` y relanzado con
`.venv\Scripts\pythonw.exe dicta.py`, **sin elevar**) para cargar los cambios de
`dicta.py`, y queda **viva** al terminar (`GET /state` 200, `version=1.0.5`,
motor Vulkan). Nota: los dos ficheros del caso reportado
(`…Opus 5.5 en Local.mp3` y su `.md`) ya no existían al empezar (el autor los
borró antes de las 13:41); el fallo se reprodujo con un audio de prueba con el
mismo tipo de nombre (un punto en medio).

### 65.7 Lo que NO se tocó

`dicta_ui.py`, `dicta_icon.py`, `README.md`, `CHANGELOG.md`. Nada publicado y sin
push. El resto del panel se verificó después del arreglo con las capturas en
claro y oscuro y **0 errores de consola**: medidor de entrada, barra de espera,
desplegables de motor/tarjeta gráfica, botón de apagar, ventana redimensionable
y el borrado en dos pasos (que sigue limpiando el documento Y su audio de
trabajo). Los ficheros de prueba subidos durante la validación se borraron con la
acción normal del panel (`doc.delete` + `upload.remove`); se conserva la
grabación de reunión de 0:44 de la prueba.

## 66. Reempaquetado portable 1.0.6: UNA sola carta por audio y el acordeón de la transcripción van DENTRO del `.exe` (verificado de punta a punta)

**Objetivo.** Recompilar el ejecutable portable con el código ya terminado de
esta tanda (una sola carta por audio, acordeón con reintentos, audio con rangos y
sin repintar la carta mientras suena, «Transcribiendo…» con progreso) y dejar
listo `dist/dicta-portable-1.0.6-windows-x64.zip`. Sin publicar nada.

**Cambios:**

- **`dicta.py`:** SÓLO la versión — `VERSION = "1.0.5"` → `"1.0.6"` (línea 233).
  Nada más. `GET /state` publica `version="1.0.6"`.
- **`dicta.spec` / `build_exe.bat`:** sin cambios (la receta que ya funcionaba).
- **No se tocó** `panel/*`, `dicta_ui.py`, `dicta_icon.py`, `README.md`,
  `CHANGELOG.md`. Nada publicado ni subido.

**Build:** `./.venv/Scripts/python.exe -m PyInstaller --noconfirm --clean
dicta.spec` → **rc=0 en 19,4 s**. `uac_admin=False` (`asInvoker`,
`<requestedExecutionLevel level="asInvoker" uiAccess="false"/>` comprobado en el
`.exe`), `console=False`. `dist/dicta` = `dicta.exe` (7.777.469 B) +
`dicta.exe.config` (1.192 B, en la RAÍZ: TOC `EXECUTABLE` del spec) +
`_internal/` + `models/ggml-small-q5_1.bin` (190.085.487 B). **Una sola copia de
`panel/`** (`find dist/dicta -type d -name panel` → sólo
`_internal/panel/`). Total 392 MB.

### 66.1 (a) Arranque del `.exe` desde carpeta LIMPIA y con entorno saneado

Copia limpia en `.tmp/clean106` (sin config, sin logs, sin datos), lanzada con
`PYTHONPATH`, `VIRTUAL_ENV` y `PYTHONHOME` **vaciados** y
`DICTA_WEBVIEW_DEBUG_PORT=9333`:

- `GET /state` → **200** con `version="1.0.6"`, `engine=auto` resuelto
  `vulkan`, `model=small`.
- **La ventana es WebView2 de verdad** (no el respaldo de Chrome):
  `http://[::1]:9333/json/version` → `Edg/155.0.4283.45`
  (el PID del puerto es un `msedgewebview2.exe` hijo de `dicta.exe`; seis
  procesos hijos). En el log: `Panel: backend WebView2 (pywebview) — ventana sin
  marco, barra integrada en la página.` y `Panel abierto (WebView2, sin barra
  nativa): http://127.0.0.1:47810/panel`.
- `dicta 1.0.6 listo — alt+q, modo toggle, idioma es, cancelar alt+e
  (elevado: no)`; `Motor GPU (Vulkan) listo (auto (dispositivo 0))`.
  `dicta_crash.log` = **0 bytes**.

### 66.2 (b) Transcripción REAL de punta a punta y UNA sola carta en el panel del congelado

Subida real por `POST /upload` (multipart, `prueba-transcripcion-106.wav`,
6.192.044 B, 0:32) a la instancia congelada:

- Estado del panel/cola recorrido **completo**: `pendiente` (respuesta del POST,
  0,04 s) → `transcribiendo` (0,24 s y 0,47 s) → **`listo` en 0,68 s**
  ≈ 47× tiempo real (modelo `small`, Vulkan) y `progress=100`, con
  `duration=0:32`. Documento: `textos/prueba-transcripcion-106.md`, **748 B**, con
  texto real (empieza «Buenos días, esta es una prueba de transcripción…»).
- **Panel del `.exe` congelado, por CDP sobre su WebView2** (`showSection('audios')`,
  `merge(await getState()); paint()`): **`n_cards = 1`** — una sola carta
  (`prueba-transcripcion-106.wav`, `5.9 MB · 0:00:32`), sin la segunda carta del
  `.md`. Carta medida 754×496 px y el reproductor presente.
- **El acordeón abre y cierra**: `aria-expanded` `false → true → false`
  con el bloque de transcripción pasando de **0 px a 359 px** y de vuelta a 0, y
  con el texto dentro (no un hueco).

### 66.3 (c) Cierre limpio

`POST {"action":"quit"}` → `{"ok": true}` (HTTP 200). Después: `/state` deja de
responder, **0 procesos** (`dicta.exe`, `whisper-server.exe` y los seis
`msedgewebview2.exe`), puertos **47123 / 47801 / 47810 libres**. VRAM dedicada
del motor: **553 MB → 0** (total del escritorio 5126 → 4485 MB). En el log:
`Cierre limpio (salida): liberando GPU y parando servicios...` y
`Cierre limpio: GPU liberada y sin procesos whisper vivos.`

### 66.4 (d) Pegado automático desde el `.exe` congelado — con un límite medido

El carril de prueba del congelado ejecuta, **clasifica** el destino
(`[normal: Chrome_WidgetWin_1 / brave.exe]` → combinación `ctrl+v`), copia el
texto al portapapeles (comprobado leyéndolo: `prueba dicta 123`) y registra
`Pegado inmediato en 0 ms` + `Texto insertado automáticamente en el campo`.

**Límite honesto:** no se pudo cerrar la prueba contra un receptor PROPIO porque
Windows no concede el primer plano a ningún proceso que no sea la ventana del
autor. Medidas **cuatro vías** desde una ventana Tk propia (registrando el
`HWND` y la clase en primer plano después de cada intento):
`SetForegroundWindow`, `AttachThreadInput`+Alt simulado, clic sintético
verificado con `WindowFromPoint` (= mi propia ventana) y `SwitchToThisWindow`
→ en las cuatro el primer plano siguió siendo `Chrome_WidgetWin_1`. La sesión
**no** está bloqueada (sin `LogonUI`) y este shell va en **Medium integrity**
(`Mandatory Label\Medium Mandatory Level`), así que no es UIPI. Como la entrega
apunta SIEMPRE a la ventana con el foco (`app.target_hwnd or
GetForegroundWindow()`), el texto acabó en la ventana de Brave del autor
(texto fijo de prueba `prueba dicta 123`); el portapapeles se guardó antes y **se
restauró** después (su contenido era `Draft Session / off (run a cell to
start)`). Para cerrar este punto con un receptor controlado hace falta que el
autor no tenga el foco en otra aplicación.

### 66.5 (e) ZIP: contenido, integridad y ausencia de datos del usuario

`dist/dicta-portable-1.0.6-windows-x64.zip` — **261.466.399 B**,
`sha256 bebc117cd93e0b988dbc513e0bbeba8331920af6ff691b93af18346e1115436d`, **1.077
entradas**, **`testzip` OK (None)**, raíces exactamente
`dicta.exe`, `dicta.exe.config`, `_internal/` y `models/`
(`models/ggml-small-q5_1.bin` dentro). **Cero ficheros de datos del usuario**: se
rastreó por patrón antes de comprimir y sobre la lista de entradas del ZIP
(`audios/`, `textos/`, `uploads/`, `.tmp/`, `dicta.log`, `whisper_server.log`,
`update.log`, `dicta_crash.log`, `dicta_config.json`, `uploads.json`) → **0**.
Los ZIP anteriores no se tocaron.

### 66.6 (f) El AYUDANTE del paquete sigue siendo el NUEVO

Volcado desde el propio `.exe` (archivo del ejecutable → `marshal` → módulo
`dicta` → `_helper_script`), sin aplicarlo (`.tmp/helper_dump.cmd`, 2.165 B):
**50 líneas**, **10 pasos** escritos en `update.log`, espera por **PID** con
`tasklist /FO CSV /NH` y fichero `pid_check.txt` (no un `findstr` de subcadena),
`robocopy /E /NFL /NDL /NJH /NJS /NP /R:3 /W:2` con `/XF dicta_config.json
update.log dicta.log dicta_crash.log`, relanzado del `.exe` al terminar, limpieza
de `.tmp` y rama de error si la app sigue viva. `_spawn_helper` lleva
`CREATE_NO_WINDOW | CREATE_NEW_PROCESS_GROUP` (`0x8000200`) y
`+ CREATE_BREAKAWAY_FROM_JOB` (`0x1000000`) con sus DOS intentos y `stdin/stdout/
stderr` a nulo.

### 66.7 (g) Comprobación de versiones: consulta a GitHub y NO se anuncia a sí misma

Con `check_updates=true` (real en `/state`, no un campo derivado), el `.exe`
congelado consulta la API pública de releases al arrancar
(`checked_at = 2026-10-16 14:10:58`) y devuelve `latest = "1.0.5"` con
**`available = false`** — no se ofrece a sí mismo la 1.0.5. La comprobación
**forzada** (`{"action":"check_update","value":{"force":true}}`) sale a la red y
repite: `checked_at = 14:21:08`, `latest = 1.0.5`, `available = false`,
`enabled = true`.

### 66.8 (h) `panel/` dentro del paquete idéntico a disco (md5)

| fichero | md5 |
| --- | --- |
| `index.html` | `ea69ede5285aa923a9b56c4384cf2ccd` |
| `app.js` | `3de7c20d751ab097a877a3f78f2e6b70` |
| `style.css` | `e60b4de4cc8d55479dd49bec0bbcc62f` |
| `desktop.js` | `30b963c5a2654899c54ae2d83ee91c1a` |

Coinciden **disco = `dist/dicta/_internal/panel/` = dentro del ZIP**: la copia del
panel es la de esta tanda (es lo que caza un ZIP con el panel anterior).

### 66.9 Limpieza y estado final

Antes de probar se mataron las instancias sueltas de intentos anteriores (**2
`pythonw.exe` que ejecutaban `dicta.py` —uno del venv y otro de
`.dsh\dsh-runtimes`—, 1 `whisper-server.exe` con el modelo en VRAM y 1
`chrome.exe --headless` de sondeo** que ocupaba el puerto 9333 y falseaba la
comprobación de WebView2). Al terminar queda **UNA sola instancia viva**: la app
de desarrollo desde el proyecto (`.venv\Scripts\pythonw.exe dicta.py`, sin
elevar), `GET /state` **200** con `version="1.0.6"`, motor Vulkan y modelo `turbo`.
Los ficheros de prueba de esta verificación viven en `.tmp/clean106` (instalación
limpia de pruebas): **no se tocó nada del autor** —ni sus audios, ni sus
documentos, ni la configuración del proyecto— y su portapapeles se restauró.

---

## 67. Los botones `.md` / `.txt` / `.wav` de las tarjetas no hacían NADA en la ventana real: WebView2 CANCELA la descarga en silencio; ahora el fichero lo guarda el BACKEND con el diálogo nativo «Guardar como...»

**Problema reportado:** *«los botones de .md, .txt, .wav de las transcripciones no
funcionan, no hacen nada al presionarlos»* — en la ventana real de la app.

**Diagnóstico MEDIDO en la ventana real (no en Chrome headless).** La ventana del
panel es WebView2 incrustado (pywebview) con puerto de depuración
(`DICTA_WEBVIEW_DEBUG_PORT=9333`). Pulsando cada botón con un **clic de verdad**
(`Input.dispatchMouseEvent` sobre el rect del botón) y escuchando los eventos de
descarga del motor:

| botón | `Page.downloadWillBegin` | bytes | estado final | fichero en disco |
| --- | --- | --- | --- | --- |
| `.md` | `reunion-20261016-135838.md` | 763 / 763 | **`canceled`** | no |
| `.txt` | `reunion-20261016-135838.txt` | 763 / 763 | **`canceled`** | no |
| `.wav` | `reunion-20261016-135838.wav` | 6.192.044 / 6.192.044 | **`canceled`** | no |

El clic SÍ llega al manejador (se ve el `<a download>` con su
`/download?doc=…&kind=…`), el motor RECIBE la respuesta entera y la **cancela**:
ni diálogo, ni fichero, ni error. La carpeta Descargas quedó igual
(**30 → 30** entradas) y no apareció ninguna excepción de consola. **Por eso la
verificación anterior «pasaba»**: se comprobaba `GET /download` = 200 con
`Content-Disposition: attachment` en un Chrome headless, y **en Chrome eso
guarda el fichero**; el que decide aquí es WebView2. Causa: pywebview **no
gestiona `DownloadStarting`** (0 referencias a *download* en
`webview/platforms/winforms.py`), así que la descarga no tiene destino y el motor
la tira.

**Segundo fallo encontrado al probar con un nombre real:** el resolvedor partía
el nombre por el ÚLTIMO punto (`os.path.splitext`), así que
`¿Cuánto costaría correr Claude Opus 5.5 en Local.md` daba base
`¿Cuánto costaría correr Claude Opus 5` → el guardado (y `GET /download`, que
ahora comparte resolvedor) devolvían `missing` / **404** con documentos de nombre
con punto. Se quita la extensión **solo si es una de las conocidas** (`.md`,
`.txt`, `.wav`).

**Solución elegida: acción del backend + diálogo NATIVO «Guardar como...».** Es lo
que un usuario espera al pulsar descargar en una app de escritorio, y es
independiente del motor de la ventana (Chrome también lo usa: un solo
comportamiento). El panel manda
`POST {action:"export", value:{name, kind:md|txt|wav}}`; el backend abre el
diálogo del sistema (`comdlg32.GetSaveFileNameW`, con la ventana del panel como
dueña, carpeta inicial Descargas, `lpstrDefExt` y aviso de sobrescritura), escribe
el fichero **él mismo** y responde `{ok, path, bytes}`. El panel enseña bajo los
botones una línea corta con la ruta elegida (`Guardado en C:\…`), o
`Guardado cancelado` si se cancela —cancelar NO es un error—, o `No se pudo
guardar`. El botón mantiene su etiqueta y su `aria-label`, y lleva `aria-busy`
mientras el diálogo está abierto. El botón de descarga de la **grabación de
reunión** va por el mismo carril. La nota es `hidden` por defecto: **0 px** de
alto mientras no se usa (la carta mide **129 px** sin nota y **150** con ella).

**Verificación (toda en la VENTANA REAL, con clic real y capturas).**

| botón | ruta escrita | bytes | comprobación de contenido |
| --- | --- | --- | --- |
| `.md` | `.tmp\proof\out1\reunion-20261016-135838.md` | **763** | md5 `fa30c19d…` = al original |
| `.txt` | `.tmp\proof\out1\reunion-20261016-135838.txt` | **763** | mismo texto de la transcripción |
| `.wav` | `.tmp\proof\out1\reunion-20261016-135838.wav` | **6.192.044** | md5 `1999960f…` = al audio; cabecera `RIFF…WAVE fmt` con **PCM, 2 canales, 48000 Hz** |
| `.md` (nombre con acentos y punto) | `.tmp\proof\dk3\¿Cuánto costaría correr Claude Opus 5.5 en Local.md` | **16.743** | md5 `425c17d0…` = al documento |

- **El diálogo sale de verdad**: captura `.tmp\proof\p6_1_oscuro_dialogo.png`
  (ventana `#32770`, título `Guardar como`, tipo `Documento Markdown (*.md)`) y
  `p6_1_oscuro_ruta.png` con la ruta completa en el campo de nombre (el texto se
  leyó con `WM_GETTEXT`: **coincide carácter a carácter**).
- **Cancelar no rompe nada**: con `Escape`/`IDCANCEL` el panel dice
  `Guardado cancelado`, **0 ficheros nuevos**, `aria-busy` a 0 y **0
  excepciones**; en `dicta.log` queda `Guardar como: cancelado (…)`.
- **Dos temas**: nota en el verde del token de cada tema —oscuro `rgb(48,209,88)`,
  claro `rgb(46,125,50)`—, mono 11 px, capturas `panel_oscuro_nota.png` y
  `panel_claro_nota.png`; el tema del autor se dejó en **`light`**
  (`dicta_config.json`).
- **0 errores de consola** (`Runtime.exceptionThrown`) en las **10 pulsaciones**
  repartidas en los lotes.
- **Nada roto alrededor** (DOM de la ventana real): **2 cartas** = una por audio
  (dedupe por raíz de nombre); acordeón (`aria-expanded` alterna, **724**
  caracteres de transcripción, carta 129 → **496 px** y vuelta); reproducción
  fluida (con `volume=0`, el reproductor avanza **1,38 s en 1,4 s**, `00:01 /
  00:32`, estado `playing`); estado de progreso con fixture
  (`Transcribiendo… 42%`, barra al **42 %**); medidor de entrada (**40** barras,
  fixture `rms=0,4` → **36** barras encendidas, estado `voice`, `-38 dB`, la
  barra horizontal retirada sigue retirada); barra de espera (**160×26** en
  `(755,420)`, valor `1,0 s` intacto, **0 marcas**); botón de apagar (fondo
  `rgba(0,0,0,0)`, borde `0px`, icono `rgb(215,0,21)`, `aria="Salir"`, sin
  pulsarlo); **8** tiras de redimensionado (`fixed`, 6 px) y **mínimo de ventana
  clavado en 800×520** (pedido 600×400 → 800×520; pedido 1000×700 → 1000×700;
  ventana restaurada a su 1024×781).
- Se probó con la app **elevada (pid 17380)** y **sin elevar (pid 1900)**: el
  guardado funciona igual en los dos casos (el backend escribe el fichero, no
  hace falta ningún permiso extra).

**Ficheros:** `dicta.py` (bloque «exportar»: `_export_source`, `_export_ctype`,
`_save_as_dialog`, `_export_save`, `_export_owner`; la acción `export` en
`do_POST`; `GET /download` pasa a usar el mismo resolvedor),
`panel/app.js` (`exportFile`/`showSaveNote`, nota `.d-save` en la carta, botón de
la grabación, 4 claves i18n en ES y EN), `panel/style.css` (`.d-save`),
`panel/index.html` (`#meetSaveNote`), `CHANGES.md`.

**Límite honesto:** el diálogo nativo lo abre el proceso de Dicta; con la ventana
del panel en primer plano sale encima de ella, pero si el autor está en otra
aplicación Windows puede pedir el foco (es lo normal en un «Guardar como...»).
Si `comdlg32` no estuviera disponible, la acción devuelve `ok:false` y el panel
dice `No se pudo guardar` en vez de fingir que guardó.


## 68. Reempaquetado portable 1.0.7: el guardado del panel va DENTRO del `.exe` (diálogo nativo «Guardar como» verificado en el congelado)

**Objetivo.** Recompilar el ejecutable portable con el código ya terminado de esta
tanda (`dicta.py`, `panel/*`) y dejar listo
`dist/dicta-portable-1.0.7-windows-x64.zip`. Sin publicar nada.

**Cambios:**

- **`dicta.py`:** SÓLO la versión — `VERSION = "1.0.6"` → `"1.0.7"` (línea 233).
  Nada más. `GET /state` publica `version="1.0.7"`.
- **`dicta.spec` / `build_exe.bat`:** sin cambios (la receta que ya funcionaba).
- **No se tocó** `panel/*`, `dicta_ui.py`, `dicta_icon.py`, `README.md`,
  `CHANGELOG.md`. Nada publicado ni subido.

**Build:** `./.venv/Scripts/python.exe -m PyInstaller --noconfirm --clean
dicta.spec` → **rc=0 en 30,7 s**. `uac_admin=False`
(`requestedExecutionLevel level="asInvoker" uiAccess="false"`, `requireAdministrator`
= 0 ocurrencias), `console=False`. `dist/dicta` = `dicta.exe` (7.782.535 B) +
`dicta.exe.config` (1.192 B, en la RAÍZ: TOC `EXECUTABLE` del spec) + `_internal/` +
`models/ggml-small-q5_1.bin` (190.085.487 B). **Una sola copia de `panel/`**
(`find dist/dicta -type d -name panel` → sólo `_internal/panel/`). Total 392 MB.

### 68.1 (a) Arranque del `.exe` desde carpeta LIMPIA y con entorno saneado

Copia limpia en `.tmp/clean107` (sin config, sin logs, sin datos), lanzada con
`PYTHONPATH`, `VIRTUAL_ENV` y `PYTHONHOME` **vaciados** y
`DICTA_WEBVIEW_DEBUG_PORT=9333`:

- `GET /state` → **200** con `version="1.0.7"`, `engine=auto` resuelto
  `vulkan`, `model=small`.
- **La ventana es WebView2 de verdad**: `http://127.0.0.1:9333/json/version` →
  `Edg/155.0.4283.45`. En el log: `Panel: backend WebView2 (pywebview) — ventana sin
  marco, barra integrada en la página.` y `Panel abierto (WebView2, sin barra
  nativa): http://127.0.0.1:47810/panel`.
- `dicta 1.0.7 listo — alt+q, modo toggle, idioma es, cancelar alt+e (elevado: no)`;
  `Motor GPU (Vulkan) listo (auto (dispositivo 0))`. `dicta_crash.log` = **0 bytes**.

### 68.2 (a bis) El arreglo del guardado DENTRO del congelado: el diálogo nativo «Guardar como» aparece

Pulsando el botón **`.md`** de una carta **CON TRANSCRIPCIÓN**, en la ventana real
del `.exe` (WebView2, por CDP sobre el puerto 9333) y vigilando la ventana por
`EnumWindows` (pid del `.exe`):

- `DIALOGS_BEFORE []` → clic `.md` → **`DIALOG_FOUND True`**,
  `class=#32770`, `title="Guardar como"`, con sus dos `Edit` hijos.
- Cancelado por mensajes (`PostMessageW(dlg, WM_COMMAND, IDCANCEL)`), **sin robar
  el teclado**: `DIALOGS_AFTER_CANCEL []`. El panel enseña **«Guardado cancelado»**
  y en `dicta.log` queda `Guardar como: cancelado (prueba-transcripcion-107.md)`;
  **0 ficheros escritos**.

Es la comprobación que caza el fallo de la 1.0.6 (el botón no hacía nada en
WebView2): en el congelado la acción `export` llega al backend y este abre el
diálogo nativo.

### 68.3 (b) Transcripción REAL de punta a punta y UNA sola carta en el panel del congelado

Subida real por `POST /upload` (multipart, `prueba-transcripcion-107.wav`,
6.192.044 B, 0:32) a la instancia congelada:

- Estado recorrido **completo**: `pendiente` (respuesta del POST, 0,02 s) →
  `transcribiendo` (99 %) → **`listo` (100 %) en ~1,0 s** ≈ 32× tiempo real
  (modelo `small`, Vulkan). Documento: `textos/prueba-transcripcion-107.md`,
  **748 B**, con texto real (empieza «Buenos días, esta es una prueba de
  transcripción…»).
- **Panel del `.exe` congelado, por CDP sobre su WebView2**: **`n_cards = 1`** —
  una sola carta (`prueba-transcripcion-107.wav`, `5.9 MB · 0:00:32`), sin la
  segunda carta del `.md`.
- **El acordeón abre**: `aria-expanded` `false → true` con el bloque
  `.m-transcript` pasando de **0 px a 359,25 px** con el texto dentro.

### 68.4 (c) Cierre limpio

`POST {"action":"quit"}` → `{"ok": true}` (HTTP 200). Después: `/state` deja de
responder, **0 procesos** (`dicta.exe`, `whisper-server.exe` y los seis
`msedgewebview2.exe`), puertos **47810 / 47801 / 9333 libres**, **VRAM dedicada
2597 → 1967 MB** (el modelo `small` liberado). En el log:
`Cierre limpio (salida): liberando GPU y parando servicios...` y
`Cierre limpio: GPU liberada y sin procesos whisper vivos.`

### 68.5 (d) Pegado automático desde el `.exe` congelado — LÍMITE HONESTO: no se forzó

No se cerró el ciclo y se dice por qué: **el primer plano era la propia app
Hermes** (`Chrome_WidgetWin_1`, pid 5204), y el carril de entrega apunta a
`app.target_hwnd or GetForegroundWindow()`. Dispararlo habría **tecleado el texto
de prueba dentro del orquestador** (como ya pasó con Brave en la tanda de la
1.0.6). El brief prohíbe explícitamente robar el foco para forzarlo, así que **no
se pulsó el carril de entrega**.

**Evidencia parcial (código en el bundle):** extrayendo el módulo `dicta` del
propio `dicta.exe` (CArchive → `marshal`) están las funciones del mecanismo de
pegado: `fallback_paste`, `_paste_mode`, `_es_ventana_propia`, `start_delivery`,
`_forzar_primer_plano`, `_post_paste`, `_uia_insert_text`. El código viaja en el
paquete; lo que no se pudo hacer sin foco ajeno es **ejercitarlo de punta a
punta**.

### 68.6 (e) ZIP: contenido, integridad y ausencia de datos del usuario

`dist/dicta-portable-1.0.7-windows-x64.zip` — **261.473.037 B**,
`sha256 7c946cfde968013a7be4bf5188bf6a7017ffe7171a693d64d31da6a0888480ef`, **1.077
entradas**, **`testzip` OK (None)**, raíces exactamente
`dicta.exe`, `dicta.exe.config`, `_internal/` y `models/`
(`models/ggml-small-q5_1.bin` dentro, 190.085.487 B). **Cero ficheros de datos del
usuario**: se rastreó por patrón antes de comprimir y sobre la lista de entradas
del ZIP (`audios/`, `textos/`, `uploads/`, `.tmp/`, `dicta.log`,
`whisper_server.log`, `update.log`, `dicta_crash.log`, `dicta_config.json`,
`uploads.json`) → **0**. Los ZIP anteriores no se tocaron.

### 68.7 (f) El AYUDANTE del paquete sigue siendo el NUEVO

Volcado desde el propio `.exe` (CArchive → `marshal` → módulo `dicta` →
`_helper_script`), sin aplicarlo (`.tmp/helper_dump_107.cmd`): **50 líneas**,
**1.905 B**, **11 pasos** escritos en `update.log`, espera por **PID** con
`tasklist /FI "PID eq %APPPID%" /FO CSV /NH` y fichero `pid_check.txt` (no un
`findstr` de subcadena), `robocopy "%SRC%" "%DST%" /E /NFL /NDL /NJH /NJS /NP /R:3
/W:2 /XF dicta_config.json update.log dicta.log dicta_crash.log`, relanzado del
`.exe` al terminar (`start "" "%EXE%"`), limpieza de `.tmp` y rama de error
`:app_alive` si la app sigue viva. `_spawn_helper` con
`CREATE_BREAKAWAY_FROM_JOB` presente en el bundle.

### 68.8 (g) Comprobación de versiones: consulta a GitHub y NO se anuncia a sí misma

Con `check_updates=true` (real en `/state`, no un campo derivado), el `.exe`
congelado consulta la API pública de releases al arrancar
(`Actualizaciones: ultima 1.0.6 (ya al dia)` en el log) y la comprobación
**forzada** (`{"action":"check_update","value":{"force":true}}`) repite por red:
`ok=true`, `force=true`, `enabled=true`, `latest="1.0.6"`, **`available=false`**,
`checked_at="2026-10-16 17:09:07"`, `error=""`. Con la 1.0.7 instalada no se ofrece
a sí misma ninguna actualización.

### 68.9 (h) `panel/` dentro del paquete idéntico a disco (md5)

| fichero | md5 |
| --- | --- |
| `index.html` | `470072260fe8868cdd5af10a7e3879d7` |
| `app.js` | `947c3a061808494d6790d749643d78eb` |
| `style.css` | `e97b041b59ab5a41a9bb816576171908` |
| `desktop.js` | `30b963c5a2654899c54ae2d83ee91c1a` |

Coinciden **disco = `dist/dicta/_internal/panel/` = dentro del ZIP**: la copia del
panel es la de esta tanda (es lo que caza un ZIP con el panel anterior).

### 68.10 Limpieza y estado final

Antes de probar se mataron las instancias sueltas (los dos `pythonw.exe` que
ejecutaban `dicta.py` —uno del venv y otro de `.dsh\dsh-runtimes`—, el
`whisper-server.exe` con el modelo en VRAM y sus seis `msedgewebview2.exe`
hijos). **Ningún `chrome --headless` ocupaba el 9333**, así que la comprobación de
WebView2 no salió falseada. Al terminar queda **UNA sola instancia viva**: la app
de desarrollo desde el proyecto (`.venv\Scripts\pythonw.exe dicta.py`, sin
elevar), `GET /state` **200** con `version="1.0.7"`, motor Vulkan y modelo `small`,
`dicta_crash.log` **0 bytes**. **No se tocó nada del autor**: ni sus audios, ni sus
documentos, ni su configuración (`dicta_config.json` intacta: `theme=light`,
`engine=vulkan`, `check_updates=true`, `gpu_device=auto`); los ficheros de prueba
de esta verificación viven en `.tmp/clean107`.

---

## 69. Demo en vídeo: GIF en el README y vídeo en la release

**Petición del autor:** subir la demo al repo como GIF en el README y no perder el vídeo completo.

- `demo/Dicta_demo.mp4` (9.756.354 B, 1920x1080, 30 fps, 65,77 s) queda **adjunto a la release v1.0.7** como asset, no en el repo (`demo/.gitignore` bloquea `*.mp4`).
- `demo/dicta-demo.gif`: **1.183.918 B**, 1000x702, **150 fotogramas**, 14,29 fps, **10,5 s**. Tramo **24,5-35,0 s** del vídeo (se añade un audio, la barra pasa de `Transcribiendo...` al resultado y el panel despliega la transcripción), recortado a la ventana real (x 295-1625, y 76-1006) y optimizado con `palettegen` (256 colores, `stats_mode=diff`) + `paletteuse` (sierra2_4a, `diff_mode=rectangle`). El tramo se eligió mirando fotogramas extraídos cada 2-4 s con ffmpeg y descartando los tramos de ajustes o de pantalla sin contenido.
- `demo/panel-dictado.png` y `demo/panel-reunion.png`: dos fotogramas reales del vídeo (t=8 s y t=20 s, recortados a la ventana) como capturas del panel.
- README reescrito en formato breve: badges (release, Windows, MIT), el GIF arriba del todo, qué hace, cómo se usa el portable, notas honestas (ventanas elevadas y UAC, Chrome/Edge para el panel, iconos ocultos en Windows 11), ajustes, motor, privacidad, compilar y arquitectura resumida.

**Validación:** el GIF se releyó con Pillow (150 fotogramas de 70 ms, 10.500 ms en total, 251 colores); la ruta del README coincide carácter a carácter con el fichero subido (`demo/dicta-demo.gif`) y su URL cruda responde 200; `Dicta_demo.mp4` aparece en `gh release view v1.0.7` junto al portable 1.0.7 y la release sigue siendo Latest.


---

## 70. GIF de la demo: el vídeo entero y el fotograma completo

**Petición del autor:** el GIF del README enseñaba solo un tramo (24,5-35,0 s) y estaba recortado a la ventana de la app. Lo quiere entero: **todo el vídeo, de principio a fin**, y **la pantalla completa tal como se grabó**, sin recortar a la ventana.

- `demo/dicta-demo.gif`, **en el mismo nombre y la misma ruta** (el README no cambia de enlace): **12.489.186 B**, **1920x1080**, **921 fotogramas**, 14 fps, **65,78 s**. El vídeo original dura **65,7667 s**: la diferencia es **+13 ms (0,02 %)**. Sin recorte de tiempo ni de imagen — el fotograma es el completo de la grabación (1920x1080, el escritorio con la ventana de Dicta centrada), no la ventana recortada del GIF anterior (1000x702, tramo 24,5-35,0 s).
- Cadena de ffmpeg en una pasada: `fps=14` + `palettegen` (`max_colors=256`, `stats_mode=full`) + `paletteuse` (`dither=sierra2_4a`, `diff_mode=rectangle`), `-loop 0`.
- **Ajustes elegidos y por qué** (medidos con SSIM contra el vídeo y comprobando fotogramas a la vista):
  - **14 fps y no menos**: 10 fps = 10.869.313 B, 12 fps = 11.817.345 B, 14 fps = 12.489.186 B. El peso no aprieta (el objetivo era no pasar de 10-15 MB y GitHub solo avisa a partir de 50 MB), así que se queda el **más fluido** en vez del más liviano.
  - **`dither=sierra2_4a`** (error-diffusion), no `none`: sin dither pesa menos (9.844.509 B a 10 fps) y su SSIM es algo mayor (0,9989 frente a 0,9984), pero en el degradado oscuro del escritorio **aparecen escalones visibles** que con sierra2_4a no están. Manda la vista, no el byte.
  - **`stats_mode=full`**, no `diff`: con el vídeo entero hay escenas de contenido distinto (ajustes, panel, dictado) y la paleta de `diff` sale peor (SSIM 0,9980 frente a 0,9985) sin ahorrar apenas peso.
  - **1920x1080**, la resolución del propio vídeo: no hubo que bajarla para cumplir el objetivo.

**Validación (cifras medidas).** ffprobe: GIF **1920x1080, 921 fotogramas, 65,780 s** frente a los **65,7667 s** del MP4 (Δ = **+13 ms**); el **último fotograma** del GIF coincide con el último del vídeo (**SSIM 0,999998**) y los fotogramas 1-6 con los del vídeo en t=k/14 con error medio ≤ **0,55 niveles**, así que está el principio y está el final. Comparación fotograma a fotograma del GIF entero contra el vídeo: **SSIM 0,9985**. Relectura con Pillow: 921 fotogramas, retardos de 70 y 80 ms. La URL cruda `https://raw.githubusercontent.com/JDMoreu/dicta/master/demo/dicta-demo.gif` responde **200** con **12.489.186 B** y el **mismo sha256** que el fichero local (`9a635d56e174d9fe2feaee923485fc61afa875e21a388eb44cf1607069c95a3b`); `gh api repos/JDMoreu/dicta/contents/demo` da `dicta-demo.gif` con **12.489.186 B**; el README sigue apuntando a `demo/dicta-demo.gif` carácter a carácter; `git rev-parse HEAD` == `git ls-remote origin master` (`8fd6ec32…`).

## 71. El nombre de la app en la prosa: Dicta, con D mayúscula

**Regla del autor:** al referirse a Dicta en el texto del repo, con **D mayúscula**; las rutas, los ficheros, los comandos, los identificadores y las URLs **no se tocan**.

- **README.md (completo):** `# Dicta — dictado y transcripción de voz 100 % local`; «administrador, **Dicta** tiene que correr igual»; «Si no ves el de **Dicta** junto al reloj»; «**la onda de Dicta**».
- **CHANGES.md:** los cuatro encabezados — `# Registro de modificaciones — Dicta`, `## 19. Lanzar Dicta no mostraba nada`, `## 29. El pegado necesita que Dicta corra elevada (y avisos nuevos)` y `## Nota sobre el icono de la bandeja (no es un fallo de Dicta)`. En el **cuerpo** se corrigieron las **21 menciones de prosa** y se dejaron a proposito las citas literales (mensajes de la app, transcripciones y titulos de ventana).
- **Releases (8):** los títulos `dicta vX` → **`Dicta vX`** y el H1 de cada nota (`# Dicta vX`), más «**Dicta** promete que nada sale de tu equipo» en las notas de la v1.0.2. Editadas con `gh release edit --title` y `--notes-file` (fichero UTF-8, que es como se evitan los acentos rotos de la línea de comandos). **No se creó ninguna release nueva**: los assets siguen intactos (`dicta-portable-1.0.7-windows-x64.zip`, 261.473.037 B, y `Dicta_demo.mp4`, 9.756.354 B; los dos `uploaded`) y la **v1.0.7 sigue siendo Latest**, sin draft ni prerelease.
- **Se quedan en minúscula a propósito** (no son prosa, son identificadores o cadenas literales): rutas y ficheros (`dicta.exe`, `dicta.py`, `dicta_ui.py`, `dicta_capture.py`, `dicta_icon.wave_mark`, `dist\dicta\`, `%LOCALAPPDATA%\Programs\dicta`, `dicta-portable-1.0.7-windows-x64.zip`, `demo/dicta-demo.gif`), el repo y las URLs (`JDMoreu/dicta`, las de releases y las de raw), los comandos (`cd dicta`, `git clone …`), el verbo y sus derivados (*«Alt+Q dicta»*, *dictado*, *dictas*), y las citas de cadenas reales de la app («dicta ya está abierto», la ventana titulada `dicta`). También el paso de la bandeja del README («→ dicta»): ese rótulo lo registra la app en minúscula (`PANEL_TITLE = "dicta — Ajustes"` en `dicta.py:4791`, `pystray.Icon("dicta", …, "dicta — dictado por voz")` en `dicta_ui.py:550`), así que se deja como el usuario lo va a leer en Windows. Y las citas literales del propio CHANGES.md («dieta ya estaba abierto», `prueba dicta 123`, el titulo `dicta — Ajustes`) se quedan tal cual: son transcripciones de lo que dijo o imprimió la app, y cambiar una cita falsea el registro.

**Validación.** Los **3 badges** del README responden **200**; `demo/dicta-demo.gif` (sha256 arriba), `demo/panel-dictado.png` y `demo/panel-reunion.png` también **200**; `gh release list` enseña los 8 títulos nuevos con **v1.0.7 = Latest**; `git status --short` solo deja `dicta_config.json` (un ajuste del autor: no se ha tocado).
