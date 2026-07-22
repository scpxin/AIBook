import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Draft, SceneSkeleton, PolishResult, ContentParseResult, ConsistencyReport, KnowledgeState, Character, WorldBuilding } from '../types/v2'
import {
  generateDraft, saveDraft, polishContent, parseContent,
  checkConsistency, getConsistencyReport, getDrafts, getModuleData,
} from '../api/v2'
import { useToastStore } from './toast'

interface DraftRaw {
  chapter_no?: string | number
  id?: string | number
  title?: string
  content?: string
  word_count_final?: number
}

interface OutlineItemRaw {
  chapter_no?: string | number
  chapter_id?: string | number
  id?: string | number
  chapter_title?: string
  title?: string
  summary?: string
  chapter_summary?: string
  scenes?: any[]
  scene_list?: any[]
  key_points?: any[]
  plot_points?: any[]
  characters?: any[]
}

export const useExecutionStore = defineStore('execution', () => {
  const projectId = ref('')
  const currentDraft = ref<Draft | null>(null)
  const draftContent = ref('')
  const polishResult = ref<PolishResult | null>(null)
  const consistencyReport = ref<ConsistencyReport | null>(null)
  const isGenerating = ref(false)
  const generationProgress = ref(0)
  const loading = ref(false)
  const error = ref('')

  async function generateDraftContent(pid: string, chapterNo: string, sceneSkeleton?: any, onChunk?: (text: string) => void) {
    isGenerating.value = true
    generationProgress.value = 0
    draftContent.value = ''
    projectId.value = pid

    return new Promise<void>((resolve, reject) => {
      generateDraft(pid, chapterNo, sceneSkeleton,
        (text: string) => {
          draftContent.value += text
          generationProgress.value = draftContent.value.length
          if (onChunk) onChunk(text)
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
          useToastStore().error(err)
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

  async function parseWrittenContent(pid: string, chapterNo: string, content: string): Promise<ContentParseResult | null> {
    loading.value = true
    error.value = ''
    try {
      return await parseContent(pid, chapterNo, content)
    } catch (e: any) {
      error.value = e.message
      return null
    } finally {
      loading.value = false
    }
  }

  async function runConsistencyCheck(pid: string, chapterNo: string, content: string, knowledgeState?: KnowledgeState, characters?: Character[], world?: Partial<WorldBuilding>) {
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

  async function startDraftGeneration(pid: string, chapterNo: string, onChunk: (text: string) => void, sceneSkeleton?: SceneSkeleton) {
    isGenerating.value = true
    draftContent.value = ''
    try {
      await generateDraftContent(pid, chapterNo, sceneSkeleton, onChunk)
    } finally {
      isGenerating.value = false
    }
  }

  async function polishDraft(pid: string, content: string) {
    loading.value = true
    try {
      polishResult.value = await polishContent(pid, content)
      return { content: polishResult.value?.polishedContent || content }
    } finally {
      loading.value = false
    }
  }

  async function parseContentSimple(pid: string, content: string, chapterNo: string = '1') {
    loading.value = true
    try {
      return await parseWrittenContent(pid, chapterNo, content)
    } finally {
      loading.value = false
    }
  }

  async function getChaptersForWriting(pid: string) {
    try {
      const outlinesRes = await getModuleData(pid, 'chapter_plan')
      const outlines = outlinesRes?.data
      if (outlines) {
        let outlineList: OutlineItemRaw[] = []
        if (Array.isArray(outlines)) {
          outlineList = outlines
        } else if (outlines.chapter_outline && Array.isArray(outlines.chapter_outline)) {
          outlineList = outlines.chapter_outline
        } else if (outlines.module_data && Array.isArray(outlines.module_data)) {
          outlineList = outlines.module_data
        } else if (outlines.chapters && Array.isArray(outlines.chapters)) {
          outlineList = outlines.chapters
        }
        if (outlineList.length > 0) {
          return outlineList.map((o: OutlineItemRaw, i: number) => ({
            id: o.chapter_no || o.chapter_id || o.id || String(i + 1),
            title: o.chapter_title || o.title || `第${i + 1}章`,
            outline: {
              title: o.chapter_title || o.title || `第${i + 1}章`,
              summary: o.summary || o.chapter_summary || '',
              scenes: Array.isArray(o.scenes) ? o.scenes : (Array.isArray(o.scene_list) ? o.scene_list : []),
              key_points: Array.isArray(o.key_points) ? o.key_points : (Array.isArray(o.plot_points) ? o.plot_points : []),
              characters: Array.isArray(o.characters) ? o.characters : [],
            },
            content: '',
            wordCount: 0,
          }))
        }
      }
      const drafts = await getDrafts(pid) as DraftRaw[]
      if (drafts && drafts.length > 0) {
        return drafts.map((d: DraftRaw) => ({
          id: String(d.chapter_no || d.id),
          title: `第${d.chapter_no}章` || d.title,
          outline: { title: d.title || `第${d.chapter_no}章`, summary: '', scenes: [], key_points: [], characters: [] },
          content: d.content || '',
          wordCount: d.word_count_final || 0,
        }))
      }
    } catch (_e) { /* fallback below */ }
    return []
  }

  return {
    projectId, currentDraft, draftContent, polishResult,
    consistencyReport, isGenerating, generationProgress, loading, error,
    generateDraftContent, saveDraftContent, polish, parseWrittenContent,
    runConsistencyCheck, loadConsistencyReport,
    generateDraft: startDraftGeneration, polishDraft, parseContent: parseContentSimple, getChaptersForWriting, getDrafts,
  }
})
