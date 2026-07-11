<template>
  <div class="character-view">
    <div class="tabs">
      <div v-for="t in tabs" :key="t.key" class="tab" :class="{ active: activeTab === t.key }" @click="activeTab = t.key">{{ t.label }}</div>
    </div>

    <div class="tab-content">
      <div v-if="activeTab === 'protagonist'" class="tab-pane">
        <h3>主角档案 (九维)</h3>
        <div v-for="group in protagonistGroups" :key="group.key" class="form-group-collapse">
          <div class="collapse-header" @click="toggleGroup(group.key)">
            <span class="collapse-icon">{{ group.expanded ? '▼' : '▶' }}</span>
            <span class="collapse-title">{{ group.label }}</span>
          </div>
          <div v-if="group.expanded" class="char-form-grid">
            <div v-for="dim in group.dims" :key="dim.key" class="form-group">
              <label>{{ dim.label }}</label>
              <input v-model="protagonist[dim.key]" class="form-input" :placeholder="dim.placeholder" />
            </div>
          </div>
        </div>
      </div>

      <div v-if="activeTab === 'supporting'" class="tab-pane">
        <h3>配角列表</h3>
        <div class="form-row">
          <div class="form-group-sm">
            <label>配角数量</label>
            <select v-model.number="supportingCount" class="form-select-sm">
              <option :value="3">3个</option><option :value="5">5个</option><option :value="8">8个</option><option :value="12">12个</option>
            </select>
          </div>
          <button @click="showAddForm = !showAddForm" class="btn-add">+ 手动添加角色</button>
        </div>
        <div v-if="showAddForm" class="add-char-form">
          <input v-model="newChar.name" placeholder="姓名" class="form-input-sm" />
          <input v-model="newChar.role" placeholder="角色定位" class="form-input-sm" />
          <input v-model="newChar.trait" placeholder="性格特点" class="form-input-sm" />
          <button @click="addChar" class="btn-save" :disabled="!newChar.name">添加</button>
        </div>
        <div class="char-grid">
          <div v-for="(c, idx) in supportingChars" :key="idx" class="char-card" :class="{ active: selectedChar === c }" @click="selectedChar = c">
            <div class="char-name">{{ c.name }}</div>
            <div class="char-role">{{ c.role }}</div>
            <div class="char-trait">{{ c.trait }}</div>
          </div>
        </div>
        <div v-if="selectedChar" class="char-detail">
          <h4>{{ selectedChar.name }} 详情</h4>
          <div class="char-form-grid">
            <div v-for="dim in charDims" :key="dim.key" class="form-group">
              <label>{{ dim.label }}</label>
              <input v-model="selectedChar[dim.key]" class="form-input" :placeholder="dim.placeholder" />
            </div>
          </div>
        </div>
      </div>

      <div v-if="activeTab === 'villain'" class="tab-pane">
        <h3>反派体系</h3>
        <div v-for="(v, idx) in villains" :key="idx" class="villain-card">
          <div class="villain-name">{{ v.name }} <span class="tier">{{ v.tier }}</span></div>
          <div class="villain-motivation">{{ v.motivation }}</div>
        </div>
      </div>

      <div v-if="activeTab === 'relations'" class="tab-pane">
        <h3>关系网络</h3>
        <RelationGraph :characters="allCharacters" :relations="relations as any" />
      </div>
    </div>

    <div v-if="error" class="error-box">{{ error }}</div>
    <div class="actions">
      <button @click="generate" :disabled="generating" class="btn-primary">
        <span v-if="generating" class="spinner"></span>{{ generating ? '生成中...' : 'AI生成角色' }}
      </button>
      <button @click="checkConsistency" class="btn-secondary">一致性检查</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useCharacterStore } from '../stores/character'
import * as v2Api from '../api/v2'
import RelationGraph from '../components/RelationGraph.vue'
import { useGeneration } from '../composables/useGeneration'

const props = defineProps<{ projectId: string }>()
const emit = defineEmits<{ complete: [data: any] }>()
const charStore = useCharacterStore()
const gen = useGeneration('characters', '角色')

const tabs = [
  { key: 'protagonist', label: '主角' },
  { key: 'supporting', label: '配角' },
  { key: 'villain', label: '反派' },
  { key: 'relations', label: '关系' },
]
const activeTab = ref('protagonist')
const generating = ref(false)
const error = ref('')
const selectedChar = ref<any>(null)
const supportingCount = ref(5)
const showAddForm = ref(false)
const newChar = reactive({ name: '', role: '', trait: '' })

