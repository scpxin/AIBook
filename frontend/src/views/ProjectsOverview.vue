<template>
  <div class="po-page">
    <AppConfirmDialog />
    <div class="po-header">
      <h2>项目管理</h2>
      <p class="po-sub">管理您的所有小说项目，随时继续创作</p>
    </div>

    <div class="po-actions">
      <button class="po-btn po-btn-primary" @click="startNewProject">
        <span class="po-btn-icon">+</span>
        新建项目
      </button>
      <div class="po-search">
        <input
          v-model="searchQuery"
          type="text"
          placeholder="搜索项目..."
          class="po-search-input"
        />
      </div>
      <button class="po-btn" @click="loadProjects" :disabled="loading">
        ↻ 刷新
      </button>
      <select v-model="sortBy" class="po-select">
        <option value="recent">最近更新</option>
        <option value="name">按名称</option>
        <option value="progress">按进度</option>
      </select>
    </div>

     <div v-if="loading" class="po-loading">加载中...</div>

     <div v-else-if="!v2Projects.length && !otherProjects.length" class="po-empty">
       <div class="po-empty-icon">📚</div>
       <p>暂无项目</p>
       <button class="po-btn po-btn-primary" @click="startNewProject">创建第一个项目</button>
     </div>

     <div v-else class="po-content">
       <!-- V2 项目 -->
       <div v-if="v2Projects.length" class="po-section">
         <h3 class="po-section-title">AI创作V2 项目 ({{ v2Projects.length }})</h3>
         <div class="po-grid">
           <div
             v-for="p in v2Projects"
             :key="p.id"
             class="po-card"
           >
             <div class="po-card-header">
               <h4 class="po-card-name">{{ p.name }}</h4>
               <span class="po-card-badge">V2</span>
             </div>
             <div v-if="failedDetails.has(p.id)" class="po-card-error">
               <span class="po-error-text">详情加载失败</span>
               <button class="po-retry-btn" @click="retryLoadDetail(p)">重试</button>
             </div>
             <div v-else class="po-card-meta">
               <span class="po-meta-item">
                 <span class="po-meta-label">模块</span>
                 <span class="po-meta-value">{{ p.moduleCount || 0 }}</span>
               </span>
               <span class="po-meta-item">
                 <span class="po-meta-label">更新</span>
                 <span class="po-meta-value">{{ formatDate(p.updated_at) }}</span>
               </span>
             </div>
             <div class="po-card-progress" v-if="!failedDetails.has(p.id)">
               <div class="progress-bar">
                 <div class="progress-fill" :style="{ width: p.progressPct + '%' }"></div>
               </div>
               <span class="progress-text">{{ p.progressPct }}%</span>
             </div>
             <div class="po-card-target" v-if="p.target && !failedDetails.has(p.id)">
              → {{ p.target }}
            </div>
              <div class="po-card-actions">
                <button class="po-card-btn po-card-btn-open" @click="openProject(p)">继续创作</button>
                <button v-if="p.tags === 'v2' || p.tags?.includes('v2')" class="po-card-btn po-card-btn-write" @click="goToWriting(p)">写作</button>
                 <button class="po-card-btn po-card-btn-export" @click="exportProject(p)" :disabled="exportingId === p.id" title="导出JSON">
                   <span v-if="exportingId === p.id" class="po-btn-spinner"></span>
                   <span v-else>导出</span>
                 </button>
                 <button class="po-card-btn po-card-btn-clone" @click="cloneProject(p)" :disabled="cloningId === p.id" title="克隆项目">
                   <span v-if="cloningId === p.id" class="po-btn-spinner"></span>
                   <span v-else>克隆</span>
                 </button>
                <button class="po-card-btn po-card-btn-del" @click="confirmDelete(p)">删除</button>
              </div>
          </div>
        </div>
      </div>

      <!-- 其他项目 -->
      <div v-if="otherProjects.length" class="po-section">
        <h3 class="po-section-title">其他项目 ({{ otherProjects.length }})</h3>
        <div class="po-grid">
          <div v-for="p in otherProjects" :key="p.id" class="po-card po-card-old">
            <div class="po-card-header">
              <h4 class="po-card-name">{{ p.name }}</h4>
              <span class="po-card-badge po-card-badge-old">旧版</span>
            </div>
            <div class="po-card-meta">
              <span class="po-meta-item">
                <span class="po-meta-label">更新</span>
                <span class="po-meta-value">{{ formatDate(p.updated_at) }}</span>
              </span>
              <span class="po-meta-item">
                <span class="po-meta-label">类型</span>
                <span class="po-meta-value">{{ p.tags || '经典' }}</span>
              </span>
            </div>
            <div class="po-card-actions">
              <button class="po-card-btn po-card-btn-open" @click="openProject(p)">查看</button>
              <button class="po-card-btn po-card-btn-del" @click="confirmDelete(p)">删除</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useProjectStore } from '../stores/project'
