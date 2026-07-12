import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { ModelConfig } from '../api/client'
import { testConnectionApi } from '../api/novel'
import { getSettings, saveModelSettings } from '../api/settings'

const STORAGE_KEY_MODELS = 'fanqie_models'
const STORAGE_KEY_ACTIVE = 'fanqie_active_model'

export const useSettingsStore = defineStore('settings', () => {
  const models = ref<ModelConfig[]>([])
  const activeModelId = ref('')
  const syncing = ref(false)

  function load() {
    try {
      models.value = JSON.parse(localStorage.getItem(STORAGE_KEY_MODELS) || '[]')
    } catch {
      models.value = []
    }
    activeModelId.value = localStorage.getItem(STORAGE_KEY_ACTIVE) || (models.value.length ? models.value[0].id : '')
  }

  async function loadFromBackend() {
    try {
      const s = await getSettings()
      if (s?.models?.length) {
        models.value = s.models
        if (s.activeModelId) activeModelId.value = s.activeModelId
      }
    } catch { /* ignore */ }
  }

  async function saveToBackend() {
    syncing.value = true
    try {
      await saveModelSettings(models.value, activeModelId.value)
    } catch { /* ignore */ }
    finally { syncing.value = false }
    saveLocal()
  }

  function saveLocal() {
    localStorage.setItem(STORAGE_KEY_MODELS, JSON.stringify(models.value))
  }

  let userModified = false
  function markUserModified() { userModified = true }

  function setActive(id: string) {
    activeModelId.value = id
    localStorage.setItem(STORAGE_KEY_ACTIVE, id)
    markUserModified()
    saveToBackend()
  }

  const activeModel = computed(() => models.value.find(m => m.id === activeModelId.value) || models.value[0])

  function addModel(m: ModelConfig) {
    models.value.push(m)
    saveLocal()
    markUserModified()
    if (!activeModelId.value) setActive(m.id)
    else saveToBackend()
  }

  function updateModel(id: string, data: Partial<ModelConfig>) {
    const idx = models.value.findIndex(m => m.id === id)
    if (idx >= 0) {
      models.value[idx] = { ...models.value[idx], ...data }
      saveLocal()
      markUserModified()
      saveToBackend()
    }
  }

  function removeModel(id: string) {
    models.value = models.value.filter(m => m.id !== id)
    if (activeModelId.value === id) {
      const next = models.value.length ? models.value[0].id : ''
      activeModelId.value = next
    }
    saveLocal()
    markUserModified()
    saveToBackend()
  }

  async function testConnection(model: ModelConfig): Promise<{ ok: boolean; error?: string; response?: string }> {
    return testConnectionApi({ endpoint: model.endpoint, apiKey: model.apiKey, model: model.model })
  }

  load()

  // Auto-load from backend on init — falls back to localStorage if backend fails
  loadFromBackend().then(() => {
    if (userModified) return
    if (!models.value.length) {
      // If backend returned nothing, try localStorage one more time
      try {
        const local = JSON.parse(localStorage.getItem(STORAGE_KEY_MODELS) || '[]')
        if (local.length) {
          models.value = local
          if (!activeModelId.value) {
            activeModelId.value = localStorage.getItem(STORAGE_KEY_ACTIVE) || local[0]?.id || ''
          }
        }
      } catch { /* ignore */ }
    }
  })

  return {
    models,
    activeModelId,
    activeModel,
    syncing,
    load,
    loadFromBackend,
    setActive,
    addModel,
    updateModel,
    removeModel,
    testConnection,
    saveToBackend,
  }
})
