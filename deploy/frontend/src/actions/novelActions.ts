import { useNovelStore } from '../stores/novel'
import { useSettingsStore } from '../stores/settings'
import { useProjectStore } from '../stores/project'
import * as novelApi from '../api/novel'
import * as chapterApi from '../api/chapter'
import * as outlineApi from '../api/outline'
import * as downloadApi from '../api/download'
import { apiStream } from '../api/client'

export function getNovelModel(idx?: number) {
  const settings = useSettingsStore()
  return settings.models[idx || 0] || settings.models[0]
}

export async function loadSavedBooks() {
  const novel = useNovelStore()
  try {
    const d = await downloadApi.listSavedBooks()
    novel.savedBooks = d.books || []
  } catch {
    novel.savedBooks = []
  }
}

export async function loadAnalyzeSavedBooks() {
  const novel = useNovelStore()
  try {
    const d = await downloadApi.listSavedBooks()
    novel.analyzeSavedBooks = d.books || []
  } catch {
    novel.analyzeSavedBooks = []
  }
}

export async function selectAnalyzeBook(b: any) {
  const novel = useNovelStore()
  novel.selectedAnalyzeBook = b.book_id
  try {
    const d = await downloadApi.getBookContent(b.book_id)
    novel.analyzeBookContent = d.content || ''
    novel.analyzeText = (d.content || '').slice(0, 10000)
  } catch {
    novel.analyzeBookContent = ''
  }
}

export async function analyzeStyleText() {
  const novel = useNovelStore()
  const m = getNovelModel()
  if (!m) { alert('请先配置AI模型'); return }
  if (!novel.styleText.trim()) { alert('请先粘贴小说文本'); return }
  novel.styleLoading = true
  try {
    const d = await novelApi.analyzeStyleApi({ endpoint: m.endpoint, apiKey: m.apiKey, model: m.model, content: novel.styleText.trim() })
    novel.styleProfile = d.result || ''
  } catch (e: any) {
    alert('分析失败: ' + e.message)
  }
  novel.styleLoading = false
}

export async function analyzeSavedBook(b: any) {
  const novel = useNovelStore()
  const m = getNovelModel()
  if (!m) { alert('请先配置AI模型'); return }
  novel.selectedSavedBook = b.book_id
  novel.savedBookAnalyzing = true
  try {
    const d = await downloadApi.getBookContent(b.book_id)
    const content = d.content || ''
    const r = await novelApi.analyzeStyleApi({ endpoint: m.endpoint, apiKey: m.apiKey, model: m.model, content })
    novel.styleProfile = r.result || ''
  } catch (e: any) {
    alert('分析失败: ' + e.message)
  }
  novel.savedBookAnalyzing = false
}

