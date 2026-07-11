<template>
  <div class="factions-view">
    <div class="section">
      <h3>势力体系设计</h3>
      <p class="tip">设计世界中的各大势力组织，包含领地、首领、内部冲突等</p>

      <div class="form-group">
        <label>核心势力数量</label>
        <select v-model="form.count" class="form-select">
          <option value="3">三大势力（三足鼎立）</option>
          <option value="4">四大势力（四方割据）</option>
          <option value="5">五大势力（五龙争珠）</option>
          <option value="6">六大门派（群豪并起）</option>
        </select>
      </div>

      <div class="form-group">
        <label>势力格局</label>
        <select v-model="form.pattern" class="form-select">
          <option value="balance">均衡对峙</option>
          <option value="supremacy">一超多方</option>
          <option value="alliance">两大连盟对抗</option>
          <option value="anarchy">群雄割据无主导</option>
        </select>
      </div>

      <div class="form-group">
        <label>势力核心矛盾</label>
        <textarea v-model="form.conflict" rows="4" placeholder="描述势力间的主要矛盾：资源争夺、理念冲突、历史恩怨..." class="form-textarea"></textarea>
      </div>

      <div class="form-group">
        <label>参考世界观和角色</label>
        <div class="context-hint" v-if="upstreamData">{{ upstreamData }}</div>
        <div class="context-hint empty" v-else>暂无世界观或角色数据</div>
      </div>

      <div class="action-row">
        <button @click="generate" :disabled="loading" class="btn btn-primary">
          <span v-if="loading" class="spinner"></span>{{ loading ? '生成中...' : 'AI生成势力体系' }}
        </button>
        <button @click="$emit('complete', resultData)" class="btn btn-ghost">跳过</button>
      </div>

      <div v-if="error" class="error-box">
        <p>{{ error }}</p>
        <button @click="useOfflineMode" class="btn btn-ghost btn-sm">使用离线模板</button>
      </div>
    </div>

    <div v-if="factions.length" class="section">
      <h3>生成结果</h3>
      <div class="factions-grid">
        <div v-for="(f, idx) in factions" :key="idx" class="faction-card">
          <div class="faction-header">
            <span class="faction-badge" :style="{ background: f.color || colors[idx] }">{{ f.short_name || f.shortName || (f.name || '').slice(0, 1) }}</span>
            <span class="faction-name">{{ f.name }}</span>
          </div>
          <div class="faction-info">
            <div class="info-row"><span class="label">首领</span>{{ f.leader || f.leader_name || '-' }}</div>
            <div class="info-row"><span class="label">领地</span>{{ f.territory || f.home || '-' }}</div>
            <div class="info-row"><span class="label">实力</span>{{ f.strength || f.power_rating || '★★★☆☆' }}</div>
          </div>
          <div class="faction-desc">{{ f.description || f.desc || '' }}</div>
          <div class="faction-relation" v-if="f.relation || f.core_relation"><strong>核心关系：</strong>{{ f.relation || f.core_relation }}</div>
        </div>
      </div>
      <button @click="$emit('complete', resultData)" class="btn btn-primary btn-complete">确认并通过</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import * as v2Api from '../api/v2'
import { useGeneration } from '../composables/useGeneration'

const props = defineProps<{ projectId: string }>()
const emit = defineEmits<{ complete: [data: any] }>()
const gen = useGeneration('factions', '势力体系')

const colors = ['#4a90d9', '#e74c3c', '#27ae60', '#f39c12', '#9b59b6', '#1abc9c']

const form = reactive({ count: '3', pattern: 'balance', conflict: '' })
const loading = ref(false)
const error = ref('')
const factions = ref<any[]>([])
const upstreamData = ref('')
const isOffline = ref(false)

const resultData = computed(() => ({
  pattern: form.pattern,
  factions: factions.value,
}))

