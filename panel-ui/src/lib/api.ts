export type Locale = "es" | "en"

export interface EngineOption {
  key: string
  label: string
  available: boolean
  reason?: string
  note?: string
  devices?: { index: number; name: string; desc?: string }[]
}

export interface ModelOption {
  key: string
  name: string
  present?: boolean
}

export interface MicDevice {
  idx: number | string
  name: string
}

export interface SourceOption {
  key: string
  label: string
  playing?: boolean
}

export interface Hotkeys {
  dictation?: string
  cancel?: string
  panel?: string
  meeting?: string
  meeting_stop?: string
  meeting_cancel?: string
}

export interface MicTest {
  active: boolean
  level: number
  peak: number
  done: boolean
  duration: number
  elapsed: number
  peaks: number[]
  silent: boolean
  wav: string | null
  error: string
}

export interface MeetingLevels {
  active: boolean
  sys: number[]
  mic: number[]
  sys_silent: boolean
  mic_silent: boolean
}

export interface Meeting {
  active: boolean
  paused: boolean
  mic_on: boolean
  doc: string | null
  wav: string | null
  status: string
  last: string
  level: number
  level_sys?: number
  level_mic?: number
  db_sys?: number
  db_mic?: number
  mic: string | null
  seconds: number
  levels?: MeetingLevels
}

export interface UpdateInfo {
  available: boolean
  latest: string
  url?: string
  notes?: string
  checked_at?: string
  progress?: number
  enabled?: boolean
  error?: string
  applied?: string
  asset_url?: string
  asset_size?: number
}

export interface UpdateState {
  available: boolean
  latest: string
  url?: string
  notes?: string
  checked_at?: string
  progress?: number
  enabled?: boolean
  error?: string
  applied?: string
  asset_url?: string
  asset_size?: number
}

export interface QueueItem {
  id?: string
  label?: string
  status?: string
  progress?: number
  doc?: string
  src?: string
  key?: string
  duration?: number
  size?: number
}

export interface Upload {
  id?: string
  name: string
  stored?: string
  size?: number
  doc?: string
  duration?: number
  audio?: string
  src?: string
  state?: string
  progress?: number
}

export interface Doc {
  name: string
  size: number
  mtime: number
  audio?: string | null
  audio_size?: number
}

export interface AppState {
  model: string
  engine: string
  engine_resolved?: string
  engines?: string[]
  engine_options?: EngineOption[]
  engine_note?: string
  gpu_device: string
  gpu_device_resolved: string
  gpu_device_note?: string
  models?: ModelOption[]
  language: string
  sens: number
  theme: "light" | "dark"
  theme_mode?: "auto" | "light" | "dark"
  voice_threshold: number
  silence_wait: number
  paste_mode?: string
  paste_modes?: string[]
  rms: number
  thr: number
  voice: boolean
  island_pos: string
  island_palette: string
  mic: number | string
  mics: MicDevice[]
  dictionary: string[]
  sources?: SourceOption[]
  meeting_source: string
  hotkey: string
  cancel_key: string
  panel_key: string
  meeting_key?: string
  meeting_stop_key?: string
  hotkeys?: Hotkeys
  mic_test: MicTest
  meeting_mic: boolean
  status: string
  status_kind: string
  st: string
  version: string
  update: UpdateState
  check_updates: boolean
  start_with_windows?: boolean
  queue: QueueItem[]
  uploads: Upload[] | null
  meeting: Meeting
  levels?: MeetingLevels
  docs: Doc[]
  icon_version?: string
}

export interface RpcResult {
  ok?: boolean
  error?: string
  [key: string]: unknown
}

export async function fetchState(): Promise<AppState | null> {
  try {
    const res = await fetch("/state", { cache: "no-store" })
    if (!res.ok) return null
    return (await res.json()) as AppState
  } catch {
    return null
  }
}

export async function rpcRaw(payload: Record<string, unknown>): Promise<RpcResult> {
  try {
    const res = await fetch("/rpc", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
    return (await res.json()) as RpcResult
  } catch {
    return { ok: false, error: "connection" }
  }
}

export async function rpc(
  action: string,
  value?: unknown,
): Promise<RpcResult> {
  return rpcRaw({ action, value: value === undefined ? null : value })
}

export async function uploadFiles(files: File[]) {
  const fd = new FormData()
  for (const f of files) fd.append("file", f, f.name)
  return fetch("/upload", { method: "POST", body: fd })
}

export async function fetchDoc(name: string): Promise<string | null> {
  for (const nm of [name, name.replace(/\.md$/i, "")]) {
    if (!nm) continue
    try {
      const res = await fetch(`/doc?doc=${encodeURIComponent(nm)}`, {
        cache: "no-store",
      })
      if (res.ok) return await res.text()
    } catch {
      /* try next */
    }
  }
  return null
}

export interface Peaks {
  name: string
  dur: number
  peaks: number[]
}

const peaksCache = new Map<string, Promise<Peaks | null>>()

export function fetchPeaks(name: string): Promise<Peaks | null> {
  const hit = peaksCache.get(name)
  if (hit) return hit
  const promise = fetch(`/peaks?name=${encodeURIComponent(name)}`, {
    cache: "no-store",
  })
    .then((r) => (r.ok ? r.json() : null))
    .then((d: Peaks | null) => (d && Array.isArray(d.peaks) && d.peaks.length ? d : null))
    .catch(() => null)
  peaksCache.set(name, promise)
  promise.then((d) => {
    if (!d && peaksCache.get(name) === promise) peaksCache.delete(name)
  })
  return promise
}

export const audioSrc = (name: string) =>
  `/audio?name=${encodeURIComponent(name)}`
