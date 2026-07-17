<template>
  <div class="character-view">
    <div v-if="pageLoading" class="page-loading">
      <div class="loading-spinner"></div>
      <p>加载中...</p>
    </div>
    <div v-else">
    <div class="tabs">
      <div v-for="t in tabs" :key="t.key" class="tab" :class="{ active: activeTab === t.key }" @click="activeTab = t.key" role="tab" tabindex="0" :aria-selected="activeTab === t.key" @keydown.left="handleTabKeydown(-1, $event)" @keydown.right="handleTabKeydown(1, $event)">{{ t.label }}</div>
    </div>

    <div class="tab-content">
      <div v-if="activeTab === 'protagonist'" class="tab-pane">
        <h3>主角档案 (九维)</h3>
        <div v-for="group in protagonistGroups" :key="group.key" class="form-group-collapse">
          <div class="collapse-header" @click="toggleGroup(group.key)" tabindex="0" @keydown.enter="toggleGroup(group.key)" @keydown.space.prevent="toggleGroup(group.key)">
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
        <div v-if="!supportingChars.length && !generating" class="empty-hint tab-pane">暂无配角，点击「AI生成角色」自动填充，或手动添加</div>
        <div class="char-grid">
          <div v-for="(c, idx) in supportingChars" :key="idx" class="char-card" :class="{ active: selectedChar === c }" tabindex="0" @click="selectedChar = c" @keydown.enter="selectedChar = c" v-keyboard-click>
            <div class="char-name">{{ c.name }}<button @click.stop="deleteChar(idx)" class="btn-delete-sm" title="删除" aria-label="删除配角">×</button></div>
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
        <div v-if="!villains.length && !generating" class="empty-hint tab-pane">暂无反派，点击「AI生成角色」自动填充，或手动添加</div>
        <div class="villain-grid">
          <div v-for="(v, idx) in villains" :key="idx" class="villain-card" :class="{ active: selectedVillain === v }" tabindex="0" @click="selectedVillain = v" @keydown.enter="selectedVillain = v" v-keyboard-click>
            <div class="villain-name">{{ v.name }} <span class="tier">{{ v.tier }}</span><button @click.stop="deleteVillain(idx)" class="btn-delete-sm" title="删除" aria-label="删除反派">x</button></div>
            <div class="villain-motivation">{{ v.motivation }}</div>
          </div>
        </div>
        <div v-if="selectedVillain" class="char-detail">
          <h4>{{ selectedVillain.name }} 详情</h4>
          <div class="char-form-grid">
            <div v-for="dim in villainDims" :key="dim.key" class="form-group">
              <label>{{ dim.label }}</label>
              <input v-model="selectedVillain[dim.key]" class="form-input" :placeholder="dim.placeholder" />
            </div>
          </div>
        </div>
      </div>

      <div v-if="activeTab === 'relations'" class="tab-pane">
        <h3>关系网络</h3>
        <RelationGraph :characters="allCharacters" :relations="relations as any" />
      </div>
    </div>

    <div v-if="error" class="error-box">{{ error }}</div>
    <div v-if="saveState === 'saving'" class="save-status">保存中...</div>
    <div v-if="saveState === 'saved'" class="save-status saved">已自动保存</div>
    <div v-if="saveState === 'error'" class="save-status error">保存失败</div>
    <div v-if="checkResultMsg" class="check-result-box">{{ checkResultMsg }}</div>
    </div>
     <div class="actions">
       <button @click="generate" :disabled="generating" class="btn-primary">
         <span v-if="generating" class="spinner"></span>{{ generating ? '生成中...' : 'AI生成角色' }}
       </button>
       <button @click="checkConsistency" class="btn-secondary">一致性检查</button>
       <button @click="confirm" class="btn-primary" :disabled="confirming">{{ confirming ? '保存中...' : '确认角色，下一步' }}</button>
     </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useCharacterStore } from '../stores/character'
import * as v2Api from '../api/v2'
import RelationGraph from '../components/RelationGraph.vue'
import { useGeneration } from '../composables/useGeneration'
import { setupConfirm } from '../composables/useConfirm'
import { setupErrorBar } from '../composables/useErrorBar'
import { vKeyboardClick } from '../directives/keyboardClick'
import { useAutoSave } from '../composables/useAutoSave'
import { useToastStore } from '../stores/toast'

