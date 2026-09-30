// SEAGAS Home — small hooks shared by the landing page sections
import { useState, useEffect, useRef } from 'react'

export function prefersReducedMotion() {
  return typeof window !== 'undefined' &&
    window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
}

// Returns [ref, inView]; inView flips to true once the element scrolls into view
export function useInView(threshold = 0.2) {
  const ref = useRef(null)
  const [inView, setInView] = useState(false)
  useEffect(() => {
    const el = ref.current
    if (!el) return
    const observer = new IntersectionObserver(([entry]) => {
      if (entry.isIntersecting) {
        setInView(true)
        observer.disconnect()
      }
    }, { threshold })
    observer.observe(el)
    return () => observer.disconnect()
  }, [threshold])
  return [ref, inView]
}

// Smoothly animates from the currently shown number to `target`
// (count-up on first run, count-up/down when the target changes)
export function useAnimatedNumber(target, run = true, duration = 1100) {
  const [value, setValue] = useState(0)
  const valueRef = useRef(0)

  useEffect(() => {
    if (!run) return
    if (prefersReducedMotion()) {
      valueRef.current = target
      setValue(target)
      return
    }
    const from = valueRef.current
    const start = performance.now()
    let frame
    const tick = (now) => {
      const t = Math.min((now - start) / duration, 1)
      const eased = 1 - Math.pow(1 - t, 3)
      const next = Math.round(from + (target - from) * eased)
      valueRef.current = next
      setValue(next)
      if (t < 1) frame = requestAnimationFrame(tick)
    }
    frame = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(frame)
  }, [target, run, duration])

  return value
}

// Types `word` out letter by letter whenever it changes (deletes the old one first)
export function useTypewriter(word, startDelay = 500) {
  const [text, setText] = useState('')
  const [ready, setReady] = useState(false)

  useEffect(() => {
    const t = setTimeout(() => setReady(true), startDelay)
    return () => clearTimeout(t)
  }, [startDelay])

  useEffect(() => {
    if (!ready) return
    if (prefersReducedMotion()) { setText(word); return }
    let t
    if (!word.startsWith(text)) {
      t = setTimeout(() => setText(text.slice(0, -1)), 28)
    } else if (text !== word) {
      t = setTimeout(() => setText(word.slice(0, text.length + 1)), 60)
    }
    return () => clearTimeout(t)
  }, [word, text, ready])

  return text
}

// Calls `handler` on a click/tap outside `ref` or on Escape, while `active`
export function useDismiss(ref, active, handler) {
  useEffect(() => {
    if (!active) return
    const onPointer = (e) => { if (ref.current && !ref.current.contains(e.target)) handler() }
    const onKey = (e) => { if (e.key === 'Escape') handler() }
    document.addEventListener('pointerdown', onPointer)
    document.addEventListener('keydown', onKey)
    return () => {
      document.removeEventListener('pointerdown', onPointer)
      document.removeEventListener('keydown', onKey)
    }
  }, [ref, active, handler])
}

// Paints the page canvas (html + body) while a page is mounted, so overscroll "bounce"
// never reveals the app's light background. Restores the previous colour on unmount.
export function useCanvasColor(color) {
  useEffect(() => {
    const html = document.documentElement
    const prev = { html: html.style.backgroundColor, body: document.body.style.backgroundColor }
    html.style.backgroundColor = color
    document.body.style.backgroundColor = color
    return () => {
      html.style.backgroundColor = prev.html
      document.body.style.backgroundColor = prev.body
    }
  }, [color])
}
