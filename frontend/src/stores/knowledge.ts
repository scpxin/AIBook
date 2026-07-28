import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { KnowledgeState, ConsistencyReport, ContentParseResult } from '../types/v2'
import { getKnowledgeSnapshot, getForeshadows, updateKnowledge, worldConsistencyCheck, getConsistencyReport } from '../api/v2'

export const useKnowledgeStore = defineStore('knowledge', () => {
  const projectId = ref('')
  const state = ref<KnowledgeState>({ characterStates: {}, worldState: {}, plotState: {} })
  const foreshadows = ref<Record<string, unknown>[]>([])
  const resolvedForeshadows = ref<Record<string, unknown>[]>([])
  const loading = ref(false)
  const error = ref('')
  const consistencyReports = ref<ConsistencyReport[]>([])

  async function loadSnapshot(pid: string) {
    loading.value = true
    error.value = ''
    projectId.value = pid
    try {
      state.value = await getKnowledgeSnapshot(pid)
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : String(e)
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
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : String(e)
    } finally {
      loading.value = false
    }
  }

  async function update(pid: string, chapterNo: string, parseResult: ContentParseResult) {
    loading.value = true
    error.value = ''
    try {
      await updateKnowledge(pid, chapterNo, parseResult)
      await loadSnapshot(pid)
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : String(e)
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
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : String(e)
    } finally {
      loading.value = false
    }
  }

  async function executeConsistencyCheck(pid: string) {
    loading.value = true
    try {
      await worldConsistencyCheck(pid)
      await loadConsistencyReports(pid)
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : String(e)
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
