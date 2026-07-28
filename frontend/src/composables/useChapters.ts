import { computed } from 'vue'
import { getAllModuleData } from '../api/v2'

export interface ChapterOption {
  value: number | string
  label: string
  title?: string
}

export function useChapters(projectId: string) {

  async function fetchChapters(): Promise<ChapterOption[]> {
    try {
      const data = await getAllModuleData(projectId)
      const modules = data?.modules || []

      const cp = modules['chapter_plan']
      if (cp) {
        let list: Record<string, unknown>[] = []
        if (Array.isArray(cp)) {
          list = cp
        } else if (Array.isArray(cp.chapter_plan)) {
          list = cp.chapter_plan
        } else if (Array.isArray(cp.module_data)) {
          list = cp.module_data
        } else if (Array.isArray(cp.chapters)) {
          list = cp.chapters
        }
        if (list.length > 0) {
          return list.map((ch: Record<string, unknown>, i: number) => ({
            value: (ch.chapter_no ?? ch.chapterNo ?? ch.id ?? (i + 1)) as string | number,
            label: String(ch.title || ch.chapter_title || `第${i + 1}章`),
            title: String(ch.title || ch.chapter_title || ''),
          }))
        }
      }

      const drafts = modules['draft']
      if (Array.isArray(drafts) && drafts.length > 0) {
        return drafts.map((d: Record<string, unknown>) => ({
          value: (d.chapter_no ?? d.chapterNo ?? d.id ?? 1) as string | number,
          label: String(d.title || `第${d.chapter_no ?? 1}章`),
          title: String(d.title || ''),
        }))
      }
    } catch (_e) { /* fallback */ }

    return Array.from({ length: 10 }, (_, i) => ({
      value: i + 1,
      label: `第${i + 1}章`,
    }))
  }

  return { fetchChapters }
}
