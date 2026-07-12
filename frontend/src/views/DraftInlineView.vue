<template>
  <div v-if="pageLoading" class="page-loading">
    <div class="loading-spinner"></div>
    <p>加载中...</p>
  </div>
  <div v-else class="draft-inline-view">
    <div class="section">
      <h3>正文生成</h3>
      <p class="tip">基于场景设计和细纲，生成章节正文内容</p>

      <div class="form-group">
        <label>选择章节</label>
        <select v-model="form.chapterNo" class="form-select">
          <option v-for="ch in chapterOptions" :key="ch.value" :value="ch.value">{{ ch.label }}</option>
        </select>
      </div>

      <div class="form-group">
        <label>场景骨架</label>
        <textarea v-model="form.skeleton" rows="4" placeholder="输入场景骨架或大纲要点..." class="form-textarea"></textarea>
      </div>

      <div class="form-group">
        <label>写作风格备注</label>
        <input v-model="form.styleNote" placeholder="如：对白为主、心理描写细腻、快节奏..." class="form-input" />
      </div>

      <div class="action-row">
        <button @click="generate" :disabled="loading" class="btn btn-primary">
          <span v-if="loading" class="spinner"></span>{{ loading ? '生成中...' : '生成正文' }}
        </button>
        <button @click="$emit('complete', resultData)" class="btn btn-ghost">跳过</button>
      </div>

      <div v-if="error" class="error-box">
        <p>{{ error }}</p>
        <button @click="useOfflineMode" class="btn btn-ghost btn-sm">使用离线模式</button>
      </div>
    </div>

    <div v-if="content" class="section">
      <h3>生成结果 <span class="word-count">字数：{{ wordCount }}</span></h3>
      <div class="streaming-output" v-if="isStreaming">
        <pre>{{ streamingContent }}</pre>
        <div class="streaming-indicator"><span class="dot"></span><span class="dot"></span><span class="dot"></span></div>
      </div>
      <div v-else class="content-box">
        <pre>{{ content }}</pre>
      </div>
      <div class="action-row">
        <button @click="regenerate" :disabled="loading" class="btn btn-ghost">重新生成</button>
        <button @click="save" class="btn btn-primary">保存正文</button>
        <button @click="handleComplete" class="btn btn-ghost">确认并通过</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { saveDraft, getDrafts, getAllModuleData } from '../api/v2'
import { useExecutionStore } from '../stores/execution'
import { useGeneration } from '../composables/useGeneration'
import { setupConfirm } from '../composables/useConfirm'
import { setupErrorBar } from '../composables/useErrorBar'
import { useChapters } from '../composables/useChapters'
import { useToastStore } from '../stores/toast'

const props = defineProps<{ projectId: string }>()
const emit = defineEmits<{ complete: [data: any] }>()
const gen = useGeneration('draft_generation', '正文生成')
const confirm = setupConfirm()
const errorBar = setupErrorBar()
const pageLoading = ref(true)

const executionStore = useExecutionStore()
const toast = useToastStore()

const form = reactive({ chapterNo: 1, skeleton: '', styleNote: '' })
const loading = ref(false)
const error = ref('')
const content = ref('')
const streamingContent = ref('')
const isStreaming = ref(false)
const isOffline = ref(false)
const chapterOptions = ref<Array<{ value: number | string; label: string }>>([])
const { fetchChapters } = useChapters(props.projectId)

const wordCount = computed(() => content.value.replace(/\s/g, '').length)

// Watch store streaming content for real-time display
watch(() => executionStore.draftContent, (val) => {
  if (isStreaming.value) {
    streamingContent.value = val
    content.value = val
  }
})

const resultData = computed(() => ({
  chapterNo: form.chapterNo,
  skeleton: form.skeleton,
  styleNote: form.styleNote,
  content: content.value,
  wordCount: wordCount.value,
}))

async function generate() {
  const previousContent = content.value
  loading.value = true
  gen.begin()
  error.value = ''
  content.value = ''
  streamingContent.value = ''
  isStreaming.value = true
  isOffline.value = false

  try {
    await executionStore.generateDraftContent(
      props.projectId,
      String(form.chapterNo),
      { skeleton: form.skeleton, style_note: form.styleNote, word_count: 3000 },
    )
    content.value = executionStore.draftContent
    streamingContent.value = executionStore.draftContent
    hasUnsavedChanges = true
  } catch (e: any) {
    errorBar.showError(e, () => generate())
    if (previousContent) {
      content.value = previousContent
    }
  } finally {
    isStreaming.value = false
    loading.value = false
    if (!error.value) gen.end()
    else gen.fail(error.value)
  }
}

