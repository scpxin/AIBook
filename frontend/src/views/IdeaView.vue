<template>
  <div v-if="pageLoading" class="page-loading">
    <div class="loading-spinner"></div>
    <p>加载灵感模块...</p>
  </div>
  <div v-else class="idea-view">
    <div class="section input-section">
      <h3>灵感输入</h3>
      <textarea v-model="form.prompt" placeholder="用一句话描述你的故事创意，例如：一个废柴少年意外获得上古传承，踏上逆天之路..." class="idea-textarea" maxlength="2000" />
      <div class="form-row">
        <select v-model="form.genre" class="form-select">
          <option value="">选择类型倾向</option>
          <option v-for="g in genres" :key="g" :value="g">{{ g }}</option>
        </select>
        <input v-model="form.reference" placeholder="参考作品(可选)" class="form-input" />
        <button @click="generate" :disabled="generating || !form.prompt" class="btn-primary">
          <span v-if="generating" class="spinner"></span>{{ generating ? '生成中...' : '生成创意' }}
        </button>
        <button @click="manualConfirm" :disabled="!form.prompt" class="btn-manual">直接使用</button>
        <button class="btn-save-tpl" :disabled="form.prompt.trim().length < 5" @click="showSaveDialog = true" aria-label="存为模板"><span aria-hidden="true">💾</span> 存为模板</button>
        <button v-if="!showTemplatePanel" class="btn-manage" @click="showTemplatePanel = true" aria-label="展开模板面板"><span aria-hidden="true">▲</span> 展开模板</button>
      </div>
    </div>

    <div v-if="showTemplatePanel" class="section quick-section">
      <div class="quick-header">
        <h3>快速开始</h3>
        <div class="quick-header-actions">
          <button class="btn-manage" @click="showTemplatePanel = false" aria-label="收起模板面板"><span aria-hidden="true">▼</span> 收起</button>
          <button class="btn-manage" @click="showManage = true" aria-label="模板管理"><span aria-hidden="true">📋</span> 模板管理</button>
        </div>
      </div>
      <p class="tip">不想等待AI生成？选择一个模板或手动输入你的故事创意</p>
      <div class="genre-filter-bar">
        <button class="genre-chip" :class="{ active: genreFilter === null }" @click="genreFilter = null">全部</button>
        <button v-for="g in availableGenres" :key="g" class="genre-chip" :class="{ active: genreFilter === g }" @click="genreFilter = g">{{ g }}</button>
      </div>
      <div v-if="!filteredTemplates.length && genreFilter" class="empty-category">该分类下暂无模板</div>
      <div class="quick-grid">
        <div v-for="tpl in filteredTemplates" :key="tpl.id" class="quick-card" tabindex="0" @click="useTemplate(tpl)" @keydown.enter="useTemplate(tpl)">
          <div class="quick-icon">{{ tpl.icon }}</div>
          <div class="quick-label">{{ tpl.name }}</div>
          <div class="quick-desc">{{ tpl.prompt.slice(0, 40) }}...</div>
        </div>
      </div>
    </div>

    <div v-if="generating" class="section">
      <div class="skeleton skeleton-card"></div>
      <div class="skeleton skeleton-card"></div>
      <div class="skeleton skeleton-card"></div>
    </div>

    <div v-if="candidates.length" class="section candidates-section">
      <h3 @click="candidatesCollapsed = !candidatesCollapsed" style="cursor:pointer;user-select:none">
        <span class="collapse-icon">{{ candidatesCollapsed ? '▶' : '▼' }}</span>
        候选创意 ({{ candidates.length }})
      </h3>
      <div v-show="!candidatesCollapsed" class="candidate-grid">
        <div v-for="(c, idx) in candidates" :key="idx" class="candidate-card" :class="{ selected: selectedIdx === idx }" tabindex="0" @click="selectedIdx = idx" @keydown.enter="selectedIdx = idx">
          <div class="candidate-title">{{ c.title }}</div>
          <div class="candidate-meta">
            <span class="score">评分: {{ c.score }}</span>
            <span class="genre">{{ c.genre }}</span>
          </div>
          <div class="candidate-desc">{{ c.description }}</div>
          <div v-if="c.tags?.length" class="candidate-tags">
            <span v-for="t in c.tags" :key="t" class="tag">{{ t }}</span>
          </div>
        </div>
      </div>
    </div>

    <div v-if="selectedIdx !== null && upgrades.length" class="section upgrade-section">
      <h3>创意升级方案</h3>
      <div class="upgrade-list">
        <div v-for="(u, idx) in upgrades" :key="idx" class="upgrade-card">
          <div class="upgrade-header">
            <span class="upgrade-type">{{ u.type }}</span>
            <span class="upgrade-score">+{{ u.scoreBoost }}</span>
          </div>
          <p class="upgrade-desc">{{ u.description }}</p>
        </div>
      </div>
    </div>

    <div v-if="selectedIdx !== null && riskAnalysisLoading" class="section risk-section">
      <h3>风险分析</h3>
      <p class="risk-loading">正在分析...</p>
    </div>

    <div v-if="selectedIdx !== null && !riskAnalysisLoading && riskAnalysis" class="section risk-section">
      <h3>风险分析</h3>
      <div class="risk-list">
        <div v-for="(r, idx) in riskAnalysis.risks" :key="idx" class="risk-item">
          <span class="risk-level" :class="r.level">{{ r.level }}</span>
          <span class="risk-text">{{ r.description }}</span>
        </div>
      </div>
      <div class="risk-mitigations">
        <div v-for="(m, idx) in riskAnalysis.mitigations" :key="idx" class="mitigation-item">{{ m }}</div>
      </div>
    </div>

    <div v-if="selectedIdx !== null && !riskAnalysisLoading && !riskAnalysis" class="section risk-section">
      <p class="risk-notice">风险分析暂不可用,您仍可继续</p>
    </div>

    <div v-if="selectedIdx !== null" class="section confirm-section">
      <button @click="confirmAndStay" class="btn-confirm btn-confirm-stay" :disabled="confirming || selectedIdx === null">确认创意</button>
      <button @click="confirm" class="btn-confirm btn-confirm-next" :disabled="confirming || selectedIdx === null">确认并进入下一步 →</button>
    </div>

    <div v-if="error" class="error-msg">{{ error }}</div>

    <TemplateDialog
      v-if="showSaveDialog"
      :project-id="projectId"
      :preset-name="form.reference || ''"
      :preset-genre="form.genre"
      :preset-prompt="form.prompt"
      :preset-reference="form.reference"
      @close="showSaveDialog = false"
      @saved="onTemplateSaved"
    />
    <TemplateManagePanel
      v-if="showManage"
      :project-id="projectId"
      @close="showManage = false"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, watch, onMounted, nextTick, computed } from 'vue'
