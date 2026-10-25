import { useEffect, useRef, useState } from "react"
import { Icon } from "@/components/Icon"
import { AudioPreview } from "@/components/audio-preview"
import { SettingsGroup, SettingsRow, PaneHead, ValuePill, Hint, Spinner } from "@/components/app-ui"
import { SelectField, type FieldOption } from "@/components/fields"
import { meterColorVar, meterZone } from "@/lib/meter"
import { Button } from "@/components/ui/button"
import { Slider } from "@/components/ui/slider"
import { Switch } from "@/components/ui/switch"
import { fetchState } from "@/lib/api"
import {
  LANG_CODES,
  LANG_LABEL,
  engineLabel,
  engineOptions,
  gpuDevices,
  gpuShortName,
  modelOptions,
} from "@/lib/format"
import { useLoadedApp } from "@/lib/store"
import { cn } from "@/lib/utils"

const DB_FLOOR = -80
const SEGMENTS = 40
const dbOf = (v: number) => (v > 0 ? 20 * Math.log10(v) : -Infinity)
const meterPct = (db: number) =>
  Math.max(
    0,
    Math.min(100, ((Math.max(DB_FLOOR, Math.min(0, db)) - DB_FLOOR) / -DB_FLOOR) * 100),
  )
const linOfDb = (db: number) => Math.pow(10, db / 20)

function useLiveMic() {
  const [mic, setMic] = useState({ rms: 0, thr: 0, voice: false, has: false })
  useEffect(() => {
    let alive = true
    let timer = 0
    const tick = async () => {
      const s = await fetchState()
      if (alive && s) {
        setMic({
          rms: Number(s.rms) || 0,
          thr: Number(s.thr) || 0,
          voice: !!s.voice,
          has: true,
        })
      }
      if (alive) timer = window.setTimeout(tick, 150)
    }
    void tick()
    return () => {
      alive = false
      window.clearTimeout(timer)
    }
  }, [])
  return mic
}