const props = defineProps<{ projectId: string }>()
const emit = defineEmits<{ complete: [data: any] }>()
const confirmDialog = setupConfirm()
const errorBar = setupErrorBar()
const toast = useToastStore()
const pageLoading = ref(true)
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
const confirming = ref(false)
const error = ref('')
const checkResultMsg = ref('')
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

const villainDims = [
  { key: 'name', label: '姓名', placeholder: '反派姓名' },
  { key: 'tier', label: '等级', placeholder: '小Boss/中Boss/大Boss/终极Boss' },
  { key: 'motivation', label: '动机', placeholder: '作恶的根本原因' },
  { key: 'trait', label: '性格', placeholder: '性格特点' },
  { key: 'appearance', label: '外貌', placeholder: '外貌特征' },
  { key: 'background', label: '背景', placeholder: '背景故事' },
  { key: 'goal', label: '目标', placeholder: '角色追求的终极目标' },
  { key: 'relation', label: '与主角关系', placeholder: '如：宿敌/仇人/对手' },
]

const protagonist = reactive<any>({})
const supportingChars = ref<any[]>([])
const villains = ref<any[]>([])
const relations = ref<any[]>([])
const selectedVillain = ref<any>(null)

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

function handleTabKeydown(dir: number, e: KeyboardEvent) {
  e.preventDefault()
  const idx = tabs.findIndex(t => t.key === activeTab.value)
  const next = (idx + dir + tabs.length) % tabs.length
  activeTab.value = tabs[next].key
}

const worldData = ref<any>(null)
const storyConcept = ref('')
const projectContext = ref<any>(null)

function enrichedStoryConcept(): string {
  const parts = [storyConcept.value]
  const ctx: string[] = []
  if (projectContext.value) {
    if (projectContext.value.sub_genre) ctx.push(`体裁: ${projectContext.value.sub_genre}`)
    if (projectContext.value.tone) ctx.push(`文风: ${projectContext.value.tone}`)
    if (projectContext.value.platform) ctx.push(`平台: ${projectContext.value.platform}`)
  }
  if (ctx.length > 0) {
    parts.push(`项目设定: ${ctx.join(', ')}`)
  }
  return parts.filter(Boolean).join(' | ')
}

function addChar() {
  if (!newChar.name) return
  supportingChars.value.push({ ...newChar })
  newChar.name = ''; newChar.role = ''; newChar.trait = ''
  showAddForm.value = false
}

async function deleteChar(idx: number) {
  const ok = await confirmDialog.confirm({
    message: '确定删除该角色？',
    detail: '删除后不可恢复',
    type: 'danger',
  })
  if (!ok) return
  supportingChars.value.splice(idx, 1)
  selectedChar.value = null
}

async function deleteVillain(idx: number) {
  const ok = await confirmDialog.confirm({
    message: '确定删除该反派？',
    detail: '删除后不可恢复',
    type: 'danger',
  })
  if (!ok) return
  villains.value.splice(idx, 1)
}

async function generate() {
  generating.value = true
  error.value = ''
  let generationSuccess = false
  gen.begin(4, '正在生成主角...')
  try {
    const result = await charStore.generateCharacters(
      props.projectId, worldData.value, enrichedStoryConcept() || undefined,
      (step: number, msg: string) => gen.progress(step, msg),
    )
    Object.assign(protagonist, result.protagonist || {})
    supportingChars.value = result.supporting || []
    villains.value = result.villains || []
    relations.value = (result.relations as any) || []
    generationSuccess = true
    const charData = { protagonist: { ...protagonist }, supporting: supportingChars.value, villains: villains.value, relations: relations.value }
    try {
      await v2Api.saveModuleData(props.projectId, 'characters', charData)
    } catch (_e) {
      toast.error('角色已生成但保存失败。数据暂存内存中,请不要关闭页面')
      gen.fail('保存失败')
      return
    }
  } catch (e: any) {
    errorBar.showError(e, () => generate())
  } finally {
    generating.value = false
    if (generationSuccess) gen.end()
    else gen.fail(error.value || '生成失败')
  }
}

