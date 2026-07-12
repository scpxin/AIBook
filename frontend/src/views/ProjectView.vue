<template>
  <div class="project-view">
    <div v-if="pageLoading" class="page-loading">
      <div class="loading-spinner"></div>
      <p>加载中...</p>
    </div>
    <div v-else>
    <div class="section">
      <h3>平台选择</h3>
      <div class="platform-grid">
        <div v-for="p in platforms" :key="p.id" class="platform-card" :class="{ active: selectedPlatform === p.id }" tabindex="0" @click="selectedPlatform = p.id" @keydown.enter="selectedPlatform = p.id">
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
            <div class="dim-header" tabindex="0" @click="toggleDim(dim.key)" @keydown.enter="toggleDim(dim.key)">
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
          <span class="compat-status" :class="r.level">{{ 
            r.level === 'pass' ? '通过' : 
            r.level === 'fail' ? '不通过' : '待检查' 
          }}</span>
        </div>
      </div>
      <div v-if="compatDetail && compatDetail.adjustment" class="compat-advice">
        <div class="compat-advice-title">调整建议</div>
        <p>{{ compatDetail.adjustment }}</p>
        <div v-if="compatDetail.pros.length" class="compat-pros">
          <span class="tag-pro" v-for="p in compatDetail.pros" :key="p">{{ p }}</span>
        </div>
        <div v-if="compatDetail.cons.length" class="compat-cons">
          <span class="tag-con" v-for="c in compatDetail.cons" :key="c">{{ c }}</span>
        </div>
      </div>
      <button @click="confirm" class="btn-confirm">确认定位,下一步</button>
    </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted, watch } from 'vue'
import * as v2Api from '../api/v2'
import { setupConfirm } from '../composables/useConfirm'
import { setupErrorBar } from '../composables/useErrorBar'
import { useGeneration } from '../composables/useGeneration'
import { useAutoSave } from '../composables/useAutoSave'
import { useToastStore } from '../stores/toast'

const props = defineProps<{ projectId: string }>()
const emit = defineEmits<{ complete: [data: any], goto: [module: string] }>()
const confirmDialog = setupConfirm()
const errorBar = setupErrorBar()
const gen = useGeneration('project', '项目定位分析')
const toast = useToastStore()
const pageLoading = ref(true)

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
const compatDetail = ref<{ pros: string[]; cons: string[]; adjustment: string } | null>(null)
const loading = ref(false)
const analyzing = ref(false)
const errorMessage = ref('')
const lastAnalyzed = ref('')
const hasIdea = ref(false)

watch(selectedPlatform, () => {
  if (dimensions.value.length) saveDimension()
  checkCompatibility()
})

const projectData = () => ({
  platform: selectedPlatform.value,
  dimensions: dimensions.value,
  compatResults: compatResults.value,
  analyzedAt: lastAnalyzed.value,
})
const { scheduleSave } = useAutoSave({
  dataRef: projectData,
  saveFn: async (data) => {
    try { await v2Api.saveModuleData(props.projectId, 'project', data) } catch (_e) { /* silent */ }
  },
  debounce: 1500,
  storageKey: `project_${props.projectId}`,
  projectId: props.projectId,
  moduleName: 'project',
})
watch([selectedPlatform, dimensions, compatResults], () => {
  scheduleSave()
}, { deep: true })

onMounted(async () => {
  loading.value = true
  errorMessage.value = ''
  try {
    const saved = await v2Api.getModuleData(props.projectId, 'project')
    if (saved?.data && Object.keys(saved.data).length > 0 && (saved.data.dimensions?.length || saved.data.platform || saved.data.sub_genre || saved.data.tone)) {
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
      analyzing.value = true
      gen.begin(12, '正在分析项目定位...')
      try {
        let allDims: any[] = []
        for (let batch = 0; batch < 3; batch++) {
          gen.progress(batch * 4, `正在分析第 ${batch + 1}/3 批维度 (${batch * 4 + 1}-${Math.min((batch + 1) * 4, 12)}/12)...`)
          try {
            const result = await v2Api.analyzeProjectBatch(props.projectId, ideaText, selectedPlatform.value, batch)
            if (result?.dimensions?.length) {
              const mapped = result.dimensions.map((d: any) => ({
                key: d.key || d.title,
                name: d.title || formatDimName(d.key),
                values: { '内容': d.content || '', '优先级': d.priority || '' },
              }))
              allDims = allDims.concat(mapped)
              dimensions.value = allDims
              lastAnalyzed.value = new Date().toLocaleTimeString()
            }
          } catch (batchErr: any) {
            // 单批失败不中断其他批
          }
        }
        if (allDims.length > 0) {
          await saveDimension()
        } else {
          throw new Error('所有批次分析均失败')
        }
      } catch (e: any) {
        errorMessage.value = '分析失败: ' + (e?.message || '未知错误') + '，请检查网络后重试'
      } finally {
        analyzing.value = false
        gen.end()
      }
    }
    compatResults.value = [
      { name: '题材合规', level: 'pending' },
      { name: '内容尺度', level: 'pending' },
      { name: '平台匹配', level: 'pending' },
    ]
    checkCompatibility()
  } catch (e: any) {
    errorBar.showError(e, () => checkCompatibility())
  } finally {
    pageLoading.value = false
    loading.value = false
  }
})

onUnmounted(() => {
  gen.end()
})

