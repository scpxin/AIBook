import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface Toast {
  id: number
  type: 'success' | 'error' | 'info' | 'action'
  message: string
  action?: { label: string; handler: () => void }
}

let nextId = 1

export const useToastStore = defineStore('toast', () => {
  const toasts = ref<Toast[]>([])

  function show(type: Toast['type'], message: string, duration = 3000) {
    const id = nextId++
    toasts.value.push({ id, type, message })
    setTimeout(() => {
      toasts.value = toasts.value.filter(t => t.id !== id)
    }, duration)
  }

  function success(msg: string) { show('success', msg) }
  function error(msg: string) { show('error', msg, 5000) }
  function info(msg: string) { show('info', msg) }
  function warning(msg: string) { show('info', msg, 4000) }

  function action(msg: string, opts: { label: string; handler: () => void }) {
    const id = nextId++
    const toast: Toast = { id, type: 'action', message: msg, action: { label: opts.label, handler: opts.handler } }
    toasts.value.push(toast)
    setTimeout(() => {
      const t = toasts.value.find(t => t.id === id)
      if (t) t.action = undefined
    }, 8000)
  }

  function dismiss(id: number) {
    toasts.value = toasts.value.filter(t => t.id !== id)
  }

  return { toasts, show, success, error, info, warning, action, dismiss }
})
