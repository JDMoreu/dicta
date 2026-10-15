# Registro de modificaciones — dicta (reuniones, documentos y UI)

Fecha: 2026-07-10 · Acompañado del skill Impeccable (v4.5.0) para el diseño de UI.

Cada cambio incluye la validación concreta que lo confirmó.

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

## 19. Lanzar dicta no mostraba nada

**Problema:** con `pythonw.exe` no hay consola y la app no abría ninguna
ventana, así que «abrir dicta» no daba ninguna señal visible. Peor: si ya
estaba corriendo, el segundo lanzamiento moría con `dicta ya está abierto (otra
instancia)` — el propio registro lo recoge dos veces (10:41:35 y 10:42:18).

**Cambios:** al arrancar se encola `open_panel` (el panel es la cara visible de
la app). Si ya hay instancia, `_wake_running_instance()` le pide por HTTP
`{"action": "open_panel"}` —recorriendo el rango de puertos y comprobando con
`/state` que quien responde es dicta, para no escribirle a otro programa— y
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

**Diagnóstico:** si dicta muere de golpe, su Chrome sobrevive. Como el perfil es
el mismo, al abrir el panel otra vez Chrome **reutiliza ese proceso** y aparece
una ventana más: se midieron dos a la vez, una `dicta` y otra `dicta-panel-…`.
Limpiar por título no sirve, porque el dicta anterior ya se había renombrado.

**Cambios:** `_clear_stale_panel(profile_dir)` mata los procesos de navegador
cuyo `CommandLine` lleva el perfil del panel (exclusivo suyo) antes de abrir uno
nuevo, e informa cuántos cerró.

**Validación:** tras reiniciar, una sola ventana `Chrome_WidgetWin_1` titulada
`dicta`.

## 22. El notch quedaba inalcanzable sin la burbuja

**Cambios:** entrada **Panel rápido** en el menú de la bandeja, que encola
`("shell", "toggle_panel")`. Si la burbuja está oculta y nunca se colocó, el
notch se ancla a la esquina por defecto en vez de a las coordenadas (0, 0).

## Nota sobre el icono de la bandeja (no es un fallo de dicta)

En `HKCU\Control Panel\NotifyIconSettings` hay tres entradas de dicta —una de
ellas del ejecutable de un dicta ANTIGUO en `Documents\Voice to text\dicta\
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

**Icono de bandeja promocionado.** Las tres entradas de dicta en
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

1. Si la ventana que el usuario mira ahora no es de dicta, se pega **ahí** (cambió
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

## 29. El pegado necesita que dicta corra elevada (y avisos nuevos)

**Diagnóstico del autor, confirmado:** el texto no se pegaba porque dicta estaba
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
- En el pegado: si el destino es protegido y dicta no está elevada, se registra
  el motivo exacto en vez de un «Pegado (Ctrl+V) enviado» que engaña.
- `_forzar_primer_plano()` (AttachThreadInput + Alt simulado): `SetForegroundWindow`
  a secas se ignoraba desde dicta, y por eso el Ctrl+V acababa en otra ventana.

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
desde dicta (DwmSetWindowAttribute falla con E_HANDLE: la ventana es de Chrome) ni
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
- **No es de dicta**: una app congelada mínima reproduce lo mismo. El
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
