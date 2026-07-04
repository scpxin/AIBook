import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { ModelConfig } from '../api/client'
import { testConnectionApi } from '../api/novel'

const STORAGE_KEY_MODELS = 'fanqie_models'
const STORAGE_KEY_ACTIVE = 'fanqie_active_model'

export const useSettingsStore = defineStore('settings', () => {
  const models = ref<ModelConfig[]>([])
  const activeModelId = ref('')

  function load() {
    try {
      models.value = JSON.parse(localStorage.getItem(STORAGE_KEY_MODELS) || '[]')
    } catch {
      models.value = []
    }
    activeModelId.value = localStorage.getItem(STORAGE_KEY_ACTIVE) || (models.value.length ? models.value[0].id : '')
  }

  function saveLocal() {
    localStorage.setItem(STORAGE_KEY_MODELS, JSON.stringify(models.value))
  }

  function setActive(id: string) {
    activeModelId.value = id
    localStorage.setItem(STORAGE_KEY_ACTIVE, id)
  }

  const activeModel = computed(() => models.value.find(m => m.id === activeModelId.value) || models.value[0])

  function addModel(m: ModelConfig) {
    models.value.push(m)
    saveLocal()
    if (!activeModelId.value) setActive(m.id)
  }

  function updateModel(id: string, data: Partial<ModelConfig>) {
    const idx = models.value.findIndex(m => m.id === id)
    if (idx >= 0) {
      models.value[idx] = { ...models.value[idx], ...data }
      saveLocal()
    }
  }

  function removeModel(id: string) {
    models.value = models.value.filter(m => m.id !== id)
    if (activeModelId.value === id) {
      setActive(models.value.length ? models.value[0].id : '')
    }
    saveLocal()
  }

  async function testConnection(model: ModelConfig): Promise<{ ok: boolean; error?: string; response?: string }> {
    return testConnectionApi({ endpoint: model.endpoint, apiKey: model.apiKey, model: model.model })
  }

  load()

  return {
    models,
    activeModelId,
    activeModel,
    load,
    setActive,
    addModel,
    updateModel,
    removeModel,
    testConnection,
  }
})
