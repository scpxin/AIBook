<template>
  <div class="outline-view">
    <div v-if="pageLoading" class="page-loading">
      <div class="loading-spinner"></div>
      <p>加载中...</p>
    </div>
    <div v-else>
    <div class="section">
      <h3>全书大纲</h3>
      <p class="section-desc">基于故事框架、人物、世界观，生成完整的全书大纲</p>

      <div class="form-group">
        <label>书名暂定</label>
        <input v-model="form.title" class="form-input" placeholder="请输入书名..." />
      </div>
      <div class="form-group">
        <label>核心冲突</label>
        <textarea v-model="form.conflict" rows="3" class="form-textarea" placeholder="主角vs命运/社会/自我..." />
      </div>
      <div class="form-row">
        <div class="form-group" style="flex:1">
          <label>预计总字数</label>
          <select v-model="form.wordCount" class="form-select">
            <option value="300000">30万字（短篇）</option>
            <option value="800000">80万字（中篇）</option>
            <option value="1500000">150万字（长篇）</option>
            <option value="3000000">300万字（超长篇）</option>
          </select>
        </div>
        <div class="form-group" style="flex:1">
          <label>主角成长路线</label>
          <textarea v-model="form.growthRoute" rows="4" class="form-textarea" placeholder="废柴→觉醒→崛起→称霸→超脱" />
        </div>
      </div>

      <div class="actions">
        <button @click="generate" :disabled="generating" class="btn-primary">
          <span v-if="generating" class="spinner"></span>{{ generating ? '生成中...' : 'AI生成全书大纲' }}
        </button>
        <button @click="prefillFromStory" :disabled="prefillLoading" class="btn-secondary">
          <span v-if="prefillLoading" class="spinner"></span>{{ prefillLoading ? '提取中...' : '从故事框架提取' }}
        </button>
      </div>
    </div>

    <div v-if="hasResult" class="section">
      <h3>大纲预览（9维度）</h3>
      <div class="outline-card">
        <div v-if="result.title" class="outline-title">{{ result.title }}</div>
        <div class="outline-meta">
          <span v-if="result.theme" class="meta-tag">主题：{{ result.theme }}</span>
          <span v-if="result.wordCount" class="meta-tag">字数：{{ formatWords(result.wordCount) }}</span>
          <span v-if="result.ending_type" class="meta-tag">结局：{{ result.ending_type }}</span>
        </div>

        <div v-if="result.opening" class="outline-section">
          <h4>1. 开篇设计</h4>
          <p>{{ typeof result.opening === 'string' ? result.opening : (result.opening.hook || result.opening.first_chapter || JSON.stringify(result.opening)) }}</p>
        </div>

        <div v-if="result.rising_actions?.length" class="outline-section">
          <h4>2. 上升阶段 ({{ result.rising_actions.length }}阶段)</h4>
          <div v-for="(r, idx) in result.rising_actions" :key="idx" class="rising-phase">
            <span class="phase-label">{{ r.phase || `阶段${idx+1}` }}</span>
            <p>{{ r.main_progress || r.character_change || '' }}</p>
            <span v-if="r.wordcount" class="wordcount-badge">{{ r.wordcount }}字</span>
          </div>
        </div>

        <div v-if="result.subplots?.length" class="outline-section">
          <h4>3. 支线规划 ({{ result.subplots.length }}条)</h4>
          <div v-for="(sp, idx) in result.subplots" :key="idx" class="subplot-item">
            <span v-if="sp.type" class="subplot-type">{{ sp.type }}</span>
            <span v-if="sp.function" class="subplot-func">{{ sp.function }}</span>
            <span v-if="sp.start_chapter" class="subplot-range">第{{ sp.start_chapter }}-{{ sp.end_chapter }}章</span>
          </div>
        </div>

        <div v-if="result.midpoint_turn" class="outline-section">
          <h4>4. 中点转折</h4>
          <p>{{ typeof result.midpoint_turn === 'string' ? result.midpoint_turn : (JSON.stringify(result.midpoint_turn)) }}</p>
        </div>

        <div v-if="result.climax_buildup" class="outline-section">
          <h4>5. 高潮铺垫</h4>
          <p>{{ typeof result.climax_buildup === 'string' ? result.climax_buildup : (result.climax_buildup.layers || result.climax_buildup.duration || JSON.stringify(result.climax_buildup)) }}</p>
        </div>

        <div v-if="result.final_climax" class="outline-section">
          <h4>6. 总高潮</h4>
          <p>{{ typeof result.final_climax === 'string' ? result.final_climax : (JSON.stringify(result.final_climax)) }}</p>
        </div>

        <div v-if="result.ending_type" class="outline-section">
          <h4>7. 结局类型</h4>
          <p>{{ result.ending_type }}</p>
        </div>

        <div v-if="result.rewatch_hooks" class="outline-section">
          <h4>8. 重读钩子</h4>
          <p>{{ typeof result.rewatch_hooks === 'string' ? result.rewatch_hooks : JSON.stringify(result.rewatch_hooks) }}</p>
        </div>

        <div v-if="result.volume_structure" class="outline-section">
          <h4>9. 卷结构</h4>
          <div v-if="Array.isArray(result.volume_structure)" class="volume-grid">
            <div v-for="(v, idx) in result.volume_structure" :key="idx" class="volume-card" tabindex="0">
              <span class="volume-num">第{{ idx + 1 }}卷</span>
              <span class="volume-title">{{ v.title || v.name }}</span>
              <p>{{ v.summary || v.role || '' }}</p>
              <span v-if="v.wordcount" class="wordcount-badge">{{ v.wordcount }}字</span>
            </div>
          </div>
          <p v-else>{{ typeof result.volume_structure === 'string' ? result.volume_structure : JSON.stringify(result.volume_structure) }}</p>
        </div>
      </div>
    </div>

    <div v-if="error" class="error-box">{{ error }}</div>

    <div v-if="hasResult" class="section">
      <button @click="confirm" class="btn-confirm">确认大纲,下一步</button>
    </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, computed, onMounted, watch } from 'vue'
