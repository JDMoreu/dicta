import { useEffect, useRef, useState } from "react"
import { Icon } from "@/components/Icon"
import {
  EmptyState,
  PaneHead,
  SettingsGroup,
  SettingsRow,
} from "@/components/app-ui"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { useLoadedApp } from "@/lib/store"
import { cn } from "@/lib/utils"

export function DictionarySection() {
  const { state, t, send, patch } = useLoadedApp()
  const [value, setValue] = useState("")
  const [confirm, setConfirm] = useState<string | null>(null)
  const timer = useRef(0)

  const words = state.dictionary || []

  useEffect(() => {
    return () => window.clearTimeout(timer.current)
  }, [])

  const arm = (word: string) => {
    if (confirm === word) {
      window.clearTimeout(timer.current)
      setConfirm(null)
      const next = words.filter((w) => w !== word)
      patch({ dictionary: next })
      void send("dictionary", next)
      return
    }
    setConfirm(word)
    window.clearTimeout(timer.current)
    timer.current = window.setTimeout(() => setConfirm(null), 2600)
  }

  const add = () => {
    const raw = value.trim()
    if (!raw) return
    const parts = raw
      .split(/[,\n]+/)
      .map((s) => s.trim())
      .filter(Boolean)
    if (!parts.length) return
    const next = words.slice()
    let changed = false
    for (const w of parts) {
      if (!next.some((v) => v.toLowerCase() === w.toLowerCase())) {
        next.push(w)
        changed = true
      }
    }
    setValue("")
    if (changed) {
      patch({ dictionary: next })
      void send("dictionary", next)
    }
  }

  return (
    <>
      <PaneHead title={t("ui.dict")} hint={t("ui.dictPaneHint")} />

      <div className="space-y-3">
        <SettingsGroup title={t("ui.dictTerms")}>
          <div className="px-4 py-3.5">
            <div className="flex items-start gap-2">
              <Textarea
                rows={1}
                value={value}
                onChange={(e) => setValue(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault()
                    add()
                  }
                }}
                placeholder={t("ui.dictPlaceholder")}
                className="min-h-9 resize-none rounded-[9px] border-0 bg-secondary px-3 py-2 text-[12.5px] leading-5 shadow-none ring-1 ring-border/70 focus-visible:ring-2 focus-visible:ring-ring/40"
              />
              <Button
                type="button"
                size="icon-sm"
                variant="secondary"
                className="size-9 shrink-0 rounded-[9px] ring-1 ring-border/70"
                aria-label={t("ui.dictAdd")}
                onClick={add}
              >
                <Icon name="plus" size={15} />
              </Button>
            </div>

            {words.length ? (
              <div className="flex flex-wrap gap-1.5 pt-2.5">
                {words.map((w) => {
                  const armed = confirm === w
                  return (
                    <span
                      key={w}
                      className={cn(
                        "inline-flex h-7 items-center gap-1 rounded-full pr-1 pl-2.5 text-[11.5px] font-medium ring-1 transition-colors",
                        armed
                          ? "bg-destructive/10 text-destructive ring-destructive/25"
                          : "bg-secondary text-text-2 ring-border/70",
                      )}
                    >
                      <span>{armed ? t("ui.confirmRemove") : w}</span>
                      <button
                        type="button"
                        className={cn(
                          "grid size-5 place-items-center rounded-full outline-none transition-colors",
                          "hover:bg-black/10 focus-visible:ring-2 focus-visible:ring-ring/60 dark:hover:bg-white/10",
                          armed && "text-destructive",
                        )}
                        aria-label={
                          armed
                            ? t("ui.confirmRemove")
                            : `${t("ui.remove")} ${w}`
                        }
                        title={
                          armed
                            ? t("ui.confirmRemove")
                            : `${t("ui.remove")} ${w}`
                        }
                        onClick={() => arm(w)}
                      >
                        <Icon name="x" size={10} strokeWidth={2.4} />
                      </button>
                    </span>
                  )
                })}
              </div>
            ) : (
              <EmptyState
                icon="book"
                title={t("ui.dictEmpty")}
                hint={t("ui.dictMultiHint")}
              />
            )}
          </div>
        </SettingsGroup>

        <SettingsGroup title={t("ui.dictHow")}>
          <SettingsRow
            icon="sparkle"
            title={t("ui.dictPrompt")}
            sub={t("ui.dictPromptHint")}
          />
          <SettingsRow
            icon="folder"
            title={t("ui.dictStored")}
            sub={t("ui.dictStoredHint")}
          />
        </SettingsGroup>
      </div>
    </>
  )
}
