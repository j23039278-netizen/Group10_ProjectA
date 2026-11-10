// SEAGAS — Choose a skill by typing (Profile → Skills), since a plain <select> cannot be searched.
// It opens like a dropdown and narrows as the student types; utils/skillSearch.js does the matching.
// skills = what can be chosen, added = library rows the student already has, value = chosen skill_id.
// The added ones are searched too, only to say so: otherwise "pyhton" would look for something else.
import { useEffect, useId, useRef, useState } from 'react'
import { label } from '../utils/labels'
import { isExactMatch, searchSkills } from '../utils/skillSearch'

const C = { ink: '#1a1f2e', body: '#4a5168', muted: '#8b92a8', line: '#e4e6ef', field: '#f5f6fa', active: '#eef3ff' }

export default function SkillPicker({ skills, added, value, onChange, emptyHint }) {
  const [query, setQuery]   = useState('')
  const [open, setOpen]     = useState(false)
  const [active, setActive] = useState(0)   // index of the highlighted result
  const input  = useRef(null)
  const panel  = useRef(null)
  const list   = useRef(null)
  const listId = useId()

  const chosen  = skills.find(s => s.skill_id === value)
  const matches = searchSkills([...skills, ...added], query)
  const results = matches.filter(m => !added.includes(m.skill))
  const typed   = query.trim()

  // Bring the whole list into view when it opens near the bottom of the page
  useEffect(() => {
    if (open) panel.current?.scrollIntoView({ block: 'nearest' })
  }, [open])

  // Keep the highlighted result in view while moving with the arrow keys
  useEffect(() => {
    if (open) list.current?.children[active]?.scrollIntoView({ block: 'nearest' })
  }, [open, active])

  // Keep a chosen name selected, so typing again replaces it
  useEffect(() => {
    if (value && document.activeElement === input.current) input.current.select()
  }, [value])

  const openList = () => {
    setOpen(true)
    setActive(Math.max(0, results.findIndex(r => r.skill.skill_id === value)))
  }

  const pick = (skill) => {
    onChange(skill.skill_id)
    setQuery('')
    setOpen(false)
  }

  const type = (text) => {
    if (value) onChange('')
    setQuery(text)
    setActive(0)
    setOpen(true)
  }

  const onKeyDown = (e) => {
    if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
      e.preventDefault()
      if (!open) openList()
      else if (results.length) {
        const step = e.key === 'ArrowDown' ? 1 : -1
        setActive((active + step + results.length) % results.length)
      }
    } else if (e.key === 'Enter' && open && results[active]) {
      e.preventDefault()
      pick(results[active].skill)
    } else if (e.key === 'Escape') {
      setOpen(false)
    }
  }

  // A whole name or alias typed counts as chosen, so Add works without opening the list
  const onBlur = () => {
    setOpen(false)
    if (!value && isExactMatch(results[0])) pick(results[0].skill)
  }

  // The best match is already added, and nothing that can be chosen matches as well
  const best = matches[0]
  const hasBest = best && added.includes(best.skill) && results[0]?.rank !== best.rank
  const message = hasBest ? `${best.skill.skill_name} is already in your skills.`
    : results.length ? ''
    : [typed ? `No skill found for "${typed}".` : 'No more skills to add here.', emptyHint].filter(Boolean).join(' ')

  return (
    <div style={{ position: 'relative', flex: 1, minWidth: '220px' }}>
      <input ref={input} type="text" role="combobox" aria-label="Search or select a skill" aria-autocomplete="list"
        aria-expanded={open} aria-controls={listId}
        aria-activedescendant={open && results[active] ? `${listId}-${active}` : undefined}
        autoComplete="off" spellCheck={false} placeholder="Search or select a skill..."
        value={chosen ? chosen.skill_name : query}
        onChange={e => type(e.target.value)} onKeyDown={onKeyDown} onBlur={onBlur}
        onClick={() => { if (!open) openList(); if (chosen) input.current.select() }}
        style={{ width: '100%', height: '100%', boxSizing: 'border-box', padding: '8px 30px 8px 12px', border: `1.5px solid ${C.line}`, borderRadius: '8px', fontSize: '13px', background: C.field, color: C.ink }} />
      <button type="button" tabIndex={-1} aria-hidden="true"
        onMouseDown={e => { e.preventDefault(); input.current.focus(); if (open) setOpen(false); else openList() }}
        style={{ position: 'absolute', top: 0, bottom: 0, right: '4px', width: '26px', border: 'none', background: 'none', padding: 0, cursor: 'pointer', color: C.body }}>
        <svg width="10" height="6" viewBox="0 0 10 6" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M1 1l4 4 4-4" /></svg>
      </button>
      {open && (
        <div ref={panel} onMouseDown={e => e.preventDefault()}
          style={{ position: 'absolute', top: 'calc(100% + 4px)', left: 0, right: 0, zIndex: 20, background: '#fff', border: `1.5px solid ${C.line}`, borderRadius: '8px', boxShadow: '0 6px 20px rgba(26,31,46,.12)', overflow: 'hidden' }}>
          {message && <div role="status" style={{ padding: '8px 12px', fontSize: '12px', color: C.body }}>{message}</div>}
          <ul ref={list} id={listId} role="listbox" aria-label="Skills"
            style={{ listStyle: 'none', margin: 0, padding: 0, maxHeight: '300px', overflowY: 'auto' }}>
            {results.map((r, i) => (
              <li key={r.skill.skill_id} id={`${listId}-${i}`} role="option" aria-selected={r.skill.skill_id === value}
                onClick={() => pick(r.skill)} onMouseMove={() => setActive(i)}
                style={{ display: 'flex', justifyContent: 'space-between', gap: '12px', padding: '6px 12px', fontSize: '13px', color: C.ink, cursor: 'pointer', background: i === active ? C.active : 'transparent', fontWeight: r.skill.skill_id === value ? '600' : '400' }}>
                <span>{r.skill.skill_name} ({label(r.skill.category)})</span>
                {r.alias && <span style={{ fontSize: '11px', color: C.muted, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>also called {r.alias}</span>}
                {r.related && <span style={{ fontSize: '11px', color: C.muted }}>related</span>}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
