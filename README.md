# dicta — dictado por voz local

App mínima de dictado por voz: **Alt+Q → hablas → Alt+Q (o pausa de 2 s) →
insertar transcripción en el campo activo.** Se intenta Windows UI Automation
primero, después Ctrl+V. La transcripción también se conserva en el portapapeles.
100 % local.

## Instalación

Requiere Windows 10/11 y Python 3.12.

```bat
git clone <url-del-repositorio> dicta
cd dicta
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

El motor de transcripción (whisper.cpp) y los modelos pesados **no** se
versionan (están en `.gitignore`, son binarios grandes). Coloca los binarios de
cada backend en `whisper_vulkan\` y `whisper_bin\`, y los modelos `*.bin` en
`models\`; si falta el modelo elegido, la app lo descarga sola la primera vez
desde HuggingFace. Después:

```bat
run.bat            :: abre el panel de ajustes y queda en la bandeja
```

`run.bat` relanza con permisos de administrador (UAC) para poder pegar texto en
aplicaciones elevadas.

## Ajustes (panel)

Clic derecho en el icono de la bandeja → **Abrir ajustes**. El panel es una
ventana de navegador en modo aplicación (Chrome/Edge), servida por la propia
app en `127.0.0.1:47810`. Sin dependencias extra, sin internet.

Tarjetas: **Idioma**, **Motor**, **Modelo**, **Micrófono**, **Sensibilidad**,
**Diccionario**, **Apariencia** y **Atajo de teclado**.

- **Idioma** —Recognition *e interfaz* cambian a la vez. Español / English /
  Português / Français / Deutsch / Italiano. Con `es` la interfaz queda en
  español; con `en`, en inglés (los demás mantienen español).
- **Diccionario** — términos y nombres propios que dictas a menudo. Se envían
  como prompt a whisper en cada petición, así que improves la transcripción de
  palabras técnicas. Intro o **Añadir** para añadir, la **×** del chip para
  quitar. Se guarda en `dicta_config.json`.
- **Apariencia** — tema claro u oscuro; se aplica a la vez al panel y a la
  isla sólida (grafito en oscuro, blanco en claro).
- **Atajos** — **Cambiar** entra en modo captura: pulsas la combinación y se
  aplica en caliente. Hay dos: el de dictado (`alt+q`) y el de cancelar
  (`alt+e`), que descarta lo dictado en curso. Si Windows rechaza la
  combinación (ya ocupada), se conserva la anterior y el panel lo explica.

Todos los parámetros usan el mismo control de lista desplegable; la rejilla
de ajustes es responsive: una o varias columnas según el ancho de la ventana.

> Nota: el idioma se manda en cada petición al servidor, no al arrancarlo, por
> eso el cambio surte efecto en el siguiente dictado sin reiniciar nada.

## Motor de transcripción (seleccionable)

Se elige desde la ventana (**Motor**) o el menú de la bandeja:

- **Automático** — usa lo mejor disponible: NVIDIA+CUDA si hay, si no Vulkan,
  si no CPU.
- **GPU Vulkan** — `whisper_vulkan/whisper-server.exe` (`ggml-vulkan.dll`).
  Funciona en **AMD, Intel y NVIDIA**. Carga el modelo una vez en la GPU y
  queda residente: cada dictado es una petición HTTP local. En una RX 9070,
  `turbo` transcribe 10 s en **~0,17 s** (≈60× tiempo real).
- **GPU CUDA** — `whisper_cuda/whisper-server.exe` (build con CUDA). Solo si
  tienes NVIDIA y has puesto ese build en `whisper_cuda/`.
- **CPU** — `whisper_bin/whisper-cli.exe`; respaldo universal.

Al arrancar detecta el hardware y hace un warmup (compila shaders) para que el
primer dictado ya vaya a tope. Cambiar de motor o de modelo reinicia el
servidor GPU (~1 s).

- `small` (defecto), `tiny`, `base`, `medium`, `turbo` (recomendado con GPU).
  Se descargan automáticamente al seleccionarlos.

## Uso

```bat
run.bat                        :: Alt+Q inicia/para; Alt+E cancela el dictado
run.bat --mode hold            :: mantener Alt+Q pulsada mientras hablas
run.bat --hotkey ctrl+alt+d    :: otra combinación
run.bat --engine vulkan        :: auto | vulkan | cuda | cpu
run.bat --model turbo          :: más precisión (recomendado con GPU)
run.bat --file ruta\audio.flac :: prueba rapida con un archivo
run.bat --list-mics            :: lista micrófonos
run.bat --no-gui               :: solo consola
run.bat --no-panel             :: no abrir el panel de ajustes al arrancar

