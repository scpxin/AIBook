<template>
  <div v-if="pageLoading" class="page-loading">
    <div class="loading-spinner"></div>
    <p>加载中...</p>
  </div>
  <div v-else class="export-view">
    <div class="section">
      <h3>导出作品</h3>
      <p class="tip">将作品导出为 TXT 或 Markdown 格式</p>

      <div v-if="loadError" class="error-state">
        <p>{{ loadError }}</p>
        <button @click="loadData" class="btn btn-primary">重试</button>
      </div>

      <div v-if="!loaded && !loadError" class="action-row">
        <button @click="loadData" class="btn btn-primary">加载作品数据</button>
      </div>

      <div v-else-if="loaded && !hasAnyData" class="empty-message">
        <p>暂无作品数据，请先完成前面的创作模块</p>
        <button @click="loadData" class="btn-secondary">重新加载</button>
      </div>

      <div v-else>
        <div class="export-controls">
          <div class="form-group">
            <label>导出格式</label>
            <select v-model="format" class="form-select">
              <option value="txt">纯文本 (.txt)</option>
              <option value="md">Markdown (.md)</option>
            </select>
          </div>
          <div class="form-group">
            <label>内容范围</label>
            <select v-model="scope" class="form-select">
              <option value="all">完整作品（大纲+正文）</option>
              <option value="outline">仅大纲</option>
              <option value="draft">仅正文（有章节才导出）</option>
            </select>
          </div>
          <div v-if="contentWarning" class="content-warning">{{ contentWarning }}</div>
          <div class="action-row">
            <button @click="doExport" class="btn btn-primary" :disabled="!hasAnyData || exportLoading">
              {{ exportLoading ? '导出中...' : '下载' }}
            </button>
            <button @click="preview = !preview" class="btn btn-ghost">{{ preview ? '隐藏预览' : '预览' }}</button>
          </div>
        </div>

        <div class="stats">
          <span>卷纲: {{ volumes.length }}</span>
          <span>章节规划: {{ chapterPlans.length }}</span>
          <span>章节大纲: {{ chapterOutlines.length }}</span>
          <span>正文: {{ drafts.length }}</span>
        </div>

        <div v-if="preview" class="preview-box">
          <h4>预览 (前2000字符)</h4>
          <pre>{{ previewText }}</pre>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import * as v2Api from '../api/v2'
import { useToastStore } from '../stores/toast'
import { setupErrorBar } from '../composables/useErrorBar'

const props = defineProps<{ projectId: string }>()

const toast = useToastStore()
const errorBar = setupErrorBar()
const pageLoading = ref(true)

const loaded = ref(false)
const loadError = ref('')
const format = ref('md')
const scope = ref('all')
const preview = ref(false)
const modulesData = ref<Record<string, any>>({})

const volumes = ref<any[]>([])
const chapterPlans = ref<any[]>([])
const chapterOutlines = ref<any[]>([])
const drafts = ref<any[]>([])

const hasAnyData = computed(() =>
  volumes.value.length > 0 ||
  chapterPlans.value.length > 0 ||
  chapterOutlines.value.length > 0 ||
  drafts.value.some(d => !!(d.content || d.content_raw))
)

async function loadData() {
  try {
    const data = await v2Api.getAllModuleData(props.projectId)
    modulesData.value = data?.modules || {}

    const sa = modulesData.value['architecture'] || {}
    volumes.value = modulesData.value['volumes'] || []
    chapterPlans.value = modulesData.value['chapter_plan'] || []
    chapterOutlines.value = modulesData.value['chapter_plan'] || []
    drafts.value = modulesData.value['draft'] || []

    if (!Array.isArray(volumes.value)) volumes.value = []
    if (!Array.isArray(chapterPlans.value)) chapterPlans.value = []
    if (!Array.isArray(chapterOutlines.value)) chapterOutlines.value = []
    if (!Array.isArray(drafts.value)) drafts.value = []

    loaded.value = true
  } catch (_e) {
    errorBar.showError(_e)
    loaded.value = false
  } finally {
    pageLoading.value = false
  }
}

const previewText = computed(() => {
  const full = generateContent()
  return full.slice(0, 2000) + (full.length > 2000 ? '\n...' : '')
})

