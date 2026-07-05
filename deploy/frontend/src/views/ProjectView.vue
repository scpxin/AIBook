<template>
  <div class="project-view">
    <div class="section">
      <h3>平台选择</h3>
      <div class="platform-grid">
        <div v-for="p in platforms" :key="p.id" class="platform-card" :class="{ active: selectedPlatform === p.id }" @click="selectedPlatform = p.id">
          <strong>{{ p.name }}</strong>
          <span>{{ p.desc }}</span>
        </div>
      </div>
    </div>

    <div class="section">
      <h3>12维度分析</h3>
      <div class="dimension-list">
        <div v-for="dim in dimensions" :key="dim.key" class="dimension-item">
          <div class="dim-header" @click="toggleDim(dim.key)">
            <span class="dim-name">{{ dim.name }}</span>
            <span class="dim-toggle">{{ expandedDims.includes(dim.key) ? '▼' : '▶' }}</span>
          </div>
          <div v-if="expandedDims.includes(dim.key)" class="dim-content">
            <div v-for="(val, k) in dim.values" :key="k" class="dim-field">
              <span class="field-label">{{ k }}:</span>
              <span class="field-value">{{ val }}</span>
            </div>
            <button class="btn-edit" @click="editDimension(dim.key)">编辑</button>
          </div>
        </div>
      </div>
    </div>

    <div class="section">
      <h3>兼容性检查</h3>
      <div class="compat-results">
        <div v-for="r in compatResults" :key="r.name" class="compat-item">
          <span class="compat-name">{{ r.name }}</span>
          <span class="compat-status" :class="r.passed ? 'pass' : 'fail'">{{ r.passed ? '通过' : '不通过' }}</span>
        </div>
      </div>
      <button @click="confirm" class="btn-confirm">确认定位,下一步</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import * as v2Api from '../api/v2'

const props = defineProps<{ projectId: string }>()
const emit = defineEmits<{ complete: [data: any] }>()

const platforms = [
  { id: 'fanqie', name: '番茄', desc: '免费网文,男频女频' },
  { id: 'qidian', name: '起点', desc: '付费男频为主' },
  { id: 'qimao', name: '七猫', desc: '免费+短篇' },
  { id: 'custom', name: '自定义', desc: '灵活配置' },
]
const selectedPlatform = ref('fanqie')
const dimensions = ref<any[]>([])
const expandedDims = ref<string[]>([])
const compatResults = ref<any[]>([])

function toggleDim(key: string) {
  const idx = expandedDims.value.indexOf(key)
  if (idx >= 0) expandedDims.value.splice(idx, 1)
  else expandedDims.value.push(key)
}

function editDimension(key: string) {
  // TODO: open edit modal
}

async function confirm() {
  await v2Api.compatibilityCheck(props.projectId, selectedPlatform.value)
  emit('complete', { platform: selectedPlatform.value, dimensions: dimensions.value })
}
</script>

<style scoped>
.project-view { max-width: 800px; margin: 0 auto; }
.section { background: #fff; border: 1px solid #eee; border-radius: 8px; padding: 20px; margin-bottom: 16px; }
.section h3 { margin: 0 0 12px; font-size: 16px; }
.platform-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 10px; }
.platform-card { border: 1px solid #ddd; border-radius: 6px; padding: 14px; cursor: pointer; display: flex; flex-direction: column; gap: 4px; transition: 0.15s; }
.platform-card strong { font-size: 14px; }
.platform-card span { font-size: 12px; color: #888; }
.platform-card:hover { border-color: var(--primary); }
.platform-card.active { border-color: var(--primary); background: #f0f8ff; }
.dimension-list { display: flex; flex-direction: column; gap: 4px; }
.dimension-item { border: 1px solid #f0f0f0; border-radius: 4px; }
.dim-header { display: flex; justify-content: space-between; padding: 8px 12px; cursor: pointer; font-weight: 500; }
.dim-toggle { font-size: 10px; color: #999; }
.dim-content { padding: 8px 12px; border-top: 1px solid #f0f0f0; }
.dim-field { display: flex; gap: 8px; padding: 2px 0; font-size: 13px; }
.field-label { font-weight: 600; color: #555; min-width: 80px; }
.field-value { color: #666; }
.btn-edit { margin-top: 8px; padding: 4px 12px; background: #f5f5f5; border: 1px solid #ddd; border-radius: 4px; font-size: 12px; cursor: pointer; }
.compat-results { display: flex; flex-direction: column; gap: 4px; margin-bottom: 16px; }
.compat-item { display: flex; justify-content: space-between; font-size: 13px; padding: 4px 0; }
.compat-name { color: #555; }
.compat-status.pass { color: #52c41a; }
.compat-status.fail { color: #ff4d4f; }
.btn-confirm { width: 100%; padding: 10px; background: #52c41a; color: #fff; border: none; border-radius: 6px; font-size: 15px; cursor: pointer; }
</style>
