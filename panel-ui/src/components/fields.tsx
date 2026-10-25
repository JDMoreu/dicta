import type { ReactNode } from "react"
import { Icon } from "@/components/Icon"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group"
import { cn } from "@/lib/utils"

export interface FieldOption {
  value: string
  label: string
  disabled?: boolean
  note?: string
  badge?: string
  icon?: string
}

export function SelectField({
  value,
  options,
  onChange,
  ariaLabel,
  className,
  disabled,
  placeholder,
}: {
  value: string
  options: FieldOption[]
  onChange: (value: string) => void
  ariaLabel: string
  className?: string
  disabled?: boolean
  placeholder?: string
}) {
  return (
    <Select value={value} onValueChange={onChange} disabled={disabled}>
      <SelectTrigger
        aria-label={ariaLabel}
        className={cn(
          "h-8 w-[228px] max-w-full rounded-[9px] border-border/80 bg-secondary px-2.5 text-[12.5px] font-medium shadow-none transition-colors hover:border-border hover:bg-secondary focus-visible:ring-2 focus-visible:ring-ring/40 data-[size=default]:h-8 data-[state=open]:rounded-b-none data-[state=open]:border-b-transparent dark:bg-secondary dark:hover:bg-secondary",
          className,
        )}
      >
        <SelectValue placeholder={placeholder} />
      </SelectTrigger>
      <SelectContent
        position="popper"
        align="end"
        side="bottom"
        sideOffset={0}
        avoidCollisions={false}
        collisionPadding={8}
        className="w-[var(--radix-select-trigger-width)] min-w-[var(--radix-select-trigger-width)] rounded-[9px] rounded-t-none border-border/80 border-t-foreground/15 bg-secondary shadow-[0_16px_32px_-18px_rgba(0,0,0,0.55)] [&_[data-slot=select-viewport]]:min-w-0"
      >
        {options.map((o) => (
          <SelectItem
            key={o.value}
            value={o.value}
            disabled={o.disabled}
            title={o.note || o.label}
            className="h-8 rounded-none pr-7 pl-2 text-[12.5px]"
          >
            {o.icon ? <Icon name={o.icon} size={14} /> : null}
            <span className="min-w-0 flex-1 truncate">{o.label}</span>
            {o.badge ? (
              <span className="shrink-0 rounded-full bg-primary/10 px-1.5 text-[10px] font-semibold text-primary">
                {o.badge}
              </span>
            ) : null}
            {o.note ? (
              <span className="min-w-0 max-w-[45%] truncate text-[10.5px] text-muted-foreground">
                {o.note}
              </span>
            ) : null}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )
}

export function Segmented({
  value,
  options,
  onChange,
  ariaLabel,
  className,
}: {
  value: string
  options: { value: string; label: ReactNode }[]
  onChange: (value: string) => void
  ariaLabel: string
  className?: string
}) {
  return (
    <ToggleGroup
      type="single"
      value={value}
      aria-label={ariaLabel}
      onValueChange={(v) => {
        if (v) onChange(v)
      }}
      className={cn(
        "h-8 gap-0 rounded-[10px] bg-secondary p-0.5 ring-1 ring-border/70",
        className,
      )}
    >
      {options.map((o) => (
        <ToggleGroupItem
          key={o.value}
          value={o.value}
          className="h-7 min-w-[64px] rounded-[8px] px-3 text-[12px] font-medium text-muted-foreground transition-colors data-[state=on]:bg-card data-[state=on]:text-foreground data-[state=on]:shadow-lift hover:text-foreground"
        >
          {o.label}
        </ToggleGroupItem>
      ))}
    </ToggleGroup>
  )
}
