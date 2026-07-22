<template>
  <div class="tl-page">
    <div class="tl-header">
      <h2>模板库</h2>
      <p class="tl-desc">管理AI生成的模板，跨项目复用，节省token消耗</p>
    </div>

    <div class="tl-filters">
      <input
        v-model="searchQuery"
        type="text"
        placeholder="搜索模板名称..."
        class="tl-search-input"
      />
      <select v-model="filterModule" class="tl-select">
        <option value="">全部模块</option>
        <option v-for="mod in moduleOptions" :key="mod.key" :value="mod.key">{{ mod.name }}</option>
      </select>
      <select v-model="filterGenre" class="tl-select">
        <option value="">全部题材</option>
        <option value="玄幻">玄幻</option>
        <option value="都市">都市</option>
        <option value="科幻">科幻</option>
        <option value="言情">言情</option>
        <option value="历史">历史</option>
      </select>
      <select v-model="sortBy" class="tl-select">
        <option value="usage">按复用次数</option>
        <option value="rating">按评分</option>
        <option value="recent">按最近创建</option>
      </select>
    </div>

    <div v-if="loading" class="tl-loading">加载中...</div>

    <div v-else-if="loadError" class="tl-error">
      <p>⚠ 加载失败: {{ loadError }}</p>
      <button class="tl-btn tl-btn-sm" @click="loadTemplates">重试</button>
    </div>

    <div v-else-if="filteredTemplates.length === 0" class="tl-empty">
      暂无模板。在创作流程中AI生成内容后，点击"保存为模板"即可添加。
    </div>

    <div v-else class="tl-grid">
      <div v-for="tpl in filteredTemplates" :key="tpl.id" class="tl-card">
        <div class="tl-card-top">
          <span class="tl-module-badge">{{ moduleDisplayName(tpl.module_key) }}</span>
          <span v-if="tpl.quality_rating > 0" class="tl-rating">★{{ tpl.quality_rating }}</span>
        </div>
        <h4 class="tl-card-name">{{ tpl.name }}</h4>
        <div class="tl-card-meta">
          <span v-if="tpl.genre" class="tl-tag">{{ tpl.genre }}</span>
          <span v-if="tpl.world_type" class="tl-tag">{{ tpl.world_type }}</span>
          <span v-if="tpl.usage_count > 0" class="tl-tag tl-tag-count">复用{{ tpl.usage_count }}次</span>
        </div>
        <div class="tl-card-actions">
          <button class="tl-btn tl-btn-sm tl-btn-primary" @click="applyTemplate(tpl)">应用</button>
          <button class="tl-btn tl-btn-sm" @click="editTemplate(tpl)">编辑</button>
          <button class="tl-btn tl-btn-sm tl-btn-danger" @click="confirmDelete(tpl)">删除</button>
        </div>
        <div class="tl-card-date">{{ tpl.created_at }}</div>
      </div>
    </div>

    <!-- Edit Dialog -->
    <div v-if="editingTpl" class="tl-edit-overlay" @click.self="editingTpl = null">
      <div class="tl-edit-modal">
        <h3>编辑模板</h3>
        <div class="tl-field">
          <label>名称</label>
          <input v-model="editForm.name" class="tl-input" />
        </div>
        <div class="tl-field">
          <label>题材</label>
          <input v-model="editForm.genre" class="tl-input" />
        </div>
        <div class="tl-field">
          <label>世界类型</label>
          <input v-model="editForm.world_type" class="tl-input" />
        </div>
        <div class="tl-field">
          <label>评分 (1-5)</label>
          <input v-model.number="editForm.quality_rating" type="number" min="1" max="5" class="tl-input" />
        </div>
        <div class="tl-actions">
          <button class="tl-btn tl-btn-primary" @click="saveEdit">保存</button>
          <button class="tl-btn" @click="editingTpl = null">取消</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useTemplateStore, type GenerationTemplate } from '../composables/useTemplateStore'
import { setupConfirm } from '../composables/useConfirm'
import { useToastStore } from '../stores/toast'

const tplStore = useTemplateStore()
const confirmDialog = setupConfirm()
const toast = useToastStore()
const router = useRouter()

const loading = ref(false)
const applying = ref(false)
const loadError = ref('')
const searchQuery = ref('')
const filterModule = ref('')
const filterGenre = ref('')
const sortBy = ref('usage')
const editingTpl = ref<GenerationTemplate | null>(null)
const editForm = ref({ name: '', genre: '', world_type: '', quality_rating: 0 })

const moduleOptions = [
  { key: 'world', name: '世界观(含势力+力量体系)' },
  { key: 'characters', name: '角色' },
  { key: 'architecture', name: '故事架构' },
  { key: 'outline', name: '全书大纲' },
  { key: 'volumes', name: '卷纲' },
  { key: 'chapter_plan', name: '章节规划' },
]

function moduleDisplayName(key: string): string {
  return moduleOptions.find(m => m.key === key)?.name || key
}