const charDims = [
  { key: 'name', label: '姓名', placeholder: '姓名' },
  { key: 'role', label: '角色定位', placeholder: '主角的朋友/导师/对手' },
  { key: 'trait', label: '性格', placeholder: '性格特点' },
  { key: 'appearance', label: '外貌', placeholder: '外貌特征' },
  { key: 'background', label: '背景', placeholder: '背景故事' },
  { key: 'goal', label: '目标', placeholder: '角色追求' },
  { key: 'relation', label: '与主角关系', placeholder: '如：挚友/暗恋/师徒' },
]

const protagonist = reactive<any>({})
const supportingChars = ref<any[]>([])
const villains = ref<any[]>([])
const relations = ref<any[]>([])

const allCharacters = computed(() => {
  const chars: any[] = []
  if (protagonist.name) chars.push(protagonist)
  chars.push(...supportingChars.value)
  chars.push(...villains.value)
  return chars
})

const nineDims = [
  { key: 'name', label: '姓名', placeholder: '主角姓名' },
  { key: 'gender', label: '性别', placeholder: '男/女' },
  { key: 'age', label: '年龄', placeholder: '年龄' },
  { key: 'appearance', label: '外貌', placeholder: '外貌特征' },
  { key: 'personality', label: '性格', placeholder: '核心性格特点' },
  { key: 'background', label: '背景', placeholder: '出身背景故事' },
  { key: 'goal', label: '目标', placeholder: '角色追求' },
  { key: 'flaw', label: '缺陷', placeholder: '致命弱点/缺点' },
  { key: 'arc', label: '成长弧线', placeholder: '角色成长方向' },
]

const protagonistGroups = ref([
  { key: 'basic', label: '基础信息', expanded: true, dims: nineDims.slice(0, 4) },
  { key: 'personality', label: '性格特质', expanded: false, dims: nineDims.slice(4, 6) },
  { key: 'growth', label: '目标与成长', expanded: false, dims: nineDims.slice(6, 9) },
])

function toggleGroup(key: string) {
  const g = protagonistGroups.value.find(g => g.key === key)
  if (g) g.expanded = !g.expanded
}

const worldData = ref<any>(null)
const storyConcept = ref('')

function addChar() {
  if (!newChar.name) return
  supportingChars.value.push({ ...newChar })
  newChar.name = ''; newChar.role = ''; newChar.trait = ''
  showAddForm.value = false
}

async function generate() {
  generating.value = true
  error.value = ''
  gen.begin(4, '正在生成主角...')
  try {
    const result = await charStore.generateCharacters(
      props.projectId, worldData.value, storyConcept.value || undefined,
      (step, msg) => gen.progress(step, msg)
    )
    Object.assign(protagonist, result.protagonist || {})
    supportingChars.value = result.supporting || []
    villains.value = result.villains || []
    relations.value = (result.relations as any) || []
    const charData = { protagonist: { ...protagonist }, supporting: supportingChars.value, villains: villains.value, relations: relations.value }
    try { await v2Api.saveModuleData(props.projectId, 'characters', charData) } catch (_e) { /* ignore */ }
  } catch (e: any) {
    error.value = e?.message || '生成失败'
    gen.fail(error.value)
  } finally {
    generating.value = false
    if (!error.value) gen.end()
  }
}

async function checkConsistency() {
  await v2Api.characterConsistencyCheck(props.projectId)
}

async function confirm() {
  await charStore.saveCharacters(props.projectId, {
    protagonist: { ...protagonist },
    supporting: supportingChars.value,
    villains: villains.value,
    relations: relations.value,
  })
  emit('complete', { protagonist, supporting: supportingChars.value, villains: villains.value })
}

onMounted(async () => {
  try {
    const saved = await v2Api.getModuleData(props.projectId, 'characters')
    if (saved?.data) {
      const d = saved.data
      if (Array.isArray(d)) {
        d.forEach((c: any) => {
          const rt = (c.role_type || c.role || '').toLowerCase()
          if (rt.includes('主角') || rt.includes('protagonist') || rt === 'main') {
            Object.assign(protagonist, c)
          } else if (rt.includes('反派') || rt.includes('villain') || rt.includes('antagonist')) {
            villains.value.push(c)
          } else {
            supportingChars.value.push(c)
          }
        })
      } else {
        if (d.protagonist) Object.assign(protagonist, d.protagonist)
        if (d.supporting) supportingChars.value = d.supporting
        if (d.villains) villains.value = d.villains
        if (d.relations) relations.value = d.relations
      }
    }
  } catch (_e) { /* ignore */ }
  try {
    const allData = await v2Api.getAllModuleData(props.projectId)
    const world = allData?.modules?.['world']
    if (world) {
      worldData.value = world
      storyConcept.value = world.origin?.hiddenTruth || ''
    }
  } catch (_e) { /* ignore */ }
})
</script>