async function checkCompatibility() {
  if (!props.projectId) return
  try {
    const allData = await v2Api.getAllModuleData(props.projectId)
    const idea = allData?.modules?.['idea']
    const ideaText = extractIdeaText(idea)
    const result = await v2Api.checkProjectCompatibility(props.projectId, ideaText, selectedPlatform.value)
    if (result) {
      compatResults.value = [
        { name: '题材合规', level: result.score >= 60 ? 'pass' : 'fail' },
        { name: '内容尺度', level: result.fit !== '极低' ? 'pass' : 'fail' },
        { name: '平台匹配', level: result.score >= 40 ? 'pass' : 'fail' },
      ]
      compatDetail.value = {
        pros: result.pros || [],
        cons: result.cons || [],
        adjustment: result.adjustment || '',
      }
    }
  } catch (e) {
    console.error('[ProjectView] compatibility check failed:', e)
    compatResults.value = compatResults.value.map((r: any) =>
      r.level === 'pending' ? r : { ...r, level: r.level, _lastError: '检查失败，显示上次结果' }
    )
    errorBar.showError(e, () => checkCompatibility())
  }
}

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

async function saveDimension(): Promise<boolean> {
  try {
    await v2Api.saveModuleData(props.projectId, 'project', {
      platform: selectedPlatform.value,
      dimensions: dimensions.value,
      compatResults: compatResults.value,
      analyzedAt: lastAnalyzed.value || new Date().toISOString(),
    })
    return true
  } catch (e: any) {
    errorMessage.value = '保存失败: ' + (e?.message || '未知错误')
    return false
  }
}

async function reanalyze() {
  analyzing.value = true
  errorMessage.value = ''
  dimensions.value = []
  lastAnalyzed.value = ''
  gen.begin(12, '正在分析项目定位...')
  try {
    const allData = await v2Api.getAllModuleData(props.projectId)
    const idea = allData?.modules?.['idea']
    const ideaText = extractIdeaText(idea)
    if (!ideaText) {
      errorMessage.value = '没有可用的灵感内容，请先在"灵感生成"步骤中确认一个灵感'
      analyzing.value = false
      gen.end()
      return
    }
    let allDims: any[] = []
    for (let batch = 0; batch < 3; batch++) {
      gen.progress(batch * 4, `正在分析第 ${batch + 1}/3 批维度 (${batch * 4 + 1}-${Math.min((batch + 1) * 4, 12)}/12)...`)
      try {
        const result = await v2Api.analyzeProjectBatch(props.projectId, ideaText, selectedPlatform.value, batch)
        if (result?.dimensions?.length) {
          const mapped = result.dimensions.map((d: any) => ({
            key: d.key || d.title,
            name: d.title || formatDimName(d.key),
            values: { '内容': d.content || '', '优先级': d.priority || '' },
          }))
          allDims = allDims.concat(mapped)
          dimensions.value = allDims
          lastAnalyzed.value = new Date().toLocaleTimeString()
        }
      } catch (batchErr: any) {
        // 单批失败不中断其他批
      }
    }
    if (dimensions.value.length > 0) {
      await saveDimension()
    } else {
      errorMessage.value = '所有维度分析失败，请检查网络后重试'
    }
  } catch (e: any) {
    errorBar.showError(e, () => reanalyze())
  } finally {
    analyzing.value = false
    gen.end()
  }
}

async function confirm() {
  if (confirming.value) return
  if (!dimensions.value.length) {
    const ok = await confirmDialog.confirm({
      message: '尚未进行项目定位分析',
      detail: '建议先进行分析以获得更好的创作建议。确定跳过？',
      type: 'warning',
    })
    if (!ok) return
  }
  const failed = compatResults.value.filter(r => r.level === 'fail')
  if (failed.length > 0) {
    const detail = compatDetail.value
    let msg = `以下兼容性检查未通过：${failed.map(f => f.name).join('、')}`
    if (detail && detail.adjustment) {
      msg += `\n\n调整建议：${detail.adjustment}`
    }
    const ok = await confirmDialog.confirm({
      message: '兼容性检查未通过',
      detail: msg,
      type: 'warning',
    })
    if (!ok) return
  }
  confirming.value = true
  try {
    const saved = await saveDimension()
    if (!saved) {
      toast.error('保存分析结果失败，请重试')
      return
    }
    emit('complete', { platform: selectedPlatform.value, dimensions: dimensions.value })
  } finally {
    confirming.value = false
  }
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
.compat-advice { background: #f6f8fa; border-radius: 8px; padding: 16px; margin-bottom: 16px; font-size: 14px; }
.compat-advice-title { font-weight: 600; margin-bottom: 8px; color: #333; }
.compat-advice p { margin: 0 0 12px; color: #555; line-height: 1.6; }
.compat-pros, .compat-cons { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px; }
.tag-pro { background: #f6ffed; color: #52c41a; padding: 2px 10px; border-radius: 12px; font-size: 12px; border: 1px solid #b7eb8f; }
.tag-con { background: #fff2e8; color: #ff4d4f; padding: 2px 10px; border-radius: 12px; font-size: 12px; border: 1px solid #ffccc7; }
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
.page-loading { display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 300px; gap: 16px; }
.loading-spinner { width: 36px; height: 36px; border: 3px solid #f0f0f0; border-top-color: #409eff; border-radius: 50%; animation: spin 0.8s linear infinite; }
</style>