const filteredTemplates = computed(() => {
  let list = [...tplStore.allTemplates.value]
  if (searchQuery.value.trim()) {
    const q = searchQuery.value.trim().toLowerCase()
    list = list.filter(t => (t.name || '').toLowerCase().includes(q))
  }
  if (filterModule.value) list = list.filter(t => t.module_key === filterModule.value)
  if (filterGenre.value) list = list.filter(t => t.genre === filterGenre.value)

  if (sortBy.value === 'usage') list.sort((a, b) => b.usage_count - a.usage_count)
  else if (sortBy.value === 'rating') list.sort((a, b) => b.quality_rating - a.quality_rating)
  else list.sort((a, b) => b.created_at.localeCompare(a.created_at))

  return list
})

onMounted(async () => {
  await loadTemplates()
})

async function loadTemplates() {
  loading.value = true
  loadError.value = ''
  try {
    await tplStore.fetchTemplates({ limit: 200 })
  } catch (e: any) {
    loadError.value = e?.message || '加载模板失败'
  } finally {
    loading.value = false
  }
}

function editTemplate(tpl: GenerationTemplate) {
  editingTpl.value = tpl
  editForm.value = {
    name: tpl.name,
    genre: tpl.genre,
    world_type: tpl.world_type,
    quality_rating: tpl.quality_rating,
  }
}

async function saveEdit() {
  if (!editingTpl.value) return
  await tplStore.updateTemplate(editingTpl.value.id, editForm.value)
  editingTpl.value = null
  toast.success('模板已保存')
}

async function confirmDelete(tpl: GenerationTemplate) {
  const ok = await confirmDialog.confirm({
    title: '删除模板',
    message: `确定删除模板"${tpl.name}"吗？`,
    confirmText: '删除',
    cancelText: '取消',
    type: 'danger',
  })
  if (ok) {
    await tplStore.deleteTemplate(tpl.id)
    toast.success('模板已删除')
  }
}

async function applyTemplate(tpl: GenerationTemplate) {
  const ok = await confirmDialog.confirm({
    title: '应用模板',
    message: `将模板"${tpl.name}"应用到当前项目？`,
    detail: '这将跳转到创作流程的对应模块并填充模板数据',
    confirmText: '应用',
    cancelText: '取消',
    type: 'info',
  })
  if (ok) {
    applying.value = true
    try {
      router.push({ path: `/create-v2/${tpl.module_key}`, query: { projectId: '', applyTemplate: String(tpl.id) } })
    } finally {
      applying.value = false
    }
  }
}
</script>

<style scoped>
.tl-page {
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
}
.tl-header h2 {
  margin: 0 0 4px;
  font-size: 24px;
}
.tl-desc {
  color: #888;
  margin: 0 0 20px;
  font-size: 14px;
}
.tl-filters {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}
.tl-select {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 14px;
  background: #fff;
}
.tl-search-input {
  flex: 1;
  min-width: 180px;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 14px;
  outline: none;
}
.tl-search-input:focus {
  border-color: #1890ff;
}
.tl-loading, .tl-empty, .tl-error {
  text-align: center;
  padding: 60px;
  color: #aaa;
}
.tl-error { color: #cf1322; }
.tl-error p { margin-bottom: 12px; }
.tl-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}
.tl-card {
  border: 1px solid #e8e8e8;
  border-radius: 12px;
  padding: 16px;
  background: #fff;
  transition: box-shadow 0.2s;
}
.tl-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}
.tl-card-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}
.tl-module-badge {
  font-size: 12px;
  padding: 2px 8px;
  background: #e6f7ff;
  color: #1890ff;
  border-radius: 4px;
}
.tl-rating {
  font-size: 13px;
  color: #fa8c16;
}
.tl-card-name {
  margin: 0 0 8px;
  font-size: 16px;
  color: #333;
}
.tl-card-meta {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  margin-bottom: 12px;
}
.tl-tag {
  font-size: 11px;
  padding: 2px 6px;
  background: #f0f0f0;
  color: #666;
  border-radius: 4px;
}
.tl-tag-count { background: #f6ffed; color: #52c41a; }
.tl-card-actions {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
}
.tl-btn {
  padding: 6px 14px;
  border: 1px solid #ddd;
  border-radius: 6px;
  background: #fff;
  cursor: pointer;
  font-size: 13px;
}
.tl-btn:hover { border-color: #999; }
.tl-btn-sm { padding: 4px 10px; font-size: 12px; }
.tl-btn-primary { background: #1890ff; color: #fff; border-color: #1890ff; }
.tl-btn-primary:hover { background: #40a9ff; }
.tl-btn-danger { color: #d9363e; border-color: #d9363e; }
.tl-btn-danger:hover { background: #fff1f0; }
.tl-card-date {
  font-size: 11px;
  color: #bbb;
}
.tl-edit-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}
.tl-edit-modal {
  background: #fff;
  border-radius: 16px;
  padding: 28px 32px;
  width: 400px;
  max-width: 90vw;
}
.tl-edit-modal h3 { margin: 0 0 16px; }
.tl-field { margin-bottom: 14px; }
.tl-field label { display: block; font-size: 13px; color: #555; margin-bottom: 4px; }
.tl-input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 14px;
  outline: none;
  box-sizing: border-box;
}
.tl-input:focus { border-color: #1890ff; }
.tl-actions {
  display: flex;
  gap: 12px;
  margin-top: 20px;
  justify-content: flex-end;
}
</style>
