import { ref, readonly } from 'vue'
import { ApiError } from '../api/client'

export interface ErrorBarState {
  message: string
  type: 'error' | 'warning' | 'info'
  retry?: () => void | Promise<void>
  show: boolean
}

interface PendingError {
  message: string
  type: 'error' | 'warning' | 'info'
  retry?: () => void | Promise<void>
}

const state = ref<ErrorBarState>({ message: '', type: 'error', show: false })
let timer: ReturnType<typeof setTimeout> | null = null
let pendingError: PendingError | null = null

const DURATION_MAP: Record<NonNullable<ErrorBarState['type']>, number> = {
  error: 10000,
  warning: 5000,
  info: 3000,
}

function showCurrent(item: PendingError) {
  if (timer) clearTimeout(timer)
  state.value = { message: item.message, type: item.type, retry: item.retry, show: true }
  const duration = DURATION_MAP[item.type]
  if (duration > 0) {
    timer = setTimeout(() => {
      state.value.show = false
      if (pendingError) {
        const next = pendingError
        pendingError = null
        showCurrent(next)
      }
    }, duration)
  }
}

export function useErrorBar() {
  function show(message: string, opts?: { type?: ErrorBarState['type']; retry?: () => void | Promise<void>; duration?: number }) {
    const type = opts?.type || 'error'
    const item: PendingError = { message, type, retry: opts?.retry }

    if (!state.value.show) {
      showCurrent(item)
    } else {
      pendingError = item
    }
  }

  function dismiss() {
    if (timer) { clearTimeout(timer); timer = null }
    state.value.show = false
    if (pendingError) {
      const next = pendingError
      pendingError = null
      showCurrent(next)
    }
  }

  function showError(err: unknown, retry?: () => void | Promise<void>) {
    const message = err instanceof ApiError ? err.message : (err instanceof Error ? err.message : String(err))
    show(message, { type: 'error', retry })
  }

  return {
    state: readonly(state),
    show,
    dismiss,
    showError,
  }
}

let instance: ReturnType<typeof useErrorBar> | null = null

export function setupErrorBar() {
  if (!instance) { instance = useErrorBar() }
  return instance
}