import * as projectApi from '../api/project'
import { setupConfirm } from '../composables/useConfirm'
import { useToastStore } from '../stores/toast'
import AppConfirmDialog from '../components/AppConfirmDialog.vue'

const toast = useToastStore()

const router = useRouter()
const projectStore = useProjectStore()
const confirmDialog = setupConfirm()

const loading = ref(false)
const searchQuery = ref('')
const failedDetails = ref<Set<string>>(new Set())
const sortBy = ref<'recent' | 'name' | 'progress'>('recent')
const projectDetails = ref<Record<string, any>>({})

const v2Projects = computed(() => {
  let list = projectStore.projectList
    .filter(p => p.tags === 'v2' || p.tags?.includes('v2'))
    .map(p => {
      const detail = projectDetails.value[p.id] || {}
      return {
        ...p,
        moduleCount: detail.moduleCount || 0,
        progressPct: detail.progressPct || 0,
        target: detail.currentTarget || '',
      }
    })
  if (searchQuery.value.trim()) {
    const q = searchQuery.value.trim().toLowerCase()
    list = list.filter(p => (p.name || '').toLowerCase().includes(q))
  }
  // 5.4-3: Sort projects
  if (sortBy.value === 'recent') {
    list.sort((a, b) => (b.updated_at || '').localeCompare(a.updated_at || ''))
  } else if (sortBy.value === 'name') {
    list.sort((a, b) => (a.name || '').localeCompare(b.name || ''))
  } else if (sortBy.value === 'progress') {
    list.sort((a, b) => (b.progressPct || 0) - (a.progressPct || 0))
  }
  return list
})

const otherProjects = computed(() => {
  let list = projectStore.projectList.filter(p => p.tags !== 'v2' && !p.tags?.includes('v2'))
  if (searchQuery.value.trim()) {
    const q = searchQuery.value.trim().toLowerCase()
    list = list.filter(p => (p.name || '').toLowerCase().includes(q))
  }
  return list
})

onMounted(async () => {
  await loadProjects()
})

async function loadProjects() {
  loading.value = true
  failedDetails.value.clear()
  try {
    await projectStore.loadList()
    // 5.4-1: Lazy-load details only for visible/summary, full details on demand
    const v2List = projectStore.projectList.filter(p => p.tags === 'v2' || p.tags?.includes('v2'))
    // Load only basic info (list endpoint already returns updated_at), skip heavy detail calls
    for (const p of v2List) {
      projectDetails.value[p.id] = {
        moduleCount: 0,
        progressPct: 0,
        target: '',
      }
    }
  } catch (e) {
    console.error('[ProjectsOverview] load failed:', e)
  } finally {
    loading.value = false
  }
}

async function retryLoadDetail(p: any) {
  try {
    const detail = await projectApi.loadV2Project(p.id)
    projectDetails.value[p.id] = {
      moduleCount: detail.pipeline?.modules ? Object.keys(detail.pipeline.modules).length : 0,
      progressPct: calcProgress(detail.pipeline),
      currentTarget: detail.pipeline?.currentModule || '',
    }
    failedDetails.value.delete(p.id)
  } catch (_e) {
    // still failed, will show retry button again
  }
}

function calcProgress(pipeline: any): number {
  if (!pipeline?.modules) return 0
  const mods = Object.values(pipeline.modules)
  if (!mods.length) return 0
  const done = mods.filter((m: any) => m.status === 'done').length
  return Math.round((done / mods.length) * 100)
}