function generateContent(): string {
  const isMD = format.value === 'md'
  const lines: string[] = []
  const H1 = isMD ? '# ' : ''
  const H2 = isMD ? '## ' : ''
  const H3 = isMD ? '### ' : ''
  const HR = isMD ? '\n---\n' : '\n' + '='.repeat(40) + '\n'

  if (scope.value === 'all' || scope.value === 'outline') {
    lines.push(`${H1}小说大纲`)
    lines.push('')

    if (volumes.value.length) {
      lines.push(`${H2}卷纲`)
      lines.push('')
      volumes.value.forEach((v: any, i: number) => {
        const name = v.name || v.title || `第${i + 1}卷`
        lines.push(`${H3}${name}`)
        if (v.summary) lines.push(v.summary)
        lines.push('')
      })
    }

    if (chapterPlans.value.length) {
      lines.push(`${H2}章节规划`)
      lines.push('')
      chapterPlans.value.forEach((cp: any, i: number) => {
        const title = cp.title || cp.chapter_title || `第${i + 1}章`
        lines.push(`${H3}${title}`)
        if (cp.target_words) lines.push(`目标字数: ${cp.target_words}`)
        if (cp.pace) lines.push(`节奏: ${cp.pace}`)
        if (cp.hook_type) lines.push(`钩子类型: ${cp.hook_type}`)
        lines.push('')
      })
    }

    if (chapterOutlines.value.length) {
      lines.push(`${H2}章节大纲`)
      lines.push('')
      chapterOutlines.value.forEach((co: any, i: number) => {
        const title = co.title || co.chapter_title || `第${i + 1}章`
        lines.push(`${H3}${title}`)
        if (co.content) lines.push(co.content)
        else if (co.summary) lines.push(co.summary)
        if (co.beats) {
          const beats = Array.isArray(co.beats) ? co.beats : []
          beats.forEach((b: string) => {
            lines.push(isMD ? `- ${b}` : `  * ${b}`)
          })
        }
        lines.push('')
      })
    }
  }

  if (drafts.value.length && (scope.value === 'all' || scope.value === 'draft')) {
    if (lines.length) lines.push(HR)
    lines.push(`${H1}正文`)
    lines.push('')
    drafts.value.forEach((d: any, i: number) => {
      const title = d.title || d.chapter_title || d.name || `第${i + 1}章`
      lines.push(`${H2}${title}`)
      lines.push('')
      lines.push(d.content || d.content_raw || '')
      lines.push('')
    })
  }

  return lines.join('\n')
}

const contentWarning = computed(() => {
  if (scope.value === 'all' || scope.value === 'draft') {
    if (drafts.value.length > 0 && !drafts.value.some(d => !!(d.content || d.content_raw))) {
      return '草稿中包含空章节，导出文件可能不完整'
    }
  }
  return ''
})

const exportLoading = ref(false)

async function doExport() {
  if (exportLoading.value) return
  exportLoading.value = true
  try {
    const content = generateContent()
    if (!content.trim()) {
      toast.error('暂无可导出的内容')
      return
    }
    const ext = format.value
    const mimeType = format.value === 'md' ? 'text/markdown' : 'text/plain'
    const blob = new Blob([content], { type: mimeType + ';charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `novel_${props.projectId}.${ext}`
    a.click()
    URL.revokeObjectURL(url)
    toast.success(`已导出为 novel_${props.projectId}.${ext}`)
  } finally {
    exportLoading.value = false
  }
}

onMounted(async () => {
  try {
    if (props.projectId) await loadData()
  } catch (e: any) {
    loadError.value = e?.message || '加载作品数据失败'
  } finally {
    pageLoading.value = false
  }
})
</script>

<style scoped>
.export-view { max-width: 700px; }
.section { background: #fff; border-radius: 12px; padding: 28px; box-shadow: 0 2px 12px rgba(0,0,0,0.06); }
.section h3 { font-size: 22px; margin: 0 0 8px; }
.tip { color: #888; font-size: 14px; margin-bottom: 20px; }
.form-group { margin-bottom: 16px; }
.form-group label { display: block; font-weight: 600; margin-bottom: 6px; font-size: 14px; color: #555; }
.form-select { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 8px; font-size: 15px; }
.action-row { display: flex; gap: 12px; margin: 16px 0; }
.btn { border: none; border-radius: 8px; padding: 10px 20px; font-size: 15px; font-weight: 600; cursor: pointer; }
.btn-primary { background: linear-gradient(135deg, #667eea, #764ba2); color: #fff; }
.btn-ghost { background: #f0f0f0; color: #555; }
.content-warning { color: #f57c00; background: #fff8e1; border-radius: 8px; padding: 10px 16px; margin-bottom: 12px; font-size: 14px; }
.stats { display: flex; gap: 16px; margin: 16px 0; font-size: 13px; color: #888; }
.stats span { background: #f8f9fa; padding: 6px 12px; border-radius: 6px; }
.preview-box { margin-top: 20px; background: #f8f9fa; border-radius: 10px; padding: 20px; }
.preview-box h4 { font-size: 15px; margin-bottom: 12px; color: #333; }
.preview-box pre { white-space: pre-wrap; font-size: 13px; line-height: 1.6; max-height: 400px; overflow-y: auto; margin: 0; padding: 12px; background: #fff; border-radius: 8px; border: 1px solid #eee; }
.page-loading { display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 300px; gap: 16px; }
.loading-spinner { width: 36px; height: 36px; border: 3px solid #f0f0f0; border-top-color: #409eff; border-radius: 50%; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
</style>