<style scoped>
.character-view { max-width: 1170px; margin: 0 auto; }
.tabs { display: flex; gap: 3px; margin-bottom: 0; }
.tab { padding: 13px 20px; background: #f5f5f5; border: 1px solid #ddd; border-bottom: none; border-radius: 8px 6px 0 0; cursor: pointer; font-size: 17px; font-weight: 500; }
.tab.active { background: #fff; border-color: #eee; color: var(--primary); }
.tab-content { background: #fff; border: 1px solid #eee; border-radius: 0 6px 6px 6px; padding: 26px; min-height: 390px; }
.tab-pane h3 { margin: 0 0 16px; font-size: 21px; }
.char-form-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
.form-group-collapse { margin-bottom: 12px; border: 1px solid #eee; border-radius: 10px; overflow: hidden; }
.collapse-header { display: flex; align-items: center; gap: 8px; padding: 12px 16px; background: #f8f9fa; cursor: pointer; user-select: none; }
.collapse-header:hover { background: #f0f0f0; }
.collapse-icon { font-size: 12px; color: #888; }
.collapse-title { font-weight: 600; color: #555; font-size: 15px; }
.form-group-collapse .char-form-grid { padding: 16px; }
.form-group label { display: block; font-weight: 600; margin-bottom: 5px; font-size: 16px; color: #555; }
.form-input { width: 100%; padding: 8px 10px; border: 1px solid #ddd; border-radius: 5px; font-size: 17px; }
.char-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 13px; }
.char-card { border: 1px solid #eee; border-radius: 8px; padding: 16px; cursor: pointer; transition: 0.15s; }
.char-card:hover { border-color: var(--primary); box-shadow: 0 2px 6px rgba(0,0,0,0.06); }
.char-card.active { border-color: var(--primary); background: #f0f8ff; }
.char-name { font-weight: 600; margin-bottom: 5px; }
.char-role { font-size: 16px; color: #888; }
.char-trait { font-size: 14px; color: #aaa; margin-top: 5px; }
.char-detail { margin-top: 21px; background: #f9f9f9; border-radius: 8px; padding: 18px; }
.char-detail h4 { margin: 0 0 12px; }
.form-row { display: flex; gap: 12px; align-items: flex-end; margin-bottom: 16px; flex-wrap: wrap; }
.form-group-sm { margin-bottom: 0; }
.form-group-sm label { display: block; font-weight: 600; margin-bottom: 4px; font-size: 14px; color: #555; }
.form-select-sm { padding: 8px 10px; border: 1px solid #ddd; border-radius: 5px; font-size: 16px; }
.add-char-form { display: flex; gap: 8px; margin-bottom: 16px; flex-wrap: wrap; align-items: flex-end; }
.form-input-sm { padding: 8px 10px; border: 1px solid #ddd; border-radius: 5px; font-size: 15px; width: 150px; }
.btn-add { padding: 8px 16px; background: #e8f4fd; color: var(--primary); border: 1px solid var(--primary); border-radius: 6px; cursor: pointer; font-size: 15px; }
.btn-save { padding: 8px 16px; background: var(--primary); color: #fff; border: none; border-radius: 6px; cursor: pointer; font-size: 15px; }
.btn-save:disabled { opacity: 0.5; }
.villain-card { border: 1px solid #eee; border-radius: 8px; padding: 16px; margin-bottom: 10px; }
.villain-name { font-weight: 600; margin-bottom: 5px; }
.tier { font-size: 14px; padding: 1px 6px; background: #fff1f0; color: #ff4d4f; border-radius: 4px; }
.villain-motivation { font-size: 17px; color: #666; }
.actions { display: flex; gap: 13px; margin-top: 21px; }
.btn-primary { padding: 13px 24px; background: var(--primary); color: #fff; border: none; border-radius: 8px; cursor: pointer; }
.btn-primary:disabled { opacity: 0.5; cursor: wait; }
.btn-secondary { padding: 13px 20px; background: #f5f5f5; border: 1px solid #ddd; border-radius: 8px; cursor: pointer; }

.spinner { display: inline-block; width: 14px; height: 14px; border: 2px solid #fff; border-top-color: transparent; border-radius: 50%; animation: spin 0.8s linear infinite; margin-right: 6px; }
@keyframes spin { to { transform: rotate(360deg); } }
.error-box { color: #e74c3c; background: #fff1f0; border-radius: 8px; padding: 12px; margin-top: 12px; font-size: 14px; }
</style>