onMounted(async () => {
  try {
    const saved = await v2Api.getModuleData(props.projectId, 'factions')
    if (saved?.data) {
      const d = saved.data
      if (Array.isArray(d)) {
        factions.value = d
        return
      }
      if (d.pattern) form.pattern = d.pattern
      if (d.conflict) form.conflict = d.conflict
      if (d.count) form.count = d.count
      if (d.factions) factions.value = d.factions
      if (d.upstreamData) upstreamData.value = d.upstreamData
      return
    }
    const allData = await v2Api.getAllModuleData(props.projectId)
    const mods = allData?.modules || {}
    const parts: string[] = []
    if (mods['world']) parts.push('世界观')
    if (mods['characters']) parts.push('角色')
    if (mods['power_system']) parts.push('力量体系')
    upstreamData.value = parts.length ? `已加载${parts.join('/')}数据` : ''
    if (mods['world']?.civilization && !form.conflict) {
      form.conflict = `基于${mods['world'].origin?.worldType || '当前世界'}文明的核心势力矛盾`
    }
  } catch (_e) { /* ignore */ }
})

async function generate() {
  loading.value = true
  gen.begin()
  error.value = ''
  isOffline.value = false
  try {
    const allData = await v2Api.getAllModuleData(props.projectId)
    const world = allData?.modules?.['world'] || {}
    const chars = allData?.modules?.['characters'] || []
    let charList = Array.isArray(chars) ? chars : []
    if (!Array.isArray(chars)) {
      const tmp = chars.protagonist || chars.data?.protagonist
      if (tmp) charList = [tmp, ...(chars.supporting || chars.data?.supporting || []), ...(chars.villains || chars.data?.villains || [])]
    }
    const result = await v2Api.generateFactions(props.projectId, {
      pattern: form.pattern,
      conflict: form.conflict,
      civilization: world.civilization || {},
      characters: charList.slice(0, 10),
      world_structure: world.structure || {},
    })
    factions.value = result.factions || []
    if (!factions.value.length) {
      useOfflineMode()
    }
    try { await v2Api.saveModuleData(props.projectId, 'factions', { factions: factions.value, meta_analysis: result.metaAnalysis || '' }) } catch (_e) { /* ignore */ }
  } catch (e: any) {
    error.value = e.message || 'AI生成器未配置或生成失败'
    useOfflineMode()
  } finally {
    loading.value = false
    if (!error.value) gen.end()
    else gen.fail(error.value)
  }
}

function useOfflineMode() {
  isOffline.value = true
  const count = parseInt(form.count)
  factions.value = getNames(form.pattern, count)
}

function getNames(pattern: string, count: number): any[] {
  const sets: Record<string, Array<{ name: string; short_name: string; desc: string }>> = {
    balance: [
      { name: '天玄宗', short_name: '天', desc: '正道魁首，以守护天下苍生为己任，坐拥灵脉最盛之地。' },
      { name: '幽冥殿', short_name: '冥', desc: '魔道巨擘，追求极致力量，行事不拘正道，但重承诺。' },
      { name: '万宝阁', short_name: '万', desc: '中立势力，掌控天下财货流通，以商道制衡正邪双方。' },
      { name: '星辰海', short_name: '星', desc: '海外仙岛势力，超然物外，精通推演天机之术。' },
      { name: '洪荒谷', short_name: '荒', desc: '远古遗族，守护上古秘境，与天地兽灵共生。' },
      { name: '轮回司', short_name: '轮', desc: '掌管生死轮回的神秘势力，游离于三界之外。' },
    ],
    supremacy: [
      { name: '帝庭', short_name: '帝', desc: '天下共主，坐拥九州之地，实力深不可测。' },
      { name: '北境联盟', short_name: '北', desc: '北方诸国联合体，以商贸和军事同盟对抗帝庭。' },
      { name: '南疆巫部', short_name: '巫', desc: '南疆蛮荒之地的巫蛊势力，世代守护祖灵。' },
      { name: '东海龙宫', short_name: '龙', desc: '海底霸主，掌控海域一切水族。' },
      { name: '西域商会', short_name: '西', desc: '横跨东西的商业帝国，以财富影响政局。' },
      { name: '暗影组织', short_name: '暗', desc: '游走于灰色地带的刺客组织。' },
    ],
  }
  const names = sets[pattern] || sets.balance
  return Array.from({ length: count }, (_, i) => ({
    name: names[i]?.name || `势力${i + 1}`,
    short_name: names[i]?.short_name || names[i]?.name?.slice(0, 1) || `${i + 1}`,
    description: names[i]?.desc || '待描述',
    leader: ['玄天宗主', '魔皇·厉无极', '万古圣君', '星辰大帝', '鸿蒙道祖', '轮回主宰'][i] || `势力${i + 1}首领`,
    territory: ['天域·云海之巅', '冥界·暗影深渊', '圣土·光明圣殿', '星辰·银河之海', '洪荒·混沌原乡', '轮回·生死之间'][i] || '待定',
    strength: ['★★★★★', '★★★★☆', '★★★★☆', '★★★☆☆', '★★★☆☆', '★★☆☆☆'][i] || '★★★☆☆',
    color: colors[i],
    relation: getRelation(i, count, pattern),
  }))
}

