// SEAGAS — One colour per skill category (skills_library.category), used wherever a
// student's skills are grouped, so each category looks the same on every page.
// Proficiency is shown with dots (●○○ / ●●○ / ●●●), not colours, so the two never clash.
export const SKILL_CATEGORIES = [
  { id: 'Technical',  title: 'Technical skills',    color: '#2d5be3', bg: '#eef3ff', border: '#cddbfb' },
  { id: 'AI_Digital', title: 'AI & digital skills', color: '#7c3aed', bg: '#f5f0ff', border: '#e1d5fb' },
  { id: 'Analytical', title: 'Analytical skills',   color: '#0f766e', bg: '#eaf7f5', border: '#c5e8e3' },
  { id: 'Soft',       title: 'Soft skills',         color: '#c2410c', bg: '#fff4ec', border: '#fcd9c2' },
]

export const LEVEL_DOTS = { beginner: 1, intermediate: 2, advanced: 3 }
export const levelDots = (level) => {
  const n = LEVEL_DOTS[level] || 1
  return '●'.repeat(n) + '○'.repeat(3 - n)
}