export async function generateInspire() {
  const novel = useNovelStore()
  const m = getNovelModel()
  if (!m) { alert('请先配置AI模型'); return }
  novel.inspireLoading = true
  novel.inspireError = ''
  const inspireTitleOptions: any[] = []
  const inspireDescOptions: any[] = []
  ;(novel as any)._inspireTitleOptions = inspireTitleOptions
  ;(novel as any)._inspireDescOptions = inspireDescOptions

  try {
    const d1 = await novelApi.inspirationTitleApi({ endpoint: m.endpoint, apiKey: m.apiKey, model: m.model, styleProfile: novel.styleProfile })
    const titleOpts = (d1.options || []).map((opt: any, i: number) => ({
      idx: i,
      text: typeof opt === 'object' ? (opt.name || opt.title || opt.text || JSON.stringify(opt)) : opt,
      selected: i === 0,
    }))
    inspireTitleOptions.push(...titleOpts)
    if (d1.options && d1.options[0]) {
      const first = d1.options[0]
      novel.title = typeof first === 'object' ? (first.name || first.title || first.text || JSON.stringify(first)) : first
    }

    const d2 = await novelApi.inspirationDescriptionApi({ endpoint: m.endpoint, apiKey: m.apiKey, model: m.model, title: novel.title, styleProfile: novel.styleProfile })
    const descOpts = (d2.options || []).map((opt: any, i: number) => ({
      idx: i,
      text: typeof opt === 'object' ? (opt.name || opt.title || opt.text || opt.description || JSON.stringify(opt)) : opt,
      selected: i === 0,
    }))
    inspireDescOptions.push(...descOpts)
    if (d2.options && d2.options[0]) {
      const first = d2.options[0]
      novel.description = typeof first === 'object' ? (first.name || first.title || first.text || first.description || JSON.stringify(first)) : first
    }

    const d3 = await novelApi.inspirationThemeApi({ endpoint: m.endpoint, apiKey: m.apiKey, model: m.model, title: novel.title, description: novel.description, styleProfile: novel.styleProfile })
    if (d3.options && d3.options[0]) {
      const first = d3.options[0]
      novel.theme = typeof first === 'object' ? (first.name || first.title || first.text || first.theme || JSON.stringify(first)) : first
    }

    const d4 = await novelApi.inspirationGenreApi({ endpoint: m.endpoint, apiKey: m.apiKey, model: m.model, title: novel.title, description: novel.description, styleProfile: novel.styleProfile })
    if (d4.options && d4.options[0]) {
      const first = d4.options[0]
      novel.genre = typeof first === 'object' ? (first.name || first.title || first.text || first.genre || JSON.stringify(first)) : first
    }

    await saveStepSummary('inspiration', {
      title: novel.title, description: novel.description, theme: novel.theme, genre: novel.genre,
    })
  } catch (e: any) {
    novel.inspireError = e.message
  }
  novel.inspireLoading = false
}

export function getInspireTitleOptions() {
  const novel = useNovelStore()
  return (novel as any)._inspireTitleOptions || []
}

export function getInspireDescOptions() {
  const novel = useNovelStore()
  return (novel as any)._inspireDescOptions || []
}

export function selectInspireTitle(opt: any) {
  const novel = useNovelStore()
  const opts = getInspireTitleOptions()
  opts.forEach((o: any) => o.selected = false)
  opt.selected = true
  novel.title = opt.text
}

export function selectInspireDesc(opt: any) {
  const novel = useNovelStore()
  const opts = getInspireDescOptions()
  opts.forEach((o: any) => o.selected = false)
  opt.selected = true
  novel.description = opt.text
}

export async function generateWorld() {
  const novel = useNovelStore()
  const m = getNovelModel()
  if (!m) { alert('请先配置AI模型'); return }
  novel.world = '正在生成世界观，请稍候...'
  try {
    const description = (novel.styleProfile ? '[风格参考]\n' + novel.styleProfile + '\n\n[故事简介]\n' : '') + novel.description
    const d = await novelApi.worldbuildingApi({ endpoint: m.endpoint, apiKey: m.apiKey, model: m.model, title: novel.title, theme: novel.theme, genre: novel.genre, description, styleProfile: novel.styleProfile })
    let text = ''
    const labels: Record<string, string> = { time_period: '【时间背景】', location: '【空间环境】', atmosphere: '【情感基调】', rules: '【世界规则】' }
    ;['time_period', 'location', 'atmosphere', 'rules'].forEach(k => {
      if (d.world?.[k]) {
        let val = d.world[k]
        if (typeof val === 'object') {
          val = val.description || val.detail || val.content || val.name || JSON.stringify(val)
        }
        text += labels[k] + '\n' + val + '\n\n'
      }
    })
    novel.world = text.trim()
    await saveStepSummary('world', { world: novel.world })
  } catch (e: any) {
    novel.world = '生成失败: ' + e.message
  }
}

