import { onUnmounted } from 'vue'
import { useGenerationStore } from '../stores/generation'

export function useGeneration(moduleKey: string, label: string, timeoutMs = 300000) {
  const gen = useGenerationStore()
  let started = false
  let timer: ReturnType<typeof setTimeout> | null = null

  function begin(totalSteps = 1, message = '') {
    gen.start(moduleKey, label, totalSteps, message)
    started = true
    if (timer) clearTimeout(timer)
    timer = setTimeout(() => {
      if (started) {
        gen.fail('操作超时，请检查网络连接后重试')
        started = false
      }
    }, timeoutMs)
  }

  function progress(step: number, message?: string) {
    gen.update(step, message)
  }

  function end() {
    if (timer) { clearTimeout(timer); timer = null }
    if (started) {
      gen.stop()
      started = false
    }
  }

  function fail(errorMessage: string) {
    if (timer) { clearTimeout(timer); timer = null }
    if (started) {
      gen.fail(errorMessage)
      started = false
    }
  }

  onUnmounted(() => {
    if (started) {
      if (timer) { clearTimeout(timer); timer = null }
      gen.stop()
      started = false
    }
  })

  return { begin, progress, end, fail }
}
