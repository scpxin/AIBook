import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

interface ModuleSaveState {
  dirty: boolean
  saving: boolean
  saved: boolean
  error: string | null
  lastSavedAt: number | null
}

type ProjectModuleMap = Record<string, Record<string, ModuleSaveState>>

const _state = ref<ProjectModuleMap>({})

function _ensureProject(projectId: string) {
  if (!_state.value[projectId]) {
    _state.value[projectId] = {}
  }
}

function _ensureModule(projectId: string, moduleName: string) {
  _ensureProject(projectId)
  if (!_state.value[projectId][moduleName]) {
    _state.value[projectId][moduleName] = {
      dirty: false,
      saving: false,
      saved: false,
      error: null,
      lastSavedAt: null,
    }
  }
}

export const useModuleSaveStore = defineStore('moduleSave', () => {
  function markDirty(projectId: string, moduleName: string) {
    _ensureModule(projectId, moduleName)
    const m = _state.value[projectId][moduleName]
    m.dirty = true
    m.saved = false
    m.error = null
  }

  function markSaving(projectId: string, moduleName: string) {
    _ensureModule(projectId, moduleName)
    const m = _state.value[projectId][moduleName]
    m.saving = true
    m.error = null
  }

  function markSaved(projectId: string, moduleName: string) {
    _ensureModule(projectId, moduleName)
    const m = _state.value[projectId][moduleName]
    m.dirty = false
    m.saving = false
    m.saved = true
    m.error = null
    m.lastSavedAt = Date.now()
  }

  function markError(projectId: string, moduleName: string, error: string) {
    _ensureModule(projectId, moduleName)
    const m = _state.value[projectId][moduleName]
    m.saving = false
    m.dirty = true
    m.error = error
  }

  function getModuleState(projectId: string, moduleName: string): ModuleSaveState {
    _ensureModule(projectId, moduleName)
    return _state.value[projectId][moduleName]
  }

  function hasUnsavedChanges(projectId: string): boolean {
    _ensureProject(projectId)
    return Object.values(_state.value[projectId]).some(m => m.dirty)
  }

  function getUnsavedModules(projectId: string): string[] {
    _ensureProject(projectId)
    return Object.entries(_state.value[projectId])
      .filter(([, m]) => m.dirty)
      .map(([name]) => name)
  }

  function isModuleSaving(projectId: string, moduleName: string): boolean {
    _ensureModule(projectId, moduleName)
    return _state.value[projectId][moduleName].saving
  }

  function getGlobalUnsavedCount(): number {
    let count = 0
    for (const proj of Object.values(_state.value)) {
      for (const mod of Object.values(proj)) {
        if (mod.dirty) count++
      }
    }
    return count
  }

  function clearProject(projectId: string) {
    delete _state.value[projectId]
  }

  function clearAll() {
    _state.value = {}
  }

  const globalUnsavedCount = computed(() => getGlobalUnsavedCount())

  return {
    markDirty,
    markSaving,
    markSaved,
    markError,
    getModuleState,
    hasUnsavedChanges,
    getUnsavedModules,
    isModuleSaving,
    getGlobalUnsavedCount,
    clearProject,
    clearAll,
    globalUnsavedCount,
  }
})
