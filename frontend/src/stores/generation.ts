import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { useToastStore } from './toast'

export interface GenerationState {
  moduleName: string
  moduleKey: string
  label: string
  totalSteps: number
  currentStep: number
  startTime: number
  message: string
}

export const useGenerationStore = defineStore('generation', () => {
  const state = ref<GenerationState | null>(null)

  const isGenerating = computed(() => state.value !== null)
  const elapsed = ref(0)

  let timer: ReturnType<typeof setInterval> | null = null

  function start(moduleKey: string, label: string, totalSteps = 1, message = '') {
    state.value = {
      moduleName: label,
      moduleKey,
      label,
      totalSteps,
      currentStep: 0,
      startTime: Date.now(),
      message: message || `正在生成${label}...`,
    }
    elapsed.value = 0
    if (timer) clearInterval(timer)
    timer = setInterval(() => {
      if (state.value) {
        elapsed.value = Math.floor((Date.now() - state.value.startTime) / 1000)
      }
    }, 1000)
  }

  function update(step: number, message?: string) {
    if (!state.value) return
    state.value = {
      ...state.value,
      currentStep: step,
      message: message || state.value.message,
    }
  }

  function stop() {
    const wasGenerating = state.value
    state.value = null
    elapsed.value = 0
    if (timer) {
      clearInterval(timer)
      timer = null
    }
    if (wasGenerating) {
      const toast = useToastStore()
      toast.success(`${wasGenerating.label} 生成完成`)
    }
  }

  function fail(errorMessage: string) {
    const wasGenerating = state.value
    state.value = null
    elapsed.value = 0
    if (timer) {
      clearInterval(timer)
      timer = null
    }
    const toast = useToastStore()
    toast.error(`${wasGenerating?.label || '生成'} 失败: ${errorMessage}`)
  }

  return {
    state,
    isGenerating,
    elapsed,
    start,
    update,
    stop,
    fail,
  }
})
