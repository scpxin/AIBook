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
          <span v-if="generating" class="spinner"></span>{{ generating ? '生成中...' : '生成创意' }}
        </button>
        <button @click="manualConfirm" :disabled="!form.prompt" class="btn-manual">直接使用</button>
      </div>
    </div>

    <div v-if="!form.prompt.trim()" class="section quick-section">
      <h3>快速开始</h3>
      <p class="tip">不想等待AI生成？选择一个模板或手动输入你的故事创意</p>
      <div class="quick-grid">
        <div v-for="tpl in quickTemplates" :key="tpl.label" class="quick-card" @click="form.prompt = tpl.prompt; form.genre = tpl.genre">
          <div class="quick-icon">{{ tpl.icon }}</div>
          <div class="quick-label">{{ tpl.label }}</div>
          <div class="quick-desc">{{ tpl.desc }}</div>
        </div>
      </div>
    </div>

    <div v-if="generating" class="section">
      <div class="skeleton skeleton-card"></div>
      <div class="skeleton skeleton-card"></div>
      <div class="skeleton skeleton-card"></div>
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
import { ref, reactive, watch, onMounted } from 'vue'
import { useIdeaStore } from '../stores/idea'
import * as v2Api from '../api/v2'
import { useGeneration } from '../composables/useGeneration'

const props = defineProps<{ projectId: string }>()
const emit = defineEmits<{ complete: [data: any] }>()

const ideaStore = useIdeaStore()
const gen = useGeneration('idea', '灵感创意')
const genres = ['玄幻', '都市', '科幻', '言情', '悬疑', '历史', '游戏', '轻小说']

const form = reactive({ prompt: '', genre: '', reference: '' })
const generating = ref(false)
const candidates = ref<any[]>([])
const selectedIdx = ref<number | null>(null)
const upgrades = ref<any[]>([])
const riskAnalysis = ref<any>(null)
const error = ref('')

const quickTemplates = [
  { icon: '🗡', label: '玄幻修仙', genre: '玄幻', desc: '逆天改命，凡人修仙', prompt: '一个被宗门抛弃的废柴少年，意外获得神秘传承，从此踏上逆天改命的修仙之路。' },
  { icon: '🏙', label: '都市异能', genre: '都市', desc: '现代都市，隐藏力量', prompt: '一个普通上班族某天突然觉醒了特殊能力，发现自己卷入了一场隐藏在都市暗处的超能战争。' },
  { icon: '🚀', label: '科幻星际', genre: '科幻', desc: '星际穿越，未来科技', prompt: '在人类星际殖民的黄金时代，一艘探索飞船在宇宙边缘发现了一个改变人类命运的古老秘密。' },
  { icon: '💕', label: '言情虐恋', genre: '言情', desc: '爱恨纠葛，虐恋情深', prompt: '高冷霸总与倔强灰姑娘之间一段充满误会与反转的虐恋故事，从互相伤害到彼此救赎。' },
]

async function manualConfirm() {
  if (!form.prompt.trim()) return
  const manualIdea = {
    title: form.prompt.slice(0, 30),
    description: form.prompt,
    genre: form.genre || '自定义',
    score: 85,
    tags: [form.genre || '自定义'],
    isManual: true,
  }
  await v2Api.confirmIdea(props.projectId, 'manual', 1)
  const fullState = {
    prompt: form.prompt,
    genre: form.genre,
    reference: form.reference,
    candidates: [manualIdea],
    selectedIdx: 0,
    upgrades: [],
    riskAnalysis: null,
    confirmedCandidate: manualIdea,
  }
  try { await v2Api.saveModuleData(props.projectId, 'idea', fullState) } catch (_e) { /* ignore */ }
  emit('complete', fullState)
}

