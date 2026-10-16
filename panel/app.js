/* dicta — lógica del panel
   Same-origin: la UI se sirve y la API vive en el mismo servidor.

     GET  /state   -> estado (JSON)
     POST /rpc     -> {action, value} y devuelve el resultado real

   Acciones: model | engine | language | theme | sens | mic | dictionary |
             hide | test | quit | window(minimize|maximize|drag) |
             set_hotkey | set_cancel_key
*/

const $  = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];

/* ---------------- i18n ---------------- */
const I18N = {
  es: {
    "ui.title": "Ajustes",
    "ui.windowTitle": "dicta — Ajustes",
    "ui.choose": "Elegir",
    "ui.subtitle": "Dictado por voz, 100% local y privado",
    "ui.statusReady": "Listo para escuchar",
    "ui.statusListening": "Escuchando…",
    "ui.statusTranscribing": "Transcribiendo…",
    "ui.statusLoading": "Cargando modelo…",
    "ui.statusInserted": "Texto insertado",
    "ui.statusTranscribed": "Transcripción lista",
    "ui.statusCancelled": "Cancelado",
    "ui.language": "Idioma",
    "ui.languageHint": "Reconocimiento e interfaz",
    "ui.engine": "Motor",
    "ui.engineUse": "En uso",
    "ui.model": "Modelo",
    "ui.modelHint": "Precisión frente a velocidad",
    "ui.mic": "Micrófono",
    "ui.sens": "Sensibilidad",
    "ui.sensLow": "Solo voces claras",
    "ui.sensHigh": "Capta susurros",
    "ui.dict": "Diccionario",
    "ui.dictHint": "Términos y nombres propios",
    "ui.dictAdd": "Añadir",
    "ui.dictPlaceholder": "Escribe o pega palabras (coma o salto de línea) y pulsa Intro",
    "ui.dictEmpty": "Aún no hay palabras. Añade términos que dictas a menudo.",
    "ui.theme": "Apariencia",
    "ui.themeLight": "Claro",
    "ui.themeDark": "Oscuro",
    "ui.shortcuts": "Atajos de teclado",
    "ui.dictateKey": "Dictado",
    "ui.dictateHint": "Inicia y para la escucha",
    "ui.cancelKey": "Cancelar dictado",
    "ui.cancelHint": "Descarta lo dictado en curso",
    "ui.changeKey": "Cambiar",
    "ui.pressKeys": "Pulsa una tecla, suelta y pulsa la siguiente: se van sumando",
    "ui.hkCombo": "Combinación en curso",
    "ui.hkHint": "Hasta 3 teclas. Retroceso borra la última; «Empezar de cero» las quita todas.",
    "ui.hkBack": "Borrar última",
    "ui.hkClear": "Empezar de cero",
    "ui.hkSave": "Guardar",
    "ui.hkDup": "Esa tecla ya está en la combinación: cada tecla entra una sola vez.",
    "ui.hkEmpty": "Pulsa al menos una tecla antes de guardar.",
    "ui.hotkeyDupMod": "Modificador repetido:",
    "ui.hotkeyUnknown": "Tecla no válida:",
    "ui.cancel": "Cancelar",
    "ui.hotkeyUnavailable": "Ese atajo ya está en uso. Prueba otra combinación.",
    "ui.hotkeyInvalid": "Combinación no válida. Usa una tecla junto a Alt, Ctrl, Mayús o Win.",
    "ui.hotkeyTooMany": "Demasiadas teclas: usa como máximo tres (por ejemplo Ctrl + Alt + S).",
    "ui.hotkeyNeedMain": "Falta la tecla principal: únela a Alt, Ctrl, Mayús o Win.",
    "ui.hotkeySame": "Esa combinación ya está puesta.",
    "ui.hotkeyTimeout": "dicta no respondió. Inténtalo de nuevo.",
    "ui.blockQuick": "Ajustes rápidos",
    "ui.blockWork": "Transcripción de audio",
    "ui.audios": "Audios",
    "ui.audiosHint": "Sube audio, vídeo o lo que sea: se guarda y se transcribe",
    "ui.pickFiles": "Elegir archivos…",
    "ui.queueEmpty": "Sin audios en cola.",
    "ui.addAudioPick": "Elegir archivos…",
    "ui.addAudioPickHint": "Se guarda una copia y se queda en tus ficheros subidos",
    "ui.uploads": "Ficheros subidos",
    "ui.uploadsHint": "Se guardan en la carpeta audios",
    "ui.uploadsEmpty": "Aún no has subido ningún fichero. Elige uno arriba y se guarda aquí.",
    "ui.confirmRemove": "¿Quitar?",
    "ui.stPending": "En espera",
    "ui.stError": "Error",
    "ui.meeting": "Reunión",
    "ui.meetingHint": "Sistema + micrófono, grabado en .wav",
    "ui.startMeeting": "Iniciar",
    "ui.meetTitle": "Inicia la grabación de la reunión",
    "ui.meetDesc": "Captura el audio del sistema y del micrófono, guarda la grabación en .wav y transcribe en vivo.",
    "ui.rec": "REC",
    "ui.pause": "Pausar",
    "ui.resume": "Reanudar",
    "ui.meetSave": "Guardar y terminar",
    "ui.meetCancel": "Cancelar",
    "ui.meetOpen": "Abrir documento",
    "ui.meetDl": "Descargar grabación",
    "ui.meetSaved": "Reunión guardada",
    "ui.meetCancelled": "Reunión cancelada",
    "ui.meetError": "Error:",
    "ui.meetLast": "Última intervención",
    "ui.meetEmptyTr": "El texto transcrito aparecerá aquí en cuanto la reunión hable.",
    "ui.saved": "Guardado",
    "ui.docDelete": "Eliminar",
    "ui.docClose": "Cerrar",
    "ui.dlAudio": "Descargar audio",
    "ui.dlDoc": "Descargar documento",
    "ui.dlDocMd": "Descargar .md",
    "ui.dlDocTxt": "Descargar .txt",
    "ui.saveChoose": "Elige dónde guardar…",
    "ui.saveDone": "Guardado en",
    "ui.saveCancel": "Guardado cancelado",
    "ui.saveFail": "No se pudo guardar",
    "ui.docRename": "Renombrar",
    "ui.remove": "Quitar",
    "ui.ttChangeDictate": "Cambiar atajo de dictado",
    "ui.ttChangeCancel": "Cambiar atajo de cancelar dictado",
    "ui.ttChangePanel": "Cambiar atajo de abrir ajustes",
    "ui.meetingKey": "Grabar reunión",
    "ui.meetingKeyHint": "Inicia y para la grabación de la reunión",
    "ui.meetCancelKey": "Cancelar o detener la reunión",
    "ui.meetCancelKeyHint": "Detiene la reunión en curso sin guardarla",
    "ui.ttChangeMeetCancel": "Cambiar atajo de cancelar reunión",
    "ui.ttChangeMeeting": "Cambiar atajo de grabar reunión",
    "ui.confirmDelete": "¿Eliminar?",
    "ui.confirmCancel": "¿Cancelar reunión?",
    "ui.docs": "Documentos",
    "ui.docsHint": "Revisa, edita y descarga",
    "ui.docsEmpty": "Aún no hay documentos.",
    /* audios y documentos: UNA sola sección (antes eran dos y parecían dos
       sesiones distintas). */
    "ui.audiosDocs": "Audios y documentos",
    "ui.audiosDocsHint": "Un solo sitio: añade audio o vídeo y cada fichero queda aquí con su transcripción",
    "ui.mediaEmpty": "Aún no hay nada. Añade un audio o graba una reunión y aparecerá aquí con su transcripción.",
    /* actualizaciones: la franja del PIE, junto a la versión. La comprobación
       va APAGADA por defecto (privacidad): nada sale del equipo hasta que el
       autor la encienda. Estados: al día / disponible / pendiente. */
    "ui.checkUpdates": "Comprobar si hay versiones nuevas",
    "ui.updOn": "Comprobación activada",
    "ui.updOff": "Comprobación apagada",
    "ui.updUpToDate": "Actualizado",
    "ui.updAvailable": "Actualización disponible",
    "ui.updPending": "Actualización pendiente",
    "ui.updChecking": "Comprobando…",
    "ui.updating": "Actualizando…",
    "ui.updDone": "Actualizado",
    "ui.updFailed": "No se pudo comprobar",
    "ui.updateNow": "Actualizar",
    /* acción manual de la franja: el enlace PREGUNTA antes de buscar, enseña
       «Buscando…» y luego el resultado real; con versión nueva, «Instalar». */
    "ui.updSearchAria": "Buscar una actualización",
    "ui.updSearchTitle": "¿Buscar una actualización?",
    "ui.updSearchBody": "Se hará una consulta anónima a la lista pública de versiones de dicta. No se envía ningún dato tuyo y no se instala nada hasta que lo confirmes.",
    "ui.updSearchGo": "Buscar",
    "ui.updSearching": "Buscando…",
    "ui.updDownload": "Descargando",
    "ui.installNow": "Instalar {v}",
    "ui.updInstallAria": "Actualizar a {v}",
    "ui.updDialogTitle": "¿Actualizar Dicta?",
    "ui.updDialogBody": "Se descargará y aplicará la versión {v}. La descarga la hace tu propio equipo: no se envía nada a ningún sitio.",
    "ui.docTranscript": "Transcripción",
    "ui.transcriptToggle": "Mostrar u ocultar la transcripción",
    "ui.docLoading": "Cargando la transcripción…",
    "ui.docLoadFail": "No se pudo cargar la transcripción. Vuelve a abrirla.",
    "ui.docExists": "Ya existe un fichero con ese nombre.",
    "ui.docRenameFail": "No se pudo renombrar.",
    "ui.save": "Guardar",
    "ui.quit": "Salir",
    "ui.quitTitle": "¿Apagar Dicta?",
    "ui.quitBody": "Se cerrará Dicta y todo lo que esté en marcha: la reunión, el dictado y las transcripciones en curso. ¿Seguro que quieres apagarlo?",
    "ui.quitConfirm": "Apagar Dicta",
    "ui.done": "Listo",
    "ui.panelKey": "Abrir ajustes",
    "ui.panelHint": "Aunque el icono de la bandeja esté oculto",
    "ui.meetMic": "Grabar también mi micrófono",
    "ui.meetMicHint": "Mezcla tu voz con el audio del sistema",
    "ui.meetMicOn": "Sí",
    "ui.meetMicOff": "No",
    "ui.meetSource": "Fuente de audio",
    "ui.meetSourceHint": "De dónde se captura el audio",
    "ui.srcAll": "Todo el sistema",
    "ui.srcMissing": "Aplicación cerrada",
    "ui.pvPlay": "Reproducir",
    "ui.pvSeek": "Saltar en el audio",
    "ui.pvNoWave": "Sin vista previa",
    "ui.pvLoad": "Cargando onda…",
    "ui.pvError": "No se pudo reproducir",
    /* prueba de micrófono (una sola fila: probar, estado, play y duración) */
    "ui.testTitle": "Probando el micrófono…",
    "ui.testHint": "Habla en voz normal mientras dura la prueba.",
    "ui.testStop": "Detener",
    "ui.testDone": "Prueba de micrófono",
    "ui.testAgain": "Repetir",
    "ui.testOk": "El micrófono se oye bien.",
    "ui.testLow": "Nivel muy bajo · acércate al micrófono",
    "ui.testSilent": "No se captó audio · acércate al micrófono",
    /* micrófono: grupo único (dispositivo, umbral + prueba integrados) */
    "ui.micGroupHint": "Dispositivo, umbral y prueba de entrada",
    "ui.micDevice": "Dispositivo de entrada",
    "ui.testRowTitle": "Probar la entrada",
    "ui.testRowHint": "Habla con voz normal para comprobar la entrada.",
    "ui.testStart": "Probar",
    /* umbral de voz real (voice_threshold, 0..1) */
    "ui.sensPeakNow": "Umbral real",
    "ui.voiceThresholdHint": "Nivel que debe superar tu voz para que dicta la escuche. Bájalo si no te oye; súbelo si capta ruido de fondo.",
    "ui.voiceThresholdLow": "Muy sensible: capta hasta susurros",
    "ui.voiceThresholdHigh": "Solo voz fuerte",
    /* medidor de entrada en vivo (rms / thr / voice) */
    "ui.micMeter": "Nivel de entrada",
    "ui.micMeterHint": "Habla y mira dónde cae tu voz: la marca es el umbral de voz.",
    "ui.micNoVoice": "Sin voz",
    "ui.micVoice": "Voz detectada",
    "ui.micMeterQuiet": "Silencio",
    "ui.micMeterLoud": "Voz fuerte",
    "ui.micMeterThr": "Umbral",
    "ui.micMeterDb": "dB",
    "ui.micMeterDrag": "Arrastra para fijar el umbral",
    /* control integrado de entrada: un medidor vertical con el umbral que se
       arrastra (ahí se funden la sensibilidad y el umbral) y el nivel de voz
       en horizontal a su lado */
    "ui.levelTitle": "Entrada y umbral",
    "ui.levelHint": "Arrastra la perilla para fijar el umbral.",
    "ui.liveVoice": "Nivel de voz",
    "ui.thrLabel": "Umbral",
    "ui.sensFactor": "sensibilidad",
    "ui.sensIncluded": "ya incluida en el umbral",
    "ui.thrRange": "rango -80 a 0 dB",
    /* opción discreta de la comprobación automática, dentro de los ajustes */
    "ui.grpApp": "Aplicación",
    "ui.updAutoTitle": "Comprobar actualizaciones",
    "ui.updAutoHint": "Busca versiones nuevas al arrancar",
    /* espera antes de transcribir (silence_wait) */
    "ui.grpWait": "Espera antes de transcribir",
    "ui.grpWaitHint": "El silencio que aguanta antes de cerrar la frase",
    "ui.waitTitle": "Espera antes de dar por terminado lo que dices",
    "ui.waitHint": "El silencio que espera antes de cerrar la frase",
    "ui.waitAria": "Espera antes de transcribir, de 0,5 a 10 segundos, en pasos de 0,5",
    "ui.waitDragHint": "Arrastra para ajustar la espera: de 0,5 a 10 s, en pasos de 0,5 s",
    "ui.waitPresets": "Rápido",
    "ui.waitCustom": "Otra cantidad",
    "ui.waitApply": "Aplicar",
    "ui.waitPh": "otro… (s)",
    "ui.waitUnitS": "segundos",
    "ui.waitRange": "De 0,2 s a 600 s (10 minutos)",
    "ui.waitInvalid": "Escribe un valor entre 0,2 y 600 segundos.",
    "ui.waitSaved": "Guardado",
    /* reunión en vivo: pistas con nombre y leyenda de la fuente */
    "ui.lvSys": "Sistema",
    "ui.lvMic": "Micrófono",
    "ui.meetLiveNote": "Se graba en .wav y se transcribe en vivo mientras hablas.",
    "ui.meetLiveTr": "Transcripción en vivo",
    "ui.srcLegendOn": "Sonando ahora",
    "ui.srcLegendOff": "En silencio",
    "tag.tiny": "Rápido", "tag.base": "Ligero", "tag.small": "Preciso",
    "tag.medium": "Muy preciso", "tag.turbo": "GPU",
    "eng.auto": "Automático", "eng.vulkan": "GPU Vulkan",
    "eng.cuda": "GPU CUDA (NVIDIA)", "eng.cpu": "CPU",
    "ui.engineHere": "En uso",
    "ui.engineDesc": "Motor para la transcripción",
    "ui.engineOff": "No disponible en este equipo",
    "ui.engineOffMany": "No disponibles",
    /* Tarjeta gráfica: lista de dispositivos del motor en uso (Vulkan/CUDA). */
    "ui.gpuTitle": "Tarjeta gráfica",
    "ui.gpuHint": "Cuál usa el motor",
    "ui.gpuAuto": "Automático",
    "ui.gpuAutoHint": "Deja que el motor elija la mejor tarjeta",
    "ui.gpuInUse": "En uso",
    "ui.gpuApplying": "Aplicando… cargando motor",
    "ui.gpuAria": "Tarjeta gráfica que usa el motor",
    "ui.gpuIntegratedWarn": "Es la gráfica integrada: bastante más lenta. En audios largos puede perder precisión.",
    /* Motivo por motor NO compatible, en lenguaje de usuario y sin sonar a que se
       le niega algo: explica por qué esa opción no aplica en ESTE equipo. */
                    "ui.dictMultiHint": "Pega varias palabras separadas por coma o por salto de línea: se añaden todas de una vez.",
    "micDefault": "Entrada predeterminada",

    /* --- claves del rediseño: raíl, grupos y filas --- */
    "ui.sections": "Secciones de ajustes",
    "ui.secDictation": "Dictado",
    "ui.secDictationHint": "Lo que se usa cuando pulsas el atajo",
    "ui.grpRecognition": "Reconocimiento",
    "ui.grpRecognitionHint": "Se aplica al siguiente dictado, sin reiniciar",
    "ui.micHint": "El que se usa al dictar",
    "ui.sensHint": "Ganancia aplicada antes de transcribir",
    "ui.sensPeak": "Umbral de voz",
    "ui.sensPeakHint": "Sube si se cuela ruido de fondo; baja si te come palabras",
    "ui.dictPaneHint": "Va como prompt en cada dictado: mejora nombres propios y jerga",
    "ui.dictTerms": "Términos",
    "ui.dictHow": "Cómo se usa",
    "ui.dictPrompt": "Prompt de reconocimiento",
    "ui.dictPromptHint": "Se manda junto al audio en cada dictado",
    "ui.dictStored": "Se guarda en dicta_config.json",
    "ui.dictStoredHint": "Junto a la aplicación, legible y editable a mano",
    "ui.queue": "Cola",
    "ui.addAudio": "Añadir audio o vídeo",
    "ui.addAudioHint": "wav, flac, ogg; mp3 y m4a si hay ffmpeg",
    "ui.editorHint": "Se guarda solo en textos\\, nunca sale de tu equipo",
    "ui.shortcutsHint": "Se aplican en caliente, sin reiniciar",
    "ui.grpKeys": "Combinaciones",
    "ui.grpKeysHint": "Pulsa «Cambiar» y luego la combinación (1, 2 o 3 teclas)",
    "ui.appearance": "Apariencia",
    "ui.appearanceHint": "Se aplica a la vez al panel y a la isla",
    "ui.grpTheme": "Tema",
    "ui.grpThemeHint": "El mismo interruptor está en la cabecera",
    "ui.themeMode": "Claro u oscuro",
    "ui.themeModeHint": "El panel cambia al instante; la isla toma el mismo tema",
    "ui.grpIsland": "La isla",
    "ui.grpIslandHint": "Única ventana flotante de dicta",
    "ui.islandPos": "Posición",
    "ui.islandPosHint": "Arriba cuelga del borde; abajo es una pastilla flotante",
    "ui.islandPalette": "Paleta",
    "ui.islandPaletteHint": "Color de la onda y del cuerpo de la isla",
    "ui.islandClick": "Click-through",
    "ui.islandClickHint": "Taparla no impide pinchar en lo que hay debajo",
    "ui.islandOn": "Activado",
    "ui.posTop": "Arriba",
    "ui.posBottom": "Abajo",
    "pal.grafito": "Grafito", "pal.oceano": "Océano", "pal.ambar": "Ámbar",
    "pal.menta": "Menta", "pal.frambuesa": "Frambuesa", "pal.violeta": "Violeta",
    "ui.engineState": "Motor",
    "keyNames": { "alt": "Alt", "ctrl": "Ctrl", "shift": "Mayús", "cmd": "Win" },
    "__": {}
  },
  en: {
    "ui.title": "Settings",
    "ui.windowTitle": "dicta — Settings",
    "ui.choose": "Choose",
    "ui.subtitle": "Voice dictation, 100% local and private",
    "ui.statusReady": "Ready to listen",
    "ui.statusListening": "Listening…",
    "ui.statusTranscribing": "Transcribing…",
    "ui.statusLoading": "Loading model…",
    "ui.statusInserted": "Text inserted",
    "ui.statusTranscribed": "Transcription ready",
    "ui.statusCancelled": "Cancelled",
    "ui.language": "Language",
    "ui.languageHint": "Recognition and interface",
    "ui.engine": "Engine",
    "ui.engineUse": "In use",
    "ui.model": "Model",
    "ui.modelHint": "Accuracy versus speed",
    "ui.mic": "Microphone",
    "ui.sens": "Sensitivity",
    "ui.sensLow": "Clear voices only",
    "ui.sensHigh": "Picks up whispers",
    "ui.dict": "Dictionary",
    "ui.dictHint": "Terms and proper nouns",
    "ui.dictAdd": "Add",
    "ui.dictPlaceholder": "Type or paste words (commas or line breaks) and press Enter",
    "ui.dictEmpty": "No words yet. Add terms you dictate often.",
    "ui.theme": "Appearance",
    "ui.themeLight": "Light",
    "ui.themeDark": "Dark",
    "ui.shortcuts": "Keyboard shortcuts",
    "ui.dictateKey": "Dictation",
    "ui.dictateHint": "Starts and stops listening",
    "ui.cancelKey": "Cancel dictation",
    "ui.cancelHint": "Discards what is being dictated",
    "ui.changeKey": "Change",
    "ui.pressKeys": "Press one key, release, then press the next: they add up",
    "ui.hkCombo": "Combination so far",
    "ui.hkHint": "Up to 3 keys. Backspace removes the last one; “Start over” clears them all.",
    "ui.hkBack": "Remove last",
    "ui.hkClear": "Start over",
    "ui.hkSave": "Save",
    "ui.hkDup": "That key is already in the combination: each key counts once.",
    "ui.hkEmpty": "Press at least one key before saving.",
    "ui.hotkeyDupMod": "Repeated modifier:",
    "ui.hotkeyUnknown": "Unknown key:",
    "ui.cancel": "Cancel",
    "ui.hotkeyUnavailable": "That shortcut is already in use. Try another combination.",
    "ui.hotkeyInvalid": "Invalid shortcut. Combine a key with Alt, Ctrl, Shift, or Win.",
    "ui.hotkeyTooMany": "Too many keys: use at most three (for example Ctrl + Alt + S).",
    "ui.hotkeyNeedMain": "Missing the main key: join it with Alt, Ctrl, Shift, or Win.",
    "ui.hotkeySame": "That combination is already set.",
    "ui.hotkeyTimeout": "dicta did not respond. Please try again.",
    "ui.blockQuick": "Quick settings",
    "ui.blockWork": "Audio transcription",
    "ui.audios": "Audio",
    "ui.audiosHint": "Upload audio, video or anything else: it is saved and transcribed",
    "ui.pickFiles": "Choose files…",
    "ui.queueEmpty": "No audio in the queue.",
    "ui.addAudioPick": "Choose files…",
    "ui.addAudioPickHint": "A copy is kept and stays in your uploaded files",
    "ui.uploads": "Uploaded files",
    "ui.uploadsHint": "Saved in the audios folder",
    "ui.uploadsEmpty": "You haven't uploaded any file yet. Pick one above and it is kept here.",
    "ui.confirmRemove": "Remove?",
    "ui.stPending": "Waiting",
    "ui.stError": "Error",
    "ui.meeting": "Meeting",
    "ui.meetingHint": "System + microphone, recorded to .wav",
    "ui.startMeeting": "Start",
    "ui.meetTitle": "Start recording the meeting",
    "ui.meetDesc": "Captures system and microphone audio, saves the recording to .wav and transcribes live.",
    "ui.rec": "REC",
    "ui.pause": "Pause",
    "ui.resume": "Resume",
    "ui.meetSave": "Save and finish",
    "ui.meetCancel": "Cancel",
    "ui.meetOpen": "Open document",
    "ui.meetDl": "Download recording",
    "ui.meetSaved": "Meeting saved",
    "ui.meetCancelled": "Meeting cancelled",
    "ui.meetError": "Error:",
    "ui.meetLast": "Last turn",
    "ui.meetEmptyTr": "Transcribed text will show here once the meeting speaks.",
    "ui.saved": "Saved",
    "ui.docDelete": "Delete",
    "ui.docClose": "Close",
    "ui.dlAudio": "Download audio",
    "ui.dlDoc": "Download document",
    "ui.dlDocMd": "Download .md",
    "ui.dlDocTxt": "Download .txt",
    "ui.saveChoose": "Choose where to save…",
    "ui.saveDone": "Saved to",
    "ui.saveCancel": "Save canceled",
    "ui.saveFail": "Could not save",
    "ui.docRename": "Rename",
    "ui.remove": "Remove",
    "ui.ttChangeDictate": "Change dictation shortcut",
    "ui.ttChangeCancel": "Change cancel-dictation shortcut",
    "ui.ttChangePanel": "Change open-settings shortcut",
    "ui.meetingKey": "Record meeting",
    "ui.meetingKeyHint": "Starts and stops the meeting recording",
    "ui.meetCancelKey": "Cancel or stop the meeting",
    "ui.meetCancelKeyHint": "Stops the running meeting without saving it",
    "ui.ttChangeMeetCancel": "Change cancel-meeting shortcut",
    "ui.ttChangeMeeting": "Change record-meeting shortcut",
    "ui.confirmDelete": "Delete?",
    "ui.confirmCancel": "Cancel meeting?",
    "ui.docs": "Documents",
    "ui.docsHint": "Review, edit and download",
    "ui.docsEmpty": "No documents yet.",
    /* audios and documents: ONE single section (used to be two, read as two
       separate sessions). */
    "ui.audiosDocs": "Audio and documents",
    "ui.audiosDocsHint": "One place: add audio or video and every file stays here with its transcript",
    "ui.mediaEmpty": "Nothing yet. Add an audio or record a meeting and it will show up here with its transcript.",
    /* updates: the footer strip, next to the version. Checking is OFF by
       default (privacy): nothing leaves the machine until it is switched on.
       States: up to date / available / pending. */
    "ui.checkUpdates": "Check for new versions",
    "ui.updOn": "Checking on",
    "ui.updOff": "Checking off",
    "ui.updUpToDate": "Up to date",
    "ui.updAvailable": "Update available",
    "ui.updPending": "Update pending",
    "ui.updChecking": "Checking…",
    "ui.updating": "Updating…",
    "ui.updDone": "Updated",
    "ui.updFailed": "Could not check",
    "ui.updateNow": "Update",
    /* manual action: the link asks first, shows "Checking…" and then the real
       result; with a new version, "Install". */
    "ui.updSearchAria": "Check for an update",
    "ui.updSearchTitle": "Check for an update?",
    "ui.updSearchBody": "An anonymous query will be made to dicta's public list of versions. No data of yours is sent, and nothing is installed until you confirm.",
    "ui.updSearchGo": "Check",
    "ui.updSearching": "Checking…",
    "ui.updDownload": "Downloading",
    "ui.installNow": "Install {v}",
    "ui.updInstallAria": "Update to {v}",
    "ui.updDialogTitle": "Update Dicta?",
    "ui.updDialogBody": "Version {v} will be downloaded and applied. The download happens on your own computer: nothing is sent anywhere.",
    "ui.docTranscript": "Transcript",
    "ui.transcriptToggle": "Show or hide the transcript",
    "ui.docLoading": "Loading the transcript…",
    "ui.docLoadFail": "The transcript could not be loaded. Open it again.",
    "ui.docExists": "A file with that name already exists.",
    "ui.docRenameFail": "Could not rename.",
    "ui.save": "Save",
    "ui.quit": "Quit",
    "ui.quitTitle": "Turn off Dicta?",
    "ui.quitBody": "Dicta will close along with everything running: the meeting, dictation and any transcription in progress. Are you sure you want to turn it off?",
    "ui.quitConfirm": "Turn off Dicta",
    "ui.done": "Done",
    "ui.panelKey": "Open settings",
    "ui.panelHint": "Even if the tray icon is hidden",
    "ui.meetMic": "Record my microphone too",
    "ui.meetMicHint": "Mixes your voice with the system audio",
    "ui.meetMicOn": "Yes",
    "ui.meetMicOff": "No",
    "ui.meetSource": "Audio source",
    "ui.meetSourceHint": "Where the audio is captured from",
    "ui.srcAll": "Whole system",
    "ui.srcMissing": "Closed app",
    "ui.pvPlay": "Play",
    "ui.pvSeek": "Seek in the audio",
    "ui.pvNoWave": "No preview",
    "ui.pvLoad": "Loading waveform…",
    "ui.pvError": "Could not play",
    /* microphone test (single row: test, status, play and duration) */
    "ui.testTitle": "Testing the microphone…",
    "ui.testHint": "Speak normally while the test runs.",
    "ui.testStop": "Stop",
    "ui.testDone": "Microphone test",
    "ui.testAgain": "Retry",
    "ui.testOk": "The microphone sounds good.",
    "ui.testLow": "Very low level · move closer to the mic",
    "ui.testSilent": "No audio captured · move closer to the mic",
    /* microphone: single group (device, threshold + input test) */
    "ui.micGroupHint": "Device, threshold and input test",
    "ui.micDevice": "Input device",
    "ui.testRowTitle": "Test the input",
    "ui.testRowHint": "Speak normally to check the input.",
    "ui.testStart": "Test",
    /* real voice threshold (voice_threshold, 0..1) */
    "ui.sensPeakNow": "Real threshold",
    "ui.voiceThresholdHint": "Level your voice must exceed for dicta to hear it. Lower it if it misses you; raise it if it picks up background noise.",
    "ui.voiceThresholdLow": "Very sensitive: picks up whispers",
    "ui.voiceThresholdHigh": "Strong voice only",
    /* live input meter (rms / thr / voice) */
    "ui.micMeter": "Input level",
    "ui.micMeterHint": "Speak and watch where your voice falls: the mark is the voice threshold.",
    "ui.micNoVoice": "No voice",
    "ui.micVoice": "Voice detected",
    "ui.micMeterQuiet": "Silence",
    "ui.micMeterLoud": "Loud",
    "ui.micMeterThr": "Threshold",
    "ui.micMeterDb": "dB",
    "ui.micMeterDrag": "Drag to set the threshold",
    /* integrated input control: vertical meter with the draggable threshold
       (sensitivity and threshold merged here) and the voice level beside it */
    "ui.levelTitle": "Input and threshold",
    "ui.levelHint": "Drag the knob to set the threshold.",
    "ui.liveVoice": "Voice level",
    "ui.thrLabel": "Threshold",
    "ui.sensFactor": "sensitivity",
    "ui.sensIncluded": "already folded into the threshold",
    "ui.thrRange": "range -80 to 0 dB",
    /* discreet option for the automatic check, inside settings */
    "ui.grpApp": "Application",
    "ui.updAutoTitle": "Check for updates",
    "ui.updAutoHint": "Looks for new versions at startup",
    /* wait before transcribing (silence_wait) */
    "ui.grpWait": "Wait before transcribing",
    "ui.grpWaitHint": "The silence it holds before closing the sentence",
    "ui.waitTitle": "Wait before closing what you said",
    "ui.waitHint": "The silence it waits before closing the sentence",
    "ui.waitAria": "Wait before transcribing, from 0.5 to 10 seconds, in 0.5 steps",
    "ui.waitDragHint": "Drag to adjust the wait: from 0.5 to 10 s, in 0.5 s steps",
    "ui.waitPresets": "Quick",
    "ui.waitCustom": "Other amount",
    "ui.waitApply": "Apply",
    "ui.waitPh": "other… (s)",
    "ui.waitUnitS": "seconds",
    "ui.waitRange": "From 0.2 s to 600 s (10 minutes)",
    "ui.waitInvalid": "Enter a value between 0.2 and 600 seconds.",
    "ui.waitSaved": "Saved",
    /* live meeting: named tracks and source legend */
    "ui.lvSys": "System",
    "ui.lvMic": "Microphone",
    "ui.meetLiveNote": "Recording to .wav and transcribing live as you speak.",
    "ui.meetLiveTr": "Live transcript",
    "ui.srcLegendOn": "Playing now",
    "ui.srcLegendOff": "Silent",
    "tag.tiny": "Fast", "tag.base": "Light", "tag.small": "Accurate",
    "tag.medium": "Most accurate", "tag.turbo": "GPU",
    "eng.auto": "Automatic", "eng.vulkan": "GPU Vulkan",
    "eng.cuda": "GPU CUDA (NVIDIA)", "eng.cpu": "CPU",
    "ui.engineHere": "In use",
    "ui.engineDesc": "Engine for transcription",
    "ui.engineOff": "Not available on this computer",
    "ui.engineOffMany": "Not available on this computer",
    /* Graphics card: device list of the engine in use (Vulkan/CUDA). */
    "ui.gpuTitle": "Graphics card",
    "ui.gpuHint": "Which one the engine uses",
    "ui.gpuAuto": "Automatic",
    "ui.gpuAutoHint": "Let the engine pick the best card",
    "ui.gpuInUse": "In use",
    "ui.gpuApplying": "Applying… loading engine",
    "ui.gpuAria": "Graphics card the engine uses",
    "ui.gpuIntegratedWarn": "This is the integrated GPU: much slower. On long audio it may lose accuracy.",
                    "ui.dictMultiHint": "Paste several words separated by commas or line breaks: they are all added at once.",
    "micDefault": "Default input",

    /* --- redesign keys: rail, groups and rows --- */
    "ui.sections": "Settings sections",
    "ui.secDictation": "Dictation",
    "ui.secDictationHint": "What runs when you press the shortcut",
    "ui.grpRecognition": "Recognition",
    "ui.grpRecognitionHint": "Applies to the next dictation, no restart",
    "ui.micHint": "The one used while dictating",
    "ui.sensHint": "Gain applied before transcribing",
    "ui.sensPeak": "Voice threshold",
    "ui.sensPeakHint": "Raise it if background noise leaks in; lower it if words get cut",
    "ui.dictPaneHint": "Sent as a prompt on every dictation: helps with names and jargon",
    "ui.dictTerms": "Terms",
    "ui.dictHow": "How it works",
    "ui.dictPrompt": "Recognition prompt",
    "ui.dictPromptHint": "Sent along with the audio on every dictation",
    "ui.dictStored": "Stored in dicta_config.json",
    "ui.dictStoredHint": "Next to the app, readable and editable by hand",
    "ui.queue": "Queue",
    "ui.addAudio": "Add audio or video",
    "ui.addAudioHint": "wav, flac, ogg; mp3 and m4a with ffmpeg",
    "ui.editorHint": "Saved only under textos\\, it never leaves your machine",
    "ui.shortcutsHint": "Applied live, no restart",
    "ui.grpKeys": "Combinations",
    "ui.grpKeysHint": "Press «Change» and then the combination (1, 2 or 3 keys)",
    "ui.appearance": "Appearance",
    "ui.appearanceHint": "Applied to both the panel and the island",
    "ui.grpTheme": "Theme",
    "ui.grpThemeHint": "The same switch is in the header",
    "ui.themeMode": "Light or dark",
    "ui.themeModeHint": "The panel switches at once; the island takes the same theme",
    "ui.grpIsland": "The island",
    "ui.grpIslandHint": "dicta's only floating window",
    "ui.islandPos": "Position",
    "ui.islandPosHint": "Top hangs from the edge; bottom is a floating pill",
    "ui.islandPalette": "Palette",
    "ui.islandPaletteHint": "Colour of the island's wave and body",
    "ui.islandClick": "Click-through",
    "ui.islandClickHint": "Clicking through still reaches what lies beneath",
    "ui.islandOn": "On",
    "ui.posTop": "Top",
    "ui.posBottom": "Bottom",
    "pal.grafito": "Graphite", "pal.oceano": "Ocean", "pal.ambar": "Amber",
    "pal.menta": "Mint", "pal.frambuesa": "Raspberry", "pal.violeta": "Violet",
    "ui.engineState": "Engine",
    "keyNames": { "alt": "Alt", "ctrl": "Ctrl", "shift": "Shift", "cmd": "Win" }
  }
};

