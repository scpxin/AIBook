<template>
  <div v-if="pageLoading" class="page-loading">
    <div class="loading-spinner"></div>
    <p>加载中...</p>
  </div>
  <div v-else class="writing-view">
    <div class="writing-layout">
      <div class="chapter-selector">
        <h4>章节选择</h4>
        <div v-if="!chapters.length && loadError" class="empty-chapters empty-chapters-error">
          <p class="error-text">⚠ {{ loadError }}</p>
          <button @click="retryLoad" class="btn-retry">重试</button>
          <p class="empty-tip">请先在「创作V2」中生成章节规划</p>
        </div>

        <div v-else-if="!chapters.length" class="empty-chapters">
          <p>暂无章节数据</p>
          <p class="empty-tip">请先在「创作V2」中生成章节规划</p>
        </div>

        <div ref="chapterListRef" class="chapter-list">
        <button v-for="(ch, idx) in chapters" :key="idx" class="chapter-item" :class="{ active: currentChapterIdx === idx }" @click="selectChapter(idx)">
          <span class="ch-num">第{{ idx + 1 }}章</span>
          <span class="ch-title">{{ ch.title }}</span>
          <span v-if="ch.wordCount" class="ch-progress">{{ ch.wordCount }}字</span>
          <span v-if="idx === currentChapterIdx && draftContent !== ch.content" class="ch-unsaved" title="未保存">*</span>
        </button>
        </div>
      </div>

      <div class="writing-main">
        <div class="outline-section" v-if="currentOutline">
          <h4 @click="outlineCollapsed = !outlineCollapsed" style="cursor:pointer;user-select:none">
            <span class="collapse-icon">{{ outlineCollapsed ? '▶' : '▼' }}</span>
            {{ currentOutline.title }} — 章节细纲
          </h4>
          <div v-show="!outlineCollapsed">
            <p v-if="currentOutline.summary" class="outline-summary">{{ currentOutline.summary }}</p>
            <div v-for="(s, si) in currentOutline.scenes" :key="si" class="scene-outline">
              <span class="scene-label">场景{{ si + 1 }}:</span>
              <span class="scene-text">{{ typeof s === 'string' ? s : ((s as any).title || (s as any).summary || JSON.stringify(s)) }}</span>
            </div>
            <div v-if="currentOutline.key_points?.length" class="outline-points">
              <span class="points-label">关键点：</span>
              <span v-for="(p, pi) in currentOutline.key_points" :key="pi" class="point-tag">{{ p }}</span>
            </div>
            <div v-if="currentOutline.characters?.length" class="outline-chars">
              <span class="chars-label">出场人物：</span>
              <span v-for="(c, ci) in currentOutline.characters" :key="ci" class="char-tag">{{ c }}</span>
            </div>
          </div>
        </div>

        <StreamingOutput
          :content="draftContent"
          :streaming="isGenerating"
          placeholder="点击下方按钮开始生成正文..."
        />

        <div class="writing-toolbar">
          <button @click="generateDraft" :disabled="isGenerating" class="btn-generate">
            {{ isGenerating ? '生成中...' : '生成正文' }}
          </button>
          <button @click="polish" :disabled="isPolishing || !draftContent" class="btn-tool">润色</button>
          <button @click="rewrite" :disabled="isGenerating || isRewriting || !draftContent" class="btn-tool">{{ isRewriting ? '重写中...' : '重写' }}</button>
          <button @click="parse" :disabled="isParsing || !draftContent" class="btn-tool">解析</button>
          <button @click="save" :disabled="isSaving || !draftContent" class="btn-save">保存</button>
        </div>

        <div v-if="parseResult" class="parse-result-panel">
          <h4>解析结果</h4>
          <pre>{{ JSON.stringify(parseResult, null, 2) }}</pre>
          <button @click="parseResult = null" class="btn-close">关闭</button>
        </div>
      </div>

      <div class="writing-side">
        <button @click="returnToMainflow" class="btn-return">← 返回主流程</button>
        <KnowledgePanel :project-id="projectId" />
        <ForeshadowPanel :project-id="projectId" />
        <ConsistencyPanel :project-id="projectId" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useExecutionStore } from '../stores/execution'
