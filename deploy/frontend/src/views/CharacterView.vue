<template>
  <div class="character-view">
    <div class="tabs">
      <div v-for="t in tabs" :key="t.key" class="tab" :class="{ active: activeTab === t.key }" @click="activeTab = t.key">{{ t.label }}</div>
    </div>

    <div class="tab-content">
      <div v-if="activeTab === 'protagonist'" class="tab-pane">
        <h3>主角档案 (九维)</h3>
        <div class="char-form-grid">
          <div v-for="dim in nineDims" :key="dim.key" class="form-group">
            <label>{{ dim.label }}</label>
            <input v-model="protagonist[dim.key]" class="form-input" :placeholder="dim.placeholder" />
          </div>
        </div>
      </div>

      <div v-if="activeTab === 'supporting'" class="tab-pane">
        <h3>配角列表</h3>
        <div class="char-grid">
          <div v-for="(c, idx) in supportingChars" :key="idx" class="char-card" @click="selectedChar = c">
            <div class="char-name">{{ c.name }}</div>
            <div class="char-role">{{ c.role }}</div>
            <div class="char-trait">{{ c.trait }}</div>
          </div>
        </div>
        <div v-if="selectedChar" class="char-detail">
          <h4>{{ selectedChar.name }} 详情</h4>
          <pre>{{ JSON.stringify(selectedChar, null, 2) }}</pre>
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

    <div class="actions">
      <button @click="generate" :disabled="generating" class="btn-primary">{{ generating ? '生成中...' : 'AI生成角色' }}</button>
      <button @click="checkConsistency" class="btn-secondary">一致性检查</button>
      <button @click="confirm" class="btn-confirm">确认角色,下一步</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { useCharacterStore } from '../stores/character'
import * as v2Api from '../api/v2'
import RelationGraph from '../components/RelationGraph.vue'

const props = defineProps<{ projectId: string }>()
const emit = defineEmits<{ complete: [data: any] }>()
const charStore = useCharacterStore()

const tabs = [
  { key: 'protagonist', label: '主角' },
  { key: 'supporting', label: '配角' },
  { key: 'villain', label: '反派' },
  { key: 'relations', label: '关系' },
]
const activeTab = ref('protagonist')
const generating = ref(false)
const selectedChar = ref<any>(null)

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

async function generate() {
  generating.value = true
  try {
    const result = await charStore.generateCharacters(props.projectId)
    Object.assign(protagonist, result.protagonist || {})
    supportingChars.value = result.supporting || []
    villains.value = result.villains || []
    relations.value = (result.relations as any) || []
  } finally {
    generating.value = false
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
</script>

<style scoped>
.character-view { max-width: 900px; margin: 0 auto; }
.tabs { display: flex; gap: 2px; margin-bottom: 0; }
.tab { padding: 10px 20px; background: #f5f5f5; border: 1px solid #ddd; border-bottom: none; border-radius: 6px 6px 0 0; cursor: pointer; font-size: 13px; font-weight: 500; }
.tab.active { background: #fff; border-color: #eee; color: var(--primary); }
.tab-content { background: #fff; border: 1px solid #eee; border-radius: 0 6px 6px 6px; padding: 20px; min-height: 300px; }
.tab-pane h3 { margin: 0 0 16px; font-size: 16px; }
.char-form-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
.form-group label { display: block; font-weight: 600; margin-bottom: 4px; font-size: 12px; color: #555; }
.form-input { width: 100%; padding: 6px 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 13px; }
.char-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 10px; }
.char-card { border: 1px solid #eee; border-radius: 6px; padding: 12px; cursor: pointer; transition: 0.15s; }
.char-card:hover { border-color: var(--primary); box-shadow: 0 2px 6px rgba(0,0,0,0.06); }
.char-name { font-weight: 600; margin-bottom: 4px; }
.char-role { font-size: 12px; color: #888; }
.char-trait { font-size: 11px; color: #aaa; margin-top: 4px; }
.char-detail { margin-top: 16px; background: #f9f9f9; border-radius: 6px; padding: 14px; }
.char-detail h4 { margin: 0 0 8px; }
.char-detail pre { font-size: 11px; white-space: pre-wrap; word-break: break-all; }
.villain-card { border: 1px solid #eee; border-radius: 6px; padding: 12px; margin-bottom: 8px; }
.villain-name { font-weight: 600; margin-bottom: 4px; }
.tier { font-size: 11px; padding: 1px 6px; background: #fff1f0; color: #ff4d4f; border-radius: 3px; }
.villain-motivation { font-size: 13px; color: #666; }
.actions { display: flex; gap: 10px; margin-top: 16px; }
.btn-primary { padding: 10px 24px; background: var(--primary); color: #fff; border: none; border-radius: 6px; cursor: pointer; }
.btn-primary:disabled { opacity: 0.5; cursor: wait; }
.btn-secondary { padding: 10px 20px; background: #f5f5f5; border: 1px solid #ddd; border-radius: 6px; cursor: pointer; }
.btn-confirm { padding: 10px 24px; background: #52c41a; color: #fff; border: none; border-radius: 6px; cursor: pointer; margin-left: auto; }
</style>
