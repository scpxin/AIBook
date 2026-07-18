<template>
  <div class="power-system-view">
    <div v-if="pageLoading" class="page-loading">
      <div class="loading-spinner"></div>
      <p>加载中...</p>
    </div>
    <div v-else>
    <div class="section">
      <h3>力量体系设计</h3>
      <p class="tip">设计修炼等级、战斗方式、能力限制等核心设定</p>

      <div class="form-group">
        <label>体系类型</label>
        <select v-model="form.systemType" class="form-select">
          <option value="cultivation">修真炼丹</option>
          <option value="magic">魔法斗气</option>
          <option value="superpower">异能觉醒</option>
          <option value="martial">武侠内功</option>
          <option value="science">科技进化</option>
          <option value="mix">混合体系</option>
        </select>
      </div>

      <div class="form-group">
        <label>核心能量名称</label>
        <input v-model="form.energyName" placeholder="如：灵力、斗气、念力..." class="form-input" />
      </div>

      <div class="form-group">
        <label>等级设定（每行一个，从低到高）</label>
        <textarea v-model="form.levels" rows="6" placeholder="练气期&#10;筑基期&#10;金丹期&#10;元婴期&#10;化神期" class="form-textarea"></textarea>
      </div>

      <div class="form-group">
        <label>核心规则/限制</label>
        <textarea v-model="form.rules" rows="4" placeholder="设定力量的来源、使用限制、副作用等..." class="form-textarea"></textarea>
      </div>

      <div class="form-group">
        <label>参考世界观</label>
        <div class="context-hint" v-if="upstreamData">{{ upstreamData }}</div>
        <div class="context-hint empty" v-else>暂无世界观数据</div>
      </div>

      <div class="action-row">
         <button @click="proceed" :disabled="loading" class="btn btn-primary">
           <span v-if="loading" class="spinner"></span>{{ loading ? '生成中...' : 'AI生成力量体系' }}
         </button>
         <button @click="$emit('skip', null)" class="btn btn-ghost">跳过</button>
      </div>

      <div v-if="error" class="error-box">
        <p>{{ error }}</p>
        <button @click="useOfflineMode" class="btn btn-ghost btn-sm">使用离线模板</button>
      </div>
    </div>

    <div v-if="resultLevels.length" class="section">
      <h3>生成结果</h3>
      <div v-for="(level, idx) in resultLevels" :key="idx" class="level-card" tabindex="0">
        <div class="level-header">
          <span class="level-index">L{{ idx + 1 }}</span>
          <span class="level-name">{{ level.name || level.title || '未命名' }}</span>
          <span v-if="level.threshold" class="level-threshold">{{ level.threshold }}</span>
        </div>
        <div class="level-desc">{{ level.desc || level.description || level.power_description || '' }}</div>
        <div v-if="level.lifespan" class="level-meta">寿元: {{ level.lifespan }}</div>
        <div v-if="level.abilities" class="level-abilities">
          <span v-for="ab in (Array.isArray(level.abilities) ? level.abilities : [level.abilities])" :key="ab" class="ability-tag">{{ ab }}</span>
        </div>
      </div>
      <button @click="confirm" class="btn btn-primary btn-complete">确认并通过</button>
    </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import * as v2Api from '../api/v2'
import { useGeneration } from '../composables/useGeneration'
import { setupConfirm } from '../composables/useConfirm'
import { setupErrorBar } from '../composables/useErrorBar'
import { useAutoSave } from '../composables/useAutoSave'
import { useToastStore } from '../stores/toast'

const props = defineProps<{ projectId: string }>()
const emit = defineEmits<{ complete: [data: any]; skip: [data: any] }>()
const gen = useGeneration('power_system', '力量体系')
const confirmDialog = setupConfirm()
const errorBar = setupErrorBar()
const pageLoading = ref(true)

const form = reactive({
  systemType: 'cultivation',
  energyName: '灵力',
  levels: '',
  rules: '',
})
const loading = ref(false)
const error = ref('')
const resultLevels = ref<any[]>([])
const upstreamData = ref('')
const isOffline = ref(false)

const resultData = computed(() => ({
  systemType: form.systemType,
  energyName: form.energyName,
  levels: form.levels,
  rules: form.rules,
  levelDetails: resultLevels.value,
}))

onMounted(async () => {
  try {
    const saved = await v2Api.getModuleData(props.projectId, 'power_system')
    if (saved?.data) {
      const d = saved.data
      if (d.systemType) form.systemType = d.systemType
      if (d.energyName) form.energyName = d.energyName
      if (d.levels) form.levels = typeof d.levels === 'string' ? d.levels : d.levels.join('\n')
      if (d.rules) form.rules = d.rules
      if (d.levelDetails) resultLevels.value = d.levelDetails
      if (d.upstreamData) upstreamData.value = d.upstreamData
    } else {
      const allData = await v2Api.getAllModuleData(props.projectId)
      const world = allData?.modules?.['world']
      if (world) {
        const rules = world.rules || {}
        upstreamData.value = `已加载世界观: ${world.origin?.worldType || '未知类型'}`
        if (!form.rules && typeof rules === 'object') {
          form.rules = Object.entries(rules).map(([k, v]) => `${k}: ${v}`).join('\n')
        }
      }
    }
  } catch (_e) { /* ignore */ } finally { pageLoading.value = false }
})