import StreamingOutput from '../components/StreamingOutput.vue'
import KnowledgePanel from '../components/KnowledgePanel.vue'
import ForeshadowPanel from '../components/ForeshadowPanel.vue'
import ConsistencyPanel from '../components/ConsistencyPanel.vue'
import * as v2Api from '../api/v2'
import { setupConfirm } from '../composables/useConfirm'
import { setupErrorBar } from '../composables/useErrorBar'
import { useToastStore } from '../stores/toast'

const route = useRoute()
const router = useRouter()
const execution = useExecutionStore()

const confirm = setupConfirm()
const errorBar = setupErrorBar()
const toast = useToastStore()
const pageLoading = ref(true)

const projectId = ref(route.query.projectId as string || '')
const chapters = ref<Array<{ id: string; title: string; outline: { title: string; summary: string; scenes: unknown[]; key_points: unknown[]; characters: unknown[] }; content: string; wordCount: number }>>([])
const currentChapterIdx = ref(0)
const draftContent = ref('')
const isGenerating = ref(false)
const isPolishing = ref(false)
const isSaving = ref(false)
const isParsing = ref(false)
const isRewriting = ref(false)
const loadError = ref('')
const parseResult = ref<any>(null)
const chapterListRef = ref<HTMLElement | null>(null)
const outlineCollapsed = ref(true)

const currentOutline = computed(() => {
  if (!chapters.value.length) return null
  const ch = chapters.value[currentChapterIdx.value]
  if (!ch) return null
  return ch.outline && (ch.outline.scenes?.length || ch.outline.summary || ch.outline.key_points?.length)
    ? ch.outline
    : { title: ch.title, summary: '', scenes: [], key_points: [], characters: [] }
})

async function selectChapter(idx: number) {
  if (idx < 0 || idx >= chapters.value.length) return
  if (draftContent.value && draftContent.value !== chapters.value[currentChapterIdx.value]?.content) {
    const ok = await confirm.confirm({
      message: '当前章节草稿有未保存的更改，切换将丢失这些更改，是否继续？',
      detail: '建议先保存当前草稿再切换章节',
      type: 'warning',
    })
    if (!ok) return
  }
  currentChapterIdx.value = idx
  draftContent.value = chapters.value[idx]?.content || ''
}

async function generateDraft() {
  const chapter = chapters.value[currentChapterIdx.value]
  if (!chapter) {
    toast.error('请先生成章节规划，然后再进入写作')
    return
  }
  isGenerating.value = true
  const backup = draftContent.value
  let hadContent = !!draftContent.value
  if (hadContent) toast.info('正在生成，将覆盖现有草稿')
  let firstChunk = true
  try {
    await execution.generateDraft(projectId.value, chapter.id, (text: string) => {
      if (firstChunk) { draftContent.value = ''; firstChunk = false }
      draftContent.value += text
    })
    toast.success('正文生成完成')
    // 5.2-3: 生成正文后自动保存
    if (draftContent.value && draftContent.value !== (chapter.content || '')) {
      try {
        await v2Api.saveDraft(projectId.value, chapter.id, draftContent.value)
        const idx = currentChapterIdx.value
        if (idx >= 0 && idx < chapters.value.length) {
          chapters.value[idx] = {
            ...chapters.value[idx],
            content: draftContent.value,
            wordCount: draftContent.value.length,
          }
        }
        toast.success('草稿已自动保存')
      } catch (saveErr) {
        toast.warning('生成成功但自动保存失败，请手动保存')
      }
    }
  } catch (e) {
    if (hadContent && backup) {
      draftContent.value = backup
    } else if (!draftContent.value) {
      draftContent.value = backup
    }
    errorBar.showError(e, () => generateDraft())
  } finally {
    isGenerating.value = false
  }
}

