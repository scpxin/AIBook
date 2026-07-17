<template>
  <div class="story-arch-view">
    <div v-if="pageLoading" class="page-loading">
      <div class="loading-spinner"></div>
      <p>加载中...</p>
    </div>
    <div v-else>
    <div class="section">
      <h3>故事框架</h3>
      <div class="form-group">
        <label>一句话概括</label>
        <input v-model="story.oneLiner" class="form-input" placeholder="用一句话描述整个故事..." />
      </div>
      <div class="form-group">
        <label>核心主题</label>
        <input v-model="story.theme" class="form-input" placeholder="如：逆天改命、守护苍生..." />
      </div>
      <div class="form-group">
        <label>核心冲突</label>
        <textarea v-model="story.coreConflict" class="form-textarea" rows="3" placeholder="主角面临的核心矛盾..." />
      </div>
      <div class="action-row">
         <button @click="generateStory" :disabled="generating" class="btn btn-primary">
           <span v-if="generating" class="spinner"></span>{{ generating ? '生成中...' : 'AI生成故事框架' }}
         </button>
      </div>
    </div>

    <div v-if="story.volumes?.length" class="section">
      <h3>卷纲预览</h3>
      <div class="volume-grid">
        <div v-for="(v, idx) in story.volumes" :key="idx" class="volume-card" tabindex="0">
          <div class="volume-header">
            <span class="volume-num">第{{ idx + 1 }}卷</span>
            <span class="volume-title">{{ v.title }}</span>
          </div>
          <div class="volume-summary">{{ v.summary }}</div>
          <div class="volume-hooks">
            <span v-for="h in v.hooks" :key="h" class="hook-tag">{{ h }}</span>
          </div>
        </div>
      </div>
    </div>

    <div v-if="story.plotEvents?.length" class="section">
      <h3>剧情节点</h3>
      <div class="plot-node-list">
        <div v-for="(n, i) in story.plotEvents" :key="i" class="plot-node-card">
          <span class="node-chapter">第{{ n.chapter || '?' }}章</span>
          <span class="node-event">{{ n.event }}</span>
        </div>
      </div>
    </div>

    <div class="section">
      <h3>剧情节点</h3>
      <div class="form-group">
        <label>节点数量</label>
        <select v-model="plotNodeCount" class="form-input" style="width:200px">
          <option :value="6">6个</option><option :value="8">8个</option><option :value="10">10个</option>
        </select>
      </div>
      <div class="action-row">
         <button @click="generatePlotNodes" :disabled="generating" class="btn btn-primary">
           <span v-if="generating" class="spinner"></span>{{ generating ? '生成中...' : 'AI生成剧情节点' }}
         </button>
      </div>
    </div>

    <div v-if="plotNodes.length" class="section">
      <h3>剧情节点列表</h3>
      <div class="plot-node-list">
        <div v-for="(n, i) in plotNodes" :key="i" class="plot-node-card">
          <span class="node-label">{{ n.type || `节点${i + 1}` }}</span>
          <span class="node-title">{{ n.title || n.name }}</span>
          <p class="node-desc">{{ n.description }}</p>
        </div>
      </div>
    </div>

    <div class="section">
      <h3>事件时间线</h3>
      <TimelineChart :events="story.plotEvents || []" :editable="true" @reorder="onReorderEvents" />
    </div>

    <div v-if="error" class="error">{{ error }}</div>

    <div class="actions">
      <button @click="confirm" class="btn-confirm" :disabled="confirming">{{ confirming ? '保存中...' : '确认架构，下一步' }}</button>
    </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, computed, onMounted, watch } from 'vue'
import { generateStoryMaster, generateMasterOutline, generatePlotNodes as genPlotNodes, getModuleData, getAllModuleData, saveModuleData } from '../api/v2'
import { useGeneration } from '../composables/useGeneration'
import { setupConfirm } from '../composables/useConfirm'
import { setupErrorBar } from '../composables/useErrorBar'
import { useAutoSave } from '../composables/useAutoSave'
import { useToastStore } from '../stores/toast'
import TimelineChart from '../components/TimelineChart.vue'

const confirmDialog = setupConfirm()
const errorBar = setupErrorBar()
const pageLoading = ref(true)