export async function generateChars() {
  const novel = useNovelStore()
  const m = getNovelModel()
  if (!m) { alert('请先配置AI模型'); return }
  novel.charsLoading = true
  novel.characters = '正在生成角色，请稍候...'
  try {
    const theme = novel.theme + (novel.styleProfile ? '\n\n[风格参考]\n' + novel.styleProfile : '')
    const d = await novelApi.charactersApi({ endpoint: m.endpoint, apiKey: m.apiKey, model: m.model, worldData: { rules: novel.world }, theme, genre: novel.genre, count: novel.charCount, styleProfile: novel.styleProfile })
    let text = ''
    ;(d.characters || []).forEach((c: any) => {
      if (c.is_organization) {
        text += (c.name || '') + ' - 组织 - ' + (c.organization_purpose || '') + '\n'
      } else {
        text += (c.name || '') + ' - ' + (c.role_type || '角色') + ' - ' + (c.personality || '') + '\n'
      }
    })
    novel.characters = text.trim()
    await saveStepSummary('characters', { characters: novel.characters })
  } catch (e: any) {
    novel.characters = '生成失败: ' + e.message
  }
  novel.charsLoading = false
}

async function loadStepSummaries() {
  const projectStore = useProjectStore()
  if (!projectStore.currentProjectId) return {}
  try {
    const r = await novelApi.stepSummaryGetApi(projectStore.currentProjectId)
    return r.summaries || {}
  } catch {
    return {}
  }
}

async function saveStepSummary(step: string, summaryData: any) {
  const projectStore = useProjectStore()
  if (!projectStore.currentProjectId) return
  try {
    await novelApi.stepSummarySaveApi({ projectId: projectStore.currentProjectId, step, summary: summaryData })
  } catch {
    console.error('步骤摘要保存失败')
  }
}

export async function generateOutline() {
  const novel = useNovelStore()
  const m = getNovelModel()
  if (!m) { alert('请先配置AI模型'); return }
  novel.outlineLoading = true
  novel.outlineText = '正在生成大纲，请稍候...'
  try {
    const summaries = await loadStepSummaries()
    const summaryParts: string[] = []
    if (summaries.inspiration) {
      const ins = summaries.inspiration
      summaryParts.push('[灵感步骤] 标题: ' + (ins.title || '') + ' | 简介: ' + (ins.description || '') + ' | 主题: ' + (ins.theme || '') + ' | 类型: ' + (ins.genre || ''))
    }
    if (summaries.world) {
      summaryParts.push('[世界观步骤] ' + (summaries.world.world || '').slice(0, 500))
    }
    if (summaries.characters) {
      summaryParts.push('[角色步骤] ' + (summaries.characters.characters || '').slice(0, 500))
    }
    const stepContext = summaryParts.length > 0 ? '\n\n[前期步骤摘要]\n' + summaryParts.join('\n') : ''
    const title = novel.title + (novel.styleProfile ? '\n\n[风格参考]\n' + novel.styleProfile : '') + stepContext
    const d = await novelApi.outlineApi({ endpoint: m.endpoint, apiKey: m.apiKey, model: m.model, title, theme: novel.theme, genre: novel.genre, charactersInfo: novel.characters, chapterCount: novel.chapterCount, narrativePerspective: novel.perspective, styleProfile: novel.styleProfile })
    const outline = d.outline || []
    let text = ''
    outline.forEach((o: any) => {
      text += '第' + o.chapter_number + '章 ' + (o.title || '') + ' - ' + (o.summary || '') + '\n'
    })
    novel.outlineText = text.trim()
    parseOutline()
    await saveOutlineToDb()
    await saveStepSummary('outline', { outlineText: novel.outlineText, outline: novel.outline })
  } catch (e: any) {
    novel.outlineText = '生成失败: ' + e.message
  }
  novel.outlineLoading = false
}

export function parseOutline() {
  const novel = useNovelStore()
  const text = novel.outlineText.trim()
  if (!text) { novel.outline = []; return }
  const lines = text.split('\n').filter(l => l.trim())
  novel.outline = lines.map((line: string, i: number) => {
    const m = line.match(/第([一-龥\d]+)章\s*(.*)/)
    if (m) return { chapter_number: m[1], title: m[1], summary: m[2] || '' }
    return { chapter_number: String(i + 1), title: line.slice(0, 30), summary: line }
  })
}

