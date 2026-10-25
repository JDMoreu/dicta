import { useEffect, useRef, useState } from "react"
import { Icon } from "@/components/Icon"
import { Button } from "@/components/ui/button"
import { audioSrc, fetchPeaks, type Peaks } from "@/lib/api"
import { fmtTime } from "@/lib/format"
import { cn } from "@/lib/utils"

function readColors() {
  const cs = getComputedStyle(document.documentElement)
  return {
    accent: cs.getPropertyValue("--primary").trim() || "#0066cc",
    dim: cs.getPropertyValue("--text-3").trim() || "#67676d",
  }
}

export function AudioPreview({
  name,
  src,
  peaks: peaksOverride,
  duration,
  noWave,
  className,
}: {
  name: string
  src?: string
  peaks?: number[]
  duration?: number
  noWave?: boolean
  className?: string
}) {
  const audioRef = useRef<HTMLAudioElement | null>(null)
  const canvasRef = useRef<HTMLCanvasElement | null>(null)
  const rafRef = useRef(0)
  const drawRef = useRef<() => void>(() => {})
  const lastTick = useRef(0)
  const [peaks, setPeaks] = useState<number[]>(peaksOverride || [])
  const [dur, setDur] = useState(Number(duration) || 0)
  const [time, setTime] = useState(0)
  const [playing, setPlaying] = useState(false)

  useEffect(() => {
    if (peaksOverride) {
      setPeaks(peaksOverride)
      return
    }
    let alive = true
    void fetchPeaks(name).then((p: Peaks | null) => {
      if (!alive || !p) return
      setPeaks(p.peaks)
      setDur((d) => (d > 0 ? d : p.dur))
    })
    return () => {
      alive = false
    }
  }, [name, peaksOverride])

  useEffect(() => {
    setDur(Number(duration) || 0)
  }, [duration])

  const total = dur || 0
  const ratio = total > 0 ? Math.min(1, time / total) : 0

  const draw = () => {
    const canvas = canvasRef.current
    if (!canvas) return
    const rect = canvas.getBoundingClientRect()
    if (!rect.width || !rect.height) return
    const dpr = Math.min(2, window.devicePixelRatio || 1)
    if (canvas.width !== Math.round(rect.width * dpr)) {
      canvas.width = Math.round(rect.width * dpr)
    }
    if (canvas.height !== Math.round(rect.height * dpr)) {
      canvas.height = Math.round(rect.height * dpr)
    }
    const ctx = canvas.getContext("2d")
    if (!ctx) return
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
    ctx.clearRect(0, 0, rect.width, rect.height)
    const colors = readColors()
    const bars = Math.max(24, Math.min(240, Math.floor(rect.width / 3.2)))
    const mid = rect.height / 2
    const gap = 1.1
    const bw = Math.max(1, rect.width / bars - gap)
    const src = peaks.length ? peaks : Array.from({ length: bars }, () => 0.14)
    const played = Math.round(bars * ratio)
    for (let i = 0; i < bars; i++) {
      const at = Math.min(src.length - 1, Math.round((i / bars) * src.length))
      const v = Math.max(0.05, Math.min(1, Number(src[at]) || 0))
      const h = Math.max(2, v * (rect.height - 4))
      const x = i * (rect.width / bars)
      ctx.globalAlpha = i < played ? 1 : 0.42
      ctx.fillStyle = i < played ? colors.accent : colors.dim
      const r = Math.min(bw / 2, 1.5)
      ctx.beginPath()
      ctx.roundRect(x, mid - h / 2, bw, h, r)
      ctx.fill()
    }
    ctx.globalAlpha = 1
    if (played > 0 && played < bars) {
      const x = (played / bars) * rect.width
      ctx.fillStyle = colors.accent
      ctx.fillRect(x, 2, 1.5, rect.height - 4)
    }
  }

  drawRef.current = draw

  useEffect(() => {
    drawRef.current()
  }, [peaks, time])

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas || typeof ResizeObserver === "undefined") return
    const ro = new ResizeObserver(() => drawRef.current())
    ro.observe(canvas)
    return () => ro.disconnect()
  }, [])

  useEffect(() => {
    const obs = new MutationObserver(() => drawRef.current())
    obs.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ["class", "data-theme"],
    })
    return () => obs.disconnect()
  }, [])

  const animate = (ts = 0) => {
    const audio = audioRef.current
    if (!audio) return
    drawRef.current()
    if (ts - lastTick.current > 240) {
      lastTick.current = ts
      setTime(audio.currentTime || 0)
    }
    if (!audio.paused) rafRef.current = requestAnimationFrame(animate)
  }

  const toggle = async () => {
    const audio = audioRef.current
    if (!audio) return
    if (!audio.paused) {
      audio.pause()
      return
    }
    try {
      await audio.play()
    } catch {
      /* noop */
    }
  }

  const seek = (clientX: number, el: HTMLElement) => {
    const audio = audioRef.current
    if (!audio || !total) return
    const r = el.getBoundingClientRect()
    const p = Math.min(1, Math.max(0, (clientX - r.left) / r.width))
    audio.currentTime = p * total
    setTime(audio.currentTime)
    drawRef.current()
  }

  return (
    <div
      className={cn(
        "flex items-center gap-2.5 rounded-[12px] bg-secondary/70 px-2 py-1.5 ring-1 ring-border/50",
        className,
      )}
    >
      <audio
        ref={audioRef}
        src={src || audioSrc(name)}
        preload="metadata"
        onPlay={() => {
          setPlaying(true)
          cancelAnimationFrame(rafRef.current)
          rafRef.current = requestAnimationFrame(animate)
        }}
        onPause={() => {
          setPlaying(false)
          cancelAnimationFrame(rafRef.current)
        }}
        onEnded={() => {
          setPlaying(false)
          setTime(0)
        }}
        onTimeUpdate={() => {
          if (audioRef.current) setTime(audioRef.current.currentTime || 0)
        }}
        onLoadedMetadata={() => {
          const a = audioRef.current
          if (a && isFinite(a.duration) && a.duration > 0) {
            setDur((d) => (d > 0 ? d : a.duration))
          }
        }}
      />
      <Button
        type="button"
        size="icon-sm"
        className="size-[30px] shrink-0 rounded-full shadow-none"
        onClick={() => void toggle()}
        aria-label={playing ? "Pause" : "Play"}
      >
        <Icon name={playing ? "pause" : "play"} size={13} />
      </Button>
      {noWave ? null : (
        <div
          role="slider"
          tabIndex={0}
          aria-label="Audio"
          aria-valuemin={0}
          aria-valuemax={100}
          aria-valuenow={Math.round(ratio * 100)}
          className="relative h-8 min-w-0 flex-1 cursor-pointer rounded-md outline-none focus-visible:ring-2 focus-visible:ring-ring/50"
          onPointerDown={(e) => {
            e.currentTarget.setPointerCapture(e.pointerId)
            seek(e.clientX, e.currentTarget)
          }}
          onPointerMove={(e) => {
            if (e.buttons === 1) seek(e.clientX, e.currentTarget)
          }}
          onKeyDown={(e) => {
            const audio = audioRef.current
            if (!audio) return
            if (e.key === " " || e.key === "Enter") {
              e.preventDefault()
              void toggle()
            } else if (e.key === "ArrowRight") {
              e.preventDefault()
              audio.currentTime = Math.min(total, audio.currentTime + 5)
            } else if (e.key === "ArrowLeft") {
              e.preventDefault()
              audio.currentTime = Math.max(0, audio.currentTime - 5)
            } else if (e.key === "Home") {
              e.preventDefault()
              audio.currentTime = 0
            } else if (e.key === "End") {
              e.preventDefault()
              audio.currentTime = total
            }
          }}
        >
          <canvas ref={canvasRef} className="block h-full w-full" />
        </div>
      )}
      <span className="shrink-0 font-mono text-[10.5px] tabular-nums text-text-2">
        {fmtTime(time)}
        {total > 0 ? ` / ${fmtTime(total)}` : ""}
      </span>
    </div>
  )
}