function MicMeter() {
  const { state, t, send } = useLoadedApp()
  const live = useLiveMic()
  const [dragDb, setDragDb] = useState<number | null>(null)
  const dragRef = useRef<number | null>(null)
  const boxRef = useRef<HTMLDivElement | null>(null)

  const sens = Math.max(0.2, Number(state.sens) || 1)
  const thrLin =
    live.has && live.thr > 0 ? live.thr : (Number(state.voice_threshold) || 0) / sens
  const thrDb = dragDb ?? dbOf(thrLin)
  const levelDb = dbOf(live.has ? live.rms : state.rms)
  const lit = Math.round((meterPct(levelDb) / 100) * SEGMENTS)
  const thrPct = meterPct(thrDb)
  const value = Number.isFinite(thrDb) ? Math.round(thrDb) : null

  const updateFromX = (clientX: number) => {
    const box = boxRef.current
    if (!box) return
    const r = box.getBoundingClientRect()
    const pct = Math.min(1, Math.max(0, (clientX - r.left) / r.width))
    const db = Math.round(DB_FLOOR + pct * -DB_FLOOR)
    dragRef.current = db
    setDragDb(db)
  }

  const commit = () => {
    const db = dragRef.current
    if (db === null) return
    const lin = Math.min(1, Math.max(0, linOfDb(db) * sens))
    const next = Math.round(lin * 1e5) / 1e5
    dragRef.current = null
    setDragDb(null)
    void send("voice_threshold", next)
  }

  return (
    <div className="flex w-[360px] max-w-full items-start gap-2.5">
      <div className="min-w-0 flex-1">
        <div
          ref={boxRef}
          role="slider"
          tabIndex={0}
          aria-label={t("ui.sensPeak")}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-valuenow={Math.round(thrPct)}
          aria-valuetext={
            value === null ? "—" : `${value} ${t("ui.micMeterDb")}`
          }
          title={t("ui.micMeterDrag")}
          className="relative h-[22px] cursor-pointer touch-none rounded-[6px] bg-secondary/60 px-1 ring-1 ring-border/50 outline-none focus-visible:ring-2 focus-visible:ring-ring/50"
          onPointerDown={(e) => {
            e.currentTarget.setPointerCapture(e.pointerId)
            updateFromX(e.clientX)
          }}
          onPointerMove={(e) => {
            if (e.buttons === 1) updateFromX(e.clientX)
          }}
          onPointerUp={() => commit()}
          onPointerCancel={() => commit()}
          onKeyDown={(e) => {
            const base = Number.isFinite(thrDb) ? thrDb : DB_FLOOR
            const step = e.shiftKey ? 5 : 1
            let next = base
            if (e.key === "ArrowRight" || e.key === "ArrowUp") next += step
            else if (e.key === "ArrowLeft" || e.key === "ArrowDown") next -= step
            else return
            e.preventDefault()
            const db = Math.max(DB_FLOOR, Math.min(0, Math.round(next)))
            dragRef.current = db
            setDragDb(db)
            commit()
          }}
        >
          <div className="flex h-full items-center gap-[2px]">
            {Array.from({ length: SEGMENTS }, (_, i) => {
              const zone = meterZone(((i + 0.5) / SEGMENTS) * 100)
              const on = i < lit
              return (
                <span
                  key={i}
                  className={cn(
                    "h-[14px] min-w-0 flex-1 rounded-[1.5px] transition-[background-color,opacity] duration-100",
                    on ? "" : "bg-border/70",
                  )}
                  style={
                    on ? { backgroundColor: meterColorVar(zone) } : undefined
                  }
                />
              )
            })}
          </div>
          <span
            aria-hidden
            className="pointer-events-none absolute top-1/2 z-10 -translate-x-1/2 -translate-y-1/2"
            style={{ left: `calc(${thrPct}% + 4px)` }}
          >
            <span className="block h-[26px] w-[7px] rounded-full border-2 border-card bg-foreground shadow-[0_1px_3px_rgba(0,0,0,.35)]" />
          </span>
        </div>
        <div className="mt-1 flex justify-between px-0.5 font-mono text-[9px] text-text-3">
          <span>-80</span>
          <span>-60</span>
          <span>-40</span>
          <span>-20</span>
          <span>0 dB</span>
        </div>
      </div>
      <ValuePill
        tone={live.voice ? "ok" : "neutral"}
        className="-mt-[3px] self-start"
      >
        {value === null ? "—" : `${value} dB`}
      </ValuePill>
    </div>
  )
}

function WaitSlider() {
  const { state, t, send } = useLoadedApp()
  const [wait, setWait] = useState(Number(state.silence_wait) || 1.5)

  useEffect(() => {
    setWait(Number(state.silence_wait) || 1.5)
  }, [state.silence_wait])

  return (
    <div className="flex w-[360px] max-w-full items-center gap-3">
      <Slider
        value={[wait]}
        min={0.5}
        max={10}
        step={0.5}
        aria-label={t("ui.waitAria")}
        onValueChange={([v]) => setWait(v)}
        onValueCommit={([v]) => void send("silence_wait", v)}
        className="[&_[data-slot=slider-range]]:bg-primary [&_[data-slot=slider-thumb]]:size-3.5 [&_[data-slot=slider-thumb]]:border-2 [&_[data-slot=slider-track]]:h-[5px] [&_[data-slot=slider-track]]:bg-border"
      />
      <ValuePill>{wait.toFixed(1).replace(".", ",")} s</ValuePill>
    </div>
  )
}

