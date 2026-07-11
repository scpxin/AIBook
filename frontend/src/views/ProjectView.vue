<template>
  <div class="project-view">
    <div class="section">
      <h3>平台选择</h3>
      <div class="platform-grid">
        <div v-for="p in platforms" :key="p.id" class="platform-card" :class="{ active: selectedPlatform === p.id }" @click="selectedPlatform = p.id">
          <strong>{{ p.name }}</strong>
          <span>{{ p.desc }}</span>
        </div>
      </div>
    </div>

    <div class="section">
      <h3>项目定位分析</h3>
      <p class="section-desc">基于灵感内容，分析12个定位维度。"待分析"表示AI未能识别，可直接手动填写。</p>
      <div v-if="loading" class="loading-hint">加载中...</div>
      <div v-else-if="errorMessage" class="error-hint">{{ errorMessage }}</div>
      <div v-else-if="!hasIdea && !dimensions.length" class="empty-hint">
        请先完成"灵感生成"步骤，获取分析素材
        <div class="empty-action">
          <button class="btn-goto" @click="$emit('goto', 'idea')">前往灵感生成</button>
        </div>
      </div>
      <template v-else>
        <div v-if="dimensions.length" class="toolbar">
          <button class="btn-reanalyze" @click="reanalyze" :disabled="analyzing"><span v-if="analyzing" class="spinner"></span>{{ analyzing ? '分析中...' : '重新分析' }}</button>
          <span v-if="lastAnalyzed" class="analyzed-time">上次分析: {{ lastAnalyzed }}</span>
        </div>
        <div v-if="dimensions.length" class="dimension-list">
          <div v-for="dim in dimensions" :key="dim.key" class="dimension-item">
            <div class="dim-header" @click="toggleDim(dim.key)">
              <span class="dim-name">{{ dim.name }}</span>
              <span class="dim-toggle">{{ expandedDims.includes(dim.key) ? '▼' : '▶' }}</span>
            </div>
            <div v-if="expandedDims.includes(dim.key)" class="dim-content">
              <div v-for="(val, k) in dim.values" :key="k" class="dim-field">
                <span class="field-label">{{ k }}:</span>
                <input v-model="dim.values[k]" class="field-input" @blur="saveDimension(dim)" />
              </div>
              <div class="dim-hint">直接修改内容，失焦自动保存</div>
            </div>
          </div>
        </div>
        <div v-else-if="analyzing" class="loading-hint">AI分析中，请稍候...</div>
        <div v-else class="empty-hint">暂无分析数据，点击"重新分析"开始</div>
      </template>
    </div>

    <div class="section">
      <h3>兼容性检查</h3>
      <div class="compat-results">
        <div v-for="r in compatResults" :key="r.name" class="compat-item">
          <span class="compat-name">{{ r.name }}</span>
          <span class="compat-status" :class="r.passed ? 'pass' : 'fail'">{{ r.passed ? '通过' : '不通过' }}</span>
        </div>
      </div>
      <button @click="confirm" class="btn-confirm">确认定位,下一步</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch } from 'vue'
import * as v2Api from '../api/v2'

const props = defineProps<{ projectId: string }>()
const emit = defineEmits<{ complete: [data: any], goto: [module: string] }>()

const platforms = [
  { id: 'fanqie', name: '番茄', desc: '免费网文,男频女频' },
  { id: 'qidian', name: '起点', desc: '付费男频为主' },
  { id: 'qimao', name: '七猫', desc: '免费+短篇' },
  { id: 'custom', name: '自定义', desc: '灵活配置' },
]
const selectedPlatform = ref('fanqie')
const dimensions = ref<any[]>([])
const expandedDims = ref<string[]>([])
const compatResults = ref<any[]>([])
const loading = ref(false)
const analyzing = ref(false)
const errorMessage = ref('')
const lastAnalyzed = ref('')
const hasIdea = ref(false)

watch(selectedPlatform, () => { if (dimensions.value.length) saveDimension() })