async function saveOutlineToDb() {
  const novel = useNovelStore()
  const projectStore = useProjectStore()
  if (!projectStore.currentProjectId) return
  if (!novel.outline || novel.outline.length === 0) return
  for (const o of novel.outline) {
    try {
      await outlineApi.saveOutlineApi({
        projectId: projectStore.currentProjectId,
        chapterNumber: typeof o.chapter_number === 'string' ? parseInt(o.chapter_number) || 1 : o.chapter_number,
        title: o.title || '',
        summary: o.summary || '',
        status: 'done',
      })
    } catch (e: any) {
      console.error('大纲保存失败:', e.message)
    }
  }
}

export async function loadOutlinesFromDb() {
  const novel = useNovelStore()
  const projectStore = useProjectStore()
  if (!projectStore.currentProjectId) return
  try {
    const r = await outlineApi.getOutlinesApi(projectStore.currentProjectId)
    if (r.outlines && Array.isArray(r.outlines) && r.outlines.length > 0) {
      const outlineItems = r.outlines.sort((a: any, b: any) => a.chapter_number - b.chapter_number)
      novel.outline = outlineItems.map((o: any) => ({
        chapter_number: o.chapter_number,
        title: o.title || ('第' + o.chapter_number + '章'),
        summary: o.summary || '',
      }))
      let text = ''
      outlineItems.forEach((o: any) => {
        text += '第' + o.chapter_number + '章 ' + (o.title || '') + ' - ' + (o.summary || '') + '\n'
      })
      novel.outlineText = text.trim()
    }
  } catch (e: any) {
    console.error('加载大纲失败:', e.message)
  }
}

export async function loadChaptersFromDb() {
  const novel = useNovelStore()
  const projectStore = useProjectStore()
  if (!projectStore.currentProjectId) return
  try {
    const r = await chapterApi.getChaptersApi(projectStore.currentProjectId)
    if (r.chapters && Array.isArray(r.chapters)) {
      for (const ch of r.chapters) {
        const idx = ch.chapter_number - 1
        if (ch.status === 'done' && ch.content && idx < novel.outline.length) {
          if (!novel.chapters[idx] || novel.chapters[idx].length < 100) {
            novel.chapters[idx] = ch.content
          }
        }
      }
    }
  } catch (e: any) {
    console.error('加载章节失败:', e.message)
  }
}

export async function generateNextChapter() {
  const novel = useNovelStore()
  parseOutline()
  if (!novel.outline.length) { alert('请先在「大纲」步骤中输入或生成大纲'); return }
  if (novel.chapters.length >= novel.outline.length) { alert('所有章节已生成完毕'); return }
  const projectStore = useProjectStore()
  if (!projectStore.currentProjectId) {
    const autoName = novel.title || '未命名项目'
    projectStore.projectName = autoName
    await saveProject()
  }
  await generateOneChapter(novel.chapters.length)
}

export async function generateAllChapters() {
  const novel = useNovelStore()
  parseOutline()
  if (!novel.outline.length) { alert('请先在「大纲」步骤中输入或生成大纲'); return }
  const projectStore = useProjectStore()
  if (!projectStore.currentProjectId) {
    const autoName = novel.title || '未命名项目'
    projectStore.projectName = autoName
    await saveProject()
  }
  await loadChaptersFromDb()
  let startIdx = novel.chapters.length
  for (let i = 0; i < novel.outline.length; i++) {
    if (i < novel.chapters.length && novel.chapters[i] && novel.chapters[i].length > 100) {
      continue
    }
    startIdx = i
    break
  }
  if (startIdx >= novel.outline.length) {
    alert('所有章节已生成完毕')
    return
  }
  try {
    await chapterApi.startGenerationApi(projectStore.currentProjectId, novel.outline.length)
  } catch { /* ignore */ }
  novel.genStatus = { total: novel.outline.length, completed: startIdx, failed: 0, current: startIdx + 1 }
  let i = startIdx
  novel.chapterPaused = false
  novel.chapterPauseIdx = i

  async function next() {
    if (novel.chapterPaused) { novel.chapterPauseIdx = i; return }
    if (i >= novel.outline.length) { novel.genStatus.current = 0; return }
    if (i < novel.chapters.length && novel.chapters[i] && novel.chapters[i].length > 100) { i++; next(); return }
    novel.genStatus.current = i + 1
    const success = await generateOneChapter(i)
    if (novel.chapterPaused) { novel.chapterPauseIdx = i; return }
    if (novel.chapters[i] && novel.chapters[i].length > 100) {
      novel.genStatus.completed++
    } else {
      novel.genStatus.failed++
    }
    try {
      await chapterApi.updateGenerationProgressApi({
        projectId: projectStore.currentProjectId,
        currentChapter: i + 1,
        completedChapters: novel.genStatus.completed,
        failedChapters: novel.genStatus.failed,
      })
    } catch { /* ignore */ }
    i++
    next()
  }
  next()
}

