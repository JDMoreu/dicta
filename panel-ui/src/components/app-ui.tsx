import type { ComponentProps, ReactNode } from "react"
import { Button } from "@/components/ui/button"
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import { Icon } from "@/components/Icon"
import { cn } from "@/lib/utils"

export function PaneHead({
  title,
  hint,
  children,
}: {
  title: string
  hint?: string
  children?: ReactNode
}) {
  return (
    <div className="mb-4 flex items-end justify-between gap-4 px-0.5">
      <div className="min-w-0">
        <h2 className="text-[19px] leading-6 font-semibold tracking-[-0.012em]">
          {title}
        </h2>
        {hint ? (
          <p className="mt-0.5 text-[12px] leading-4 text-muted-foreground">
            {hint}
          </p>
        ) : null}
      </div>
      {children}
    </div>
  )
}

export function SettingsGroup({
  title,
  hint,
  children,
  className,
  action,
}: {
  title?: string
  hint?: string
  children: ReactNode
  className?: string
  action?: ReactNode
}) {
  return (
    <section
      className={cn(
        "overflow-hidden rounded-[14px] bg-card shadow-lift",
        className,
      )}
    >
      {title || hint || action ? (
        <header className="flex items-center justify-between gap-3 px-4 pt-3.5 pb-2.5">
          <h3 className="text-[12.5px] leading-4 font-semibold tracking-[0.005em]">
            {title}
          </h3>
          {action ?? (
            <span className="max-w-[62%] text-right text-[11px] leading-4 text-muted-foreground">
              {hint}
            </span>
          )}
        </header>
      ) : null}
      <div className="divide-y divide-border/60">{children}</div>
    </section>
  )
}

export function Tile({
  icon,
  tone = "accent",
  size = 16,
  className,
}: {
  icon: string
  tone?: "accent" | "danger" | "ok" | "neutral"
  size?: number
  className?: string
}) {
  return (
    <span
      className={cn(
        "grid size-8 shrink-0 place-items-center rounded-[10px] ring-1",
        tone === "accent" &&
          "bg-primary/9 text-primary ring-primary/12 dark:bg-primary/12",
        tone === "danger" &&
          "bg-destructive/9 text-destructive ring-destructive/15",
        tone === "ok" && "bg-success/10 text-success ring-success/15",
        tone === "neutral" &&
          "bg-secondary text-muted-foreground ring-border",
        className,
      )}
    >
      <Icon name={icon} size={size} />
    </span>
  )
}

export function SettingsRow({
  icon,
  title,
  sub,
  control,
  children,
  tone,
  className,
  stack,
}: {
  icon: string
  title: ReactNode
  sub?: ReactNode
  control?: ReactNode
  children?: ReactNode
  tone?: "accent" | "danger" | "ok" | "neutral"
  className?: string
  stack?: boolean
}) {
  if (stack) {
    return (
      <div className={cn("px-4 py-3.5", className)}>
        <div className="flex items-start gap-3">
          <Tile icon={icon} tone={tone} />
          <div className="min-w-0 flex-1 pt-0.5">
            <div className="text-[13px] leading-[18px] font-semibold">
              {title}
            </div>
            {sub ? (
              <div className="mt-0.5 text-[11.5px] leading-4 text-muted-foreground">
                {sub}
              </div>
            ) : null}
          </div>
          {control ? <div className="flex shrink-0 items-center gap-2">{control}</div> : null}
        </div>
        {children ? <div className="mt-3">{children}</div> : null}
      </div>
    )
  }
  return (
    <div
      className={cn(
        "flex min-h-[56px] items-center gap-3 px-4 py-2.5",
        className,
      )}
    >
      <Tile icon={icon} tone={tone} />
      <div className="min-w-0 flex-1">
        <div className="text-[13px] leading-[18px] font-semibold">{title}</div>
        {sub ? (
          <div className="mt-0.5 text-[11.5px] leading-4 text-muted-foreground">
            {sub}
          </div>
        ) : null}
      </div>
      {control ? (
        <div className="flex shrink-0 items-center gap-2">{control}</div>
      ) : null}
      {children}
    </div>
  )
}