import { useIdeaStore } from '../stores/idea'
import * as v2Api from '../api/v2'
import { getTemplates } from '../api/v2'
import { useGeneration } from '../composables/useGeneration'
import { setupConfirm } from '../composables/useConfirm'
import { setupErrorBar } from '../composables/useErrorBar'
import { useToastStore } from '../stores/toast'
import TemplateDialog from '../components/TemplateDialog.vue'
import TemplateManagePanel from '../components/TemplateManagePanel.vue'
import type { IdeaTemplate } from '../types/v2'

const confirmDialog = setupConfirm()
const errorBar = setupErrorBar()
const toast = useToastStore()

const props = defineProps<{ projectId: string }>()
const emit = defineEmits<{ complete: [data: any] }>()

const ideaStore = useIdeaStore()
const gen = useGeneration('idea', '灵感创意')
const genres = ['玄幻', '都市', '科幻', '言情', '悬疑', '历史', '游戏', '轻小说']

const form = reactive({ prompt: '', genre: '', reference: '' })
const generating = ref(false)
const candidates = ref<any[]>([])
const selectedIdx = ref<number | null>(null)
const upgrades = ref<any[]>([])
const riskAnalysis = ref<any>(null)
const riskAnalysisLoading = ref(false)
const error = ref('')

const confirming = ref(false)
const showSaveDialog = ref(false)
const showManage = ref(false)
const showTemplatePanel = ref(true)
const selectingIdx = ref<number | null>(null)
const templates = ref<IdeaTemplate[]>([])
const genreFilter = ref<string | null>(null)

const availableGenres = computed(() => {
  const set = new Set(templates.value.map((t: IdeaTemplate) => t.genre))
  return Array.from(set).sort()
})
const filteredTemplates = computed(() => {
  if (!genreFilter.value) return templates.value
  return templates.value.filter((t: IdeaTemplate) => t.genre === genreFilter.value)
})

