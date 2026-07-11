import { useGenerationStore } from '../stores/generation'

export function useGeneration(moduleKey: string, label: string) {
  const gen = useGenerationStore()
  let started = false

  function begin(totalSteps = 1, message = '') {
    gen.start(moduleKey, label, totalSteps, message)
    started = true
  }

  function progress(step: number, message?: string) {
    gen.update(step, message)
  }

  function end() {
    if (started) {
      gen.stop()
      started = false
    }
  }

  function fail(errorMessage: string) {
    if (started) {
      gen.fail(errorMessage)
      started = false
    }
  }

  return { begin, progress, end, fail }
}
