import type { Directive } from 'vue'

function isInteractive(el: HTMLElement): boolean {
  const tag = el.tagName.toLowerCase()
  return tag === 'button' || tag === 'a' || tag === 'input' || tag === 'select' || tag === 'textarea' || el.getAttribute('role') === 'button' || el.tabIndex >= 0
}

function handleKeydown(e: Event, handler: (e: Event) => void) {
  const key = (e as KeyboardEvent).key
  if (key === 'Enter' || key === ' ') {
    e.preventDefault()
    handler(e)
  }
}

export const vKeyboardClick: Directive<HTMLElement, (e: Event) => void> = {
  mounted(el, binding) {
    if (isInteractive(el)) return
    el.setAttribute('role', 'button')
    el.setAttribute('tabindex', '0')
    el.setAttribute('aria-pressed', 'false')
    el.style.cursor = 'pointer'
    const handler = (e: Event) => handleKeydown(e, binding.value)
    el.addEventListener('keydown', handler)
    ;(el as any).__vKeyboardHandler = handler
  },
  unmounted(el) {
    const handler = (el as any).__vKeyboardHandler
    if (handler) el.removeEventListener('keydown', handler)
  },
}