async function generate() {
  generating.value = true
  error.value = ''
  gen.begin()
  try {
    await ideaStore.generateIdeas(props.projectId, form.prompt, form.genre)
    candidates.value = ideaStore.ideas as any[] || []
    selectedIdx.value = null
    upgrades.value = []
    riskAnalysis.value = null
  } catch (e: any) {
    error.value = e?.message || '生成失败'
    gen.fail(error.value)
  } finally {
    generating.value = false
    if (!error.value) gen.end()
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
  const fullState = {
    prompt: form.prompt,
    genre: form.genre,
    reference: form.reference,
    candidates: candidates.value,
    selectedIdx: selectedIdx.value,
    upgrades: upgrades.value,
    riskAnalysis: riskAnalysis.value,
    confirmedCandidate: candidate,
  }
  try { await v2Api.saveModuleData(props.projectId, 'idea', fullState) } catch (_e) { /* ignore */ }
  emit('complete', fullState)
}

watch(selectedIdx, (val) => {
  if (val !== null) onSelectCandidate(val)
})

onMounted(async () => {
  try {
    const saved = await v2Api.getModuleData(props.projectId, 'idea')
    if (saved?.data && (saved.data.candidates || saved.data.confirmedCandidate || saved.data.prompt)) {
      const d = saved.data
      if (d.candidates) {
        candidates.value = d.candidates
        selectedIdx.value = d.selectedIdx ?? null
        upgrades.value = d.upgrades || []
        riskAnalysis.value = d.riskAnalysis || null
      } else if (d.confirmedCandidate) {
        candidates.value = [d.confirmedCandidate]
        selectedIdx.value = 0
      }
      if (d.prompt || d.title) form.prompt = d.prompt || d.title || ''
      if (d.genre) form.genre = d.genre || ''
      if (d.reference) form.reference = d.reference || ''
    }
  } catch (_e) { /* ignore */ }
})
</script>

<style scoped>
.idea-view { max-width: 1170px; margin: 0 auto; }
.section { background: #fff; border: 1px solid #eee; border-radius: 10px; padding: 26px; margin-bottom: 21px; }
.section h3 { margin: 0 0 12px; font-size: 21px; }
.idea-textarea { width: 100%; height: 104px; padding: 13px; border: 1px solid #ddd; border-radius: 5px; resize: vertical; font-size: 18px; }
.form-row { display: flex; gap: 10px; margin-top: 13px; align-items: center; }
.form-select, .form-input { padding: 10px 10px; border: 1px solid #ddd; border-radius: 5px; font-size: 17px; }
.form-input { flex: 1; }
.btn-primary { padding: 10px 20px; background: var(--primary); color: #fff; border: none; border-radius: 5px; cursor: pointer; white-space: nowrap; }
.spinner { display: inline-block; width: 14px; height: 14px; border: 2px solid #fff; border-top-color: transparent; border-radius: 50%; animation: spin 0.8s linear infinite; margin-right: 6px; }
@keyframes spin { to { transform: rotate(360deg); } }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-manual { padding: 10px 20px; background: #52c41a; color: #fff; border: none; border-radius: 5px; cursor: pointer; white-space: nowrap; font-size: 16px; }
.btn-manual:disabled { opacity: 0.5; cursor: not-allowed; }
.quick-section { background: #f8fafc; }
.quick-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 12px; margin-top: 16px; }
.quick-card { border: 2px solid #e8e8e8; border-radius: 10px; padding: 18px; cursor: pointer; transition: 0.15s; text-align: center; }
.quick-card:hover { border-color: var(--primary); background: #f0f8ff; transform: translateY(-2px); }
.quick-icon { font-size: 28px; margin-bottom: 8px; }
.quick-label { font-weight: 600; font-size: 17px; margin-bottom: 4px; }
.quick-desc { font-size: 14px; color: #999; }
.candidate-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 16px; }
.candidate-card { border: 1px solid #eee; border-radius: 8px; padding: 18px; cursor: pointer; transition: 0.2s; }
.candidate-card:hover { border-color: var(--primary); box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
.candidate-card.selected { border-color: var(--primary); background: #f0f8ff; }
.candidate-title { font-weight: 600; margin-bottom: 8px; }
.candidate-meta { display: flex; gap: 16px; font-size: 16px; color: #888; margin-bottom: 8px; }
.candidate-desc { font-size: 17px; color: #555; line-height: 1.5; }
.candidate-tags { display: flex; flex-wrap: wrap; gap: 5px; margin-top: 10px; }
.tag { font-size: 14px; padding: 3px 6px; background: #f0f0f0; border-radius: 4px; color: #666; }
.upgrade-list { display: flex; flex-direction: column; gap: 10px; }
.upgrade-card { border: 1px solid #eee; border-radius: 8px; padding: 16px; }
.upgrade-header { display: flex; justify-content: space-between; margin-bottom: 5px; }
.upgrade-type { font-weight: 600; font-size: 18px; }
.upgrade-score { color: #52c41a; font-weight: 600; }
.upgrade-desc { font-size: 17px; color: #555; margin: 0; }
.risk-list { display: flex; flex-direction: column; gap: 8px; }
.risk-item { display: flex; align-items: center; gap: 10px; font-size: 17px; }
.risk-level { padding: 3px 6px; border-radius: 4px; font-size: 14px; font-weight: 600; }
.risk-level.high { background: #fff1f0; color: #ff4d4f; }
.risk-level.medium { background: #fffbe6; color: #fa8c16; }
.risk-level.low { background: #f6ffed; color: #52c41a; }
.risk-text { color: #555; }
.risk-mitigations { margin-top: 16px; }
.mitigation-item { font-size: 16px; color: #666; padding: 4px 0; }
.btn-confirm { margin-top: 21px; width: 100%; padding: 13px; background: #52c41a; color: #fff; border: none; border-radius: 8px; font-size: 20px; cursor: pointer; }
.error-msg { color: #ff4d4f; padding: 16px; text-align: center; }
</style>
