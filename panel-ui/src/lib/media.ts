import type { AppState } from "./api"
import { baseName, docStem, stripExt } from "./format"

export interface MediaItem {
  kind: "doc" | "upload"
  key: string
  stem: string
  name: string
  size: number
  duration: number
  play: string
  hasWav: boolean
  doc: string
  docName: string
  upName: string
  transcribe: boolean
  state: string
  progress: number
}

const finished = (st: string) => st === "listo" || st === "error"

function queueAudioMap(state: AppState) {
  const map = new Map<string, string>()
  ;(state.queue || []).forEach((q) => {
    const src = baseName(q.src)
    if (!src) return
    ;[q.doc, q.label, q.src].forEach((v) => {
      const k = docStem(v || "")
      if (k && !map.has(k)) map.set(k, src)
    })
  })
  return map
}

function uploadItems(state: AppState) {
  const qa = queueAudioMap(state)
  if (Array.isArray(state.uploads)) {
    return state.uploads.map((u) => ({
      name: String(u.name || ""),
      size: Number(u.size) || 0,
      duration: Number(u.duration) || 0,
      doc: baseName(u.doc),
      state: String(u.state || "pendiente"),
      progress: Number(u.progress) || 0,
      play:
        baseName(u.src || u.audio) || qa.get(docStem(u.name || "")) || "",
    }))
  }
  return (state.queue || []).map((q) => {
    const st = String(q.status || "")
    return {
      name: baseName(q.label || q.src),
      size: Number(q.size) || 0,
      duration: Number(q.duration) || 0,
      doc: baseName(q.doc),
      state: st.startsWith("error")
        ? "error"
        : st === "listo"
          ? "listo"
          : "transcribiendo",
      progress: Number(q.progress) || 0,
      play: baseName(q.src),
    }
  })
}

export function deriveMedia(state: AppState): MediaItem[] {
  const qa = queueAudioMap(state)
  const docs = (state.docs || [])
    .slice()
    .sort((a, b) => (Number(b.mtime) || 0) - (Number(a.mtime) || 0))
  const ups = uploadItems(state)
  const have = new Set<string>()
  const items: MediaItem[] = []

  const withExt = (n?: string) => {
    const s = String(n || "")
    if (!s) return ""
    return stripExt(s) !== s ? s : s + ".md"
  }

  const upByStem = new Map<string, (typeof ups)[number]>()
  ups.forEach((u) => {
    const k = docStem(u.doc || u.name)
    if (k && !upByStem.has(k)) upByStem.set(k, u)
  })

  const qStem = new Map<string, { status: string; progress: number }>()
  ;(state.queue || []).forEach((q) => {
    const k = docStem(baseName(q.doc || q.label || q.src))
    if (k && !qStem.has(k)) {
      qStem.set(k, {
        status: String(q.status || ""),
        progress: Number(q.progress) || 0,
      })
    }
  })

  const mt = state.meeting || ({} as AppState["meeting"])
  const mStem = mt.active ? docStem(baseName(mt.doc || "")) : ""
  const live: MediaItem[] = []
  if (mStem) {
    live.push({
      kind: "upload",
      key: "live:" + mStem,
      stem: mStem,
      name: baseName(mt.wav || mt.doc || "") || baseName(mt.doc || ""),
      size: 0,
      duration: Number(mt.seconds) || 0,
      play: "",
      hasWav: false,
      upName: "",
      docName: "",
      doc: "",
      transcribe: false,
      state: "transcribiendo",
      progress: -1,
    })
  }

  docs.forEach((d) => {
    const stem = docStem(d.name)
    if (stem) have.add(stem)
    if (mStem && stem === mStem) return
    const u = upByStem.get(stem)
    if (u && !finished(u.state)) return
    const own = baseName(d.audio)
    const audio = own || (u && u.play) || qa.get(stem) || ""
    items.push({
      kind: "doc",
      key: "doc:" + d.name,
      stem,
      name: (u && u.name) || own || d.name,
      size:
        Number(u ? u.size : own ? Number(d.audio_size) || d.size : d.size) || 0,
      duration: Number(u ? u.duration : 0) || 0,
      play: audio,
      hasWav: !!own,
      doc: withExt(d.name),
      docName: withExt(d.name),
      upName: u ? u.name : "",
      transcribe: true,
      state: "listo",
      progress: 100,
    })
  })

  const pend: MediaItem[] = []
  ups.forEach((u) => {
    const stem = docStem(u.doc || u.name)
    if (stem && have.has(stem) && finished(u.state)) return
    const q = qStem.get(stem) || { status: "", progress: 0 }
    pend.push({
      kind: "upload",
      key: "up:" + u.name,
      stem,
      name: u.name,
      size: Number(u.size) || 0,
      duration: Number(u.duration) || 0,
      play: u.play || qa.get(docStem(u.name)) || "",
      hasWav: false,
      upName: u.name,
      docName: "",
      doc: "",
      transcribe: false,
      state: String(u.state || "pendiente"),
      progress: Number(u.progress) || Number(q.progress) || 0,
    })
  })

  return live.concat(pend, items)
}