async function polish() {
  const ok = await confirm.confirm({
    message: '确定执行此操作？',
    detail: '将润色正文内容，可能覆盖现有草稿',
    type: 'warning',
  })
  if (!ok) return
  isPolishing.value = true
  const backup = draftContent.value
  try {
    const result = await execution.polishDraft(projectId.value, backup)
    if (result?.content != null) {
      draftContent.value = result.content
      toast.success('润色完成')
    }
  } catch (e: any) {
    if (backup && !draftContent.value) {
      draftContent.value = backup
    }
    errorBar.showError(e, () => polish())
  } finally {
    isPolishing.value = false
  }
}

async function rewrite() {
  const chapter = chapters.value[currentChapterIdx.value]
  if (!chapter) {
    toast.error('无法识别当前章节')
    return
  }
  const ok = await confirm.confirm({
    message: '确定执行此操作？',
    detail: '将重写正文内容，现有草稿将被覆盖',
    type: 'warning',
  })
  if (!ok) return
  const backup = draftContent.value
  draftContent.value = ''
  isRewriting.value = true
  try {
    await execution.generateDraft(projectId.value, chapter.id, (text: string) => {
      draftContent.value += text
    })
    toast.success('重写完成')
  } catch (e) {
    if (backup && !draftContent.value) {
      draftContent.value = backup
    }
    errorBar.showError(e, () => rewrite())
  } finally {
    isRewriting.value = false
  }
}

async function parse() {
  const chapter = chapters.value[currentChapterIdx.value]
  if (!chapter) {
    toast.error('无法识别当前章节')
    return
  }
  isParsing.value = true
  try {
    const result = await execution.parseContent(projectId.value, draftContent.value, String(chapter.id))
    parseResult.value = result
    toast.success('内容解析完成')
  } catch (e: any) {
    errorBar.showError(e, () => parse())
  } finally {
    isParsing.value = false
  }
}

async function returnToMainflow() {
  if (draftContent.value && draftContent.value !== chapters.value[currentChapterIdx.value]?.content) {
    const ok = await confirm.confirm({
      message: '当前章节草稿有未保存的更改，返回将丢失这些更改，是否继续？',
      detail: '建议先保存当前草稿再返回',
      type: 'warning',
    })
    if (!ok) return
  }
  router.push({ path: '/create-v2', query: { projectId: projectId.value } })
}

async function save() {
  if (isSaving.value) return
  const chapter = chapters.value[currentChapterIdx.value]
  if (!chapter) {
    toast.error('无法识别当前章节，无法保存')
    return
  }
  if (draftContent.value === (chapter.content || '')) {
    toast.info('内容未变更')
    return
  }
  const ok = await confirm.confirm({
    message: '确定执行此操作？',
    detail: '将保存当前草稿内容',
    type: 'warning',
  })
  if (!ok) return
  isSaving.value = true
  try {
    await v2Api.saveDraft(projectId.value, chapter.id, draftContent.value)
    const idx = currentChapterIdx.value
    if (idx >= 0 && idx < chapters.value.length) {
      chapters.value[idx] = {
        ...chapters.value[idx],
        content: draftContent.value,
        wordCount: draftContent.value.length,
      }
    }
    toast.success('草稿保存成功')
  } catch (e) {
    errorBar.showError(e, () => save())
  } finally {
    isSaving.value = false
  }
}

