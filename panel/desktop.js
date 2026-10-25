/* dicta — barra de ventana INTEGRADA (backend WebView2 / pywebview).
 *
 * La ventana del panel es sin marco (frameless): no hay barra de Windows. Este
 * fichero lo INYECTA el backend al terminar de cargar la página
 * (window.events.loaded -> <script src="/panel/desktop.js">) cuando el panel
 * se abre con pywebview. Con el backend de Chrome NO se inyecta: allí manda la
 * barra nativa.
 *
 * Qué hace, en cuatro pasos:
 *   1. Reserva el alto de la barra (--dtbar-h): así el contenido empieza
 *      donde empieza el raíl, sin huecos. (La regla que ocultaba la cabecera
 *      `.app-head` se retiró: la cabecera ya no existe.)
 *   2. Dibuja la barra: el nombre «Dicta» y los botones
 *      minimizar/maximizar/cerrar, con los tokens del panel, así sigue el tema
 *      claro/oscuro solo.
 *   3. La barra NO lleva icono de marca, pil de estado ni enlace «Actualizar»:
 *      el icono se retiró del panel entero. Solo «Dicta», el hueco de arrastre
 *      y los botones.
 *   4. Habla con el backend por `window.pywebview.api`: los métodos
 *      minimize() / restore() / maximize() / close() / isMaximized().
 *   5. REDIMENSIONADO: ocho tiras invisibles en los bordes del viewport piden
 *      al backend el tamaño nativo por ese borde (ver `buildResizeEdges`).
 *
 * En la barra: «Dicta», el hueco de arrastre y los botones de ventana. No
 * hay icono (se retiró), ni título/subtítulo ni selector de tema: el tema se
 * elige en Apariencia.
 *
 * El ARRASTRE: los elementos llevan la clase `pywebview-drag-region`
 * (`webview.DRAG_REGION_SELECTOR`) como marca de zona, pero quien mueve la
 * ventana es dicta: al pulsar, la barra llama `pywebview.api.drag_window()` y el
 * backend sigue al cursor con un bucle de Win32. (El puente de arrastre de
 * pywebview, `pywebviewMoveWindow`, no mueve la ventana en este montaje: la
 * llamada llega y `window.move()` no hace nada.) Solo el nombre y el hueco
 * central arrastran — nunca los botones ni la pil, o pulsarlos movería.
 *
 * No toca la lógica de app.js: reubica la pil (un nodo) y crea su propia barra;
 * si la página se recarga, se sustituye a sí misma (idempotente).
 */
