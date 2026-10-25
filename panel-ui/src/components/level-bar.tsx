import { Icon } from "@/components/Icon"
import { meterColorVar, meterZone } from "@/lib/meter"
import { cn } from "@/lib/utils"

/**
 * Suelo del medidor: -80 dBFS, el rango completo que muestra un vúmetro de voz.
 * Con este suelo el ruido de fondo de una sala enciende varias rayas (se ve que
 * la entrada está viva) y al hablar sube el resto del recorrido.
 */
const DB_FLOOR = -80
const DB_CEIL = 0
const SEGMENTS = 32

/**
 * Nivel de una fuente de audio, compacto: icono + nombre + rayas.
 *
 * Mismo lenguaje que el medidor de «Entrada y umbral» de Ajustes (rayas con
 * rampa de color), pero más bajo y más fino. Se coloca en una sola fila junto
 * al otro canal, por eso no lleva la cifra de dB al lado: queda en el `title`.
 */
export function LevelBar({
  label,
  icon,
  level,
  db,
  active,
  paused,
  className,
}: {
  label: string
  icon: string
  level?: number
  db?: number
  active: boolean
  paused?: boolean
  className?: string
}) {
  const dbNum = Number(db)
  const hasDb = Number.isFinite(dbNum)
  const rawLvl = Number(level)
  const pct = !hasDb
    ? Math.max(0, Math.min(1, Number.isFinite(rawLvl) ? rawLvl : 0)) * 100
    : Math.pow(
        Math.max(
          0,
          Math.min(1, (dbNum - DB_FLOOR) / (DB_CEIL - DB_FLOOR)),
        ),
        // Curva suave: el ruido de fondo (-60..-75 dB) se queda en la parte
        // baja pero visible, y la voz sube el resto del recorrido.
        0.65,
      ) * 100
  const shown = active && !paused ? pct : 0
  // Señal mínima visible: si hay algo de audio se encienden dos rayas aunque el
  // nivel caiga por debajo del suelo, para que se vea que la entrada está viva.
  const audible = active && !paused && hasDb && dbNum > -88
  const lit = Math.max(Math.round((shown / 100) * SEGMENTS), audible ? 3 : 0)
  const dbText = hasDb ? `${Math.round(Math.min(DB_CEIL, dbNum))} dB` : "—"

  return (
    <div className={cn("flex min-w-0 flex-1 items-center gap-2", className)}>
      <span className="grid size-[18px] shrink-0 place-items-center rounded-[5px] bg-secondary text-text-3 ring-1 ring-border/50">
        <Icon name={icon} size={10} />
      </span>
      <span className="w-[64px] shrink-0 truncate text-[11.5px] font-medium text-text-2">
        {label}
      </span>
      <span
        title={`${label}: ${dbText}`}
        className="flex h-[16px] min-w-0 flex-1 items-center gap-[2px] overflow-hidden rounded-[5px] bg-secondary/60 px-1.5 ring-1 ring-border/50 ring-inset"
        role="meter"
        aria-label={label}
        aria-valuemin={DB_FLOOR}
        aria-valuemax={DB_CEIL}
        aria-valuenow={hasDb ? Math.round(dbNum) : DB_FLOOR}
        aria-valuetext={dbText}
      >
        {Array.from({ length: SEGMENTS }, (_, i) => {
          const zone = meterZone(((i + 0.5) / SEGMENTS) * 100)
          const on = i < lit
          return (
            <span
              key={i}
              className={cn(
                "h-[10px] min-w-0 flex-1 rounded-[2px] transition-[background-color,opacity] duration-100",
                on ? "" : "bg-border/70",
                paused && "opacity-40",
              )}
              style={on ? { backgroundColor: meterColorVar(zone) } : undefined}
            />
          )
        })}
      </span>
    </div>
  )
}