const props = defineProps<{ projectId: string }>()
const emit = defineEmits<{ complete: [data: Record<string, unknown>] }>()
const gen = useGeneration('story_architecture', '故事架构')
const generating = ref(false)
const confirming = ref(false)
const error = ref('')
const plotNodeCount = ref(6)
const plotNodes = ref<Record<string, unknown>[]>([])

const story: any = reactive({ oneLiner: '', theme: '', coreConflict: '', volumes: [], plotEvents: [] })

function onReorderEvents(newEvents: unknown[]) { story.plotEvents = newEvents }

async function generateStory() {
  generating.value = true; error.value = ''; gen.begin(3, '正在生成故事框架...')
  try {
    const allData = await getAllModuleData(props.projectId)
    const chars = allData?.modules?.['characters']
    const protagonist = chars?.protagonist || chars?.data?.protagonist || null
    const characters = [
      chars?.protagonist || chars?.data?.protagonist,
      ...(chars?.supporting || chars?.data?.supporting || []),
      ...(chars?.villains || chars?.data?.villains || [])
    ].filter(Boolean)
    const world = allData?.modules?.['world']
    const result = await generateStoryMaster(props.projectId, protagonist, world, characters) as any
    if (result) {
      if (result.oneLiner) story.oneLiner = result.oneLiner
      if (result.theme) story.theme = result.theme
      if (result.coreConflict) story.coreConflict = result.coreConflict
      if (result.masterStory) {
        if (result.masterStory.theme) story.theme = result.masterStory.theme
        if (result.masterStory.volumes) story.volumes = result.masterStory.volumes
        if (result.masterStory.plotEvents) story.plotEvents = result.masterStory.plotEvents
      }
      if (result.volumes) story.volumes = result.volumes
      if (result.plotEvents) story.plotEvents = result.plotEvents
    }
    gen.progress(1, '正在提取卷纲...')
    gen.progress(2, '正在整理剧情节点...')
    gen.progress(3, '故事框架生成完成')
    gen.end()
  } catch (e: any) {
    errorBar.showError(e, () => generateStory())
    gen.fail(e?.message || '生成失败')
  }
  finally { generating.value = false }
}

async function generatePlotNodes() {
  generating.value = true; error.value = ''; gen.begin()
  try {
    const allData = await getAllModuleData(props.projectId)
    const world = allData?.modules?.['world']
    const chars = allData?.modules?.['characters']
    const storySystem = {
      theme: story.theme,
      conflict: story.coreConflict,
      protagonist: chars?.protagonist || {},
      world: world || {},
      characters: [chars?.protagonist, ...(chars?.supporting || []), ...(chars?.villains || [])].filter(Boolean),
      plot_events: story.plotEvents || [],
    }
    const result = await generateMasterOutline(props.projectId, storySystem)
    if (result) {
      const r = result as any
      if (r.plotEvents) story.plotEvents = r.plotEvents
      else if (r.event_chain) story.plotEvents = r.event_chain.map((e: any) => ({ chapter: e.chapter_hint || 1, event: e.event || e.name || '' }))
    }
    gen.end()
  } catch (e: any) { errorBar.showError(e, () => generatePlotNodes()); gen.fail(e?.message || 'AI生成失败') }
  finally { generating.value = false }
}



async function confirm() {
  if (confirming.value) return
  cancel()
  const ok = await confirmDialog.confirm({
    message: '确定进入下一步？',
    detail: '确认后将保存当前故事架构数据并进入下一模块',
    type: 'info',
  })
  if (!ok) return
  confirming.value = true
  const data = {
    story: { ...story },
    plot_nodes: plotNodes.value,
  }
  try {
    await saveModuleData(props.projectId, 'story_architecture', data)
    toast.success('故事架构已保存')
    emit('complete', data)
  } catch (e: any) {
    toast.error('保存失败: ' + (e?.message || '未知错误'))
  } finally {
    confirming.value = false
  }
}

