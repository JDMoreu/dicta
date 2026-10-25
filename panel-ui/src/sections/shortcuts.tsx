import { useEffect, useRef, useState } from "react"
import { Icon } from "@/components/Icon"
import { PaneHead, SettingsGroup, SettingsRow, Hint } from "@/components/app-ui"
import { Button } from "@/components/ui/button"
import { Kbd } from "@/components/ui/kbd"
import type { AppState, RpcResult } from "@/lib/api"
import { hotkeyPretty, meetStopName } from "@/lib/format"
import { useLoadedApp } from "@/lib/store"
import { cn } from "@/lib/utils"

type Target = "hotkey" | "cancel_key" | "panel_key" | "meeting" | "meeting_cancel"

const MAX_KEYS = 3
const MODS = ["ctrl", "alt", "shift", "cmd"]
const MOD_MAP: Record<string, string> = {
  alt: "alt",
  control: "ctrl",
  ctrl: "ctrl",
  shift: "shift",
  meta: "cmd",
  os: "cmd",
}
const NAMED: Record<string, string> = {
  tab: "tab",
  enter: "enter",
  insert: "insert",
  delete: "delete",
  home: "home",
  end: "end",
  pageup: "pageup",
  pagedown: "pagedown",
  left: "left",
  up: "up",
  right: "right",
  down: "down",
}

const meetStopSpec = (state: AppState) => {
  const h = state.hotkeys || {}
  return h.meeting_stop ?? h.meeting_cancel ?? state.meeting_stop_key ?? ""
}

const currentSpec = (state: AppState, target: Target) => {
  if (target === "hotkey") return String(state.hotkey || "")
  if (target === "cancel_key") return String(state.cancel_key || "")
  if (target === "panel_key") return String(state.panel_key || "")
  if (target === "meeting") return String(state.hotkeys?.meeting ?? state.meeting_key ?? "")
  return meetStopSpec(state)
}

const tokenOf = (e: KeyboardEvent): string | null => {
  const key = String(e.key || "")
  const mod = MOD_MAP[key.toLowerCase()]
  if (mod) return mod
  if (/^F(?:[1-9]|1[0-9]|2[0-4])$/i.test(key)) return key.toLowerCase()
  if (key.length === 1 && /^[a-z0-9]$/i.test(key)) return key.toLowerCase()
  if (NAMED[key.toLowerCase()]) return NAMED[key.toLowerCase()]
  if (e.code?.startsWith("Key")) return e.code.slice(3).toLowerCase()
  if (e.code?.startsWith("Digit")) return e.code.slice(5).toLowerCase()
  return null
}

const specOf = (keys: string[]) => {
  const mods = MODS.filter((m) => keys.includes(m))
  const main = keys.filter((k) => !MODS.includes(k))
  return mods.concat(main).join("+")
}

function why(res: RpcResult, t: (k: string) => string) {
  const code = String(res.error || "").trim()
  if (code.startsWith("unknown key"))
    return `${t("ui.hotkeyUnknown")} ${code.split(":").pop()?.trim() || ""}`
  if (code.startsWith("duplicate modifier"))
    return `${t("ui.hotkeyDupMod")} ${code.split(":").pop()?.trim() || ""}`
  if (code === "too many keys (max 3)") return t("ui.hotkeyTooMany")
  if (code === "only one main key allowed" || code === "missing main key")
    return t("ui.hotkeyNeedMain")
  if (code === "empty" || code === "empty part") return t("ui.hotkeyInvalid")
  if (code === "timeout" || code === "connection") return t("ui.hotkeyTimeout")
  if (code === "invalid") return t("ui.hotkeyInvalid")
  return t("ui.hotkeyUnavailable")
}

function Keycaps({ spec, empty, locale }: { spec: string; empty: string; locale: "es" | "en" }) {
  if (!spec) {
    return <span className="px-1 text-[11px] text-text-3">{empty}</span>
  }
  return (
    <span className="flex items-center gap-1">
      {spec.split("+").map((k, i) => (
        <span key={`${k}-${i}`} className="flex items-center gap-1">
          {i ? <span className="text-[10px] text-text-3">+</span> : null}
          <Kbd className="h-6 min-w-6 rounded-md bg-secondary px-1.5 font-sans text-[10.5px] font-medium text-text-2 ring-1 ring-border/70">
            {hotkeyPretty(k, locale)}
          </Kbd>
        </span>
      ))}
    </span>
  )
}