const MODELS = ["tiny", "base", "small", "medium", "turbo"];
/* Nombres COMPLETOS del modelo para el selector (la app usa los id cortos,
   pero el usuario ve «Whisper Large v3 Turbo», no «turbo»). */
const MODEL_LABEL = {
  "tiny": "Whisper Tiny",
  "base": "Whisper Base",
  "small": "Whisper Small",
  "medium": "Whisper Medium",
  "large-v3": "Whisper Large v3",
  "turbo": "Whisper Large v3 Turbo"
};
const MODEL_ID_BY_LABEL = Object.fromEntries(
  Object.entries(MODEL_LABEL).map(([id, label]) => [label.toLowerCase(), id]));
/* El backend puede publicar /state.models con nombres completos (strings u
   objetos {value,label}); si no llega, se usan los cinco de siempre. */
function modelList() {
  const out = [];
  const seen = new Set();
  const push = (v, l) => {
    v = String(v); if (!v || seen.has(v)) return;
    seen.add(v); out.push({ value: v, label: String(l || MODEL_LABEL[v] || v) });
  };
  const list = Array.isArray(state.models) ? state.models : null;
  if (list && list.length) {
    list.forEach(it => {
      if (it && typeof it === "object") push(it.key ?? it.value ?? it.id ?? it.name,
                                             it.label ?? it.name ?? it.key);
      else if (it != null) {
        const s = String(it);
        push(MODEL_LABEL[s] ? s : (MODEL_ID_BY_LABEL[s.toLowerCase()] || s),
             MODEL_LABEL[s] || s);
      }
    });
  }
  if (!out.length) MODELS.forEach(id => push(id, MODEL_LABEL[id]));
  if (state.model && !seen.has(String(state.model)))
    push(state.model, MODEL_LABEL[state.model] || String(state.model));
  return out;
}
/* Motores: se listan TODOS los que publica el backend (`engine_options`, con su
   disponibilidad) para que quien tenga una NVIDIA los vea aunque en ESTE equipo
   no estén. Los que no son compatibles salen DESHABILITADOS con el motivo en
   una línea; solo los `available` se pueden elegir. Si el backend todavía no
   publica la lista, se ofrecen los cinco posibles y se habilitan los conocidos. */
function engLabel(key, fallback) {
  const k = "eng." + key, s = t(k);
  return s === k ? (fallback || key) : s;
}
/* Motivo legible para un motor NO compatible en ESTE equipo. Se apoya en una
   línea honesta y concreta por motor (nada de tecnicismos ni de dar a entender
   que se le niega algo que le corresponde); si no hay una redactada, cae en la
   genérica. */
function engineList() {
  let items;
  if (Array.isArray(state.engine_options) && state.engine_options.length) {
    items = state.engine_options.map(o => ({
      key: o.key, label: o.label, available: o.available !== false,
      reason: o.reason || o.note || ""
    }));
  } else {
    const known = Array.isArray(state.engines) ? state.engines : [];
    items = ["auto", "vulkan", "cuda", "cpu"].map(k => ({
      key: k, available: !known.length || known.indexOf(k) >= 0, reason: ""
    }));
  }
  /* La app es solo para Windows: ROCm no aplica (va por Linux/WSL), así que se
     quita de la lista del todo —ni desplegable, ni fila de resumen, ni cuenta
     como no disponible—. Auto, Vulkan, CUDA y CPU se quedan (CUDA sigue visible
     aunque aquí esté deshabilitado). */
  return items.filter(o => o.key !== "rocm").map(o => {
    /* El backend publica el motivo de cada motor (`reason`) ya en lenguaje de
       usuario, tanto si se puede usar como si no; si no llega (backend viejo),
       se cae a la línea propia por motor. Un motor NO disponible lo lleva como
       motivo (`note`) y uno disponible como explicación (`info`), para que se
       entienda por qué Vulkan es lo óptimo aquí y no parezca que se le niega
       ROCm o CUDA al usuario. */
    const why = "";
    return {
      value: o.key,
      label: engLabel(o.key, o.label),
      disabled: !o.available,
      note: "",
      info: o.available ? why : ""
    };
  });
}
/* Solo español e inglés: la interfaz NO tiene traducción a los demás, así que
   el selector no debe ofrecerlos (este mismo `language` se pasa a whisper). */
const LANG_CODES = ["es", "en"];
const LANG_LABEL = {
  es: "Español", en: "English", pt: "Português",
  fr: "Français", de: "Deutsch", it: "Italiano"
};

/* La interfaz solo existe en español e inglés. */
const uiLocale = () => (state.language === "en" ? "en" : "es");
const t = (k) => (I18N[uiLocale()][k] ?? I18N.es[k] ?? k);

/* ---------------- iconos: un mapa, un constructor ----------------
   SVG en línea, sin fuente ni sprite: si un icono no está en el mapa, no existe.
   Rejilla 24×24 (área viva 2…22), trazo 1,8 y 2 por debajo de 18 px —la misma
   corrección óptica que dicta_icon.wave_mark—, uniones y extremos redondeados,
   sin relleno, currentColor. */
const ICONS = {
  /* identidad, audio y captura */
  wave:'<path d="M3 10v4M7.5 7.5v9M12 4.5v15M16.5 7.5v9M21 10v4"/>',
  mic:'<rect x="9" y="2.5" width="6" height="11" rx="3"/><path d="M5.5 11a6.5 6.5 0 0 0 13 0"/><path d="M12 17.5V21M8.5 21h7"/>',
  'mic-off':'<path d="M15 5.5v-1a3 3 0 0 0-6 0v7M9 12.4a3 3 0 0 0 4.7 2.1"/><path d="M5.5 11a6.5 6.5 0 0 0 9.9 5.6M12 17.5V21M8.5 21h7M3.5 3.5l17 17"/>',
  globe:'<circle cx="12" cy="12" r="9"/><path d="M3 12h18"/><path d="M12 3c2.6 2.5 3.9 5.5 3.9 9s-1.3 6.5-3.9 9c-2.6-2.5-3.9-5.5-3.9-9S9.4 5.5 12 3z"/>',
  chip:'<rect x="6.5" y="6.5" width="11" height="11" rx="2.5"/><path d="M10 10h4v4h-4z"/><path d="M10 2.5v4M14 2.5v4M10 17.5v4M14 17.5v4M2.5 10h4M2.5 14h4M17.5 10h4M17.5 14h4"/>',
  layers:'<path d="M12 2.8l8.4 4.3L12 11.4 3.6 7.1 12 2.8z"/><path d="M3.6 12.1L12 16.4l8.4-4.3"/><path d="M3.6 16.7L12 21l8.4-4.3"/>',
  gpu:'<rect x="4" y="5.6" width="16" height="12.8" rx="2.6"/><circle cx="9.8" cy="12" r="2.5"/><path d="M14.6 10.2h3M14.6 13.8h3"/>',
  gauge:'<path d="M3.5 17.5a9 9 0 1 1 17 0"/><path d="M12 17.5l4.2-6.4"/><circle cx="12" cy="17.5" r="1.1"/>',
  timer:'<circle cx="12" cy="13.5" r="7.5"/><path d="M12 13.5l3.2-2.2"/><path d="M9 2.5h6"/><path d="M12 2.5V6"/>',
  speaker:'<path d="M11 4.6L6.6 8.5H3.2v7h3.4L11 19.4z"/><path d="M14.8 9.7a3.4 3.4 0 0 1 0 4.6"/><path d="M17.6 6.9a7.4 7.4 0 0 1 0 10.2"/>',
  monitor:'<rect x="2.5" y="4" width="19" height="13" rx="2.5"/><path d="M8.5 21h7M12 17v4"/>',
  window:'<rect x="3" y="4.5" width="18" height="15" rx="2.5"/><path d="M3 8.8h18"/><path d="M6.2 6.7h.01M8.9 6.7h.01"/>',
  'file-audio':'<path d="M13 3.2H7.2a2 2 0 0 0-2 2v13.6a2 2 0 0 0 2 2h9.6a2 2 0 0 0 2-2V9z"/><path d="M13 3.2V9h5.8"/><path d="M10.6 17.4v-3.1l4-.9v3.1"/><circle cx="9.5" cy="17.6" r="1.2"/><circle cx="13.5" cy="16.7" r="1.2"/>',
  'file-text':'<path d="M13 3.2H7.2a2 2 0 0 0-2 2v13.6a2 2 0 0 0 2 2h9.6a2 2 0 0 0 2-2V9z"/><path d="M13 3.2V9h5.8"/><path d="M8.6 13h6.8M8.6 16.6h4.4"/>',
  /* datos */
  book:'<path d="M12 6.6C10.6 5.1 8.8 4.3 6.6 4.3H3.8V19h2.8c2.2 0 4 .8 5.4 2.2 1.4-1.4 3.2-2.2 5.4-2.2h2.8V4.3h-2.8c-2.2 0-4 .8-5.4 2.3z"/><path d="M12 6.6v14.6"/>',
  folder:'<path d="M3.5 6.6a2 2 0 0 1 2-2h3.1l2 2.5h7.9a2 2 0 0 1 2 2v8.4a2 2 0 0 1-2 2H5.5a2 2 0 0 1-2-2z"/>',
  keyboard:'<rect x="2.5" y="6" width="19" height="12" rx="2.5"/><path d="M6 9.6h.01M9.4 9.6h.01M12.8 9.6h.01M16.2 9.6h.01M6 13h.01M18 13h.01M9.4 13h5.2"/>',
  users:'<circle cx="9.2" cy="8" r="3.2"/><path d="M3.2 20a6 6 0 0 1 12 0"/><path d="M16.4 5.3a3.2 3.2 0 0 1 0 5.4"/><path d="M17.8 14.3a6 6 0 0 1 3 5.7"/>',
  /* acciones */
  play:'<path d="M7.5 5.2l11 6.8-11 6.8z"/>',
  pause:'<path d="M9.2 5.5v13M14.8 5.5v13"/>',
  stop:'<rect x="6.5" y="6.5" width="11" height="11" rx="2.5"/>',
  plus:'<path d="M12 5v14M5 12h14"/>',
  x:'<path d="M6 6l12 12M18 6L6 18"/>',
  check:'<path d="M4.8 12.6l4.8 4.8L19.2 6.8"/>',
  trash:'<path d="M4.5 6.5h15"/><path d="M9.5 6.5V4.8a1.3 1.3 0 0 1 1.3-1.3h2.4a1.3 1.3 0 0 1 1.3 1.3v1.7"/><path d="M6.5 6.5l1 12.1a1.6 1.6 0 0 0 1.6 1.4h5.8a1.6 1.6 0 0 0 1.6-1.4l1-12.1"/>',
  pencil:'<path d="M4.6 19.4h3.8L18.9 8.9a1.9 1.9 0 0 0 0-2.7l-1.1-1.1a1.9 1.9 0 0 0-2.7 0L4.6 15.6z"/><path d="M13.5 6.7l3.8 3.8"/>',
  download:'<path d="M12 3.5v11"/><path d="M7.6 10.4L12 14.8l4.4-4.4"/><path d="M4.5 19.5h15"/>',
  upload:'<path d="M12 15.5v-11"/><path d="M7.6 9L12 4.6 16.4 9"/><path d="M4.5 19.5h15"/>',
  copy:'<rect x="8.6" y="8.6" width="11.9" height="11.9" rx="2.5"/><path d="M15.4 5.6v-.8a1.8 1.8 0 0 0-1.8-1.8H5.4a1.8 1.8 0 0 0-1.8 1.8v8.2a1.8 1.8 0 0 0 1.8 1.8h.8"/>',
  refresh:'<path d="M20 12a8 8 0 1 1-2.5-5.8"/><path d="M20.3 4.4v4.3h-4.3"/>',
  search:'<circle cx="10.8" cy="10.8" r="6.3"/><path d="M15.4 15.4l4.1 4.1"/>',
  sliders:'<path d="M4 7.5h9M17.5 7.5H20M4 16.5h2.5M11 16.5h9"/><circle cx="15.2" cy="7.5" r="2.2"/><circle cx="8.7" cy="16.5" r="2.2"/>',
  power:'<path d="M12 3.5v8"/><path d="M7.3 6.5a7 7 0 1 0 9.4 0"/>',
  'external-link':'<path d="M13.5 4.5h6v6"/><path d="M19.5 4.5L11.2 12.8"/><path d="M17.5 14v4.2a1.8 1.8 0 0 1-1.8 1.8H5.3a1.8 1.8 0 0 1-1.8-1.8V7.8A1.8 1.8 0 0 1 5.3 6h4.2"/>',
  zap:'<path d="M13.4 3L5.6 13.4h5L10.6 21l7.8-10.4h-5z"/>',
  sparkle:'<path d="M12 3.4l1.7 4.9 4.9 1.7-4.9 1.7L12 16.6l-1.7-4.9L5.4 10l4.9-1.7z"/><path d="M18.4 16.4l.7 2 2 .7-2 .7-.7 2-.7-2-2-.7 2-.7z"/>',
  /* interfaz */
  sun:'<circle cx="12" cy="12" r="4.2"/><path d="M12 2.5v2M12 19.5v2M2.5 12h2M19.5 12h2M5.2 5.2l1.4 1.4M17.4 17.4l1.4 1.4M5.2 18.8l1.4-1.4M17.4 6.6l1.4-1.4"/>',
  moon:'<path d="M20.5 13.4A8.6 8.6 0 0 1 10.6 3.5a8.6 8.6 0 1 0 9.9 9.9z"/>',
  'chevron-down':'<path d="M6 9.5l6 6 6-6"/>',
  'chevron-right':'<path d="M9.5 6l6 6-6 6"/>',
  info:'<circle cx="12" cy="12" r="9"/><path d="M12 11.2V17M12 7.6h.01"/>',
  'alert-triangle':'<path d="M12 4.2L21 19.6H3z"/><path d="M12 10v4.2M12 17h.01"/>',
  'dots-h':'<circle cx="5.5" cy="12" r="1.3"/><circle cx="12" cy="12" r="1.3"/><circle cx="18.5" cy="12" r="1.3"/>',
  'dots-v':'<circle cx="12" cy="5.5" r="1.3"/><circle cx="12" cy="12" r="1.3"/><circle cx="12" cy="18.5" r="1.3"/>',
  settings:'<circle cx="12" cy="12" r="3.1"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.9l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-2.9 1.2 2 2 0 1 1-4 0 1.7 1.7 0 0 0-2.9-1.2l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1A1.7 1.7 0 0 0 2.1 14a2 2 0 1 1 0-4 1.7 1.7 0 0 0 1.2-2.9l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1A1.7 1.7 0 0 0 9 3.1a2 2 0 1 1 4 0 1.7 1.7 0 0 0 2.9 1.2l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1A1.7 1.7 0 0 0 20 10a2 2 0 1 1 0 4 1.7 1.7 0 0 0-1.2.9z"/>'
};
const USES_SW = 2;                    /* trazo por debajo de 18 px */

/* Construye el <svg> de un icono del mapa. Un solo constructor para todo: los
   [data-icon] que trae el HTML y los que crea el JS. */
function iconSVG(name, size, sw) {
  const body = ICONS[name];
  if (!body) return "";
  const s = +(size || 20);
  const w = sw != null ? +sw : (s <= 18 ? USES_SW : 1.8);
  return '<svg viewBox="0 0 24 24" width="' + s + '" height="' + s +
    '" fill="none" stroke="currentColor" stroke-width="' + w +
    '" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" ' +
    'focusable="false">' + body + '</svg>';
}

/* Construye el <svg> de cada [data-icon]. Idempotente: un icono ya pintado no
   se reconstruye (el panel se repinta cada 800 ms). */
