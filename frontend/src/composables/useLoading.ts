import { ref, readonly } from 'vue'

const loadingCount = ref(0)
const loadingMessage = ref('')

export function useLoading() {
  function start(message = '') {
    loadingCount.value++
    loadingMessage.value = message
  }

  function stop() {
    loadingCount.value = Math.max(0, loadingCount.value - 1)
    if (loadingCount.value === 0) loadingMessage.value = ''
  }

  function withLoading<T>(fn: () => Promise<T>, message = ''): Promise<T> {
    start(message)
    return fn().finally(() => stop())
  }

  return {
    isLoading: readonly(loadingCount),
    loadingMessage: readonly(loadingMessage),
    start,
    stop,
    withLoading,
  }
}

let instance: ReturnType<typeof useLoading> | null = null

export function setupLoading() {
  if (!instance) { instance = useLoading() }
  return instance
}