async function retryLoad() {
  pageLoading.value = true
  loadError.value = ''
  try {
    if (projectId.value) {
      try {
        const chaptersData = await execution.getChaptersForWriting(projectId.value)
        if (chaptersData?.length) { chapters.value = chaptersData as any; return }
      } catch (_e) { /* fallback to v2 */ }
      // Fallback: 从v2 pipeline chapter_outline加载
      const outlineData = await v2Api.getModuleData(projectId.value, 'chapter_outline')
      const raw = outlineData?.data
      if (raw) {
        let items: any[] = []
        if (Array.isArray(raw)) items = raw
        else if (raw.chapterOutlines) items = raw.chapterOutlines
        else if (raw.outlines) items = raw.outlines
        else if (raw.form) items = raw.form.chapterOutlines || []
        if (items.length) {
          chapters.value = items.map((o: any, i: number) => ({
            id: String(i + 1),
            title: o.title || o.chapter_title || `第${i + 1}章`,
            outline: { title: o.title || '', summary: o.summary || o.description || '', scenes: o.scenes || o.scene_list || [], key_points: o.key_points || [], characters: o.characters || [] },
            content: o.content || '',
            wordCount: o.wordCount || o.word_count || 0,
          }))
          return
        }
      }
      // Fallback2: 从chapter_plan加载
      const planData = await v2Api.getModuleData(projectId.value, 'chapter_plan')
      const planRaw = planData?.data
      if (planRaw) {
        let items: any[] = []
        if (Array.isArray(planRaw)) items = planRaw
        else if (planRaw.chapterPlans) items = planRaw.chapterPlans
        else if (planRaw.form) items = planRaw.form.chapterPlans || []
        if (items.length) {
          chapters.value = items.map((c: any, i: number) => ({
            id: String(i + 1),
            title: c.title || c.chapter_title || `第${i + 1}章`,
            outline: { title: c.title || '', summary: c.summary || '', scenes: [], key_points: [], characters: [] },
            content: c.content || '',
            wordCount: c.wordCount || c.word_count || c.target_words || 0,
          }))
          return
        }
      }
      loadError.value = '暂无章节数据，请先完成章节规划或章节细纲模块'
    }
  } catch (e: any) {
    loadError.value = e.message || '加载章节失败'
  } finally {
    pageLoading.value = false }
}

onMounted(async () => {
  try {
    if (projectId.value) {
      try {
        const chaptersData = await execution.getChaptersForWriting(projectId.value)
        chapters.value = chaptersData as any
        try {
          const drafts = await execution.getDrafts(projectId.value)
          if (drafts?.length) {
            // P2-6: Multi-strategy chapter matching (exact → number → title → partial)
            const findChapterIdx = (d: any): number => {
              const draftNo = String(d.chapter_no || d.chapter_id || d.id || '')
              const draftTitle = String(d.chapter_title || d.title || '')
              // Strategy 1: Exact ID match
              let idx = chapters.value.findIndex(ch => String(ch.id) === draftNo)
              if (idx >= 0) return idx
              // Strategy 2: Number match (chapter number)
              const numMatch = draftNo.match(/\d+/)
              if (numMatch) {
                const num = parseInt(numMatch[0])
                idx = chapters.value.findIndex(ch => ch.title?.includes(`第${num}章`) || ch.title?.includes(numMatch[0]))
                if (idx >= 0) return idx
              }
              // Strategy 3: Title match
              if (draftTitle) {
                idx = chapters.value.findIndex(ch => ch.title === draftTitle || ch.title?.includes(draftTitle) || draftTitle.includes(ch.title || ''))
                if (idx >= 0) return idx
              }
              // Strategy 4: Index fallback
              const draftIdx = parseInt(draftNo) - 1
              if (draftIdx >= 0 && draftIdx < chapters.value.length) return draftIdx
              return -1
            }
            const currentId = String(chapters.value[currentChapterIdx.value]?.id || '')
            const currentMatch = drafts.find((d: any) => String(d.chapter_no) === currentId)
            if (currentMatch?.content || currentMatch?.content_raw) {
              draftContent.value = currentMatch.content || currentMatch.content_raw
            }
            for (const d of drafts) {
              const idx = findChapterIdx(d)
              if (idx >= 0 && (d.content || d.content_raw)) {
                chapters.value[idx] = {
                  ...chapters.value[idx],
                  content: d.content || d.content_raw,
                  wordCount: (d.content || d.content_raw || '').length,
                }
              }
            }
          }
        } catch (_e) { /* draft restore optional */ }
      } catch (e: any) {
        errorBar.showError(e, () => retryLoad())
        loadError.value = e.message || '加载章节失败'
      }
    } else {
      loadError.value = '缺少项目ID参数，请从「创作V2」进入写作'
    }
  } finally {
    pageLoading.value = false
    await nextTick()
    scrollToActiveChapter()
  }
})

function scrollToActiveChapter() {
  if (!chapterListRef.value) return
  const active = chapterListRef.value.querySelector('.chapter-item.active') as HTMLElement | null
  if (active) {
    active.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
  }
}

