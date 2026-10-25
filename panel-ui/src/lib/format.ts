import type { AppState, EngineOption, Locale, ModelOption } from "./api"
import { I18N } from "./i18n"

export const localeOf = (s: AppState): Locale =>
  s.language === "en" ? "en" : "es"

export function translate(
  locale: Locale,
  key: string,
  vars?: Record<string, string | number>,
) {
  const raw = I18N[locale][key] ?? I18N.es[key] ?? key
  let out = typeof raw === "string" ? raw : String(key)
  if (vars) {
    for (const [k, v] of Object.entries(vars)) {
      out = out.replace(new RegExp(`\\{${k}\\}`, "g"), String(v))
    }
  }
  return out
}

const KEY_NAMES: Record<Locale, Record<string, string>> = {
  es: { alt: "Alt", ctrl: "Ctrl", shift: "Mayús", cmd: "Win" },
  en: { alt: "Alt", ctrl: "Ctrl", shift: "Shift", cmd: "Win" },
}

export function hotkeyPretty(spec: string, locale: Locale) {
  const names = KEY_NAMES[locale]
  return (spec || "")
    .split("+")
    .filter(Boolean)
    .map((k) =>
      k.length === 1 || /^f\d+$/i.test(k) ? k.toUpperCase() : names[k] || k,
    )
    .join(" + ")
}

export const baseName = (p: string | null | undefined) =>
  String(p || "")
    .split(/[\\/]/)
    .pop() || ""

export const extOf = (n: string) =>
  (String(n).match(/\.([a-z0-9]+)$/i) || ["", ""])[1].toLowerCase()

const FILE_EXT =
  /\.(md|markdown|txt|wav|wave|mp3|m4a|m4b|aac|flac|ogg|oga|opus|wma|aif|aiff|amr|caf|mp4|m4v|mkv|mov|webm|avi|wmv|mpg|mpeg|3gp|bin)$/i

export const stripExt = (n: string) => String(n || "").replace(FILE_EXT, "")
export const docStem = (n: string) => stripExt(baseName(n))

export function fmtSize(bytes: number) {
  const b = Number(bytes) || 0
  if (!b) return ""
  if (b >= 1048576) return (b / 1048576).toFixed(1) + " MB"
  return Math.max(1, Math.round(b / 1024)) + " KB"
}

export function fmtTime(sec: number, hours = false) {
  const total = Math.max(0, Math.floor(Number(sec) || 0))
  const h = Math.floor(total / 3600)
  const m = Math.floor((total % 3600) / 60)
  const s = total % 60
  const p2 = (n: number) => String(n).padStart(2, "0")
  if (hours || h > 0) return `${h}:${p2(m)}:${p2(s)}`
  return `${p2(m)}:${p2(s)}`
}

export const hoursOf = (d: number) => (Number(d) || 0) >= 3600

export function verText(v: string | null | undefined) {
  if (!v) return ""
  const parts = String(v).split(".")
  while (parts.length < 3) parts.push("0")
  return "v" + parts.slice(0, 3).join(".")
}

export const MODEL_LABEL: Record<string, string> = {
  tiny: "Whisper Tiny",
  base: "Whisper Base",
  small: "Whisper Small",
  medium: "Whisper Medium",
  turbo: "Whisper Large v3 Turbo",
}

export const LANG_CODES = ["es", "en"]
export const LANG_LABEL: Record<string, string> = {
  es: "Español",
  en: "English",
}


export function modelOptions(state: AppState): { value: string; label: string }[] {
  const out: { value: string; label: string }[] = []
  const seen = new Set<string>()
  const push = (v: string, l?: string) => {
    v = String(v)
    if (!v || seen.has(v)) return
    seen.add(v)
    out.push({ value: v, label: String(l || MODEL_LABEL[v] || v) })
  }
  const list = Array.isArray(state.models) ? state.models : null
  if (list && list.length) {
    list.forEach((it: ModelOption) => {
      if (it && typeof it === "object") {
        const key = String(it.key ?? "")
        push(key, it.name ?? MODEL_LABEL[key] ?? key)
      }
    })
  }
  if (!out.length) {
    Object.keys(MODEL_LABEL).forEach((id) => push(id, MODEL_LABEL[id]))
  }
  if (state.model && !seen.has(String(state.model))) {
    push(state.model, MODEL_LABEL[state.model])
  }
  return out
}

export function engineOptions(state: AppState): EngineOption[] {
  let items: EngineOption[]
  if (Array.isArray(state.engine_options) && state.engine_options.length) {
    items = state.engine_options.map((o) => ({
      ...o,
      available: o.available !== false,
      reason: o.reason || o.note || "",
    }))
  } else {
    const known = Array.isArray(state.engines) ? state.engines : []
    items = ["auto", "vulkan", "cuda", "cpu"].map((k) => ({
      key: k,
      label: k,
      available: !known.length || known.indexOf(k) >= 0,
      reason: "",
    }))
  }
  return items.filter((o) => o.key !== "rocm")
}

export function engineLabel(key: string, locale: Locale, fallback = "") {
  const k = "eng." + key
  const s = translate(locale, k)
  return s === k ? fallback || key : s
}

export function gpuEngine(state: AppState) {
  return (state.engine_options || []).find(
    (o) => o.key === (state.gpu_device_resolved === "auto" ? state.engine : state.engine),
  )
}

export function gpuDevices(state: AppState) {
  const options = state.engine_options || []
  const engine =
    options.find((o) => o.key === state.engine) ||
    options.find((o) => o.key === state.engine_resolved) ||
    options.find((o) => o.key === state.gpu_device_resolved)
  return engine && Array.isArray(engine.devices) ? engine.devices : []
}

export function gpuShortName(name: string) {
  return String(name || "")
    .replace(/\(R\)/gi, "")
    .replace(/\s*\([^)]*driver[^)]*\)/gi, "")
    .replace(/\s{2,}/g, " ")
    .trim()
}

export function meetStopName(state: AppState) {
  const h = state.hotkeys || {}
  if ("meeting_stop" in h) return "meeting_stop"
  if ("meeting_cancel" in h) return "meeting_cancel"
  return "meeting_stop"
}

export function meetStopLabel(state: AppState, locale: Locale) {
  const h = state.hotkeys || {}
  const spec = h.meeting_stop ?? h.meeting_cancel ?? state.meeting_stop_key ?? ""
  return spec ? hotkeyPretty(spec, locale) : ""
}

export const AUDIO_EXT = /^(wav|flac|ogg|oga|opus|mp3|m4a|aac|webm)$/

export const UPLOAD_STATE: Record<
  string,
  { key: string; tone: "wait" | "run" | "ok" | "err" }
> = {
  pendiente: { key: "ui.stPending", tone: "wait" },
  transcribiendo: { key: "ui.statusTranscribing", tone: "run" },
  listo: { key: "ui.saved", tone: "ok" },
  error: { key: "ui.stError", tone: "err" },
}
