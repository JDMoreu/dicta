import {
  useEffect,
  useRef,
  useState,
  type DragEvent,
} from "react"
import { Icon } from "@/components/Icon"
import { AudioPreview } from "@/components/audio-preview"
import { EmptyState, PaneHead, Spinner, Tag } from "@/components/app-ui"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { fetchDoc, rpcRaw, uploadFiles, type AppState } from "@/lib/api"
import { baseName, docStem, fmtSize, fmtTime, stripExt } from "@/lib/format"
import { deriveMedia, type MediaItem } from "@/lib/media"
import { useLoadedApp } from "@/lib/store"
import { cn } from "@/lib/utils"

const UPLOAD_STATE: Record<string, { key: string; tone: string }> = {
  pendiente: { key: "ui.stPending", tone: "wait" },
  transcribiendo: { key: "ui.statusTranscribing", tone: "run" },
  listo: { key: "ui.saved", tone: "ok" },
  error: { key: "ui.stError", tone: "err" },
}

function noteToneClass(tone: string) {
  if (tone === "ok") return "text-success"
  if (tone === "err") return "text-destructive"
  return "text-text-2"
}

function MediaCard({
  item,
  focusStem,
  onFocused,
}: {
  item: MediaItem
  focusStem: string
  onFocused: () => void
}) {
  const { state, t, send, refresh, patch } = useLoadedApp()
  const cardRef = useRef<HTMLDivElement | null>(null)
  const [open, setOpen] = useState(false)
  const [text, setText] = useState<string | null>(null)
  const [failed, setFailed] = useState(false)
  const [armed, setArmed] = useState(false)
  const [renaming, setRenaming] = useState(false)
  const [draft, setDraft] = useState("")
  const [renameErr, setRenameErr] = useState("")
  const [busy, setBusy] = useState(false)
  const [note, setNote] = useState("")
  const [noteTone, setNoteTone] = useState("wait")
  const [flash, setFlash] = useState(false)
  const armTimer = useRef(0)
  const noteTimer = useRef(0)
  const renameInput = useRef<HTMLInputElement | null>(null)
  const renameDone = useRef(false)

  useEffect(() => {
    return () => {
      window.clearTimeout(armTimer.current)
      window.clearTimeout(noteTimer.current)
    }
  }, [])

  useEffect(() => {
    if (!focusStem || focusStem !== item.stem) return
    setFlash(true)
    cardRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" })
    const timer = window.setTimeout(() => setFlash(false), 2200)
    const done = window.setTimeout(onFocused, 1500)
    return () => {
      window.clearTimeout(timer)
      window.clearTimeout(done)
    }
  }, [focusStem, item.stem, onFocused])

  useEffect(() => {
    if (!open || text !== null || failed || !item.doc) return
    let alive = true
    void fetchDoc(item.doc).then((txt) => {
      if (!alive) return
      if (txt === null) setFailed(true)
      else setText(txt)
    })
    return () => {
      alive = false
    }
  }, [open, text, failed, item.doc])

  useEffect(() => {
    if (renaming) {
      renameDone.current = false
      window.setTimeout(() => {
        renameInput.current?.focus()
        renameInput.current?.select()
      }, 0)
    }
  }, [renaming])

  const showNote = (msg: string, tone: string, hold = 0) => {
    setNote(msg)
    setNoteTone(tone)
    window.clearTimeout(noteTimer.current)
    if (hold) noteTimer.current = window.setTimeout(() => setNote(""), hold)
  }

  const arm = () => {
    if (armed) {
      setArmed(false)
      window.clearTimeout(armTimer.current)
      void remove()
      return
    }
    setArmed(true)
    window.clearTimeout(armTimer.current)
    armTimer.current = window.setTimeout(() => setArmed(false), 2600)
  }

  const remove = async () => {
    if (busy) return
    setBusy(true)
    const doc = item.doc
    const up = item.upName
    if (doc) {
      await rpcRaw({ action: "doc.delete", doc })
      patch({
        docs: state.docs.filter((d) => baseName(d.name) !== doc),
      })
    }
    if (up) {
      await send("upload.remove", up)
      patch({
        uploads: (state.uploads || []).filter((u) => u.name !== up),
      })
    } else {
      await refresh()
    }
    setBusy(false)
  }

  const commitRename = async () => {
    if (renameDone.current) return
    const val = draft.trim()
    const original = stripExt(baseName(item.docName || item.name))
    if (!val || val === original) {
      renameDone.current = true
      setRenaming(false)
      return
    }
    renameDone.current = true
    const res = await rpcRaw({
      action: "doc.rename",
      doc: baseName(item.docName),
      name: val,
    })
    if (res.ok) {
      setRenaming(false)
      setRenameErr("")
      await refresh()
    } else {
      renameDone.current = false
      setRenameErr(res.error === "exists" ? t("ui.docExists") : t("ui.docRenameFail"))
      window.setTimeout(() => {
        renameInput.current?.focus()
        renameInput.current?.select()
      }, 0)
    }
  }

  const exportAs = async (kind: "md" | "txt" | "wav") => {
    if (busy) return
    setBusy(true)
    showNote(t("ui.saveChoose"), "wait")
    const name = kind === "wav" ? item.play : item.stem
    const res = await send("export", { name, kind })
    setBusy(false)
    if (res.ok === true && res.path) {
      showNote(`${t("ui.saveDone")} ${res.path}`, "ok", 12000)
    } else if (res.ok === true && res.canceled) {
      showNote(t("ui.saveCancel"), "wait", 4000)
    } else {
      showNote(t("ui.saveFail"), "err", 8000)
    }
  }

  const ext = (item.name.split(".").pop() || "").toLowerCase()
  const video = /^(mp4|mkv|mov|avi|webm|m4v|wmv)$/.test(ext)
  const icon = video ? "monitor" : item.play || item.transcribe ? "file-audio" : "file-text"
  const st = UPLOAD_STATE[item.state] || UPLOAD_STATE.pendiente
  const prog =
    item.state === "listo" || item.state === "error" || Number(item.progress) < 0
      ? -1
      : Math.max(0, Math.min(100, Number(item.progress) || 0))
  const meta = [
    item.size ? fmtSize(item.size) : "",
    item.duration ? fmtTime(item.duration, true) : "",
  ]
    .filter(Boolean)
    .join("  ·  ")

  return (
    <article
      ref={cardRef}
      className={cn(
        "overflow-hidden rounded-xl bg-card ring-1 transition-shadow",
        flash ? "ring-2 ring-primary/45 shadow-lift" : "ring-border",
      )}
    >
      <div className="flex items-center gap-3 px-3.5 py-3">
        <span className="grid size-8 shrink-0 place-items-center rounded-lg bg-primary/10 text-primary">
          <Icon name={icon} size={15} />
        </span>
        <div className="min-w-0 flex-1">
          {renaming ? (
            <div className="flex min-w-0 items-center gap-0.5">
              <Input
                ref={renameInput}
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault()
                    void commitRename()
                  } else if (e.key === "Escape") {
                    e.preventDefault()
                    renameDone.current = true
                    setRenaming(false)
                    setRenameErr("")
                  }
                }}
                onBlur={() => void commitRename()}
                spellCheck={false}
                className="h-6 min-w-0 rounded-md border-0 bg-secondary px-1.5 py-0 text-[12.5px] font-medium shadow-none ring-1 ring-border focus-visible:ring-2 focus-visible:ring-ring/50"
              />
              <span className="shrink-0 text-[11px] text-text-3">.md</span>
            </div>
          ) : (
            <div
              className="truncate text-[12.5px] font-medium text-text"
              title={item.name}
            >
              {item.name}
            </div>
          )}
          <div className="mt-0.5 flex min-h-[14px] items-center gap-2">
            {meta ? (
              <span className="text-[10.5px] text-text-3 tabular-nums">{meta}</span>
            ) : null}
            {renameErr ? (
              <span className="text-[10.5px] text-destructive">{renameErr}</span>
            ) : null}
          </div>
        </div>

        <div className="flex shrink-0 items-center gap-1">
          {item.transcribe ? (
            <Button
              type="button"
              variant="secondary"
              size="icon-sm"
              className="size-8 rounded-lg"
              aria-expanded={open}
              aria-label={t("ui.transcriptToggle")}
              title={t("ui.transcriptToggle")}
              onClick={() => setOpen((v) => !v)}
            >
              <Icon
                name="chevron-right"
                size={14}
                className={cn("transition-transform", open && "rotate-90")}
              />
            </Button>
          ) : null}
          {item.transcribe && item.doc ? (
            <Button
              type="button"
              variant="secondary"
              size="icon-sm"
              className="size-8 rounded-lg"
              aria-label={t("ui.docRename")}
              title={t("ui.docRename")}
              onClick={() => {
                setDraft(stripExt(baseName(item.docName || item.name)))
                setRenameErr("")
                setRenaming(true)
              }}
            >
              <Icon name="pencil" size={13} />
            </Button>
          ) : null}
          <Button
            type="button"
            variant={armed ? "destructive" : "secondary"}
            size="sm"
            className={cn(
              "h-8 rounded-lg",
              armed ? "gap-1.5 px-2 text-[10.5px] text-white" : "w-8 px-0",
            )}
            disabled={busy || (!item.doc && !item.upName)}
            aria-label={t(armed ? "ui.confirmDelete" : "ui.docDelete")}
            title={t(armed ? "ui.confirmDelete" : "ui.docDelete")}
            onClick={arm}
          >
            {busy ? (
              <Spinner className="size-3" />
            ) : (
              <>
                <Icon name="trash" size={13} />
                {armed ? t("ui.confirmDelete") : null}
              </>
            )}
          </Button>
        </div>
      </div>

      {item.play ? (
        <div className="px-3.5 pb-3">
          <AudioPreview name={item.play} />
        </div>
      ) : (
        <div className="h-3" />
      )}

      {!item.transcribe ? (
        <div className="flex items-center gap-2 px-3.5 pb-3">
          <Tag tone={st.tone as "wait" | "run" | "ok" | "err"}>
            {t(st.key)}
            {prog >= 0 ? ` ${Math.round(prog)}%` : ""}
          </Tag>
          {prog >= 0 ? (
            <span className="h-1 min-w-0 flex-1 overflow-hidden rounded-full bg-border/70">
              <span
                className="block h-full rounded-full bg-primary transition-[width] duration-300"
                style={{ width: `${prog}%` }}
              />
            </span>
          ) : (
            <span className="text-[10.5px] text-text-3">
              {item.state === "transcribiendo" ? t("ui.statusTranscribing") : ""}
            </span>
          )}
        </div>
      ) : null}

      {open && item.transcribe ? (
        <div className="border-t border-border/70 px-3.5 py-3">
          <div className="mb-1.5 text-[10.5px] font-medium tracking-[0.04em] text-text-3 uppercase">
            {t("ui.docTranscript")}
          </div>
          {failed ? (
            <div className="flex items-center gap-2 text-[11.5px] text-destructive">
              {t("ui.docLoadFail")}
              <button
                type="button"
                className="font-medium underline underline-offset-2"
                onClick={() => {
                  setFailed(false)
                  setText(null)
                }}
              >
                {t("ui.testAgain")}
              </button>
            </div>
          ) : text === null ? (
            <div className="flex items-center gap-2 py-1 text-[11.5px] text-text-2">
              <Spinner className="size-3" />
              {t("ui.docLoading")}
            </div>
          ) : (
            <div
              tabIndex={0}
              role="region"
              aria-label={t("ui.docTranscript")}
              className="max-h-[280px] overflow-auto overscroll-contain rounded-lg bg-secondary/45 px-3 py-2.5 text-[12px] leading-relaxed whitespace-pre-wrap text-text ring-1 ring-border/50"
            >
              {text || t("ui.docLoading")}
            </div>
          )}
        </div>
      ) : null}

      {item.transcribe ? (
        <div className="flex flex-wrap items-center gap-1.5 border-t border-border/70 px-3.5 py-2">
          <Button
            type="button"
            variant="ghost"
            size="sm"
            disabled={busy}
            className="h-7 gap-1.5 rounded-md px-2 text-[10.5px] text-text-2"
            aria-label={t("ui.dlDocMd")}
            title={t("ui.dlDocMd")}
            onClick={() => void exportAs("md")}
          >
            <Icon name="file-text" size={12} />
            .md
          </Button>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            disabled={busy}
            className="h-7 gap-1.5 rounded-md px-2 text-[10.5px] text-text-2"
            aria-label={t("ui.dlDocTxt")}
            title={t("ui.dlDocTxt")}
            onClick={() => void exportAs("txt")}
          >
            <Icon name="download" size={12} />
            .txt
          </Button>
          {item.hasWav ? (
            <Button
              type="button"
              variant="ghost"
              size="sm"
              disabled={busy}
              className="h-7 gap-1.5 rounded-md px-2 text-[10.5px] text-text-2"
              aria-label={t("ui.dlAudio")}
              title={t("ui.dlAudio")}
              onClick={() => void exportAs("wav")}
            >
              <Icon name="file-audio" size={12} />
              .wav
            </Button>
          ) : null}
          {note ? (
            <span
              className={cn(
                "ml-auto max-w-[55%] truncate text-[10.5px]",
                noteToneClass(noteTone),
              )}
              title={note}
            >
              {note}
            </span>
          ) : null}
        </div>
      ) : null}
    </article>
  )
}