async function manualConfirm() {
  if (!form.prompt.trim()) return
  if (form.prompt.trim().length < 5) {
    errorBar.show('请输入至少5个字的创意描述')
    return
  }
  const ok = await confirmDialog.confirm({
    message: '确定直接使用当前创意进入下一步？',
    detail: '跳过AI生成直接使用手动输入的创意',
    type: 'warning',
  })
  if (!ok) return
  const manualIdea = {
    title: form.prompt.slice(0, 30),
    description: form.prompt,
    genre: form.genre || '自定义',
    score: 85,
    tags: [form.genre || '自定义'],
    isManual: true,
  }
  await v2Api.confirmIdea(props.projectId, 'manual', 1)
  const fullState = {
    prompt: form.prompt,
    genre: form.genre,
    reference: form.reference,
    candidates: [manualIdea],
    selectedIdx: 0,
    upgrades: [],
    riskAnalysis: null,
    confirmedCandidate: manualIdea,
  }
  try { await v2Api.saveModuleData(props.projectId, 'idea', fullState) } catch (_e) {
    toast.error('保存灵感数据失败，请手动备份')
  }
  emit('complete', fullState)
}

async function generate() {
  if (form.prompt.trim().length < 5) {
    errorBar.show('请输入至少5个字的创意描述')
    return
  }
  generating.value = true
  error.value = ''
  gen.begin()
  try {
    await ideaStore.generateIdeas(props.projectId, form.prompt, form.genre)
    candidates.value = ideaStore.ideas as any[] || []
    selectedIdx.value = null
    upgrades.value = []
    riskAnalysis.value = null
    riskAnalysisLoading.value = false
  } catch (e: any) {
    errorBar.showError(e, () => generate())
    gen.fail(e?.message || '生成失败')
  } finally {
    generating.value = false
    if (!error.value) gen.end()
  }
}

async function onSelectCandidate(idx: number) {
  selectedIdx.value = idx
  selectingIdx.value = idx
  try {
    const candidate = candidates.value[idx]
    await ideaStore.upgradeIdea(candidate)
    upgrades.value = ideaStore.upgradeVersions as any[] || []
    riskAnalysisLoading.value = true
    try {
      riskAnalysis.value = await v2Api.analyzeIdeaRisks(props.projectId, candidate.title || candidate.description || '')
    } catch (_e) {
      riskAnalysis.value = null
    } finally {
      riskAnalysisLoading.value = false
    }
  } catch (e: any) {
    error.value = e?.message || '升级失败'
  } finally {
    selectingIdx.value = null
  }
}

async function confirmAndStay() {
  if (confirming.value) return
  if (selectedIdx.value === null) return
  const candidate = candidates.value[selectedIdx.value]
  if (!candidate) {
    errorBar.show('候选创意数据异常，请重新生成')
    return
  }
  confirming.value = true
  try {
    await v2Api.confirmIdea(props.projectId, candidate.id, candidate.version)
    const fullState = {
      prompt: form.prompt,
      genre: form.genre,
      reference: form.reference,
      candidates: candidates.value,
      selectedIdx: selectedIdx.value,
      upgrades: upgrades.value,
      riskAnalysis: riskAnalysis.value,
      confirmedCandidate: candidate,
    }
    try {
      await v2Api.saveModuleData(props.projectId, 'idea', fullState)
      toast.success('创意已确认并保存')
    } catch (_e) {
      toast.error('保存灵感数据失败，请重试')
      return
    }
  } catch (e: any) {
    errorBar.showError(e, () => confirmAndStay())
  } finally {
    confirming.value = false
  }
}

async function confirm() {
  if (confirming.value) return
  if (selectedIdx.value === null) return
  const candidate = candidates.value[selectedIdx.value]
  if (!candidate) {
    errorBar.show('候选创意数据异常，请重新生成')
    return
  }
  confirming.value = true
  try {
    await v2Api.confirmIdea(props.projectId, candidate.id, candidate.version)
    const fullState = {
      prompt: form.prompt,
      genre: form.genre,
      reference: form.reference,
      candidates: candidates.value,
      selectedIdx: selectedIdx.value,
      upgrades: upgrades.value,
      riskAnalysis: riskAnalysis.value,
      confirmedCandidate: candidate,
    }
    try {
      await v2Api.saveModuleData(props.projectId, 'idea', fullState)
    } catch (_e) {
      toast.error('保存灵感数据失败，请重试')
      return
    }
    emit('complete', fullState)
  } catch (e: any) {
    errorBar.showError(e, () => confirm())
  } finally {
    confirming.value = false
  }
}

async function loadTemplates() {
  try {
    const res = await getTemplates(props.projectId)
    templates.value = res.templates
  } catch (_e) {
    console.error('[IdeaView] loadTemplates failed:', _e)
    toast.error('加载模板列表失败，请检查网络')
  }
}

