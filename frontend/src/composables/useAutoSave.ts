import { ref, onBeforeUnmount } from 'vue'
import { registerSaveFn } from './useSaveRegistry'
import { useModuleSaveStore } from '../stores/moduleSave'

export interface AutoSaveOptions<T> {
  dataRef: () => T
  saveFn: (data: T) => Promise<void>
  debounce?: number
  storageKey?: string
  onSaveError?: (e: unknown) => void
  onSaveSuccess?: () => void
  projectId?: string
  moduleName?: string
}

export type SaveState = 'idle' | 'saving' | 'saved' | 'error'

export function useAutoSave<T>(opts: AutoSaveOptions<T>) {
   const saveState = ref<SaveState>('idle')
   const lastSavedAt = ref<number | null>(null)
   let timer: ReturnType<typeof setTimeout> | null = null
   let isUnmounting = false
   let resetTimer: ReturnType<typeof setTimeout> | null = null
   const DEBOUNCE = opts.debounce ?? 2000

   const moduleStore = useModuleSaveStore()

   const _markDirty = () => {
     if (opts.projectId && opts.moduleName) {
       moduleStore.markDirty(opts.projectId, opts.moduleName)
     }
   }

   const _markSaving = () => {
     if (opts.projectId && opts.moduleName) {
       moduleStore.markSaving(opts.projectId, opts.moduleName)
     }
   }

   const _markSaved = () => {
     if (opts.projectId && opts.moduleName) {
       moduleStore.markSaved(opts.projectId, opts.moduleName)
     }
   }

   const _markError = (e: unknown) => {
     if (opts.projectId && opts.moduleName) {
       const msg = e instanceof Error ? e.message : '保存失败'
       moduleStore.markError(opts.projectId, opts.moduleName, msg)
     }
   }

   const _registeredUnregister = registerSaveFn(saveNow)

  function getStoredBackup(): T | null {
    if (!opts.storageKey) return null
    try {
      const raw = localStorage.getItem(`autosave_${opts.storageKey}`)
      if (!raw) return null
      try {
        const parsed = JSON.parse(raw)
        if (parsed?.timestamp !== undefined) return parsed.data
        return parsed
      } catch { return null }
    } catch { return null }
  }

  function setStoredBackup(data: T) {
    if (!opts.storageKey) return
    try {
      const backup = { timestamp: Date.now(), data }
      localStorage.setItem(`autosave_${opts.storageKey}`, JSON.stringify(backup))
      cleanupOldBackups()
    } catch { /* quota exceeded - ignore */ }
  }

  function cleanupOldBackups() {
    try {
      const now = Date.now()
      const maxAge = 7 * 24 * 60 * 60 * 1000
      const keysToRemove: string[] = []
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i)
        if (key && key.startsWith('autosave_')) {
          try {
            const raw = localStorage.getItem(key)
            if (raw) {
              const parsed = JSON.parse(raw)
              if (parsed?.timestamp && (now - parsed.timestamp) > maxAge) {
                keysToRemove.push(key)
              }
            }
          } catch { /* ignore parse errors */ }
        }
      }
      for (const key of keysToRemove) {
        localStorage.removeItem(key)
      }
    } catch { /* ignore */ }
  }

  function clearStoredBackup() {
    if (!opts.storageKey) return
    localStorage.removeItem(`autosave_${opts.storageKey}`)
  }

  async function saveNow(): Promise<void> {
    if (isUnmounting) {
      setStoredBackup(opts.dataRef())
      return
    }
    _markSaving()
    saveState.value = 'saving'
    try {
      await opts.saveFn(opts.dataRef())
      _markSaved()
      saveState.value = 'saved'
      lastSavedAt.value = Date.now()
      setStoredBackup(opts.dataRef())
      opts.onSaveSuccess?.()
      if (resetTimer) clearTimeout(resetTimer)
      resetTimer = setTimeout(() => { if (saveState.value === 'saved') saveState.value = 'idle' }, 2000)
    } catch (e) {
      _markError(e)
      saveState.value = 'error'
      setStoredBackup(opts.dataRef())
      opts.onSaveError?.(e)
    }
  }

  function scheduleSave() {
    _markDirty()
    if (timer) clearTimeout(timer)
    timer = setTimeout(() => { saveNow() }, DEBOUNCE)
  }

  function cancel() {
    if (timer) { clearTimeout(timer); timer = null }
  }

  function handleBeforeUnload(e: BeforeUnloadEvent) {
    if (saveState.value === 'saving' || timer) {
      e.preventDefault()
      e.returnValue = ''
    }
  }

  function restoreBackup(): T | null {
    return getStoredBackup()
  }

  window.addEventListener('beforeunload', handleBeforeUnload)

   onBeforeUnmount(() => {
      isUnmounting = true
      if (saveState.value === 'saving' || timer !== null) {
        setStoredBackup(opts.dataRef())
      }
      cancel()
      if (resetTimer) clearTimeout(resetTimer)
      if (saveState.value === 'saving') {
        setStoredBackup(opts.dataRef())
      }
      window.removeEventListener('beforeunload', handleBeforeUnload)
      _registeredUnregister()
   })

  return {
    saveState,
    lastSavedAt,
    saveNow,
    scheduleSave,
    cancel,
    restoreBackup,
    clearStoredBackup,
  }
}