onMounted(async () => {
  try {
    const saved = await getModuleData(props.projectId, 'story_architecture')
    if (saved?.data) {
      const d = saved.data
      if (d.story) Object.assign(story, d.story)
      if (d.plot_nodes) plotNodes.value = d.plot_nodes
    }
  } catch (_e) { /* ignore */ }
  try {
    const allData = await getAllModuleData(props.projectId)
    const chars = allData?.modules?.['characters']
    if (chars?.protagonist || chars?.data?.protagonist) {
      const p = chars.protagonist || chars.data?.protagonist
      if (!story.oneLiner && p.title) story.oneLiner = p.title + '的冒险'
    }
    const world = allData?.modules?.['world']
    if (world && !story.theme && world.theme) story.theme = world.theme
  } catch (_e) { /* ignore */ }
  finally { pageLoading.value = false }
})

const toast = useToastStore()
const storyArchData = () => ({ story: { ...story }, plot_nodes: plotNodes.value })
const { saveState, scheduleSave, cancel } = useAutoSave({
  dataRef: storyArchData,
  saveFn: async (data) => {
    await saveModuleData(props.projectId, 'story_architecture', data)
  },
  debounce: 2000,
  storageKey: `story_arch_${props.projectId}`,
  onSaveError: () => toast.error('故事架构自动保存失败，已存至本地备份'),
  projectId: props.projectId,
  moduleName: 'story_architecture',
})
watch(story, () => {
  scheduleSave()
}, { deep: true })
</script>

<style scoped>
.story-arch-view { max-width: 1170px; margin: 0 auto; }
.section { background: #fff; border: 1px solid #eee; border-radius: 10px; padding: 26px; margin-bottom: 21px; }
.section h3 { margin: 0 0 12px; font-size: 21px; }
.form-group { margin-bottom: 16px; }
.form-group label { display: block; font-weight: 600; margin-bottom: 5px; font-size: 17px; color: #555; }
.form-input, .form-textarea, .form-select { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 5px; font-size: 17px; resize: vertical; font-family: inherit; }
.form-row { display: flex; gap: 16px; }
.action-row { margin-top: 10px; }
.volume-grid { display: flex; flex-direction: column; gap: 13px; }
.volume-card { border: 1px solid #eee; border-radius: 8px; padding: 18px; }
.volume-header { display: flex; align-items: center; gap: 13px; margin-bottom: 8px; }
.volume-num { font-size: 16px; color: var(--primary); font-weight: 600; background: #e8f4fd; padding: 3px 8px; border-radius: 4px; }
.volume-title { font-weight: 600; font-size: 18px; }
.volume-summary { font-size: 17px; color: #666; line-height: 1.6; }
.volume-hooks { display: flex; flex-wrap: wrap; gap: 5px; margin-top: 10px; }
.hook-tag { font-size: 14px; padding: 3px 6px; background: #f0f0f0; border-radius: 4px; color: #666; }
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
.plot-node-list { display: flex; flex-wrap: wrap; gap: 12px; }
.plot-node-card { border: 1px solid #eee; border-radius: 8px; padding: 16px; min-width: 200px; flex: 1; }
.node-label { font-size: 13px; color: var(--primary); background: #f0f4ff; padding: 2px 8px; border-radius: 4px; margin-right: 8px; }
.node-title { font-weight: 600; }
.node-desc { font-size: 15px; color: #666; margin-top: 8px; line-height: 1.5; }
.error { color: #e74c3c; margin-bottom: 12px; font-size: 15px; }
.actions { display: flex; gap: 13px; margin-top: 21px; }
.btn { border: none; border-radius: 10px; padding: 12px 24px; font-size: 16px; font-weight: 600; cursor: pointer; }
.btn-primary { background: linear-gradient(135deg, var(--primary), var(--primary-light)); color: #fff; }
.btn-primary:disabled { opacity: 0.5; cursor: wait; }
.spinner { display: inline-block; width: 14px; height: 14px; border: 2px solid #fff; border-top-color: transparent; border-radius: 50%; animation: spin 0.8s linear infinite; margin-right: 6px; }
@keyframes spin { to { transform: rotate(360deg); } }
.btn-confirm { padding: 13px 24px; background: #52c41a; color: #fff; border: none; border-radius: 8px; cursor: pointer; margin-left: auto; }
.page-loading { display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 300px; gap: 16px; }
.loading-spinner { width: 36px; height: 36px; border: 3px solid #f0f0f0; border-top-color: #409eff; border-radius: 50%; animation: spin 0.8s linear infinite; }
</style>
