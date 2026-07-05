<template>
  <div class="world-view">
    <div class="tabs">
      <div v-for="tab in tabs" :key="tab.key" class="tab" :class="{ active: activeTab === tab.key }" @click="activeTab = tab.key">
        {{ tab.label }}
      </div>
    </div>

    <div class="tab-content">
      <div v-if="activeTab === 'origin'" class="tab-pane">
        <h3>世界本源</h3>
        <div class="form-group">
          <label>世界类型</label>
          <select v-model="world.origin.worldType" class="form-select">
            <option>低魔世界</option><option>中魔世界</option><option>高魔世界</option>
            <option>科幻宇宙</option><option>末日废土</option><option>现实平行</option>
          </select>
        </div>
        <div class="form-group">
          <label>起源故事</label>
          <textarea v-model="world.origin.originStory" class="form-textarea" rows="4" placeholder="世界的起源..." />
        </div>
        <div class="form-group">
          <label>隐藏真相</label>
          <textarea v-model="world.origin.hiddenTruth" class="form-textarea" rows="3" placeholder="世界背后隐藏的秘密..." />
        </div>
      </div>

      <div v-if="activeTab === 'rules'" class="tab-pane">
        <h3>世界规则 (6要素)</h3>
        <div class="rules-grid">
          <div v-for="rule in worldRules" :key="rule.key" class="rule-card">
            <div class="rule-name">{{ rule.name }}</div>
            <textarea v-model="world.rules[rule.key]" class="form-textarea" rows="2" :placeholder="rule.placeholder" />
          </div>
        </div>
      </div>

      <div v-if="activeTab === 'structure'" class="tab-pane">
        <h3>世界层级结构</h3>
        <WorldMapTree :structure="world.structure" />
      </div>

      <div v-if="activeTab === 'civilization'" class="tab-pane">
        <h3>文明体系 (8维度)</h3>
        <div class="civ-grid">
          <div v-for="dim in civDimensions" :key="dim.key" class="civ-card">
            <div class="civ-name">{{ dim.name }}</div>
            <textarea v-model="world.civilization[dim.key]" class="form-textarea" rows="2" />
          </div>
        </div>
      </div>

      <div v-if="activeTab === 'history'" class="tab-pane">
        <h3>历史时间线</h3>
        <TimelineChart :events="world.history" />
      </div>
    </div>

    <div class="actions">
      <button @click="generate" :disabled="generating" class="btn-primary">{{ generating ? '生成中...' : 'AI生成世界观' }}</button>
      <button @click="checkConsistency" class="btn-secondary">一致性检查</button>
      <button @click="confirm" class="btn-confirm">确认世界观,下一步</button>
    </div>
    <div v-if="checkResult" class="check-result">
      <span :class="checkResult.passed ? 'pass' : 'fail'">{{ checkResult.message }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useWorldStore } from '../stores/world'
import * as v2Api from '../api/v2'
import WorldMapTree from '../components/WorldMapTree.vue'
import TimelineChart from '../components/TimelineChart.vue'

const props = defineProps<{ projectId: string }>()
const emit = defineEmits<{ complete: [data: any] }>()

const worldStore = useWorldStore()
const tabs = [
  { key: 'origin', label: '本源' },
  { key: 'rules', label: '规则' },
  { key: 'structure', label: '结构' },
  { key: 'civilization', label: '文明' },
  { key: 'history', label: '历史' },
]
const activeTab = ref('origin')
const generating = ref(false)
const checkResult = ref<any>(null)

const world = reactive<any>({
  origin: { worldType: '', originStory: '', hiddenTruth: '' },
  rules: {},
  structure: {},
  civilization: {},
  history: [],
})

const worldRules = [
  { key: 'power', name: '力量体系', placeholder: '修炼/异能的核心规则...' },
  { key: 'economy', name: '经济系统', placeholder: '货币、资源、交易规则...' },
  { key: 'politics', name: '政治结构', placeholder: '国家、势力、权力分配...' },
  { key: 'technology', name: '科技水平', placeholder: '科技树限制、核心原理...' },
  { key: 'culture', name: '文化习俗', placeholder: '节日、禁忌、礼仪...' },
  { key: 'taboo', name: '禁忌规则', placeholder: '世界底层限制、因果律...' },
]

const civDimensions = [
  { key: 'government', name: '政体' }, { key: 'religion', name: '信仰' },
  { key: 'military', name: '军事' }, { key: 'education', name: '教育' },
  { key: 'art', name: '艺术' }, { key: 'trade', name: '贸易' },
  { key: 'law', name: '法律' }, { key: 'class', name: '阶级' },
]

async function generate() {
  generating.value = true
  try {
    const result = await worldStore.generateWorld(props.projectId, world.origin)
    Object.assign(world, result)
  } finally {
    generating.value = false
  }
}

async function checkConsistency() {
  const result = await v2Api.worldConsistencyCheck(props.projectId)
  checkResult.value = result
}

async function confirm() {
  await worldStore.saveWorld(props.projectId, world)
  emit('complete', world)
}
</script>

<style scoped>
.world-view { max-width: 900px; margin: 0 auto; }
.tabs { display: flex; gap: 2px; margin-bottom: 0; }
.tab { padding: 10px 20px; background: #f5f5f5; border: 1px solid #ddd; border-bottom: none; border-radius: 6px 6px 0 0; cursor: pointer; font-size: 13px; font-weight: 500; }
.tab.active { background: #fff; border-color: #eee; color: var(--primary); }
.tab-content { background: #fff; border: 1px solid #eee; border-radius: 0 6px 6px 6px; padding: 20px; }
.tab-pane h3 { margin: 0 0 16px; font-size: 16px; }
.form-group { margin-bottom: 14px; }
.form-group label { display: block; font-weight: 600; margin-bottom: 6px; font-size: 13px; color: #555; }
.form-select, .form-textarea { width: 100%; padding: 8px 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 13px; }
.rules-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }
.rule-card { border: 1px solid #eee; border-radius: 6px; padding: 12px; }
.rule-name { font-weight: 600; margin-bottom: 6px; font-size: 13px; }
.civ-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; }
.civ-card { border: 1px solid #eee; border-radius: 6px; padding: 12px; }
.civ-name { font-weight: 600; margin-bottom: 6px; font-size: 13px; }
.actions { display: flex; gap: 10px; margin-top: 16px; }
.btn-primary { padding: 10px 24px; background: var(--primary); color: #fff; border: none; border-radius: 6px; cursor: pointer; }
.btn-primary:disabled { opacity: 0.5; cursor: wait; }
.btn-secondary { padding: 10px 20px; background: #f5f5f5; border: 1px solid #ddd; border-radius: 6px; cursor: pointer; }
.btn-confirm { padding: 10px 24px; background: #52c41a; color: #fff; border: none; border-radius: 6px; cursor: pointer; margin-left: auto; }
.check-result { margin-top: 10px; font-size: 13px; text-align: center; }
.check-result .pass { color: #52c41a; }
.check-result .fail { color: #ff4d4f; }
</style>
