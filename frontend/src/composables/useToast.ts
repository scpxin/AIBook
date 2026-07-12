import { ref, readonly } from 'vue'

export interface ToastItem {
  id: number
  message: string
  type: 'success' | 'error' | 'warning' | 'info'
}

const toasts = ref<ToastItem[]>([])
let nextId = 1

export function useToast() {
  function show(message: string, type: ToastItem['type']) {
    const id = nextId++
    toasts.value.push({ id, message, type })
    setTimeout(() => {
      toasts.value = toasts.value.filter((t) => t.id !== id)
    }, 3000)
  }

  function success(message: string) {
    show(message, 'success')
  }

  function error(message: string) {
    show(message, 'error')
  }

  function warning(message: string) {
    show(message, 'warning')
  }

  function info(message: string) {
    show(message, 'info')
  }

  return {
    toasts: readonly(toasts),
    success,
    error,
    warning,
    info,
  }
}

let instance: ReturnType<typeof useToast> | null = null

export function setupToast() {
  if (!instance) { instance = useToast() }
  return instance
}
