<template>
  <div class="story-arch-view">
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
        <div v-for="(v, idx) in story.volumes" :key="idx" class="volume-card">
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

    <div class="section">
      <h3>全书大纲</h3>
      <div class="form-group">
        <label>书名暂定</label>
        <input v-model="outline.title" class="form-input" placeholder="请输入书名..." />
      </div>
      <div class="form-row">
        <div class="form-group" style="flex:1">
          <label>核心冲突</label>
          <textarea v-model="outline.conflict" rows="3" class="form-textarea" placeholder="主角vs命运/社会/自我..." />
        </div>
        <div class="form-group" style="flex:1">
          <label>预计总字数</label>
          <select v-model="outline.wordCount" class="form-select">
            <option value="300000">30万字（短篇）</option>
            <option value="800000">80万字（中篇）</option>
            <option value="1500000">150万字（长篇）</option>
            <option value="3000000">300万字（超长篇）</option>
          </select>
          <label style="margin-top:10px">主角成长路线</label>
          <textarea v-model="outline.growthRoute" rows="4" class="form-textarea" placeholder="废柴→觉醒→崛起→称霸→超脱" />
        </div>
      </div>
      <div class="action-row">
         <button @click="generateOutline" :disabled="generating" class="btn btn-primary">
           <span v-if="generating" class="spinner"></span>{{ generating ? '生成中...' : 'AI生成全书大纲' }}
         </button>
      </div>
    </div>

    <div v-if="outline.title || outline.theme" class="section">
      <h3>大纲预览</h3>
      <div class="outline-card">
        <div v-if="outline.title" class="outline-title">{{ outline.title }}</div>
        <div class="outline-meta">
          <span v-if="outline.theme" class="meta-tag">主题：{{ outline.theme }}</span>
          <span v-if="outline.wordCount" class="meta-tag">字数：{{ formatWords(outline.wordCount) }}</span>
        </div>
        <div v-if="outline.conflict" class="outline-section">
          <h4>核心冲突</h4><p>{{ outline.conflict }}</p>
        </div>
        <div v-if="outline.growthRoute" class="outline-section">
          <h4>主角成长路线</h4>
          <div class="growth-timeline">
            <span v-for="(step, idx) in growthSteps" :key="idx" class="growth-step">
              {{ step }}<span v-if="idx < growthSteps.length - 1" class="arrow">→</span>
            </span>
          </div>
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
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, computed, onMounted } from 'vue'
import { generateStoryMaster, generateMasterOutline, generatePlotNodes as genPlotNodes, getModuleData, getAllModuleData, saveModuleData } from '../api/v2'
import { useGeneration } from '../composables/useGeneration'
import TimelineChart from '../components/TimelineChart.vue'

const props = defineProps<{ projectId: string }>()
const emit = defineEmits<{ complete: [data: any] }>()
const gen = useGeneration('story_architecture', '故事架构')
const generating = ref(false)
const error = ref('')
const plotNodeCount = ref(6)
const plotNodes = ref<any[]>([])

const story = reactive<any>({ oneLiner: '', theme: '', coreConflict: '', volumes: [], plotEvents: [] })
const outline = reactive({ title: '', theme: '', conflict: '', wordCount: '1500000', growthRoute: '' })

const growthSteps = computed(() =>
  outline.growthRoute.split(/[→\n,，]/).map((s: string) => s.trim()).filter(Boolean)
)

function formatWords(n: string): string {
  const num = parseInt(n); return num >= 10000 ? (num / 10000) + '万字' : n + '字'
}

function onReorderEvents(newEvents: any[]) { story.plotEvents = newEvents }

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
      if (result.theme) story.theme = story.theme || result.theme
      if (result.coreConflict) story.coreConflict = result.coreConflict
      if (result.masterStory) {
        if (result.masterStory.theme) story.theme = story.theme || result.masterStory.theme
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
    error.value = e?.message || '生成失败'
    gen.fail(error.value)
  }
  finally { generating.value = false }
}

async function generateOutline() {
  generating.value = true; error.value = ''; gen.begin()
  try {
    const allData = await getAllModuleData(props.projectId)
    const world = allData?.modules?.['world']
    const chars = allData?.modules?.['characters']
    const storySystem = {
      theme: story.theme || outline.theme,
      conflict: story.coreConflict || outline.conflict,
      protagonist: chars?.protagonist || {},
      world: world || {},
      characters: [chars?.protagonist, ...(chars?.supporting || []), ...(chars?.villains || [])].filter(Boolean),
      plot_events: story.plotEvents || [],
    }
    const result = await generateMasterOutline(props.projectId, storySystem)
    if (result) {
      const r = result as any
      if (r.title) outline.title = r.title
      if (r.theme) outline.theme = r.theme
      if (r.conflict) outline.conflict = r.conflict
      if (r.wordCount) outline.wordCount = String(r.wordCount)
      if (r.growthRoute) outline.growthRoute = r.growthRoute
      if (r.growth_route) outline.growthRoute = r.growth_route
    }
    gen.end()
  } catch (e: any) { error.value = e?.message || 'AI生成失败，可手动填写'; gen.fail(error.value) }
  finally { generating.value = false }
}

async function generatePlotNodes() {
  generating.value = true; error.value = ''; gen.begin()
  try {
    const chapterPlan = { totalChapters: 100 }
    const masterOutline = { theme: story.theme || outline.theme, conflict: story.coreConflict || outline.conflict }
    const result = await genPlotNodes(props.projectId, chapterPlan, masterOutline) as any
    plotNodes.value = Array.isArray(result) ? result : (result?.nodes || result?.plotNodes || result?.plot_nodes || [])
    gen.end()
  } catch (e: any) { error.value = e?.message || '生成失败'; gen.fail(error.value) }
  finally { generating.value = false }
}

async function confirm() {
  const data = {
    story: { ...story },
    outline: { ...outline },
    plot_nodes: plotNodes.value,
  }
  await saveModuleData(props.projectId, 'story_architecture', { module_data: data })
  emit('complete', data)
}

onMounted(async () => {
  try {
    const saved = await getModuleData(props.projectId, 'story_architecture')
    if (saved?.data) {
      const d = saved.data
      if (d.story) Object.assign(story, d.story)
      if (d.outline) Object.assign(outline, d.outline)
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
})
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
</style>
