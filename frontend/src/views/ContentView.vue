<template>
  <div class="content-view">
    <div class="section">
      <h3>{{ title }}</h3>
      <p class="tip">{{ desc }}</p>

      <div class="form-group">
        <label>选择章节</label>
        <select v-model="form.chapterNo" class="form-select">
          <option v-for="i in 10" :key="i" :value="i">第 {{ i }} 章</option>
        </select>
      </div>

      <div class="form-group">
        <label>{{ contentLabel }}</label>
        <textarea v-model="form.content" rows="10" :placeholder="contentPlaceholder" class="form-textarea"></textarea>
      </div>

      <div class="action-row">
        <button @click="runModule" :disabled="loading" class="btn btn-primary">
          <span v-if="loading" class="spinner"></span>{{ loading ? '处理中...' : actionLabel }}
        </button>
        <button @click="$emit('complete', resultData)" class="btn btn-ghost">跳过</button>
      </div>

      <div v-if="error" class="error-box">
        <p>{{ error }}</p>
      </div>
    </div>

    <div v-if="result" class="section">
      <h3>处理结果</h3>
      <div class="result-box">
        <div v-if="typeof result === 'string'">
          <pre>{{ result }}</pre>
        </div>
        <div v-else-if="typeof result === 'object'" class="result-tree">
          <TreeNode v-for="(val, key) in topLevelKeys" :key="key" :node-key="String(key)" :node-value="(result as any)[key]" :depth="0" />
        </div>
      </div>
      <div v-if="moduleType === 'polish' && polishedContent" class="diff-box">
        <h4>对比视图</h4>
        <div class="diff-panels">
          <div class="diff-panel before">
            <div class="diff-label">原文</div>
            <pre>{{ form.content }}</pre>
          </div>
          <div class="diff-panel after">
            <div class="diff-label">润色后</div>
            <pre>{{ polishedContent }}</pre>
          </div>
        </div>
      </div>
      <div v-if="moduleType === 'knowledge_update' && knowledgeAdded.length" class="diff-box">
        <h4>知识库更新 (&times;{{ knowledgeAdded.length }})</h4>
        <ul class="knowledge-list">
          <li v-for="(item, i) in knowledgeAdded" :key="i">{{ item }}</li>
        </ul>
      </div>
      <button @click="$emit('complete', resultData)" class="btn btn-primary btn-complete">确认并通过</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive, onMounted } from 'vue'
import * as v2Api from '../api/v2'
import { useGeneration } from '../composables/useGeneration'
import TreeNode from '../components/TreeNode.vue'

const props = defineProps<{
  projectId: string
  moduleType: string
  title: string
  desc: string
  actionLabel: string
}>()
const emit = defineEmits<{ complete: [data: any] }>()
const moduleLabel = computed(() => {
  const map: Record<string, string> = {
    polish: '润色优化',
    content_parsing: '内容解析',
    knowledge_update: '知识库更新',
    consistency_check: '一致性检查',
  }
  return map[props.moduleType] || '内容处理'
})
const gen = useGeneration(props.moduleType, moduleLabel.value)

const form = reactive({ chapterNo: 1, content: '' })
const loading = ref(false)
const error = ref('')
const result = ref<any>(null)
const polishedContent = ref('')
const knowledgeAdded = ref<string[]>([])

const contentLabel = computed(() => {
  const map: Record<string, string> = {
    polish: '待润色内容',
    content_parsing: '待解析正文',
    knowledge_update: '正文内容（用于更新知识库）',
    consistency_check: '待检查正文',
  }
  return map[props.moduleType] || '正文内容'
})

const contentPlaceholder = computed(() => {
  if (props.moduleType === 'polish') return '粘贴需要润色的正文内容...'
  if (props.moduleType === 'content_parsing') return '粘贴需要解析的正文内容...'
  return '粘贴或输入正文内容...'
})

const flatResult = computed(() => {
  if (!result.value || typeof result.value === 'string') return {}
  const flat: Record<string, any> = {}
  for (const [k, v] of Object.entries(result.value)) {
    if (v !== null && v !== undefined && typeof v !== 'object') {
      flat[k] = String(v)
    } else if (Array.isArray(v) && v.length < 5) {
      flat[k] = String(v)
    }
  }
  return flat
})

const topLevelKeys = computed(() => {
  if (!result.value || typeof result.value !== 'object') return []
  return Object.keys(result.value)
})

const resultData = computed(() => ({
  moduleType: props.moduleType,
  chapterNo: form.chapterNo,
  content: form.content,
  result: result.value,
  polishedContent: polishedContent.value,
  knowledgeAdded: knowledgeAdded.value,
}))