export function MediaSection() {
  const { state, t, refresh } = useLoadedApp()
  const items = deriveMedia(state as AppState)
  const [uploading, setUploading] = useState(false)
  const [uploadNote, setUploadNote] = useState("")
  const [hover, setHover] = useState(false)
  const [focusStem, setFocusStem] = useState("")
  const inputRef = useRef<HTMLInputElement | null>(null)
  const dragDepth = useRef(0)

  useEffect(() => {
    const onFocus = (event: Event) => {
      const detail = (event as CustomEvent).detail
      const stem = docStem(baseName(String(detail || "")))
      if (stem) setFocusStem(stem)
    }
    window.addEventListener("dicta:focus-doc", onFocus)
    return () => window.removeEventListener("dicta:focus-doc", onFocus)
  }, [])

  const upload = async (files: FileList | File[] | null) => {
    const list = files ? Array.from(files) : []
    if (!list.length || uploading) return
    setUploading(true)
    setUploadNote("…")
    try {
      const res = await uploadFiles(list)
      if (!res.ok) throw new Error("upload")
      setUploadNote(`${list.length} →`)
      await refresh()
    } catch {
      setUploadNote("error")
    }
    setUploading(false)
    if (inputRef.current) inputRef.current.value = ""
    window.setTimeout(() => setUploadNote(""), 6000)
  }

  const onDrop = (e: DragEvent) => {
    e.preventDefault()
    dragDepth.current = 0
    setHover(false)
    void upload(e.dataTransfer.files)
  }

  return (
    <>
      <PaneHead title={t("ui.audiosDocs")} hint={t("ui.audiosDocsHint")}>
        {items.length ? (
          <span className="text-[11px] text-text-3 tabular-nums">
            {items.length}
          </span>
        ) : null}
      </PaneHead>

      <input
        ref={inputRef}
        type="file"
        multiple
        hidden
        accept="audio/*,video/*,.wav,.flac,.ogg,.mp3,.m4a,.aac,.wma,.opus,.mp4,.mkv,.mov,.webm,.avi"
        onChange={(e) => void upload(e.target.files)}
      />

      <button
        type="button"
        onClick={() => inputRef.current?.click()}
        onDragEnter={(e) => {
          e.preventDefault()
          dragDepth.current += 1
          setHover(true)
        }}
        onDragOver={(e) => {
          e.preventDefault()
          e.dataTransfer.dropEffect = "copy"
        }}
        onDragLeave={(e) => {
          e.preventDefault()
          dragDepth.current = Math.max(0, dragDepth.current - 1)
          if (!dragDepth.current) setHover(false)
        }}
        onDrop={onDrop}
        className={cn(
          "group mb-3 flex w-full items-center gap-3 rounded-xl border border-dashed px-4 py-3 text-left outline-none transition-colors",
          "focus-visible:ring-2 focus-visible:ring-ring/50",
          hover
            ? "border-primary/60 bg-primary/6"
            : "border-border bg-card/55 hover:border-primary/35 hover:bg-secondary/40",
        )}
      >
        <span className="grid size-8 shrink-0 place-items-center rounded-lg bg-primary/10 text-primary">
          {uploading ? <Spinner className="size-4" /> : <Icon name="upload" size={15} />}
        </span>
        <span className="min-w-0 flex-1">
          <span className="block text-[12px] font-medium text-text">
            {t(hover ? "ui.pickFiles" : "ui.addAudioPick")}
          </span>
          <span className="block truncate text-[10.5px] text-text-2">
            {t("ui.addAudioPickHint")}
          </span>
        </span>
        <span className="shrink-0 text-[11px] text-text-3">{uploadNote}</span>
        <span className="grid size-7 shrink-0 place-items-center rounded-md bg-secondary text-text-2 ring-1 ring-border/60 transition-colors group-hover:text-text">
          <Icon name="plus" size={14} />
        </span>
      </button>

      {items.length ? (
        <div className="space-y-2">
          {items.map((item) => (
            <MediaCard
              key={item.key}
              item={item}
              focusStem={focusStem}
              onFocused={() => setFocusStem("")}
            />
          ))}
        </div>
      ) : (
        <EmptyState icon="file-audio" title={t("ui.mediaEmpty")} />
      )}
      <span className="sr-only" aria-live="polite">
        {uploadNote}
      </span>
    </>
  )
}
