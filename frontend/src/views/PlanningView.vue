<template>
  <div class="planning-view">
    <div v-if="pageLoading" class="page-loading">
      <div class="loading-spinner"></div>
      <p>加载中...</p>
    </div>
    <div v-else>
    <div class="sub-tabs">
      <button :class="{ active: activeSubTab === 'volumes' }" @click="activeSubTab = 'volumes'">卷纲</button>
      <button :class="{ active: activeSubTab === 'chapter_plan' }" @click="activeSubTab = 'chapter_plan'">章节规划</button>
      <button :class="{ active: activeSubTab === 'chapter_plan' }" @click="activeSubTab = 'chapter_plan'">章节细纲</button>
      <button :class="{ active: activeSubTab === 'scene_design' }" @click="activeSubTab = 'scene_design'">场景设计</button>
    </div>
    <div v-if="activeSubTab === 'volumes'" class="sub-pane">
      <h4>卷纲设计</h4>
      <p class="tip">规划整部小说的卷结构，每卷包含核心冲突与字数目标</p>
      <div class="form-group">
        <label>参考全书大纲</label>
        <div class="context-hint" v-if="upstreamData">{{ upstreamData }}</div>
        <div class="context-hint empty" v-else>暂无全书大纲数据，建议先完成M9全书大纲</div>
      </div>
      <div class="form-group">
        <label>卷数量</label>
        <select v-model="form.volumeCount" class="form-select">
          <option value="3">3卷</option>
          <option value="5">5卷</option>
          <option value="7">7卷</option>
          <option value="10">10卷</option>
        </select>
      </div>
      <div class="form-group">
        <label>每卷章节数</label>
        <input v-model.number="form.chaptersPerVolume" type="number" min="5" max="50" class="form-input" />
      </div>
      <div class="form-group">
        <label>每卷核心主题</label>
        <textarea v-model="form.themes" rows="4" placeholder="每行一个主题&#10;成长&#10;复仇&#10;守护&#10;终极对决" class="form-textarea"></textarea>
      </div>
      <div v-if="volumeList.length" class="result-list">
        <div v-for="(v, idx) in volumeList" :key="idx" class="plan-card" tabindex="0">
          <div class="plan-card-header">
            <span class="plan-num">第{{ idx + 1 }}卷</span>
            <span class="plan-title">{{ v.name || v.title }}</span>
          </div>
          <p class="plan-summary">{{ v.summary }}</p>
          <div class="plan-meta"><span>字数目标: {{ v.target_words || v.wordCount }}w</span><span>章节数: {{ v.chapter_count || v.chapterCount }}</span></div>
        </div>
      </div>
    </div>

    <div v-else-if="moduleKey === 'chapter_plan'" class="sub-pane">
      <h4>章节规划</h4>
      <p class="tip">规划每章标题、字数目标、节奏钩子</p>
      <div class="form-group">
        <label>参考剧情节点</label>
        <div class="context-hint" v-if="upstreamData">{{ upstreamData }}</div>
        <div class="context-hint empty" v-else>暂无故事架构数据，建议先完成故事框架设计</div>
      </div>
      <div class="form-group">
        <label>总章节数</label>
        <input v-model.number="form.totalChapters" type="number" min="10" max="200" class="form-input" />
      </div>
      <div class="form-group">
        <label>平均字数/章</label>
        <input v-model.number="form.wordsPerChapter" type="number" min="2000" max="10000" class="form-input" />
      </div>
      <div class="form-group">
        <label>节奏模式</label>
        <select v-model="form.rhythmMode" class="form-select">
          <option value="3chapter">3章一爽(网文经典)</option>
          <option value="5chapter">5章一循环(中节奏)</option>
          <option value="loose">自由节奏(文学向)</option>
        </select>
      </div>
      <div v-if="chapterPlans.length" class="result-table">
        <table class="chapter-table">
          <thead><tr><th>章</th><th>标题</th><th>字数</th><th>节奏</th><th>钩子</th></tr></thead>
          <tbody>
            <tr v-for="(ch, idx) in chapterPlans" :key="idx">
              <td>{{ idx + 1 }}</td>
              <td>{{ ch.title }}</td>
              <td>{{ ch.target_words || ch.wordCount }}w</td>
              <td>{{ ch.pace || '-' }}</td>
              <td>{{ ch.hook_type || ch.hookType || '-' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div v-else-if="moduleKey === 'chapter_plan'" class="sub-pane">
      <h4>章节细纲</h4>
      <p class="tip">为每个章节写出场景、情绪、核心动作的详细大纲</p>
      <div class="form-group">
        <label>参考章节规划</label>
        <div class="context-hint" v-if="upstreamData">{{ upstreamData }}</div>
        <div class="context-hint empty" v-else>暂无章节规划数据，建议先完成M12章节规划</div>
      </div>
      <div class="form-group">
        <label>细纲密度</label>
        <select v-model="form.detailLevel" class="form-select">
          <option value="coarse">粗纲(每章3-5句)</option>
          <option value="medium">中纲(每章5-8句)</option>
          <option value="fine">细纲(每章8-15句)</option>
        </select>
      </div>
      <div v-if="moduleKey === 'chapter_plan'" class="form-group">
        <label>章节总数</label>
        <input v-model.number="form.totalChapters" type="number" min="1" max="1000" />
      </div>
      <div class="form-group">
        <label>重点关注章节（可选）</label>
        <input v-model="form.focusChapters" placeholder="如：1,3,5-8,20（留空则全量生成）" class="form-input" />
      </div>
      <div v-if="chapterOutlines.length" class="result-list">
        <div v-for="(o, idx) in chapterOutlines" :key="idx" class="plan-card">
          <div class="plan-card-header"><span class="plan-num">第{{ idx + 1 }}章</span><span class="plan-title">{{ o.title }}</span></div>
          <div class="outline-scenes">
            <div v-for="(s, si) in o.scenes" :key="si" class="scene-item"><span class="scene-num">场景{{ si + 1 }}</span><span class="scene-summary">{{ s }}</span></div>
          </div>
          <div class="outline-emotion" v-if="o.emotionCurve"><span>情绪曲线:</span><EmotionCurveChart :curve="o.emotionCurve" :height="30" /></div>
        </div>
      </div>
    </div>

    <div v-else-if="moduleKey === 'scene_design'" class="sub-pane">
      <h4>场景设计</h4>
      <p class="tip">为每个章节设计具体场景：环境氛围、出场人物、关键事件</p>
      <div class="form-group">
        <label>章节选择</label>
        <select v-model="sceneForm.chapterNo" class="form-select">
          <option v-for="i in 20" :key="i" :value="i">第 {{ i }} 章</option>
        </select>
      </div>
      <div class="form-group">
        <label>参考章节大纲</label>
        <div class="context-hint" v-if="upstreamData">{{ upstreamData }}</div>
        <div class="context-hint empty" v-else>暂无章节大纲数据</div>
      </div>
      <div class="form-group">
        <label>场景名称</label>
        <input v-model="sceneForm.sceneName" placeholder="如：山门拜师、密林遇袭..." class="form-input" />
      </div>
      <div class="form-group">
        <label>场景氛围</label>
        <select v-model="sceneForm.atmosphere" class="form-select">
          <option value="tense">紧张刺激</option>
          <option value="calm">平和日常</option>
          <option value="mysterious">神秘诡异</option>
          <option value="epic">史诗恢弘</option>
          <option value="emotional">情感浓烈</option>
          <option value="humorous">轻松诙谐</option>
        </select>
      </div>
      <div class="form-group">
        <label>出场人物</label>
        <input v-model="sceneForm.characters" placeholder="如：主角、师兄李青、长老王玄..." class="form-input" />
      </div>
      <div class="form-group">
        <label>关键事件概要</label>
        <textarea v-model="sceneForm.event" rows="4" placeholder="描述本场景发生的核心事件..." class="form-textarea" />
      </div>
      <div class="form-group">
        <label>场景钩子（悬念）</label>
        <input v-model="sceneForm.hook" placeholder="本场景结尾留下的悬念..." class="form-input" />
      </div>
      <div v-if="sceneDesigns.length" class="result-list">
        <div v-for="(s, idx) in sceneDesigns" :key="idx" class="plan-card">
          <div class="plan-card-header">
            <span class="plan-num">场景{{ idx + 1 }}</span>
            <span class="plan-title">{{ s.name || s.sceneName }}</span>
          </div>
          <p class="plan-summary">{{ s.event || s.description }}</p>
          <div class="plan-meta">
            <span v-if="s.atmosphere">氛围: {{ s.atmosphere }}</span>
            <span v-if="s.characters">人物: {{ s.characters }}</span>
          </div>
        </div>
      </div>
    </div>

    <div class="actions">
      <button @click="generate" :disabled="generating" class="btn-primary">
        <span v-if="generating" class="spinner"></span>{{ generating ? '生成中...' : 'AI生成' }}
      </button>
      <button @click="proceed" class="btn-confirm">确认,下一步</button>
    </div>

    <div v-if="isOffline" class="offline-badge">当前数据来自离线模板 (非AI生成) <button @click="generate" class="btn-link">重新AI生成</button></div>

    <div v-if="error" class="error-box">
      <p>{{ error }}</p>
      <button @click="useOfflineMode" class="btn btn-ghost btn-sm">使用离线模板</button>
    </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import EmotionCurveChart from '../components/EmotionCurveChart.vue'
import { saveModuleData, getAllModuleData, getModuleData } from '../api/v2'
import { useGeneration } from '../composables/useGeneration'
import { useToastStore } from '../stores/toast'
import { setupConfirm } from '../composables/useConfirm'
import { setupErrorBar } from '../composables/useErrorBar'
import * as v2Api from '../api/v2'
import { useAutoSave } from '../composables/useAutoSave'

const props = defineProps<{ projectId: string; currentModule: string }>()
const emit = defineEmits<{ complete: [data: any] }>()
const gen = useGeneration(props.currentModule, '规划内容')
const confirm = setupConfirm()
const errorBar = setupErrorBar()
const toast = useToastStore()
const pageLoading = ref(true)

const moduleKey = computed(() => props.currentModule)
const activeSubTab = ref(props.currentModule === 'chapter_plan' ? 'chapter_plan' : (props.currentModule === 'volumes' ? 'volumes' : 'chapter_plan'))
const generating = ref(false)
const error = ref('')
const upstreamData = ref('')
const isOffline = ref(false)
const upstreamRawData = ref<any>({})

const formDefaults: Record<string, any> = {
  volumes: { volumeCount: '5', chaptersPerVolume: 20, themes: '' },
  chapter_plan: { totalChapters: 100, wordsPerChapter: 3000, rhythmMode: '3chapter', detailLevel: 'medium', focusChapters: '' },
  scene_design: { chapterNo: 1, sceneName: '', atmosphere: 'tense', characters: '', event: '', hook: '' },
}

const form = ref({ ...(formDefaults[props.currentModule] || formDefaults.volumes) })

watch(moduleKey, (key) => {
  form.value = { ...formDefaults[key] }
  if (key === 'scene_design') {
    form.value = sceneForm
  }
})

const volumeList = ref<any[]>([])
const chapterPlans = ref<any[]>([])
const chapterOutlines = ref<any[]>([])
const sceneDesigns = ref<any[]>([])
const sceneForm = reactive({ chapterNo: 1, sceneName: '', atmosphere: 'tense', characters: '', event: '', hook: '' })

const planningData = () => {
   const key = activeSubTab.value
   if (key === 'volumes') return { volumes: volumeList.value, form: form.value }
   if (key === 'chapter_plan') return { chapterPlans: chapterPlans.value, form: form.value }
   if (key === 'chapter_plan') return { chapterOutlines: chapterOutlines.value, form: form.value }
   if (key === 'scene_design') return { sceneDesigns: sceneDesigns.value, form: sceneForm }
   return { volumes: volumeList.value, chapterPlans: chapterPlans.value, chapterOutlines: chapterOutlines.value, form: form.value }
}
const resultPayload = computed(planningData)
const { scheduleSave } = useAutoSave({
   dataRef: planningData,
   saveFn: async (data) => {
      try { await v2Api.saveModuleData(props.projectId, activeSubTab.value || 'volumes', data) } catch (_e) { /* silent */ }
   },
   debounce: 1500,
   storageKey: `planning_${activeSubTab.value}_${props.projectId}`,
   projectId: props.projectId,
   moduleName: activeSubTab.value || 'volumes',
})
watch([volumeList, chapterPlans, chapterOutlines, sceneDesigns, form], () => { scheduleSave() }, { deep: true })

onMounted(async () => {
  try {
    const saved = await getModuleData(props.projectId, activeSubTab.value)
    const raw = saved?.data
    if (raw) {
      if (Array.isArray(raw)) {
        if (activeSubTab.value === 'volumes') { volumeList.value = raw; return }
        if (activeSubTab.value === 'chapter_plan') { chapterPlans.value = raw; return }
        if (activeSubTab.value === 'chapter_plan') { chapterOutlines.value = raw; return }
      }
      if (raw.form || raw.volumes || raw.chapterPlans || raw.chapterOutlines) {
        if (raw.form) Object.assign(form.value, raw.form)
        if (raw.volumes) volumeList.value = raw.volumes
        if (raw.chapterPlans) chapterPlans.value = raw.chapterPlans
        if (raw.chapterOutlines) chapterOutlines.value = raw.chapterOutlines
        if (raw.sceneDesigns) sceneDesigns.value = raw.sceneDesigns
        if (raw.upstreamData) upstreamData.value = raw.upstreamData
        return
      }
    }
    const allData = await getAllModuleData(props.projectId)
    const modules = allData?.modules || {}
    upstreamRawData.value = modules
    if (activeSubTab.value === 'volumes') {
      const sa = modules['architecture']
      if (sa) {
        const title = sa.outline?.title || sa.story?.oneLiner || ''
        const theme = sa.outline?.theme || sa.story?.theme || ''
        upstreamData.value = `已加载故事架构: ${title || '未命名'}`
        if (!form.value.themes && (theme || sa.story?.theme)) {
          form.value.themes = (theme || sa.story?.theme)
        }
      }
    } else if (activeSubTab.value === 'chapter_plan') {
      const sa = modules['architecture']
      const pn = sa?.plot_nodes
      upstreamData.value = (pn && pn.length) ? `已加载${pn.length}个剧情节点` : ''
    } else if (activeSubTab.value === 'chapter_plan') {
      const plans = modules['chapter_plan']
      upstreamData.value = plans ? `已加载章节规划数据` : ''
    } else if (activeSubTab.value === 'scene_design') {
      const outlines = modules['chapter_plan']
      upstreamData.value = outlines ? `已加载章节细纲数据` : ''
    }
  } catch (_e) { /* ignore */ } finally { pageLoading.value = false }
})

async function proceed() {
  const ok = await confirm.confirm({
    message: '确定进入下一步？',
    detail: '确认后将保存规划数据并进入下一模块',
    type: 'info',
  })
  if (!ok) return
  try {
    await v2Api.saveModuleData(props.projectId, activeSubTab.value || 'volumes', resultPayload.value)
  } catch (e) {
    toast.error('保存规划数据失败，请重试')
    return
  }
  emit('complete', resultPayload.value)
}

async function generate() {
  generating.value = true
  gen.begin()
  error.value = ''
  isOffline.value = false
  try {
    const key = activeSubTab.value
    const modules = upstreamRawData.value
    if (key === 'volumes') {
      const sa = modules['architecture'] || {}
      const outline = sa.outline || sa.story || {}
      const count = parseInt(form.value.volumeCount) || 5
      const result = await v2Api.generateVolumes(props.projectId, count, outline).catch((e) => { console.error('[PlanningView] generateVolumes error:', e); return null }) as any
      const items = result?.volumes || (Array.isArray(result) ? result : (result ? [result] : []))
      volumeList.value = items
      if (!items.length) useOfflineMode()
      else await saveModuleData(props.projectId, 'volumes', { volumes: volumeList.value, form: form.value })
    } else if (key === 'chapter_plan') {
      const sa = modules['architecture'] || {}
      const outline = sa.outline || sa.story || {}
      const plotNodesData = sa.plot_nodes || []
      const result = await v2Api.planChapters(
        props.projectId, outline, plotNodesData,
        form.value.wordsPerChapter || 3000,
      ).catch(() => null)
      chapterPlans.value = result ? (Array.isArray(result) ? result : (result.chapters || [])) : []
      if (!chapterPlans.value.length) useOfflineMode()
      else await saveModuleData(props.projectId, 'chapter_plan', { chapterPlans: chapterPlans.value, form: form.value })
    } else if (key === 'chapter_plan') {
      const chapterPlansData = modules['chapter_plan'] || {}
      const total = form.value.totalChapters || 10
      const result = await v2Api.generateChapterOutlines(props.projectId, total, chapterPlansData)
      const items = (result as any).outlines || (result as any).chapters || (result as any).items || []
      chapterOutlines.value = items
      await saveModuleData(props.projectId, 'chapter_plan', { chapterOutlines: chapterOutlines.value, form: form.value })
    } else if (key === 'scene_design') {
      const chapterNo = sceneForm.chapterNo || 1
      const chapterOutline = {
        chapterNo,
        sceneName: sceneForm.sceneName,
        atmosphere: sceneForm.atmosphere,
        characters: sceneForm.characters,
        event: sceneForm.event,
        hook: sceneForm.hook,
      }
      const result = await v2Api.designScenes(props.projectId, chapterOutline).catch(() => null)
      sceneDesigns.value = result ? (Array.isArray(result) ? result : (result.scenes || [result])) : []
      if (!sceneDesigns.value.length) useOfflineMode()
      else await saveModuleData(props.projectId, 'scene_design', { sceneDesigns: sceneDesigns.value, form: sceneForm })
    }
  } catch (e: any) {
    errorBar.showError(e, () => generate())
    useOfflineMode()
  } finally {
    generating.value = false
    if (!error.value) gen.end()
    else gen.fail(error.value)
  }
}

function useOfflineMode() {
  toast.warning('AI生成不可用，已使用离线模板数据，可稍后重新生成')
  isOffline.value = true
  const key = activeSubTab.value
  if (key === 'volumes') {
    const themes = form.value.themes?.split('\n').filter(Boolean) || []
    const count = parseInt(form.value.volumeCount) || 5
    volumeList.value = Array.from({ length: count }, (_, i) => ({
      name: themes[i] || `第${i + 1}卷`,
      title: themes[i] || `第${i + 1}卷`,
      summary: `围绕"${themes[i] || '核心冲突'}"展开的主要矛盾与发展`,
      target_words: (form.value.chaptersPerVolume || 20) * 3,
      chapter_count: form.value.chaptersPerVolume || 20,
    }))
  } else if (key === 'chapter_plan') {
    chapterPlans.value = Array.from({ length: Math.min(form.value.totalChapters || 100, 10) }, (_, i) => ({
      title: `第${i + 1}章`,
      target_words: form.value.wordsPerChapter || 3000,
      pace: i % 3 === 0 ? '高' : i % 3 === 1 ? '中' : '低',
      hook_type: i % 4 === 0 ? '悬念' : i % 4 === 1 ? '爽点' : i % 4 === 2 ? '反转' : '铺垫',
    }))
  } else if (key === 'chapter_plan') {
    const density = form.value.detailLevel === 'coarse' ? 3 : form.value.detailLevel === 'medium' ? 6 : 10
    chapterOutlines.value = Array.from({ length: 3 }, (_, i) => ({
      title: `第${i + 1}章大纲`,
      scenes: Array.from({ length: density }, (_, si) => `场景${si + 1}：待细化`),
      emotionCurve: Array.from({ length: 10 }, (_, j) => Math.sin(j / 1.5 + i) * 40 + 50),
    }))
  }
}
</script>

<style scoped>
.planning-view { max-width: 1100px; }
.sub-tabs { display: flex; gap: 4px; margin-bottom: 18px; border-bottom: 2px solid #eee; }
.sub-tabs button { padding: 10px 18px; border: none; background: none; cursor: pointer; font-size: 14px; color: #888; border-bottom: 2px solid transparent; margin-bottom: -2px; transition: all .2s; }
.sub-tabs button:hover { color: #555; }
.sub-tabs button.active { color: var(--primary); border-bottom-color: var(--primary); font-weight: 600; }
.sub-pane { background: #fff; border-radius: 14px; padding: 24px; box-shadow: 0 2px 12px rgba(0,0,0,.05); }
.sub-pane h4 { font-size: 20px; margin: 0 0 6px; }
.tip { color: #888; margin-bottom: 18px; font-size: 14px; }
.context-hint { padding: 10px 14px; background: #f0f8ff; border: 1px solid #d4eaff; border-radius: 8px; font-size: 13px; color: #4a90d9; margin-bottom: 14px; }
.context-hint.empty { background: #fff8e1; border-color: #ffe082; color: #f57c00; }
.form-group { margin-bottom: 14px; }
.form-group label { display: block; font-weight: 600; margin-bottom: 6px; font-size: 14px; color: #555; }
.form-select, .form-input { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 8px; font-size: 14px; }
.form-textarea { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 8px; font-size: 14px; resize: vertical; font-family: inherit; }
.result-list { margin-top: 20px; }
.plan-card { border: 1px solid #eee; border-radius: 10px; padding: 14px; margin-bottom: 10px; }
.plan-card-header { display: flex; align-items: center; gap: 10px; margin-bottom: 6px; }
.plan-num { font-size: 14px; color: var(--primary); font-weight: 600; }
.plan-title { font-weight: 600; font-size: 16px; }
.plan-summary { font-size: 14px; color: #666; line-height: 1.6; margin: 0 0 6px; }
.plan-meta { display: flex; gap: 16px; font-size: 13px; color: #999; }
.node-header { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
.node-num { font-size: 13px; background: #e8f4fd; color: var(--primary); padding: 1px 6px; border-radius: 4px; }
.node-title { font-weight: 600; font-size: 16px; }
.node-type { font-size: 13px; color: #888; margin-left: auto; }
.node-actors { display: flex; gap: 4px; margin-top: 6px; }
.actor-tag { font-size: 12px; padding: 1px 6px; background: #f0f0f0; border-radius: 4px; }
.chapter-table { width: 100%; border-collapse: collapse; font-size: 14px; }
.chapter-table th, .chapter-table td { border: 1px solid #eee; padding: 6px 8px; text-align: left; }
.chapter-table th { background: #f9f9f9; font-weight: 600; }
.outline-scenes { display: flex; flex-direction: column; gap: 4px; margin: 8px 0; }
.scene-item { display: flex; gap: 6px; font-size: 13px; }
.scene-num { color: var(--primary); flex-shrink: 0; }
.outline-emotion { display: flex; align-items: center; gap: 8px; margin-top: 6px; font-size: 13px; color: #888; }
.actions { display: flex; gap: 12px; margin-top: 18px; }
.btn-primary { padding: 11px 22px; background: linear-gradient(135deg, var(--primary), var(--primary-light)); color: #fff; border: none; border-radius: 8px; cursor: pointer; font-size: 14px; font-weight: 600; }
.btn-primary:disabled { opacity: 0.5; cursor: wait; }
.btn-confirm { padding: 11px 22px; background: #52c41a; color: #fff; border: none; border-radius: 8px; cursor: pointer; font-size: 14px; font-weight: 600; margin-left: auto; }
.btn { border: none; border-radius: 10px; cursor: pointer; }
.btn-sm { padding: 8px 16px; font-size: 14px; }
.btn-ghost { background: #f0f0f0; color: #555; }
.error-box { margin-top: 16px; padding: 16px; background: #fff3f3; border: 1px solid #ffcdd2; border-radius: 10px; }
.error-box p { color: #c62828; margin-bottom: 8px; }
.spinner { display: inline-block; width: 14px; height: 14px; border: 2px solid #fff; border-top-color: transparent; border-radius: 50%; animation: spin 0.8s linear infinite; margin-right: 6px; }
@keyframes spin { to { transform: rotate(360deg); } }
.page-loading { display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 300px; gap: 16px; }
.loading-spinner { width: 36px; height: 36px; border: 3px solid #f0f0f0; border-top-color: #409eff; border-radius: 50%; animation: spin 0.8s linear infinite; }
</style>