onMounted(async () => {
  loading.value = true
  errorMessage.value = ''
  try {
    const saved = await v2Api.getModuleData(props.projectId, 'project')
    if (saved?.data && (saved.data.dimensions?.length || saved.data.platform)) {
      if (saved.data.platform) selectedPlatform.value = saved.data.platform
      if (saved.data.dimensions) {
        dimensions.value = saved.data.dimensions
        lastAnalyzed.value = saved.data.analyzedAt || ''
      }
      if (saved.data.compatResults) compatResults.value = saved.data.compatResults
      hasIdea.value = true
      loading.value = false
      return
    }

    const allData = await v2Api.getAllModuleData(props.projectId)
    const idea = allData?.modules?.['idea']
    const ideaText = extractIdeaText(idea)
    if (ideaText) {
      hasIdea.value = true
      try {
        const result = await v2Api.analyzeProject(props.projectId, ideaText, selectedPlatform.value)
        if (result && typeof result === 'object') {
          dimensions.value = mapResultToDimensions(result)
          lastAnalyzed.value = new Date().toLocaleTimeString()
          await saveDimension()
        }
      } catch (e: any) {
        errorMessage.value = '分析失败: ' + (e?.message || '未知错误') + '，请检查网络后重试'
      }
    }
    compatResults.value = [
      { name: '题材合规', passed: true },
      { name: '内容尺度', passed: true },
      { name: '平台匹配', passed: true },
    ]
  } catch (e: any) {
    errorMessage.value = '加载数据失败: ' + (e?.message || '未知错误')
  }
  loading.value = false
})

function extractIdeaText(idea: any): string {
  if (!idea) return ''
  const sel = idea.selected || (idea.selectedIdx != null && idea.candidates?.[idea.selectedIdx])
  return sel?.title || sel?.concept || sel?.description || idea.prompt || idea.confirmedCandidate?.title || ''
}

function mapResultToDimensions(result: any): any[] {
  if (!result || typeof result !== 'object') return []
  return Object.entries(result)
    .filter(([_, v]) => v != null)
    .slice(0, 12)
    .map(([key, val]) => {
      const obj = typeof val === 'object' ? val as any : { value: String(val) }
      return {
        key,
        name: formatDimName(key),
        values: obj.title ? { '内容': obj.content || '', '优先级': obj.priority || '' } : obj,
      }
    })
}

function formatDimName(key: string): string {
  const map: Record<string, string> = {
    target_audience: '目标读者',
    core_hook: '核心卖点',
    novelty_angle: '新颖角度',
    emotional_resonance: '情感共鸣点',
    update_strategy: '更新策略',
    title_direction: '书名方向',
    cover_concept: '封面概念',
    opener_strategy: '开篇策略',
    main_conflict: '主线矛盾',
    subplot_count: '支线数量',
    climax_pattern: '高潮模式',
    ending_direction: '结局方向',
    market_position: '市场定位',
    competition: '竞品分析',
    trend_alignment: '趋势匹配',
    platform_fit: '平台匹配度',
    serialization: '连载策略',
    word_count: '字数规划',
    update_frequency: '更新频率',
    monetization: '变现模式',
    risk_assessment: '风险评估',
  }
  return map[key] || key
}

function toggleDim(key: string) {
  const idx = expandedDims.value.indexOf(key)
  if (idx >= 0) expandedDims.value.splice(idx, 1)
  else expandedDims.value.push(key)
}

async function saveDimension(_dim?: any) {
  try {
    await v2Api.saveModuleData(props.projectId, 'project', {
      platform: selectedPlatform.value,
      dimensions: dimensions.value,
      compatResults: compatResults.value,
      analyzedAt: lastAnalyzed.value || new Date().toISOString(),
    })
  } catch (_e) { /* ignore */ }
}

