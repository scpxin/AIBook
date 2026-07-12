<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-card template-manage">
      <button class="modal-close" @click="$emit('close')">&times;</button>
      <h3>模板管理</h3>
      <div v-if="loading" class="state-msg">加载中...</div>
      <div v-else-if="!templates.length" class="state-msg">暂无模板，从灵感模块保存</div>
      <div v-else class="template-list">
        <div v-for="tpl in templates" :key="tpl.id" class="tpl-item">
          <div class="tpl-info">
            <span class="tpl-icon">{{ tpl.icon }}</span>
            <div class="tpl-detail">
              <div class="tpl-name">{{ tpl.name }}</div>
              <div class="tpl-meta">{{ tpl.genre }} · {{ tpl.updated_at?.slice(0, 10) }}</div>
            </div>
          </div>
          <div class="tpl-actions">
            <button class="btn-icon-btn" title="编辑" @click="handleEdit(tpl)">✏</button>
            <button class="btn-icon-btn" title="删除" @click="handleDelete(tpl)">🗑</button>
          </div>
        </div>
      </div>
    </div>
    <TemplateDialog
      v-if="editing"
      :template="editing"
      :project-id="projectId"
      @close="editing = null"
      @saved="handleSaved"
    />
    <div v-if="confirmDelete" class="confirm-mask">
      <div class="confirm-card">
        <p>确定删除模板 "{{ confirmDelete.name }}"?</p>
        <div class="confirm-actions">
          <button class="btn-save" @click="doDelete">删除</button>
          <button class="btn-cancel" @click="confirmDelete = null">取消</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getTemplates, deleteTemplate } from '../api/v2'
import { useToastStore } from '../stores/toast'
import type { IdeaTemplate } from '../types/v2'
import TemplateDialog from './TemplateDialog.vue'

const props = defineProps<{ projectId: string }>()
defineEmits<{ close: [] }>()

const toast = useToastStore()
const templates = ref<IdeaTemplate[]>([])
const loading = ref(true)
const editing = ref<IdeaTemplate | null>(null)
const confirmDelete = ref<IdeaTemplate | null>(null)

async function load() {
  loading.value = true
  try {
    const res = await getTemplates(props.projectId)
    templates.value = res.templates
  } catch (e: any) {
    toast.error(e.message || '加载失败')
  } finally {
    loading.value = false
  }
}

function handleEdit(tpl: IdeaTemplate) {
  editing.value = tpl
}

function handleSaved(saved: IdeaTemplate) {
  templates.value = templates.value.map(t => t.id === saved.id ? saved : t)
}

function handleDelete(tpl: IdeaTemplate) {
  confirmDelete.value = tpl
}

async function doDelete() {
  if (!confirmDelete.value) return
  const id = confirmDelete.value.id
  try {
    await deleteTemplate(id)
    templates.value = templates.value.filter(t => t.id !== id)
    toast.success('模板已删除')
  } catch (e: any) {
    toast.error(e.message || '删除失败')
  } finally {
    confirmDelete.value = null
  }
}

onMounted(load)
</script>

<style scoped>
.template-manage { max-width: 520px; min-height: 200px; }
.state-msg { padding: 20px; text-align: center; color: #999; }
.template-list { max-height: 360px; overflow-y: auto; }
.tpl-item { display: flex; align-items: center; justify-content: space-between; padding: 10px 8px; border-bottom: 1px solid #f0f0f0; }
.tpl-item:last-child { border-bottom: none; }
.tpl-info { display: flex; align-items: center; gap: 10px; flex: 1; overflow: hidden; }
.tpl-icon { font-size: 22px; width: 32px; text-align: center; }
.tpl-detail { overflow: hidden; }
.tpl-name { font-weight: 600; font-size: 14px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.tpl-meta { font-size: 12px; color: #999; }
.tpl-actions { display: flex; gap: 4px; }
.btn-icon-btn { width: 32px; height: 32px; border-radius: 6px; border: 1px solid #ddd; background: #fff; cursor: pointer; font-size: 15px; }
.btn-icon-btn:hover { background: #f5f5f5; }
.confirm-mask { position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; border-radius: 8px; }
.confirm-card { background: #fff; padding: 20px; border-radius: 8px; min-width: 260px; }
.confirm-card p { margin-bottom: 16px; text-align: center; }
.confirm-actions { display: flex; gap: 10px; }
.confirm-actions .btn-save { flex: 1; }
.confirm-actions .btn-cancel { flex: 1; }
</style>