function paintIcons(root = document) {
  root.querySelectorAll("[data-icon]").forEach(el => {
    if (el.dataset.ico === el.dataset.icon) return;
    const svg = iconSVG(el.dataset.icon, el.dataset.size, el.dataset.sw);
    if (!svg) return;
    el.innerHTML = svg;
    el.dataset.ico = el.dataset.icon;
  });
}

/* Cambia el icono de un contenedor [data-icon] (idempotente). Conserva el
   tamaño y el trazo que ya tuviera si no se pasan. */
function setIcon(el, name, size, sw) {
  if (!el || !ICONS[name] || el.dataset.icon === name) return;
  if (size != null) el.dataset.size = String(size);
  if (sw != null) el.dataset.sw = String(sw);
  el.dataset.icon = name;
  el.innerHTML = iconSVG(name, el.dataset.size, el.dataset.sw);
  el.dataset.ico = name;
}

/* Estado de confirmación de un botón destructivo (dos clics): conserva su icono
   y se rellena de rojo —el mismo cromo que la etiqueta «¿Eliminar?» del diseño—,
   mientras el nombre accesible pasa a la pregunta. Se reaplica en cada repintado
   porque el sondeo de /state vuelve a pintar el idioma. */
function confirmState(btn, on, idleKey, confirmKey) {
  if (!btn) return;
  const k = on ? confirmKey : idleKey;
  btn.setAttribute("aria-label", t(k));
  btn.title = t(k);
  btn.classList.toggle("confirm", on);
}

/* ---------------- raíl: una sección a la vista ---------------- */
function showSection(sec) {
  $$("#rail .rail-item").forEach(b => {
    b.setAttribute("aria-current", String(b.dataset.sec === sec));
  });
  $$("#pane > section").forEach(s => { s.hidden = s.dataset.sec !== sec; });
  const pane = $("#pane");
  if (pane) pane.scrollTop = 0;
}

/* ---------------- estado ---------------- */
let state = {
  model: "small", engine: "auto", engine_resolved: "cpu", engines: ["auto", "cpu"],
  models: null, voice_threshold: 0.3, silence_wait: 1.05,
  language: "es", sens: 1.2, theme: "dark", mic: null, st: "idle",
  island_pos: "top", island_palette: "grafito",
  mics: [], dictionary: [], hotkey: "alt+q", cancel_key: "alt+e", status: "",
  hotkeys: { meeting: "", meeting_cancel: "", meeting_stop: "" },
  sources: [], meeting_source: "all", meeting_mic: true,
  queue: [], meeting: {}, docs: [], mic_test: {}, uploads: null,
  icon_version: "1", engine_options: [], engine_note: "",
  /* tarjeta gráfica (dispositivos del motor): elección, resolución real y nota */
  gpu_device: "auto", gpu_device_resolved: "", gpu_device_note: "",
  /* actualizaciones: ACTIVADAS por defecto —la franja enseña su estado normal
     sin que haya que encender nada—; el backend puede apagarlas y su `enabled`
     manda. `update` lo publica el backend; si aún no lo hace, `null` y la UI no
     muestra nada. */
  check_updates: true, update: null
};

/* ---------------- backend ---------------- */
async function send(action, value) {
  try {
    const response = await fetch("/rpc", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action, value: value === undefined ? null : value })
    });
    return await response.json();
  } catch (_) { return { ok: false, error: "connection" }; }
}

function cmd(name) { return send(name, null); }

async function getState() {
  try {
    const r = await fetch("/state", { cache: "no-store" });
    return JSON.parse(await r.text());
  } catch (_) { return null; }
}

/* ---------------- tema e i18n ---------------- */
const WAVES = new Set();          // reproductores vivos: repintar con el tema

function paintTheme() {
  const dark = state.theme !== "light";
  const want = dark ? "dark" : "light";
  const flipped = document.documentElement.getAttribute("data-theme") !== want;
  if (flipped) document.documentElement.setAttribute("data-theme", want);
  vizSyncPalette();                     // los colores del tema, al día
  if (flipped) WAVES.forEach(p => paintWave(p));   // la onda toma el acento nuevo
  if (flipped) VIZ.forEach(L => { L.cv.width = 0; });  // las pistas, su color
  paintThemeColor();
  $$("#themeSwitch .ts-opt").forEach(b => {
    b.setAttribute("aria-checked", String((b.dataset.val === "dark") === dark));
  });
  $$("#themeSeg [data-theme-val]").forEach(b => {
    b.setAttribute("aria-pressed", String(b.dataset.themeVal === want));
  });
  moveThemeThumb();
}

/* La barra de título nativa de la ventana (la dibuja Chrome en modo aplicación)
   se pinta con color-scheme + el color de este meta, que se lee del token --bg
   del tema activo. Desde fuera no se puede: la ventana es de otro proceso. */
function paintThemeColor() {
  const meta = $('meta[name="theme-color"]');
  const bg = getComputedStyle(document.documentElement)
    .getPropertyValue("--bg").trim();
  if (meta && bg && meta.getAttribute("content") !== bg) meta.setAttribute("content", bg);
}

function moveThemeThumb() {
  const sw = $("#themeSwitch");
  const active = $("#themeSwitch .ts-opt[aria-checked='true']");
  const thumb = $(".ts-thumb", sw);
  if (!sw || !active || !thumb) return;
  const a = active.getBoundingClientRect(), s = sw.getBoundingClientRect();
  thumb.style.width = a.width + "px";
  thumb.style.height = a.height + "px";
  thumb.style.transform = `translateX(${a.left - s.left - 4}px)`;
}

function paintI18n() {
  document.documentElement.lang = uiLocale();
  $$("[data-i18n]").forEach(el => { el.textContent = t(el.dataset.i18n); });
  $$("[data-i18n-ph]").forEach(el => { el.placeholder = t(el.dataset.i18nPh); });
  $$("[data-i18n-aria]").forEach(el => { el.setAttribute("aria-label", t(el.dataset.i18nAria)); });
  $$("[data-i18n-title]").forEach(el => { el.title = t(el.dataset.i18nTitle); });
  document.title = t("ui.windowTitle");
}

/* Partes legibles de un atajo 'ctrl+alt+d'. */
function hotkeyPretty(spec) {
  const names = I18N[uiLocale()].keyNames || I18N.es.keyNames;
  return (spec || "").split("+").filter(Boolean)
    .map(k => (k.length === 1 || /^f\d+$/i.test(k)
      ? k.toUpperCase() : (names[k] || k)))
    .join(" + ");
}

/* ---------------- selects (un estilo para todos los parámetros) --------- */
function fillSelect(sel, options, current) {
  const sig = options.map(o => o.value + "\u0001" + o.label + "\u0001" + (o.on == null ? "" : String(o.on))
                              + "\u0001" + (o.disabled ? "1" : "0") + "\u0001" + (o.note || "")
                              + "\u0001" + (o.info || "") + "\u0001" + (o.title || "")
                              + "\u0001" + (o.aria || "") + "\u0001" + (o.badge || "")).join("|")
              + "|" + String(current);
  if (sel.dataset.sig !== sig) {
    sel.dataset.sig = sig;
    sel.innerHTML = "";
    options.forEach(o => {
      const opt = document.createElement("option");
      opt.value = o.value;
      opt.textContent = o.label;
      /* Estado opcional por opción (fuentes de audio: ¿está sonando?): viaja en
         un data- atributo para que el desplegable propio pinte su punto. */
      if (o.on != null) opt.dataset.on = o.on ? "1" : "0";
      /* Detalle por opción que NO cabe en la etiqueta visible (la tarjeta: su
         nombre COMPLETO con el aviso de la integrada). Va al title —y, el nombre
         completo, al aria— para que el desplegable propio lo conserve sin
         recargar la fila. */
      if (o.title) opt.title = o.title;
      if (o.aria) opt.setAttribute("aria-label", o.aria);
      /* Marca corta tras la etiqueta (p. ej. «En uso»): la pinta el desplegable. */
      if (o.badge) opt.dataset.badge = o.badge;
      /* Una opción no compatible con el equipo se VE, pero no se puede elegir:
         `disabled` lo respeta también el <select> nativo (respaldo sin JS) y el
         motivo viaja en data-note para que el desplegable propio lo enseñe. */
      if (o.disabled) opt.disabled = true;
      /* El motivo de una opción no elegible va a `data-note`; la explicación de
         una opción SÍ elegible (p. ej. por qué Vulkan es lo óptimo) a
         `data-info`. Los dos los pinta el desplegable propio. */
      const extra = o.disabled ? (o.note || "") : (o.info || "");
      if (extra) opt.dataset[o.disabled ? "note" : "info"] = extra;
      sel.appendChild(opt);
    });
  }
  const val = String(current);
  if (sel.value !== val && [...sel.options].some(o => o.value === val)) {
    sel.value = val;
  }
}
const selOpts = [
  ["#selLang", () => LANG_CODES.map(c => ({ value: c, label: LANG_LABEL[c] })), () => state.language],
  ["#selEngine", () => engineList(), () => state.engine],
  ["#selModel", () => modelList(), () => state.model],
];

function paintSelects() {
  selOpts.forEach(([sel, opts, cur]) => fillSelect($(sel), opts(), cur()));
  const resolved = engLabel(state.engine_resolved || "cpu");
  const hint = $("#engineHint");
  if (hint) {
    /* Descripción BREVE y útil de la fila. El autor mandó quitar el recuento
       «N no disponible(s) en este equipo» (sonaba a que le negaban un motor) y
       el motor EN USO ya se lee en el raíl (`#engineState`, abajo). */
    const desc = t("ui.engineDesc");
    hint.textContent = desc;
    hint.title = desc;
  }
  const rail = $("#engineState");
  if (rail) rail.textContent = resolved;
}

/* ---------------- tarjeta gráfica (dispositivos del motor) ----------------
   El motor publica, en cada `engine_options`, una lista `devices` con
   {index, name, desc} (VACÍA en Auto/CPU/CUDA/ROCm). Aquí se enseñan las
   tarjetas del motor EN USO (`engine_resolved`, que es el que de verdad tira) con
   su nombre TAL CUAL, MÁS «Automático» (value 'auto'). La elegida es
   `gpu_device`; la que está en uso de verdad es `gpu_device_resolved`. Al elegir
   se manda la acción `gpu_device` ({index:N} o 'auto'), que guarda y RELANZA el
   motor (tarda unos segundos): mientras tanto se enseña «aplicando / cargando
   motor» y las opciones quedan inertes, para que no parezca colgado. */
let gpuBusy = false, gpuPicked = null, gpuAt = 0;

function gpuEngineOpt() {
  const opts = Array.isArray(state.engine_options) ? state.engine_options : [];
  const key = state.engine_resolved || state.engine;
  return opts.find(o => o.key === key) || opts.find(o => o.key === state.engine) || null;
}
const gpuDevices = () => { const o = gpuEngineOpt(); return (o && Array.isArray(o.devices)) ? o.devices : []; };
/* La elección puede llegar como 'auto' o como {'index': N} (el backend guarda el
   dict en el config), así que se normaliza a clave de texto ('auto' o el índice). */
const gpuKey = g => (g && typeof g === "object")
  ? String(g.index != null ? g.index : "auto")
  : String(g == null || g === "" ? "auto" : g);
const gpuSelKey = () => gpuKey(state.gpu_device);
const gpuResKey = () => gpuKey(state.gpu_device_resolved);
/* La integrada se reconoce por `uma: 1` (memoria unificada). El aviso de que va
   más lenta va al title del dispositivo, en lenguaje claro. */
const gpuIsIntegrated = d => /(^|[^0-9])uma:\s*1/.test(String(d && d.desc || ""));
function gpuTip(d) {
  const desc = String(d && d.desc || "");
  return desc + (gpuIsIntegrated(d) ? "\n" + t("ui.gpuIntegratedWarn") : "");
}
/* El motor publica el nombre CON el controlador detrás, entre paréntesis
   («AMD Radeon RX 9070 (AMD proprietary driver)»). En la LISTA se enseña SOLO el
   nombre de la tarjeta: se corta el paréntesis FINAL del controlador, cualquier
   variante que mencione «driver» («(NVIDIA proprietary driver)», «(AMD
   proprietary driver)»…), sin tocar otros paréntesis del nombre (el «(TM)» de
   «AMD Radeon(TM) Graphics» se queda). El nombre COMPLETO se conserva en el
   title y en el aria de la fila, para no perder información. */
function gpuShortName(name) {
  const s = String(name == null ? "" : name).trim();
  const cut = s.replace(/\s*\([^()]*\bdriver\b[^()]*\)\s*$/i, "").trim();
  return cut || s;
}
/* Misma marca de «fila activa» que la lista del motor la pone el desplegable
   propio (`data-active` en ddMark): la tarjeta se pinta con ESTE MISMO
   componente, así que comparte realce, foco y teclado sin nada aparte. */

function paintGpu() {
  const row = $("#gpuRow"), sel = $("#selGpu");
  if (!row || !sel) return;
  const devs = gpuDevices();
  /* Sin dispositivos (Auto, CPU…): no se pinta NADA, ni una lista vacía. */
  if (!devs.length) {
    row.hidden = true;
    fillSelect(sel, [], "auto");            // deja el desplegable sin opciones
    const b0 = $("#gpuBusy"); if (b0) b0.hidden = true;
    const n0 = $("#gpuNote"); if (n0) n0.hidden = true;
    return;
  }
  row.hidden = false;

  const selKey = gpuSelKey(), resKey = gpuResKey();
  /* «Automático» PRIMERO (value 'auto'); después cada tarjeta del motor con su
     nombre YA LIMPIO. El nombre COMPLETO y el aviso de la integrada viajan en el
     title (y el completo, además, en el aria) para no perder información. */
  const items = [{ value: "auto", label: t("ui.gpuAuto"), title: t("ui.gpuAutoHint") }]
    .concat(devs.map(d => {
      const full = String(d.name || "");
      /* «en uso»: la tarjeta que el motor usa de verdad (gpu_device_resolved) y
         que no es la elegida; si coincide, el propio check ya lo dice. */
      const inuse = resKey && resKey !== "auto" && String(d.index) === resKey
                    && String(d.index) !== selKey;
      return {
        value: String(d.index),
        label: gpuShortName(d.name),                    // solo el nombre de la tarjeta
        title: (full ? full + "\n" : "") + gpuTip(d),   // nombre COMPLETO + aviso integrada
        aria: full || undefined,                        // el nombre COMPLETO sigue accesible
        badge: inuse ? t("ui.gpuInUse") : "",
        disabled: gpuBusy                               // mientras aplica: no elegible
      };
    }));
  fillSelect(sel, items, selKey);

  /* El estado «aplicando» se anuncia en el propio control (aria-busy) y se ve
     como aviso en la columna de texto; las opciones quedan inertes mientras. */
  const wrap = $("#gpuWrap");
  if (wrap) wrap.setAttribute("aria-busy", String(gpuBusy));
  const busy = $("#gpuBusy");
  if (busy) busy.hidden = !gpuBusy;
  const note = $("#gpuNote");
  if (note) {
    const n = String(state.gpu_device_note || "").trim();
    note.hidden = !n;
    note.textContent = n;
  }
}

/* Elige tarjeta: refleja la elección al instante, manda la acción y deja el
   estado «aplicando» mientras el motor recarga. */
async function gpuApply(value) {
  if (gpuBusy) return;
  gpuBusy = true; gpuPicked = value; gpuAt = Date.now();
  state.gpu_device = value;                            // optimista: se ve ya
  paintGpu();
  const res = await send("gpu_device", value === "auto" ? "auto" : { index: Number(value) });
  const s = await getState();
  if (s) merge(s);
  paintGpu();
  if (!res || res.ok === false) { gpuBusy = false; paintGpu(); }
}

/* Lo llama el sondeo: quita el «aplicando» cuando el config ya refleja la
   elección (con un mínimo para que se lea) o al cabo de un tope, para no parecer
   colgado si el motor tarda. */
function gpuTick() {
  if (!gpuBusy) return;
  const ok = gpuSelKey() === String(gpuPicked);
  const dt = Date.now() - gpuAt;
  if ((ok && dt > 2200) || dt > 15000) { gpuBusy = false; gpuPicked = null; paintGpu(); }
}

/* ---------------- isla: posición y paleta (sección Apariencia) ----------------
   Los controles no llevan id (los 72 de app.js no se tocan): se localizan por
   atributo. El <select> de paleta va dentro de un .select-wrap, así que lo
   mejora el desplegable propio sin cambiar nada de esto. */
const PALETTES = ["grafito", "oceano", "ambar", "menta", "frambuesa", "violeta"];

function paintAppearance() {
  $$("[data-island-pos-val]").forEach(b => {
    b.setAttribute("aria-pressed",
      String((state.island_pos || "top") === b.dataset.islandPosVal));
  });
  const sel = $("[data-island-palette]");
  if (sel) {
    fillSelect(sel, PALETTES.map(p => ({ value: p, label: t("pal." + p) })),
               state.island_palette || "grafito");
  }
}

/* ---------------- micrófono ---------------- */
function paintMic() {
  const sel = $("#selMic");
  const items = state.mics.length ? state.mics : [{ idx: "", name: t("micDefault") }];
  fillSelect(sel, items.map(it => ({
    value: String(it.idx), label: it.name })), state.mic === null ? "" : String(state.mic));
}

/* ---------------- entrada y umbral: UN SOLO control integrado ----------------
   Antes había dos deslizadores sueltos (sensibilidad y umbral) que movían lo
   mismo —el backend calcula `thr = voice_threshold / sensibilidad`— y ninguno
   explicaba cómo se graduaba. Ahora hay UN control:
     · medidor VERTICAL de barras con el nivel de entrada EN VIVO (/state.rms)
       sobre una escala en dB, y la MARCA del umbral ARRASTRABLE;
     · a su lado, el nivel de voz EN HORIZONTAL con su estado.
   Lo que se mueve (arrastrando o con las flechas) es el umbral del DETECTOR, o
   sea /state.thr; el ajuste que se manda al backend sigue siendo
   `voice_threshold`, calculado para que la marca caiga justo donde se suelta.
   La sensibilidad ya no es un mando aparte: es el factor interno del backend
   (thr = umbral / sensibilidad) y se enseña en la nota del control. */
const VTH_MAX = 1;
const vthOf = () => Math.min(VTH_MAX, Math.max(0, Number(state.voice_threshold) || 0));
/* El backend divide por max(0.2, sens): el mismo rasero aquí, para que la marca
   sea EXACTAMENTE el umbral que usa el detector. */
const sensOf = () => Math.max(0.2, Number(state.sens) || 1);

/* Escala del medidor: dBFS logarítmica de -80 a 0, como cualquier mesa. */
const METER_DB_FLOOR = -80, METER_DB_CEIL = 0;
const dbOf = r => { const v = Number(r); return v > 0 ? 20 * Math.log10(v) : -Infinity; };
const meterPct = db => Math.max(0, Math.min(100,
  ((Math.max(METER_DB_FLOOR, Math.min(METER_DB_CEIL, db)) - METER_DB_FLOOR) /
   (METER_DB_CEIL - METER_DB_FLOOR)) * 100));
const clamp01 = v => Math.min(1, Math.max(0, v));
const linOfDb = db => Math.pow(10, db / 20);
const dbOfLin = lin => dbOf(clamp01(lin));

/* Nivel EN VIVO del micrófono. Lo alimentan los dos caminos (el sondeo general
   por `merge()` y su propio sondeo rápido) y lo suaviza un bucle por fotograma:
   así el medidor se mueve en tiempo real sin saltar de un fotograma al otro. */
const micLive = { rms: 0, thr: 0, voice: false, has: false };
let micRaf = 0, micFrameAt = 0, micShownDb = NaN, micPaintKey = "";
let micThrOverride = null, micThrUntil = 0, micDragging = false;
let micEls = null;

function micRefs() {
  if (!micEls) {
    micEls = { box: $("#micMeter"), bars: $("#micMeterBars"), mark: $("#micMeterThr"),
               note: $("#micThrNote") };
  }
  return micEls;
}

const micTargetDb = () => dbOf(micLive.has ? micLive.rms : state.rms);
/* La marca es el umbral del DETECTOR (/state.thr). Mientras se arrastra —y unos
   instantes después, hasta que el backend lo confirma— manda la posición del
   ratón, para que la marca no dé un salto atrás. */
function micMarkDb() {
  const now = performance.now();
  if (micThrOverride !== null && (micDragging || now < micThrUntil)) return micThrOverride;
  const th = Number(micLive.has ? micLive.thr : state.thr);
  return dbOf((isFinite(th) && th > 0) ? th : vthOf() / sensOf());
}
/* Balística honesta: un cambio grande entra al instante; los pequeños se
   deslizan (ataque rápido, caída suave), que es lo que lo hace ver fluido. */
function micStepDb() {
  const tb = micTargetDb();
  if (!isFinite(tb)) { micShownDb = -Infinity; return micShownDb; }
  if (!isFinite(micShownDb)) { micShownDb = tb; return micShownDb; }
  const d = tb - micShownDb;
  if (Math.abs(d) > 6) micShownDb = tb;
  else micShownDb += d * (d > 0 ? 0.55 : 0.25);
  return micShownDb;
}

/* Recuadros del medidor HORIZONTAL y marcas de la escala: se construyen UNA vez. */
const H_SEG = 40;
/* Zona de color de cada recuadro según su dB (semáforo por nivel): verde hasta
   -20 dB, ámbar hasta -6 dB y rojo por encima (saturación). Se fija al construir
   para no tocarla cada fotograma. */
function segZone(pctOfSeg) {
  const db = METER_DB_FLOOR + (pctOfSeg / 100) * (METER_DB_CEIL - METER_DB_FLOOR);
  if (db <= -20) return "ok";
  if (db <= -6) return "warn";
  return "err";
}
function buildMeterBars() {
  const box = micRefs().bars;
  if (!box || box.dataset.built) return;
  box.dataset.built = "1";
  for (let i = 0; i < H_SEG; i++) {
    const b = document.createElement("i");
    b.dataset.on = "0";
    b.dataset.zone = segZone(((i + 0.5) / H_SEG) * 100);
    box.appendChild(b);
  }
}
const V_TICKS = [0, -20, -40, -60, -80];
function buildMeterScale() {
  const box = $("#micScale");
  if (box && !box.dataset.built) {
    box.dataset.built = "1";
    V_TICKS.forEach(v => {
      const tick = document.createElement("span");
      tick.className = "imtr-tick";
      tick.style.left = meterPct(v) + "%";
      tick.dataset.edge = v === 0 ? "end" : (v === METER_DB_FLOOR ? "start" : "");
      tick.textContent = v + " " + t("ui.micMeterDb");
      box.appendChild(tick);
    });
  }
}

/* Pinta el control: medidor HORIZONTAL (recuadros + perilla del umbral), la
   píldora de estado de voz y la nota con el valor real del umbral. */
function paintMicMeter() {
  const E = micRefs();
  if (!E.box || !E.bars || !E.mark) return;
  buildMeterBars();
  buildMeterScale();

  const db = micStepDb();
  const pct = meterPct(db);
  const thrPct = meterPct(micMarkDb());
  const voice = !!(micLive.has ? micLive.voice : state.voice);
  /* El bucle por fotograma llama aquí 25 veces por segundo: si nada ha cambiado
     (ni el nivel, ni la marca, ni la voz, ni el idioma) no se toca el DOM. */
  const key = pct.toFixed(2) + "|" + thrPct.toFixed(2) + "|" +
              (voice ? 1 : 0) + "|" + uiLocale();
  if (key === micPaintKey) return;
  micPaintKey = key;

  const lit = Math.round((pct / 100) * H_SEG);        // se llena de izquierda a derecha
  const kids = E.bars.children;
  for (let i = 0; i < kids.length; i++) {
    const on = i < lit ? "1" : "0";
    if (kids[i].dataset.on !== on) kids[i].dataset.on = on;
  }
  E.bars.dataset.lit = String(lit);

  E.mark.style.left = thrPct + "%";
  E.mark.title = t("ui.micMeterThr") + " \u00B7 " +
    (isFinite(micMarkDb()) ? Math.round(micMarkDb()) + " " + t("ui.micMeterDb") : "\u2014");
  E.box.setAttribute("aria-valuenow", String(Math.round(thrPct)));
  E.box.setAttribute("aria-valuetext", t("ui.micMeterThr") + " " +
    (isFinite(micMarkDb()) ? Math.round(micMarkDb()) + " " + t("ui.micMeterDb") : "\u2014"));

  /* la píldora «Con voz / Sin voz» se RETIRÓ (el medidor y su perilla ya dan
     ese feedback); queda solo el estado del medidor, sin texto a la vista */
  E.box.dataset.state = voice ? "voice" : "quiet";

  /* el valor del umbral, COMPACTO junto al medidor («-59 dB»); el detalle
     largo (sensibilidad ×N, rango) va al title/aria, no a la vista */
  if (E.note) {
    const th = micMarkDb();
    const val = isFinite(th) ? Math.round(th) + " " + t("ui.micMeterDb") : "\u2014";
    if (E.note.textContent !== val) E.note.textContent = val;
    const detail = t("ui.thrLabel") + ": " + val + " \u00B7 " +
      t("ui.sensFactor") + " \u00D7" + sensOf().toFixed(1).replace(".", ",") +
      " " + t("ui.sensIncluded") + " \u00B7 " + t("ui.thrRange");
    if (E.note.title !== detail) E.note.title = detail;
    E.note.setAttribute("aria-label", detail);
  }
}

