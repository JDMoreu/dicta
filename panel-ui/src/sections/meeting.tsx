import { useEffect, useRef, useState } from "react"
import { Icon } from "@/components/Icon"
import { AudioPreview } from "@/components/audio-preview"
import { LevelBar } from "@/components/level-bar"
import {
  PaneHead,
  SettingsGroup,
  SettingsRow,
  Spinner,
} from "@/components/app-ui"
import { SelectField, type FieldOption } from "@/components/fields"
import { Button } from "@/components/ui/button"
import { Switch } from "@/components/ui/switch"
import { fetchState } from "@/lib/api"
import { fmtTime } from "@/lib/format"
import { useLoadedApp } from "@/lib/store"
import { cn } from "@/lib/utils"

const fileBase = (p?: string | null) =>
  p ? String(p).split(/[\\/]/).pop() || "" : ""

function SourceRow() {
  const { state, t, send, patch } = useLoadedApp()
  const m = state.meeting || {}
  const list = state.sources?.length
    ? state.sources.slice()
    : [{ key: "all", label: t("ui.srcAll"), playing: true }]
  const cur = String(state.meeting_source || "all")
  if (!list.some((s) => s.key === cur)) {
    list.unshift({ key: cur, label: t("ui.srcMissing"), playing: false })
  }
  const current = list.find((s) => s.key === cur)
  const options: FieldOption[] = list.map((s) => ({
    value: s.key,
    label: s.key === "all" ? t("ui.srcAll") : s.label,
  }))

  return (
    <SettingsRow
      icon="monitor"
      title={t("ui.meetSource")}
      sub={t("ui.meetSourceHint")}
      control={
        <div className="flex items-center gap-2">
          <span
            aria-hidden
            title={t(current?.playing ? "ui.srcLegendOn" : "ui.srcLegendOff")}
            className={cn(
              "size-2 shrink-0 rounded-full ring-2 ring-card transition-colors",
              current?.playing
                ? "bg-success shadow-[0_0_0_3px_color-mix(in_srgb,var(--success)_18%,transparent)]"
                : "bg-text-3/40",
            )}
          />
          <SelectField
            value={cur}
            options={options}
            disabled={!!m.active}
            ariaLabel={t("ui.meetSource")}
            onChange={(v) => {
              patch({ meeting_source: v })
              void send("meeting_source", v)
            }}
          />
        </div>
      }
    />
  )
}

function MeetingMicRow() {
  const { state, t, send, patch } = useLoadedApp()
  const on = state.meeting_mic !== false
  return (
    <SettingsRow
      icon="mic"
      title={t("ui.meetMic")}
      sub={t("ui.meetMicHint")}
      control={
        <div className="flex items-center gap-2.5">
          <span className="text-[11.5px] text-text-2">
            {t(on ? "ui.meetMicOn" : "ui.meetMicOff")}
          </span>
          <Switch
            checked={on}
            aria-label={t("ui.meetMic")}
            onCheckedChange={(v) => {
              patch({ meeting_mic: v })
              void send("meeting_mic", v)
            }}
            className="data-[state=unchecked]:bg-[var(--text-3)]/55"
          />
        </div>
      }
    />
  )
}

function IdleCard() {
  const { state, t, send } = useLoadedApp()
  const [starting, setStarting] = useState(false)
  const status = String(state.meeting?.status || "")

  const start = async () => {
    if (starting) return
    setStarting(true)
    await send("meeting", "start")
    setStarting(false)
  }

  return (
    <section className="relative overflow-hidden rounded-xl bg-card ring-1 ring-border">
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 opacity-[0.55] dark:opacity-[0.38]"
        style={{
          background:
            "radial-gradient(120% 90% at 50% 0%, color-mix(in srgb, var(--brand-2) 10%, transparent), transparent 62%)",
        }}
      />
      <div className="relative flex flex-col items-center px-6 py-9 text-center">
        <div className="mb-5 flex h-9 items-end gap-1">
          {[7, 14, 22, 30, 22, 34, 18, 26, 12, 20, 9, 15].map((h, i) => (
            <span
              key={i}
              className="w-[3px] rounded-full bg-primary/35"
              style={{ height: h }}
            />
          ))}
        </div>
        <h3 className="text-[15px] font-semibold tracking-[-0.01em] text-text">
          {t("ui.meetTitle")}
        </h3>
        <p className="mt-1 max-w-[430px] text-[12px] leading-relaxed text-text-2">
          {t("ui.meetDesc")}
        </p>
        <button
          type="button"
          onClick={() => void start()}
          disabled={starting}
          aria-label={t("ui.meetTitle")}
          title={t("ui.meetTitle")}
          className={cn(
            "mt-5 grid size-12 place-items-center rounded-full text-white outline-none",
            "bg-[linear-gradient(135deg,var(--brand-1),var(--brand-2)_58%,var(--brand-3))]",
            "shadow-[0_8px_22px_-8px_color-mix(in_srgb,var(--brand-2)_65%,transparent)]",
            "transition-transform hover:scale-[1.04] active:scale-95",
            "focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-card",
            "disabled:opacity-70",
          )}
        >
          {starting ? <Spinner className="size-5 text-white" /> : <Icon name="play" size={19} />}
        </button>
        <p className="mt-4 h-4 text-[11px] text-text-2">
          {status || t("ui.meetLiveNote")}
        </p>
      </div>
    </section>
  )
}

