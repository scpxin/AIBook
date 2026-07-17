<template>
  <div class="world-view">
    <div v-if="pageLoading" class="page-loading">
      <div class="loading-spinner"></div>
      <p>加载中...</p>
    </div>
    <div v-else">
    <div v-if="!ideaText && !pageLoading" class="upstream-missing-hint">
      尚未完成灵感生成，建议先完成"灵感"和"项目定位"模块以获得更好的世界观生成效果
    </div>
    <div class="auto-save-status">
      <span v-if="saveState === 'saving'" class="saving">保存中...</span>
      <span v-else-if="saveState === 'saved'" class="saved">已自动保存</span>
      <span v-else-if="saveState === 'error'" class="error">保存失败</span>
    </div>
    <div class="accordion">
      <div v-for="tab in tabs" :key="tab.key" class="accordion-item">
        <div class="accordion-header" role="button" :tabindex="0" :aria-expanded="activeTab === tab.key" :aria-controls="`panel-${tab.key}`" @click="toggleTab(tab.key)" @keydown.enter.prevent="toggleTab(tab.key)" @keydown.space.prevent="toggleTab(tab.key)">
          <span class="accordion-icon">{{ activeTab === tab.key ? '▼' : '▶' }}</span>
          <span>{{ tab.label }}</span>
        </div>
        <div v-if="activeTab === tab.key" class="accordion-body">
          <div v-if="tab.key === 'origin'" class="tab-pane">
            <h3>世界本源</h3>
            <div class="form-group">
              <label>世界类型</label>
              <select v-model="world.origin.worldType" class="form-select">
                <option value="" disabled>请选择世界类型</option>
                <option>低魔世界</option><option>中魔世界</option><option>高魔世界</option>
                <option>科幻宇宙</option><option>末日废土</option><option>现实平行</option>
              </select>
            </div>
            <div class="form-group">
              <label>起源故事</label>
              <textarea v-model="world.origin.originStory" class="form-textarea" rows="4" placeholder="世界的起源..." maxlength="5000" />
              <span class="char-count">{{ world.origin.originStory.length }}/5000</span>
            </div>
            <div class="form-group">
              <label>隐藏真相</label>
              <textarea v-model="world.origin.hiddenTruth" class="form-textarea" rows="3" placeholder="世界背后隐藏的秘密..." maxlength="5000" />
              <span class="char-count">{{ world.origin.hiddenTruth.length }}/5000</span>
            </div>
          </div>

          <div v-else-if="tab.key === 'rules'" class="tab-pane">
            <h3>世界规则 (6要素)</h3>
            <div class="rules-grid">
              <div v-for="rule in worldRules" :key="rule.key" class="rule-card">
                <div class="rule-name">{{ rule.name }}</div>
                <textarea v-model="world.rules[rule.key]" class="form-textarea" rows="2" :placeholder="rule.placeholder" maxlength="5000" />
                <span class="char-count">{{ (world.rules[rule.key] || '').length }}/5000</span>
              </div>
            </div>
          </div>

          <div v-else-if="tab.key === 'structure'" class="tab-pane">
            <h3>世界层级结构</h3>
            <WorldMapTree :structure="world.structure" />
          </div>

          <div v-else-if="tab.key === 'civilization'" class="tab-pane">
            <h3>文明体系 (8维度)</h3>
            <div class="civ-grid">
              <div v-for="dim in civDimensions" :key="dim.key" class="civ-card">
                <div class="civ-name">{{ dim.name }}</div>
                <textarea v-model="world.civilization[dim.key]" class="form-textarea" rows="2" maxlength="5000" />
                <span class="char-count">{{ (world.civilization[dim.key] || '').length }}/5000</span>
              </div>
            </div>
          </div>

          <div v-else-if="tab.key === 'history'" class="tab-pane">
            <h3>历史时间线</h3>
            <TimelineChart :events="world.history" />
          </div>
        </div>
      </div>
    </div>

     <div class="actions">
       <button @click="generate" :disabled="generating" class="btn-primary"><span v-if="generating" class="spinner"></span>{{ generating ? '生成中...' : 'AI生成世界观' }}</button>
       <button @click="checkConsistency" class="btn-secondary">一致性检查</button>
       <button @click="confirm" class="btn-primary" :disabled="confirming">{{ confirming ? '保存中...' : '确认设定，下一步' }}</button>
     </div>
    <div v-if="error" class="error-box">{{ error }}</div>
    <div v-if="loadError" class="load-error-box"><p>{{ loadError }}</p><button @click="reloadPage" class="btn-secondary">重试</button></div>
    <div v-if="checkResult" class="check-result">
      <span :class="checkResult.passed ? 'pass' : 'fail'">{{ checkResult.message }}</span>
    </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch } from 'vue'
