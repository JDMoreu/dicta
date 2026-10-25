import { Icon } from "@/components/Icon"
import { PaneHead, SettingsGroup, SettingsRow } from "@/components/app-ui"
import { Segmented } from "@/components/fields"
import { useLoadedApp } from "@/lib/store"
import { cn } from "@/lib/utils"

const PALETTES = [
  {
    key: "grafito",
    light: ["#3dd9c4", "#5b9dff", "#9b7bff"],
    dark: ["#3dd9c4", "#5b9dff", "#9b7bff"],
  },
  {
    key: "oceano",
    light: ["#33b3f2", "#2973eb", "#4d47d9"],
    dark: ["#33b3f2", "#2973eb", "#4d47d9"],
  },
  {
    key: "ambar",
    light: ["#ffcc4d", "#ff9933", "#f27326"],
    dark: ["#ffcc4d", "#ff9933", "#f27326"],
  },
  {
    key: "menta",
    light: ["#4de699", "#33cc8c", "#26a699"],
    dark: ["#4de699", "#33cc8c", "#26a699"],
  },
  {
    key: "frambuesa",
    light: ["#ff6699", "#ff4073", "#d9338c"],
    dark: ["#ff6699", "#ff4073", "#d9338c"],
  },
  {
    key: "violeta",
    light: ["#b380ff", "#8c59ff", "#d966f2"],
    dark: ["#b380ff", "#8c59ff", "#d966f2"],
  },
]

const gradientOf = (pal: (typeof PALETTES)[number]) =>
  `linear-gradient(90deg, ${pal.light[0]}, ${pal.light[1]}, ${pal.light[2]})`

/**
 * Alturas de las 16 barras de la vista previa, derivadas de la MISMA silueta que
 * usa la isla real (8 valores base interpolados). Así el ajuste no diverge de lo
 * que se ve en pantalla.
 */
const ISLAND_BAR_H = (() => {
  const base = [0.21, 0.49, 0.3, 0.72, 0.4, 0.58, 0.26, 0.44]
  const n = 16
  return Array.from({ length: n }, (_, i) => {
    const t = (i / (n - 1)) * (base.length - 1)
    const lo = Math.floor(t)
    const hi = Math.min(base.length - 1, lo + 1)
    const v = base[lo] + (base[hi] - base[lo]) * (t - lo)
    return Math.round(6 + v * 20)      // 6..26 px dentro de 32
  })
})()

/**
 * Silueta REAL de la isla: cuerpo de 128 por 32 de alto. Arriba y en oscuro es
 * la muesca del diseño (`viewBox` 675x113) con el hombro subido a 7 px, porque
 * a 32 de alto el 12/113 se lee como un escalón: el hombro es un cuarto de
 * disco que se abre HACIA AFUERA (concavo) y las esquinas de abajo llevan
 * 45/113 del alto. En claro la muesca va recta arriba y solo redondea abajo.
 * En posición Abajo la isla flota y es una pastilla de 16 de radio.
 */
const NOTCH = (() => {
  const bodyW = 128
  const h = 32
  const f = 7
  const r = (h * 45) / 113
  const w = bodyW + 2 * f
  return { bodyW, w, h, f, r }
})()

function notchPath() {
  const { w, h, f, r } = NOTCH
  return [
    "M0 0",
    `A${f} ${f} 0 0 1 ${f} ${f}`,          // hombro izquierdo, se abre afuera
    `V${h - r}`,
    `A${r} ${r} 0 0 0 ${f + r} ${h}`,      // esquina inferior izquierda
    `H${w - f - r}`,
    `A${r} ${r} 0 0 0 ${w - f} ${h - r}`,  // esquina inferior derecha
    `V${f}`,
    `A${f} ${f} 0 0 1 ${w} 0`,             // hombro derecho
    "Z",
  ].join("")
}

function IslandPreview() {
  const { state } = useLoadedApp()
  const pal = PALETTES.find((p) => p.key === state.island_palette) || PALETTES[0]
  const top = state.island_pos !== "bottom"
  const dark = state.theme === "dark"

  return (
    <div className="relative mx-4 mt-3 mb-1 h-[86px] overflow-hidden rounded-lg bg-secondary/45 ring-1 ring-border/60">
      <div
        aria-hidden
        className="absolute inset-0 opacity-70"
        style={{
          background:
            "radial-gradient(80% 120% at 50% 0%, color-mix(in srgb, var(--brand-2) 9%, transparent), transparent 70%)",
        }}
      />
      <span
        aria-hidden
        className={cn(
          "absolute inset-x-0 h-px bg-border",
          top ? "top-0" : "bottom-0",
        )}
      />
      <div
        className={cn(
          "absolute inset-x-0 flex justify-center",
          // Abajo la isla flota a 10 px del borde (ISLAND_BOTTOM_GAP): si se
          // pegaba al canto parecía recortada.
          top ? "top-0" : "bottom-[10px]",
        )}
      >
        <div
          className={cn(
            // Geometría REAL de la isla: cuerpo de 128 por 32 y onda de 96 px
            // con 16 barras de 3 y 3 de hueco. Arriba y en oscuro, muesca con
            // hombros; en claro la muesca va recta arriba y solo redondea
            // abajo. En posición Abajo es una pastilla de 16 de radio.
            "flex items-center justify-center gap-[3px]",
            dark ? "bg-black" : "bg-white",
          )}
          style={
            !top
              ? {
                  width: NOTCH.bodyW,
                  height: NOTCH.h,
                  borderRadius: NOTCH.h / 2,
                }
              : dark
                ? {
                    width: NOTCH.w,
                    height: NOTCH.h,
                    clipPath: `path("${notchPath()}")`,
                  }
                : {
                    width: NOTCH.bodyW,
                    height: NOTCH.h,
                    borderRadius: `0 0 ${NOTCH.r}px ${NOTCH.r}px`,
                  }
          }
        >
          {ISLAND_BAR_H.map((h, i) => (
            <span
              key={i}
              className="w-[3px] shrink-0 rounded-full"
              style={{
                height: h,
                backgroundImage: gradientOf(pal),
                backgroundSize: "96px 100%",
                backgroundPosition: `${-i * 6}px 0`,
              }}
            />
          ))}
        </div>
      </div>
    </div>
  )
}