export function ValuePill({
  children,
  className,
  tone = "neutral",
}: {
  children: ReactNode
  className?: string
  tone?: "neutral" | "accent" | "danger" | "ok"
}) {
  return (
    <span
      className={cn(
        // `leading-none` + un pelín de padding inferior: la caja de línea de la
        // fuente reserva espacio de descendente y el número quedaba pegado
        // arriba (más aire abajo que arriba). Así el texto queda centrado de
        // verdad dentro de la píldora.
        "inline-flex h-7 min-w-[54px] items-center justify-center rounded-full px-2.5 pt-[2px] pb-[2px] font-mono text-[11px] leading-none tabular-nums ring-1",
        tone === "neutral" &&
          "bg-secondary text-text-2 ring-border/80",
        tone === "accent" && "bg-primary/10 text-primary ring-primary/15",
        tone === "danger" &&
          "bg-destructive/10 text-destructive ring-destructive/15",
        tone === "ok" && "bg-success/10 text-success ring-success/15",
        className,
      )}
    >
      {children}
    </span>
  )
}

export function Tag({
  children,
  tone = "wait",
}: {
  children: ReactNode
  tone?: "wait" | "run" | "ok" | "err" | "neutral"
}) {
  return (
    <span
      className={cn(
        "inline-flex h-6 items-center gap-1.5 rounded-full px-2.5 text-[11px] font-semibold ring-1",
        tone === "wait" && "bg-secondary text-text-2 ring-border",
        tone === "run" && "bg-primary/10 text-primary ring-primary/15",
        tone === "ok" && "bg-success/10 text-success ring-success/15",
        tone === "err" &&
          "bg-destructive/10 text-destructive ring-destructive/15",
        tone === "neutral" && "bg-secondary text-muted-foreground ring-border",
      )}
    >
      {children}
    </span>
  )
}

export function Hint({
  children,
  className,
}: {
  children: ReactNode
  className?: string
}) {
  return (
    <p className={cn("text-[11.5px] leading-4 text-muted-foreground", className)}>
      {children}
    </p>
  )
}

export function TipButton({
  label,
  children,
  side = "top",
  ...props
}: ComponentProps<typeof Button> & {
  label: string
  side?: "top" | "bottom" | "left" | "right"
}) {
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <Button aria-label={label} {...props}>
          {children}
        </Button>
      </TooltipTrigger>
      <TooltipContent side={side}>{label}</TooltipContent>
    </Tooltip>
  )
}

export function EmptyState({
  icon,
  title,
  hint,
  action,
}: {
  icon: string
  title: string
  hint?: string
  action?: ReactNode
}) {
  return (
    <div className="flex flex-col items-center justify-center px-6 py-10 text-center">
      <div className="relative mb-3 grid size-12 place-items-center rounded-full bg-primary/8 text-primary ring-1 ring-primary/10">
        <span
          aria-hidden
          className="absolute inset-0 rounded-full opacity-40 blur-md"
          style={{ background: "var(--brand-gradient)" }}
        />
        <Icon name={icon} size={21} className="relative" />
      </div>
      <p className="max-w-[380px] text-[12.5px] leading-5 font-medium">
        {title}
      </p>
      {hint ? (
        <p className="mt-1 max-w-[380px] text-[11.5px] leading-4 text-muted-foreground">
          {hint}
        </p>
      ) : null}
      {action ? <div className="mt-4">{action}</div> : null}
    </div>
  )
}

export function Spinner({ className }: { className?: string }) {
  return (
    <span
      aria-hidden
      className={cn(
        "inline-block size-3.5 animate-spin rounded-full border-[1.5px] border-current border-t-transparent",
        className,
      )}
    />
  )
}

export function Divider() {
  return <div className="h-px bg-border/60" />
}