import { useWorldStore } from '../stores/world'
import * as v2Api from '../api/v2'
import WorldMapTree from '../components/WorldMapTree.vue'
import TimelineChart from '../components/TimelineChart.vue'
import { useGeneration } from '../composables/useGeneration'
import { setupConfirm } from '../composables/useConfirm'
import { useAutoSave } from '../composables/useAutoSave'
import { useToastStore } from '../stores/toast'
import { setupErrorBar } from '../composables/useErrorBar'

const props = defineProps<{ projectId: string }>()
const emit = defineEmits<{ complete: [data: any] }>()
const confirmDialog = setupConfirm()
const errorBar = setupErrorBar()
const toast = useToastStore()
const pageLoading = ref(true)

const worldStore = useWorldStore()
const gen = useGeneration('world', '世界观')
const tabs = [
  { key: 'origin', label: '本源' },
  { key: 'rules', label: '规则' },
  { key: 'structure', label: '结构' },
  { key: 'civilization', label: '文明' },
  { key: 'history', label: '历史' },
]
const activeTab = ref('origin')

function toggleTab(key: string) {
  activeTab.value = activeTab.value === key ? '' : key
}
const generating = ref(false)
const confirming = ref(false)
const error = ref('')
const loadError = ref('')
const checkResult = ref<any>(null)

function reloadPage() { window.location.reload() }

const world = reactive<any>({
  origin: { worldType: '', originStory: '', hiddenTruth: '' },
  rules: {},
  structure: {},
  civilization: {},
  history: [],
})

const worldRules = [
  { key: 'power', name: '力量体系', placeholder: '修炼/异能的核心规则...' },
  { key: 'economy', name: '经济系统', placeholder: '货币、资源、交易规则...' },
  { key: 'politics', name: '政治结构', placeholder: '国家、势力、权力分配...' },
  { key: 'technology', name: '科技水平', placeholder: '科技树限制、核心原理...' },
  { key: 'culture', name: '文化习俗', placeholder: '节日、禁忌、礼仪...' },
  { key: 'taboo', name: '禁忌规则', placeholder: '世界底层限制、因果律...' },
]

const civDimensions = [
  { key: 'government', name: '政体' }, { key: 'religion', name: '信仰' },
  { key: 'military', name: '军事' }, { key: 'education', name: '教育' },
  { key: 'art', name: '艺术' }, { key: 'trade', name: '贸易' },
  { key: 'law', name: '法律' }, { key: 'class', name: '阶级' },
]

const ideaText = ref('')
const ideaGenre = ref('')
const projectPlatform = ref('')
const projectSubGenre = ref('')
const projectTone = ref('')

function enrichedIdeaContext(): string {
  const parts = [ideaText.value]
  const ctx: string[] = []
  if (ideaGenre.value) ctx.push(`题材: ${ideaGenre.value}`)
  if (projectPlatform.value) ctx.push(`目标平台: ${projectPlatform.value}`)
  if (projectSubGenre.value) ctx.push(`小说体裁: ${projectSubGenre.value}`)
  if (projectTone.value) ctx.push(`文风基调: ${projectTone.value}`)
  if (ctx.length > 0) {
    parts.push(`\n项目上下文:\n${ctx.join('\n')}`)
  }
  return parts.join('\n')
}