import { generateMasterOutline, saveMasterOutline, getModuleData, getAllModuleData, saveModuleData } from '../api/v2'
import { useGeneration } from '../composables/useGeneration'
import { setupConfirm } from '../composables/useConfirm'
import { setupErrorBar } from '../composables/useErrorBar'
import { useAutoSave } from '../composables/useAutoSave'
import { useToastStore } from '../stores/toast'

const confirmDialog = setupConfirm()
const errorBar = setupErrorBar()
const pageLoading = ref(true)

const props = defineProps<{ projectId: string }>()
const emit = defineEmits<{ complete: [data: any] }>()
const gen = useGeneration('outline', '全书大纲')

const generating = ref(false)
const prefillLoading = ref(false)
const error = ref('')
const form = reactive({ title: '', conflict: '', wordCount: '1500000', growthRoute: '' })
const result = reactive<any>({ title: '', theme: '', conflict: '', wordCount: '', growthRoute: '', volumes: [], opening: null, rising_actions: [], subplots: [], midpoint_turn: null, climax_buildup: null, final_climax: null, ending_type: '', rewatch_hooks: null, volume_structure: null })

const growthSteps = computed(() =>
  (result.growthRoute || form.growthRoute).split(/[→\n,，]/).map((s: string) => s.trim()).filter(Boolean)
)

const hasResult = computed(() => {
  return result.title || result.theme || result.opening || result.rising_actions?.length ||
    result.subplots?.length || result.midpoint_turn || result.climax_buildup ||
    result.final_climax || result.ending_type || result.rewatch_hooks || result.volume_structure
})

function formatWords(n: string | number): string {
  const num = typeof n === 'string' ? parseInt(n) : n
  return num >= 10000 ? (num / 10000) + '万字' : n + '字'
}

async function generate() {
  generating.value = true
  error.value = ''
  gen.begin(1, '正在生成全书大纲...')
  try {
    const allData = await getAllModuleData(props.projectId)
    const chars = allData?.modules?.['characters']
    const world = allData?.modules?.['world']
    const storyArch = allData?.modules?.['story_architecture']
    const storySystem = {
      theme: form.title || storyArch?.story?.theme || '',
      conflict: form.conflict || storyArch?.story?.coreConflict || '',
      protagonist: chars?.protagonist || {},
      world: world || {},
      characters: [chars?.protagonist, ...(chars?.supporting || []), ...(chars?.villains || [])].filter(Boolean),
      plot_events: storyArch?.story?.plotEvents || [],
      word_count: parseInt(form.wordCount),
      growth_route: form.growthRoute,
    }
    const r = await generateMasterOutline(props.projectId, storySystem) as any
    if (r) {
      if (r.title) result.title = r.title
      if (r.theme) result.theme = r.theme
      if (r.conflict) result.conflict = r.conflict
      if (r.wordCount) result.wordCount = String(r.wordCount)
      if (r.growthRoute) result.growthRoute = r.growthRoute
      if (r.growth_route) result.growthRoute = r.growth_route
      if (r.volumes) result.volumes = r.volumes

      if (r.opening) result.opening = r.opening
      if (r.rising_actions) result.rising_actions = r.rising_actions
      if (r.subplots) result.subplots = r.subplots
      if (r.midpoint_turn) result.midpoint_turn = r.midpoint_turn
      if (r.climax_buildup) result.climax_buildup = r.climax_buildup
      if (r.final_climax) result.final_climax = r.final_climax
      if (r.ending_type) result.ending_type = r.ending_type
      if (r.rewatch_hooks) result.rewatch_hooks = r.rewatch_hooks
      if (r.volume_structure) result.volume_structure = r.volume_structure
    }
    gen.end()
  } catch (e: any) {
    errorBar.showError(e, () => generate())
    gen.fail(e?.message || '生成失败，可手动填写')
  } finally {
    generating.value = false
  }
}

