<template>
  <div class="planning-view">
    <div class="sub-tabs">
      <div v-for="t in subTabs" :key="t.key" class="sub-tab" :class="{ active: activeSubTab === t.key }" @click="activeSubTab = t.key">{{ t.label }}</div>
    </div>

    <div class="sub-content">
      <div v-if="activeSubTab === 'volumes'" class="sub-pane">
        <h4>卷纲</h4>
        <div v-for="(v, idx) in volumeList" :key="idx" class="plan-card">
          <div class="plan-card-header">
            <span class="plan-num">第{{ idx + 1 }}卷</span>
            <span class="plan-title">{{ v.title }}</span>
            <span class="plan-status" :class="v.status">{{ v.status }}</span>
          </div>
          <p class="plan-summary">{{ v.summary }}</p>
          <div class="plan-meta">
            <span>字数目标: {{ v.wordCount }}w</span>
            <span>章节数: {{ v.chapterCount }}</span>
          </div>
        </div>
      </div>

      <div v-if="activeSubTab === 'nodes'" class="sub-pane">
        <h4>剧情节点</h4>
        <div v-for="(n, idx) in plotNodes" :key="idx" class="plan-card">
          <div class="node-header">
            <span class="node-num">节点{{ idx + 1 }}</span>
            <span class="node-title">{{ n.title }}</span>
            <span class="node-type">{{ n.type }}</span>
          </div>
          <p>{{ n.description }}</p>
          <div class="node-actors">
            <span v-for="a in n.actors" :key="a" class="actor-tag">{{ a }}</span>
          </div>
        </div>
      </div>

      <div v-if="activeSubTab === 'chapterPlan'" class="sub-pane">
        <h4>章节规划</h4>
        <table class="chapter-table">
          <thead><tr><th>章</th><th>标题</th><th>字数</th><th>节奏</th><th>钩子</th></tr></thead>
          <tbody>
            <tr v-for="(ch, idx) in chapterPlans" :key="idx">
              <td>{{ idx + 1 }}</td>
              <td>{{ ch.title }}</td>
              <td>{{ ch.wordCount }}w</td>
              <td>{{ ch.pace }}</td>
              <td>{{ ch.hookType }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-if="activeSubTab === 'outline'" class="sub-pane">
        <h4>章节细纲</h4>
        <div v-for="(o, idx) in chapterOutlines" :key="idx" class="plan-card">
          <div class="plan-card-header">
            <span class="plan-num">第{{ idx + 1 }}章</span>
            <span class="plan-title">{{ o.title }}</span>
          </div>
          <div class="outline-scenes">
            <div v-for="(s, si) in o.scenes" :key="si" class="scene-item">
              <span class="scene-num">场景{{ si + 1 }}</span>
              <span class="scene-summary">{{ s }}</span>
            </div>
          </div>
          <div class="outline-emotion">
            <span>情绪曲线:</span>
            <EmotionCurveChart :curve="o.emotionCurve" :height="30" />
          </div>
        </div>
      </div>
    </div>

    <div class="actions">
      <button @click="generate" :disabled="generating" class="btn-primary">{{ generating ? '生成中...' : '生成规划' }}</button>
      <button @click="confirm" class="btn-confirm">确认规划,下一步</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { usePlanningStore } from '../stores/planning'
import EmotionCurveChart from '../components/EmotionCurveChart.vue'

const props = defineProps<{ projectId: string; currentModule: string }>()
const emit = defineEmits<{ complete: [data: any] }>()
const planning = usePlanningStore()
const generating = ref(false)

const subTabs = [
  { key: 'volumes', label: '卷纲' },
  { key: 'nodes', label: '剧情节点' },
  { key: 'chapterPlan', label: '章节规划' },
  { key: 'outline', label: '章节细纲' },
]
const activeSubTab = ref(props.currentModule === 'volumes' ? 'volumes' : props.currentModule === 'plotNodes' ? 'nodes' : props.currentModule === 'chapterPlan' ? 'chapterPlan' : 'outline')

const volumeList = ref<any[]>([])
const plotNodes = ref<any[]>([])
const chapterPlans = ref<any[]>([])
const chapterOutlines = ref<any[]>([])

async function generate() {
  generating.value = true
  try {
    const result = await planning.generatePlanning(props.projectId)
    volumeList.value = result.volumes || []
    plotNodes.value = result.plotNodes || []
    chapterPlans.value = result.chapterPlans || []
    chapterOutlines.value = result.chapterOutlines || []
  } finally {
    generating.value = false
  }
}

async function confirm() {
  await planning.savePlanning(props.projectId, {
    volumes: volumeList.value,
    plotNodes: plotNodes.value,
    chapterPlans: chapterPlans.value,
    chapterOutlines: chapterOutlines.value,
  })
  emit('complete', {})
}
</script>

<style scoped>
.planning-view { max-width: 900px; margin: 0 auto; }
.sub-tabs { display: flex; gap: 2px; margin-bottom: 0; }
.sub-tab { padding: 8px 16px; background: #f5f5f5; border: 1px solid #ddd; border-bottom: none; border-radius: 6px 6px 0 0; cursor: pointer; font-size: 12px; font-weight: 500; }
.sub-tab.active { background: #fff; color: var(--primary); }
.sub-content { background: #fff; border: 1px solid #eee; border-radius: 0 6px 6px 6px; padding: 20px; min-height: 300px; }
.sub-pane h4 { margin: 0 0 14px; font-size: 15px; }
.plan-card { border: 1px solid #eee; border-radius: 6px; padding: 14px; margin-bottom: 10px; }
.plan-card-header { display: flex; align-items: center; gap: 10px; margin-bottom: 6px; }
.plan-num { font-size: 12px; color: var(--primary); font-weight: 600; }
.plan-title { font-weight: 600; font-size: 14px; }
.plan-status { font-size: 11px; padding: 1px 6px; border-radius: 3px; margin-left: auto; }
.plan-status.draft { background: #f0f0f0; color: #888; }
.plan-status.done { background: #f6ffed; color: #52c41a; }
.plan-summary { font-size: 13px; color: #666; line-height: 1.6; margin: 0 0 8px; }
.plan-meta { display: flex; gap: 16px; font-size: 12px; color: #999; }
.node-header { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
.node-num { font-size: 11px; background: #e8f4fd; color: var(--primary); padding: 1px 6px; border-radius: 3px; }
.node-title { font-weight: 600; font-size: 14px; }
.node-type { font-size: 11px; color: #888; margin-left: auto; }
.node-actors { display: flex; gap: 4px; margin-top: 6px; }
.actor-tag { font-size: 11px; padding: 1px 6px; background: #f0f0f0; border-radius: 3px; }
.chapter-table { width: 100%; border-collapse: collapse; font-size: 12px; }
.chapter-table th, .chapter-table td { border: 1px solid #eee; padding: 6px 8px; text-align: left; }
.chapter-table th { background: #f9f9f9; font-weight: 600; }
.outline-scenes { display: flex; flex-direction: column; gap: 4px; margin: 8px 0; }
.scene-item { display: flex; gap: 6px; font-size: 12px; }
.scene-num { color: var(--primary); flex-shrink: 0; }
.outline-emotion { display: flex; align-items: center; gap: 8px; margin-top: 6px; font-size: 12px; color: #888; }
.actions { display: flex; gap: 10px; margin-top: 16px; }
.btn-primary { padding: 10px 24px; background: var(--primary); color: #fff; border: none; border-radius: 6px; cursor: pointer; }
.btn-primary:disabled { opacity: 0.5; cursor: wait; }
.btn-confirm { padding: 10px 24px; background: #52c41a; color: #fff; border: none; border-radius: 6px; cursor: pointer; margin-left: auto; }
</style>
