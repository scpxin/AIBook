import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { KnowledgeState, ConsistencyReport } from '../types/v2'
import { getKnowledgeSnapshot, getForeshadows, updateKnowledge, worldConsistencyCheck, getConsistencyReport } from '../api/v2'

export const useKnowledgeStore = defineStore('knowledge', () => {
  const projectId = ref('')
  const state = ref<KnowledgeState>({ characterStates: {}, worldState: {}, plotState: {} })
  const foreshadows = ref<any[]>([])
  const resolvedForeshadows = ref<any[]>([])
  const loading = ref(false)
  const error = ref('')
  const consistencyReports = ref<any[]>([])

  async function loadSnapshot(pid: string) {
    loading.value = true
    error.value = ''
    projectId.value = pid
    try {
      state.value = await getKnowledgeSnapshot(pid)
    } catch (e: any) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function loadForeshadows(pid: string, status?: string) {
    loading.value = true
    error.value = ''
    try {
      const r = await getForeshadows(pid, status)
      if (status === 'resolved') {
        resolvedForeshadows.value = r.foreshadows
      } else {
        foreshadows.value = r.foreshadows
      }
    } catch (e: any) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function update(pid: string, chapterNo: string, parseResult: any) {
    loading.value = true
    error.value = ''
    try {
      await updateKnowledge(pid, chapterNo, parseResult)
      await loadSnapshot(pid)
    } catch (e: any) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  const latestReport = computed(() => consistencyReports.value[0] || null)

  async function loadConsistencyReports(pid: string) {
    loading.value = true
    try {
      const r = await getConsistencyReport(pid)
      consistencyReports.value = r.reports || []
    } catch (e: any) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function executeConsistencyCheck(pid: string) {
    loading.value = true
    try {
      await worldConsistencyCheck(pid)
      await loadConsistencyReports(pid)
    } catch (e: any) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  return {
    projectId, state, foreshadows, resolvedForeshadows, loading, error,
    consistencyReports, latestReport,
    loadSnapshot, loadForeshadows, update, loadConsistencyReports, executeConsistencyCheck,
  }
})
