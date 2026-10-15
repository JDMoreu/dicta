# Historial de versiones — dicta

**dicta** es un dictado por voz y transcripción de reuniones que funciona
**100 % en tu equipo**: el audio y el texto nunca salen de tu ordenador.

Aquí tienes, **de la versión más nueva a la más antigua**, qué cambió en cada
una, por qué y qué se solucionó. Cada versión publicada en GitHub conserva su
paquete portable descargable, así que siempre puedes volver a una anterior.

- **Última versión publicada:** v1.0.1
- **Cómo se usa:** descarga el ZIP portable de la release, descomprímelo y abre
  `dicta.exe`. No hace falta instalar Python, ni Chrome, ni nada más.

---

## v1.0.1 — 15 de octubre de 2026

**Pegado automático dentro de las terminales.**

**Qué cambió**

- Ahora dicta **mira qué ventana tiene el foco** y pega con la combinación
  correcta según el programa:
  - **Windows Terminal, VS Code, JetBrains, mintty, WezTerm** → `Ctrl+Shift+V`.
  - **Consola clásica** (cmd/PowerShell en su propia ventana) → `Ctrl+V`, que
    ahí sí funciona.
  - **Cualquier otra aplicación** → `Ctrl+V`, como siempre.
  - Si no reconoce la ventana, usa `Shift+Insert`, que cubre la mayoría.
- Se añade el ajuste **`paste_mode`** en la configuración, por si alguna
  terminal concreta se resiste: `auto` (por defecto, detecta sola), `ctrl+v`,
  `ctrl+shift+v` o `shift+insert`.
- Se publica el paquete **portable 1.0.1** con todo esto ya incluido dentro del
  `.exe` (sin instalar nada aparte).

**Por qué**

Si dictabas dentro de una terminal, el texto **no aparecía**: dicta pegaba
siempre con `Ctrl+V`, y la terminal se queda esa combinación para sí misma, así
que había que dar `Ctrl+Shift+V` a mano. La combinación correcta depende del
programa que muestra la terminal, no del que corre dentro.

**Qué se solucionó**

- El texto dictado ya llega solo **dentro de las terminales**.
- **Arreglo de fondo:** la función que trae al frente la ventana de destino no
  se estaba ejecutando (un error silenciado), así que a veces el texto podía
  caer en el sitio equivocado. Ya funciona.

> Si usabas la v1.0.0 y dictas solo en aplicaciones normales (chat, documentos,
> correo), este fallo no te afectaba: la v1.0.0 te sirve igual.

---

## v1.0.0 — 15 de octubre de 2026

**Primera versión pública.**

**Qué cambió**

- Primer paquete **portable autónomo**: un ZIP que trae la aplicación, el motor
  de transcripción, las bibliotecas y un modelo de voz listo para usar, de modo
  que **transcribe desde el primer arranque**.
- **Sin instalar nada**: no necesita Python ni Chrome. La ventana de la
  aplicación usa el WebView2 que ya viene con Windows.
- **Sin permisos de administrador**: arranca y funciona sin pedir UAC.
- La app instala su propia configuración de arranque (`dicta.exe.config`) si
  falta, para que abra la ventana correctamente aunque se copie sola.

**Por qué**

Era la primera entrega para que cualquiera pudiera probarla sin montar un
entorno de desarrollo: un solo fichero, se descomprime y funciona.

**Qué se solucionó**

- El ejecutable compilado **arrancaba, pero la ventana no se abría** con su
  interfaz integrada (caía al navegador). La causa era que .NET se negaba a
  cargar una biblioteca desde un fichero marcado como «de internet» (lo que
  Windows hace con lo que se descomprime de un ZIP descargado). Se resolvió
  incluyendo en el paquete el fichero de configuración que lo permite, así que
  **le funciona igual a quien se descarga la release**, no solo en este equipo.
- El ejecutable pedía permisos de administrador y **ni siquiera abría** desde un
  proceso sin elevar. Ahora arranca normal.

---

## Próxima versión — en preparación

Todavía **sin publicar**. Esto es lo que ya está hecho y entrará en la próxima
release:

**Pegado automático que funciona en los agentes de terminal y en Terax.**

- **Mecanismo de pegado elegido según el destino**, en vez de una sola
  combinación:
  - **Consolas reales** → se escribe directamente en el **búfer de entrada** de
    la consola (lo que leen las interfaces de texto), y **llega aunque la
    ventana no tenga el foco**.
  - **Ventanas Chromium/Electron con terminal integrada** (Hermes, OpenCode,
    Cursor, y agentes como Claude/Codex…) → el texto se **teclea como entrada
    real**, que entra en cualquier xterm.js.
  - **Emuladores de terminal** → `Ctrl+Shift+V`; **apps normales** → `Ctrl+V`
    (sin cambios).
  - Último recurso: envío posteado a la ventana.
  - Se añade el modo forzado **`type`** a `paste_mode` (teclear el texto, sin
    depender de la combinación ni del portapapeles).
- **Terax** (terminal hecho con Tauri + WebView2, el que usa el autor con `pi`)
  se detecta y se pega **tecleando** el texto, que es lo único que entra en su
  xterm.js. Antes caía a `Ctrl+V` y no llegaba nada.

**Comprobación de actualizaciones desde la propia app.**

- La app podrá **avisar cuando haya una versión nueva** publicada, mostrando sus
  notas, y **descargarla y aplicarla** sin tener que ir a GitHub.
- **Nada sale de tu equipo salvo que tú lo actives.** La comprobación viene
  **apagada de fábrica** (ajuste `check_updates`) y se activa desde el panel.
  Cuando está activa, lo único que hace es **una consulta anónima** a la página
  pública de releases de GitHub; **no envía ningún dato tuyo**: ni
  identificadores, ni telemetría, ni el estado de la app. Si está apagada, dicta
  **no abre ninguna conexión** a internet.

---

## Cómo se publica cada versión

- Cada versión se publica en GitHub como una **release** con su paquete portable
  descargable; **las versiones anteriores se conservan**, no se borran, para que
  puedas volver a cualquiera de ellas.
- Las notas de cada release explican, en lenguaje claro, qué cambió y por qué
  (este fichero es el resumen ordenado de todas).
- El registro técnico interno, con el detalle y las medidas de cada cambio, vive
  en `CHANGES.md`.