/* ---- mover el umbral: arrastrando la marca sobre el medidor, o con flechas ---- */
function setThresholdDb(db) {
  const sens = sensOf();
  const lin = clamp01(linOfDb(db) * sens);            // el ajuste que come el backend
  micThrOverride = dbOfLin(lin / sens);               // dónde queda la marca (con topes)
  micThrUntil = performance.now() + 900;
  state.voice_threshold = Math.round(lin * 1e5) / 1e5;
  paintMicMeter();
  return state.voice_threshold;
}
function commitThreshold() {
  send("voice_threshold", state.voice_threshold);
}
function meterDragFrom(clientX) {
  const box = micRefs().box;
  if (!box) return;
  const r = box.getBoundingClientRect();
  const pct = Math.min(1, Math.max(0, (clientX - r.left) / r.width));
  setThresholdDb(METER_DB_FLOOR + pct * (METER_DB_CEIL - METER_DB_FLOOR));
}
function wireMicMeter() {
  const box = micRefs().box;
  if (!box) return;
  box.addEventListener("mousedown", e => {
    micDragging = true; meterDragFrom(e.clientX); e.preventDefault();
  });
  window.addEventListener("mousemove", e => { if (micDragging) meterDragFrom(e.clientX); });
  window.addEventListener("mouseup", () => {
    if (micDragging) { micDragging = false; commitThreshold(); }
  });
  box.addEventListener("keydown", e => {
    let db = micMarkDb();
    if (!isFinite(db)) db = METER_DB_FLOOR;
    const step = e.shiftKey ? 5 : 1;
    if (e.key === "ArrowUp" || e.key === "ArrowRight") db += step;
    else if (e.key === "ArrowDown" || e.key === "ArrowLeft") db -= step;
    else return;
    e.preventDefault();
    setThresholdDb(Math.min(METER_DB_CEIL, Math.max(METER_DB_FLOOR, db)));
    commitThreshold();
  });
}

/* Sondeo PROPIO del medidor: más rápido que el general (que repinta todo el
   panel), solo mientras la sección Dictado está a la vista. */
const micVisible = () => {
  const sec = document.querySelector('section[data-sec="dictado"]');
  return !!sec && !sec.hidden;
};
async function micPoll() {
  let wait = 700;
  if (micVisible()) {
    wait = document.hasFocus() ? 140 : 420;
    const s = await getState();
    if (s) {
      micLive.rms = Number(s.rms) || 0;
      micLive.thr = Number(s.thr) || 0;
      micLive.voice = !!s.voice;
      micLive.has = true;
    }
  }
  setTimeout(micPoll, wait);
}
/* Bucle por fotograma: mueve las barras y el nivel con el valor suavizado. */
function micFrame(ts) {
  micRaf = requestAnimationFrame(micFrame);
  if (ts - micFrameAt < 40) return;                   // ~25 fps: fluido y barato
  micFrameAt = ts;
  if (micVisible()) paintMicMeter();
}

/* ---------------- espera antes de transcribir (silence_wait) ----------------
   BARRA limpia (SIN marcas): un carril suave con el tramo recorrido encendido en
   acento y el tirador de la MISMA familia que la perilla del umbral (reutiliza
   `.imtr-thr i`: línea + agarre 8x20 con muescas, acento al pasar), centrado
   verticalmente en el carril. SIN NINGUN TEXTO: el valor vive SOLO en la píldora
   y el rango/paso en el title+aria. Va COMPACTA en el raíl de SU MISMA fila,
   junto al título y a la píldora. Se ajusta a ESCALONES de 0,5 s al arrastrar y
   con el teclado, y se guarda al SOLTAR (acción silence_wait; el backend admite
   0,2-600 s, así que 0,5-10 s entra de sobra). */
const WAIT_UI_MIN = 0.5, WAIT_UI_MAX = 10, WAIT_UI_STEP = 0.5, WAIT_PAD = 12;
const waitOf = () => Math.min(WAIT_UI_MAX, Math.max(WAIT_UI_MIN,
  Number(state.silence_wait) || 1.5));
/* ajuste a ESCALONES de 0,5 s: es como lo pide el autor (potenciómetro) */
const waitSnap = s => Math.round(Math.min(WAIT_UI_MAX,
  Math.max(WAIT_UI_MIN, Number(s) || WAIT_UI_MIN)) * 2) / 2;
/* SIEMPRE un decimal con coma («2,0 s»), que es como lo lee el autor. */
const waitPretty = s => (Math.round(Math.min(WAIT_UI_MAX,
  Math.max(WAIT_UI_MIN, Number(s) || 0)) * 10) / 10).toFixed(1).replace(".", ",") + " s";

let waitDragging = false, waitEls = null;
function waitRefs() {
  if (!waitEls) waitEls = { box: $("#waitSlider"), knob: $("#waitKnob"), fill: $("#waitFill") };
  return waitEls;
}
/* Posición de un valor sobre el eje (0..1), con la misma regla que el tirador. */
const waitPct = v => (Math.min(WAIT_UI_MAX, Math.max(WAIT_UI_MIN, v)) - WAIT_UI_MIN) /
  (WAIT_UI_MAX - WAIT_UI_MIN);

/* Tirador y TRAMO encendido sobre el MISMO eje (medio agarre a cada lado:
   WAIT_PAD). El ancho del tramo encendido SIGUE al tirador. SIN marcas. */
function paintWaitScale() {
  const E = waitRefs();
  if (!E.box) return;
  const r = E.box.getBoundingClientRect();
  const inner = Math.max(0, r.width - WAIT_PAD * 2);
  const x = WAIT_PAD + waitPct(waitOf()) * inner;
  if (E.knob) E.knob.style.left = x + "px";
  if (E.fill) E.fill.style.width = x + "px";
}

function paintWait() {
  const v = waitOf();
  const val = $("#waitValue");
  if (val) val.textContent = waitPretty(v);
  const E = waitRefs();
  if (E.box) {
    E.box.setAttribute("aria-valuenow", String(v));
    E.box.setAttribute("aria-valuetext", waitPretty(v));
  }
  paintWaitScale();
}

/* setWait: fija el valor (sin enviar) ajustado a escalones de 0,5 s. `commit`
   manda la acción al backend. */
function setWait(seconds, commit) {
  const v = waitSnap(seconds);
  if (!isFinite(v)) return;
  state.silence_wait = v;
  paintWait();
  if (commit) send("silence_wait", v);
}

function waitFromX(clientX) {
  const E = waitRefs();
  if (!E.box) return;
  const r = E.box.getBoundingClientRect();
  const inner = Math.max(1, r.width - WAIT_PAD * 2);
  const pct = Math.min(1, Math.max(0, (clientX - r.left - WAIT_PAD) / inner));
  setWait(WAIT_UI_MIN + pct * (WAIT_UI_MAX - WAIT_UI_MIN));
}

/* Arrastre (ratón) + teclado (flechas ±0,5 s; Mayús ±1 s; Inicio/Fin). */
function wireWaitSlider() {
  const E = waitRefs();
  if (!E.box) return;
  E.box.addEventListener("mousedown", e => {
    waitDragging = true; E.box.dataset.drag = "1";
    waitFromX(e.clientX); e.preventDefault();
  });
  window.addEventListener("mousemove", e => { if (waitDragging) waitFromX(e.clientX); });
  window.addEventListener("mouseup", () => {
    if (waitDragging) {
      waitDragging = false; delete E.box.dataset.drag;
      send("silence_wait", state.silence_wait);
    }
  });
  E.box.addEventListener("keydown", e => {
    let v = waitOf();
    const step = e.shiftKey ? 1 : WAIT_UI_STEP;
    if (e.key === "ArrowRight" || e.key === "ArrowUp") v += step;
    else if (e.key === "ArrowLeft" || e.key === "ArrowDown") v -= step;
    else if (e.key === "Home") v = WAIT_UI_MIN;
    else if (e.key === "End") v = WAIT_UI_MAX;
    else return;
    e.preventDefault();
    setWait(v, true);
  });
  window.addEventListener("resize", paintWaitScale);
}

/* ---------------- diccionario ---------------- */
function paintDict() {
  const box = $("#chips");
  const words = state.dictionary || [];
  box.innerHTML = "";
  words.forEach(w => {
    const c = document.createElement("span");
    c.className = "chip";
    const label = document.createElement("span");
    label.textContent = w;
    const x = document.createElement("button");
    x.type = "button";
    x.dataset.icon = "x"; x.dataset.size = "10"; x.dataset.sw = "2.4";
    const rm = t("ui.remove") + " " + w;
    x.setAttribute("aria-label", rm);
    x.title = rm;
    x.addEventListener("click", () => {
      state.dictionary = state.dictionary.filter(v => v !== w);
      paintDict();
      send("dictionary", state.dictionary);
    });
    c.append(label, x);
    box.appendChild(c);
  });
  paintIcons(box);                      // el aspa de cada chip
  $("#dictEmpty").hidden = words.length > 0;
  const cnt = $("#dictCount");
  if (cnt) { cnt.hidden = words.length === 0; cnt.textContent = String(words.length); }
}

function addWord() {
  const inp = $("#dictInput");
  const raw = inp.value.trim();
  if (!raw) return;
  const words = raw.split(/[,\n]+/).map(s => s.trim()).filter(Boolean);
  let changed = false;
  words.forEach(w => {
    if (!state.dictionary.some(v => v.toLowerCase() === w.toLowerCase())) {
      state.dictionary.push(w);
      changed = true;
    }
  });
  inp.value = "";
  if (changed) {
    paintDict();
    send("dictionary", state.dictionary);
  }
  inp.focus();
}

/* ---------------- pistas vivas: bandas de frecuencia REALES ----------------
   Mientras captura, el backend publica la energía por bandas —/state.levels =
   {sys:[12], mic:[12]}, de grave a agudo, 0..1—. Ese dato mueve TODA pista de
   audio del panel: las dos de la reunión (Sistema y Micrófono) y el medidor de
   la prueba de entrada. Nunca una raya plana: si no hay captura, la pista queda
   limpia, sin dibujo.

   Dos cosas hacen que el movimiento sea fluido de verdad:
     · El sondeo solo trae el OBJETIVO. El dibujo va por requestAnimationFrame y
       cada banda persigue su valor frame a frame (ataque rápido, ~45 ms; caída
       lenta, ~260 ms): no salta de un fotograma al siguiente.
     · Si el sondeo se para, el objetivo CADUCA solo (700 ms) y las barras caen a
       cero en lugar de quedarse congeladas.

   Canvas 2D y nada más: sin librerías. */
const BANDS = 12;                  // bandas que publica el backend (grave→agudo)
const COLS = 48;                   // columnas dibujadas: interpolan esas bandas
const VIZ = new Map();             // contenedor de la pista -> estado de dibujo
const vizPalette = { accent: "#0066CC", ok: "#2E7D32", warn: "#B25000" };
let vizRaf = 0, vizPrev = 0;
let liveLevels = null;             // última energía por bandas {sys, mic}
let liveScalars = { sys: 0, mic: 0, probe: 0, probePeak: 0 };    // RMS de respaldo

const vizNum = v => Math.min(1, Math.max(0, Number(v) || 0));

/* La paleta se lee de los tokens del tema (y se refresca al cambiar de tema):
   un getComputedStyle por frame costaría fotogramas. */
function vizReadPalette() {
  const cs = getComputedStyle(document.documentElement);
  ["accent", "ok", "warn"].forEach(k => {
    const v = (cs.getPropertyValue("--" + k) || "").trim();
    if (v) vizPalette[k] = v;
  });
}

let vizThemeSeen = "";
function vizSyncPalette() {
  const th = document.documentElement.getAttribute("data-theme") || "light";
  if (th !== vizThemeSeen) { vizThemeSeen = th; vizReadPalette(); }
}

/* Estado de una pista. El canvas ya está en el HTML; si faltara, se crea el
   primero del contenedor (ocupa el alto libre; debajo van nivel y pico). */
function laneOf(host) {
  if (!host) return null;
  let L = VIZ.get(host);
  if (!L) {
    let cv = host.querySelector(":scope > .viz-canvas");
    if (!cv) {
      cv = document.createElement("canvas");
      cv.className = "viz-canvas";
      host.insertBefore(cv, host.firstChild);
    }
    L = { cv, ctx: cv.getContext("2d"), color: "accent",
          level: host.querySelector("i"), peak: host.querySelector(".probe-peak"),
          cur: new Float64Array(BANDS), pk: new Float64Array(BANDS),
          tgt: new Float64Array(BANDS), lvl: 0, pkLvl: 0, on: false, seen: 0 };
    VIZ.set(host, L);
  }
  return L;
}

/* Objetivo de una pista. Con bandas del backend se dibujan TAL CUAL; si el
   backend todavía no las publica, la energía que sí llega (el RMS) reparte
   altura entre las bandas con la caída natural del espectro, así la pista se
   mueve ya y nunca se queda plana. `on` falso = esa pista no captura: a cero. */
function laneTarget(host, bands, rms, on, color) {
  const L = laneOf(host);
  if (!L) return;
  if (color) L.color = color;
  const v = vizNum(rms);
  for (let i = 0; i < BANDS; i++) {
    let t = 0;
    if (on) {
      t = (Array.isArray(bands) && bands.length)
        ? vizNum(bands[Math.floor((i * bands.length) / BANDS)])
        : v * (1 - (0.5 * i) / (BANDS - 1));
    }
    L.tgt[i] = t;
  }
  L.on = !!on;
  L.seen = performance.now();
  vizStart();
}

function vizStart() {
  if (!vizRaf) { vizPrev = 0; vizRaf = requestAnimationFrame(vizFrame); }
}

/* Un fotograma: persigue los objetivos, dibuja las barras y mueve el nivel y su
   pico. El bucle se para solo cuando no queda nada que enseñar. */
function vizFrame(ts) {
  vizRaf = 0;
  const dt = Math.min(64, Math.max(8, ts - vizPrev || 16));
  vizPrev = ts;
  const now = performance.now();
  const kA = 1 - Math.exp(-dt / 45);         // ataque: sube de inmediato
  const kR = 1 - Math.exp(-dt / 260);        // caída: se desvanece sin tirones
  const dpr = Math.min(2, window.devicePixelRatio || 1);
  let alive = false;

  VIZ.forEach(L => {
    if (L.on && now - L.seen > 700) {        // se paró el sondeo: objetivo caducado
      L.on = false;
      L.tgt.fill(0);
    }
    let sum = 0;
    for (let i = 0; i < BANDS; i++) {
      L.cur[i] += (L.tgt[i] - L.cur[i]) * (L.tgt[i] > L.cur[i] ? kA : kR);
      if (L.cur[i] > L.pk[i]) L.pk[i] = L.cur[i];
      else L.pk[i] = Math.max(0, L.pk[i] - dt * 0.0006);
      sum += L.cur[i];
    }
    sum /= BANDS;
    L.lvl += (sum - L.lvl) * (sum > L.lvl ? kA : kR);
    if (L.lvl > L.pkLvl) L.pkLvl = L.lvl;
    else L.pkLvl = Math.max(0, L.pkLvl - dt * 0.00025);

    const w = L.cv.clientWidth, h = L.cv.clientHeight;
    if (w > 0 && h > 0 && L.ctx) {
      if (L.cv.width !== Math.round(w * dpr)) L.cv.width = Math.round(w * dpr);
      if (L.cv.height !== Math.round(h * dpr)) L.cv.height = Math.round(h * dpr);
      const ctx = L.ctx;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.clearRect(0, 0, w, h);
      ctx.fillStyle = vizPalette[L.color] || vizPalette.accent;
      /* Las 12 bandas del backend se reparten en COLS columnas estrechas
         interpolando entre bandas vecinas: así la pista se lee como un espectro
         que SUBE Y BAJA con el habla, no como unos bloques anchos. Una columna
         sin energía no se dibuja (nada de raya de fondo) y las flojas salen
         tenues: el alfa sube con el valor. */
      const gap = 2, cw = Math.max(1, (w - gap * (COLS - 1)) / COLS);
      for (let c = 0; c < COLS; c++) {
        const f = (c / (COLS - 1)) * (BANDS - 1);
        const i0 = Math.floor(f), i1 = Math.min(BANDS - 1, i0 + 1), k = f - i0;
        const v = L.cur[i0] * (1 - k) + L.cur[i1] * k;
        if (v < 0.012) continue;
        const bh = Math.max(2, Math.min(h, v * (h - 2)));
        ctx.globalAlpha = 0.25 + 0.75 * Math.min(1, v * 2.5);
        ctx.fillRect(c * (cw + gap), h - bh, cw, bh);
      }
      ctx.globalAlpha = 1;
    }
    if (L.level) L.level.style.transform = "scaleX(" + L.lvl.toFixed(3) + ")";
    if (L.peak) L.peak.style.left = (L.pkLvl * 100).toFixed(1) + "%";
    if (L.on || sum > 0.004 || L.lvl > 0.004) alive = true;
  });

  if (alive) vizRaf = requestAnimationFrame(vizFrame);
  else VIZ.forEach(vizRest);
}

/* En reposo la pista no dibuja NADA: mejor vacía que con una raya fingiendo una
   medida. Se limpia el lienzo y el nivel y el pico vuelven a cero. */
function vizRest(L) {
  for (let i = 0; i < BANDS; i++) { L.cur[i] = 0; L.pk[i] = 0; }
  L.lvl = 0; L.pkLvl = 0;
  if (L.level) L.level.style.transform = "scaleX(0)";
  if (L.peak) L.peak.style.left = "0%";
  if (L.ctx && L.cv.width > 0 && L.cv.clientHeight > 0) {
    L.ctx.setTransform(1, 0, 0, 1, 0, 0);
    L.ctx.clearRect(0, 0, L.cv.width, L.cv.height);
  }
}

/* Bandas de una pista: solo valen si el backend está capturando de verdad
   (levels.active). Fuera de una grabación las manda a cero y el aviso
   `*_silent` a True, así que ahí NO se pintan: se usa el respaldo escalar. */
function bandsOf(key) {
  const L = liveLevels;
  if (!L || !L.active || !Array.isArray(L[key]) || !L[key].length) return null;
  return L[key];
}

/* Objetivos de las pistas vivas. La de la reunión se apaga con la pausa y con
   el micrófono fuera de la mezcla; la de la prueba, mientras no haya prueba.
   El punto de la etiqueta se apaga cuando esa pista no capta sonido (el
   `*_silent` real del backend): feedback de un vistazo. */
function paintLevels() {
  const m = state.meeting || {};
  const rec = !!m.active && !m.paused;
  const L = liveLevels || {};
  const sysBands = bandsOf("sys"), micBands = bandsOf("mic");
  const sysSound = bandsLive(sysBands), micSound = bandsLive(micBands);
  const micOn = rec && state.meeting_mic !== false;
  /* Cada pista es el MISMO medidor del dictado (`.hmeter`): la barra se llena
     con la energía real de /state.levels y pasa a verde al captar voz. */
  meetMeter($("#lvSys"), sysBands, liveScalars.sys, rec, rec && sysSound);
  meetMeter($("#lvMic"), micBands, liveScalars.mic, micOn, micOn && micSound);
  /* El punto se apaga solo cuando esa pista no capta NADA: el aviso del backend
     Y las bandas a cero. (Con el flag a secas parpadeaba entre palabras.) */
  quietDot($("#lvSys"), rec && !sysSound && !!L.sys_silent);
  quietDot($("#lvMic"), rec && state.meeting_mic !== false &&
             !micSound && !!L.mic_silent);
}

/* Medidor de una pista de la reunión: EL MISMO componente del dictado
   (`.hmeter` con su `.hmeter-fill`). La barra se llena con la energía real de
   la pista —el pico de sus bandas de /state.levels, o su RMS de respaldo— y
   pasa a verde (`data-state="voice"`) cuando esa pista capta voz, igual que el
   medidor de voz del dictado. `on` falso = no captura: barra a cero. */
function meetMeter(box, bands, scalar, on, voice) {
  if (!box) return;
  const fill = box.querySelector(".hmeter-fill");
  if (!fill) return;
  let v = 0;
  if (on) {
    if (Array.isArray(bands) && bands.length) {
      for (let i = 0; i < bands.length; i++) v = Math.max(v, vizNum(bands[i]));
    } else {
      v = vizNum(scalar);
    }
  }
  const pct = Math.round(v * 100);
  if (fill.dataset.pct !== String(pct)) {
    fill.dataset.pct = String(pct);
    fill.style.width = pct + "%";
  }
  const st = voice ? "voice" : "quiet";
  if (box.dataset.state !== st) box.dataset.state = st;
}

/* ¿Hay energía de verdad en estas bandas? (por encima del ruido de fondo) */
function bandsLive(bands) {
  if (!Array.isArray(bands) || !bands.length) return false;
  let sum = 0;
  for (let i = 0; i < bands.length; i++) sum += Number(bands[i]) || 0;
  return sum > 0.02;
}

function quietDot(host, quiet) {
  const dot = host && host.parentElement &&
    host.parentElement.querySelector(".lv-dot");
  if (dot) dot.classList.toggle("quiet", !!quiet);
}

/* ---------------- vista previa de audio (onda propia, sin librerías) ---------
   La envolvente se pide UNA vez por fichero y se cachea por nombre: el panel
   repinta cada 800 ms y no debe volver a decodificar ni a repintar el canvas.
   Suena un solo fichero a la vez en un <audio> compartido (oculto); cada fila
   tiene su propio control (play, onda, tiempo) y su propia barra de salto. */
const peaksCache = new Map();      // nombre -> Promise<{dur, peaks}|null>
const audioUrls = new Map();       // nombre -> objectURL con MIME correcto
const AUDIO_MIME = {
  wav: "audio/wav", flac: "audio/flac", ogg: "audio/ogg", oga: "audio/ogg",
  opus: "audio/ogg", mp3: "audio/mpeg", m4a: "audio/mp4", aac: "audio/aac",
  webm: "audio/webm"
};
const ICON_PLAY = '<svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor" aria-hidden="true"><path d="M8.5 5.3v13.4L19 12z"/></svg>';
const ICON_PAUSE = '<svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor" aria-hidden="true"><rect x="7" y="5.4" width="3.4" height="13.2" rx="1.3"/><rect x="13.6" y="5.4" width="3.4" height="13.2" rx="1.3"/></svg>';

const baseName = p => String(p || "").split(/[\\/]/).pop();
const extOf = n => (String(n).match(/\.([a-z0-9]+)$/i) || [, ""])[1].toLowerCase();
/* Extensiones que el panel reconoce DE VERDAD. Quitar la extension es quitar
   UNA extension real: un nombre como «¿Cuanto costaria correr Claude Opus 5.5
   en Local» NO termina en extension (lo que hay tras el ultimo punto es
   «.5 en Local»), y cortarlo por ahi partia el nombre por la mitad: la subida y
   su documento dejaban de emparejarse y salian DOS tarjetas del mismo audio. */
const FILE_EXT = /\.(md|markdown|txt|wav|wave|mp3|m4a|m4b|aac|flac|ogg|oga|opus|wma|aif|aiff|amr|caf|mp4|m4v|mkv|mov|webm|avi|wmv|mpg|mpeg|3gp|bin)$/i;
const stripExt = n => String(n || "").replace(FILE_EXT, "");
/* ¿la duración pasa de una hora? -> etiqueta con horas (misma en ambos lados) */
const hoursOf = d => (Number(d) || 0) >= 3600;

function fetchPeaks(name) {
  if (!peaksCache.has(name)) {
    const pr = fetch(`/peaks?name=${encodeURIComponent(name)}`, { cache: "no-store" })
      .then(r => (r.ok ? r.json() : null))
      .then(d => (d && Array.isArray(d.peaks) && d.peaks.length ? d : null))
      .catch(() => null);
    /* Un fallo NO se recuerda: la grabación de la reunión se normaliza al
       cerrarse y /peaks puede no poder leerla durante ese instante; cachear el
       fallo dejaba la onda en la guía discontinua para el resto de la sesión. */
    pr.then(d => { if (!d && peaksCache.get(name) === pr) peaksCache.delete(name); });
    peaksCache.set(name, pr);
  }
  return peaksCache.get(name);
}

/* El endpoint sirve el audio con su TIPO REAL y acepta rangos, así que se usa
   la URL DIRECTA: el navegador empieza a sonar con el primer trozo y puede
   saltar sin bajarse el fichero entero. Bajar TODO el audio a un blob (22 MB en
   memoria) antes de sonar era lo que se notaba como «se traba» en audios largos.
   Solo si el tipo no es reproducible por URL se corrige con un blob. */
async function audioUrl(name) {
  const hit = audioUrls.get(name);
  if (hit) return hit;
  if (AUDIO_MIME[extOf(name)]) {
    const direct = `/audio?name=${encodeURIComponent(name)}`;
    audioUrls.set(name, direct);
    return direct;
  }
  const r = await fetch(`/audio?name=${encodeURIComponent(name)}`, { cache: "no-store" });
  if (!r.ok) throw new Error("http " + r.status);
  const url = URL.createObjectURL(new Blob([await r.arrayBuffer()],
    { type: AUDIO_MIME[extOf(name)] || "audio/wav" }));
  if (audioUrls.size >= 6) {                    // memoria acotada
    const [old] = audioUrls.keys();
    if (old !== name) { URL.revokeObjectURL(audioUrls.get(old)); audioUrls.delete(old); }
  }
  audioUrls.set(name, url);
  return url;
}

const player = $("#previewAudio");
let liveP = null;                               // la fila que suena ahora

function stateOf(p, s) { p.state = s; labelPreview(p); }

player.addEventListener("play", () => { if (liveP) stateOf(liveP, "playing"); });
player.addEventListener("pause", () => {
  if (liveP) stateOf(liveP, player.ended ? "idle" : "paused");
});
player.addEventListener("loadedmetadata", () => {
  if (liveP && isFinite(player.duration) && player.duration > 0) liveP.dur = player.duration;
  if (liveP) paintPreview(liveP);
});
player.addEventListener("timeupdate", () => {
  if (!liveP) return;
  liveP.t = player.currentTime;
  labelPreview(liveP);
  paintWave(liveP);
});
player.addEventListener("ended", () => {
  if (!liveP) return;
  liveP.t = 0;
  stateOf(liveP, "idle");
  paintWave(liveP);
});
player.addEventListener("error", () => { if (liveP) stateOf(liveP, "error"); });

