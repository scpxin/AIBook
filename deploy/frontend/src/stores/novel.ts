import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface OutlineItem {
  chapter_number: number | string
  title: string
  summary: string
  characters?: string[]
  key_points?: any
  emotion?: string
  technique_focus?: string
}

export const useNovelStore = defineStore('novel', () => {
  const step = ref(0)
  const title = ref('')
  const description = ref('')
  const theme = ref('')
  const genre = ref('')
  const world = ref('')
  const characters = ref('')
  const outlineText = ref('')
  const outline = ref<OutlineItem[]>([])
  const chapters = ref<string[]>([])
  const currentChapter = ref(0)
  const charCount = ref(6)
  const chapterCount = ref(3)
  const perspective = ref('第三人称')
  const targetWords = ref(3000)
  const styleProfile = ref('')
  const useCraft = ref(true)

  // UI state
  const inspireLoading = ref(false)
  const inspireError = ref('')
  const charsLoading = ref(false)
  const outlineLoading = ref(false)
  const chapterLoading = ref(false)
  const chapterProgress = ref('')
  const chapterPaused = ref(false)
  const chapterPauseIdx = ref(0)
  const genStatus = ref({ total: 0, completed: 0, failed: 0, current: 0 })

  // Style analysis state
  const styleExpanded = ref(false)
  const styleTab = ref('paste')
  const styleText = ref('')
  const styleLoading = ref(false)
  const savedBooks = ref<any[]>([])
  const selectedSavedBook = ref('')
  const savedBookAnalyzing = ref(false)

  // AI analyze state
  const analyzeTab = ref('paste')
  const analyzeText = ref('')
  const analyzeLoading = ref(false)
  const analyzeResult = ref('')
  const analyzeSavedBooks = ref<any[]>([])
  const selectedAnalyzeBook = ref('')
  const analyzeBookContent = ref('')
  const styleProfileForGenerate = ref('')

  // AI generate state
  const genLoading = ref(false)
  const genResult = ref('')
  const genForm = { genre: '', count: 3, protagonist: '', world: '', outline: '' }

  function reset() {
    step.value = 0
    title.value = ''
    description.value = ''
    theme.value = ''
    genre.value = ''
    world.value = ''
    characters.value = ''
    outlineText.value = ''
    outline.value = []
    chapters.value = []
    currentChapter.value = 0
    targetWords.value = 3000
    styleProfile.value = ''
    useCraft.value = true
    chapterCount.value = 3
    charCount.value = 6
    perspective.value = '第三人称'
  }

  return {
    step, title, description, theme, genre, world, characters,
    outlineText, outline, chapters, currentChapter,
    charCount, chapterCount, perspective, targetWords,
    styleProfile, useCraft,
    inspireLoading, inspireError,
    charsLoading, outlineLoading, chapterLoading, chapterProgress,
    chapterPaused, chapterPauseIdx, genStatus,
    styleExpanded, styleTab, styleText, styleLoading,
    savedBooks, selectedSavedBook, savedBookAnalyzing,
    analyzeTab, analyzeText, analyzeLoading, analyzeResult,
    analyzeSavedBooks, selectedAnalyzeBook, analyzeBookContent,
    styleProfileForGenerate,
    genLoading, genResult, genForm,
    reset,
  }
})