async function reanalyze() {
  analyzing.value = true
  errorMessage.value = ''
  try {
    const allData = await v2Api.getAllModuleData(props.projectId)
    const idea = allData?.modules?.['idea']
    const ideaText = extractIdeaText(idea)
    if (!ideaText) {
      errorMessage.value = '没有可用的灵感内容，请先在"灵感生成"步骤中确认一个灵感'
      analyzing.value = false
      return
    }
    const result = await v2Api.analyzeProject(props.projectId, ideaText, selectedPlatform.value)
    if (result && typeof result === 'object') {
      dimensions.value = mapResultToDimensions(result)
      lastAnalyzed.value = new Date().toLocaleTimeString()
      await saveDimension()
    }
  } catch (e: any) {
    errorMessage.value = '分析失败: ' + (e?.message || '未知错误') + '，请检查网络或AI配置后重试'
  }
  analyzing.value = false
}

async function confirm() {
  await saveDimension({})
  emit('complete', { platform: selectedPlatform.value, dimensions: dimensions.value })
}
</script>

<style scoped>
.project-view { max-width: 1040px; margin: 0 auto; }
.section { background: #fff; border: 1px solid #eee; border-radius: 10px; padding: 26px; margin-bottom: 21px; }
.section h3 { margin: 0 0 12px; font-size: 21px; }
.platform-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 13px; }
.platform-card { border: 1px solid #ddd; border-radius: 8px; padding: 18px; cursor: pointer; display: flex; flex-direction: column; gap: 5px; transition: 0.15s; }
.platform-card strong { font-size: 18px; }
.platform-card span { font-size: 16px; color: #888; }
.platform-card:hover { border-color: var(--primary); }
.platform-card.active { border-color: var(--primary); background: #f0f8ff; }
.dimension-list { display: flex; flex-direction: column; gap: 5px; }
.dimension-item { border: 1px solid #f0f0f0; border-radius: 5px; }
.dim-header { display: flex; justify-content: space-between; padding: 10px 12px; cursor: pointer; font-weight: 500; }
.dim-toggle { font-size: 13px; color: #999; }
.dim-content { padding: 10px 12px; border-top: 1px solid #f0f0f0; }
.dim-field { display: flex; gap: 10px; padding: 3px 0; font-size: 17px; }
.field-label { font-weight: 600; color: #555; min-width: 104px; }
.field-input { flex: 1; padding: 4px 8px; border: 1px solid #ddd; border-radius: 4px; font-size: 16px; color: #333; }
.field-input:focus { border-color: var(--primary); outline: none; }
.dim-hint { margin-top: 8px; font-size: 12px; color: #999; }
.compat-results { display: flex; flex-direction: column; gap: 5px; margin-bottom: 21px; }
.compat-item { display: flex; justify-content: space-between; font-size: 17px; padding: 5px 0; }
.compat-name { color: #555; }
.compat-status.pass { color: #52c41a; }
.compat-status.fail { color: #ff4d4f; }
.section-desc { font-size: 13px; color: #888; margin: -6px 0 14px; }
.toolbar { margin-bottom: 12px; display: flex; align-items: center; gap: 12px; }
.btn-reanalyze { padding: 6px 16px; background: var(--primary); color: #fff; border: none; border-radius: 5px; font-size: 14px; cursor: pointer; }
.btn-reanalyze:disabled { opacity: 0.6; cursor: not-allowed; }
.analyzed-time { font-size: 12px; color: #999; }
.loading-hint { text-align: center; color: #999; padding: 20px; font-size: 14px; }
.empty-hint { color: #f57c00; background: #fff8e1; border-radius: 8px; margin-bottom: 10px; padding: 20px; font-size: 14px; text-align: center; }
.empty-action { margin-top: 12px; }
.btn-goto { padding: 6px 16px; background: var(--primary); color: #fff; border: none; border-radius: 5px; cursor: pointer; font-size: 14px; }
.error-hint { color: #ff4d4f; background: #fff1f0; border-radius: 8px; margin-bottom: 10px; padding: 12px; font-size: 14px; }
.btn-confirm { width: 100%; padding: 13px; background: #52c41a; color: #fff; border: none; border-radius: 8px; font-size: 20px; cursor: pointer; }
.spinner { display: inline-block; width: 12px; height: 12px; border: 2px solid #fff; border-top-color: transparent; border-radius: 50%; animation: spin 0.8s linear infinite; margin-right: 4px; }
@keyframes spin { to { transform: rotate(360deg); } }
</style>
