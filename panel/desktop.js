/* dicta — barra de ventana INTEGRADA (backend WebView2 / pywebview).
 *
 * La ventana del panel es sin marco (frameless): no hay barra de Windows. Este
 * fichero lo INYECTA el backend al terminar de cargar la página
 * (window.events.loaded -> <script src="/panel/desktop.js">) cuando el panel
 * se abre con pywebview. Con el backend de Chrome NO se inyecta: allí manda la
 * barra nativa.
 *
 * Qué hace, en cuatro pasos:
 *   1. Reserva el alto de la barra (--dtbar-h) y OCULTA la cabecera del panel
 *      (.app-head), que la barra sustituye: así el contenido empieza donde
 *      empieza el raíl, sin huecos.
 *   2. Dibuja la barra: la onda de la marca, el nombre «Dicta» y los botones
 *      minimizar/maximizar/cerrar, con los tokens del panel, así sigue el tema
 *      claro/oscuro solo.
 *   3. La barra NO lleva pil de estado ni enlace «Actualizar»: ambos se
 *      eliminaron. Solo el icono, «Dicta», el hueco de arrastre y los botones.
 *   4. Habla con el backend por `window.pywebview.api`: los métodos
 *      minimize() / restore() / maximize() / close() / isMaximized().
 *   5. REDIMENSIONADO: ocho tiras invisibles en los bordes del viewport piden
 *      al backend el tamaño nativo por ese borde (ver `buildResizeEdges`).
 *
 * En la barra: ICONO de la app, «Dicta», la PIL de estado (izquierda), el hueco
 * de arrastre, el enlace «Actualizar» (derecha) y los botones de ventana. No hay
 * título/subtítulo ni selector de tema: el tema se elige en Apariencia.
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
  var ICON_CSS = 18;                          // icono de la barra, en px CSS
  var ICON_VER = '1';                         // invalida la caché si cambia
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
      'body{padding-top:var(--dtbar-h);box-sizing:border-box}',
      '.shell{height:calc(100vh - var(--dtbar-h));',
      'height:calc(100dvh - var(--dtbar-h))}',
      // La barra sustituye a la cabecera: sin ocultarla, el contenido
      // empezaría tras el hueco de la cabecera (un hueco visible).
      '.dt-desktop .app-head{display:none}',

      '.dtbar{position:fixed;top:0;left:0;right:0;height:var(--dtbar-h);',
      'z-index:60;display:flex;align-items:stretch;gap:2px;',
      'padding-left:var(--sp-3,12px);background:var(--bg);color:var(--text);',
      'box-shadow:0 1px 0 var(--line-2),0 1px 3px rgba(0,0,0,.04);',
      'font-family:var(--fn-ui,"Segoe UI",system-ui,sans-serif);',
      'font-size:var(--fs-secondary,12px);user-select:none}',

      '.dtbar-brand{display:flex;align-items:center;color:var(--accent);',
      'padding-right:var(--sp-2,8px)}',
      // El icono es el PNG REAL de la app (el mismo render que la bandeja y
      // el .exe), servido por la propia app en /panel/icon.png.
      '.dtbar-icon{display:block;width:' + ICON_CSS + 'px;height:' + ICON_CSS +
        'px;flex:0 0 auto}',
      '.dtbar-title{display:flex;align-items:center;font-weight:600;',
      'letter-spacing:-.01em;color:var(--text);white-space:nowrap}',
      // El hueco flexible (.dtbar-drag) ocupa todo el centro de la barra: es la
      // zona de arrastre. Ya no hay pil de estado ni enlace «Actualizar».
      '.dtbar-drag{flex:1 1 auto;min-width:24px}',

      '.dtbar-btns{display:flex;align-items:stretch;margin-left:var(--sp-2,8px)}',
      '.dtbtn{width:46px;height:100%;border:0;background:transparent;color:inherit;',
      'display:flex;align-items:center;justify-content:center;cursor:default;',
      'transition:background var(--t-micro,120ms) var(--ease-out,ease-out),',
      'color var(--t-micro,120ms) var(--ease-out,ease-out)}',
      '.dtbtn:hover{background:' +
        'color-mix(in srgb,var(--text) 8%,transparent)}',
      '.dtbtn:active{background:color-mix(in srgb,var(--text) 14%,transparent)}',
      '.dtbtn:focus-visible{outline:2px solid var(--accent);outline-offset:-2px}',
      '.dtbtn-close:hover{background:var(--err);color:#fff}',
      '.dtbtn-close:active{background:color-mix(in srgb,var(--err) 80%,#000)}',
      // El 2º icono del botón maximizar solo aparece cuando está maximizada.
      '.dtbtn[data-cmd="maximize"] .ico-restore{display:none}',
      '.dtbtn[data-cmd="maximize"].is-max .ico-max{display:none}',
      '.dtbtn[data-cmd="maximize"].is-max .ico-restore{display:block}'
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

    // El icono de la app: el MISMO dibujo de la bandeja y del .exe, servido
    // por la app en /panel/icon.png (PNG del render real, no un SVG aparte).
    // Se pide al doble del tamaño lógico en pantallas con escalado
    // (devicePixelRatio) para que quede nítido al reducir.
    var brand = document.createElement('span');
    brand.className = 'dtbar-brand';
    var dpr = Math.min(2, Math.max(1, window.devicePixelRatio || 1));
    var iconPx = Math.round(ICON_CSS * dpr);

    function currentTheme() {
      return document.documentElement.getAttribute('data-theme') === 'light'
        ? 'light' : 'dark';
    }
    function iconURL(theme) {
      return '/panel/icon.png?size=' + iconPx + '&theme=' + theme +
        '&v=' + ICON_VER;
    }

    var img = document.createElement('img');
    img.className = 'dtbar-icon';
    img.width = ICON_CSS;
    img.height = ICON_CSS;
    img.alt = '';
    img.setAttribute('aria-hidden', 'true');
    img.dataset.theme = currentTheme();
    img.src = iconURL(img.dataset.theme);
    // Si el PNG no llegara (backend raro), no dejamos un hueco: se cae al
    // dibujo de respaldo en SVG.
    img.addEventListener('error', function () {
      brand.innerHTML = '<svg viewBox="0 0 24 24" width="15" height="15" ' +
        'fill="none" stroke="currentColor" stroke-width="1.8" ' +
        'stroke-linecap="round" aria-hidden="true">' +
        '<path d="M3 12h2M7 8v8M11 5v14M15 9v6M19 11v2"/></svg>';
    });
    // El icono de la bandeja sigue al tema; el de la barra también (si no,
    // en tema claro se quedaría con el azulejo oscuro).
    if (window.MutationObserver) {
      new MutationObserver(function () {
        var t = currentTheme();
        if (img.dataset.theme !== t && img.parentNode === brand) {
          img.dataset.theme = t;
          img.src = iconURL(t);
        }
      }).observe(document.documentElement, {
        attributes: true, attributeFilter: ['data-theme']});
    }
    brand.appendChild(img);

    /* La versión del icono la publica la app en `/state.icon_version`: al llevarla
       en la URL, el navegador no puede servir un PNG cacheado del dibujo viejo
       (el mismo icono que la barra de Windows y que el favicon). app.js avisa por
       evento cuando cambia; si el aviso aún no ha llegado, se pide una vez. */
    function applyIconVersion(v) {
      var ver = String(v || '1');
      if (!ver || ver === ICON_VER) return;
      ICON_VER = ver;
      if (img.parentNode === brand) img.src = iconURL(img.dataset.theme);
    }
    document.addEventListener('dicta-icon-version', function (ev) {
      applyIconVersion(ev && ev.detail);
    });
    try {
      fetch('/state', { cache: 'no-store' })
        .then(function (r) { return r.json(); })
        .then(function (s) { if (s) applyIconVersion(s.icon_version); })
        .catch(function () {});
    } catch (e) { /* sin fetch: se queda la versión por defecto */ }

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

    bar.appendChild(brand);
    bar.appendChild(title);
    // El hueco flexible ocupa TODO el centro de la barra: es la zona de
    // arrastre grande. (La pil de estado se ELIMINÓ y el enlace «Actualizar» se
    // retiró: la barra ya solo lleva icono + «Dicta» + botones de ventana.)
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
          p.then(function (v) { b.classList.toggle('is-max', !!v); },
                 function () {});
        }
      } catch (e) { /* sin backend: el icono se queda con el de maximizar */ }
    });
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
  } else {
    document.addEventListener('DOMContentLoaded', function () {
      buildBar();
      buildResizeEdges();
    }, { once: true });
  }
})();