function useOfflineMode() {
  isOffline.value = true
  loading.value = true
  error.value = ''
  setTimeout(() => {
    content.value = generateMockContent(form.chapterNo, form.skeleton, form.styleNote)
    streamingContent.value = content.value
    hasUnsavedChanges = true
    loading.value = false
  }, 500)
}

function generateMockContent(chapter: number, skeleton: string, style: string): string {
  const lines = skeleton.split('\n').filter(l => l.trim())
  const sceneHint = lines.length ? lines[0].slice(0, 30) : '启程'
  const styleHint = style ? `写作风格：${style}\n\n` : ''
  return `第${chapter}章 ${sceneHint}

${styleHint}【场景骨架参考】
${skeleton || '（暂无场景骨架，请先完成场景设计模块）'}

【正文开始】

（请在此处基于场景骨架创作正文内容。建议：${lines.length > 1 ? lines.slice(1).join('；') : '围绕核心事件展开描写，注意人物情感变化和场景氛围营造'}）


—— 本章未完 ——`
}

async function save() {
  if (!content.value) return
  try {
    await saveDraft(props.projectId, String(form.chapterNo), content.value)
    lastSavedContent = content.value
    hasUnsavedChanges = false
    clearLocalStorageBackup()
    toast.success('草稿已保存')
  } catch (e: any) {
    toast.error('保存失败: ' + e.message)
    error.value = e.message
  }
}

async function handleComplete() {
  const ok = await confirm.confirm({
    message: '确定通过正文内容？',
    detail: '确认后将保存当前正文并进入下一模块',
    type: 'info',
  })
  if (!ok) return
  hasUnsavedChanges = false
  clearLocalStorageBackup()
  emit('complete', resultData.value)
}

function regenerate() {
  if (isOffline.value) {
    content.value = generateMockContent(form.chapterNo, form.skeleton, form.styleNote)
  } else {
    generate()
  }
}

let autoSaveTimer: ReturnType<typeof setInterval> | null = null
let hasUnsavedChanges = false
let lastSavedContent = ''

function backupToLocalStorage() {
  if (content.value && hasUnsavedChanges) {
    try {
      localStorage.setItem(`draft_backup_${props.projectId}_${form.chapterNo}`, content.value)
    } catch (e: any) {
      if (e?.name === 'QuotaExceededError') {
        toast.info('本地备份空间不足，请手动保存到服务器')
      }
    }
  }
}

function clearLocalStorageBackup() {
  try {
    localStorage.removeItem(`draft_backup_${props.projectId}_${form.chapterNo}`)
  } catch (_e) { /* ignore */ }
}

const beforeUnloadHandler = (e: BeforeUnloadEvent) => {
  if (hasUnsavedChanges && content.value) {
    backupToLocalStorage()
    e.preventDefault()
    e.returnValue = ''
  }
}

onMounted(async () => {
  try {
    try {
      chapterOptions.value = await fetchChapters()
      if (chapterOptions.value.length > 0) {
        const exists = chapterOptions.value.find(c => String(c.value) === String(form.chapterNo))
        if (!exists) form.chapterNo = chapterOptions.value[0].value
      }
    } catch (_e) { /* ignore */ }
    try {
      const drafts = await getDrafts(props.projectId) as any[]
      const found = drafts?.find((d: any) => String(d.chapter_no) === String(form.chapterNo))
      if (found?.content) {
        content.value = found.content
      } else {
        // Restore from localStorage backup if available
        const backup = localStorage.getItem(`draft_backup_${props.projectId}_${form.chapterNo}`)
        if (backup) {
          content.value = backup
          hasUnsavedChanges = true
        }
      }
    } catch (e) {
      console.error('[DraftInlineView] load drafts error:', e)
    }
    try {
      const allData = await getAllModuleData(props.projectId)
      const sceneDesign = allData?.modules?.['scene_design']
      if (sceneDesign && !form.skeleton) {
        const scenes = sceneDesign.scenes || sceneDesign || []
        if (Array.isArray(scenes) && scenes.length > 0) {
          form.skeleton = scenes.map((s: any, i: number) =>
            `[场景${i + 1}] ${s.sceneName || s.name || ''}: ${s.event || s.summary || ''} (氛围:${s.atmosphere || '未知'})`
          ).join('\n')
        }
      }
    } catch (_e) { /* ignore */ }
  } finally {
    pageLoading.value = false
  }

  hasUnsavedChanges = false
  autoSaveTimer = setInterval(async () => {
    if (content.value === lastSavedContent) return
    if (content.value && hasUnsavedChanges) {
      try {
        await saveDraft(props.projectId, String(form.chapterNo), content.value)
        lastSavedContent = content.value
        hasUnsavedChanges = false
        clearLocalStorageBackup()
      } catch (_e) { /* ignore */ }
    }
  }, 15000)

  window.addEventListener('beforeunload', beforeUnloadHandler)
})