async function runModule() {
  loading.value = true
  gen.begin()
  error.value = ''
  result.value = null
  polishedContent.value = ''
  knowledgeAdded.value = []

  try {
    const pid = props.projectId
    const chapterNo = String(form.chapterNo)
    const content = form.content

    switch (props.moduleType) {
      case 'polish': {
        const res = await v2Api.polishContent(pid, content, '整体优化')
        result.value = res
        polishedContent.value = (res as any).polished_content || (res as any).polishedContent || content
        break
      }
      case 'content_parsing': {
        const allData = await v2Api.getAllModuleData(props.projectId).catch(() => null)
        const chars = allData?.modules?.['characters']
        const characters = Array.isArray(chars) ? chars : (chars ? [
          chars.protagonist, ...(chars.supporting || []), ...(chars.villains || []),
        ].filter(Boolean) : undefined)
        const res = await v2Api.parseContent(pid, chapterNo, content, characters)
        result.value = res
        break
      }
      case 'knowledge_update': {
        const parseRes = await v2Api.parseContent(pid, chapterNo, content).catch(() => ({}))
        const res = await v2Api.updateKnowledge(pid, chapterNo, parseRes)
        result.value = { updated: (res as any).updated, count: (res as any).count || 0 }
        knowledgeAdded.value = (res as any).added || []
        break
      }
      case 'consistency_check': {
        const allData = await v2Api.getAllModuleData(props.projectId).catch(() => null)
        const modules = allData?.modules || {}
        const knowledgeState = modules['consistency_check'] || null
        const chars = modules['characters']
        const characters = Array.isArray(chars) ? chars : (chars ? [
          chars.protagonist,
          ...(chars.supporting || []),
          ...(chars.villains || []),
        ].filter(Boolean) : undefined)
        const worldData = modules['world'] || undefined
        const powerSystem = modules['power_system'] || undefined
        const res = await v2Api.checkConsistency(pid, chapterNo, content, knowledgeState, characters, worldData, powerSystem)
        result.value = res
        break
      }
      default:
        result.value = `已保存${props.moduleType}数据`
    }
  } catch (e: any) {
    error.value = e.message || 'AI生成器未配置或处理失败'
    result.value = null
  } finally {
    loading.value = false
    if (!error.value) gen.end()
    else gen.fail(error.value)
  }
}

onMounted(async () => {
  try {
    const saved = await v2Api.getModuleData(props.projectId, props.moduleType)
    if (saved?.data && (saved.data.chapterNo || saved.data.content || saved.data.result)) {
      const d = saved.data
      if (d.chapterNo) form.chapterNo = d.chapterNo
      if (d.content) form.content = d.content
      if (d.result) result.value = d.result
      if (d.polishedContent) polishedContent.value = d.polishedContent
      return
    }
  } catch (_e) { /* ignore */ }
  try {
    const allData = await v2Api.getAllModuleData(props.projectId)
    const drafts = allData?.modules?.['draft_generation']
    const draftArr = Array.isArray(drafts) ? drafts : []
    const firstDraft = draftArr.find((d: any) => String(d.chapter_no) === String(form.chapterNo)) || draftArr[0]
    if (firstDraft) {
      if (firstDraft.content_raw && !form.content) {
        form.content = firstDraft.content_raw
      }
      if (firstDraft.chapter_no && !form.chapterNo) {
        form.chapterNo = firstDraft.chapter_no
      }
    }
  } catch (_e) { /* ignore */ }
})
</script>

<style scoped>
.content-view { max-width: 900px; }
.section { background: #fff; border-radius: 16px; padding: 28px; margin-bottom: 20px; box-shadow: 0 4px 16px rgba(0,0,0,.06); }
.section h3 { font-size: 22px; margin-bottom: 10px; }
.section h4 { font-size: 16px; margin: 16px 0 8px; color: #555; }
.tip { color: #888; margin-bottom: 20px; font-size: 16px; }
.form-group { margin-bottom: 18px; }
.form-group label { display: block; font-weight: 600; margin-bottom: 8px; font-size: 16px; color: #555; }
.form-select, .form-textarea { width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 10px; font-size: 16px; resize: vertical; font-family: inherit; }
.form-textarea { min-height: 200px; }
.action-row { display: flex; gap: 12px; margin-top: 20px; }
.btn { border: none; border-radius: 10px; padding: 12px 24px; font-size: 16px; font-weight: 600; cursor: pointer; }
.btn-primary { background: linear-gradient(135deg, var(--primary), var(--primary-light)); color: #fff; }
.btn-ghost { background: #f0f0f0; color: #555; }
.btn-complete { margin-top: 20px; }
.error-box { margin-top: 16px; padding: 16px; background: #fff3f3; border: 1px solid #ffcdd2; border-radius: 10px; }
.error-box p { color: #c62828; }
.result-box { background: #f8f9fa; border-radius: 10px; padding: 20px; max-height: 500px; overflow-y: auto; }
.result-box pre { white-space: pre-wrap; font-size: 15px; line-height: 1.6; }
.result-tree { font-family: inherit; }
.diff-box { margin-top: 20px; }
.diff-box h4 { font-size: 16px; margin-bottom: 12px; color: #333; }
.diff-panels { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.diff-panel { border-radius: 10px; padding: 16px; max-height: 400px; overflow-y: auto; }
.diff-panel.before { background: #fff5f5; border: 1px solid #ffcdd2; }
.diff-panel.after { background: #f0fff4; border: 1px solid #c6f6d5; }
.diff-label { font-weight: 600; margin-bottom: 8px; font-size: 14px; }
.diff-panel.before .diff-label { color: #c62828; }
.diff-panel.after .diff-label { color: #2e7d32; }
.diff-panel pre { white-space: pre-wrap; font-size: 14px; line-height: 1.6; margin: 0; }
.knowledge-list { list-style: none; padding: 0; margin: 0; }
.knowledge-list li { padding: 8px 12px; margin-bottom: 6px; background: #f0f7ff; border-left: 3px solid var(--primary); border-radius: 6px; font-size: 14px; }
.result-item { padding: 6px 0; font-size: 15px; }
.result-key { font-weight: 600; color: var(--primary); }
.polished-output { margin-top: 16px; background: #f0fff4; border: 1px solid #c6f6d5; border-radius: 10px; padding: 20px; }
.spinner { display: inline-block; width: 14px; height: 14px; border: 2px solid #fff; border-top-color: transparent; border-radius: 50%; animation: spin 0.8s linear infinite; margin-right: 6px; }
@keyframes spin { to { transform: rotate(360deg); } }
</style>
