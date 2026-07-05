<template>
  <div class="idea-view">
    <div class="section input-section">
      <h3>灵感输入</h3>
      <textarea v-model="form.prompt" placeholder="用一句话描述你的故事创意..." class="idea-textarea" />
      <div class="form-row">
        <select v-model="form.genre" class="form-select">
          <option value="">选择类型倾向</option>
          <option v-for="g in genres" :key="g" :value="g">{{ g }}</option>
        </select>
        <input v-model="form.reference" placeholder="参考作品(可选)" class="form-input" />
        <button @click="generate" :disabled="generating || !form.prompt" class="btn-primary">
          {{ generating ? '生成中...' : '生成创意' }}
        </button>
      </div>
    </div>

    <div v-if="candidates.length" class="section candidates-section">
      <h3>候选创意</h3>
      <div class="candidate-grid">
        <div v-for="(c, idx) in candidates" :key="idx" class="candidate-card" :class="{ selected: selectedIdx === idx }" @click="selectedIdx = idx">
          <div class="candidate-title">{{ c.title }}</div>
          <div class="candidate-meta">
            <span class="score">评分: {{ c.score }}</span>
            <span class="genre">{{ c.genre }}</span>
          </div>
          <div class="candidate-desc">{{ c.description }}</div>
          <div v-if="c.tags?.length" class="candidate-tags">
            <span v-for="t in c.tags" :key="t" class="tag">{{ t }}</span>
          </div>
        </div>
      </div>
    </div>

    <div v-if="selectedIdx !== null && upgrades.length" class="section upgrade-section">
      <h3>创意升级方案</h3>
      <div class="upgrade-list">
        <div v-for="(u, idx) in upgrades" :key="idx" class="upgrade-card">
          <div class="upgrade-header">
            <span class="upgrade-type">{{ u.type }}</span>
            <span class="upgrade-score">+{{ u.scoreBoost }}</span>
          </div>
          <p class="upgrade-desc">{{ u.description }}</p>
        </div>
      </div>
    </div>

    <div v-if="selectedIdx !== null && riskAnalysis" class="section risk-section">
      <h3>风险分析</h3>
      <div class="risk-list">
        <div v-for="(r, idx) in riskAnalysis.risks" :key="idx" class="risk-item">
          <span class="risk-level" :class="r.level">{{ r.level }}</span>
          <span class="risk-text">{{ r.description }}</span>
        </div>
      </div>
      <div class="risk-mitigations">
        <div v-for="(m, idx) in riskAnalysis.mitigations" :key="idx" class="mitigation-item">{{ m }}</div>
      </div>
      <button @click="confirm" class="btn-confirm">确认创意,进入下一步</button>
    </div>

    <div v-if="error" class="error-msg">{{ error }}</div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import { useIdeaStore } from '../stores/idea'
import * as v2Api from '../api/v2'

const props = defineProps<{ projectId: string }>()
const emit = defineEmits<{ complete: [data: any] }>()

const ideaStore = useIdeaStore()
const genres = ['玄幻', '都市', '科幻', '言情', '悬疑', '历史', '游戏', '轻小说']

const form = reactive({ prompt: '', genre: '', reference: '' })
const generating = ref(false)
const candidates = ref<any[]>([])
const selectedIdx = ref<number | null>(null)
const upgrades = ref<any[]>([])
const riskAnalysis = ref<any>(null)
const error = ref('')

async function generate() {
  generating.value = true
  error.value = ''
  try {
    await ideaStore.generateIdeas(props.projectId, form.prompt, form.genre)
    candidates.value = ideaStore.ideas as any[] || []
    selectedIdx.value = null
    upgrades.value = []
    riskAnalysis.value = null
  } catch (e: any) {
    error.value = e?.message || '生成失败'
  } finally {
    generating.value = false
  }
}

async function onSelectCandidate(idx: number) {
  selectedIdx.value = idx
  try {
    const candidate = candidates.value[idx]
    await ideaStore.upgradeIdea(candidate)
    upgrades.value = ideaStore.upgradeVersions as any[] || []
    riskAnalysis.value = await v2Api.analyzeIdeaRisks(props.projectId, candidate.title || candidate.description || '')
  } catch (e: any) {
    error.value = e?.message || '升级失败'
  }
}

async function confirm() {
  if (selectedIdx.value === null) return
  const candidate = candidates.value[selectedIdx.value]
  await v2Api.confirmIdea(props.projectId, candidate.id, candidate.version)
  emit('complete', candidate)
}

watch(selectedIdx, (val) => {
  if (val !== null) onSelectCandidate(val)
})
</script>

<style scoped>
.idea-view { max-width: 900px; margin: 0 auto; }
.section { background: #fff; border: 1px solid #eee; border-radius: 8px; padding: 20px; margin-bottom: 16px; }
.section h3 { margin: 0 0 12px; font-size: 16px; }
.idea-textarea { width: 100%; height: 80px; padding: 10px; border: 1px solid #ddd; border-radius: 4px; resize: vertical; font-size: 14px; }
.form-row { display: flex; gap: 8px; margin-top: 10px; align-items: center; }
.form-select, .form-input { padding: 8px 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 13px; }
.form-input { flex: 1; }
.btn-primary { padding: 8px 20px; background: var(--primary); color: #fff; border: none; border-radius: 4px; cursor: pointer; white-space: nowrap; }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
.candidate-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 12px; }
.candidate-card { border: 1px solid #eee; border-radius: 6px; padding: 14px; cursor: pointer; transition: 0.2s; }
.candidate-card:hover { border-color: var(--primary); box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
.candidate-card.selected { border-color: var(--primary); background: #f0f8ff; }
.candidate-title { font-weight: 600; margin-bottom: 6px; }
.candidate-meta { display: flex; gap: 12px; font-size: 12px; color: #888; margin-bottom: 6px; }
.candidate-desc { font-size: 13px; color: #555; line-height: 1.5; }
.candidate-tags { display: flex; flex-wrap: wrap; gap: 4px; margin-top: 8px; }
.tag { font-size: 11px; padding: 2px 6px; background: #f0f0f0; border-radius: 3px; color: #666; }
.upgrade-list { display: flex; flex-direction: column; gap: 8px; }
.upgrade-card { border: 1px solid #eee; border-radius: 6px; padding: 12px; }
.upgrade-header { display: flex; justify-content: space-between; margin-bottom: 4px; }
.upgrade-type { font-weight: 600; font-size: 14px; }
.upgrade-score { color: #52c41a; font-weight: 600; }
.upgrade-desc { font-size: 13px; color: #555; margin: 0; }
.risk-list { display: flex; flex-direction: column; gap: 6px; }
.risk-item { display: flex; align-items: center; gap: 8px; font-size: 13px; }
.risk-level { padding: 2px 6px; border-radius: 3px; font-size: 11px; font-weight: 600; }
.risk-level.high { background: #fff1f0; color: #ff4d4f; }
.risk-level.medium { background: #fffbe6; color: #fa8c16; }
.risk-level.low { background: #f6ffed; color: #52c41a; }
.risk-text { color: #555; }
.risk-mitigations { margin-top: 12px; }
.mitigation-item { font-size: 12px; color: #666; padding: 3px 0; }
.btn-confirm { margin-top: 16px; width: 100%; padding: 10px; background: #52c41a; color: #fff; border: none; border-radius: 6px; font-size: 15px; cursor: pointer; }
.error-msg { color: #ff4d4f; padding: 12px; text-align: center; }
</style>
