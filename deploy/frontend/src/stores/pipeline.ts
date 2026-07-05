import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { PipelineProgress, ModuleInfo, ModuleStatus, ModuleState } from '../types/v2'
import {
  getPipelineModules, getPipelineStatus, getNextModule, getModuleData,
} from '../api/v2'

export const usePipelineStore = defineStore('pipeline', () => {
  const currentProjectId = ref('')
  const progress = ref<PipelineProgress | null>(null)
  const modules = ref<ModuleInfo[]>([])
  const loading = ref(false)
  const error = ref('')

  const currentModule = computed(() => progress.value?.currentModule || '')
  const nextModule = computed(() => progress.value?.nextModule || null)
  const progressPct = computed(() => progress.value?.progressPct || 0)
  const isComplete = computed(() => progressPct.value >= 100)

  const getModuleState = computed(() => (name: string): ModuleState | null => {
    return progress.value?.modules?.[name] || null
  })

  async function loadModules() {
    try {
      const r = await getPipelineModules()
      modules.value = r.modules
    } catch (e: any) {
      error.value = e.message
    }
  }

  async function loadStatus(projectId: string) {
    loading.value = true
    error.value = ''
    try {
      currentProjectId.value = projectId
      progress.value = await getPipelineStatus(projectId)
    } catch (e: any) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function fetchNext(projectId: string) {
    try {
      const r = await getNextModule(projectId)
      return r
    } catch (e: any) {
      error.value = e.message
      return null
    }
  }

  async function fetchModuleData(projectId: string, moduleName: string) {
    try {
      const r = await getModuleData(projectId, moduleName)
      return r.data
    } catch (e: any) {
      error.value = e.message
      return null
    }
  }

  function updateModuleStatus(name: string, status: ModuleStatus, err: string | null = null) {
    if (!progress.value) return
    const mod = progress.value.modules[name]
    if (!mod) return
    mod.status = status
    if (status === 'generating') mod.startedAt = new Date().toISOString()
    if (status === 'done') mod.completedAt = new Date().toISOString()
    if (status === 'failed') mod.error = err
  }

  return {
    currentProjectId, progress, modules, loading, error,
    currentModule, nextModule, progressPct, isComplete, getModuleState,
    loadModules, loadStatus, fetchNext, fetchModuleData, updateModuleStatus,
  }
})
