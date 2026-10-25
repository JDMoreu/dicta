/* Iconos de dicta: un mapa, un constructor (extraído de panel/app.js). */
const ICONS: Record<string, string> = {
  "mic": "<rect x=\"9\" y=\"2.5\" width=\"6\" height=\"11\" rx=\"3\"/><path d=\"M5.5 11a6.5 6.5 0 0 0 13 0\"/><path d=\"M12 17.5V21M8.5 21h7\"/>",
  "mic-off": "<path d=\"M15 5.5v-1a3 3 0 0 0-6 0v7M9 12.4a3 3 0 0 0 4.7 2.1\"/><path d=\"M5.5 11a6.5 6.5 0 0 0 9.9 5.6M12 17.5V21M8.5 21h7M3.5 3.5l17 17\"/>",
  "globe": "<circle cx=\"12\" cy=\"12\" r=\"9\"/><path d=\"M3 12h18\"/><path d=\"M12 3c2.6 2.5 3.9 5.5 3.9 9s-1.3 6.5-3.9 9c-2.6-2.5-3.9-5.5-3.9-9S9.4 5.5 12 3z\"/>",
  "chip": "<rect x=\"6.5\" y=\"6.5\" width=\"11\" height=\"11\" rx=\"2.5\"/><path d=\"M10 10h4v4h-4z\"/><path d=\"M10 2.5v4M14 2.5v4M10 17.5v4M14 17.5v4M2.5 10h4M2.5 14h4M17.5 10h4M17.5 14h4\"/>",
  "layers": "<path d=\"M12 2.8l8.4 4.3L12 11.4 3.6 7.1 12 2.8z\"/><path d=\"M3.6 12.1L12 16.4l8.4-4.3\"/><path d=\"M3.6 16.7L12 21l8.4-4.3\"/>",
  "gpu": "<rect x=\"4\" y=\"5.6\" width=\"16\" height=\"12.8\" rx=\"2.6\"/><circle cx=\"9.8\" cy=\"12\" r=\"2.5\"/><path d=\"M14.6 10.2h3M14.6 13.8h3\"/>",
  "gauge": "<path d=\"M3.5 17.5a9 9 0 1 1 17 0\"/><path d=\"M12 17.5l4.2-6.4\"/><circle cx=\"12\" cy=\"17.5\" r=\"1.1\"/>",
  "timer": "<circle cx=\"12\" cy=\"13.5\" r=\"7.5\"/><path d=\"M12 13.5l3.2-2.2\"/><path d=\"M9 2.5h6\"/><path d=\"M12 2.5V6\"/>",
  "speaker": "<path d=\"M11 4.6L6.6 8.5H3.2v7h3.4L11 19.4z\"/><path d=\"M14.8 9.7a3.4 3.4 0 0 1 0 4.6\"/><path d=\"M17.6 6.9a7.4 7.4 0 0 1 0 10.2\"/>",
  "monitor": "<rect x=\"2.5\" y=\"4\" width=\"19\" height=\"13\" rx=\"2.5\"/><path d=\"M8.5 21h7M12 17v4\"/>",
  "window": "<rect x=\"3\" y=\"4.5\" width=\"18\" height=\"15\" rx=\"2.5\"/><path d=\"M3 8.8h18\"/><path d=\"M6.2 6.7h.01M8.9 6.7h.01\"/>",
  "file-audio": "<path d=\"M13 3.2H7.2a2 2 0 0 0-2 2v13.6a2 2 0 0 0 2 2h9.6a2 2 0 0 0 2-2V9z\"/><path d=\"M13 3.2V9h5.8\"/><path d=\"M10.6 17.4v-3.1l4-.9v3.1\"/><circle cx=\"9.5\" cy=\"17.6\" r=\"1.2\"/><circle cx=\"13.5\" cy=\"16.7\" r=\"1.2\"/>",
  "file-text": "<path d=\"M13 3.2H7.2a2 2 0 0 0-2 2v13.6a2 2 0 0 0 2 2h9.6a2 2 0 0 0 2-2V9z\"/><path d=\"M13 3.2V9h5.8\"/><path d=\"M8.6 13h6.8M8.6 16.6h4.4\"/>",
  "book": "<path d=\"M12 6.6C10.6 5.1 8.8 4.3 6.6 4.3H3.8V19h2.8c2.2 0 4 .8 5.4 2.2 1.4-1.4 3.2-2.2 5.4-2.2h2.8V4.3h-2.8c-2.2 0-4 .8-5.4 2.3z\"/><path d=\"M12 6.6v14.6\"/>",
  "folder": "<path d=\"M3.5 6.6a2 2 0 0 1 2-2h3.1l2 2.5h7.9a2 2 0 0 1 2 2v8.4a2 2 0 0 1-2 2H5.5a2 2 0 0 1-2-2z\"/>",
  "keyboard": "<rect x=\"2.5\" y=\"6\" width=\"19\" height=\"12\" rx=\"2.5\"/><path d=\"M6 9.6h.01M9.4 9.6h.01M12.8 9.6h.01M16.2 9.6h.01M6 13h.01M18 13h.01M9.4 13h5.2\"/>",
  "users": "<circle cx=\"9.2\" cy=\"8\" r=\"3.2\"/><path d=\"M3.2 20a6 6 0 0 1 12 0\"/><path d=\"M16.4 5.3a3.2 3.2 0 0 1 0 5.4\"/><path d=\"M17.8 14.3a6 6 0 0 1 3 5.7\"/>",
  "play": "<path d=\"M7.5 5.2l11 6.8-11 6.8z\"/>",
  "pause": "<path d=\"M9.2 5.5v13M14.8 5.5v13\"/>",
  "stop": "<rect x=\"6.5\" y=\"6.5\" width=\"11\" height=\"11\" rx=\"2.5\"/>",
  "plus": "<path d=\"M12 5v14M5 12h14\"/>",
  "x": "<path d=\"M6 6l12 12M18 6L6 18\"/>",
  "check": "<path d=\"M4.8 12.6l4.8 4.8L19.2 6.8\"/>",
  "trash": "<path d=\"M4.5 6.5h15\"/><path d=\"M9.5 6.5V4.8a1.3 1.3 0 0 1 1.3-1.3h2.4a1.3 1.3 0 0 1 1.3 1.3v1.7\"/><path d=\"M6.5 6.5l1 12.1a1.6 1.6 0 0 0 1.6 1.4h5.8a1.6 1.6 0 0 0 1.6-1.4l1-12.1\"/>",
  "pencil": "<path d=\"M4.6 19.4h3.8L18.9 8.9a1.9 1.9 0 0 0 0-2.7l-1.1-1.1a1.9 1.9 0 0 0-2.7 0L4.6 15.6z\"/><path d=\"M13.5 6.7l3.8 3.8\"/>",
  "download": "<path d=\"M12 3.5v11\"/><path d=\"M7.6 10.4L12 14.8l4.4-4.4\"/><path d=\"M4.5 19.5h15\"/>",
  "upload": "<path d=\"M12 15.5v-11\"/><path d=\"M7.6 9L12 4.6 16.4 9\"/><path d=\"M4.5 19.5h15\"/>",
  "copy": "<rect x=\"8.6\" y=\"8.6\" width=\"11.9\" height=\"11.9\" rx=\"2.5\"/><path d=\"M15.4 5.6v-.8a1.8 1.8 0 0 0-1.8-1.8H5.4a1.8 1.8 0 0 0-1.8 1.8v8.2a1.8 1.8 0 0 0 1.8 1.8h.8\"/>",
  "refresh": "<path d=\"M20 12a8 8 0 1 1-2.5-5.8\"/><path d=\"M20.3 4.4v4.3h-4.3\"/>",
  "search": "<circle cx=\"10.8\" cy=\"10.8\" r=\"6.3\"/><path d=\"M15.4 15.4l4.1 4.1\"/>",
  "sliders": "<path d=\"M4 7.5h9M17.5 7.5H20M4 16.5h2.5M11 16.5h9\"/><circle cx=\"15.2\" cy=\"7.5\" r=\"2.2\"/><circle cx=\"8.7\" cy=\"16.5\" r=\"2.2\"/>",
  "power": "<path d=\"M12 3.5v8\"/><path d=\"M7.3 6.5a7 7 0 1 0 9.4 0\"/>",
  "external-link": "<path d=\"M13.5 4.5h6v6\"/><path d=\"M19.5 4.5L11.2 12.8\"/><path d=\"M17.5 14v4.2a1.8 1.8 0 0 1-1.8 1.8H5.3a1.8 1.8 0 0 1-1.8-1.8V7.8A1.8 1.8 0 0 1 5.3 6h4.2\"/>",
  "zap": "<path d=\"M13.4 3L5.6 13.4h5L10.6 21l7.8-10.4h-5z\"/>",
  "sparkle": "<path d=\"M12 3.4l1.7 4.9 4.9 1.7-4.9 1.7L12 16.6l-1.7-4.9L5.4 10l4.9-1.7z\"/><path d=\"M18.4 16.4l.7 2 2 .7-2 .7-.7 2-.7-2-2-.7 2-.7z\"/>",
  "sun": "<circle cx=\"12\" cy=\"12\" r=\"4.2\"/><path d=\"M12 2.5v2M12 19.5v2M2.5 12h2M19.5 12h2M5.2 5.2l1.4 1.4M17.4 17.4l1.4 1.4M5.2 18.8l1.4-1.4M17.4 6.6l1.4-1.4\"/>",
  "moon": "<path d=\"M20.5 13.4A8.6 8.6 0 0 1 10.6 3.5a8.6 8.6 0 1 0 9.9 9.9z\"/>",
  "chevron-down": "<path d=\"M6 9.5l6 6 6-6\"/>",
  "chevron-right": "<path d=\"M9.5 6l6 6-6 6\"/>",
  "info": "<circle cx=\"12\" cy=\"12\" r=\"9\"/><path d=\"M12 11.2V17M12 7.6h.01\"/>",
  "alert-triangle": "<path d=\"M12 4.2L21 19.6H3z\"/><path d=\"M12 10v4.2M12 17h.01\"/>",
  "dots-h": "<circle cx=\"5.5\" cy=\"12\" r=\"1.3\"/><circle cx=\"12\" cy=\"12\" r=\"1.3\"/><circle cx=\"18.5\" cy=\"12\" r=\"1.3\"/>",
  "dots-v": "<circle cx=\"12\" cy=\"5.5\" r=\"1.3\"/><circle cx=\"12\" cy=\"12\" r=\"1.3\"/><circle cx=\"12\" cy=\"18.5\" r=\"1.3\"/>",
  "settings": "<circle cx=\"12\" cy=\"12\" r=\"3.1\"/><path d=\"M19.4 15a1.7 1.7 0 0 0 .3 1.9l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-2.9 1.2 2 2 0 1 1-4 0 1.7 1.7 0 0 0-2.9-1.2l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1A1.7 1.7 0 0 0 2.1 14a2 2 0 1 1 0-4 1.7 1.7 0 0 0 1.2-2.9l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1A1.7 1.7 0 0 0 9 3.1a2 2 0 1 1 4 0 1.7 1.7 0 0 0 2.9 1.2l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1A1.7 1.7 0 0 0 20 10a2 2 0 1 1 0 4 1.7 1.7 0 0 0-1.2.9z\"/>"
}

export function Icon({ name, size = 18, strokeWidth, className }: { name: string; size?: number; strokeWidth?: number; className?: string }) {
  const body = ICONS[name]
  if (!body) return null
  const sw = strokeWidth ?? (size <= 18 ? 2 : 1.8)
  return (
    <svg viewBox="0 0 24 24" width={size} height={size} fill="none" stroke="currentColor" strokeWidth={sw} strokeLinecap="round" strokeLinejoin="round" aria-hidden focusable="false" className={className} dangerouslySetInnerHTML={{ __html: body }} />
  )
}
