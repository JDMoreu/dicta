import { useEffect, useMemo, useState, type ReactNode } from "react"
import { Icon } from "@/components/Icon"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import { Button } from "@/components/ui/button"
import { TipButton } from "@/components/app-ui"
import { deriveMedia } from "@/lib/media"
import { engineLabel, verText } from "@/lib/format"
import { useLoadedApp, type SectionId } from "@/lib/store"
import {
  updateAvailable,
  updateDisplay,
  updateDownloading,
} from "@/lib/update"
import { cn } from "@/lib/utils"

const RAIL: { id: SectionId; icon: string; key: string }[] = [
  { id: "dictado", icon: "mic", key: "ui.secDictation" },
  { id: "diccionario", icon: "book", key: "ui.dict" },
  { id: "reunion", icon: "users", key: "ui.meeting" },
  { id: "audios", icon: "file-audio", key: "ui.audiosDocs" },
  { id: "atajos", icon: "keyboard", key: "ui.shortcuts" },
  { id: "apariencia", icon: "sun", key: "ui.appearance" },
]

function Rail() {
  const { state, t, section, setSection } = useLoadedApp()
  const media = useMemo(() => deriveMedia(state), [state])
  const counts: Partial<Record<SectionId, number>> = {
    diccionario: state.dictionary.length,
    audios: media.length,
  }
  const engine = engineLabel(
    state.engine_resolved || state.engine || "cpu",
    state.language === "en" ? "en" : "es",
  )

  return (
    <nav className="flex min-h-0 w-[212px] shrink-0 flex-col gap-1 border-r border-border/60 px-2.5 pt-3 pb-3">
      {RAIL.map((item) => {
        const active = section === item.id
        return (
          <button
            key={item.id}
            type="button"
            onClick={() => setSection(item.id)}
            aria-current={active ? "page" : undefined}
            className={cn(
              "group relative flex h-9 items-center gap-2.5 rounded-[10px] px-2.5 text-left text-[12.5px] font-medium outline-none transition-colors",
              "focus-visible:ring-2 focus-visible:ring-ring/50",
              active
                ? "bg-primary/9 text-primary"
                : "text-text-2 hover:bg-accent/70 hover:text-foreground",
            )}
          >
            <Icon
              name={item.icon}
              size={17}
              className={active ? "text-primary" : "text-text-3"}
            />
            <span className="min-w-0 flex-1 truncate">{t(item.key)}</span>
            {counts[item.id] ? (
              <span
                className={cn(
                  "grid h-5 min-w-5 place-items-center rounded-full px-1.5 font-mono text-[10px] tabular-nums",
                  active
                    ? "bg-primary/12 text-primary"
                    : "bg-surface-3/80 text-text-2",
                )}
              >
                {counts[item.id]}
              </span>
            ) : null}
          </button>
        )
      })}
      <div className="mt-auto flex flex-col gap-0.5 px-2.5 pt-4">
        <span className="text-[9.5px] font-semibold tracking-[0.08em] text-text-3 uppercase">
          {t("ui.engineState")}
        </span>
        <span className="truncate text-[11px] font-medium text-text-2" title={engine}>
          {engine}
        </span>
      </div>
    </nav>
  )
}

function UpdDialogs({
  open,
  mode,
  onOpenChange,
  onInstall,
  onSearch,
}: {
  open: boolean
  mode: "check" | "install"
  onOpenChange: (open: boolean) => void
  onInstall: () => void
  onSearch: () => void
}) {
  const { state, t } = useLoadedApp()
  const u = state.update || {}
  const latest = verText(u.latest) || verText(state.version)

  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent className="w-[400px] max-w-[calc(100vw-2rem)] gap-0 rounded-[16px] border-0 bg-card p-5 shadow-lift-lg">
        <AlertDialogHeader className="gap-2.5 text-left">
          <span className="grid size-10 place-items-center rounded-[12px] bg-primary/9 text-primary ring-1 ring-primary/12">
            <Icon name={mode === "install" ? "download" : "search"} size={18} />
          </span>
          <AlertDialogTitle className="text-[15px] leading-5 font-semibold">
            {t(mode === "install" ? "ui.updDialogTitle" : "ui.updSearchTitle")}
          </AlertDialogTitle>
          <AlertDialogDescription className="text-[12px] leading-[18px] text-muted-foreground">
            {mode === "install"
              ? t("ui.updDialogBody", { v: latest })
              : t("ui.updSearchBody")}
          </AlertDialogDescription>
          {mode === "install" && u.notes ? (
            <div className="mt-1 max-h-[180px] overflow-auto rounded-[10px] bg-secondary/70 p-2.5 text-[11px] leading-[17px] whitespace-pre-line text-text-2 ring-1 ring-border/60">
              {u.notes}
            </div>
          ) : null}
        </AlertDialogHeader>
        <AlertDialogFooter className="mt-4 flex-row justify-end gap-2">
          <AlertDialogCancel className="h-9 rounded-[9px] px-3.5 text-[12.5px]">
            {t("ui.cancel")}
          </AlertDialogCancel>
          <AlertDialogAction
            onClick={mode === "install" ? onInstall : onSearch}
            className="h-9 rounded-[9px] px-3.5 text-[12.5px]"
          >
            <Icon
              name={mode === "install" ? "download" : "search"}
              size={14}
            />
            {t(mode === "install" ? "ui.updateNow" : "ui.updSearchGo")}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}