export function ShortcutsSection() {
  const { state, t, locale, send, refresh } = useLoadedApp()
  const [target, setTarget] = useState<Target | null>(null)
  const [keys, setKeys] = useState<string[]>([])
  const [error, setError] = useState("")
  const [saving, setSaving] = useState(false)
  const targetRef = useRef<Target | null>(null)
  const keysRef = useRef<string[]>([])

  targetRef.current = target
  keysRef.current = keys

  useEffect(() => {
    if (!target) return
    const onKey = (e: KeyboardEvent) => {
      if (!targetRef.current) return
      e.preventDefault()
      e.stopPropagation()
      if (e.key === "Escape") {
        setTarget(null)
        setKeys([])
        setError("")
        return
      }
      if (e.key === "Backspace") {
        setKeys((prev) => prev.slice(0, -1))
        setError("")
        return
      }
      const token = tokenOf(e)
      if (!token) return
      if (keysRef.current.includes(token)) {
        setError(t("ui.hkDup"))
        return
      }
      if (keysRef.current.length >= MAX_KEYS) {
        setError(t("ui.hotkeyTooMany"))
        return
      }
      setKeys((prev) => [...prev, token])
      setError("")
    }
    window.addEventListener("keydown", onKey, true)
    return () => window.removeEventListener("keydown", onKey, true)
  }, [target, t])

  const open = (next: Target) => {
    setTarget(next)
    setKeys([])
    setError("")
  }

  const close = () => {
    setTarget(null)
    setKeys([])
    setError("")
  }

  const save = async () => {
    if (!target || saving) return
    if (!keys.length) {
      setError(t("ui.hkEmpty"))
      return
    }
    if (!keys.some((k) => !MODS.includes(k))) {
      setError(t("ui.hotkeyNeedMain"))
      return
    }
    const spec = specOf(keys)
    if (spec === currentSpec(state, target).toLowerCase()) {
      setError(t("ui.hotkeySame"))
      return
    }
    setSaving(true)
    let res: RpcResult
    if (target === "meeting" || target === "meeting_cancel") {
      const name = target === "meeting_cancel" ? meetStopName(state) : "meeting"
      res = await send("hotkey", { name, keys: spec })
    } else {
      const action =
        target === "cancel_key"
          ? "set_cancel_key"
          : target === "panel_key"
            ? "set_panel_key"
            : "set_hotkey"
      res = await send(action, spec)
    }
    setSaving(false)
    if (res.ok) {
      close()
      await refresh()
      return
    }
    setError(why(res, t))
  }

  const rows: { target: Target; icon: string; title: string; sub: string; key: string }[] = [
    {
      target: "hotkey",
      icon: "mic",
      title: t("ui.dictateKey"),
      sub: t("ui.dictateHint"),
      key: "hotkey",
    },
    {
      target: "cancel_key",
      icon: "x",
      title: t("ui.cancelKey"),
      sub: t("ui.cancelHint"),
      key: "cancel_key",
    },
    {
      target: "panel_key",
      icon: "settings",
      title: t("ui.panelKey"),
      sub: t("ui.panelHint"),
      key: "panel_key",
    },
    {
      target: "meeting",
      icon: "users",
      title: t("ui.meetingKey"),
      sub: t("ui.meetingKeyHint"),
      key: "meeting",
    },
    {
      target: "meeting_cancel",
      icon: "stop",
      title: t("ui.meetCancelKey"),
      sub: t("ui.meetCancelKeyHint"),
      key: "meeting_cancel",
    },
  ]

  const changeLabel: Record<Target, string> = {
    hotkey: "ui.ttChangeDictate",
    cancel_key: "ui.ttChangeCancel",
    panel_key: "ui.ttChangePanel",
    meeting: "ui.ttChangeMeeting",
    meeting_cancel: "ui.ttChangeMeetCancel",
  }

  return (
    <>
      <PaneHead title={t("ui.shortcuts")} hint={t("ui.shortcutsHint")} />

      <SettingsGroup title={t("ui.grpKeys")} hint={t("ui.grpKeysHint")}>
        {rows.map((row) => (
          <SettingsRow
            key={row.target}
            icon={row.icon}
            title={row.title}
            sub={row.sub}
            control={
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  className="flex h-8 items-center rounded-lg px-1 outline-none focus-visible:ring-2 focus-visible:ring-ring/50"
                  aria-label={t(row.title)}
                  title={t(changeLabel[row.target])}
                  onClick={() => open(row.target)}
                >
                  <Keycaps
                    spec={currentSpec(state, row.target)}
                    empty="—"
                    locale={locale}
                  />
                </button>
                <Button
                  type="button"
                  variant="secondary"
                  size="icon-sm"
                  className="size-8 rounded-lg"
                  aria-label={t(changeLabel[row.target])}
                  title={t(changeLabel[row.target])}
                  onClick={() => open(row.target)}
                >
                  <Icon name="keyboard" size={14} />
                </Button>
              </div>
            }
          />
        ))}

        {target ? (
          <div className="border-t border-border/70 px-4 py-3.5">
            <div className="flex items-center gap-2">
              <span
                className={cn(
                  "size-2 shrink-0 rounded-full bg-primary",
                  "shadow-[0_0_0_4px_color-mix(in_srgb,var(--primary)_14%,transparent)]",
                )}
              />
              <p className="min-w-0 flex-1 text-[11.5px] text-text-2">
                {t("ui.pressKeys")}
              </p>
              <span className="shrink-0 font-mono text-[10.5px] text-text-3 tabular-nums">
                {keys.length}/{MAX_KEYS}
              </span>
            </div>

            <div
              className="mt-3 flex min-h-9 flex-wrap items-center gap-1.5 rounded-lg bg-secondary/55 px-2.5 py-1.5 ring-1 ring-border/60"
              role="list"
              aria-label={t("ui.hkCombo")}
            >
              {keys.length ? (
                keys.map((k, i) => (
                  <span key={`${k}-${i}`} className="flex items-center gap-1.5" role="listitem">
                    {i ? <span className="text-[10px] text-text-3">+</span> : null}
                    <Kbd className="h-6 min-w-6 rounded-md bg-card px-1.5 font-sans text-[10.5px] font-medium text-text ring-1 ring-border/70">
                      {hotkeyPretty(k, locale)}
                    </Kbd>
                  </span>
                ))
              ) : (
                <span className="text-[11px] text-text-3">—</span>
              )}
            </div>

            <Hint className="mt-2">{t("ui.hkHint")}</Hint>
            {error ? (
              <p className="mt-2 text-[11px] text-destructive" role="alert">
                {error}
              </p>
            ) : null}

            <div className="mt-3 flex flex-wrap items-center gap-2">
              <Button
                type="button"
                variant="secondary"
                size="sm"
                className="h-8 rounded-lg px-2.5 text-[11px]"
                disabled={!keys.length}
                onClick={() => {
                  setKeys((prev) => prev.slice(0, -1))
                  setError("")
                }}
              >
                {t("ui.hkBack")}
              </Button>
              <Button
                type="button"
                variant="secondary"
                size="sm"
                className="h-8 rounded-lg px-2.5 text-[11px]"
                disabled={!keys.length}
                onClick={() => {
                  setKeys([])
                  setError("")
                }}
              >
                {t("ui.hkClear")}
              </Button>
              <Button
                type="button"
                variant="ghost"
                size="icon-sm"
                className="ml-auto size-8 rounded-lg text-text-3"
                aria-label={t("ui.cancel")}
                title={t("ui.cancel")}
                onClick={close}
              >
                <Icon name="x" size={14} />
              </Button>
              <Button
                type="button"
                size="sm"
                className="h-8 rounded-lg px-3 text-[11px]"
                disabled={!keys.length || saving}
                onClick={() => void save()}
              >
                {saving ? "…" : t("ui.hkSave")}
              </Button>
            </div>
          </div>
        ) : null}
      </SettingsGroup>
    </>
  )
}
