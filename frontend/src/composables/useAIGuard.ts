import { computed } from 'vue'
import { useSettingsStore } from '../stores/settings'

export function useAIGuard() {
  const settings = useSettingsStore()

  const isAIConfigured = computed(() => {
    const models = settings.models
    if (!models || !models.length) return false
    const active = models.find(m => m.id === settings.activeModelId) || models[0]
    return !!(active && active.apiKey && active.endpoint && active.model &&
      active.endpoint !== 'http://x' && active.apiKey.length > 4)
  })

  return { isAIConfigured }
}
