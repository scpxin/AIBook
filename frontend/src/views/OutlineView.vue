<template>
  <div class="outline-view">
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
        <button @click="prefillFromStory" class="btn-secondary">从故事框架提取</button>
      </div>
    </div>

    <div v-if="result.title || result.theme" class="section">
      <h3>大纲预览</h3>
      <div class="outline-card">
        <div v-if="result.title" class="outline-title">{{ result.title }}</div>
        <div class="outline-meta">
          <span v-if="result.theme" class="meta-tag">主题：{{ result.theme }}</span>
          <span v-if="result.wordCount" class="meta-tag">字数：{{ formatWords(result.wordCount) }}</span>
        </div>
        <div v-if="result.conflict" class="outline-section">
          <h4>核心冲突</h4><p>{{ result.conflict }}</p>
        </div>
        <div v-if="result.growthRoute" class="outline-section">
          <h4>主角成长路线</h4>
          <div class="growth-timeline">
            <span v-for="(step, idx) in growthSteps" :key="idx" class="growth-step">
              {{ step }}<span v-if="idx < growthSteps.length - 1" class="arrow">→</span>
            </span>
          </div>
        </div>
        <div v-if="result.volumes?.length" class="outline-section">
          <h4>卷纲</h4>
          <div class="volume-grid">
            <div v-for="(v, idx) in result.volumes" :key="idx" class="volume-card">
              <span class="volume-num">第{{ idx + 1 }}卷</span>
              <span class="volume-title">{{ v.title || v.name }}</span>
              <p>{{ v.summary }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="error" class="error-box">{{ error }}</div>

    <div v-if="result.title || result.theme" class="section">
      <button @click="confirm" class="btn-confirm">确认大纲,下一步</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, computed, onMounted } from 'vue'
import { generateMasterOutline, saveMasterOutline, getModuleData, getAllModuleData, saveModuleData } from '../api/v2'
import { useGeneration } from '../composables/useGeneration'

const props = defineProps<{ projectId: string }>()
const emit = defineEmits<{ complete: [data: any] }>()
const gen = useGeneration('outline', '全书大纲')

const generating = ref(false)
const error = ref('')
const form = reactive({ title: '', conflict: '', wordCount: '1500000', growthRoute: '' })
const result = reactive<any>({ title: '', theme: '', conflict: '', wordCount: '', growthRoute: '', volumes: [] })

const growthSteps = computed(() =>
  (result.growthRoute || form.growthRoute).split(/[→\n,，]/).map((s: string) => s.trim()).filter(Boolean)
)

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
      if (r.volumes?.length) result.volumes = r.volumes
    }
    gen.end()
  } catch (e: any) {
    error.value = e?.message || '生成失败，可手动填写'
    gen.fail(error.value)
  } finally {
    generating.value = false
  }
}

function prefillFromStory() {
  getModuleData(props.projectId, 'story_architecture').then((saved) => {
    const d = saved?.data
    if (d?.story) {
      if (d.story.oneLiner) form.title = d.story.oneLiner
      if (d.story.coreConflict) form.conflict = d.story.coreConflict
    }
    if (d?.outline) {
      if (d.outline.title) form.title = d.outline.title
      if (d.outline.conflict) form.conflict = d.outline.conflict
      if (d.outline.growthRoute) form.growthRoute = d.outline.growthRoute
    }
  }).catch(() => {})
}

async function confirm() {
  try {
    await saveMasterOutline(props.projectId, result)
    await saveModuleData(props.projectId, 'story_architecture', {
      module_data: { outline: { ...result } },
    })
  } catch (_e) { /* ignore */ }
  emit('complete', { ...result })
}

onMounted(async () => {
  try {
    const saved = await getModuleData(props.projectId, 'story_architecture')
    if (saved?.data?.outline) {
      const o = saved.data.outline
      if (o.title) result.title = o.title
      if (o.theme) result.theme = o.theme
      if (o.conflict) result.conflict = o.conflict
      if (o.growthRoute) result.growthRoute = o.growthRoute
    }
  } catch (_e) { /* ignore */ }
})
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
</style>
