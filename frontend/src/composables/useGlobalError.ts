import { ref } from 'vue'

export function useGlobalError() {
  const globalError = ref('')
  const globalSuccess = ref('')
  let errorTimer: ReturnType<typeof setTimeout> | null = null
  let successTimer: ReturnType<typeof setTimeout> | null = null

  function showError(msg: string, duration = 5000) {
    globalError.value = msg
    if (errorTimer) clearTimeout(errorTimer)
    errorTimer = setTimeout(() => { globalError.value = '' }, duration)
  }

  function showSuccess(msg: string, duration = 3000) {
    globalSuccess.value = msg
    if (successTimer) clearTimeout(successTimer)
    successTimer = setTimeout(() => { globalSuccess.value = '' }, duration)
  }

  function clearError() { globalError.value = '' }
  function clearSuccess() { globalSuccess.value = '' }

  return { globalError, globalSuccess, showError, showSuccess, clearError, clearSuccess }
}