function paintWave(p) {
  const track = p.track, cv = p.canvas;
  if (!track || !cv) return;            // reproductor sin onda (prueba de micro)
  const w = Math.max(1, Math.round(track.clientWidth));
  const h = Math.max(1, Math.round(track.clientHeight));
  const dpr = Math.min(2, window.devicePixelRatio || 1);
  if (cv.width !== Math.round(w * dpr)) cv.width = Math.round(w * dpr);
  if (cv.height !== Math.round(h * dpr)) cv.height = Math.round(h * dpr);
  const ctx = cv.getContext("2d");
  if (!ctx || w < 2) return;
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, w, h);
  const accent = vizPalette.accent || (getComputedStyle(document.documentElement)
    .getPropertyValue("--accent") || "").trim() || "#5B9DFF";
  ctx.fillStyle = accent;
  const mid = h / 2, maxH = Math.max(2, h - 8);
  const peaks = p.peaks || [];
  /* NADA de rayas planas: sin envolvente —o con la captura muda (silent)— la
     pista no dibuja nada; queda su guía discontinua (.pv-track.empty) y el
     texto de al lado explica qué pasa. */
  const empty = !peaks.length || !!p.silent;
  if (track.classList.contains("empty") !== empty) track.classList.toggle("empty", empty);
  if (empty) return;
  const played = p.dur > 0 ? Math.min(1, Math.max(0, p.t / p.dur)) : 0;
  const cut = played * w;
  const cols = Math.max(1, Math.floor(w));
  const bw = w / cols;
  for (let x = 0; x < cols; x++) {
    const a = Math.floor((x * peaks.length) / cols);
    const b = Math.max(a + 1, Math.floor(((x + 1) * peaks.length) / cols));
    let v = 0;
    for (let i = a; i < b && i < peaks.length; i++) if (peaks[i] > v) v = peaks[i];
    const bh = Math.max(2, v * maxH);
    ctx.globalAlpha = (x + 0.5) * bw <= cut ? 1 : 0.3;   // lo ya escuchado, a plena
    ctx.fillRect(x * bw, mid - bh / 2, bw, bh);
  }
  ctx.globalAlpha = 1;
}

function labelPreview(p) {
  const playing = p.state === "playing";
  const lbl = p.state === "error" ? t("ui.pvError")
    : playing ? t("ui.pause") : t("ui.pvPlay");
  const txt = `${fmtTime(p.t, hoursOf(p.dur))} / ${fmtTime(p.dur, hoursOf(p.dur))}`;
  const sig = `${p.state}|${lbl}|${txt}|${p.name}`;
  if (p.sig === sig) return;                 // nada cambió: no tocar el DOM
  p.sig = sig;
  p.btn.innerHTML = playing ? ICON_PAUSE : ICON_PLAY;
  p.btn.dataset.state = p.state;
  p.btn.setAttribute("aria-pressed", String(playing));
  p.btn.setAttribute("aria-label", lbl);
  p.btn.title = lbl;
  p.time.textContent = txt;
  if (p.track) {
    p.track.setAttribute("aria-label", `${t("ui.pvSeek")} — ${p.name}`);
    p.track.setAttribute("aria-valuenow", String(p.dur > 0 ? Math.round((p.t / p.dur) * 100) : 0));
    p.track.setAttribute("aria-valuetext", txt);
  }
}

function paintPreview(p) { labelPreview(p); paintWave(p); }

function seekTo(p, ratio) {
  if (p.broken || !p.dur) return;
  p.t = Math.min(p.dur, Math.max(0, ratio * p.dur));
  if (liveP === p && player.dataset.name === p.name) {
    try { player.currentTime = p.t; } catch (_) {}
  }
  paintPreview(p);
}

function stopPreview(p) {
  if (liveP === p) { liveP = null; try { player.pause(); } catch (_) {} }
  p.state = "idle"; p.t = 0;
  paintPreview(p);
}

function disposePreview(p) {
  if (p.ro) p.ro.disconnect();
  clearTimeout(p.slow);
  clearTimeout(p.retry);
  WAVES.delete(p);
  if (liveP === p) { liveP = null; try { player.pause(); } catch (_) {} }
  p.el.remove();
}

async function togglePreview(p) {
  if (p.state === "playing") { player.pause(); return; }
  if (liveP && liveP !== p) stopPreview(liveP);
  liveP = p;
  p.state = "loading";
  labelPreview(p);
  try {
    if (!p.url) p.url = await audioUrl(p.name);
    /* `reload`: una pista servida por URL (la prueba) es SIEMPRE una grabación
       nueva, aunque se llame igual que la anterior. */
    const fresh = p.reload || player.dataset.name !== p.name;
    if (fresh) { p.reload = false; player.dataset.name = p.name; player.src = p.url; }
    await player.play();
    if (fresh && p.t > 0 && isFinite(player.duration)) player.currentTime = p.t;
    /* Si la duración no vino por adelantado (backend viejo), se aprende del
       propio audio en cuanto suena: el tiempo nunca se queda en 00:00. */
    if (!p.dur && isFinite(player.duration) && player.duration > 0) {
      p.dur = player.duration;
      paintPreview(p);
    }
  } catch (_) {
    stateOf(p, "error");
  }
}

/* Trae la envolvente de una pista y la dibuja. Si el fichero todavía no se
   puede leer —la grabación de la reunión se normaliza justo al cerrarse y
   /peaks puede fallar durante ese instante— REINTENTA unas cuantas veces en vez
   de dejar la onda clavada en la guía discontinua toda la sesión. */
function loadPeaks(p, tries) {
  tries = tries || 0;
  fetchPeaks(p.name).then(d => {
    if (!p.el.isConnected) return;
    if (!d) {
      if (tries < 8) { p.retry = setTimeout(() => loadPeaks(p, tries + 1), 900); return; }
      p.loading = false; clearTimeout(p.slow);
      p.broken = true;                 // /peaks no pudo: la fila sigue, sin onda
      p.note.textContent = t("ui.pvNoWave");
      p.note.hidden = false;
      if (p.track) { p.track.setAttribute("aria-disabled", "true"); p.track.tabIndex = -1; }
      paintPreview(p);
      return;
    }
    p.loading = false; clearTimeout(p.slow);
    p.broken = false;
    p.peaks = d.peaks;
    if (!p.dur) p.dur = Number(d.dur) || 0;
    p.note.hidden = true;
    if (p.track) { p.track.removeAttribute("aria-disabled"); p.track.tabIndex = 0; }
    paintPreview(p);
  });
}

/* Reproductor de una fila: botón, onda pulsable y tiempo.
   opts.url     -> usa esta URL en vez del endpoint /audio?name=
   opts.peaks   -> envolvente ya conocida (la prueba de micro la trae en /state)
   opts.dur     -> duración conocida POR ADELANTADO: el tiempo se enseña antes
                   de reproducir, no al acabar
   opts.silent  -> la captura salió muda: la pista lo dice con texto
   opts.skipPeaks -> no pide /peaks (aquí no hay envolvente en el servidor) */
function makePreview(name, opts) {
  opts = opts || {};
  const noWave = !!opts.noWave;      // sin onda (prueba de micro: el feedback ya está en el medidor)
  const el = document.createElement("div");
  el.className = "pv";
  const btn = document.createElement("button");
  btn.type = "button"; btn.className = "pv-play"; btn.dataset.state = "idle";
  const time = document.createElement("span");
  time.className = "pv-time";
  const note = document.createElement("span");
  note.className = "pv-note"; note.hidden = true;
  let track = null, canvas = null;
  if (noWave) {
    el.append(btn, time, note);
  } else {
    track = document.createElement("div");
    track.className = "pv-track"; track.tabIndex = 0;
    track.setAttribute("role", "slider");
    track.setAttribute("aria-valuemin", "0");
    track.setAttribute("aria-valuemax", "100");
    canvas = document.createElement("canvas");
    canvas.className = "pv-wave";
    track.appendChild(canvas);
    el.append(btn, track, time, note);
  }

  const p = { el, name, btn, track, canvas, time, note, ro: null,
              peaks: (opts.peaks && opts.peaks.length) ? opts.peaks : null,
              silent: !!opts.silent, dur: Number(opts.dur) || 0, t: 0,
              url: opts.url || null, reload: !!opts.url, state: "idle",
              broken: false, loading: true };
  WAVES.add(p);

  btn.addEventListener("click", () => togglePreview(p));

  if (track) {
    const ratioAt = ev => {
      const r = track.getBoundingClientRect();
      return r.width ? Math.min(1, Math.max(0, (ev.clientX - r.left) / r.width)) : 0;
    };
    let dragging = false;
    track.addEventListener("pointerdown", ev => {
      if (p.broken) return;
      ev.preventDefault();
      dragging = true;
      if (track.setPointerCapture) { try { track.setPointerCapture(ev.pointerId); } catch (_) {} }
      seekTo(p, ratioAt(ev));
    });
    track.addEventListener("pointermove", ev => { if (dragging) seekTo(p, ratioAt(ev)); });
    const endDrag = () => { dragging = false; };
    track.addEventListener("pointerup", endDrag);
    track.addEventListener("pointercancel", endDrag);
    track.addEventListener("keydown", ev => {
      const k = ev.key;
      if (k === "ArrowLeft" || k === "ArrowRight") {
        if (!p.dur) return;
        ev.preventDefault();
        seekTo(p, Math.max(0, Math.min(p.dur, p.t + (k === "ArrowLeft" ? -2 : 2))) / p.dur);
      } else if (k === "Home") { ev.preventDefault(); seekTo(p, 0); }
      else if (k === "End") { ev.preventDefault(); seekTo(p, 1); }
      else if (k === " " || k === "Enter") { ev.preventDefault(); togglePreview(p); }
    });
  }

  p.slow = setTimeout(() => {
    if (p.loading && !p.broken) { note.textContent = t("ui.pvLoad"); note.hidden = false; }
  }, 400);

  if (opts.skipPeaks || noWave) {
    p.loading = false;
    clearTimeout(p.slow);
    /* La prueba de micro trae su envolvente en /state, pero su pista no se
       dibuja: si la captura salió muda lo cuenta el texto de al lado. */
    if (noWave && opts.silent) { note.textContent = t("ui.testSilent"); note.hidden = false; }
  } else {
    loadPeaks(p);
  }

  if (track && window.ResizeObserver) {
    p.ro = new ResizeObserver(() => paintWave(p));
    p.ro.observe(track);
  }
  labelPreview(p);
  return p;
}

/* ---------------- audios, reunión y documentos ---------------- */
/* Estado de un fichero subido -> texto y color de su tapiña (la misma escala
   que el resto del panel: en espera, transcribiendo, guardado, error). */
const UPLOAD_STATE = {
  pendiente:      { key: "ui.stPending", cls: "wait" },
  transcribiendo: { key: "ui.statusTranscribing", cls: "run" },
  listo:          { key: "ui.saved", cls: "ok" },
  error:          { key: "ui.stError", cls: "err" }
};

/* ¿La subida ya terminó (bien o mal)? El ESTADO lo manda su ficha de /state; el
   progreso, la cola. Nunca se decide por «existe el .md», que se crea en cuanto
   empieza a escribir. */
const finishedState = st => st === "listo" || st === "error";

/* El audio de un fichero SUBIDO vive en audios/ con un nombre interno (a
   diferencia de una reunión, que guarda el .wav con el nombre del documento).
   El ÚNICO sitio donde el panel ve ese nombre es el `src` del trabajo en la
   cola (/state.queue), así que se indexa por RAÍZ de nombre —la del documento y
   la del propio fichero subido— para casar cada subida con su documento ya
   transcrito. Sin este índice la tarjeta del documento no podía enseñar su
   audio: la subida desaparecía al transcribirse (deduplicación) y la
   transcripción quedaba justo donde iba el reproductor, sin audio que ver. */
function queueAudioMap() {
  const m = new Map();
  (state.queue || []).forEach(q => {
    const src = baseName(q.src || "");
    if (!src) return;
    [q.doc, q.label, q.src].forEach(v => {
      const k = docStem(baseName(v || ""));
      if (k && !m.has(k)) m.set(k, src);
    });
  });
  return m;
}

/* Los ficheros subidos, ya con la forma de la ficha. Mientras el backend no
   publique `uploads`, se derivan de la cola (`queue`), que trae los mismos
   datos con otro nombre: UNA sola lista, nunca la misma cosa dos veces. */
function uploadItems() {
  const qa = queueAudioMap();
  if (Array.isArray(state.uploads)) {
    return state.uploads.map(u => ({
      name: String(u.name || ""),
      size: Number(u.size) || 0,
      duration: Number(u.duration) || 0,
      doc: baseName(u.doc),
      state: String(u.state || "pendiente"),
      progress: Number(u.progress) || 0,
      /* El reproductor de la ficha se puede pintar DESDE YA: el audio que el
         backend puso en audios/ lo da la cola (aquí por raíz de nombre). */
      play: baseName(u.src || u.audio || "") || qa.get(docStem(u.name)) || ""
    }));
  }
  return (state.queue || []).map(q => {
    const st = String(q.status || "");
    return {
      name: baseName(q.label || q.src),
      size: Number(q.size) || 0,
      duration: Number(q.duration) || 0,
      doc: baseName(q.doc),
      state: st.startsWith("error") ? "error" : st === "listo" ? "listo" : "transcribiendo",
      progress: Number(q.progress) || 0,
      play: baseName(q.src)
    };
  });
}

/* Peso legible (KB / MB): la ficha dice lo que ocupa el fichero de verdad. */
function fmtSize(bytes) {
  const b = Number(bytes) || 0;
  if (!b) return "";
  if (b >= 1048576) return (b / 1048576).toFixed(1) + " MB";
  return Math.max(1, Math.round(b / 1024)) + " KB";
}

/* ---- reunión: hub con tres caras (inicio / en vivo / resumen) ---- */
/* Duración legible. Con grabaciones largas añade las HORAS (2:00:00 en vez de
   120:00): la etiqueta del tiempo no se alarga raro y no empuja la onda. */
function fmtTime(sec, hours) {
  sec = Math.max(0, Math.floor(sec || 0));
  const h = Math.floor(sec / 3600);
  const m = Math.floor((sec % 3600) / 60);
  const s = sec % 60;
  const p2 = n => String(n).padStart(2, "0");
  if (hours || h > 0) return `${h}:${p2(m)}:${p2(s)}`;
  return `${p2(m)}:${p2(s)}`;
}

/* Grabación recién guardada: se puede escuchar antes de descargar. */
let meetPv = null;

function paintMeetWav(m) {
  const slot = $("#meetWav");
  const wav = m.status === "guardada" ? baseName(m.wav) : "";
  if (meetPv && meetPv.name !== wav) { disposePreview(meetPv); meetPv = null; }
  if (wav && !meetPv) { meetPv = makePreview(wav); slot.appendChild(meetPv.el); }
  if (meetPv) labelPreview(meetPv);      // el idioma puede haber cambiado
  slot.hidden = !meetPv;
}

/* Fuente de audio de la reunión: todo el sistema o una aplicación concreta.
   El punto marca si esa fuente está sonando; se bloquea con la reunión activa. */
function paintSources() {
  const sel = $("#selSource");
  const list = (state.sources || []).slice();
  if (!list.length) list.push({ key: "all", playing: true });
  const cur = String(state.meeting_source || "all");
  if (!list.some(s => s.key === cur)) {
    list.unshift({ key: cur, label: t("ui.srcMissing"), playing: false });
  }
  fillSelect(sel, list.map(s => ({
    value: s.key,
    label: s.key === "all" ? t("ui.srcAll") : s.label,
    /* El estado ya NO va como ●/○ en el texto (salían puntos incoherentes y
       sin significado): viaja como dato y lo pinta el MISMO punto .src-dot que
       usa el resto del panel. */
    on: !!s.playing
  })), cur);
  sel.disabled = !!(state.meeting || {}).active;
  const curSrc = list.find(s => s.key === cur);
  $("#srcDot").classList.toggle("on", !!curSrc && !!curSrc.playing);
}

function paintMeeting() {
  const m = state.meeting || {};
  const idle = $("#meetIdle"), live = $("#meetLive"), done = $("#meetDone");

  if (m.active) {
    idle.hidden = true;  done.hidden = true;  live.hidden = false;
    $("#meetTimer").textContent = fmtTime(m.seconds);
    $("#recPill").classList.toggle("paused", !!m.paused);
    const pause = $("#btnMeetPause");
    const pauseKey = m.paused ? "ui.resume" : "ui.pause";
    setIcon(pause, m.paused ? "play" : "pause");
    pause.setAttribute("aria-label", t(pauseKey));
    pause.title = t(pauseKey);
    const tr = $("#meetTranscript");
    if (m.paused) {
      tr.textContent = t("ui.meetLast") + " — " + (m.last || t("ui.meetEmptyTr"));
      tr.classList.add("muted");
    } else if (m.last) {
      tr.textContent = m.last;
      tr.classList.remove("muted");
    } else {
      tr.textContent = t("ui.meetEmptyTr");
    }
    const err = $("#meetErr");
    if (m.status && String(m.status).startsWith("error")) {
      err.textContent = t("ui.meetError") + " " + m.status;
      err.hidden = false;
    } else {
      err.hidden = true;
    }
    /* Niveles en vivo: las PISTAS se mueven con la energía real que publica el
       backend (levels.sys / levels.mic); paintLevels les da el objetivo y el
       bucle de dibujo las anima. Pausado, la pista se apaga. */
    paintLevels();
    /* La pista del micrófono solo tiene sentido si se graba: apagado, se oculta
       para no dejar una barra muerta con su etiqueta. */
    const micLane = $(".meet-level.lv-mic");
    if (micLane) micLane.hidden = state.meeting_mic === false;
    // El polling repinta i18n; conserva el estado de confirmación del clic.
    const cancel = $("#btnMeetCancel");
    confirmState(cancel, !!cancel.dataset.confirm, "ui.meetCancel", "ui.confirmCancel");
    return;
  }

  live.hidden = true;
  if (m.status === "guardada" || m.status === "cancelada") {
    idle.hidden = true;  done.hidden = false;
    $("#meetDoneText").textContent =
      (m.status === "guardada" ? t("ui.meetSaved") : t("ui.meetCancelled"))
      + (m.doc ? " · " + m.doc.split(/[\\/]/).pop() : "");
    $("#btnMeetOpenDoc").hidden = m.status !== "guardada";
    $("#btnMeetDlWav").hidden = !(m.status === "guardada" && m.wav);
    $("#meetDone").dataset.doc = (m.doc || "").split(/[\\/]/).pop() || "";
    $("#meetDone").dataset.wav = (m.wav || "").split(/[\\/]/).pop() || "";
    paintMeetWav(m);
    return;
  }
  idle.hidden = false;
  done.hidden = true;
  const status = $("#meetStatus");
  if (m.status) {
    status.textContent = m.status;
    status.classList.toggle("err", String(m.status).startsWith("error"));
  } else {
    status.textContent = "";
  }
}

/* Micrófono en la reunión: mezcla tu voz con el audio del sistema. */
function paintMeetMic() {
  const sw = $("#meetMicSwitch");
  if (!sw) return;
  const on = state.meeting_mic !== false;
  sw.setAttribute("aria-checked", String(on));
  const st = $("#meetMicState");
  if (st) st.textContent = on ? t("ui.meetMicOn") : t("ui.meetMicOff");
}

/* ---- prueba de micrófono: medidor de nivel en vivo + escucha de lo grabado ----
   Contrato fijado: POST {action:"mic.test",value:"start"|"stop"}; /state.mic_test
   trae {active, level, peak, done, wav}; el audio se sirve en GET /panel/mictest.wav.
   Si el backend todavía no lo cumple, la UI queda lista y no lanza nada. */
let micTestPv = null;

function micTestVisible() { const b = $("#micTest"); return !!b && !b.hidden; }

function stopMicPlayer() {
  if (micTestPv) { disposePreview(micTestPv); micTestPv = null; }
  const slot = $("#micTestSlot");
  if (slot) slot.innerHTML = "";
}

/* Arranca o para la prueba desde el propio grupo «Micrófono»: el botón «Probar»
   («Probar la entrada») y el Detener/Repetir del propio panel en vivo. */
async function startMicTest() {
  const active = !!(state.mic_test || {}).active;
  const box = $("#micTest");
  if (box) box.hidden = false;                       // se muestra al probar
  await send("mic.test", active ? "stop" : "start");
  merge(await getState());
  paint();
}

function paintMicTest() {
  const mt = state.mic_test || {};
  const active = !!mt.active;
  const done = !active && !!mt.done;
  if (active && $("#micTest")) $("#micTest").hidden = false;   // prueba en marcha

  /* El botón «Probar» solo se enseña con la prueba cerrada: en marcha (o recién
     terminada) manda el propio panel en vivo con su Detener/Repetir. */
  const go = $("#micTestGo");
  if (go) go.hidden = micTestVisible();

  if (micTestVisible()) {
    const ttl = $("#micTestTitle"), msg = $("#micTestMsg"), act = $("#micTestAct");
    /* La acción de la prueba es un ICONO (stop / repeat), con su nombre
       accesible: nunca un botón de texto «Detener». */
    const setAct = (name, key) => {
      if (!act) return;
      setIcon(act, name, 13);
      act.setAttribute("aria-label", t(key));
      act.title = t(key);
    };
    if (active) {
      if (ttl) ttl.textContent = t("ui.testTitle");
      if (msg) msg.textContent = t("ui.testHint");
      setAct("stop", "ui.testStop");
    } else if (done) {
      const pk = Math.max(0, liveScalars.probePeak);
      if (ttl) ttl.textContent = t("ui.testDone");
      /* Captura muda: se dice con texto, nunca con una raya plana. */
      if (msg) msg.textContent = mt.silent ? t("ui.testSilent")
        : (pk < 0.05 ? t("ui.testLow") : t("ui.testOk"));
      setAct("refresh", "ui.testAgain");
    }
  }

  /* Lo grabado vive en /panel/mictest.wav y se reproduce EN ESTA MISMA fila: el
     backend publica `duration` (el tiempo se ve desde el primer momento, no al
     acabar) y `silent` (una captura muda lo cuenta con texto). Solo se enseña si
     la prueba está ABIERTA: en el arranque el backend puede traer una prueba ya
     terminada y no debe salir sin pedirlo. */
  const withWav = micTestVisible() && done && !!mt.wav;
  const slot = $("#micTestSlot");
  if (withWav && slot) {
    if (!micTestPv) {
      /* Sin onda y SIN nota propia: el estado (incluida la captura muda) ya lo
         dice el texto de la fila (#micTestMsg); aquí solo van play y duración. */
      micTestPv = makePreview(baseName(mt.wav), {
        url: "/panel/mictest.wav", skipPeaks: true, noWave: true, dur: mt.duration });
      slot.innerHTML = "";
      slot.appendChild(micTestPv.el);
    }
    syncMicTestPv(mt);
  } else if (micTestPv) {
    stopMicPlayer();
  }
  const player = $("#micTestPlayer");
  if (player) player.hidden = !withWav;
}

/* El reproductor de la prueba se crea UNA vez y luego solo se le actualiza la
   duración (el primer /state puede llegar sin ella). El estado de la captura lo
   lleva el texto de la fila, no este reproductor. */
function syncMicTestPv(mt) {
  const p = micTestPv;
  if (!p) return;
  const dur = Number(mt.duration) || 0;
  if (!p.dur && dur) { p.dur = dur; paintPreview(p); return; }
  labelPreview(p);                      // el idioma puede haber cambiado
}

const mRows = new Map();
/* Nota del guardado de la grabación de reunión: misma mecánica que la de las
   tarjetas (`saveNote` + `saveT`), fuera de la lista de tarjetas. */
const meetSave = { saveNote: null, saveT: null, busy: false };

/* ==========================================================================
   AUDIOS Y DOCUMENTOS: una SOLA tarjeta, rehecha desde cero
   --------------------------------------------------------------------------
   Una reunión grabada, un audio subido ya transcrito y uno recién subido
   mientras transcribe usan EL MISMO componente (.d-item .m-item), con un ORDEN
   FIJO y sin posicionamiento absoluto ni alturas fijas:

     1. cabecera    icono + nombre real + peso · duración + acciones
                    (renombrar y quitar/eliminar en DOS PASOS);
     2. reproductor onda REAL (/peaks) con su duración, alineado al raíl;
     3. debajo      la transcripción completa (con su propio scroll interno) o,
                    si aún no está, el estado con su barra de progreso;
     4. descargas   .md / .txt / .wav, visibles y funcionales cuando EXISTEN.

   Nada se superpone: cabecera, reproductor, transcripción y descargas son
   bloques APILADOS en columna dentro de la misma tarjeta.
   ========================================================================== */

/* Lista ÚNICA: cada cosa del autor aparece una sola vez. Un documento ya
   transcrito (subida terminada o reunión grabada) se pinta con su tarjeta; una
   subida que AÚN no tiene documento se pinta con la MISMA tarjeta, en curso. En
   cuanto la subida tiene transcripción, su tarjeta pasa a ser la del documento:
   nunca se ven las dos a la vez ni se solapan. */