export function pauseGeneration() {
  const novel = useNovelStore()
  const projectStore = useProjectStore()
  novel.chapterPaused = true
  novel.chapterProgress = '已暂停（点击"继续生成"恢复）'
  chapterApi.pauseGenerationApi(projectStore.currentProjectId).catch(() => {})
}

export async function resumeGeneration() {
  const novel = useNovelStore()
  novel.chapterPaused = false
  await generateAllChapters()
}

async function saveChapterToDb(idx: number) {
  const novel = useNovelStore()
  const projectStore = useProjectStore()
  if (!projectStore.currentProjectId) return
  if (!novel.chapters[idx]) return
  const o = novel.outline[idx]
  try {
    await chapterApi.saveChapterApi({
      projectId: projectStore.currentProjectId,
      chapterNumber: idx + 1,
      title: o ? (o.title || ('第' + (idx + 1) + '章')) : ('第' + (idx + 1) + '章'),
      content: novel.chapters[idx],
      status: 'done',
    })
  } catch (e: any) {
    console.error('章节保存失败:', e.message)
  }
}

async function generateOneChapter(idx: number) {
  const novel = useNovelStore()
  const m = getNovelModel()
  if (!m) { alert('请先配置AI模型'); return false }
  novel.chapterLoading = true
  novel.chapterProgress = '正在生成第' + (idx + 1) + '章 / 共' + novel.outline.length + '章...'
  const o = novel.outline[idx]
  const prevSummary = idx > 0 ? (novel.chapters[idx - 1] || '').slice(0, 200) : ''
  const prevEnd = idx > 0 ? (novel.chapters[idx - 1] || '').slice(-300) : ''
  let stepContext = ''
  try {
    const summaries = await loadStepSummaries()
    const ctxParts: string[] = []
    if (summaries.world && summaries.world.world) {
      ctxParts.push('[世界观] ' + summaries.world.world.slice(0, 300))
    }
    if (summaries.characters && summaries.characters.characters) {
      ctxParts.push('[角色] ' + summaries.characters.characters.slice(0, 300))
    }
    if (ctxParts.length > 0) stepContext = '\n\n[上下文参考]\n' + ctxParts.join('\n')
  } catch { /* ignore */ }
  try {
    const outlineChapterNum = typeof o.chapter_number === 'string' ? parseInt(o.chapter_number) || (idx + 1) : o.chapter_number
    const d = await novelApi.generateChapterApi({
      endpoint: m.endpoint,
      apiKey: m.apiKey,
      model: m.model,
      projectTitle: novel.title,
      genre: novel.genre,
      chapterNumber: outlineChapterNum || (idx + 1),
      chapterTitle: o.title || '',
      chapterOutline: o.summary + stepContext,
      continuationPoint: prevEnd,
      previousChapterSummary: prevSummary,
      chapterCharacters: (o.characters || []).join(', '),
      targetWordCount: novel.targetWords,
      narrativePerspective: novel.perspective,
      useCraft: novel.useCraft,
    })
    novel.chapters[idx] = d.content
    novel.chapterProgress = ''
    await saveChapterToDb(idx)
    return true
  } catch (e: any) {
    novel.chapterProgress = '第' + (idx + 1) + '章生成失败: ' + e.message
    return false
  } finally {
    novel.chapterLoading = false
  }
}