async function checkConsistency() {
  error.value = ''  // 清除之前的错误
  try {
    const result = await v2Api.characterConsistencyCheck(props.projectId)
    if (result.passed) {
      checkResultMsg.value = `一致性检查通过 (${result.score || 100}分)`
    } else {
      checkResultMsg.value = `发现 ${result.issues?.length || 0} 个问题`
    }
  } catch (e: any) {
    error.value = '一致性检查失败: ' + (e?.message || '未知错误')
  }
}

async function confirm() {
  if (confirming.value) return
  cancel()
  const ok = await confirmDialog.confirm({
    message: '确定进入下一步？',
    detail: '确认后将保存当前角色设定并进入下一模块',
    type: 'info',
  })
  if (!ok) return
  confirming.value = true
  try {
    await charStore.saveCharacters(props.projectId, {
      protagonist: { ...protagonist },
      supporting: supportingChars.value,
      villains: villains.value,
      relations: relations.value,
    })
    toast.success('角色设定已保存')
    emit('complete', { protagonist, supporting: supportingChars.value, villains: villains.value })
  } catch (e: any) {
    toast.error('保存失败: ' + (e?.message || '未知错误'))
  } finally {
    confirming.value = false
  }
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
  } catch (_e) {
    console.debug('[CharacterView] restore saved data failed:', _e)
  }
  try {
    const allData = await v2Api.getAllModuleData(props.projectId)
    const world = allData?.modules?.['world']
    if (world) {
      worldData.value = world
      storyConcept.value = world.origin?.hiddenTruth || ''
    }
    const project = allData?.modules?.['project']
    if (project) {
      projectContext.value = project
    }
  } catch (_e) {
    console.debug('[CharacterView] prefill from world failed:', _e)
  }
  finally { pageLoading.value = false }
})

const charData = () => ({
  protagonist: { ...protagonist },
  supporting: supportingChars.value,
  villains: villains.value,
  relations: relations.value,
})
const { saveState, scheduleSave, cancel } = useAutoSave({
  dataRef: charData,
  saveFn: async (data) => {
    await v2Api.saveModuleData(props.projectId, 'characters', data)
  },
  debounce: 3000,
  storageKey: `characters_${props.projectId}`,
  onSaveError: () => toast.error('角色设定自动保存失败，已存至本地备份'),
  projectId: props.projectId,
  moduleName: 'characters',
})
watch([protagonist, supportingChars, villains, relations], () => {
  scheduleSave()
}, { deep: true })
watch(activeTab, () => { checkResultMsg.value = '' })
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
.villain-card { border: 1px solid #eee; border-radius: 8px; padding: 16px; margin-bottom: 10px; cursor: pointer; transition: 0.15s; }
.villain-card:hover { border-color: var(--primary); }
.villain-card.active { border-color: var(--primary); background: #f0f8ff; }
.villain-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 13px; }
.villain-name { font-weight: 600; margin-bottom: 5px; }
.tier { font-size: 14px; padding: 1px 6px; background: #fff1f0; color: #ff4d4f; border-radius: 4px; }
.villain-motivation { font-size: 17px; color: #666; }
.btn-delete-sm { background: none; border: none; color: #c62828; font-size: 18px; cursor: pointer; margin-left: 6px; vertical-align: middle; line-height: 1; }
.btn-delete-sm:hover { color: #ff0000; }
.actions { display: flex; gap: 13px; margin-top: 21px; }
.btn-primary { padding: 13px 24px; background: var(--primary); color: #fff; border: none; border-radius: 8px; cursor: pointer; }
.btn-primary:disabled { opacity: 0.5; cursor: wait; }
.btn-secondary { padding: 13px 20px; background: #f5f5f5; border: 1px solid #ddd; border-radius: 8px; cursor: pointer; }

.spinner { display: inline-block; width: 14px; height: 14px; border: 2px solid #fff; border-top-color: transparent; border-radius: 50%; animation: spin 0.8s linear infinite; margin-right: 6px; }
@keyframes spin { to { transform: rotate(360deg); } }
.error-box { color: #e74c3c; background: #fff1f0; border-radius: 8px; padding: 12px; margin-top: 12px; font-size: 14px; }
.page-loading { display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 300px; gap: 16px; }
.loading-spinner { width: 36px; height: 36px; border: 3px solid #f0f0f0; border-top-color: #409eff; border-radius: 50%; animation: spin 0.8s linear infinite; }
</style>
