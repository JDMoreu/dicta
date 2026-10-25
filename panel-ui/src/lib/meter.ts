/**
 * Rampa de color del vúmetro, compartida por «Entrada y umbral» (Ajustes) y la
 * grabación de reunión. Seis tramos: verde → verde amarillento → amarillo →
 * naranja → naranja rojizo → rojo fuerte.
 *
 * Los colores viven en `index.css` como `--meter-1..6` (uno por tema), así el
 * mismo nivel se ve igual en toda la app y en claro/oscuro.
 */
export const METER_ZONES = 6

export function meterColorVar(index: number): string {
  const n = Math.max(0, Math.min(METER_ZONES - 1, index)) + 1
  return `var(--meter-${n})`
}

/** Índice de tramo (0..5) para un porcentaje 0..100 del recorrido. */
export function meterZone(pct: number): number {
  const p = Math.max(0, Math.min(100, pct))
  return Math.min(METER_ZONES - 1, Math.floor((p / 100) * METER_ZONES))
}