(function () {
  'use strict';
  if (window.__dictaDesktopBar) return;      // ya está puesta
  window.__dictaDesktopBar = true;

  var BAR_H = 36;                             // alto de la barra, en px
  var DRAG = 'pywebview-drag-region';         // clase de arrastre de pywebview
  var APP_NAME = 'Dicta';                     // el nombre, con D mayúscula
  document.documentElement.classList.add('dt-desktop');

  function api() {
    return (window.pywebview && window.pywebview.api) || null;
  }

  // La API de pywebview solo está lista tras el evento `pywebviewready`.
  function withApi(fn) {
    var a = api();
    if (a && typeof a.minimize === 'function') {
      try { fn(a); } catch (e) { /* el backend no está: no rompemos la página */ }
      return;
    }
    window.addEventListener('pywebviewready', function () { withApi(fn); },
                            { once: true });
  }

  /* ---------------------------------------------------------- 1. espacio */
  function reserveHeight() {
    var s = document.createElement('style');
    s.id = 'dicta-desktop-css';
    s.textContent = [
      ':root{--dtbar-h:' + BAR_H + 'px}',
      // El hueco de la barra va DENTRO del shell, no como padding del body:
      // con el padding en el body el documento ganaba 36 px de recorrido y el
      // foco del <select> desplazaba la ventana entera hacia arriba.
      'body{padding-top:0;box-sizing:border-box}',
      '.shell{height:100vh;height:100dvh;',
      'padding-top:var(--dtbar-h);box-sizing:border-box}',
      // (La regla que ocultaba `.app-head` se retiró: la cabecera ya no
      // existe en el HTML.)

      '.dtbar{position:fixed;top:0;left:0;right:0;height:var(--dtbar-h);',
      'z-index:60;display:flex;align-items:stretch;gap:2px;',
      'padding-left:var(--sp-3,12px);',
      'background:var(--bg,var(--background,#F2F2F5));',
      'color:var(--text,var(--foreground,#1D1D1F));',
      'box-shadow:0 1px 0 var(--line-2,var(--border,rgba(0,0,0,.06))),' +
        '0 1px 3px rgba(0,0,0,.04);',
      'font-family:var(--fn-ui,"Segoe UI Variable Text","Segoe UI",' +
        'system-ui,sans-serif);',
      'font-size:var(--fs-secondary,12px);user-select:none}',
      '.dtbar-title{display:flex;align-items:center;font-weight:600;',
      'letter-spacing:-.01em;',
      'color:var(--text,var(--foreground,#1D1D1F));white-space:nowrap}',
      // El hueco flexible (.dtbar-drag) ocupa todo el centro de la barra: es la
      // zona de arrastre. Ya no hay pil de estado ni enlace «Actualizar».
      '.dtbar-drag{flex:1 1 auto;min-width:24px}',

      '.dtbar-btns{display:flex;align-items:stretch;margin-left:var(--sp-2,8px)}',
      '.dtbtn{width:46px;height:100%;border:0;background:transparent;color:inherit;',
      'display:flex;align-items:center;justify-content:center;cursor:default;',
      'transition:background var(--t-micro,120ms) var(--ease-out,ease-out),',
      'color var(--t-micro,120ms) var(--ease-out,ease-out)}',
      '.dtbtn:hover{background:' +
        'color-mix(in srgb,var(--text,var(--foreground,#1D1D1F)) 8%,transparent)}',
      '.dtbtn:active{background:' +
        'color-mix(in srgb,var(--text,var(--foreground,#1D1D1F)) 14%,transparent)}',
      '.dtbtn:focus-visible{outline:2px solid ' +
        'var(--ring,var(--accent,#0066CC));outline-offset:-2px}',
      '.dtbtn-close:hover{background:' +
        'var(--err,var(--destructive,#D70015));color:#fff}',
      '.dtbtn-close:active{background:' +
        'color-mix(in srgb,var(--err,var(--destructive,#D70015)) 80%,#000)}',
      // El 2º icono del botón maximizar solo aparece cuando está maximizada.
      '.dtbtn[data-cmd="maximize"] .ico-restore{display:none}',
      '.dtbtn[data-cmd="maximize"].is-max .ico-max{display:none}',
      '.dtbtn[data-cmd="maximize"].is-max .ico-restore{display:block}',
      // Borde de toda la ventana: una capa fija por encima del contenido. El
      // color sale del texto del tema (oscuro en claro, claro en oscuro), así
      // contrasta con apps del mismo color sin ser una línea dura.
      '.dtframe{position:fixed;inset:0;z-index:2147483647;',
      'pointer-events:none;box-sizing:border-box;',
      'border:1px solid rgba(128,128,128,.35);',
      'border-color:color-mix(in srgb,',
      'var(--text,var(--foreground,#808080)) 22%,transparent);',
      'border-radius:8px}',
      '.dt-max .dtframe{border-radius:0}'
    ].join('');
    document.head.appendChild(s);
  }

  /* ------------------------------------------------------------ 2. barra */
  function svg(paths) {
    return '<svg viewBox="0 0 16 16" width="12" height="12" fill="none" ' +
           'stroke="currentColor" stroke-width="1.4" stroke-linecap="round" ' +
           'stroke-linejoin="round" aria-hidden="true">' + paths + '</svg>';
  }

  /* Arrastre: pywebview trae el suyo para la clase `pywebview-drag-region`
     (manejador en document.body), pero en este montaje su puente no mueve la
     ventana (medido: la llamada llega al backend y `window.move()` no hace
     nada). Así que la barra pide el arrastre por la API
     (`pywebview.api.drag_window()`) y lo lleva dicta con el bucle clásico de
     Win32. Se corta la propagación del mousedown para que el manejador de
     pywebview no interfiera: un solo movedor. La clase se queda puesta en los
     mismos elementos como marca de la zona de arrastre. */
  function hookDrag(el) {
    el.addEventListener('mousedown', function (e) {
      if (e.button !== 0) return;
      e.preventDefault();
      e.stopPropagation();
      withApi(function (a) {
        if (typeof a.drag_window === 'function') a.drag_window();
      });
    });
  }

  function buildBar() {
    var bar = document.createElement('div');
    bar.className = 'dtbar';
    bar.id = 'dtbar';

    var title = document.createElement('span');
    title.className = 'dtbar-title ' + DRAG;      // zona de arrastre
    title.textContent = APP_NAME;

    var drag = document.createElement('span');
    drag.className = 'dtbar-drag ' + DRAG;        // el resto del hueco arrastra
    hookDrag(title);
    hookDrag(drag);

    var btns = document.createElement('div');
    btns.className = 'dtbar-btns';

    function button(cmd, label, paths) {
      var b = document.createElement('button');
      b.type = 'button';
      b.className = 'dtbtn' + (cmd === 'close' ? ' dtbtn-close' : '');
      b.dataset.cmd = cmd;
      b.title = label;
      b.setAttribute('aria-label', label);
      b.innerHTML = svg(paths);
      b.addEventListener('click', function (e) {
        e.preventDefault();
        e.stopPropagation();
        withApi(function (a) {
          if (cmd === 'maximize') {
            a.maximize().then(syncMaximize, syncMaximize);
          } else if (typeof a[cmd] === 'function') {
            a[cmd]();
          }
        });
      });
      btns.appendChild(b);
      return b;
    }

    button('minimize', 'Minimizar', '<path d="M3.5 8.5h9"/>');
    button('maximize', 'Maximizar',
           '<rect class="ico-max" x="4" y="4" width="8" height="8" rx="1"/>' +
           '<path class="ico-restore" d="M6 6V4.5h7.5V12H12"/>' +
           '<rect class="ico-restore" x="4" y="6" width="6.5" height="6.5" ' +
           'rx="1"/>');
    button('close', 'Cerrar',
           '<path d="M4.5 4.5l7 7M11.5 4.5l-7 7"/>');

    bar.appendChild(title);
    // El hueco flexible ocupa TODO el centro de la barra: es la zona de
    // arrastre grande. (El icono de la marca, la pil de estado y el enlace
    // «Actualizar» se retiraron: la barra solo lleva «Dicta» + botones.)
    bar.appendChild(drag);
    bar.appendChild(btns);
    document.body.appendChild(bar);

    // El icono del botón maximizar tiene que decir lo que hará ahora.
    withApi(function () { syncMaximize(); });
    return bar;
  }

  function syncMaximize() {
    withApi(function (a) {
      var b = document.querySelector('.dtbtn[data-cmd="maximize"]');
      if (!b || typeof a.isMaximized !== 'function') return;
      try {
        var p = a.isMaximized();
        if (p && typeof p.then === 'function') {
          p.then(function (v) {
            b.classList.toggle('is-max', !!v);
            document.documentElement.classList.toggle('dt-max', !!v);
          }, function () {});
        }
      } catch (e) { /* sin backend: el icono se queda con el de maximizar */ }
    });
  }

  function buildFrame() {
    var f = document.createElement('div');
    f.className = 'dtframe';
    f.setAttribute('aria-hidden', 'true');
    document.body.appendChild(f);
  }

  /* ------------------------------------------ 5. bordes de redimensionado */
  /* La ventana es SIN MARCO: Windows no dibuja la franja de redimensionado y,
     además, el control de WebView2 cubre TODO el cliente (medido con
     WindowFromPoint: en cualquier borde devuelve el hijo
     `Chrome_RenderWidgetHostHWND`, nunca el form), así que el form nunca recibe
     WM_NCHITTEST y no hay bordes nativos que agarrar. Estas tiras INVISIBLES
     (6 px) en los ocho bordes del viewport recogen el `mousedown` y piden al
     backend el redimensionado NATIVO por ese borde
     (`pywebview.api.resize_window(edge)`), que arranca el bucle de tamaño de
     Windows tal cual (respeta el mínimo de 800x520). El CURSOR lo pone el CSS
     (`n-resize`/`e-resize`/`nwse-resize`…), así que «se ve» como cualquier
     ventana. Son `position:fixed` y no entran en el flujo: NO tocan la
     maquetación (mismo raíl, mismas filas, mismos tokens). */
  function buildResizeEdges() {
    var EDGE = 6;                            // grosor sensible del borde, en px
    var strips = [
      // esquinas y bordes comparten z-index: las esquinas se añaden DESPUÉS,
      // así que en la esquina manda la esquina (gana el último en el DOM).
      ['top',         'n-resize',  'left:0;right:0;top:0;height:' + EDGE + 'px'],
      ['bottom',      's-resize',  'left:0;right:0;bottom:0;height:' + EDGE + 'px'],
      ['left',        'w-resize',  'left:0;top:0;bottom:0;width:' + EDGE + 'px'],
      ['right',       'e-resize',  'right:0;top:0;bottom:0;width:' + EDGE + 'px'],
      ['topleft',     'nw-resize', 'left:0;top:0;width:' + EDGE + 'px;height:' + EDGE + 'px'],
      ['topright',    'ne-resize', 'right:0;top:0;width:' + EDGE + 'px;height:' + EDGE + 'px'],
      ['bottomleft',  'sw-resize', 'left:0;bottom:0;width:' + EDGE + 'px;height:' + EDGE + 'px'],
      ['bottomright', 'se-resize', 'right:0;bottom:0;width:' + EDGE + 'px;height:' + EDGE + 'px']
    ];
    var s = document.createElement('style');
    s.id = 'dicta-resize-css';
    // z-index por ENCIMA de la barra (60): el borde SUPERIOR tiene que poder
    // agarrarse aunque la barra ocupe todo el ancho de arriba — como en
    // Windows, donde el filo de arriba de la barra de título redimensiona.
    s.textContent = '.dtresize{position:fixed;z-index:70;user-select:none}';
    document.head.appendChild(s);
    strips.forEach(function (e) {
      var d = document.createElement('div');
      d.className = 'dtresize';
      d.dataset.edge = e[0];
      d.style.cssText = e[2] + ';cursor:' + e[1];
      d.addEventListener('mousedown', function (ev) {
        if (ev.button !== 0) return;
        ev.preventDefault();
        ev.stopPropagation();      // que no lo tome el arrastre de la barra
        var edge = d.dataset.edge;
        withApi(function (a) {
          if (typeof a.resize_window === 'function') a.resize_window(edge);
        });
      });
      document.body.appendChild(d);
    });
  }

  reserveHeight();
  if (document.body) {
    buildBar();
    buildResizeEdges();
    buildFrame();
  } else {
    document.addEventListener('DOMContentLoaded', function () {
      buildBar();
      buildResizeEdges();
      buildFrame();
    }, { once: true });
  }
})();