onBeforeUnmount(() => {
  window.removeEventListener('beforeunload', beforeUnloadHandler)
  if (autoSaveTimer) clearInterval(autoSaveTimer)
  // Use sendBeacon for reliable unload save
  if (content.value && hasUnsavedChanges) {
    const blob = new Blob([content.value], { type: 'text/plain' })
    const apiPrefix = import.meta.env.VITE_API_PREFIX || ''
    const success = navigator.sendBeacon(`${apiPrefix}/api/v2/projects/${props.projectId}/drafts/${form.chapterNo}/backup`, blob)
    if (!success) backupToLocalStorage()
  }
})
</script>

<style scoped>
.draft-inline-view { max-width: 900px; }
.section { background: #fff; border-radius: 16px; padding: 28px; margin-bottom: 20px; box-shadow: 0 4px 16px rgba(0,0,0,.06); }
.section h3 { font-size: 22px; margin-bottom: 10px; display: flex; align-items: center; gap: 12px; }
.word-count { font-size: 14px; font-weight: 400; color: #888; }
.tip { color: #888; margin-bottom: 20px; font-size: 16px; }
.form-group { margin-bottom: 18px; }
.form-group label { display: block; font-weight: 600; margin-bottom: 8px; font-size: 16px; color: #555; }
.form-input, .form-select, .form-textarea { width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 10px; font-size: 16px; resize: vertical; font-family: inherit; }
.form-textarea { min-height: 100px; }
.action-row { display: flex; gap: 12px; margin-top: 20px; }
.btn { border: none; border-radius: 10px; padding: 12px 24px; font-size: 16px; font-weight: 600; cursor: pointer; }
.btn-sm { padding: 8px 16px; font-size: 14px; }
.btn-primary { background: linear-gradient(135deg, var(--primary), var(--primary-light)); color: #fff; }
.btn-ghost { background: #f0f0f0; color: #555; }
.error-box { margin-top: 16px; padding: 16px; background: #fff3f3; border: 1px solid #ffcdd2; border-radius: 10px; }
.error-box p { color: #c62828; margin-bottom: 8px; }
.spinner { display: inline-block; width: 14px; height: 14px; border: 2px solid #fff; border-top-color: transparent; border-radius: 50%; animation: spin 0.8s linear infinite; margin-right: 6px; }
@keyframes spin { to { transform: rotate(360deg); } }
.streaming-output { background: #f8f9fa; border-radius: 10px; padding: 24px; border: 1px solid #eee; position: relative; }
.streaming-output pre, .content-box pre { white-space: pre-wrap; font-size: 16px; line-height: 1.8; font-family: 'Georgia', serif; }
.content-box { background: #f8f9fa; border-radius: 10px; padding: 24px; border: 1px solid #eee; }
.streaming-indicator { display: flex; gap: 4px; margin-top: 12px; }
.dot { width: 8px; height: 8px; background: var(--primary); border-radius: 50%; animation: pulse 1.4s infinite; }
.dot:nth-child(2) { animation-delay: 0.2s; }
.dot:nth-child(3) { animation-delay: 0.4s; }
@keyframes pulse { 0%, 80%, 100% { opacity: 0.3; } 40% { opacity: 1; } }
.page-loading { display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 300px; gap: 16px; }
.loading-spinner { width: 36px; height: 36px; border: 3px solid #f0f0f0; border-top-color: #409eff; border-radius: 50%; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
</style>