function formatDate(d: string): string {
  if (!d) return '-'
  const dt = new Date(d)
  if (isNaN(dt.getTime())) return d.slice(0, 16).replace('T', ' ')
  return dt.toISOString().replace('T', ' ').slice(0, 19)
}

function startNewProject() {
  const name = prompt('请输入项目名称:', '我的小说')
  if (name === null) return
  router.push({ path: '/create-v2', query: { new: '1', name: name.slice(0, 64) } })
}

async function openProject(p: any) {
  if (p.tags === 'v2' || p.tags?.includes('v2')) {
    router.push({ path: '/create-v2', query: { projectId: p.id } })
  } else {
    router.push({ path: '/writing', query: { projectId: p.id } })
  }
}

function goToWriting(p: any) {
  router.push({ path: '/create-v2/writing/chapter_1', query: { projectId: p.id } })
}

const exportingId = ref<string>('')
const cloningId = ref<string>('')

async function exportProject(p: any) {
  if (exportingId.value) return
  exportingId.value = p.id
  try {
    let data: any
    if (p.tags === 'v2' || p.tags?.includes('v2')) {
      data = await projectApi.loadV2Project(p.id)
    } else {
      return
    }
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${p.name || 'project'}_${p.id.slice(0, 8)}.json`
    a.click()
    URL.revokeObjectURL(url)
  } catch (e: any) {
    console.error('[ProjectsOverview] export failed:', e)
    toast.error('导出失败: ' + (e?.message || ''));
  } finally {
    exportingId.value = ''
  }
}

async function cloneProject(p: any) {
  if (cloningId.value) return
  cloningId.value = p.id
  try {
    let source: any
    if (p.tags === 'v2' || p.tags?.includes('v2')) {
      source = await projectApi.loadV2Project(p.id)
    } else {
      toast.error('旧版项目暂不支持克隆')
      return
    }
    await projectApi.saveV2Project({
      name: (source.name || p.name || '未命名') + '（副本）',
      modules: source.modules || {},
      pipeline: source.pipeline || {},
      templateSelections: source.templateSelections || {},
      sharedContext: source.sharedContext || {},
    })
    toast.success('项目已克隆')
    await loadProjects()
  } catch (e: any) {
    console.error('[ProjectsOverview] clone failed:', e)
    toast.error('克隆失败: ' + (e?.message || ''))
  } finally {
    cloningId.value = ''
  }
}

async function confirmDelete(p: any) {
  const ok = await confirmDialog.confirm({
    title: '删除项目',
    message: `确定删除项目"${p.name}"吗？`,
    detail: '删除后项目将进入回收站，可在30天内恢复',
    confirmText: '删除',
    cancelText: '取消',
    type: 'danger',
  })
  if (ok) {
    // 5.4-2: Move to recycle bin instead of permanent delete
    try {
      await projectApi.softDeleteV2Project(p.id)
      toast.action('项目已移至回收站', {
        label: '撤销',
        handler: async () => {
          try {
            await projectApi.restoreV2Project(p.id)
            await loadProjects()
            toast.success('项目已恢复')
          } catch (_e) {
            toast.error('恢复失败')
          }
        },
      })
      await loadProjects()
    } catch (_e) {
      // Fallback to hard delete if soft delete not supported
      await projectStore.remove(p.id)
      await loadProjects()
      toast.success('项目已删除')
    }
  }
}
</script>

<style scoped>
.po-page {
  padding: 28px 32px;
  max-width: 1200px;
  margin: 0 auto;
}
.po-header h2 {
  margin: 0 0 4px;
  font-size: 28px;
}
.po-sub {
  color: #888;
  margin: 0 0 24px;
  font-size: 15px;
}
.po-actions {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
  align-items: center;
}
.po-search {
  flex: 1;
  max-width: 300px;
}
.po-search-input {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 14px;
  outline: none;
  transition: border-color 0.2s;
}
.po-search-input:focus {
  border-color: #1890ff;
}
.po-select {
  padding: 10px 14px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 15px;
  background: #fff;
  cursor: pointer;
}
.po-btn {
  padding: 10px 20px;
  border: 1px solid #ddd;
  border-radius: 8px;
  background: #fff;
  cursor: pointer;
  font-size: 15px;
  display: flex;
  align-items: center;
  gap: 6px;
}
.po-btn:hover {
  border-color: #999;
}
.po-btn-primary {
  background: #1890ff;
  color: #fff;
  border-color: #1890ff;
}
.po-btn-primary:hover {
  background: #40a9ff;
  border-color: #40a9ff;
}
.po-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.po-btn-icon {
  font-size: 18px;
  font-weight: 600;
}
.po-loading, .po-empty {
  text-align: center;
  padding: 80px 20px;
  color: #aaa;
}
.po-empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
}
.po-empty p {
  font-size: 18px;
  margin-bottom: 20px;
  color: #888;
}
.po-section {
  margin-bottom: 32px;
}
.po-section-title {
  font-size: 18px;
  color: #333;
  margin: 0 0 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid #eee;
}
.po-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}
.po-card {
  background: #fff;
  border: 1px solid #e8e8e8;
  border-radius: 12px;
  padding: 20px;
  transition: box-shadow 0.2s;
}
.po-card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
}
.po-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}
.po-card-name {
  margin: 0;
  font-size: 17px;
  color: #333;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.po-card-badge {
  font-size: 11px;
  padding: 2px 8px;
  background: #e6f7ff;
  color: #1890ff;
  border-radius: 4px;
  margin-left: 8px;
  flex-shrink: 0;
}
.po-card-badge-old {
  background: #f5f5f5;
  color: #999;
}
.po-card-meta {
  display: flex;
  gap: 16px;
  margin-bottom: 12px;
}
.po-card-error {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
  padding: 8px 12px;
  background: #fff2f0;
  border: 1px solid #ffccc7;
  border-radius: 6px;
}
.po-error-text {
  font-size: 13px;
  color: #cf1322;
}
.po-retry-btn {
  padding: 4px 12px;
  background: #fff;
  border: 1px solid #ffccc7;
  border-radius: 4px;
  font-size: 13px;
  color: #cf1322;
  cursor: pointer;
}
.po-retry-btn:hover {
  background: #fff2f0;
  border-color: #ff4d4f;
}
.po-meta-item {
  display: flex;
  flex-direction: column;
}
.po-meta-label {
  font-size: 11px;
  color: #aaa;
}
.po-meta-value {
  font-size: 14px;
  color: #555;
}
.po-card-progress {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}
.progress-bar {
  flex: 1;
  height: 6px;
  background: #f0f0f0;
  border-radius: 3px;
  overflow: hidden;
}
.progress-fill {
  height: 100%;
  background: #52c41a;
  border-radius: 3px;
  transition: width 0.3s;
}
.progress-text {
  font-size: 12px;
  color: #888;
  min-width: 32px;
  text-align: right;
}
.po-card-target {
  font-size: 12px;
  color: #1890ff;
  margin-bottom: 12px;
}
.po-card-actions {
  display: flex;
  gap: 8px;
}
.po-card-btn {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  background: #fff;
  cursor: pointer;
  font-size: 13px;
}
.po-card-btn:hover {
  border-color: #999;
}
.po-card-btn-open {
  background: #52c41a;
  color: #fff;
  border-color: #52c41a;
}
.po-card-btn-open:hover {
  background: #73d13d;
  border-color: #73d13d;
}
.po-card-btn-write {
  background: #1890ff;
  color: #fff;
  border-color: #1890ff;
}
.po-card-btn-write:hover {
  background: #40a9ff;
}
.po-card-btn-del {
  color: #d9363e;
  border-color: #d9363e;
  flex: 0 0 auto;
  padding: 8px 14px;
}
.po-card-btn-del:hover {
  background: #fff1f0;
}
.po-btn-spinner {
  display: inline-block;
  width: 12px;
  height: 12px;
  border: 2px solid #52c41a;
  border-top-color: transparent;
  border-radius: 50%;
  animation: po-spin 0.6s linear infinite;
}
@keyframes po-spin { to { transform: rotate(360deg); } }
</style>