function GpuRow() {
  const { state, t, send, patch } = useLoadedApp()
  const devices = gpuDevices(state)
  const [applying, setApplying] = useState(false)
  const [picked, setPicked] = useState("")
  const started = useRef(0)

  const raw = state.gpu_device as unknown
  const current =
    raw && typeof raw === "object"
      ? String((raw as { index?: number }).index ?? "auto")
      : String(raw ?? "auto")

  useEffect(() => {
    if (!applying) return
    const timer = window.setInterval(() => {
      const resolved =
        state.gpu_device && typeof state.gpu_device === "object"
          ? String((state.gpu_device as { index?: number }).index ?? "auto")
          : String(state.gpu_device ?? "auto")
      const elapsed = Date.now() - started.current
      if ((resolved === picked && elapsed > 2000) || elapsed > 15000) {
        setApplying(false)
      }
    }, 300)
    return () => window.clearInterval(timer)
  }, [applying, picked, state.gpu_device])

  if (!devices.length) return null

  const options: FieldOption[] = [
    { value: "auto", label: t("ui.gpuAuto") },
    ...devices.map((d) => ({
      value: String(d.index),
      label: gpuShortName(d.name),
      disabled: applying,
    })),
  ]

  const choose = (v: string) => {
    if (applying || v === current) return
    setApplying(true)
    setPicked(v)
    started.current = Date.now()
    patch({ gpu_device: v })
    void send("gpu_device", v === "auto" ? "auto" : { index: Number(v) })
  }

  const note = String(state.gpu_device_note || "").trim()

  return (
    <SettingsRow
      icon="gpu"
      title={t("ui.gpuTitle")}
      sub={
        <span className="flex flex-col gap-1">
          <span>{t("ui.gpuHint")}</span>
          {applying ? (
            <span className="inline-flex items-center gap-1.5 text-[10.5px] text-primary">
              <Spinner className="size-3" />
              {t("ui.gpuApplying")}
            </span>
          ) : null}
          {note ? <Hint>{note}</Hint> : null}
        </span>
      }
      control={
        <SelectField
          value={current}
          options={options}
          onChange={choose}
          disabled={applying}
          ariaLabel={t("ui.gpuAria")}
        />
      }
    />
  )
}

function MicTest() {
  const { state, t, send } = useLoadedApp()
  const [open, setOpen] = useState(false)
  const mt = state.mic_test || {}
  const active = !!mt.active
  const done = !active && !!mt.done

  const start = async () => {
    setOpen(true)
    await send("mic.test", active ? "stop" : "start")
  }

  const close = async () => {
    if (active) await send("mic.test", "stop")
    setOpen(false)
  }

  if (!open) {
    return (
      <SettingsRow
        icon="mic"
        title={t("ui.testRowTitle")}
        sub={t("ui.testRowHint")}
        control={
          <Button
            type="button"
            variant="secondary"
            size="icon-sm"
            className="size-8 rounded-lg"
            aria-label={t("ui.testStart")}
            onClick={() => void start()}
          >
            <Icon name="play" size={15} />
          </Button>
        }
      />
    )
  }

  const peak = Number(mt.peak) || 0
  const message = active
    ? t("ui.testHint")
    : mt.silent
      ? t("ui.testSilent")
      : peak < 0.05
        ? t("ui.testLow")
        : t("ui.testOk")

  return (
    <SettingsRow
      stack
      icon="mic"
      title={active ? t("ui.testTitle") : t("ui.testDone")}
      sub={message}
      control={
        <>
          <Button
            type="button"
            variant="secondary"
            size="icon-sm"
            className="size-8 rounded-lg"
            aria-label={t(active ? "ui.testStop" : "ui.testAgain")}
            onClick={() => void start()}
          >
            <Icon name={active ? "stop" : "refresh"} size={14} />
          </Button>
          <Button
            type="button"
            variant="ghost"
            size="icon-sm"
            className="size-8 rounded-lg"
            aria-label={t("ui.docClose")}
            onClick={() => void close()}
          >
            <Icon name="x" size={14} />
          </Button>
        </>
      }
    >
      {active ? (
        <div className="flex items-center gap-2 text-[11px] text-text-2">
          <Spinner className="size-3 text-primary" />
          {t("ui.testTitle")}
        </div>
      ) : done && mt.wav ? (
        <AudioPreview
          name="mictest.wav"
          src="/panel/mictest.wav"
          peaks={mt.peaks}
          duration={mt.duration}
          noWave
        />
      ) : null}
    </SettingsRow>
  )
}

