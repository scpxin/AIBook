<template>
  <div class="modules-overview">
    <div class="overview-header">
      <h2>13模块流水线总览</h2>
      <p class="sub">查看各模块生成状态与数据概览</p>
    </div>

    <div class="top-bar">
      <select v-model="selectedPid" class="project-select" @change="onProjectChange">
        <option value="">-- 选择项目 --</option>
        <option v-for="p in projectList" :key="p.id" :value="p.id">{{ p.name }}</option>
      </select>
      <button v-if="selectedPid" class="btn-refresh" @click="reload">刷新</button>
    </div>

    <div v-if="!selectedPid" class="empty">请先选择一个项目</div>

    <div v-else-if="loading" class="loading">加载中...</div>

    <template v-else-if="modules.length">
      <div class="progress-summary">
        <div class="progress-bar-track">
          <div class="progress-bar-fill" :style="{ width: progressPct + '%' }"></div>
        </div>
        <div class="progress-stats">
          <span class="stat done">已完成 {{ counts.done }}</span>
          <span class="stat generating" v-if="counts.generating">生成中 {{ counts.generating }}</span>
          <span class="stat failed" v-if="counts.failed">失败 {{ counts.failed }}</span>
          <span class="stat pending">剩余 {{ 13 - counts.done }}</span>
        </div>
      </div>

      <div class="filter-bar">
        <input v-model="searchQuery" placeholder="搜索模块名称..." class="search-input" />
        <div class="filter-btns">
          <button v-for="f in filters" :key="f.key" @click="statusFilter = f.key" :class="{ active: statusFilter === f.key }" class="filter-btn">{{ f.label }}</button>
        </div>
      </div>

      <div class="modules-grid">
        <div
          v-for="(mod, idx) in filteredModules"
          :key="mod.name"
          class="module-card"
          :class="{
            done: getModuleStatus(mod.name) === 'done',
            active: getModuleStatus(mod.name) === 'generating',
            failed: getModuleStatus(mod.name) === 'failed',
            locked: getModuleStatus(mod.name) === 'locked',
          }"
          tabindex="0" @click="navigateToModule(mod.name)" @keydown.enter="navigateToModule(mod.name)"
        >
          <div class="card-header">
            <span class="card-idx">{{ idx + 1 }}</span>
            <span class="card-name">{{ mod.display_name || mod.name }}</span>
            <span class="card-badge" :class="'badge-' + (getModuleStatus(mod.name) || 'pending')">
              {{ statusText(getModuleStatus(mod.name)) }}
            </span>
          </div>
          <div class="card-body">
            <div class="card-layer-tag">{{ mod.layer }}</div>
            <div v-if="mod.dependencies?.length" class="card-deps">
              上游: {{ mod.dependencies.join(' / ') }}
            </div>
            <div class="card-data-preview" v-if="moduleData[mod.name] != null">
              {{ getDataPreview(mod.name) }}
            </div>
            <div class="card-data-preview empty-data" v-else-if="getModuleStatus(mod.name) === 'done'">
              暂无数据
            </div>
          </div>
          <div class="card-footer" v-if="getModuleTime(mod.name)">
            <span class="card-time">{{ getModuleTime(mod.name) }}</span>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { usePipelineStore } from '../stores/pipeline'
import { useProjectStore } from '../stores/project'
import { useToastStore } from '../stores/toast'
import { getAllModuleData } from '../api/v2'
import type { PipelineProgress } from '../types/v2'

const router = useRouter()
const pipeline = usePipelineStore()
const project = useProjectStore()
const toast = useToastStore()
const modules = ref<any[]>([])
const progress = ref<PipelineProgress | null>(null)
const moduleData = ref<Record<string, any>>({})
const loading = ref(false)
const searchQuery = ref('')
const statusFilter = ref('all')
const selectedPid = ref('')
const projectList = ref<{ id: string; name: string }[]>([])

const filters = [
  { key: 'all', label: '全部' },
  { key: 'done', label: '已完成' },
  { key: 'generating', label: '生成中' },
  { key: 'failed', label: '失败' },
  { key: 'pending', label: '待开始' },
  { key: 'locked', label: '未解锁' },
]

const progressPct = computed(() => progress.value?.progressPct || 0)

