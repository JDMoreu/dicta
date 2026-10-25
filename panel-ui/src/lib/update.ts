import type { AppState } from "./api"
import { verText } from "./format"

export type UpdTone = "run" | "err" | "pend" | "new" | "ok"

export interface UpdDisplay {
  key: string
  tone: UpdTone
  pct?: number
  v?: string
}

export function updateEnabled(state: AppState) {
  if (typeof state.check_updates === "boolean") return state.check_updates
  return state.update ? state.update.enabled !== false : true
}

export function updateDisplay(
  state: AppState,
  searching: boolean,
  busy: boolean,
): UpdDisplay | null {
  const u = state.update
  if (searching) return { key: "ui.updSearching", tone: "run" }
  const prog = u ? Number(u.progress) || 0 : 0
  if (busy || (prog > 0 && prog < 100 && u && u.available === true)) {
    return { key: "ui.updDownload", tone: "run", pct: prog }
  }
  if (u && u.error) return { key: "ui.updFailed", tone: "err" }
  if (u && u.applied) return { key: "ui.updPending", tone: "pend" }
  if (u && u.available) {
    return { key: "ui.updAvailable", tone: "new", v: verText(u.latest) }
  }
  if (u && u.checked_at) {
    return { key: "ui.updUpToDate", tone: "ok", v: verText(state.version) }
  }
  if (!updateEnabled(state)) return { key: "ui.updOff", tone: "pend" }
  return { key: "ui.updUpToDate", tone: "ok", v: verText(state.version) }
}

export function updateDownloading(state: AppState, busy: boolean) {
  const u = state.update
  const prog = u ? Number(u.progress) || 0 : 0
  return !!(
    busy ||
    (prog > 0 && prog < 100 && u && u.available === true)
  )
}

export function updateAvailable(state: AppState) {
  const u = state.update
  return !!(u && u.available === true && !u.applied && !u.error)
}
