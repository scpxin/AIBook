<template>
  <div class="story-view">
    <div class="section">
      <h3>故事总纲</h3>
      <div class="form-group">
        <label>一句话概括</label>
        <input v-model="story.oneLiner" class="form-input" placeholder="用一句话描述整个故事..." />
      </div>
      <div class="form-group">
        <label>核心冲突</label>
        <textarea v-model="story.coreConflict" class="form-textarea" rows="2" placeholder="主角面临的核心矛盾..." />
      </div>
      <div class="form-group">
        <label>主题</label>
        <input v-model="story.theme" class="form-input" placeholder="故事主题(如:复仇/成长/守护)" />
      </div>
    </div>

    <div class="section">
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
      <h3>事件时间线</h3>
      <TimelineChart :events="story.plotEvents" :editable="true" @reorder="onReorderEvents" />
    </div>

    <div class="actions">
      <button @click="generate" :disabled="generating" class="btn-primary">{{ generating ? '生成中...' : 'AI生成故事体系' }}</button>
      <button @click="confirm" class="btn-confirm">确认故事,下一步</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useStoryStore } from '../stores/story'
import TimelineChart from '../components/TimelineChart.vue'

const props = defineProps<{ projectId: string }>()
const emit = defineEmits<{ complete: [data: any] }>()
const storyStore = useStoryStore()
const generating = ref(false)

const story = reactive<any>({
  oneLiner: '',
  coreConflict: '',
  theme: '',
  volumes: [],
  plotEvents: [],
})

async function generate() {
  generating.value = true
  try {
    const result = await storyStore.generateStory(props.projectId)
    Object.assign(story, result)
  } finally {
    generating.value = false
  }
}

function onReorderEvents(newEvents: any[]) {
  story.plotEvents = newEvents
}

async function confirm() {
  await storyStore.saveStory(props.projectId, { ...story })
  emit('complete', { ...story })
}
</script>

<style scoped>
.story-view { max-width: 900px; margin: 0 auto; }
.section { background: #fff; border: 1px solid #eee; border-radius: 8px; padding: 20px; margin-bottom: 16px; }
.section h3 { margin: 0 0 12px; font-size: 16px; }
.form-group { margin-bottom: 12px; }
.form-group label { display: block; font-weight: 600; margin-bottom: 4px; font-size: 13px; color: #555; }
.form-input, .form-textarea { width: 100%; padding: 8px 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 13px; }
.volume-grid { display: flex; flex-direction: column; gap: 10px; }
.volume-card { border: 1px solid #eee; border-radius: 6px; padding: 14px; }
.volume-header { display: flex; align-items: center; gap: 10px; margin-bottom: 6px; }
.volume-num { font-size: 12px; color: var(--primary); font-weight: 600; background: #e8f4fd; padding: 2px 8px; border-radius: 3px; }
.volume-title { font-weight: 600; font-size: 14px; }
.volume-summary { font-size: 13px; color: #666; line-height: 1.6; }
.volume-hooks { display: flex; flex-wrap: wrap; gap: 4px; margin-top: 8px; }
-hook-tag { font-size: 11px; padding: 2px 6px; background: #f0f0f0; border-radius: 3px; color: #666; }
.actions { display: flex; gap: 10px; margin-top: 16px; }
.btn-primary { padding: 10px 24px; background: var(--primary); color: #fff; border: none; border-radius: 6px; cursor: pointer; }
.btn-primary:disabled { opacity: 0.5; cursor: wait; }
.btn-confirm { padding: 10px 24px; background: #52c41a; color: #fff; border: none; border-radius: 6px; cursor: pointer; margin-left: auto; }
</style>