function mediaItems() {
  const qa = queueAudioMap();
  const docs = (state.docs || []).slice()
    .sort((a, b) => (Number(b.mtime) || 0) - (Number(a.mtime) || 0));
  const ups = uploadItems();
  const have = new Set();
  const items = [];

  const withExt = n => {
    const s = String(n || "");
    if (!s) return "";
    return stripExt(s) !== s ? s : s + ".md";
  };

  /* Índice por RAÍZ: enlaza una subida con su documento ya transcrito, para que
     la tarjeta del documento sepa que TAMBIÉN hay una ficha de subida que
     borrar. Sin esto, eliminar un documento ya transcrito dejaba su subida
     huérfana en uploads.json y la tarjeta volvía a aparecer (fantasma). */
  const upByStem = new Map();
  ups.forEach(u => {
    const k = docStem(u.doc || u.name);
    if (k && !upByStem.has(k)) upByStem.set(k, u);
  });
  /* Estado real de la cola por RAÍZ: da el PROGRESO (que la ficha de /state no
     publica) y respalda el estado de la subida. */
  const qStem = new Map();
  (state.queue || []).forEach(q => {
    const k = docStem(baseName(q.doc || q.label || q.src));
    if (k && !qStem.has(k)) qStem.set(k, { status: String(q.status || ""), progress: Number(q.progress) || 0 });
  });
  const finished = finishedState;

  /* Reunión EN CURSO: su .md ya existe (el backend lo escribe MIENTRAS
     transcribe) y su .wav también, así que por «existe el fichero» se pintaba
     como una tarjeta TERMINADA —con reproductor, duración y descargas— cuando
     lo que pasa es que sigue grabando. Mientras la reunión vive, esa tarjeta es
     la del estado en curso: «Transcribiendo…», sin reproductor (el .wav se
     está escribiendo) y sin descargas. */
  const mt = state.meeting || {};
  const mStem = mt.active ? docStem(baseName(mt.doc || "")) : "";
  const live = [];
  if (mStem) {
    live.push({
      kind: "upload", key: "live:" + mStem, stem: mStem,
      name: baseName(mt.wav || mt.doc || "") || baseName(mt.doc || ""),
      size: 0, duration: Number(mt.seconds) || 0, play: "",
      hasWav: false, upName: "", docName: "", doc: "",
      transcribe: false, state: "transcribiendo", progress: -1
    });
  }

  docs.forEach(d => {
    const stem = docStem(d.name);
    if (stem) have.add(stem);
    if (mStem && stem === mStem) return;         // la pinta su tarjeta en curso
    const u = upByStem.get(stem);
    /* Si su subida AÚN está en curso (pendiente/transcribiendo), NO es una
       transcripción terminada: la representa la tarjeta de la subida con su
       «Transcribiendo…». El .md YA existe desde el primer instante (el backend
       lo escribe MIENTRAS transcribe) y su estado todavía no es «listo»: por eso
       no basta con que el fichero esté, hay que mirar el ESTADO de la subida. */
    if (u && !finished(u.state)) return;
    const own = baseName(d.audio);                 // .wav de la reunión, si lo hay
    /* El audio de la carta: el .wav propio de la reunión o el audio REAL de la
       subida que produjo este documento. Un documento que NO tiene audio propio
       ni subida que lo respalde se queda SIN reproductor y SIN duración: la
       onda prestada del audio de al lado era justo el fallo de la tarjeta
       duplicada. */
    const audio = own || (u && u.play) || qa.get(stem) || "";
    items.push({
      kind: "doc", key: "doc:" + d.name, stem,
      /* Con subida emparejada, la carta es la del AUDIO que el autor añadió
         (su nombre, su peso y su duración reales) y lleva DENTRO su
         transcripción: una sola carta, no una del .mp3 y otra del .md. Una
         reunión grabada no tiene subida: su audio es el .wav que se llama como
         el documento, y la cabecera enseña ESE fichero. */
      name: (u && u.name) || own || d.name,
      size: Number(u ? u.size : (own ? (Number(d.audio_size) || d.size) : d.size)) || 0,
      duration: Number(u ? u.duration : d.duration) || 0,
      play: audio,
      hasWav: !!own, doc: withExt(d.name), docName: withExt(d.name),
      upName: u ? u.name : "",
      transcribe: true
    });
  });

  /* Subidas SIN documento terminado: van ARRIBA, con su estado y su barra. Una
     subida NUNCA es «transcripción» hasta que su estado es final (listo/error)
     Y su documento existe —cuando lo es, la representa la tarjeta del doc—. */
  const pend = [];
  ups.forEach(u => {
    const stem = docStem(u.doc || u.name);
    if (stem && have.has(stem) && finished(u.state)) return;   // ya la representa su doc
    const q = qStem.get(stem) || {};
    pend.push({
      kind: "upload", key: "up:" + u.name, stem,
      name: u.name, size: Number(u.size) || 0,
      duration: Number(u.duration) || 0,
      play: u.play || qa.get(docStem(u.name)) || "",
      hasWav: false,
      upName: u.name, docName: "",
      doc: "", transcribe: false,
      state: String(u.state || "pendiente"),
      progress: Number(u.progress) || Number(q.progress) || 0
    });
  });
  return live.concat(pend, items);
}

/* Construye UNA tarjeta vacía; su contenido lo pone paintMediaCard en cada
   repintado (el sondeo de /state). Todo es flujo normal: ningún hijo se saca
   del flujo con position:absolute ni con alturas fijas. */
function makeMediaCard() {
  const el = document.createElement("div");
  el.className = "d-item m-item";

  /* (1) cabecera: icono + nombre real + peso/duración + acciones */
  const head = document.createElement("div");
  head.className = "m-head";
  const tile = document.createElement("span");
  tile.className = "tile accent m-tile";
  tile.dataset.icon = "file-audio"; tile.dataset.size = "16";
  const txt = document.createElement("span");
  txt.className = "m-txt";
  const name = document.createElement("span");
  name.className = "m-name";
  const meta = document.createElement("span");
  meta.className = "m-meta";
  txt.append(name, meta);
  const acts = document.createElement("span");
  acts.className = "m-acts";
  const ren = document.createElement("button");
  ren.type = "button"; ren.className = "btn btn-soft btn-icon btn-sm";
  ren.dataset.icon = "pencil"; ren.dataset.size = "13";
  const del = document.createElement("button");
  del.type = "button"; del.className = "btn btn-danger btn-icon btn-sm";
  del.dataset.icon = "trash"; del.dataset.size = "13";
  /* Flecha de la transcripción: MISMO botón de icono que el lápiz y la basura
     (btn btn-soft btn-icon btn-sm), integrado en la cabecera de la carta. Al
     abrir, el chevron gira para apuntar hacia abajo. */
  const acc = document.createElement("button");
  acc.type = "button"; acc.className = "btn btn-soft btn-icon btn-sm m-acc";
  acc.dataset.icon = "chevron-right"; acc.dataset.size = "14"; acc.dataset.sw = "2.2";
  acc.setAttribute("aria-expanded", "false");
  acts.append(acc, ren, del);
  head.append(tile, txt, acts);

  /* (2) reproductor: onda real (/peaks) + su duración */
  const pvSlot = document.createElement("div");
  pvSlot.className = "m-pv";

  /* (3) estado + progreso (mientras transcribe) o transcripción completa */
  const stateRow = document.createElement("div");
  stateRow.className = "m-state"; stateRow.hidden = true;
  const tag = document.createElement("span");
  tag.className = "tag m-tag";
  const progWrap = document.createElement("span");
  progWrap.className = "m-prog"; progWrap.hidden = true;
  const bar = document.createElement("span");
  bar.className = "q-bar";
  const fill = document.createElement("i");
  bar.append(fill);
  progWrap.append(bar);
  stateRow.append(tag, progWrap);

  const transcript = document.createElement("div");
  transcript.className = "m-transcript";
  transcript.setAttribute("role", "region");
  transcript.tabIndex = 0;
  transcript.hidden = true;

  /* (4) descargas: solo cuando existen (iconos distintos) */
  const tools = document.createElement("div");
  tools.className = "m-tools";
  const mkFmt = (icon, label, kind) => {
    const b = document.createElement("button");
    b.type = "button"; b.className = "btn btn-soft btn-fmt";
    b.dataset.kind = kind;
    const i = document.createElement("span");
    i.dataset.icon = icon; i.dataset.size = "13";
    const f = document.createElement("span");
    f.className = "fmt"; f.textContent = label;
    b.append(i, f);
    return b;
  };
  const dlMd = mkFmt("file-text", ".md", "md");
  const dlTxt = mkFmt("download", ".txt", "txt");
  const dlWav = mkFmt("file-audio", ".wav", "wav");
  tools.append(dlMd, dlTxt, dlWav);

  /* Confirmación del guardado (ruta elegida): propia línea, oculta por defecto
     para que no ocupe ni un píxel mientras no se usa. */
  const saveNote = document.createElement("p");
  saveNote.className = "d-save";
  saveNote.hidden = true;
  saveNote.setAttribute("role", "status");

  el.append(head, pvSlot, stateRow, transcript, tools, saveNote);

  const r = { el, tile, name, meta, ren, del, acc, pvSlot, pv: null,
              stateRow, tag, progWrap, fill, open: false,
              transcript, tools, dlMd, dlTxt, dlWav, saveNote, saveT: null,
              doc: "", base: "", transcribe: false, loaded: false,
              tReady: false, tRetry: null,
              remove: null, delIdle: "ui.remove", delOn: "ui.confirmRemove",
              prev: {},
              dispose() { clearTimeout(r.tRetry); clearTimeout(r.saveT); if (r.pv) { disposePreview(r.pv); r.pv = null; } } };

  /* desplegar/plegar la transcripción (sin repintar: solo su visibilidad) */
  acc.addEventListener("click", () => {
    r.open = !r.open;
    acc.setAttribute("aria-expanded", String(r.open));
    acc.dataset.open = r.open ? "1" : "0";
    transcript.hidden = !r.open;
  });

  /* renombrar (lápiz): solo cuando hay documento/transcripción */
  ren.addEventListener("click", () => { if (r.doc) beginRename(r, r.doc); });

  /* quitar (subida en curso) / eliminar (documento): DOS PASOS, el mismo botón
     pasa a la pregunta en rojo y solo el segundo clic llama al backend. */
  del.addEventListener("click", async () => {
    if (!r.remove || (!r.remove.doc && !r.remove.up)) return;
    if (del.dataset.confirm) {
      delete del.dataset.confirm;
      confirmState(del, false, r.delIdle, r.delOn);
      await runMediaDelete(r.remove);
      return;
    }
    del.dataset.confirm = "1";
    confirmState(del, true, r.delIdle, r.delOn);
    setTimeout(() => {
      if (!del.dataset.confirm || !del.isConnected) return;
      delete del.dataset.confirm;
      confirmState(del, false, r.delIdle, r.delOn);
    }, 2600);
  });

  /* Descargar = «Guardar como...» del backend. La ventana del panel es WebView2
     incrustado y CANCELA en silencio las descargas por navegacion (medido en la
     ventana real: el clic arranca la descarga, llegan los bytes enteros y el
     motor la cancela; nada en disco y ningun aviso). Por eso el fichero lo
     escribe la app donde el usuario elija y el panel enseña la ruta. */
  [dlMd, dlTxt, dlWav].forEach(b => b.addEventListener("click", () => {
    exportFile(r, r.base, b.dataset.kind, b);
  }));

  paintIcons(el);                       // los iconos de la tarjeta, una vez
  return r;
}

/* Carga el texto ENTERO de la transcripción una sola vez por tarjeta (endpoint
   /doc). Se prueba el nombre tal cual y sin extensión porque según de dónde
   venga el documento llega con .md o sin ella.
   Si el .md aún no se puede leer (se está escribiendo, o acaba de renombrarse)
   se REINTENTA: antes se marcaba como cargado dejando el hueco VACÍO para
   siempre, y entonces la flecha parecía no hacer nada (el hueco vacío no
   ocupa). */
async function loadTranscript(r, doc, tries) {
  tries = tries || 0;
  let txt = null;
  for (const nm of [doc, stripExt(baseName(doc))]) {
    if (!nm) continue;
    try {
      const res = await fetch("/doc?doc=" + encodeURIComponent(nm), { cache: "no-store" });
      if (!res.ok) continue;
      txt = (await res.text()) || "";
      break;
    } catch (_) { /* se prueba el siguiente */ }
  }
  if (!r.el.isConnected || r.doc !== doc) return;
  if (txt === null) {
    if (tries < 6) {
      r.tRetry = setTimeout(() => loadTranscript(r, doc, tries + 1), 900);
      return;
    }
    r.tReady = false;
    r.transcript.textContent = t("ui.docLoadFail");
    return;
  }
  r.tReady = true;
  r.transcript.textContent = txt;
}

function paintMediaCard(r, it) {
  /* --- cabecera: icono, nombre real y peso · duración --- */
  const key = it.key + "|" + (it.doc || "") + "|" + (it.upName || "");
  if (r.prev.key !== key) {
    r.prev.key = key;
    r.doc = it.doc || "";
    r.base = it.doc ? docStem(it.doc) : "";
    r.transcribe = !!it.transcribe;
    r.loaded = false; r.tReady = false;
    clearTimeout(r.tRetry);
    r.transcript.textContent = "";
    r.remove = { doc: it.docName || "", up: it.upName || "" };
    r.delIdle = it.transcribe ? "ui.docDelete" : "ui.remove";
    r.delOn = it.transcribe ? "ui.confirmDelete" : "ui.confirmRemove";
  }
  if (r.prev.name !== it.name) {
    r.name.textContent = it.name;
    r.name.title = it.name;
    r.prev.name = it.name;
  }
  const ext = (String(it.name).split(".").pop() || "").toLowerCase();
  const video = /^(mp4|mkv|mov|avi|webm|m4v|wmv)$/.test(ext);
  const kind = video ? "monitor" : (it.play || it.transcribe ? "file-audio" : "file-text");
  if (r.prev.kind !== kind) { setIcon(r.tile, kind, 16); r.prev.kind = kind; }

  const bits = [];
  if (it.size) bits.push(fmtSize(it.size));
  if (it.duration) bits.push(fmtTime(it.duration, true));
  const meta = bits.join("  ·  ");
  if (r.prev.meta !== meta) { r.meta.textContent = meta; r.meta.hidden = !meta; r.prev.meta = meta; }

  /* --- (2) reproductor: onda real (/peaks) --- */
  const play = it.play || "";
  if (r.prev.play !== play) {
    r.prev.play = play;
    if (r.pv) { disposePreview(r.pv); r.pv = null; }
    if (play) { r.pv = makePreview(play); r.pvSlot.append(r.pv.el); }
  }
  if (r.pv) labelPreview(r.pv);                 // el idioma puede haber cambiado

  /* --- (3) transcripción (acordeón plegable) o el estado con su barra --- */
  if (r.transcribe) {
    r.stateRow.hidden = true;
    r.acc.hidden = false;
    r.transcript.hidden = !r.open;
    if (!r.loaded && r.doc) {
      /* Se pide UNA vez por tarjeta. Mientras llega, el hueco dice que está
         cargando: así la flecha SIEMPRE enseña algo al desplegar (antes, si la
         carga fallaba, el hueco quedaba vacío y desplegar parecía no hacer
         nada). */
      r.loaded = true;
      if (!r.tReady) r.transcript.textContent = t("ui.docLoading");
      loadTranscript(r, r.doc);
    }
  } else {
    r.acc.hidden = true;
    r.transcript.hidden = true;
    r.stateRow.hidden = false;
    const st = UPLOAD_STATE[it.state] || UPLOAD_STATE.pendiente;
    /* Mientras no termina, la tarjeta dice «Transcribiendo…» (o «En espera» si
       aún está en la cola) CON su porcentaje y su barra. El ESTADO lo manda la
       ficha de la subida y el PROGRESO la cola: nunca «existe el fichero», que
       no distingue nada (el .md nace en cuanto empieza a escribir). */
    const prog = (finishedState(it.state) || Number(it.progress) < 0)
      ? -1 : Math.max(0, Math.min(100, Number(it.progress) || 0));
    const lk = it.state + "|" + Math.round(prog) + "|" + uiLocale();
    if (r.prev.st !== lk) {
      r.tag.className = "tag m-tag " + st.cls;
      r.tag.textContent = t(st.key) + (prog >= 0 ? " " + Math.round(prog) + "%" : "");
      r.progWrap.hidden = prog < 0;
      if (prog >= 0) r.fill.style.width = prog + "%";
      r.prev.st = lk;
    }
  }

  /* --- (4) descargas: solo las que existen DE VERDAD --- */
  const showMd = r.transcribe && !!r.base;
  const showTxt = r.transcribe && !!r.base;
  const showWav = r.transcribe && !!it.hasWav;
  const dk = showMd + "" + showTxt + showWav;
  if (r.prev.dk !== dk) {
    r.dlMd.hidden = !showMd;
    r.dlTxt.hidden = !showTxt;
    r.dlWav.hidden = !showWav;
    r.tools.hidden = !(showMd || showTxt || showWav);
    r.prev.dk = dk;
  }
  r.ren.hidden = !r.transcribe || !r.doc;

  /* --- etiquetas (texto, aria-label y title) al idioma actual --- */
  if (r.prev.lab !== uiLocale()) {
    r.dlMd.setAttribute("aria-label", t("ui.dlDocMd")); r.dlMd.title = t("ui.dlDocMd");
    r.dlTxt.setAttribute("aria-label", t("ui.dlDocTxt")); r.dlTxt.title = t("ui.dlDocTxt");
    r.dlWav.setAttribute("aria-label", t("ui.dlAudio")); r.dlWav.title = t("ui.dlAudio");
    r.ren.setAttribute("aria-label", t("ui.docRename")); r.ren.title = t("ui.docRename");
    r.transcript.setAttribute("aria-label", t("ui.docTranscript"));
    r.acc.title = t("ui.transcriptToggle");
    r.acc.setAttribute("aria-label", t("ui.transcriptToggle"));
    r.prev.lab = uiLocale();
  }
  confirmState(r.del, !!r.del.dataset.confirm, r.delIdle, r.delOn);
}

/* Firma de TODO lo que pinta una tarjeta: si no cambia, la tarjeta no se toca.
   El sondeo de /state corre cada 800 ms (150 con algo capturando) y antes volvía
   a pisar la tarjeta entera en cada vuelta, TAMBIÉN MIENTRAS SUENA su audio. El
   tiempo que corre lo pinta el propio reproductor por sus eventos (play/
   timeupdate), así que repintar la tarjeta no aportaba nada y solo hacía trabajo
   en mitad de la reproducción. */
function mediaSig(it, r) {
  return [it.kind, it.key, it.name, it.size, it.duration, it.play, it.doc,
          it.docName, it.upName, it.state, it.progress, it.hasWav,
          it.transcribe, r.open ? 1 : 0, uiLocale()].join("|");
}

/* Pinta UNA SOLA lista, reconciliando en sitio (conserva reproductores, foco y
   selección). Cada tarjeta se crea una vez y se reutiliza. */
function paintMedia() {
  const box = $("#media");
  if (!box) return;
  const items = mediaItems();
  const seen = new Set();
  items.forEach((it, i) => {
    let r = mRows.get(it.key);
    if (!r) { r = makeMediaCard(); r.sig = null; mRows.set(it.key, r); }
    if (box.children[i] !== r.el) box.insertBefore(r.el, box.children[i] || null);
    const sig = mediaSig(it, r);
    if (r.sig !== sig) { r.sig = sig; paintMediaCard(r, it); }
    seen.add(it.key);
  });
  mRows.forEach((r, key) => {
    if (seen.has(key)) return;
    if (r.dispose) r.dispose();
    r.el.remove();
    mRows.delete(key);
  });
  const empty = $("#mediaEmpty");
  if (empty) empty.hidden = items.length > 0;
  const cnt = $("#mediaCount");
  if (cnt) { cnt.hidden = items.length === 0; cnt.textContent = String(items.length); }
}

/* «Descargar» = «Guardar como...» NATIVO del backend. La ventana del panel es
   WebView2 incrustado y CANCELA en silencio las descargas por navegación (un
   <a download> arranca la descarga, llegan los bytes enteros y el motor la
   cancela: nada en disco y ningún aviso — medido por CDP en la ventana real).
   Por eso el fichero lo escribe la APP en la ruta que elija el usuario y el
   panel enseña esa ruta: POST {action:"export", value:{name, kind}}.
   `dest` es cualquier objeto con `saveNote` (el nodo de la nota) y `saveT`. */
async function exportFile(dest, name, kind, btn) {
  if (!dest || !name || dest.busy) return;
  dest.busy = true;
  if (btn) btn.setAttribute("aria-busy", "true");
  showSaveNote(dest, t("ui.saveChoose"), "wait", 0);
  const res = await send("export", { name, kind });
  dest.busy = false;
  if (btn) btn.removeAttribute("aria-busy");
  if (res && res.ok === true && res.path) {
    showSaveNote(dest, t("ui.saveDone") + " " + res.path, "ok", 12000, res.path);
  } else if (res && res.ok === true && res.canceled) {
    /* Cancelar NO es un fallo: se dice y se va solo, sin romper nada. */
    showSaveNote(dest, t("ui.saveCancel"), "cancel", 4000);
  } else {
    showSaveNote(dest, t("ui.saveFail"), "err", 8000);
  }
}

/* Nota de guardado: texto corto, y la ruta entera en el title. `hold` = 0 la
   deja fija mientras el diálogo está abierto. */
function showSaveNote(dest, msg, state, hold, full) {
  const n = dest && dest.saveNote;
  if (!n) return;
  n.textContent = msg;
  n.dataset.state = state;
  n.hidden = false;
  clearTimeout(dest.saveT);
  dest.saveT = hold ? setTimeout(() => { n.hidden = true; }, hold) : null;
  if (full) n.title = full;
  else n.removeAttribute("title");
}

function showRenameError(r, msg) {
  const wrap = r.el.querySelector(".d-rename-wrap");
  if (!wrap) return;
  let err = wrap.querySelector(".d-rename-err");
  if (!err) {
    err = document.createElement("span");
    err.className = "d-rename-err";
    wrap.appendChild(err);
  }
  err.textContent = msg;
  wrap.classList.add("bad");
  clearTimeout(r.badT);
  r.badT = setTimeout(() => {
    if (!wrap.isConnected) return;
    err.textContent = ""; wrap.classList.remove("bad");
  }, 3000);
}

/* Renombrar en línea: la carta se vuelve un campo con el nombre base y su
   extensión (que NO se toca). Enter guarda, Escape sale, perder el foco guarda. */
function beginRename(r, filename) {
  if (r.el.querySelector(".d-rename-wrap")) return;
  const base = stripExt(filename);
  const ext = filename.slice(base.length);          /* ".md" */
  const wrap = document.createElement("span");
  wrap.className = "d-rename-wrap";
  const input = document.createElement("input");
  input.type = "text"; input.className = "d-rename";
  input.value = base; input.spellcheck = false;
  const extEl = document.createElement("span");
  extEl.className = "d-ext"; extEl.textContent = ext;
  wrap.append(input, extEl);
  r.name.hidden = true;
  r.name.parentNode.insertBefore(wrap, r.name.nextSibling);
  input.focus(); input.select();

  let done = false;
  const cancel = () => { done = true; wrap.remove(); r.name.hidden = false; };
  const commit = async () => {
    if (done) return;
    const val = input.value.trim();
    if (!val || val === base) { cancel(); return; }
    done = true;
    const ok = await renameDoc(filename, val, r);
    if (!ok) { done = false; input.focus(); input.select(); return; }
    wrap.remove(); r.name.hidden = false;
  };
  input.addEventListener("keydown", e => {
    if (e.key === "Enter") { e.preventDefault(); commit(); }
    else if (e.key === "Escape") { e.preventDefault(); cancel(); }
  });
  input.addEventListener("blur", commit);
}

async function renameDoc(oldName, newBase, r) {
  try {
    const res = await fetch("/rpc", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action: "doc.rename", doc: oldName, name: newBase })
    });
    const data = await res.json().catch(() => ({}));
    if (res.ok && data && data.ok) {
      merge(await getState());
      paint();
      return true;
    }
    showRenameError(r, (data && data.error === "exists")
      ? t("ui.docExists") : t("ui.docRenameFail"));
    return false;
  } catch (_) {
    showRenameError(r, t("ui.docRenameFail"));
    return false;
  }
}

/* ---- audios y documentos: UNA SOLA lista ----
   La lista, las tarjetas y su reconciliación viven arriba (mediaItems /
   makeMediaCard / paintMediaCard / paintMedia). Aquí queda solo la clave que
   enlaza una subida con su documento ya transcrito. */

/* Nombre base sin extensión: «X.md» y la grabación «X» caen en la misma clave,
   que es lo que enlaza una subida con su documento ya transcrito. */
function docStem(n) { return stripExt(baseName(n)); }

/* Borra lo que le toca a UNA tarjeta, todo de una vez y en orden:
     · doc -> POST {action:"doc.delete", doc:"NOMBRE.md"}   (textos/NOMBRE.md)
     · up  -> POST {action:"upload.remove", value:"NOMBRE"} (uploads/<...> y su ficha)
   Una reunión grabada se borra solo con doc; una subida sin transcribir, solo
   con up; una subida YA transcrita lleva los DOS (doc + up) —eso es lo que
   evita que su ficha de subida quede huérfana y la tarjeta reaparezca—. */
async function runMediaDelete(remove) {
  if (remove.doc) {
    try {
      await fetch("/rpc", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "doc.delete", doc: remove.doc })
      });
    } catch (_) {}
  }
  if (remove.up) await send("upload.remove", remove.up);
  merge(await getState());
  paint();
}

/* Trae a la vista la TARJETA de ese documento (nunca una copia): abre la
   sección única de audios y documentos y la desplaza hasta ella. La usan los
   flujos que antes abrían un editor duplicado (abrir el documento desde un
   fichero subido o desde la reunión recién guardada).
   El `doc` llega unas veces como nombre base («Prueba_1»), otras con extensión
   («Prueba_1.md», o la ruta entera de la cola), así que se compara por RAÍZ de
   nombre (la misma clave que enlaza una subida con su documento). */