function onTemplateSaved(saved: IdeaTemplate) {
  templates.value = templates.value.filter((t: IdeaTemplate) => t.id !== saved.id)
  templates.value.unshift(saved)
}

async function useTemplate(tpl: IdeaTemplate) {
   form.prompt = tpl.prompt
   form.genre = tpl.genre
   form.reference = tpl.reference || ''
   await nextTick()
   // 模板直接应用，不触发AI生成
   const templateIdea = {
     title: tpl.prompt.slice(0, 30),
     description: tpl.prompt,
     genre: tpl.genre || '自定义',
     score: 85,
     tags: [tpl.genre || '自定义'],
     isTemplate: true,
     templateId: tpl.id,
   }
   const fullState = {
     prompt: form.prompt,
     genre: form.genre,
     reference: form.reference,
     candidates: [templateIdea],
     selectedIdx: 0,
     upgrades: [],
     riskAnalysis: null,
     confirmedCandidate: templateIdea,
   }
   try { await v2Api.saveModuleData(props.projectId, 'idea', fullState) } catch (_e) {
     toast.error('保存灵感数据失败，请手动备份')
   }
   emit('complete', fullState)
 }

const skipWatch = ref(false)
const candidatesCollapsed = ref(false)
let candidateDebounceTimer: ReturnType<typeof setTimeout> | null = null

watch(() => form.prompt, (val) => {
  showTemplatePanel.value = (val as string).trim().length < 2
})

watch(selectedIdx, (val) => {
  if (skipWatch.value || val === null) return
  if (candidateDebounceTimer) clearTimeout(candidateDebounceTimer)
  candidateDebounceTimer = setTimeout(() => onSelectCandidate(val), 250)
})

const pageLoading = ref(true)

onMounted(async () => {
  try {
    const saved = await v2Api.getModuleData(props.projectId, 'idea')
    if (saved?.data && Object.keys(saved.data).length > 0) {
      const d = saved.data
      skipWatch.value = true
      if (d.candidates) {
        candidates.value = d.candidates
        selectedIdx.value = d.selectedIdx ?? null
        upgrades.value = d.upgrades || []
        riskAnalysis.value = d.riskAnalysis || null
      } else if (d.confirmedCandidate) {
        candidates.value = [d.confirmedCandidate]
        selectedIdx.value = 0
      } else if (d.title || d.prompt || d.genre) {
        candidates.value = [{
          title: d.title || d.prompt || '',
          genre: d.genre || d.genreHint || '',
          target_audience: d.target_audience || '',
          writing_style: d.writing_style || '',
          tone: d.tone || d.style || '',
          summary: d.summary || '',
          isManual: true,
        }]
        selectedIdx.value = 0
      }
      await nextTick()
      skipWatch.value = false
      if (selectedIdx.value !== null) {
        await onSelectCandidate(selectedIdx.value)
      }
      if (d.prompt || d.title) form.prompt = d.prompt || d.title || ''
      if (d.genre) form.genre = d.genre || ''
      if (d.reference) form.reference = d.reference || ''
    }
  } catch (_e) {
    console.error('[IdeaView] restore saved data failed:', _e)
  }
  finally { pageLoading.value = false }
  loadTemplates()
})
</script>