function LiveCard() {
  const { state, t, send, setSection } = useLoadedApp()
  const m = state.meeting || {}
  const [cancelArmed, setCancelArmed] = useState(false)
  const [busy, setBusy] = useState<string | null>(null)

  const act = async (action: string) => {
    if (busy) return
    setBusy(action)
    await send("meeting", action)
    setBusy(null)
  }

  const stop = async () => {
    if (busy) return
    setBusy("stop")
    await send("meeting", "stop")
    const next = await fetchState()
    setBusy(null)
    const doc = fileBase(next?.meeting?.doc)
    if (doc) {
      setSection("audios")
      window.setTimeout(
        () => window.dispatchEvent(new CustomEvent("dicta:focus-doc", { detail: doc })),
        220,
      )
    }
  }

  const cancel = async () => {
    if (!cancelArmed) {
      setCancelArmed(true)
      window.setTimeout(() => setCancelArmed(false), 2600)
      return
    }
    setCancelArmed(false)
    await act("cancel")
  }

  // Transcripción completa: se pega abajo cuando llega texto nuevo.
  const trRef = useRef<HTMLDivElement | null>(null)
  const transcript = String((m as { transcript?: string }).transcript || m.last || "")
  useEffect(() => {
    const el = trRef.current
    if (el) el.scrollTop = el.scrollHeight
  }, [transcript])

  const err = String(m.status || "").startsWith("error")

  return (
    <section className="overflow-hidden rounded-[14px] bg-card shadow-lift">
      <div className="flex items-center gap-3 px-4 pt-3.5 pb-3">
        <span
          aria-hidden
          className={cn(
            "size-2.5 shrink-0 rounded-full",
            m.paused ? "bg-warning" : "animate-pulse bg-destructive",
          )}
        />
        <div className="min-w-0 flex-1">
          <div className="text-[13px] leading-[18px] font-semibold">
            {m.paused ? t("ui.meetStatePaused") : t("ui.meetStateRec")}
          </div>
          <div className="mt-0.5 flex items-center gap-1.5 text-[11.5px] leading-4 text-muted-foreground">
            <span className="font-mono text-[12px] tabular-nums text-text-2">
              {fmtTime(Number(m.seconds) || 0)}
            </span>
            <span aria-hidden className="text-text-3">·</span>
            <span className="truncate">{t("ui.meetLiveNote")}</span>
          </div>
        </div>
        <div className="flex shrink-0 items-center gap-1.5">
          <Button
            type="button"
            variant="secondary"
            size="icon-sm"
            className="size-8 rounded-lg"
            aria-label={t(m.paused ? "ui.resume" : "ui.pause")}
            title={t(m.paused ? "ui.resume" : "ui.pause")}
            disabled={!!busy}
            onClick={() => void act(m.paused ? "resume" : "pause")}
          >
            <Icon name={m.paused ? "play" : "pause"} size={14} />
          </Button>
          <Button
            type="button"
            variant="default"
            size="icon-sm"
            className="size-8 rounded-lg"
            aria-label={t("ui.meetSave")}
            title={t("ui.meetSave")}
            disabled={!!busy}
            onClick={() => void stop()}
          >
            {busy === "stop" ? (
              <Spinner className="size-3.5 text-primary-foreground" />
            ) : (
              <Icon name="stop" size={13} />
            )}
          </Button>
          <Button
            type="button"
            variant={cancelArmed ? "destructive" : "secondary"}
            size="icon-sm"
            className={cn("size-8 rounded-lg", cancelArmed && "text-white")}
            aria-label={t(cancelArmed ? "ui.confirmCancel" : "ui.meetCancel")}
            title={t(cancelArmed ? "ui.confirmCancel" : "ui.meetCancel")}
            disabled={!!busy}
            onClick={() => void cancel()}
          >
            <Icon name="x" size={13} />
          </Button>
        </div>
      </div>

      <div className="flex items-center gap-4 px-4 pb-3">
        <LevelBar
          label={t("ui.lvSys")}
          icon="monitor"
          active={!!m.active}
          paused={!!m.paused}
          level={m.level_sys ?? m.level}
          db={m.db_sys}
        />
        {state.meeting_mic !== false ? (
          <LevelBar
            label={t("ui.lvMic")}
            icon="mic"
            active={!!m.active}
            paused={!!m.paused}
            level={m.level_mic}
            db={m.db_mic}
          />
        ) : null}
      </div>

      <div className="px-4 pb-3">
        <div className="mb-1.5 text-[10.5px] font-medium tracking-[0.04em] text-text-3 uppercase">
          {t("ui.meetLiveTr")}
        </div>
        <div
          ref={trRef}
          className="h-[190px] max-h-[52vh] min-h-[96px] resize-y overflow-y-auto overscroll-contain rounded-lg bg-secondary/50 px-3 py-2 ring-1 ring-border/60"
        >
          <p
            className={cn(
              "whitespace-pre-wrap text-[12.5px] leading-relaxed",
              m.paused || !transcript ? "text-text-3" : "text-text",
            )}
          >
            {transcript || t("ui.meetEmptyTr")}
          </p>
        </div>
        {err ? (
          <p className="mt-2 text-[11px] text-destructive">
            {t("ui.meetError")} {m.status}
          </p>
        ) : null}
      </div>
    </section>
  )
}

