// SEAGAS — Readiness colours, the same on every page: the bands of System Settings
// (On Track from, Needs Support below; defaults 70 and 40). The student and advisor
// portals call applyBands when they open. Scores keep bright green / yellow / red even in
// the black-and-red portal themes (--s-score-* can still override them).
let onTrack = 70
let needsSupport = 40

export function applyBands(settings) {
  onTrack = settings.readiness_on_track ?? onTrack
  needsSupport = settings.readiness_needs_support ?? needsSupport
}

export const readinessColor = (score) => {
  if (score == null) return 'var(--s-muted, #8b92a8)'
  const s = parseFloat(score)
  return s >= onTrack ? 'var(--s-score-good, #16a34a)'
    : s >= needsSupport ? 'var(--s-score-warn, #ca8a04)'
      : 'var(--s-score-bad, #dc2626)'
}
