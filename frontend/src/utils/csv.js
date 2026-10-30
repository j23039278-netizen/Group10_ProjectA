// SEAGAS — Download rows as a CSV file that Excel opens correctly (UTF-8 with BOM).
// columns: [{ label, value: row => any }]
const cell = (v) => {
  const s = v == null ? '' : String(v)
  return /[",\r\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s
}

export function downloadCsv(fileName, columns, rows) {
  const lines = [columns.map(c => cell(c.label)).join(',')]
  for (const row of rows) lines.push(columns.map(c => cell(c.value(row))).join(','))
  const blob = new Blob(['﻿' + lines.join('\r\n')], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = fileName
  a.click()
  URL.revokeObjectURL(url)
}

// e.g. "advisor_students_2026-10-30.csv"
export const csvName = (what) => `${what}_${new Date().toISOString().slice(0, 10)}.csv`