function DoneCard() {
  const { state, t, send, setSection } = useLoadedApp()
  const m = state.meeting || {}
  const [note, setNote] = useState("")
  const [busy, setBusy] = useState(false)
  const saved = m.status === "guardada"
  const doc = fileBase(m.doc)
  const wav = saved ? fileBase(m.wav) : ""

  const download = async () => {
    if (!wav || busy) return
    setBusy(true)
    setNote(t("ui.saveChoose"))
    const res = await send("export", { name: wav, kind: "wav" })
    setBusy(false)
    setNote(res.ok === false ? res.error || t("ui.saveFail") : t("ui.saveDone"))
  }

  return (
    <section className="overflow-hidden rounded-xl bg-card p-5 ring-1 ring-border">
      <div className="flex items-start gap-3">
        <span className="mt-0.5 grid size-9 shrink-0 place-items-center rounded-full bg-success/12 text-success ring-1 ring-success/20">
          <Icon name={saved ? "check" : "x"} size={16} />
        </span>
        <div className="min-w-0 flex-1">
          <h3 className="text-[13.5px] font-semibold text-text">
            {t(saved ? "ui.meetSaved" : "ui.meetCancelled")}
          </h3>
          <p className="truncate text-[11.5px] text-text-2">
            {doc || t("ui.meetEmptyTr")}
          </p>
        </div>
        <Button
          type="button"
          variant="ghost"
          size="icon-sm"
          className="size-8 rounded-lg text-text-3"
          aria-label={t("ui.docClose")}
          title={t("ui.docClose")}
          onClick={() => void send("meeting", "dismiss")}
        >
          <Icon name="x" size={14} />
        </Button>
      </div>

      {saved && wav ? (
        <div className="mt-4">
          <AudioPreview name={wav} src={`/audio?name=${encodeURIComponent(wav)}`} />
        </div>
      ) : null}

      <div className="mt-4 flex flex-wrap items-center gap-2">
        {saved && doc ? (
          <Button
            type="button"
            variant="secondary"
            size="sm"
            className="h-8 rounded-lg px-3 text-[11.5px]"
            onClick={() => {
              setSection("audios")
              window.setTimeout(
                () =>
                  window.dispatchEvent(
                    new CustomEvent("dicta:focus-doc", { detail: doc }),
                  ),
                120,
              )
            }}
          >
            <Icon name="file-text" size={13} />
            {t("ui.meetOpen")}
          </Button>
        ) : null}
        {saved && wav ? (
          <Button
            type="button"
            variant="secondary"
            size="sm"
            className="h-8 rounded-lg px-3 text-[11.5px]"
            disabled={busy}
            onClick={() => void download()}
          >
            {busy ? <Spinner className="size-3" /> : <Icon name="download" size={13} />}
            {t("ui.meetDl")}
          </Button>
        ) : null}
        {note ? <span className="text-[11px] text-text-2">{note}</span> : null}
      </div>
    </section>
  )
}

export function MeetingSection() {
  const { state, t } = useLoadedApp()
  const m = state.meeting || {}
  const finished = m.status === "guardada" || m.status === "cancelada"

  return (
    <>
      <PaneHead title={t("ui.meeting")} hint={t("ui.meetingHint")} />
      <div className="space-y-3">
        <SettingsGroup>
          <SourceRow />
          <MeetingMicRow />
        </SettingsGroup>
        {m.active ? <LiveCard /> : finished ? <DoneCard /> : <IdleCard />}
      </div>
    </>
  )
}