<style scoped>
.idea-view { max-width: 1170px; margin: 0 auto; }
.section { background: #fff; border: 1px solid #eee; border-radius: 10px; padding: 26px; margin-bottom: 21px; }
.section h3 { margin: 0 0 12px; font-size: 21px; }
.idea-textarea { width: 100%; height: 104px; padding: 13px; border: 1px solid #ddd; border-radius: 5px; resize: vertical; font-size: 18px; }
.form-row { display: flex; gap: 10px; margin-top: 13px; align-items: center; }
.form-select, .form-input { padding: 10px 10px; border: 1px solid #ddd; border-radius: 5px; font-size: 17px; }
.form-input { flex: 1; }
.btn-primary { padding: 10px 20px; background: var(--primary); color: #fff; border: none; border-radius: 5px; cursor: pointer; white-space: nowrap; }
.spinner { display: inline-block; width: 14px; height: 14px; border: 2px solid #fff; border-top-color: transparent; border-radius: 50%; animation: spin 0.8s linear infinite; margin-right: 6px; }
@keyframes spin { to { transform: rotate(360deg); } }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-manual { padding: 10px 20px; background: #52c41a; color: #fff; border: none; border-radius: 5px; cursor: pointer; white-space: nowrap; font-size: 16px; }
.btn-manual:disabled { opacity: 0.5; cursor: not-allowed; }
.quick-section { background: #f8fafc; }
.quick-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 12px; margin-top: 16px; }
.quick-card { border: 2px solid #e8e8e8; border-radius: 10px; padding: 18px; cursor: pointer; transition: 0.15s; text-align: center; }
.quick-card:hover { border-color: var(--primary); background: #f0f8ff; transform: translateY(-2px); }
.quick-icon { font-size: 28px; margin-bottom: 8px; }
.quick-label { font-weight: 600; font-size: 17px; margin-bottom: 4px; }
.quick-desc { font-size: 14px; color: #999; }
.candidate-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 16px; }
.candidate-card { border: 1px solid #eee; border-radius: 8px; padding: 18px; cursor: pointer; transition: 0.2s; }
.candidate-card:hover { border-color: var(--primary); box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
.candidate-card.selected { border-color: var(--primary); background: #f0f8ff; }
.candidate-title { font-weight: 600; margin-bottom: 8px; }
.candidate-meta { display: flex; gap: 16px; font-size: 16px; color: #888; margin-bottom: 8px; }
.candidate-desc { font-size: 17px; color: #555; line-height: 1.5; }
.candidate-tags { display: flex; flex-wrap: wrap; gap: 5px; margin-top: 10px; }
.tag { font-size: 14px; padding: 3px 6px; background: #f0f0f0; border-radius: 4px; color: #666; }
.upgrade-list { display: flex; flex-direction: column; gap: 10px; }
.upgrade-card { border: 1px solid #eee; border-radius: 8px; padding: 16px; }
.upgrade-header { display: flex; justify-content: space-between; margin-bottom: 5px; }
.upgrade-type { font-weight: 600; font-size: 18px; }
.upgrade-score { color: #52c41a; font-weight: 600; }
.upgrade-desc { font-size: 17px; color: #555; margin: 0; }
.risk-list { display: flex; flex-direction: column; gap: 8px; }
.risk-item { display: flex; align-items: center; gap: 10px; font-size: 17px; }
.risk-level { padding: 3px 6px; border-radius: 4px; font-size: 14px; font-weight: 600; }
.risk-level.high { background: #fff1f0; color: #ff4d4f; }
.risk-level.medium { background: #fffbe6; color: #fa8c16; }
.risk-level.low { background: #f6ffed; color: #52c41a; }
.risk-text { color: #555; }
.risk-mitigations { margin-top: 16px; }
.mitigation-item { font-size: 16px; color: #666; padding: 4px 0; }
.risk-loading { color: #888; font-size: 16px; }
.btn-confirm { margin-top: 21px; width: 100%; padding: 13px; background: #52c41a; color: #fff; border: none; border-radius: 8px; font-size: 20px; cursor: pointer; }
.btn-confirm-stay { background: #1890ff; margin-bottom: 8px; }
.btn-confirm-stay:hover { background: #40a9ff; }
.btn-confirm-next { background: #52c41a; font-size: 16px; padding: 10px; }
.quick-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px; }
.quick-header h3 { margin: 0; }
.btn-manage { padding: 6px 12px; border: 1px solid #ddd; border-radius: 6px; background: #fff; cursor: pointer; font-size: 14px; }
.btn-manage:hover { background: #f5f5f5; }
.genre-filter-bar { display: flex; gap: 6px; margin: 10px 0; flex-wrap: wrap; }
.genre-chip { padding: 4px 10px; border-radius: 14px; border: 1px solid #ddd; background: #fff; cursor: pointer; font-size: 13px; }
.genre-chip.active { background: var(--primary); color: #fff; border-color: var(--primary); }
.btn-save-tpl { padding: 10px 16px; background: #faad14; color: #fff; border: none; border-radius: 5px; cursor: pointer; white-space: nowrap; font-size: 16px; }
.btn-save-tpl:disabled { opacity: 0.5; cursor: not-allowed; }
.error-msg { color: #ff4d4f; padding: 16px; text-align: center; }
.collapse-icon { display: inline-block; width: 12px; font-size: 12px; margin-right: 4px; transition: transform 0.2s; }
.page-loading { display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 300px; gap: 16px; color: #666; }
.loading-spinner { width: 36px; height: 36px; border: 3px solid #f0f0f0; border-top-color: #409eff; border-radius: 50%; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
</style>