Atajos globales: **Alt+Q** dicta, **Alt+E** cancela el dictado y **Ctrl+Alt+P**
abre los ajustes (así no dependes de ver el icono de la bandeja). Los tres se
pueden cambiar en el panel.
```

Al arrancar, dicta **abre el panel de ajustes**: es su única cara visible,
porque con `pythonw.exe` no hay consola y vive en la bandeja. Si ya estaba
corriendo, volver a lanzarlo **trae ese panel al frente** en vez de no hacer
nada visible.

Windows 11 esconde los iconos nuevos de la bandeja del sistema. Si no ves el de
dicta junto al reloj, actívalo en **Configuración → Personalización → Barra de
tareas → Otros iconos de la bandeja del sistema → dicta**.

Si la aplicación destino (por ejemplo, OpenCode) está ejecutándose como
administrador, inicia también `run.bat` con **Ejecutar como administrador**.
Windows bloquea la automatización de procesos con distinto nivel de permisos;
no es necesario desactivar Windows Defender.

## La interfaz

- **Bandeja del sistema**: dicta vive como icono junto al reloj. Clic derecho
  abre el menú con **Abrir panel de ajustes** (clic izquierdo también),
  **Modelo**, **Motor**, **Micrófono**, **Sensibilidad**, **Apariencia** y
  **Salir**.
- **Isla al grabar**: mientras una reunión está en marcha, la misma isla se
  queda en pantalla con la onda siguiendo **en vivo** lo que se captura (sistema
  y micrófono), para ver de un vistazo que está entrando audio. El panel muestra
  además el nivel de cada canal por separado.
- **Isla al dictar**: al pulsar Alt+Q aparece en la parte **superior** central,
  colgando del borde de arriba (a 10 px; esquinas de arriba rectas y las de
  abajo redondeadas, como una muesca), de 128×36 px, una isla sólida (grafito en oscuro, blanco en
  claro; estilo Dynamic Island) sin bordes. Mientras hablas muestra una onda
  de degradado plana que sigue tu voz; al procesar, la misma onda en cálido;
  al cancelar (Alt+E) colapsa a puntos en rojo. Al pegar el texto, la isla
  desaparece al instante. Se oculta sola al terminar. Arriba se ve de reojo sin
  tapar lo que estás leyendo; la tarjeta con la transcripción crece hacia abajo.
- **Panel de ajustes**: ventana de navegador en modo aplicación con el diseño
  descrito arriba (idioma, motor, modelo, micrófono, sensibilidad, diccionario,
  fuente de reunión y atajos). El interruptor claro/oscuro (sol ↔ luna)
  vive en la barra superior. Se sirve sin barra nativa del sistema y con el
  icono de dicta; en la barra de tareas se lee **dicta**, no un identificador
  interno. Se abre desde la bandeja o al arrancar la app.

## Identidad

Un solo símbolo recorre la app: **la onda de dicta** (5 cápsulas con el
degradado teal → azul → violeta sobre cuerpo de grafito). Lo dibuja una única
función (`dicta_icon.wave_mark`) para la isla, la bandeja y el icono, así que
no pueden divergir. `dicta_icon.py` genera `dicta.ico` (16 a 256 px) y el de la
bandeja, redibujando cada talla: 5 barras a partir de 40 px y **3 barras más
gruesas por debajo**, porque a 24-32 px cinco barras de 1 px se funden en una
mancha (medido).



## Arquitectura

- El hotkey usa una cola: el hilo detector no toca Tk, el foco ni la
  transcripción. Los cambios de estado y el pegado se procesan desde Tk.
- La estructura nativa `MSG` tiene su tamaño/layout completo de Windows x64.
- `whisper-cli` corre como subprocess con `timeout=180`: un subprocess
  colgado no afecta al resto.
- La transcripción corre en un hilo de trabajo y vuelve a Tk por una cola.
- Inserción por UI Automation (`ValuePattern.SetValue`) para campos accesibles
  como el Prompt de OpenCode Desktop; Ctrl+V es el fallback para el resto.
- El texto queda en el portapapeles aunque el pegado automático sea rechazado.
- El panel es same-origin: `dicta.py` sirve `panel/` y a la vez la API
  (`GET /state`, `POST /rpc`) en `PANEL_PORT = 47810`, solo en `127.0.0.1`. Por
  eso la UI usa `fetch` normal, sin CORS ni puentes. Las acciones llegan por
  `ui_events` y las aplica el hilo de Tk, igual que las de la bandeja.
- `whisper-server` **ignora el flag `-l` del arranque**: el idioma y el prompt
  viajan como campos en cada POST a `/inference`. Por eso el cambio de idioma
  y el diccionario no necesitan reiniciar el servidor.
- La muesca se dibuja con numpy (forma + ecualizador) y se sube al canvas como
  PPM, renderizando a 3x y promediando para anti-alias; fuera de la forma se
  usa el color-key de Windows para que quede transparente. El ancho se anima
  hacia el del texto (efecto Dynamic Island).
- **Todo el Win32 de dicta lleva `argtypes`/`restype` declarados.** Sin eso,
  ctypes devuelve por defecto un `c_int` de 32 bits y un `HMODULE` con los bits
  altos activos llega truncado *con extensión de signo*: `GetModuleHandleW`
  entrega `0xffffffffdb4e0000` en vez de `0x7ff6db4e0000`, y con ese puntero
  basura `RegisterClassExW` y `CreateWindowExW` revientan con *access
  violation*. Fue la causa de que la isla no apareciera nunca.
- **La isla vive en `dicta_ui.py`, sobre la base layered de
  `dicta_layered.py`** (clase `LayeredWindow`): transparencia real por píxel con un solo DIB, cuyo
  tamaño se **recrea para que coincida siempre con el fotograma** (si no,
  `memmove` escribe fuera del búfer y mata el hilo de dibujo) y con
  `WM_NCHITTEST` devolviendo `HTTRANSPARENT` sobre los píxeles transparentes.
- **Para colocar cosas cerca del borde inferior** no basta
  `SPI_GETWORKAREA` (0x0030): con la barra de tareas auto-oculta devuelve la
  pantalla completa, así que también se lee el rectángulo de `Shell_TrayWnd`.
- La captura por aplicación (`dicta_capture.py`) es WASAPI *process loopback*
  en ctypes puro: `ActivateAudioInterfaceAsync` contra el dispositivo virtual
  `PROCESS_LOOPBACK` con el PID objetivo, sin instalar nada.

## Audios, reuniones y documentos

Tres funciones en el panel, con el mismo motor (Vulkan/CPU) y 100 % local:

- **Audios** — sube **uno o varios** archivos (wav, flac, ogg; mp3/m4a si hay
  `ffmpeg` instalado). Se procesan **en cola** con barra de progreso; cada uno
  genera un documento en `textos\` y puedes abrir su transcripción o descargar
  el audio original desde la propia fila de la cola. Cada audio tiene **vista
  previa antes de transcribir**: forma de onda dibujada con los picos reales
  (`GET /peaks`), reproducción con play/pausa y salto al punto que pulses.
- **Reunión** — botón **Iniciar** para capturar el **audio del sistema**
  (loopback WASAPI) **o el de una sola aplicación**, más el **micrófono**, y
  grabarlo en un **.wav estéreo real** (`audios\reunion-*.wav`: canal izquierdo
  = sistema o aplicación, derecho = micrófono) mientras transcribe la reunión
  **en vivo**. La fuente se elige en el panel: *Todo el sistema* (el audio del
  **altavoz por defecto**, no el primero de la lista de dispositivos)
  o una app concreta de las que estén sonando (Teams, el navegador…), útil para
  no mezclar la música de otro programa. La captura por aplicación usa WASAPI
  *process loopback* (por eso `dicta_capture.py` va aparte y sin dependencias),
  y **si falla, la reunión sigue con el micrófono** en vez de caerse. El
  micrófono se captura con **PortAudio** (`sounddevice`), el mismo motor del
  dictado: `soundcard` solo sabe leer dispositivos en IEEE float y con este
  micro abortaba con `AssertionError`, dejando la reunión sin voz. Mientras
  graba muestra temporizador, indicador REC y la última intervención
  transcrita; puedes **pausar/reanudar**, **guardar y terminar**, o **cancelar**
  (descarta grabación y transcripción). Al guardar, el documento queda en
  `textos\` con marcas de tiempo, duración y temas, y se enlaza a su grabación.
- **Documentos** — lista de documentos generados; al pulsar uno se abre en el
  **editor/vista previa**, donde puedes revisarlo, editarlo, **descargarlo**
  como `.md` o `.txt` y **eliminarlo** (con doble confirmación). Los
  documentos de reunión incluyen además el enlace a su `.wav` y su reproductor
  con onda. Cada documento incluye duración, transcripción y **temas**.

Todo queda en `audios\` (originales subidos) y `textos\` (documentos), junto
a la app. Requiere `soundcard` (ya en `requirements.txt`) para la reunión.

## Compilar el ejecutable (.exe)

```bat
build_exe.bat        :: crea dist\dicta\dicta.exe (una sola vez; ~1 min)
```

El resultado es una carpeta `dist\dicta\` que debes distribuir **completa**
(el .exe solo no arranca):

- `dicta.exe` — sin ventana de consola, pide permisos de administrador (UAC)
  al abrir; es necesario para inyectar texto en otras apps.
- `_internal\` — el bundle: `panel\` (interfaz) y los motores
  `whisper_bin\`, `whisper_vulkan\`.
- `models\` — **externo** (no se empaqueta): copia ahí tus `*.bin`. Si falta
  el modelo elegido, se descarga solo la primera vez.
- `dicta_config.json`, `dicta.log`, `.tmp\` — se crean solos al ejecutar.

`dicta.spec` ya deja todo listo (onedir, `--noconsole`, manifiesto de admin,
sin UPX). Instala en una carpeta escribible (p. ej.
`%LOCALAPPDATA%\Programs\dicta`); si lo pones en `Program Files`, el perfil
del panel necesita permisos de escritura.

> La versión que corre se muestra en el pie del panel (`v1.0`): sirve para
> confirmar que no estás sobre un build antiguo.

## Requisitos

Windows 10/11 + Python en `.venv` (requisitos mínimos en
`requirements.txt`: numpy, sounddevice, soundfile, pystray, Pillow).
El arranque usa `pythonw` (sin consola); los registros van a `dicta.log`.
Chrome o Edge instalados para el panel de ajustes (usa el modo aplicación;
si no hay ninguno, el resto de la app funciona igual y los ajustes quedan
solo en la bandeja).
La primera vez, si elegiste un modelo no descargado aún, baja ~150-800 MB
de HuggingFace una sola vez.