async function focusDocCard(name) {
  if (!name) return;
  const stem = docStem(baseName(name));
  showSection("audios");                 /* la sección única: audios y documentos */
  const find = () => {
    for (const r of mRows.values()) if (r.base === stem) return r;
    return null;
  };
  let r = find();
  if (!r) { merge(await getState()); paint(); r = find(); }
  if (!r) return;
  r.el.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

/* ---- actualizaciones: la franja del PIE, junto a la versión ---- */
/* Por privacidad la comprobación va APAGADA por defecto: el interruptor de la
   franja solo la enciende si el autor quiere, y es el único momento en que
   dicta pregunta por una versión nueva. El backend publica /state.version,
   /state.update = {available, latest, url, notes, checked_at, progress,
   enabled, error, applied} y el ajuste REAL en /state.check_updates; las
   acciones son POST {action:"check_updates"} (el ajuste), {action:"check_update",
   value:{force:true}} (buscar AHORA, aunque el ajuste esté apagado — es una
   acción explícita del autor, no una comprobación de fondo) y {action:"update"}
   (descargar y aplicar, que el ajuste tampoco bloquea). La franja enseña
   SIEMPRE el estado real y, al pulsar «Actualizar», pregunta ANTES con el
   diálogo propio del panel: si el autor cancela no se envía nada y la descarga
   no llega a lanzarse. Si el backend no publicara `update`, updInfo() devuelve
   null y la franja queda apagada. */
let updBusy = false;      // entre pulsar «Actualizar» y que el backend termine
let updSearching = false; // entre confirmar la búsqueda y que responda
let updTimer = null;      // sondeo breve mientras descarga
let updAutoChecked = false; // el auto-chequeo de arranque ya se lanzó (una vez)

function updInfo() {
  const u = state.update;
  return (u && typeof u === "object") ? u : null;
}

/* El ajuste REAL vive en /state.check_updates (lo publica el backend tal cual
   está en dicta_config.json) y está ACTIVADO por defecto. Antes se espejaba
   /state.update.enabled, que sale «off» (enabled=false) hasta la PRIMERA
   comprobación aunque el ajuste esté encendido: el interruptor mentía al
   arrancar. El respaldo local (state.check_updates, defecto true) cubre el
   instante previo al primer /state. */
function updEnabled() {
  if (typeof state.check_updates === "boolean") return state.check_updates;
  const u = updInfo();
  return u ? (u.enabled !== false) : true;
}

/* Estado REAL de la franja, resuelto por prioridad: lo que está pasando ahora
   manda. Devuelve la clave de la NOTA breve (o null, sin nota) y un `state`
   para dar color con CSS. La ACCIÓN (el enlace) se decide aparte, en
   paintUpdate(), porque su etiqueta depende de si hay algo que instalar. */
function updStatus(u) {
  /* Búsqueda manual en curso: la franja lo dice («Buscando…») aunque el
     backend aún no haya publicado nada nuevo. */
  if (updSearching) return { key: "ui.updSearching", cls: "run" };
  const prog = u ? Number(u.progress) || 0 : 0;
  if (updBusy || (prog > 0 && prog < 100 && u && u.available === true))
    return { key: "ui.updDownload", cls: "run", pct: prog };
  if (u && u.error) return { key: "ui.updFailed", cls: "err" };
  if (u && u.applied) return { key: "ui.updPending", cls: "pend" };
  if (u && u.available) return { key: "ui.updAvailable", cls: "new", v: verText(u.latest) };
  if (u && u.checked_at) return { key: "ui.updUpToDate", cls: "ok", v: verText(state.version) };
  /* Todavía sin datos: si el ajuste está APAGADO se dice («Comprobación
     apagada»); si está encendido se enseña el reposo «Actualizado · vX»
     mientras el panel pide la PRIMERA comprobación (el backend solo comprueba
     cuando se lo piden: ver el auto-chequeo de paintUpdate). */
  if (!updEnabled()) return { key: "ui.updOff", cls: "pend" };
  return { key: "ui.updUpToDate", cls: "ok", v: verText(state.version) };
}

function paintUpdate() {
  const sw = $("#updSwitch");
  if (sw) sw.setAttribute("aria-checked", String(updEnabled()));

  const u = updInfo();
  const prog = u ? Number(u.progress) || 0 : 0;
  const downloading = updBusy || (prog > 0 && prog < 100 && u && u.available === true);
  const avail = !!(u && u.available === true && !u.applied && !u.error);

  /* El ESTADO del pie es, a la vez, el BOTÓN: al día solo informa
     («Actualizado · vX», no pulsable); con versión nueva o error se vuelve
     pulsable (data-action="1", acento + puntero + subrayado + foco) y al
     pulsarlo se abre el diálogo propio (onUpdLink → buscar/instalar). No hay
     enlace aparte: el mismo elemento es estado y acción. */
  const st = updStatus(u);
  const stEl = $("#updState");
  if (stEl) {
    if (!st) {
      stEl.hidden = true;
      stEl.textContent = "";
      stEl.dataset.action = "0";
      stEl.disabled = true;
    } else {
      let txt = t(st.key);
      if (st.pct > 0) txt += " " + Math.round(st.pct <= 1 ? st.pct * 100 : st.pct) + "%";
      else if (st.v) txt += " \u00B7 " + st.v;
      stEl.hidden = false;
      if (stEl.textContent !== txt) stEl.textContent = txt;
      stEl.dataset.state = st.cls;
      stEl.title = txt;
      /* Pulsable cuando hay algo que hacer: versión nueva (INSTALAR, en acento)
         o comprobación manual (BUSCAR: al día, sin datos o con error — así no
         se pierde la búsqueda a mano al haber quitado el enlace «Actualizar»).
         Mientras descarga o busca queda inerte. */
      let act = "0";
      if (!downloading && !updSearching) act = avail ? "install" : "check";
      stEl.dataset.action = act;
      stEl.disabled = (act === "0");
      const aria = act === "install"
        ? t("ui.updInstallAria").replace("{v}", verText(u.latest))
        : (act === "check" ? t("ui.updSearchAria") : txt);
      if (stEl.getAttribute("aria-label") !== aria) stEl.setAttribute("aria-label", aria);
    }
  }

  /* Progreso: el backend lo publica 0..100; se aceptan también 0..1. Solo se
     enseña mientras descarga (o justo al empezar). */
  let pct = prog > 0 ? (prog <= 1 ? prog * 100 : prog) : -1;
  if (updBusy && pct < 0) pct = 0;
  if (pct >= 0) pct = Math.max(0, Math.min(100, pct));
  const box = $("#updProg");
  if (box) box.hidden = pct < 0;
  const fill = $("#updProgFill");
  if (fill && pct >= 0) fill.style.width = Math.round(pct) + "%";

  /* COMPROBACIÓN AUTOMÁTICA de arranque: el backend NO comprueba solo al
     arrancar (solo cuando se lo piden), así que el panel pide UNA vez la
     comprobación cuando ya hay /state real y el ajuste está ENCENDIDO. Con el
     ajuste apagado NO se llama (cero salidas a la red, el criterio de
     privacidad del proyecto). `u` es /state.update: si es null aún no llegó el
     primer /state y no se dispara. */
  if (!updAutoChecked && u && updEnabled() && !u.checked_at &&
      !updBusy && !updSearching) {
    updAutoChecked = true;
    send("check_update");
  }
}

/* Interruptor del ajuste `check_updates`. Al activarlo se pide una comprobación
   inmediata; el estado real llega por /state.update. */
async function toggleUpdateCheck() {
  const on = !updEnabled();
  state.check_updates = on;                    // fuente real (respuesta inmediata)
  const u = updInfo(); if (u) u.enabled = on;  // espejo, por compatibilidad
  paintUpdate();
  await send("check_updates", on);
  if (on) await send("check_update");
  merge(await getState());
  paint();
}

/* Diálogo propio de confirmación: pregunta antes de descargar. Se construye con
   los datos reales (versión y notas) y no envía nada por su cuenta. */
function openUpdDialog() {
  const dlg = $("#updDialog");
  if (!dlg) return;
  const u = updInfo() || {};
  const body = $("#updBody");
  if (body) {
    const base = t("ui.updDialogBody").replace("{v}", verText(u.latest) || "");
    body.textContent = u.notes ? base + "\n\n" + String(u.notes) : base;
  }
  dlg.hidden = false;
  paintIcons(dlg);                 // iconos SVG en línea de sus botones
  const c = $("#updConfirm");
  if (c) c.focus();
}

function closeUpdDialog() {
  const dlg = $("#updDialog");
  if (dlg) dlg.hidden = true;
}

/* Diálogo propio de BÚSQUEDA: el enlace «Actualizar» pregunta antes de tocar
   la red. No envía nada por su cuenta. */
function openUpdCheckDialog() {
  const dlg = $("#updCheckDialog");
  if (!dlg) return;
  dlg.hidden = false;
  paintI18n();                     // el diálogo, en el idioma de la interfaz
  paintIcons(dlg);                 // iconos SVG en línea de sus botones
  const c = $("#updCheckGo");
  if (c) c.focus();
}

function closeUpdCheckDialog() {
  const dlg = $("#updCheckDialog");
  if (dlg) dlg.hidden = true;
}

/* El enlace de la franja: con una versión nueva YA conocida abre el diálogo de
   descarga (con las notas); si no, el de búsqueda. */
function onUpdLink() {
  if (updBusy || updSearching) return;
  const u = updInfo();
  if (u && u.available === true && !u.applied && !u.error) openUpdDialog();
  else openUpdCheckDialog();
}

/* Buscar: «Buscando…» visible mientras responde y el resultado REAL (de
   /state.update) en la franja. Va con force=true: es una búsqueda MANUAL del
   autor, así que consulta GitHub aunque la comprobación automática esté
   apagada. No bloquea la interfaz: el POST devuelve y luego se refresca. */
async function runUpdateSearch() {
  closeUpdCheckDialog();
  if (updSearching || updBusy) return;
  updSearching = true;
  paintUpdate();                   // enseña «Buscando…» ya
  await send("check_update", { force: true });
  merge(await getState());
  updSearching = false;
  paint();                         // el resultado, con la versión
}

/* Aplicar: SOLO desde el diálogo (POST update). Mientras descarga, el progreso
   se pinta en la franja del pie con /state.update.progress; este bucle corto
   solo sirve para reencender el botón cuando ha terminado. */
async function applyUpdate() {
  closeUpdDialog();
  if (updBusy) return;
  updBusy = true;
  paintUpdate();
  await send("update");
  merge(await getState());
  paint();
  if (updTimer) clearInterval(updTimer);
  let n = 0;
  updTimer = setInterval(async () => {
    n++;
    const s = await getState();
    if (s) { merge(s); paint(); }
    const u = updInfo();
    const done = !u || !!u.applied || !!u.error || u.available !== true
                 || (Number(u.progress) || 0) >= 100;
    if (done || n > 200) {
      clearInterval(updTimer); updTimer = null;
      updBusy = false;
      paintUpdate();
    }
  }, 1500);
}

async function uploadAudios(files) {
  if (!files || !files.length) return;
  const fd = new FormData();
  for (const f of files) fd.append("file", f, f.name);
  $("#pickInfo").textContent = "…";
  try {
    await fetch("/upload", { method: "POST", body: fd });
    $("#pickInfo").textContent = `${files.length} →`;
  } catch (_) {
    $("#pickInfo").textContent = "error";
  }
  $("#audioFiles").value = "";
}

/* El favicon de la pestaña tiene que ser EL MISMO icono que el de la barra de
   Windows (lo sirve la app en /panel/icon.png). El navegador cachea ese PNG por
   URL, así que se pide con la versión que publica el backend
   (`/state.icon_version`): cuando cambia el dibujo cambia la URL y se refresca
   solo, sin quedarse con el viejo. */
function paintIcon() {
  const ver = state.icon_version || "1";
  const link = $("#favIcon");
  if (link) {
    const href = `/panel/icon.png?size=32&v=${encodeURIComponent(ver)}`;
    if (link.getAttribute("href") !== href) link.setAttribute("href", href);
  }
  /* La barra integrada la dibuja panel/desktop.js: se le avisa con un evento
     para que refresque su PNG con la misma versión (una sola fuente de verdad). */
  if (window.__dictaIconVer !== ver) {
    window.__dictaIconVer = ver;
    try {
      document.dispatchEvent(new CustomEvent("dicta-icon-version", { detail: ver }));
    } catch (_) { /* navegador sin CustomEvent: el favicon ya está puesto */ }
  }
}

/* ---------------- pintado general ---------------- */
/* La versión se muestra SIEMPRE con tres componentes (mayor.menor.parche): el
   backend publica «1.0» y el autor quiere leer «v1.0.0». */
function verText(v) {
  if (!v) return "";
  const parts = String(v).split(".");
  while (parts.length < 3) parts.push("0");
  return "v" + parts.slice(0, 3).join(".");
}

function paint() {
  paintTheme();
  paintIcon();
  paintI18n();
  paintSelects();
  paintGpu();
  paintAppearance();
  paintMic();
  paintMicMeter();
  paintWait();
  paintDict();
  paintSources();
  paintMedia();
  paintMeeting();
  paintLevels();                         // pistas vivas (reunión / prueba)
  paintUpdate();                         // actualizaciones (fila discreta)
  WAVES.forEach(labelPreview);           // etiquetas al idioma actual
  $("#hotkeyValue").textContent = hotkeyPretty(state.hotkey) || "Alt + Q";
  $("#cancelKeyValue").textContent = hotkeyPretty(state.cancel_key) || "Alt + E";
  if ($("#panelKeyValue")) {
    $("#panelKeyValue").textContent = hotkeyPretty(state.panel_key) || "Ctrl + Alt + P";
  }
  if ($("#meetingKeyValue")) {
    $("#meetingKeyValue").textContent =
      hotkeyPretty((state.hotkeys || {}).meeting) || "Ctrl + Alt + R";
  }
  if ($("#meetCancelKeyValue")) {
    $("#meetCancelKeyValue").textContent =
      hotkeyPretty(meetStopLabel()) || "Ctrl + Alt + S";
  }
  paintMeetMic();
  paintMicTest();
  /* La PIL DE ESTADO se eliminó: la cabecera y la barra ya no la llevan, y su
     feedback (hablar / transcribir) lo da el medidor de entrada. */
}

/* ---------------- cambio de atajos (dictado y cancelar) ---------------- */
const MAIN_KEY_RE = /^[a-z0-9]{1}$/i;
let hkCapturing = null;      // "hotkey" | "cancel_key" | "panel_key" | "meeting" | "meeting_cancel" | null

/* El atajo de detener la reunión: el backend lo publica como `meeting_stop`
   (algunas versiones usan `meeting_cancel`); se acepta el que llegue. */
function meetStopName() {
  const h = state.hotkeys || {};
  if ("meeting_stop" in h) return "meeting_stop";
  if ("meeting_cancel" in h) return "meeting_cancel";
  return "meeting_stop";
}
function meetStopLabel() {
  const h = state.hotkeys || {};
  return h.meeting_stop ?? h.meeting_cancel ?? "";
}

/* ---------------- cambio de atajos: captura ACUMULATIVA ----------------
   El autor lo pidió así: NO hay que pulsar todas las teclas a la vez (con tres
   fallaba). Cada pulsación añade UNA ficha a la combinación y se ve cómo crece;
   «Borrar última» (o Retroceso) quita la última, «Empezar de cero» las vacía y
   «Guardar» la aplica. Los fallos se explican aquí mismo, con el motivo que
   devuelve el backend (no se cierra el capturador: se corrige y se sigue). */
const HK_MAX = 3;                 // el backend valida 1..3 teclas
const HK_MOD_TOKENS = ["ctrl", "alt", "shift", "cmd"];   // orden del backend
let hkKeys = [];                  // fichas acumuladas, en orden de pulsación

const HK_MODS = { alt: "alt", control: "ctrl", ctrl: "ctrl", shift: "shift",
                  meta: "cmd", os: "cmd" };
const HK_NAMED = {
  tab: "tab", enter: "enter", insert: "insert", delete: "delete", home: "home",
  end: "end", pageup: "pageup", pagedown: "pagedown", left: "left", up: "up",
  right: "right", down: "down"
};

/* UNA pulsación -> UNA ficha: un modificador o una tecla. Cada modificador llega
   en su propio keydown (se pulse a la vez o por separado), así que se acumulan
   igual las dos formas. */
function hkToken(e) {
  const k = String(e.key || "");
  const mod = HK_MODS[k.toLowerCase()];
  if (mod) return mod;
  if (/^F(?:[1-9]|1[0-9]|2[0-4])$/i.test(k)) return k.toLowerCase();
  if (k.length === 1 && MAIN_KEY_RE.test(k)) return k.toLowerCase();
  if (HK_NAMED[k.toLowerCase()]) return HK_NAMED[k.toLowerCase()];
  if (e.code && e.code.startsWith("Key")) return e.code.slice(3).toLowerCase();
  if (e.code && e.code.startsWith("Digit")) return e.code.slice(5).toLowerCase();
  return null;
}

/* Orden canónico del backend (MOD_ORDER = ctrl, alt, shift, cmd) y comprobación
   de que hay una tecla principal además de los modificadores. */
function hkSpec() {
  const mods = HK_MOD_TOKENS.filter(m => hkKeys.indexOf(m) >= 0);
  const main = hkKeys.filter(k => HK_MOD_TOKENS.indexOf(k) < 0);
  return mods.concat(main).join("+");
}
function hkHasMain() { return hkKeys.some(k => HK_MOD_TOKENS.indexOf(k) < 0); }

function hkCurrent(target) {
  return target === "cancel_key" ? state.cancel_key
       : target === "panel_key" ? state.panel_key
       : target === "meeting" ? (state.hotkeys || {}).meeting
       : target === "meeting_cancel" ? meetStopLabel()
       : state.hotkey;
}

/* El capturador, dibujado: una ficha por tecla, con su «+» entre medias. */
function hkPaint() {
  const box = $("#hkChips");
  if (box) {
    box.innerHTML = "";
    hkKeys.forEach((k, i) => {
      if (i) {
        const plus = document.createElement("span");
        plus.className = "hk-plus";
        plus.textContent = "+";
        box.appendChild(plus);
      }
      const chip = document.createElement("span");
      chip.className = "hk-chip";
      chip.setAttribute("role", "listitem");
      chip.textContent = hotkeyPretty(k);
      box.appendChild(chip);
    });
  }
  const count = $("#hkCount");
  if (count) count.textContent = hkKeys.length + "/" + HK_MAX;
  const back = $("#hkBack"), save = $("#hkSave");
  if (back) back.disabled = !hkKeys.length;
  if (save) save.disabled = !hkKeys.length;
}

/* El motivo se enseña DENTRO del capturador (y este sigue abierto): el autor
   quiere ver en pantalla por qué no vale (tecla repetida, combinación inválida)
   y corregirla sin empezar de nuevo. `#hkError` queda como red de seguridad por
   si algún día el capturador no estuviera en el DOM. */
function hkShowError(text) {
  const box = $("#hkCaptureError");
  if (box) { box.textContent = text || ""; box.hidden = !text; }
  const out = $("#hkError");
  if (out && !box) { out.textContent = text || ""; out.hidden = !text; }
}

/* Traduce el motivo del backend a una línea clara: se usan los MISMOS textos que
   dicta.py (hotkey_spec_error) para que la app y el panel digan lo mismo. */
function hkWhy(res) {
  const code = String((res && res.error) || "").trim();
  if (code.indexOf("unknown key") === 0)
    return t("ui.hotkeyUnknown") + " " + code.split(":").pop().trim();
  if (code.indexOf("duplicate modifier") === 0)
    return t("ui.hotkeyDupMod") + " " + code.split(":").pop().trim();
  if (code === "too many keys (max 3)") return t("ui.hotkeyTooMany");
  if (code === "only one main key allowed" || code === "missing main key")
    return t("ui.hotkeyNeedMain");
  if (code === "empty" || code === "empty part") return t("ui.hotkeyInvalid");
  if (code === "timeout" || code === "connection") return t("ui.hotkeyTimeout");
  if (code === "invalid") return t("ui.hotkeyInvalid");
  return t("ui.hotkeyUnavailable");
}

function hkOpen(target) {
  hkCapturing = target;
  hkKeys = [];
  const el = $("#hkCapture");
  if (el) el.hidden = false;
  hkShowError("");
  hkPaint();
}

function hkClose() {
  hkCapturing = null;
  hkKeys = [];
  const el = $("#hkCapture");
  if (el) el.hidden = true;
  hkShowError("");
}

function hkBackspace() {
  if (!hkKeys.length) return;
  hkKeys.pop();
  hkShowError("");
  hkPaint();
}

function hkClear() {
  hkKeys = [];
  hkShowError("");
  hkPaint();
}

/* Guardar: aplica la combinación acumulada (1..3 teclas). Solo aquí se habla con
   el backend; si lo rechaza, se enseña el motivo y el capturador sigue abierto. */
async function hkSave() {
  if (!hkCapturing) return;
  const save = $("#hkSave");
  const target = hkCapturing;
  const spec = hkSpec();
  if (!hkKeys.length) { hkShowError(t("ui.hkEmpty")); return; }
  if (!hkHasMain()) { hkShowError(t("ui.hotkeyNeedMain")); return; }
  if (hkKeys.length > HK_MAX) { hkShowError(t("ui.hotkeyTooMany")); return; }
  if (spec === String(hkCurrent(target) || "").toLowerCase()) {
    hkShowError(t("ui.hotkeySame"));
    return;
  }
  if (save) save.disabled = true;                 // sin doble envío
  let response;
  try {
    if (target === "meeting" || target === "meeting_cancel") {
      /* Los atajos de reunión usan {action:"hotkey", value:{name,keys}}. */
      const name = target === "meeting_cancel" ? meetStopName() : "meeting";
      response = await send("hotkey", { name, keys: spec });
    } else {
      const action = target === "cancel_key" ? "set_cancel_key"
                   : target === "panel_key" ? "set_panel_key" : "set_hotkey";
      response = await send(action, spec);
    }
  } finally {
    if (save) save.disabled = false;
  }
  if (response && response.ok) {
    if (target === "cancel_key") state.cancel_key = response.cancel_key || spec;
    else if (target === "panel_key") state.panel_key = response.panel_key || spec;
    else if (target === "meeting") {
      state.hotkeys = Object.assign({}, state.hotkeys,
        { meeting: (response.hotkeys && response.hotkeys.meeting) || spec });
    } else if (target === "meeting_cancel") {
      const name = meetStopName();
      const hs = response.hotkeys || {};
      state.hotkeys = Object.assign({}, state.hotkeys,
        { [name]: hs[name] || spec });
    } else state.hotkey = response.hotkey || spec;
    hkClose();
    paint();
    return;
  }
  hkShowError(hkWhy(response));                   // motivo a la vista
  hkPaint();
}

function wireHotkeyCapture() {
  $("#btnChangeKey").addEventListener("click", () => hkOpen("hotkey"));
  $("#hotkeyValue").addEventListener("dblclick", () => hkOpen("hotkey"));
  $("#btnChangeCancel").addEventListener("click", () => hkOpen("cancel_key"));
  $("#cancelKeyValue").addEventListener("dblclick", () => hkOpen("cancel_key"));
  $("#btnChangePanel").addEventListener("click", () => hkOpen("panel_key"));
  $("#panelKeyValue").addEventListener("dblclick", () => hkOpen("panel_key"));
  $("#btnChangeMeeting").addEventListener("click", () => hkOpen("meeting"));
  $("#meetingKeyValue").addEventListener("dblclick", () => hkOpen("meeting"));
  $("#btnChangeMeetCancel").addEventListener("click", () => hkOpen("meeting_cancel"));
  $("#meetCancelKeyValue").addEventListener("dblclick", () => hkOpen("meeting_cancel"));
  $("#hkCancel").addEventListener("click", hkClose);
  $("#hkBack").addEventListener("click", hkBackspace);
  $("#hkClear").addEventListener("click", hkClear);
  $("#hkSave").addEventListener("click", hkSave);

  /* El atajo es un control: se abre también con Intro o Espacio. */
  [["#hotkeyValue", "hotkey"], ["#cancelKeyValue", "cancel_key"],
   ["#panelKeyValue", "panel_key"], ["#meetingKeyValue", "meeting"],
   ["#meetCancelKeyValue", "meeting_cancel"]].forEach(([sel, key]) => {
    $(sel).addEventListener("keydown", e => {
      if (e.key === "Enter" || e.key === " ") { e.preventDefault(); hkOpen(key); }
    });
  });

  /* Captura ACUMULATIVA: cada pulsación añade UNA ficha a la combinación (no hay
     que pulsarlas todas a la vez, que era lo que fallaba con tres). Escape cierra
     y Retroceso quita la última; lo que no sea una tecla admisible se ignora para
     no romper la combinación que ya llevas. */
  window.addEventListener("keydown", e => {
    if (!hkCapturing) return;
    e.preventDefault();
    e.stopPropagation();
    if (e.key === "Escape") { hkClose(); return; }
    if (e.key === "Backspace") { hkBackspace(); return; }
    const tok = hkToken(e);
    if (!tok) return;
    if (hkKeys.indexOf(tok) >= 0) { hkShowError(t("ui.hkDup")); return; }
    if (hkKeys.length >= HK_MAX) { hkShowError(t("ui.hotkeyTooMany")); return; }
    hkKeys.push(tok);
    hkShowError("");
    hkPaint();
  }, true);
}

/* ---------------- eventos ---------------- */
function wire() {
  $("#selLang").addEventListener("change", e => {
    state.language = e.target.value;
    paint();
    send("language", state.language);
  });
  $("#selEngine").addEventListener("change", e => {
    state.engine = e.target.value;
    paint();
    send("engine", state.engine);
  });
  /* Tarjeta gráfica: es EL MISMO control que el motor (un <select> dentro de
     .select-wrap, mejorado por el desplegable propio), así que elegir un
     dispositivo (o «Automático») dispara aquí su `change` —igual que el <select>
     nativo o el de motor— y manda la acción gpu_device, que guarda y RELANZA el
     motor. El teclado (flechas, Inicio/Fin, Intro/espacio, Escape) lo lleva el
     propio desplegable, sin código aparte. */
  const gpuSel = $("#selGpu");
  if (gpuSel) gpuSel.addEventListener("change", e => gpuApply(e.target.value));
  $("#selModel").addEventListener("change", e => {
    state.model = e.target.value;
    paint();
    send("model", state.model);
  });
  // Interruptor de tema: cada icono selecciona SU tema (sol = claro, luna = oscuro).
  $$("#themeSwitch .ts-opt").forEach(btn => {
    btn.addEventListener("click", () => {
      const want = btn.dataset.val;
      if (state.theme === want) return;
      state.theme = want;
      paint();
      send("theme", state.theme);
    });
  });
  window.addEventListener("resize", moveThemeThumb);

  /* El mismo ajuste de tema desde la sección Apariencia. */
  $$("#themeSeg [data-theme-val]").forEach(btn => {
    btn.addEventListener("click", () => {
      const want = btn.dataset.themeVal;
      if (state.theme === want) return;
      state.theme = want;
      paint();
      send("theme", state.theme);
    });
  });

  /* Posición de la isla (arriba/abajo) desde Apariencia. */
  $$("[data-island-pos-val]").forEach(btn => {
    btn.addEventListener("click", () => {
      const want = btn.dataset.islandPosVal;
      if (state.island_pos === want) return;
      state.island_pos = want;
      paint();
      send("island_pos", want);
    });
  });

  /* Paleta de la isla: el <select> lo mejora el desplegable propio, que
     dispara un `change` que burbujea (igual que el <select> nativo). */
  const palSel = $("[data-island-palette]");
  if (palSel) palSel.addEventListener("change", e => {
    state.island_palette = e.target.value;
    send("island_palette", state.island_palette);
  });

  /* Raíl: una sección a la vista, el resto con `hidden`. */
  $$("#rail .rail-item").forEach(btn => {
    btn.addEventListener("click", () => showSection(btn.dataset.sec));
  });

  /* ¿Se graba también tu micrófono? (mezcla micro + sistema) */
  $("#meetMicSwitch").addEventListener("click", () => {
    state.meeting_mic = !(state.meeting_mic !== false);
    paint();
    send("meeting_mic", state.meeting_mic);
  });

  /* Fuente de audio de la reunión (el punto marca si esa fuente suena). */
  $("#selSource").addEventListener("change", e => {
    state.meeting_source = e.target.value;
    paintSources();
    send("meeting_source", state.meeting_source);
  });

  $("#selMic").addEventListener("change", e => {
    const v = e.target.value;
    state.mic = v === "" ? null : Number(v);
    send("mic", state.mic);
  });

  /* Entrada y umbral: UN control integrado (medidor vertical con la marca
     arrastrable + nivel de voz en horizontal). Arrastrar la marca manda
     `voice_threshold` al backend. */
  wireMicMeter();

  $("#btnAdd").addEventListener("click", addWord);
  /* Enter añade; Mayús+Intro inserta un salto de línea (así se pueden pegar
     varias palabras en líneas distintas). */
  $("#dictInput").addEventListener("keydown", e => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); addWord(); }
  });

  /* Espera antes de transcribir: UNA barra deslizable (0,5-10 s). */
  wireWaitSlider();

  /* audios: selección múltiple → cola */
  $("#btnPickAudio").addEventListener("click", () => $("#audioFiles").click());
  $("#audioFiles").addEventListener("change", e => uploadAudios(e.target.files));

  /* actualizaciones (franja del pie): interruptor del ajuste, botón Actualizar
     que PREGUNTA antes con el diálogo propio, y el diálogo en sí. Cancelar no
     envía nada: la descarga solo se lanza desde «Actualizar» del diálogo. */
  const updSw = $("#updSwitch");
  if (updSw) updSw.addEventListener("click", toggleUpdateCheck);
  /* El ESTADO del pie ES la acción: se pulsa cuando hay algo que hacer. */
  const updStateEl = $("#updState");
  if (updStateEl) updStateEl.addEventListener("click", onUpdLink);
  const updDlg = $("#updDialog");
  const updCancel = $("#updCancel");
  if (updCancel) updCancel.addEventListener("click", closeUpdDialog);
  const updConfirm = $("#updConfirm");
  if (updConfirm) updConfirm.addEventListener("click", applyUpdate);
  if (updDlg) {
    updDlg.addEventListener("click", e => {
      if (e.target === updDlg) closeUpdDialog();     // clic fuera: cancela
    });
  }
  /* diálogo de BÚSQUEDA: «Actualizar» pregunta antes de tocar la red */
  const updCheckDlg = $("#updCheckDialog");
  const updCheckCancel = $("#updCheckCancel");
  if (updCheckCancel) updCheckCancel.addEventListener("click", closeUpdCheckDialog);
  const updCheckGo = $("#updCheckGo");
  if (updCheckGo) updCheckGo.addEventListener("click", runUpdateSearch);
  if (updCheckDlg) {
    updCheckDlg.addEventListener("click", e => {
      if (e.target === updCheckDlg) closeUpdCheckDialog();   // clic fuera: cancela
    });
  }

  /* reunión: hub de grabación (sistema + micro) */
  $("#btnMeeting").addEventListener("click", async () => {
    const m = state.meeting || {};
    if (m.active) return;
    const res = await send("meeting", "start");
    if (res && res.status) state.meeting = state.meeting || {};
    merge(await getState());
    paint();
  });

  $("#btnMeetPause").addEventListener("click", async () => {
    const paused = !!(state.meeting || {}).paused;
    await send("meeting", paused ? "resume" : "pause");
    merge(await getState());
    paint();
  });

  $("#btnMeetStop").addEventListener("click", async () => {
    await send("meeting", "stop");
    merge(await getState());
    paint();
    if ((state.meeting || {}).doc) {
      focusDocCard(state.meeting.doc.split(/[\\/]/).pop());
    }
  });

  $("#btnMeetCancel").addEventListener("click", async () => {
    const btn = $("#btnMeetCancel");
    if (!btn.dataset.confirm) {
      btn.dataset.confirm = "1";
      confirmState(btn, true, "ui.meetCancel", "ui.confirmCancel");
      setTimeout(() => {
        if (btn.dataset.confirm) {
          delete btn.dataset.confirm;
          confirmState(btn, false, "ui.meetCancel", "ui.confirmCancel");
        }
      }, 2600);
      return;
    }
    delete btn.dataset.confirm;
    confirmState(btn, false, "ui.meetCancel", "ui.confirmCancel");
    await send("meeting", "cancel");
    merge(await getState());
    paint();
  });
  $("#meetDone").addEventListener("click", async e => {
    const btn = e.target.closest("button");
    if (!btn) return;
    const dd = $("#meetDone");
    if (btn.id === "btnMeetOpenDoc" && dd.dataset.doc) focusDocCard(dd.dataset.doc);
    else if (btn.id === "btnMeetDlWav" && dd.dataset.wav) {
      /* La grabación también se guarda con el diálogo nativo: la descarga por
         navegación no escribe nada en la ventana de WebView2. */
      meetSave.saveNote = meetSave.saveNote || $("#meetSaveNote");
      exportFile(meetSave, dd.dataset.wav, "wav", btn);
    }
    else if (btn.id === "btnMeetDismiss") {
      // Tiene que olvidarlo el BACKEND: si solo se limpia aqui, el sondeo de
      // /state lo repinta y la tarjeta reaparece (era el fallo del Cerrar).
      await send("meeting", "dismiss");
      merge(await getState());
      paint();
    }
  });

  wireHotkeyCapture();

  $("#btnDone").addEventListener("click", () => cmd("hide"));

  /* Prueba de micrófono: una sola entrada, en el grupo «Micrófono» (botón
     «Probar la entrada» → #micTestGo). El aviso duplicado del pie se retiró. */
  const micGo = $("#micTestGo");
  if (micGo) micGo.addEventListener("click", startMicTest);
  $("#micTestAct").addEventListener("click", async () => {
    const active = !!(state.mic_test || {}).active;
    await send("mic.test", active ? "stop" : "start");
    merge(await getState());
    paint();
  });
  $("#micTestClose").addEventListener("click", async () => {
    if ((state.mic_test || {}).active) await send("mic.test", "stop");
    state.mic_test = Object.assign({}, state.mic_test, { active: false });
    $("#micTest").hidden = true;
    $("#micTestPlayer").hidden = true;
    const go = $("#micTestGo");
    if (go) go.hidden = false;
    stopMicPlayer();
  });

  /* Apagado: SIEMPRE por el diálogo PROPIO del panel (nada de window.confirm).
     Ese diálogo pregunta si apagar Dicta y avisa de que se cerrará todo; solo
     «Apagar Dicta» envía el apagado al backend, que cierra limpio (POST
     {action:"quit"}). Escape y clic fuera cancelan sin enviar nada. */
  const quitDlg = $("#quitDialog");
  const closeQuit = () => { if (quitDlg) quitDlg.hidden = true; };
  const openQuit = () => {
    if (!quitDlg) return;
    quitDlg.hidden = false;
    paintI18n();                    // el diálogo, en el idioma de la interfaz
    paintIcons(quitDlg);            // iconos SVG en línea de sus botones
    const c = $("#quitConfirm");
    if (c) c.focus();
  };
  $("#btnQuit").addEventListener("click", openQuit);
  $("#quitCancel").addEventListener("click", closeQuit);
  $("#quitConfirm").addEventListener("click", () => cmd("quit"));
  if (quitDlg) {
    quitDlg.addEventListener("click", e => {
      if (e.target === quitDlg) closeQuit();      // clic fuera: cancela
    });
  }

  window.addEventListener("keydown", e => {
    if (e.key === "Escape") {
      if (updCheckDlg && !updCheckDlg.hidden) { closeUpdCheckDialog(); return; }
      if (updDlg && !updDlg.hidden) { closeUpdDialog(); return; }
      if (quitDlg && !quitDlg.hidden) { closeQuit(); return; }
      if (!hkCapturing) cmd("hide");
    }
  });
}

