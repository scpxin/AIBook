export function useKeyboardNav(callback: () => void) {
  function onKeyDown(e: KeyboardEvent) {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault()
      callback()
    }
  }
  return { tabindex: 0, onKeyDown }
}