const counts = computed(() => {
  const m = progress.value?.modules || {}
  let done = 0, generating = 0, failed = 0
  for (const v of Object.values(m)) {
    if (v.status === 'done') done++
    else if (v.status === 'generating') generating++
    else if (v.status === 'failed') failed++
  }
  return { done, generating, failed }
})

const filteredModules = computed(() => {
  let list = modules.value
  if (searchQuery.value.trim()) {
    const q = searchQuery.value.trim().toLowerCase()
    list = list.filter(m => (m.display_name || m.name).toLowerCase().includes(q))
  }
  if (statusFilter.value !== 'all') {
    list = list.filter(m => getModuleStatus(m.name) === statusFilter.value)
  }
  return list
})

function getModuleStatus(name: string): string {
  return progress.value?.modules?.[name]?.status || 'pending'
}

function statusText(s: string): string {
  const map: Record<string, string> = { done: '已完成', generating: '生成中', failed: '失败', locked: '未解锁', pending: '待开始' }
  return map[s] || '待开始'
}

function getModuleTime(name: string): string {
  const m = progress.value?.modules?.[name]
  if (!m?.completedAt) return ''
  try {
    return new Date(m.completedAt).toLocaleString('zh-CN', { month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit' })
  } catch { return '' }
}

function navigateToModule(name: string) {
  if (getModuleStatus(name) !== 'locked' && selectedPid.value) {
    router.push(`/create-v2/${name}?project_id=${selectedPid.value}`)
  }
}

function getDataPreview(name: string): string {
  const data = moduleData.value[name]
  if (!data) return ''

  switch (name) {
    case 'world': {
      const parts: string[] = []
      if (data.origin || data.origin_name) parts.push(`世界观: ${data.origin_name || '已生成'}`)
      if (data.power_system && typeof data.power_system === 'object') {
        const tiers = Object.keys(data.power_system).length
        if (tiers) parts.push(`力量体系 ${tiers}阶`)
      }
      if (Array.isArray(data.factions) && data.factions.length) parts.push(`${data.factions.length}个势力`)
      return parts.join(' · ') || '已生成'
    }
    case 'characters': {
      if (Array.isArray(data)) return `${data.length}个角色`
      const chars = data.characters || data.items || data
      if (Array.isArray(chars)) return `${chars.length}个角色`
      return '已生成'
    }
    case 'architecture': {
      if (data.story_type || data.type) return `类型: ${data.story_type || data.type}`
      if (data.story?.type) return `类型: ${data.story.type}`
      return '已生成'
    }
    case 'outline': {
      if (data.total_chapters) return `${data.total_chapters}章大纲`
      if (Array.isArray(data.chapters)) return `${data.chapters.length}章大纲`
      if (Array.isArray(data)) return `${data.length}章大纲`
      return '已生成'
    }
    case 'volumes': {
      if (Array.isArray(data)) return `${data.length}卷`
      return '已生成'
    }
    case 'chapter_plan': {
      if (Array.isArray(data)) return `${data.length}章规划`
      if (data.chapters && Array.isArray(data.chapters)) return `${data.chapters.length}章规划`
      return '已生成'
    }
    case 'draft': {
      let total = 0
      const chapters = data.chapters || data
      if (typeof chapters === 'object' && chapters !== null) {
        for (const ch of Object.values(chapters)) {
          if (ch && typeof ch === 'object') {
            const item = ch as Record<string, any>
            total += Number(item.word_count || item.word_count_raw || item.char_count || 0)
          }
        }
      }
      return total ? `${total.toLocaleString()}字` : '已生成'
    }
    default:
      return '已生成'
  }
}

async function onProjectChange() {
  if (!selectedPid.value) {
    progress.value = null
    moduleData.value = {}
    return
  }
  loading.value = true
  try {
    await pipeline.loadStatus(selectedPid.value)
    progress.value = pipeline.progress
    const all = await getAllModuleData(selectedPid.value).catch(() => null)
    moduleData.value = all?.modules || {}
  } catch (e: any) {
    toast.error('加载失败: ' + (e?.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

async function reload() {
  await onProjectChange()
}

onMounted(async () => {
  await project.loadList()
  projectList.value = project.projectList.map(p => ({ id: p.id, name: p.name }))
  await pipeline.loadModules()
  modules.value = pipeline.modules

  const pid = router.currentRoute.value.query?.project_id as string
    || pipeline.currentProjectId
    || project.currentProjectId
  if (pid) {
    selectedPid.value = pid
    await onProjectChange()
  }
})
</script>

<style scoped>
.modules-overview { max-width: 1600px; margin: 0 auto; padding: 24px 16px; }
.overview-header { margin-bottom: 20px; }
.overview-header h2 { font-size: 24px; margin: 0 0 4px; }
.sub { color: #999; font-size: 14px; margin: 0; }

.top-bar { display: flex; gap: 10px; align-items: center; margin-bottom: 16px; }
.project-select { padding: 8px 12px; border: 1px solid #ddd; border-radius: 8px; font-size: 14px; min-width: 200px; background: #fff; }
.btn-refresh { padding: 8px 16px; border: 1px solid #ddd; border-radius: 8px; background: #fff; cursor: pointer; font-size: 14px; }

.loading, .empty { text-align: center; padding: 60px 28px; color: #999; font-size: 16px; }

.progress-summary { margin-bottom: 20px; }
.progress-bar-track { height: 8px; background: #f0f0f0; border-radius: 4px; overflow: hidden; margin-bottom: 8px; }
.progress-bar-fill { height: 100%; background: var(--primary, #4a90d9); border-radius: 4px; transition: width .4s; }
.progress-stats { display: flex; gap: 16px; font-size: 14px; }
.stat { font-weight: 600; }
.stat.done { color: #52c41a; }
.stat.generating { color: #1890ff; }
.stat.failed { color: #ff4d4f; }
.stat.pending { color: #aaa; }

.filter-bar { display: flex; align-items: center; gap: 12px; margin-bottom: 18px; flex-wrap: wrap; }
.search-input { flex: 1; min-width: 200px; padding: 8px 12px; border: 1px solid #ddd; border-radius: 8px; font-size: 14px; }
.filter-btns { display: flex; gap: 6px; flex-wrap: wrap; }
.filter-btn { padding: 6px 12px; border: 1px solid #ddd; border-radius: 6px; background: #fff; cursor: pointer; font-size: 13px; transition: .15s; }
.filter-btn.active { background: var(--primary, #4a90d9); color: #fff; border-color: var(--primary, #4a90d9); }

.modules-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 12px; }
.module-card {
  background: #fff; border-radius: 12px; padding: 14px;
  box-shadow: 0 1px 6px rgba(0,0,0,.05); cursor: pointer; transition: .2s;
  border-left: 4px solid #e0e0e0; display: flex; flex-direction: column; gap: 8px;
}
.module-card:hover { transform: translateY(-1px); box-shadow: 0 3px 12px rgba(0,0,0,.1); }
.module-card.done { border-left-color: #52c41a; }
.module-card.active { border-left-color: #1890ff; }
.module-card.failed { border-left-color: #ff4d4f; }
.module-card.locked { opacity: 0.5; cursor: not-allowed; }
.card-header { display: flex; align-items: center; gap: 8px; }
.card-idx { width: 28px; height: 28px; border-radius: 6px; background: #f0f0f0; display: flex; align-items: center; justify-content: center; font-size: 14px; font-weight: 700; flex-shrink: 0; }
.done .card-idx { background: #52c41a; color: #fff; }
.active .card-idx { background: #1890ff; color: #fff; }
.failed .card-idx { background: #ff4d4f; color: #fff; }
.card-name { font-size: 15px; font-weight: 600; flex: 1; }
.card-badge { font-size: 12px; padding: 2px 8px; border-radius: 4px; font-weight: 600; flex-shrink: 0; }
.badge-done { background: #f6ffed; color: #52c41a; }
.badge-generating { background: #e6f7ff; color: #1890ff; }
.badge-failed { background: #fff1f0; color: #ff4d4f; }
.badge-locked { background: #f5f5f5; color: #999; }
.badge-pending { background: #fffbe6; color: #faad14; }
.card-body { display: flex; flex-direction: column; gap: 4px; }
.card-layer-tag { font-size: 12px; color: #aaa; background: #f8f8f8; padding: 1px 6px; border-radius: 4px; display: inline-block; width: fit-content; }
.card-deps { font-size: 12px; color: #888; }
.card-data-preview { font-size: 13px; color: #333; background: #f9fafb; padding: 6px 10px; border-radius: 6px; line-height: 1.5; }
.card-data-preview.empty-data { color: #bbb; }
.card-footer { display: flex; justify-content: flex-end; margin-top: auto; }
.card-time { font-size: 11px; color: #bbb; }
</style>
