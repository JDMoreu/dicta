import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react"
import {
  fetchState,
  rpc,
  type AppState,
  type Locale,
  type RpcResult,
} from "./api"
import { localeOf, translate } from "./format"

export type SectionId =
  | "dictado"
  | "diccionario"
  | "reunion"
  | "audios"
  | "atajos"
  | "apariencia"

interface AppContextValue {
  state: AppState | null
  ready: boolean
  locale: Locale
  t: (key: string, vars?: Record<string, string | number>) => string
  send: (action: string, value?: unknown) => Promise<RpcResult>
  refresh: () => Promise<AppState | null>
  patch: (partial: Partial<AppState>) => void
  section: SectionId
  setSection: (s: SectionId) => void
}

const AppContext = createContext<AppContextValue | null>(null)

const POLL_IDLE = 800
const POLL_LIVE = 100
const POLL_BACKGROUND = 700       // en segundo plano, ~1 refresco cada 2,8 s
const CACHE_KEY = "dicta-state-v1"

function cachedState(): AppState | null {
  try {
    const raw = localStorage.getItem(CACHE_KEY)
    if (!raw) return null
    const value = JSON.parse(raw) as AppState
    if (!value || typeof value !== "object") return null
    if (!Array.isArray(value.mics) || !value.meeting || !value.theme) return null
    if (value.theme_mode === "auto") {
      value.theme = window.matchMedia("(prefers-color-scheme: dark)").matches
        ? "dark"
        : "light"
    }
    return value
  } catch {
    return null
  }
}

export function AppProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AppState | null>(() => cachedState())
  const [section, setSection] = useState<SectionId>("dictado")
  const stateRef = useRef<AppState | null>(state)
  const jsonRef = useRef(state ? JSON.stringify(state) : "")
  const autoChecked = useRef(false)
  const aliveRef = useRef(true)

  const adopt = useCallback((next: AppState | null) => {
    if (!next) return false
    const json = JSON.stringify(next)
    if (json === jsonRef.current) return false
    jsonRef.current = json
    stateRef.current = next
    setState(next)
    try {
      localStorage.setItem(CACHE_KEY, json)
    } catch {
      // sin almacenamiento, seguimos con el estado en memoria
    }
    return true
  }, [])

  const refresh = useCallback(async () => {
    const next = await fetchState()
    if (next) adopt(next)
    return next
  }, [adopt])

  useEffect(() => {
    aliveRef.current = true
    let timer = 0
    let sleepy = 0
    const tick = async () => {
      const live = !!(
        stateRef.current?.meeting?.active || stateRef.current?.mic_test?.active
      )
      // En segundo plano se sigue consultando, pero más despacio: si no, el
      // panel se queda con estado viejo (una reunión iniciada con el atajo no
      // aparece hasta que le das el foco).
      if (!document.hasFocus() && !live && stateRef.current) {
        sleepy += 1
      }
      const wait = !document.hasFocus() && !live && stateRef.current
      if (live || document.hasFocus() || !stateRef.current || sleepy % 4 === 1) {
        const next = await fetchState()
        if (aliveRef.current && next) adopt(next)
      }
      if (!aliveRef.current) return
      timer = window.setTimeout(tick, wait ? POLL_BACKGROUND : live ? POLL_LIVE : POLL_IDLE)
    }
    void tick()
    return () => {
      aliveRef.current = false
      window.clearTimeout(timer)
    }
  }, [adopt])

  const send = useCallback(
    async (action: string, value?: unknown) => {
      const result = await rpc(action, value)
      void refresh()
      return result
    },
    [refresh],
  )

  const patch = useCallback((partial: Partial<AppState>) => {
    const base = stateRef.current
    if (!base) return
    const next = { ...base, ...partial }
    const json = JSON.stringify(next)
    jsonRef.current = json
    stateRef.current = next
    setState(next)
    try {
      localStorage.setItem(CACHE_KEY, json)
    } catch {
      // idem
    }
  }, [])

  const theme = state?.theme === "dark" ? "dark" : "light"
  const locale = state ? localeOf(state) : "es"
  const t = useCallback(
    (key: string, vars?: Record<string, string | number>) =>
      translate(locale, key, vars),
    [locale],
  )

  useEffect(() => {
    const root = document.documentElement
    root.classList.toggle("dark", theme === "dark")
    root.dataset.theme = theme
    root.style.colorScheme = theme
    try {
      localStorage.setItem("dicta-theme", theme)
      if (state?.theme_mode) {
        localStorage.setItem("dicta-theme-mode", state.theme_mode)
      }
    } catch {
      // sin almacenamiento, el HTML de arranque usa el tema del sistema
    }
  }, [theme, state?.theme_mode])

  useEffect(() => {
    document.documentElement.lang = locale
    document.title = translate(locale, "ui.windowTitle")
  }, [locale])

  useEffect(() => {
    const version = state?.icon_version
    if (!version) return
    let link = document.getElementById("favicon") as HTMLLinkElement | null
    if (!link) {
      link = document.createElement("link")
      link.id = "favicon"
      link.rel = "icon"
      link.type = "image/png"
      document.head.appendChild(link)
    }
    link.href = `/panel/icon.png?size=32&v=${encodeURIComponent(version)}`
  }, [state?.icon_version])

  useEffect(() => {
    if (!state || autoChecked.current) return
    if (!state.check_updates) return
    if (state.update && state.update.checked_at) return
    autoChecked.current = true
    void rpc("check_update")
  }, [state])

  const value = useMemo<AppContextValue>(
    () => ({
      state,
      ready: !!state,
      locale,
      t,
      send,
      refresh,
      patch,
      section,
      setSection,
    }),
    [state, locale, t, send, refresh, patch, section],
  )

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>
}

export function useApp() {
  const ctx = useContext(AppContext)
  if (!ctx) throw new Error("useApp outside AppProvider")
  return ctx
}

export function useLoadedApp() {
  const ctx = useApp()
  if (!ctx.state) throw new Error("state not loaded")
  return ctx as AppContextValue & { state: AppState }
}