const toast = useToastStore()
const powerData = () => ({ ...form, upstreamData: upstreamData.value, levelDetails: resultLevels.value })
const { saveState, scheduleSave } = useAutoSave({
  dataRef: powerData,
  saveFn: async (data) => {
    await v2Api.saveModuleData(props.projectId, 'power_system', data)
  },
  debounce: 2000,
  storageKey: `power_${props.projectId}`,
  onSaveError: () => toast.error('力量体系自动保存失败，已存至本地备份'),
  projectId: props.projectId,
  moduleName: 'power_system',
})
watch(form, () => {
  scheduleSave()
}, { deep: true })

async function proceed() {
  loading.value = true
  gen.begin()
  error.value = ''
  isOffline.value = false
  try {
    const allData = await v2Api.getAllModuleData(props.projectId)
    const world = allData?.modules?.['world']
    const result = await v2Api.generatePowerSystem(props.projectId, {
      system_type: form.systemType,
      energy_name: form.energyName,
      levels: form.levels.split('\n').filter(Boolean),
      rules: form.rules,
      world_rules: world?.rules || {},
      world_type: world?.origin?.worldType || '',
    })
    resultLevels.value = result.tiers || []
    if (!resultLevels.value.length) {
      resultLevels.value = buildLocalLevels()
    }
    try { await v2Api.saveModuleData(props.projectId, 'power_system', resultData.value) } catch (_e) { /* ignore */ }
  } catch (e: any) {
     errorBar.showError(e, () => proceed())
    useOfflineMode()
  } finally {
    loading.value = false
    if (!error.value) gen.end()
    else gen.fail(error.value)
  }
}

async function confirm() {
  const ok = await confirmDialog.confirm({
    message: '确定进入下一步？',
    detail: '确认后将保存当前力量体系数据并进入下一模块',
    type: 'info',
  })
  if (!ok) return
  try { await v2Api.saveModuleData(props.projectId, 'power_system', powerData()) } catch (_e) { /* ignore */ }
  emit('complete', resultData.value)
}

function buildLocalLevels() {
  const levels = form.levels.split('\n').filter(Boolean)
  return levels.map((name, i) => ({
    name,
    desc: getLevelDesc(i, form.systemType),
  }))
}

function getLevelDesc(idx: number, type: string): string {
  const descs: Record<string, string[]> = {
    cultivation: ['初窥门径，感应天地灵气', '灵气入体，淬炼经脉', '凝液化固，道基初成', '丹道合一，元神初现', '化虚合道，超凡入圣'],
    magic: ['魔法学徒，初步感知元素', '初级法师，掌握基础咒语', '中级法师，能释放强力法术', '大法师，精通多系禁咒', '大贤者，触及魔法本源'],
    martial: ['入门扎桩，锻炼体魄', '小有所成，内力初显', '打通经脉，真气运转', '一代宗师，开宗立派', '天人合一，武道通神'],
  }
  const arr = descs[type] || descs.cultivation
  return arr[Math.min(idx, arr.length - 1)]
}

function useOfflineMode() {
  isOffline.value = true
  resultLevels.value = buildLocalLevels()
}
</script>

<style scoped>
.power-system-view { max-width: 900px; }
.section { background: #fff; border-radius: 16px; padding: 28px; margin-bottom: 20px; box-shadow: 0 4px 16px rgba(0,0,0,.06); }
.section h3 { font-size: 22px; margin-bottom: 10px; }
.tip { color: #888; margin-bottom: 20px; font-size: 16px; }
.context-hint { padding: 8px 12px; background: #f0f8ff; border: 1px solid #d4eaff; border-radius: 8px; font-size: 13px; color: #4a90d9; margin-bottom: 14px; }
.context-hint.empty { background: #fff8e1; border-color: #ffe082; color: #f57c00; }
.form-group { margin-bottom: 18px; }
.form-group label { display: block; font-weight: 600; margin-bottom: 8px; font-size: 16px; color: #555; }
.form-select, .form-input { width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 10px; font-size: 16px; }
.form-textarea { width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 10px; font-size: 16px; resize: vertical; min-height: 120px; font-family: inherit; }
.action-row { display: flex; gap: 12px; margin-top: 20px; }
.btn { border: none; border-radius: 10px; padding: 12px 24px; font-size: 16px; font-weight: 600; cursor: pointer; }
.btn-sm { padding: 8px 16px; font-size: 14px; }
.btn-primary { background: linear-gradient(135deg, var(--primary), var(--primary-light)); color: #fff; }
.btn-ghost { background: #f0f0f0; color: #555; }
.btn-complete { margin-top: 20px; }
.error-box { margin-top: 16px; padding: 16px; background: #fff3f3; border: 1px solid #ffcdd2; border-radius: 10px; }
.error-box p { color: #c62828; margin-bottom: 8px; }
.level-card { border: 1px solid #eee; border-radius: 12px; padding: 16px; margin-bottom: 12px; background: #fafafa; }
.level-name { font-weight: 700; font-size: 18px; color: var(--primary); margin-bottom: 6px; }
.level-desc { color: #666; font-size: 15px; }
.level-abilities { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px; }
.ability-tag { font-size: 12px; padding: 2px 8px; background: #e8f4fd; color: var(--primary); border-radius: 4px; }
.spinner { display: inline-block; width: 14px; height: 14px; border: 2px solid #fff; border-top-color: transparent; border-radius: 50%; animation: spin 0.8s linear infinite; margin-right: 6px; }
@keyframes spin { to { transform: rotate(360deg); } }
.page-loading { display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 300px; gap: 16px; }
.loading-spinner { width: 36px; height: 36px; border: 3px solid #f0f0f0; border-top-color: #409eff; border-radius: 50%; animation: spin 0.8s linear infinite; }
</style>
