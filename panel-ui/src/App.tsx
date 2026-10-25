import { AppShell } from "@/components/app-shell"
import { AppProvider, useApp } from "@/lib/store"
import { TooltipProvider } from "@/components/ui/tooltip"
import { DictationSection } from "@/sections/dictation"
import { DictionarySection } from "@/sections/dictionary"
import { MeetingSection } from "@/sections/meeting"
import { MediaSection } from "@/sections/media"
import { ShortcutsSection } from "@/sections/shortcuts"
import { AppearanceSection } from "@/sections/appearance"

function Boot() {
  return (
    <div className="grid h-full place-items-center bg-background">
      <div className="flex flex-col items-center gap-4">
        <div className="flex h-10 items-end gap-[4px]">
          {[12, 20, 31, 38, 27, 33, 18, 24, 13].map((h, i) => (
            <span
              key={i}
              className="w-[4px] animate-pulse rounded-full"
              style={{
                height: h,
                backgroundImage:
                  "linear-gradient(180deg, var(--brand-1), var(--brand-2) 55%, var(--brand-3))",
                animationDelay: `${i * 70}ms`,
                animationDuration: "1.2s",
              }}
            />
          ))}
        </div>
        <span className="text-[11px] font-medium tracking-[0.16em] text-text-3">
          Dicta
        </span>
      </div>
    </div>
  )
}

function Panes() {
  const { ready, section } = useApp()
  if (!ready) return <Boot />

  return (
    <AppShell>
      {section === "dictado" ? <DictationSection /> : null}
      {section === "diccionario" ? <DictionarySection /> : null}
      {section === "reunion" ? <MeetingSection /> : null}
      {section === "audios" ? <MediaSection /> : null}
      {section === "atajos" ? <ShortcutsSection /> : null}
      {section === "apariencia" ? <AppearanceSection /> : null}
    </AppShell>
  )
}

export default function App() {
  return (
    <AppProvider>
      <TooltipProvider delayDuration={280}>
        <Panes />
      </TooltipProvider>
    </AppProvider>
  )
}