export function DictationSection() {
  const { state, t, send, patch, locale } = useLoadedApp()
  const engines = engineOptions(state)
  const models = modelOptions(state)

  const engineFields: FieldOption[] = engines.map((o) => ({
    value: o.key,
    label: engineLabel(o.key, locale, o.label),
    // Sin notas de compatibilidad: el motor que no existe en este equipo se
    // muestra desactivado y ya.
    disabled: !o.available,
  }))

  return (
    <>
      <PaneHead title={t("ui.secDictation")} hint={t("ui.secDictationHint")} />

      <div className="space-y-3">
        <SettingsGroup
          title={t("ui.grpRecognition")}
          hint={t("ui.grpRecognitionHint")}
        >
          <SettingsRow
            icon="globe"
            title={t("ui.language")}
            sub={t("ui.languageHint")}
            control={
              <SelectField
                value={state.language === "en" ? "en" : "es"}
                options={LANG_CODES.map((c) => ({
                  value: c,
                  label: LANG_LABEL[c],
                }))}
                ariaLabel={t("ui.language")}
                onChange={(v) => {
                  patch({ language: v })
                  void send("language", v)
                }}
              />
            }
          />
          <SettingsRow
            icon="chip"
            title={t("ui.engine")}
            sub={t("ui.engineDesc")}
            control={
              <SelectField
                value={state.engine}
                options={engineFields}
                ariaLabel={t("ui.engine")}
                onChange={(v) => {
                  patch({ engine: v })
                  void send("engine", v)
                }}
              />
            }
          />
          <GpuRow />
          <SettingsRow
            icon="layers"
            title={t("ui.model")}
            sub={t("ui.modelHint")}
            control={
              <SelectField
                value={state.model}
                options={models}
                ariaLabel={t("ui.model")}
                onChange={(v) => {
                  patch({ model: v })
                  void send("model", v)
                }}
              />
            }
          />
        </SettingsGroup>

        <SettingsGroup>
          <SettingsRow
            icon="timer"
            title={t("ui.grpWait")}
            sub={t("ui.waitHint")}
            control={<WaitSlider />}
          />
        </SettingsGroup>

        <SettingsGroup
          title={t("ui.mic")}
          hint={t("ui.micGroupHint")}
        >
          <SettingsRow
            icon="mic"
            title={t("ui.micDevice")}
            sub={t("ui.micHint")}
            control={
              <SelectField
                value={String(state.mic ?? "")}
                options={state.mics.map((m) => ({
                  value: String(m.idx),
                  label: /asignador de sonido microsoft|microsoft sound mapper/i.test(
                    m.name,
                  )
                    ? t("ui.micSystemDefault")
                    : m.name,
                }))}
                ariaLabel={t("ui.micDevice")}
                onChange={(v) => {
                  patch({ mic: Number(v) })
                  void send("mic", Number(v))
                }}
              />
            }
          />
          <SettingsRow
            icon="sliders"
            title={t("ui.levelTitle")}
            sub={t("ui.levelHint")}
            control={<MicMeter />}
          />
          <MicTest />
        </SettingsGroup>

        <SettingsGroup title={t("ui.grpApp")}>
          <SettingsRow
            icon="refresh"
            title={t("ui.updAutoTitle")}
            sub={t("ui.updAutoHint")}
            control={
              <Switch
                checked={state.check_updates !== false}
                aria-label={t("ui.checkUpdates")}
                onCheckedChange={(on) => {
                  patch({ check_updates: on })
                  void send("check_updates", on)
                  if (on) void send("check_update")
                }}
                className="data-[state=unchecked]:bg-[var(--text-3)]/55"
              />
            }
          />
        </SettingsGroup>
      </div>
    </>
  )
}
