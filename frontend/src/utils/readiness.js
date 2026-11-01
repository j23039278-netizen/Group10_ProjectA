// SEAGAS — Readiness colours, the same on every page: the bands of System Settings
// (On Track from, Needs Support below; defaults 70 and 40). The student and advisor
// portals call applyBands when they open.
let onTrack = 70
let needsSupport = 40

export function applyBands(settings) {
  onTrack = settings.readiness_on_track ?? onTrack
  needsSupport = settings.readiness_needs_support ?? needsSupport
}

export const readinessColor = (score) => {
  if (score == null) return '#8b92a8'
  const s = parseFloat(score)
  return s >= onTrack ? '#16a34a' : s >= needsSupport ? '#d97706' : '#dc2626'
}
