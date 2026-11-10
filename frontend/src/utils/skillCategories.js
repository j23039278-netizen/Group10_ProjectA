// SEAGAS — One colour per skill category (skills_library.category), used wherever a
// student's skills are grouped, so each category looks the same on every page.
// Proficiency is shown with dots (●○○ / ●●○ / ●●●), not colours, so the two never clash.
export const SKILL_CATEGORIES = [
  { id: 'Technical',  title: 'Technical skills',    color: 'var(--s-cat-tech, #2d5be3)', bg: 'var(--s-cat-tech-bg, #eef3ff)', border: 'var(--s-cat-tech-border, #cddbfb)' },
  { id: 'AI_Digital', title: 'AI & digital skills', color: 'var(--s-cat-ai, #7c3aed)', bg: 'var(--s-cat-ai-bg, #f5f0ff)', border: 'var(--s-cat-ai-border, #e1d5fb)' },
  { id: 'Analytical', title: 'Analytical skills',   color: 'var(--s-cat-ana, #0f766e)', bg: 'var(--s-cat-ana-bg, #eaf7f5)', border: 'var(--s-cat-ana-border, #c5e8e3)' },
  { id: 'Soft',       title: 'Soft skills',         color: 'var(--s-cat-soft, #c2410c)', bg: 'var(--s-cat-soft-bg, #fff4ec)', border: 'var(--s-cat-soft-border, #fcd9c2)' },
]

export const LEVEL_DOTS = { beginner: 1, intermediate: 2, advanced: 3 }
export const levelDots = (level) => {
  const n = LEVEL_DOTS[level] || 1
  return '●'.repeat(n) + '○'.repeat(3 - n)
}