export function AppearanceSection() {
  const { state, t, send, patch } = useLoadedApp()
  const themeMode = state.theme_mode || (state.theme === "dark" ? "dark" : "light")

  return (
    <>
      <PaneHead title={t("ui.appearance")} hint={t("ui.appearanceHint")} />

      <div className="space-y-3">
        <SettingsGroup title={t("ui.grpTheme")} hint={t("ui.grpThemeHint")}>
          <SettingsRow
            icon={state.theme === "dark" ? "moon" : "sun"}
            title={t("ui.themeMode")}
            sub={t("ui.themeModeHint")}
            control={
              <Segmented
                value={themeMode}
                ariaLabel={t("ui.grpTheme")}
                onChange={(v) => {
                  const mode = v === "auto" ? "auto" : v === "dark" ? "dark" : "light"
                  const effective =
                    mode === "auto"
                      ? window.matchMedia("(prefers-color-scheme: dark)").matches
                        ? "dark"
                        : "light"
                      : mode
                  patch({ theme_mode: mode, theme: effective })
                  void send("theme", mode)
                }}
                options={[
                  {
                    value: "auto",
                    label: (
                      <span className="flex items-center gap-1.5">
                        <Icon name="monitor" size={13} />
                        {t("ui.themeAuto")}
                      </span>
                    ),
                  },
                  {
                    value: "light",
                    label: (
                      <span className="flex items-center gap-1.5">
                        <Icon name="sun" size={13} />
                        {t("ui.themeLight")}
                      </span>
                    ),
                  },
                  {
                    value: "dark",
                    label: (
                      <span className="flex items-center gap-1.5">
                        <Icon name="moon" size={13} />
                        {t("ui.themeDark")}
                      </span>
                    ),
                  },
                ]}
              />
            }
          />
        </SettingsGroup>

        <SettingsGroup title={t("ui.grpIsland")} hint={t("ui.grpIslandHint")}>
          <IslandPreview />
          <SettingsRow
            icon="monitor"
            title={t("ui.islandPos")}
            sub={t("ui.islandPosHint")}
            control={
              <Segmented
                value={state.island_pos === "bottom" ? "bottom" : "top"}
                ariaLabel={t("ui.islandPos")}
                onChange={(v) => {
                  patch({ island_pos: v })
                  void send("island_pos", v)
                }}
                options={[
                  { value: "top", label: t("ui.posTop") },
                  { value: "bottom", label: t("ui.posBottom") },
                ]}
              />
            }
          />
          <SettingsRow
            stack
            icon="sparkle"
            title={t("ui.islandPalette")}
            sub={t("ui.islandPaletteHint")}
          >
            <div className="grid grid-cols-3 gap-2">
              {PALETTES.map((pal) => {
                const selected = (state.island_palette || "grafito") === pal.key
                return (
                  <button
                    key={pal.key}
                    type="button"
                    aria-pressed={selected}
                    onClick={() => {
                      if (selected) return
                      patch({ island_palette: pal.key })
                      void send("island_palette", pal.key)
                    }}
                    className={cn(
                      "flex h-9 items-center gap-2 rounded-lg px-2 text-left outline-none transition-all",
                      "ring-1 focus-visible:ring-2 focus-visible:ring-ring/50",
                      selected
                        ? "bg-primary/6 ring-primary/35"
                        : "bg-secondary/45 ring-border/60 hover:bg-secondary",
                    )}
                  >
                    <span
                      className="h-4 w-9 shrink-0 rounded-full shadow-[inset_0_1px_1px_rgba(255,255,255,.35)]"
                      style={{ backgroundImage: gradientOf(pal) }}
                    />
                    <span
                      className={cn(
                        "min-w-0 flex-1 truncate text-[11px] font-medium",
                        selected ? "text-text" : "text-text-2",
                      )}
                    >
                      {t(`pal.${pal.key}`)}
                    </span>
                    {selected ? (
                      <Icon name="check" size={12} className="shrink-0 text-primary" />
                    ) : null}
                  </button>
                )
              })}
            </div>
          </SettingsRow>
        </SettingsGroup>
      </div>
    </>
  )
}
