import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useSettingsStore } from './settings'
import { useNovelStore } from './novel'
import { apiStream } from '../api/client'

export const useModalsStore = defineStore('modals', () => {
  // Read chapter modal
  const showRead = ref(false)
  const readTitle = ref('')
  const readContent = ref('')
  const readIdx = ref(0)

  // Chapter settings modal
  const showSettings = ref(false)
  const settingsIdx = ref(0)
  const settingsTargetWords = ref(3000)
  const settingsExtraPrompt = ref('')

  // Polish/compare modal
  const showPolish = ref(false)
  const polishIdx = ref(0)
  const polishOriginal = ref('')
  const polishResult = ref('')
  const polishLoading = ref(false)
  const polishTip = ref('正在润色中，请稍候...')

  // Compare modal
  const showCompare = ref(false)
  const compareIdx = ref(0)
  const compareOriginal = ref('')

  function openRead(idx: number) {
    const novel = useNovelStore()
    readIdx.value = idx
    readTitle.value = '第' + (idx + 1) + '章 ' + (novel.outline[idx]?.title || '')
    readContent.value = novel.chapters[idx]
    showRead.value = true
  }

  function saveRead() {
    const novel = useNovelStore()
    novel.chapters[readIdx.value] = readContent.value
    showRead.value = false
  }

  function openSettings(idx: number) {
    const novel = useNovelStore()
    settingsIdx.value = idx
    settingsTargetWords.value = novel.targetWords
    settingsExtraPrompt.value = ''
    showSettings.value = true
  }

  function applySettings(onRegenerate: (idx: number, target: number, extra: string) => void) {
    showSettings.value = false
    onRegenerate(settingsIdx.value, settingsTargetWords.value, settingsExtraPrompt.value)
  }

  function openPolish(idx: number, modelIdx: number) {
    const novel = useNovelStore()
    const settings = useSettingsStore()
    if (idx >= novel.chapters.length) return
    polishIdx.value = idx
    polishOriginal.value = novel.chapters[idx]
    polishResult.value = ''
    polishLoading.value = true
    polishTip.value = '正在润色中，请稍候...'
    showPolish.value = true
    const model = settings.models[modelIdx] || settings.models[0]
    const prompt = '请对以下小说章节进行润色优化，保持原意不变，提升文笔流畅度、画面感和节奏感，去除AI痕迹，使语言更自然生动。直接输出润色后的正文内容，不要任何解释。\n\n原文：\n' + novel.chapters[idx]
    apiStream(
      '/api/generate_chapter_stream',
      { model: { name: model.name, endpoint: model.endpoint, apiKey: model.apiKey, model: model.model }, prompt, target_words: 0, temperature: 0.5, max_tokens: 16000 },
      (text: string) => { polishResult.value += text },
      () => { polishLoading.value = false; polishTip.value = '润色完成' },
      (err: string) => { polishLoading.value = false; polishTip.value = '润色失败: ' + err }
    )
  }

  function savePolish() {
    const novel = useNovelStore()
    if (polishResult.value && polishResult.value !== '(请点击润色按钮后的结果将显示在这里)') {
      novel.chapters[polishIdx.value] = polishResult.value
    }
    showPolish.value = false
  }

  function openCompare(idx: number) {
    const novel = useNovelStore()
    if (idx >= novel.chapters.length) return
    compareIdx.value = idx
    compareOriginal.value = novel.chapters[idx]
    showCompare.value = true
  }

  return {
    showRead, readTitle, readContent, readIdx,
    showSettings, settingsIdx, settingsTargetWords, settingsExtraPrompt,
    showPolish, polishIdx, polishOriginal, polishResult, polishLoading, polishTip,
    showCompare, compareIdx, compareOriginal,
    openRead, saveRead, openSettings, applySettings, openPolish, savePolish, openCompare,
  }
})