async function prefillFromStory() {
  prefillLoading.value = true
  let saved: any
  try {
    saved = await getModuleData(props.projectId, 'story_architecture')
  } catch (e) {
    toast.error('从故事框架预填数据失败')
    prefillLoading.value = false
    return
  }
  const d = saved?.data
  if (!d?.story) {
    toast.info('暂无故事框架数据，请先完成故事架构模块')
    prefillLoading.value = false
    return
  }
  if (d?.story) {
    if (d.story.oneLiner) form.title = d.story.oneLiner
    if (d.story.coreConflict) form.conflict = d.story.coreConflict
  }
  prefillLoading.value = false
}

async function confirm() {
  const ok = await confirmDialog.confirm({
    message: '确定进入下一步？',
    detail: '确认后将保存当前大纲数据并进入下一模块',
    type: 'info',
  })
  if (!ok) return
  try {
    await saveMasterOutline(props.projectId, result)
    await saveModuleData(props.projectId, 'outline', {
      module_data: { ...result },
    })
  } catch (_e) { /* ignore */ }
  emit('complete', { ...result })
}

onMounted(async () => {
  try {
    const saved = await getModuleData(props.projectId, 'outline')
    if (saved?.data?.outline) {
      const o = saved.data.outline
      if (o.title) result.title = o.title
      if (o.theme) result.theme = o.theme
      if (o.conflict) result.conflict = o.conflict
      if (o.growthRoute) result.growthRoute = o.growthRoute
    } else if (saved?.data?.title) {
      Object.assign(result, saved.data)
    }
  } catch (_e) { /* ignore */ }
  finally { pageLoading.value = false }
})

const toast = useToastStore()
const outlineData = () => ({ form: { ...form }, result: { ...result } })
const { saveState, scheduleSave } = useAutoSave({
  dataRef: outlineData,
  saveFn: async (data) => {
    await saveModuleData(props.projectId, 'outline', data)
  },
  debounce: 2000,
  storageKey: `outline_${props.projectId}`,
  onSaveError: () => toast.error('大纲自动保存失败，已存至本地备份'),
  projectId: props.projectId,
  moduleName: 'outline',
})
watch([form, result], () => {
  scheduleSave()
}, { deep: true })
</script>

<style scoped>
.outline-view { max-width: 1040px; margin: 0 auto; }
.section { background: #fff; border: 1px solid #eee; border-radius: 10px; padding: 26px; margin-bottom: 21px; }
.section h3 { margin: 0 0 12px; font-size: 21px; }
.section-desc { font-size: 13px; color: #888; margin: -6px 0 14px; }
.form-group { margin-bottom: 16px; }
.form-group label { display: block; font-weight: 600; margin-bottom: 5px; font-size: 17px; color: #555; }
.form-input, .form-textarea, .form-select { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 5px; font-size: 17px; }
.form-row { display: flex; gap: 16px; }
.actions { display: flex; gap: 13px; margin: 20px 0; }
.btn-primary { padding: 13px 24px; background: var(--primary); color: #fff; border: none; border-radius: 8px; cursor: pointer; font-size: 16px; }
.btn-primary:disabled { opacity: 0.5; cursor: wait; }
.btn-secondary { padding: 13px 20px; background: #f5f5f5; border: 1px solid #ddd; border-radius: 8px; cursor: pointer; }
.btn-confirm { width: 100%; padding: 13px; background: #52c41a; color: #fff; border: none; border-radius: 8px; font-size: 20px; cursor: pointer; }
.outline-card { border: 2px solid var(--primary); border-radius: 14px; padding: 24px; background: #f8fbff; }
.outline-title { font-size: 24px; font-weight: 700; color: var(--primary); margin-bottom: 12px; }
.outline-meta { display: flex; gap: 12px; margin-bottom: 16px; flex-wrap: wrap; }
.meta-tag { background: #e8f4fd; color: var(--primary); padding: 4px 12px; border-radius: 8px; font-size: 14px; font-weight: 600; }
.outline-section { margin-top: 16px; }
.outline-section h4 { font-size: 16px; color: #333; margin-bottom: 8px; }
.outline-section p { color: #555; font-size: 15px; line-height: 1.6; }
.growth-timeline { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; }
.growth-step { background: #fff; border: 1px solid #ddd; border-radius: 8px; padding: 6px 14px; font-size: 15px; font-weight: 600; }
.growth-step .arrow { color: var(--primary); margin-left: 8px; font-weight: 700; }
.volume-grid { display: flex; flex-direction: column; gap: 12px; margin-top: 10px; }
.volume-card { border: 1px solid #eee; border-radius: 8px; padding: 14px; }
.volume-num { font-size: 14px; color: var(--primary); font-weight: 600; margin-right: 8px; }
.volume-title { font-weight: 600; }
.spinner { display: inline-block; width: 12px; height: 12px; border: 2px solid #fff; border-top-color: transparent; border-radius: 50%; animation: spin 0.8s linear infinite; margin-right: 4px; }
@keyframes spin { to { transform: rotate(360deg); } }
.error-box { color: #e74c3c; background: #fff1f0; border-radius: 8px; padding: 12px; margin-bottom: 16px; }
.page-loading { display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 300px; gap: 16px; }
.loading-spinner { width: 36px; height: 36px; border: 3px solid #f0f0f0; border-top-color: #409eff; border-radius: 50%; animation: spin 0.8s linear infinite; }
</style>
