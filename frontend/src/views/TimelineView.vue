<template>
  <div class="timeline-view">
    <div class="section">
      <h3>时间线构建</h3>
      <p class="section-desc">基于世界观历史与故事事件，构建完整的历史时间线</p>

      <div v-if="historyEvents.length" class="event-source">
        <h4>历史事件来源</h4>
        <div v-for="(evt, i) in historyEvents" :key="i" class="event-item">
          <span class="event-era">{{ evt.era || evt.period || '未知时代' }}</span>
          <span class="event-desc">{{ evt.description || evt.event || evt.name }}</span>
        </div>
      </div>

      <div class="actions">
        <button @click="buildTimeline" :disabled="building" class="btn-primary">
          <span v-if="building" class="spinner"></span>{{ building ? '构建中...' : 'AI构建时间线' }}
        </button>
        <button @click="useWorldHistory" class="btn-secondary">使用世界观历史</button>
      </div>
    </div>

    <div v-if="timeline.events?.length" class="section">
      <h3>时间线预览</h3>
      <TimelineChart :events="timeline.events" :editable="true" @reorder="onReorder" />
    </div>

    <div v-if="error" class="error-box">{{ error }}</div>

    <div v-if="timeline.events?.length" class="section">
      <button @click="confirm" class="btn-confirm">确认时间线,下一步</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { buildTimeline as buildTimelineApi, saveTimeline, getAllModuleData } from '../api/v2'
import TimelineChart from '../components/TimelineChart.vue'
import { useGeneration } from '../composables/useGeneration'

const props = defineProps<{ projectId: string }>()
const emit = defineEmits<{ complete: [data: any] }>()
const gen = useGeneration('timeline', '时间线')

const building = ref(false)
const error = ref('')
const historyEvents = ref<any[]>([])
const timeline = reactive<any>({ events: [] })

async function buildTimeline() {
  building.value = true
  error.value = ''
  gen.begin(1, '正在构建时间线...')
  try {
    const result = await buildTimelineApi(props.projectId, { events: historyEvents.value }, historyEvents.value)
    if (result) {
      if (result.events) timeline.events = result.events
      else if (Array.isArray(result)) timeline.events = result
      else timeline.events = []
    }
    gen.end()
  } catch (e: any) {
    error.value = e?.message || '构建失败'
    gen.fail(error.value)
  } finally {
    building.value = false
  }
}

function useWorldHistory() {
  if (historyEvents.value.length) {
    timeline.events = historyEvents.value.map((e: any) => ({
      era: e.era || e.period,
      title: e.name || e.event || e.description,
      description: e.description || e.event,
      year: e.year || e.time,
    }))
  }
}

function onReorder(newEvents: any[]) {
  timeline.events = newEvents
}

async function confirm() {
  try {
    await saveTimeline(props.projectId, { events: timeline.events })
  } catch (_e) { /* ignore */ }
  emit('complete', { events: timeline.events })
}

onMounted(async () => {
  try {
    const allData = await getAllModuleData(props.projectId)
    const world = allData?.modules?.['world']
    if (world?.history) {
      historyEvents.value = Array.isArray(world.history) ? world.history : []
    }
    const story = allData?.modules?.['story_architecture']
    if (story?.plotEvents) {
      historyEvents.value.push(...story.plotEvents)
    }
  } catch (_e) { /* ignore */ }
})
</script>

<style scoped>
.timeline-view { max-width: 1040px; margin: 0 auto; }
.section { background: #fff; border: 1px solid #eee; border-radius: 10px; padding: 26px; margin-bottom: 21px; }
.section h3 { margin: 0 0 12px; font-size: 21px; }
.section-desc { font-size: 13px; color: #888; margin: -6px 0 14px; }
.event-source { margin-bottom: 20px; }
.event-source h4 { font-size: 15px; margin-bottom: 10px; }
.event-item { display: flex; gap: 12px; padding: 6px 0; border-bottom: 1px solid #f0f0f0; }
.event-era { font-weight: 600; color: var(--primary); min-width: 100px; }
.event-desc { color: #666; }
.actions { display: flex; gap: 13px; margin: 20px 0; }
.btn-primary { padding: 13px 24px; background: var(--primary); color: #fff; border: none; border-radius: 8px; cursor: pointer; font-size: 16px; }
.btn-primary:disabled { opacity: 0.5; cursor: wait; }
.btn-secondary { padding: 13px 20px; background: #f5f5f5; border: 1px solid #ddd; border-radius: 8px; cursor: pointer; }
.btn-confirm { width: 100%; padding: 13px; background: #52c41a; color: #fff; border: none; border-radius: 8px; font-size: 20px; cursor: pointer; }
.spinner { display: inline-block; width: 12px; height: 12px; border: 2px solid #fff; border-top-color: transparent; border-radius: 50%; animation: spin 0.8s linear infinite; margin-right: 4px; }
@keyframes spin { to { transform: rotate(360deg); } }
.error-box { color: #e74c3c; background: #fff1f0; border-radius: 8px; padding: 12px; margin-bottom: 16px; }
</style>