async function generate() {
  generating.value = true
  error.value = ''
  let generationSuccess = false
  gen.begin(5, '正在生成世界本源...')
  try {
    const result = await worldStore.generateWorld(
      props.projectId, world.origin, enrichedIdeaContext(), ideaGenre.value,
      (step, msg) => gen.progress(step, msg)
    )
    Object.assign(world, result)
    generationSuccess = true
    try {
      await v2Api.saveModuleData(props.projectId, 'world', { ...world })
    } catch (_e) {
      toast.error('世界观已生成但保存失败。数据暂存内存中，请检查网络后重试')
      gen.fail('保存失败')
      return
    }
  } catch (e: any) {
    errorBar.showError(e, () => generate())
  } finally {
    generating.value = false
    if (generationSuccess) gen.end()
    else gen.fail(error.value || '生成失败')
  }
}

async function checkConsistency() {
  error.value = ''  // 清除之前的错误
  try {
    const result = await v2Api.worldConsistencyCheck(props.projectId)
    checkResult.value = result
    if (result.passed) {
      toast.success(`一致性检查通过 (${result.score || 100}分)`)
    } else {
      toast.warning(`发现 ${result.issues?.length || 0} 个不一致问题`)
    }
  } catch (e: any) {
    error.value = '一致性检查失败: ' + (e?.message || '未知错误')
  }
}

async function confirm() {
  if (confirming.value) return
  cancel()
  const ok = await confirmDialog.confirm({
    message: '确定进入下一步？',
    detail: '确认后将保存当前世界观设定并进入下一模块',
    type: 'info',
  })
  if (!ok) return
  confirming.value = true
  try {
    await worldStore.updateLocalWorld(props.projectId, world)
    toast.success('世界观已保存')
    emit('complete', world)
  } catch (e: any) {
    toast.error('保存失败: ' + (e?.message || '未知错误'))
  } finally {
    confirming.value = false
  }
}

onMounted(async () => {
  try {
    const saved = await v2Api.getModuleData(props.projectId, 'world')
    if (saved?.data && Object.keys(saved.data).length > 0) {
      Object.assign(world, saved.data)
    }
  } catch (_e) {
    loadError.value = '加载已保存的世界观数据失败'
  }
  if (!world.rules || Object.keys(world.rules).length === 0) {
    world.rules = {}
    worldRules.forEach(r => { world.rules[r.key] = '' })
  }
  if (!world.civilization || Object.keys(world.civilization).length === 0) {
    world.civilization = {}
    civDimensions.forEach(d => { world.civilization[d.key] = '' })
  }
  if (!Array.isArray(world.history)) {
    if (world.history && world.history.history && Array.isArray(world.history.history)) {
      world.history = world.history.history
    } else if (typeof world.history === 'object' && world.history !== null) {
      world.history = Object.entries(world.history).map(([k, v]) => ({ era: k, description: String(v) }))
    } else {
      world.history = []
    }
  }
  try {
    const allData = await v2Api.getAllModuleData(props.projectId)
    const idea = allData?.modules?.['idea']
    if (idea) {
      const sel = idea.confirmedCandidate || (idea.selectedIdx != null ? idea.candidates?.[idea.selectedIdx] : null)
      ideaText.value = sel?.title || sel?.concept || sel?.description || idea.prompt || ''
      ideaGenre.value = idea.genre || ''
      if (!world.origin.originStory) {
        world.origin.originStory = `基于创意"${ideaText.value}"构建的世界观`
      }
    }
    const project = allData?.modules?.['project']
    if (project) {
      projectPlatform.value = project.platform || ''
      projectSubGenre.value = project.sub_genre || ''
      projectTone.value = project.tone || ''
      if (!world.origin.worldType && project.sub_genre) {
        world.origin.worldType = project.sub_genre
      }
    }
  } catch (_e) {
    console.debug('[WorldView] prefill from story failed:', _e)
  }
  finally { pageLoading.value = false }
})