watch(() => currentChapterIdx.value, async () => {
  await nextTick()
  scrollToActiveChapter()
})
</script>

<style scoped>
.writing-view { height: 100%; }
.writing-layout { display: flex; height: 100%; gap: 0; }
.chapter-selector {
  width: 234px;
  background: #fafafa;
  border-right: 1px solid #eee;
  overflow-y: auto;
  padding: 16px 0;
  display: flex;
  flex-direction: column;
}
.chapter-list { flex: 1; overflow-y: auto; }
.empty-chapters-error { }
.error-text { color: #cf1322; }
.btn-retry { margin: 8px 0; padding: 6px 16px; background: #fff; border: 1px solid #ffccc7; border-radius: 4px; cursor: pointer; font-size: 13px; color: #cf1322; }
.btn-retry:hover { background: #fff2f0; }
.chapter-selector h4 { padding: 0 12px; margin: 0 0 8px; font-size: 17px; }
.chapter-item {
  display: flex;
  flex-direction: column;
  padding: 10px 12px;
  cursor: pointer;
  border-left: 4px solid transparent;
  transition: 0.15s;
}
.chapter-item:hover { background: #f0f0f0; }
.chapter-item.active { background: #e8f4fd; border-left-color: var(--primary); }
.ch-num { font-size: 16px; color: #888; }
.ch-title { font-size: 17px; font-weight: 500; }
.ch-progress { font-size: 14px; color: #bbb; }
.ch-unsaved { color: #e6a23c; font-weight: bold; font-size: 18px; line-height: 1; margin-left: 4px; }
.collapse-icon { display: inline-block; width: 12px; font-size: 12px; margin-right: 4px; transition: transform 0.2s; }
.writing-main { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
.outline-section { padding: 18px 20px; background: #f9f9f9; border-bottom: 1px solid #eee; max-height: 234px; overflow-y: auto; }
.outline-section h4 { margin: 0 0 8px; font-size: 18px; }
.scene-outline { display: flex; gap: 8px; font-size: 16px; padding: 3px 0; }
.scene-label { color: var(--primary); flex-shrink: 0; font-weight: 500; }
.scene-text { color: #666; }
.outline-summary { font-size: 15px; color: #555; margin: 6px 0; font-style: italic; }
.outline-points, .outline-chars { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 6px; align-items: center; }
.points-label, .chars-label { font-size: 14px; color: #888; font-weight: 500; }
.point-tag, .char-tag { font-size: 13px; background: #e8f4fd; color: #1890ff; padding: 2px 7px; border-radius: 4px; }
.char-tag { background: #f6ffed; color: #52c41a; }
.writing-toolbar { display: flex; gap: 10px; padding: 13px 20px; border-top: 1px solid #eee; background: #fafafa; }
.btn-generate { padding: 10px 20px; background: var(--primary); color: #fff; border: none; border-radius: 5px; cursor: pointer; }
.btn-generate:disabled { opacity: 0.5; cursor: wait; }
.btn-tool { padding: 10px 14px; background: #fff; border: 1px solid #ddd; border-radius: 5px; cursor: pointer; font-size: 17px; }
.btn-tool:disabled { opacity: 0.4; cursor: not-allowed; }
.btn-save { padding: 10px 14px; background: #52c41a; color: #fff; border: none; border-radius: 5px; cursor: pointer; margin-left: auto; }
.btn-return { width: 100%; padding: 10px; margin-bottom: 14px; background: #fff; border: 1px solid #ddd; border-radius: 6px; cursor: pointer; font-size: 15px; text-align: center; }
.btn-return:hover { background: #f5f5f5; border-color: #999; }
.writing-side { width: 338px; background: #fafafa; border-left: 1px solid #eee; overflow-y: auto; padding: 16px; }
.empty-chapters { padding: 20px 12px; text-align: center; color: #999; font-size: 16px; }
.empty-tip { font-size: 14px; color: #bbb; margin-top: 4px; }
.page-loading { display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 300px; gap: 16px; }
.loading-spinner { width: 36px; height: 36px; border: 3px solid #f0f0f0; border-top-color: #409eff; border-radius: 50%; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
</style>