/* La pil de estado se eliminó (el feedback lo da el medidor de entrada): ya no
   hay nodo de estado que pintar. */

/* ---------------- desplegable propio ----------------
   El popup de un <select> nativo no se puede estilizar (Chrome solo le aplica
   color-scheme), así que su presentación pasa a un botón con el valor actual +
   una lista flotante. El <select> SIGUE en el DOM y sigue siendo la única
   fuente de verdad: al elegir se le cambia el valor y se dispara su `change`,
   igual que si lo hubiera tocado el usuario. app.js no cambia.
   Teclado: flechas / Inicio / Fin / Intro / Espacio / Escape / Tab. */
const DD = { wrap: null, idx: 0, menu: null, opts: [] };

function ddInit() {
  DD.menu = document.createElement("div");
  DD.menu.className = "dd-menu";
  DD.menu.id = "ddMenu";
  DD.menu.setAttribute("role", "listbox");
  DD.menu.hidden = true;
  document.body.appendChild(DD.menu);

  $$(".select-wrap").forEach(wrap => {
    const sel = $("select", wrap);
    if (!sel || wrap.dataset.dd) return;
    wrap.dataset.dd = "1";
    sel.classList.add("dd-native");          // se oculta; el botón ocupa su sitio

    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "dd-btn";
    btn.setAttribute("aria-haspopup", "listbox");
    btn.setAttribute("aria-expanded", "false");
    btn.setAttribute("aria-controls", "ddMenu");
    const val = document.createElement("span");
    val.className = "dd-val";
    btn.appendChild(val);
    wrap.insertBefore(btn, sel);
    wrap.dd = { sel, btn, val };

    btn.addEventListener("click", () => ddOpen(wrap, true));
    btn.addEventListener("keydown", e => ddKey(e, wrap));
    sel.addEventListener("change", () => ddLabel(wrap));
    /* app.js repinta opciones y `disabled` sin disparar nada: hay que enterarse.
       childList = opciones nuevas; attributes = sel.disabled (paintSources). */
    new MutationObserver(() => {
      ddLabel(wrap);
      if (DD.wrap === wrap) ddOpen(wrap, false);       // la lista abierta, al día
    }).observe(sel, { childList: true, subtree: true, attributes: true,
                      attributeFilter: ["disabled"] });
    ddLabel(wrap);
  });

  document.addEventListener("pointerdown", e => {
    if (DD.wrap && !DD.menu.contains(e.target)
        && !DD.wrap.dd.btn.contains(e.target)) ddClose(false);
  }, true);
  document.addEventListener("keydown", e => {
    if (DD.wrap && e.key === "Escape") { e.preventDefault(); ddClose(true); }
  }, true);
  const pane = $(".pane");
  if (pane) pane.addEventListener("scroll", () => ddClose(false));
  window.addEventListener("resize", () => ddClose(false));
}

/* Punto de estado de una fuente de audio (mismo .src-dot en toda la UI). */
function srcDotEl(on) {
  const d = document.createElement("span");
  d.className = "src-dot" + (on ? " on" : "");
  d.setAttribute("aria-hidden", "true");
  return d;
}

/* La etiqueta del botón es siempre el texto de la opción seleccionada. En la
   fuente de audio, además, el botón lleva delante su punto de estado. */
function ddLabel(wrap) {
  const { sel, btn, val } = wrap.dd;
  const opt = sel.options[sel.selectedIndex];
  val.textContent = opt ? opt.textContent : "";
  /* El detalle del elegido (la tarjeta: nombre COMPLETO + aviso de la integrada)
     también en el control PLEGADO, para no perderlo con la lista cerrada. El
     motor (sin título por opción) no cambia. */
  if (opt && opt.title) btn.title = opt.title; else btn.removeAttribute("title");
  if (sel.id === "selSource") {
    let d = btn.querySelector(".src-dot");
    if (!d) { d = srcDotEl(false); btn.insertBefore(d, val); }
    d.classList.toggle("on", !!opt && opt.dataset.on === "1");
  }
  const lab = sel.getAttribute("aria-label");
  if (lab) btn.setAttribute("aria-label", lab);
  if (sel.disabled) btn.setAttribute("disabled", "");
  else btn.removeAttribute("disabled");
}

function ddSync() { $$(".select-wrap[data-dd]").forEach(w => ddLabel(w)); }

function ddOpen(wrap, focus) {
  const { sel, btn } = wrap.dd;
  const opts = [...sel.options];
  if (!opts.length || sel.disabled) return;
  const isSrc = sel.id === "selSource";    // sus opciones llevan punto de estado
  DD.menu.innerHTML = "";
  DD.opts = [];
  opts.forEach((o, i) => {
    const it = document.createElement("div");
    it.className = "dd-opt";
    it.id = "ddOpt" + i;
    it.setAttribute("role", "option");
    it.setAttribute("aria-selected", String(i === sel.selectedIndex));
    /* Mismo punto para TODAS las fuentes: verde si está sonando, apagado si no.
       (Antes iba un ●/○ de texto en la etiqueta, de tamaño y color variables.) */
    if (isSrc) it.appendChild(srcDotEl(o.dataset.on === "1"));
    const lab = document.createElement("span");
    lab.className = "dd-lab";
    lab.textContent = o.textContent;
    it.appendChild(lab);
    /* Detalle por opción que no cabe en la etiqueta visible (la tarjeta: su
       nombre COMPLETO con el aviso de la integrada): se conserva en el title —y,
       el nombre completo, en el aria— del propio ítem; la marca corta (p. ej.
       «En uso») se pinta como distintivo tras la etiqueta. */
    if (o.title) it.title = o.title;
    if (o.getAttribute("aria-label")) it.setAttribute("aria-label", o.getAttribute("aria-label"));
    if (o.dataset.badge) {
      const bd = document.createElement("span");
      bd.className = "dd-badge";
      bd.textContent = o.dataset.badge;
      it.appendChild(bd);
    }
    /* Opción NO compatible con el equipo: se ve (para que quien tenga esa GPU
       sepa que existe), pero queda deshabilitada y con el motivo en una línea. */
    if (o.disabled) {
      it.classList.add("is-off");
      it.setAttribute("aria-disabled", "true");
      if (o.dataset.note) {
        const nt = document.createElement("span");
        nt.className = "dd-note";
        nt.textContent = o.dataset.note;
        it.appendChild(nt);
      }
    } else if (o.dataset.info) {
      /* Opción que SÍ se puede elegir, con su explicación debajo: así se ve en
         la propia lista por qué es la buena en este equipo. */
      it.classList.add("is-info");
      const nt = document.createElement("span");
      nt.className = "dd-note";
      nt.textContent = o.dataset.info;
      it.appendChild(nt);
    }
    if (i === sel.selectedIndex) {
      const chk = document.createElement("span");
      chk.className = "dd-chk";
      chk.dataset.icon = "check"; chk.dataset.size = "14"; chk.dataset.sw = "2";
      it.appendChild(chk);
    }
    it.addEventListener("pointerdown", e => e.preventDefault());  // el foco no sale del botón
    it.addEventListener("pointerenter", () => { if (!o.disabled) ddMark(i); });
    it.addEventListener("click", () => { if (!o.disabled) ddPick(wrap, i); });
    DD.menu.appendChild(it);
    DD.opts.push(it);
  });
  paintIcons(DD.menu);                       // el check del seleccionado
  DD.wrap = wrap;
  DD.menu.setAttribute("aria-label", sel.getAttribute("aria-label") || t("ui.choose"));
  DD.menu.hidden = false;
  ddPlace(btn);
  btn.setAttribute("aria-expanded", "true");
  ddMark(sel.selectedIndex >= 0 ? sel.selectedIndex : 0);
  if (focus && !btn.hasAttribute("disabled")) btn.focus();
}

/* Menú flotante: position:fixed para que no lo recorte el `overflow:hidden` del
   grupo; se pega al botón y se gira hacia arriba si no cabe abajo. */
function ddPlace(btn) {
  const r = btn.getBoundingClientRect();
  const m = DD.menu;
  m.style.left = "0px"; m.style.top = "0px";
  m.style.minWidth = Math.round(Math.max(160, r.width)) + "px";
  /* La lista NO se ensancha con la explicación del motor: si no, un motivo largo
     estira el menú a media pantalla. Se le pone tope y el texto envuelve. */
  m.style.maxWidth = Math.round(Math.min(420, window.innerWidth - 24)) + "px";
  /* Tope de alto: los motores llevan una línea de motivo debajo del nombre, así
     que la lista necesita más aire que antes (si no, corta la última opción). */
  m.style.maxHeight = Math.round(Math.max(120, Math.min(460, window.innerHeight - r.bottom - 12))) + "px";
  const mr = m.getBoundingClientRect();
  let left = r.left, top = r.bottom + 4;
  if (left + mr.width > window.innerWidth - 8) left = Math.max(8, window.innerWidth - 8 - mr.width);
  if (top + mr.height > window.innerHeight - 8) top = Math.max(8, r.top - 4 - mr.height);
  m.style.left = Math.round(left) + "px";
  m.style.top = Math.round(top) + "px";
}

/* Marca la opción activa (la del teclado) y la deja a la vista. */
function ddMark(i) {
  DD.idx = i;
  DD.opts.forEach((el, k) => { el.dataset.active = String(k === i); });
  const el = DD.opts[i];
  if (!el) return;
  const top = el.offsetTop, bot = top + el.offsetHeight;
  if (top < DD.menu.scrollTop) DD.menu.scrollTop = top;
  else if (bot > DD.menu.scrollTop + DD.menu.clientHeight)
    DD.menu.scrollTop = bot - DD.menu.clientHeight;
  DD.wrap.dd.btn.setAttribute("aria-activedescendant", el.id);
}

/* Siguiente opción ELEGIBLE (las deshabilitadas no se pueden marcar). */
function ddStep(from, dir) {
  const n = DD.opts.length;
  if (!n) return 0;
  let i = from;
  for (let c = 0; c < n; c++) {
    i = (i + dir + n) % n;
    if (!DD.opts[i].classList.contains("is-off")) return i;
  }
  return from;
}
/* Primera y última elegibles (Inicio / Fin). */
function ddEdge(last) {
  const n = DD.opts.length;
  for (let c = 0; c < n; c++) {
    const i = last ? n - 1 - c : c;
    if (!DD.opts[i].classList.contains("is-off")) return i;
  }
  return 0;
}

function ddKey(e, wrap) {
  const k = e.key, open = DD.wrap === wrap;
  if (!open) {
    if (["ArrowDown", "ArrowUp", "Enter", " ", "Home", "End"].includes(k)) {
      e.preventDefault();
      ddOpen(wrap, false);
      if (k === "ArrowUp" || k === "End") ddMark(ddEdge(k === "End"));
    }
    return;
  }
  if (k === "ArrowDown") { e.preventDefault(); ddMark(ddStep(DD.idx, 1)); }
  else if (k === "ArrowUp") { e.preventDefault(); ddMark(ddStep(DD.idx, -1)); }
  else if (k === "Home") { e.preventDefault(); ddMark(ddEdge(false)); }
  else if (k === "End") { e.preventDefault(); ddMark(ddEdge(true)); }
  else if (k === "Enter" || k === " ") { e.preventDefault(); if (DD.opts[DD.idx] && !DD.opts[DD.idx].classList.contains("is-off")) ddPick(wrap, DD.idx); }
  else if (k === "Escape") { e.preventDefault(); ddClose(true); }
  else if (k === "Tab") ddClose(false);
}

function ddPick(wrap, i) {
  const sel = wrap.dd.sel;
  const opt = sel.options[i];
  if (opt && opt.disabled) { ddClose(true); return; }   // no compatible: no se elige
  if (i >= 0 && i < sel.options.length && i !== sel.selectedIndex) {
    sel.selectedIndex = i;
    sel.dispatchEvent(new Event("change", { bubbles: true }));  // como el usuario
  }
  ddLabel(wrap);
  ddClose(true);
}

function ddClose(refocus) {
  if (!DD.wrap) return;
  DD.menu.hidden = true;
  DD.menu.innerHTML = "";
  DD.opts = [];
  const btn = DD.wrap.dd.btn;
  btn.setAttribute("aria-expanded", "false");
  btn.removeAttribute("aria-activedescendant");
  DD.wrap = null;
  if (refocus && !btn.hasAttribute("disabled")) btn.focus();
}

/* app.js rellena los <select> con fillSelect() sin disparar `change`; se envuelve
   (sin modificarla) para que la etiqueta del botón no se quede atrás. */
const fillSelectRaw = window.fillSelect;
if (typeof fillSelectRaw === "function") {
  window.fillSelect = function (...a) {
    const r = fillSelectRaw.apply(this, a);
    ddSync();
    return r;
  };
}

ddInit();

/* ---------------- arranque ---------------- */
function merge(s) {
  if (!s) return false;
  /* El medidor de entrada tiene su propio camino: aquí se le pasa el nivel más
     reciente, para que se pinte aunque su sondeo rápido esté parado. */
  if ("rms" in s) {
    micLive.rms = Number(s.rms) || 0;
    micLive.thr = Number(s.thr) || 0;
    micLive.voice = !!s.voice;
    micLive.has = true;
  }
  /* Campos VOLÁTILES: la energía por bandas (levels) y los RMS de las pistas
     cambian en cada sondeo. No entran en `state` —dispararían un repintado
     completo varias veces por segundo—; van directos a las pistas vivas, que se
     pintan por frame. */
  if ("levels" in s) { liveLevels = s.levels || null; delete s.levels; }
  if (s.meeting && typeof s.meeting === "object") {
    /* El backend manda las bandas también dentro de `meeting`: se usan como
       respaldo y se apartan del estado por lo mismo (cambian en cada sondeo). */
    if (s.meeting.levels && !liveLevels) liveLevels = s.meeting.levels;
    delete s.meeting.levels;
    liveScalars.sys = Number(s.meeting.level_sys) || 0;
    liveScalars.mic = Number(s.meeting.level_mic) || 0;
    delete s.meeting.level_sys;
    delete s.meeting.level_mic;
  }
  if (s.mic_test && typeof s.mic_test === "object") {
    liveScalars.probe = Number(s.mic_test.level) || 0;
    liveScalars.probePeak = Number(s.mic_test.peak) || 0;
    delete s.mic_test.level;
    delete s.mic_test.peak;
  }
  let changed = false;
  for (const k of Object.keys(s)) {
    if (JSON.stringify(s[k]) !== JSON.stringify(state[k])) { state[k] = s[k]; changed = true; }
  }
  return changed;
}

/* Sondeo: 800 ms en reposo (solo con la ventana al frente) y 150 ms mientras hay
   algo capturando —aunque la ventana no tenga el foco—, para que las pistas
   vivas vayan al día. El repintado completo solo ocurre cuando el estado cambia
   de verdad: la energía entra por su propio camino (merge la aparta antes). */
const POLL_IDLE = 800, POLL_LIVE = 150;

function vizLive() {
  return !!((state.meeting || {}).active) || !!((state.mic_test || {}).active);
}

async function poll() {
  const live = vizLive();
  if (live || document.hasFocus()) {
    const s = await getState();
    if (s) { if (merge(s)) paint(); else paintLevels(); }
  }
  gpuTick();                                     // estado «aplicando» de la tarjeta
  setTimeout(poll, live ? POLL_LIVE : POLL_IDLE);
}

async function boot() {
  paintIcons();                         /* iconos SVG en línea */
  showSection("dictado");               /* raíl: sección inicial */
  vizSyncPalette();                     /* colores de las pistas vivas */
  wire();
  paint();
  if (merge(await getState())) paint();
  poll();
  micPoll();                                  // el medidor de entrada, en vivo
  micRaf = requestAnimationFrame(micFrame);
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", boot);
} else {
  boot();
}