import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Draft, PolishResult, ContentParseResult, ConsistencyReport } from '../types/v2'
import {
  generateDraft, saveDraft, polishContent, parseContent,
  checkConsistency, getConsistencyReport,
} from '../api/v2'

export const useExecutionStore = defineStore('execution', () => {
  const projectId = ref('')
  const currentDraft = ref<Draft | null>(null)
  const draftContent = ref('')
  const polishResult = ref<PolishResult | null>(null)
  const parseResult = ref<ContentParseResult | null>(null)
  const consistencyReport = ref<ConsistencyReport | null>(null)
  const isGenerating = ref(false)
  const generationProgress = ref(0)
  const loading = ref(false)
  const error = ref('')

  async function generateDraftContent(pid: string, chapterNo: string, sceneSkeleton: any) {
    isGenerating.value = true
    generationProgress.value = 0
    draftContent.value = ''
    projectId.value = pid

    return new Promise<void>((resolve, reject) => {
      generateDraft(pid, chapterNo, sceneSkeleton,
        (text: string) => {
          draftContent.value += text
          generationProgress.value = draftContent.value.length
        },
        () => {
          isGenerating.value = false
          currentDraft.value = {
            chapterNo: parseInt(chapterNo) || 1,
            content: draftContent.value,
            contentRaw: draftContent.value,
            wordCountRaw: draftContent.value.length,
            wordCountFinal: draftContent.value.length,
            polishStatus: 'unpolished',
            foreshadowAdded: [],
            continuityCheck: 'pending',
            version: 1,
          }
          resolve()
        },
        (err: string) => {
          isGenerating.value = false
          error.value = err
          reject(new Error(err))
        }
      )
    })
  }

  async function saveDraftContent(pid: string, chapterNo: string, content: string) {
    return saveDraft(pid, chapterNo, content)
  }

  async function polish(pid: string, content: string, focus?: string) {
    loading.value = true
    error.value = ''
    try {
      polishResult.value = await polishContent(pid, content, focus)
    } catch (e: any) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function parseWrittenContent(pid: string, chapterNo: string, content: string) {
    loading.value = true
    error.value = ''
    try {
      parseResult.value = await parseContent(pid, chapterNo, content)
    } catch (e: any) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function runConsistencyCheck(pid: string, chapterNo: string, content: string, knowledgeState?: any, characters?: any[], world?: any) {
    loading.value = true
    error.value = ''
    try {
      consistencyReport.value = await checkConsistency(pid, chapterNo, content, knowledgeState, characters, world)
    } catch (e: any) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function loadConsistencyReport(pid: string, chapterNo?: string) {
    loading.value = true
    error.value = ''
    try {
      const r = await getConsistencyReport(pid, chapterNo)
      if (r.reports.length > 0) consistencyReport.value = r.reports[0]
    } catch (e: any) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  return {
    projectId, currentDraft, draftContent, polishResult, parseResult,
    consistencyReport, isGenerating, generationProgress, loading, error,
    generateDraftContent, saveDraftContent, polish, parseWrittenContent,
    runConsistencyCheck, loadConsistencyReport,
  }
})