function Footer() {
  const { state, t, send } = useLoadedApp()
  const [quitOpen, setQuitOpen] = useState(false)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [mode, setMode] = useState<"check" | "install">("check")
  const [searching, setSearching] = useState(false)
  const [busy, setBusy] = useState(false)

  const downloading = updateDownloading(state, busy)
  const avail = updateAvailable(state)
  const status = updateDisplay(state, searching, busy)
  const u = state.update || {}
  const pctRaw = Number(u.progress) || 0
  const pct = Math.max(0, Math.min(100, pctRaw <= 1 ? pctRaw * 100 : pctRaw))

  useEffect(() => {
    if (!busy) return
    if (
      u.applied ||
      u.error ||
      pct >= 100 ||
      (u.checked_at && !u.available)
    ) {
      setBusy(false)
    }
  }, [busy, u.applied, u.error, pct, u.available, u.checked_at])

  useEffect(() => {
    if (!busy) return
    const timer = window.setTimeout(() => setBusy(false), 90000)
    return () => window.clearTimeout(timer)
  }, [busy])

  const openStatus = () => {
    if (downloading || searching) return
    setMode(avail ? "install" : "check")
    setDialogOpen(true)
  }

  const onSearch = async () => {
    setDialogOpen(false)
    setSearching(true)
    await send("check_update", { force: true })
    setSearching(false)
  }

  const onInstall = async () => {
    setDialogOpen(false)
    setBusy(true)
    await send("update")
  }

  const tone =
    status?.tone === "run"
      ? "text-primary"
      : status?.tone === "err"
        ? "text-destructive"
        : status?.tone === "new"
          ? "text-primary"
          : status?.tone === "pend"
            ? "text-warning"
            : "text-text-3"

  return (
    <footer className="flex h-[52px] shrink-0 items-center gap-2 border-t border-border/60 bg-card/55 px-3">
      <TipButton
        label={t("ui.quit")}
        variant="ghost"
        size="icon-sm"
        className="size-8 rounded-lg text-text-3 hover:text-destructive"
        onClick={() => setQuitOpen(true)}
      >
        <Icon name="power" size={16} />
      </TipButton>

      {status ? (
        <button
          type="button"
          onClick={openStatus}
          disabled={downloading || searching}
          className={cn(
            "group ml-1 flex h-8 items-center gap-1.5 rounded-lg px-2 text-[11.5px] font-medium outline-none transition-colors",
            "focus-visible:ring-2 focus-visible:ring-ring/50",
            downloading || searching
              ? "cursor-default"
              : "hover:bg-accent/70",
            tone,
          )}
          title={t("ui.updSearchAria")}
          aria-label={t("ui.updSearchAria")}
        >
          <span
            aria-hidden
            className={cn(
              "size-1.5 rounded-full",
              status.tone === "run" && "animate-pulse bg-primary",
              status.tone === "err" && "bg-destructive",
              status.tone === "new" && "bg-primary",
              status.tone === "pend" && "bg-warning",
              status.tone === "ok" && "bg-success/80",
            )}
          />
          <span>
            {t(status.key)}
            {status.pct !== undefined && status.pct > 0
              ? ` ${Math.round(status.pct <= 1 ? status.pct * 100 : status.pct)}%`
              : status.v
                ? ` · ${status.v}`
                : ""}
          </span>
          {downloading ? (
            <span className="ml-1 block h-1 w-14 overflow-hidden rounded-full bg-border">
              <span
                className="block h-full rounded-full bg-primary transition-[width]"
                style={{ width: `${Math.max(4, pct)}%` }}
              />
            </span>
          ) : null}
        </button>
      ) : null}

      <span className="flex-1" />

      <Button
        type="button"
        size="sm"
        className="ml-1 h-8 gap-1.5 rounded-[9px] px-3 text-[12px] font-semibold"
        onClick={() => void send("hide")}
      >
        <Icon name="check" size={14} />
        {t("ui.done")}
      </Button>

      <AlertDialog open={quitOpen} onOpenChange={setQuitOpen}>
        <AlertDialogContent className="w-[400px] max-w-[calc(100vw-2rem)] gap-0 rounded-[16px] border-0 bg-card p-5 shadow-lift-lg">
          <AlertDialogHeader className="gap-2.5 text-left">
            <span className="grid size-10 place-items-center rounded-[12px] bg-destructive/10 text-destructive ring-1 ring-destructive/15">
              <Icon name="power" size={18} />
            </span>
            <AlertDialogTitle className="text-[15px] leading-5 font-semibold">
              {t("ui.quitTitle")}
            </AlertDialogTitle>
            <AlertDialogDescription className="text-[12px] leading-[18px] text-muted-foreground">
              {t("ui.quitBody")}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter className="mt-4 flex-row justify-end gap-2">
            <AlertDialogCancel className="h-9 rounded-[9px] px-3.5 text-[12.5px]">
              {t("ui.cancel")}
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={() => void send("quit")}
              className="h-9 rounded-[9px] bg-destructive px-3.5 text-[12.5px] text-white hover:bg-destructive/90"
            >
              <Icon name="power" size={14} />
              {t("ui.quitConfirm")}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <UpdDialogs
        open={dialogOpen}
        mode={mode}
        onOpenChange={setDialogOpen}
        onInstall={() => void onInstall()}
        onSearch={() => void onSearch()}
      />
    </footer>
  )
}

export function AppShell({ children }: { children: ReactNode }) {
  const { section } = useLoadedApp()
  return (
    <div className="shell flex h-full min-h-0 flex-col overflow-clip">
      <div className="flex min-h-0 flex-1">
        <Rail />
        <main
          key={section}
          className="min-w-0 flex-1 overflow-y-auto animate-in fade-in-0 slide-in-from-bottom-1 duration-150"
        >
          <div className="mx-auto w-full max-w-[752px] px-7 pt-5 pb-8">
            {children}
          </div>
        </main>
      </div>
      <Footer />
    </div>
  )
}