function getRelation(idx: number, count: number, pattern: string): string {
  if (pattern === 'supremacy' && idx === 0) return '独霸天下，其余势力联合勉强抗衡'
  if (pattern === 'alliance') return idx < count / 2 ? '联盟A阵营，与对立阵营对抗' : '联盟B阵营'
  if (pattern === 'anarchy') return '各自为政，互相警惕'
  if (pattern === 'balance') return idx % 2 === 0 ? '与相邻势力摩擦不断，维持微妙平衡' : '中立偏保守，暗中发展实力'
  return '与其他势力保持警惕的和平'
}
</script>

<style scoped>
.factions-view { max-width: 900px; }
.section { background: #fff; border-radius: 16px; padding: 28px; margin-bottom: 20px; box-shadow: 0 4px 16px rgba(0,0,0,.06); }
.section h3 { font-size: 22px; margin-bottom: 10px; }
.tip { color: #888; margin-bottom: 20px; font-size: 16px; }
.context-hint { padding: 8px 12px; background: #f0f8ff; border: 1px solid #d4eaff; border-radius: 8px; font-size: 13px; color: #4a90d9; margin-bottom: 14px; }
.context-hint.empty { background: #fff8e1; border-color: #ffe082; color: #f57c00; }
.form-group { margin-bottom: 18px; }
.form-group label { display: block; font-weight: 600; margin-bottom: 8px; font-size: 16px; color: #555; }
.form-select, .form-input { width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 10px; font-size: 16px; }
.form-textarea { width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 10px; font-size: 16px; resize: vertical; min-height: 100px; font-family: inherit; }
.action-row { display: flex; gap: 12px; margin-top: 20px; }
.btn { border: none; border-radius: 10px; padding: 12px 24px; font-size: 16px; font-weight: 600; cursor: pointer; }
.btn-sm { padding: 8px 16px; font-size: 14px; }
.btn-primary { background: linear-gradient(135deg, var(--primary), var(--primary-light)); color: #fff; }
.btn-ghost { background: #f0f0f0; color: #555; }
.btn-complete { margin-top: 20px; }
.error-box { margin-top: 16px; padding: 16px; background: #fff3f3; border: 1px solid #ffcdd2; border-radius: 10px; }
.error-box p { color: #c62828; margin-bottom: 8px; }
.factions-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.faction-card { border: 1px solid #eee; border-radius: 14px; padding: 20px; background: #fafafa; }
.faction-header { display: flex; align-items: center; gap: 10px; margin-bottom: 14px; }
.faction-badge { width: 36px; height: 36px; border-radius: 8px; color: #fff; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 18px; }
.faction-name { font-weight: 700; font-size: 18px; }
.faction-info { margin-bottom: 12px; }
.info-row { display: flex; padding: 4px 0; font-size: 15px; }
.info-row .label { font-weight: 600; width: 50px; color: #666; flex-shrink: 0; }
.faction-desc { color: #555; font-size: 15px; line-height: 1.6; margin-bottom: 10px; }
.faction-relation { font-size: 14px; color: #888; border-top: 1px solid #eee; padding-top: 10px; }
.spinner { display: inline-block; width: 14px; height: 14px; border: 2px solid #fff; border-top-color: transparent; border-radius: 50%; animation: spin 0.8s linear infinite; margin-right: 6px; }
@keyframes spin { to { transform: rotate(360deg); } }
</style>