export function exportNovel() {
  const novel = useNovelStore()
  if (!novel.chapters.length) { alert('没有可导出的章节'); return }
  let text = novel.title + '\n\n'
  if (novel.description) text += '简介：' + novel.description + '\n\n'
  if (novel.world) text += '=== 世界观 ===\n' + novel.world + '\n\n'
  if (novel.characters) text += '=== 角色 ===\n' + novel.characters + '\n\n'
  text += '=== 正文 ===\n\n'
  novel.chapters.forEach((c, i) => {
    if (!c) return
    const title = novel.outline[i] ? novel.outline[i].title : String(i + 1)
    text += '第' + (i + 1) + '章 ' + title + '\n\n' + c + '\n\n'
  })
  const blob = new Blob(['\uFEFF' + text], { type: 'text/plain;charset=utf-8' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = (novel.title || '小说') + '.txt'
  a.click()
  setTimeout(() => URL.revokeObjectURL(a.href), 2000)
}

export async function runAnalyze(modelIdx?: number) {
  const novel = useNovelStore()
  const m = getNovelModel(modelIdx)
  if (!m) { alert('请先选择模型'); return }
  if (!novel.analyzeText.trim()) { alert('请先粘贴小说文本'); return }
  novel.analyzeLoading = true
  try {
    const d = await novelApi.aiAnalyzeApi({ endpoint: m.endpoint, apiKey: m.apiKey, model: m.model, content: novel.analyzeText.trim() })
    novel.analyzeResult = d.result
    novel.styleProfileForGenerate = d.result
  } catch (e: any) {
    alert('分析失败: ' + e.message)
  }
  novel.analyzeLoading = false
}

export async function runGenerate(modelIdx?: number) {
  const novel = useNovelStore()
  const m = getNovelModel(modelIdx)
  if (!m) { alert('请先选择模型'); return }
  if (!novel.styleProfileForGenerate) { alert('请先完成风格分析'); return }
  novel.genLoading = true
  try {
    const d = await novelApi.aiGenerateApi({
      endpoint: m.endpoint,
      apiKey: m.apiKey,
      model: m.model,
      styleProfile: novel.styleProfileForGenerate,
      genre: novel.genForm.genre || '未指定',
      count: novel.genForm.count || 3,
      protagonist: novel.genForm.protagonist || '未指定',
      world: novel.genForm.world || '未指定',
      outline: novel.genForm.outline || '未指定',
    })
    novel.genResult = d.result
  } catch (e: any) {
    alert('生成失败: ' + e.message)
  }
  novel.genLoading = false
}

export function getGenChapters() {
  const novel = useNovelStore()
  if (!novel.genResult) return []
  const chapters: any[] = []
  const re = /第([一-龥\d]+)章\s*(.*?)(?:\n|$)/g
  let match
  let lastIdx = 0
  while ((match = re.exec(novel.genResult)) !== null) {
    if (lastIdx > 0) chapters[chapters.length - 1].text = novel.genResult.slice(lastIdx, match.index).trim()
    chapters.push({ title: '第' + match[1] + '章' + (match[2] ? ' ' + match[2] : ''), text: '' })
    lastIdx = match.index + match[0].length
  }
  if (chapters.length && lastIdx < novel.genResult.length) {
    chapters[chapters.length - 1].text = novel.genResult.slice(lastIdx).trim()
  }
  return chapters
}

export function saveGenerated() {
  const novel = useNovelStore()
  if (!novel.genResult) return
  const blob = new Blob(['\uFEFF' + novel.genResult], { type: 'text/plain;charset=utf-8' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = 'AI仿写.txt'
  a.click()
  setTimeout(() => URL.revokeObjectURL(a.href), 2000)
}

export function polishChapter(idx: number) {
  const novel = useNovelStore()
  const modals = useNovelStore() as any
  if (idx >= novel.chapters.length) return
  ;(modals as any)._polishOriginal = novel.chapters[idx]
  ;(modals as any)._polishResult = ''
  ;(modals as any)._polishTip = '正在润色中，请稍候...'
  ;(modals as any)._polishShow = true
  ;(modals as any)._polishIdx = idx
  const prompt = '请对以下小说章节进行润色优化，保持原意不变，提升文笔流畅度、画面感和节奏感，去除AI痕迹，使语言更自然生动。直接输出润色后的正文内容，不要任何解释。\n\n原文：\n' + novel.chapters[idx]
  const model = getNovelModel()
  apiStream(
    '/api/generate_chapter_stream',
    { model: { name: model.name, endpoint: model.endpoint, apiKey: model.apiKey, model: model.model }, prompt, target_words: 0, temperature: 0.5, max_tokens: 16000 },
    (text: string) => { (modals as any)._polishResult += text },
    () => { (modals as any)._polishTip = '润色完成' },
    (err: string) => { (modals as any)._polishTip = '润色失败: ' + err }
  )
}

export function openCompare(idx: number) {
  const novel = useNovelStore()
  const modals = useNovelStore() as any
  if (idx >= novel.chapters.length) return
  ;(modals as any)._compareOriginal = novel.chapters[idx]
  ;(modals as any)._compareShow = true
  ;(modals as any)._compareIdx = idx
}

export async function saveProject() {
  const novel = useNovelStore()
  const projectStore = useProjectStore()
  if (!projectStore.projectName.trim()) { alert('请输入项目名称'); return }
  const novelData = JSON.parse(JSON.stringify({
    title: novel.title, description: novel.description, theme: novel.theme, genre: novel.genre,
    world: novel.world, characters: novel.characters, outlineText: novel.outlineText,
    outline: novel.outline, chapters: novel.chapters, step: novel.step,
    targetWords: novel.targetWords, useCraft: novel.useCraft,
    chapterCount: novel.chapterCount, charCount: novel.charCount,
    perspective: novel.perspective, styleProfile: novel.styleProfile,
  }))
  try {
    const r = await projectStore.save({
      id: projectStore.currentProjectId || undefined,
      name: projectStore.projectName.trim(),
      step: novel.step || 0,
      novelData,
    })
    projectStore.currentProjectId = r.id
    projectStore.selectedProjectId = r.id
    await projectStore.loadList()
    alert('项目已保存: ' + r.name)
  } catch (e: any) {
    alert('保存失败: ' + e.message)
  }
}

export async function loadProject() {
  const novel = useNovelStore()
  const projectStore = useProjectStore()
  if (!projectStore.selectedProjectId) return
  try {
    const r = await projectStore.load(projectStore.selectedProjectId)
    if (r.error) { alert(r.error); return }
    projectStore.currentProjectId = r.id
    projectStore.projectName = r.name || ''
    const n = r.data || {}
    novel.title = n.title || ''
    novel.description = n.description || ''
    novel.theme = n.theme || ''
    novel.genre = n.genre || ''
    novel.world = n.world || ''
    novel.characters = n.characters || ''
    novel.outlineText = n.outlineText || ''
    novel.outline = n.outline || []
    novel.chapters = n.chapters || []
    novel.step = n.step || 0
    novel.targetWords = n.targetWords || 3000
    novel.useCraft = n.useCraft || false
    novel.chapterCount = n.chapterCount || 10
    novel.charCount = n.charCount || 3
    novel.perspective = n.perspective || '第三人称'
    novel.styleProfile = n.styleProfile || ''
    await loadOutlinesFromDb()
    await loadChaptersFromDb()
    alert('已加载项目: ' + r.name)
  } catch (e: any) {
    alert('加载失败: ' + e.message)
  }
}

export async function deleteProject() {
  const projectStore = useProjectStore()
  if (!projectStore.selectedProjectId) return
  const proj = projectStore.projectList.find(p => p.id === projectStore.selectedProjectId)
  if (!proj) return
  if (!confirm('确定删除项目 "' + proj.name + '"？')) return
  try {
    await projectStore.remove(projectStore.selectedProjectId)
    alert('已删除')
  } catch (e: any) {
    alert('删除失败: ' + e.message)
  }
}

export function newProject() {
  const novel = useNovelStore()
  const projectStore = useProjectStore()
  novel.reset()
  projectStore.projectName = ''
  projectStore.selectedProjectId = ''
}
