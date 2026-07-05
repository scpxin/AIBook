// @ts-nocheck
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

  async function generateDraft(pid: string, chapterNo: string, onChunk: (text: string) => void) {
    isGenerating.value = true
    draftContent.value = ''
    try {
      await generateDraftContent(pid, chapterNo, undefined).then(() => {
        // Stream already handled via draftContent ref
      })
    } finally {
      isGenerating.value = false
    }
  }

  async function polishDraft(pid: string, content: string) {
    loading.value = true
    try {
      await polish(pid, content)
      return { content: polishResult.value?.result || polishResult.value?.improvedContent || content }
    } finally {
      loading.value = false
    }
  }

  async function parseContent(pid: string, content: string) {
    loading.value = true
    try {
      return await parseWrittenContent(pid, '1', content)
    } finally {
      loading.value = false
    }
  }

  async function getChaptersForWriting(pid: string) {
    return [
      { id: '1', title: '第一章 开局', outline: { title: '第一章 开局', scenes: ['主角出场', '冲突初现', '悬念设置'] }, content: '' },
      { id: '2', title: '第二章 发展', outline: { title: '第二章 发展', scenes: ['剧情推进', '新角色登场', '伏笔铺设'] }, content: '' },
      { id: '3', title: '第三章 高潮', outline: { title: '第三章 高潮', scenes: ['正面对决', '情绪爆发', '重大转折'] }, content: '' },
    ]
  }

  return {
    projectId, currentDraft, draftContent, polishResult, parseResult,
    consistencyReport, isGenerating, generationProgress, loading, error,
    generateDraftContent, saveDraftContent, polish, parseWrittenContent,
    runConsistencyCheck, loadConsistencyReport,
    generateDraft, polishDraft, parseContent, getChaptersForWriting,
  }
})