const worldData = () => ({ ...world })
const { saveState, scheduleSave, cancel } = useAutoSave({
  dataRef: worldData,
  saveFn: async (data) => {
    await v2Api.saveModuleData(props.projectId, 'world', data)
  },
  debounce: 2000,
  storageKey: `world_${props.projectId}`,
  onSaveError: () => toast.error('世界观自动保存失败，已存至本地备份'),
  projectId: props.projectId,
  moduleName: 'world',
})
watch(world, () => {
  scheduleSave()
}, { deep: true })
</script>

<style scoped>
.world-view { max-width: 1170px; margin: 0 auto; }
.upstream-missing-hint {
  background: #fff8e1;
  border: 1px solid #ffe082;
  border-radius: 8px;
  padding: 12px 16px;
  margin-bottom: 16px;
  color: #f57c00;
  font-size: 14px;
}
.accordion { border: 1px solid #eee; border-radius: 10px; overflow: hidden; }
.accordion-item { border-bottom: 1px solid #eee; }
.accordion-item:last-child { border-bottom: none; }
.accordion-header { display: flex; align-items: center; gap: 8px; padding: 14px 18px; background: #f8f9fa; cursor: pointer; user-select: none; font-weight: 600; color: #555; }
.accordion-header:hover { background: #f0f0f0; }
.accordion-icon { font-size: 12px; color: #888; }
.auto-save-status { text-align: right; font-size: 12px; color: #888; min-height: 18px; }
.auto-save-status .saving { color: #1890ff; }
.auto-save-status .saved { color: #52c41a; }
.auto-save-status .error { color: #ff4d4f; }
.accordion-body { padding: 20px; }
.tab-pane h3 { margin: 0 0 16px; font-size: 21px; }
.form-group { margin-bottom: 18px; }
.form-group label { display: block; font-weight: 600; margin-bottom: 8px; font-size: 17px; color: #555; }
.form-select, .form-textarea { width: 100%; padding: 10px 10px; border: 1px solid #ddd; border-radius: 5px; font-size: 17px; }
.rules-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; }
.rule-card { border: 1px solid #eee; border-radius: 8px; padding: 16px; }
.rule-name { font-weight: 600; margin-bottom: 8px; font-size: 17px; }
.civ-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 13px; }
.civ-card { border: 1px solid #eee; border-radius: 8px; padding: 16px; }
.civ-name { font-weight: 600; margin-bottom: 8px; font-size: 17px; }
.actions { display: flex; gap: 13px; margin-top: 21px; }
.btn-primary { padding: 13px 24px; background: var(--primary); color: #fff; border: none; border-radius: 8px; cursor: pointer; }
.btn-primary:disabled { opacity: 0.5; cursor: wait; }
.spinner { display: inline-block; width: 14px; height: 14px; border: 2px solid #fff; border-top-color: transparent; border-radius: 50%; animation: spin 0.8s linear infinite; margin-right: 6px; }
@keyframes spin { to { transform: rotate(360deg); } }
.btn-secondary { padding: 13px 20px; background: #f5f5f5; border: 1px solid #ddd; border-radius: 8px; cursor: pointer; }

.check-result { margin-top: 13px; font-size: 17px; text-align: center; }
.check-result .pass { color: #52c41a; }
.check-result .fail { color: #ff4d4f; }
.error-box { color: #e74c3c; background: #fff1f0; border-radius: 8px; padding: 12px; margin-top: 12px; font-size: 14px; }
.page-loading { display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 300px; gap: 16px; }
.loading-spinner { width: 36px; height: 36px; border: 3px solid #f0f0f0; border-top-color: #409eff; border-radius: 50%; animation: spin 0.8s linear infinite; }
</style>
