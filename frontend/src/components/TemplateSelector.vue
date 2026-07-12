<template>
  <Teleport to="body">
    <div class="ts-overlay" @click.self="$emit('close')">
      <div class="ts-modal">
        <button class="ts-close" @click="$emit('close')">&times;</button>

        <div class="ts-header">
          <h3>选择模块数据</h3>
          <p class="ts-subtitle">{{ moduleDisplayName }}</p>
        </div>

        <div class="ts-options">
          <button class="ts-option-btn" @click="selectAI">
            <span class="ts-option-icon">🤖</span>
            <span class="ts-option-label">AI生成</span>
            <span class="ts-option-desc">使用大模型智能生成全新内容</span>
          </button>
          <button class="ts-option-btn" @click="showTemplateList = true" :disabled="loading">
            <span class="ts-option-icon">📋</span>
            <span class="ts-option-label">选择模板</span>
            <span class="ts-option-desc">复用已有AI生成结果，不消耗token</span>
          </button>
        </div>

        <div v-if="showTemplateList" class="ts-template-section">
          <div v-if="loading" class="ts-loading">正在搜索匹配模板...</div>

          <template v-else>
            <div v-if="compatible.length > 0" class="ts-section">
              <h4 class="ts-section-title">✅ 可用模板</h4>
              <div
                v-for="item in compatible"
                :key="item.template.id"
                class="ts-card"
                :class="{ 'ts-card-selected': selectedTemplateId === item.template.id }"
                @click="selectedTemplateId = item.template.id"
              >
                <div class="ts-card-header">
                  <span class="ts-card-name">{{ item.template.name }}</span>
                  <span class="ts-card-score">{{ item.score }}%</span>
                </div>
                <div class="ts-card-meta">
                  <span v-if="item.template.usage_count > 0" class="ts-tag ts-tag-used">复用 {{ item.template.usage_count }}次</span>
                  <span v-if="item.template.quality_rating > 0" class="ts-tag ts-tag-rated">★{{ item.template.quality_rating }}</span>
                  <span v-if="isInCompatGroup(item.template)" class="ts-tag ts-tag-same">同组兼容</span>
                  <span class="ts-tag">{{ item.template.genre || '通用' }}</span>
                </div>
                <div class="ts-card-preview">{{ getPreviewText(item.template) }}</div>
                <button class="ts-preview-btn" @click.stop="togglePreview(item.template)">
                  {{ previewingId === item.template.id ? '收起' : '查看详情' }}
                </button>
                <div v-if="previewingId === item.template.id" class="ts-detail">
                  <pre>{{ JSON.stringify(item.template.output_data, null, 2) }}</pre>
                </div>
              </div>
            </div>

            <div v-if="incompatible.length > 0" class="ts-section">
              <h4 class="ts-section-title">
                ❌ 不可用模板
                <button class="ts-toggle-btn" @click="showIncompatible = !showIncompatible">
                  {{ showIncompatible ? '收起' : '展开查看' }}
                </button>
              </h4>
              <div v-if="showIncompatible">
                <div
                  v-for="item in incompatible"
                  :key="item.template.id"
                  class="ts-card ts-card-disabled"
                >
                  <div class="ts-card-header">
                    <span class="ts-card-name">{{ item.template.name }}</span>
                  </div>
                  <div class="ts-card-reason">{{ item.reason }}</div>
                </div>
              </div>
            </div>

            <div v-if="compatible.length === 0 && incompatible.length === 0" class="ts-empty">
              暂无模板，请先AI生成内容后保存为模板
            </div>
          </template>
        </div>

        <div v-if="showTemplateList && selectedTemplateId" class="ts-actions">
          <button class="ts-btn ts-btn-primary" @click="applySelected">使用此模板</button>
          <button class="ts-btn" @click="selectedTemplateId = null">取消选择</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useTemplateStore, type GenerationTemplate, type MatchResult } from '../composables/useTemplateStore'

const props = defineProps<{
  moduleKey: string
  moduleDisplayName: string
  projectId: string
  projectContext: Record<string, string>
  selectedTemplates: Record<string, string>
}>()

const emit = defineEmits<{
  close: []
  selectAI: []
  selectTemplate: [data: any, template: GenerationTemplate]
}>()

const tplStore = useTemplateStore()

const showTemplateList = ref(false)
const loading = ref(false)
const compatible = ref<MatchResult[]>([])
const incompatible = ref<MatchResult[]>([])
const selectedTemplateId = ref<number | null>(null)
const previewingId = ref<number | null>(null)
const showIncompatible = ref(false)

onMounted(async () => {
  // Auto-load templates if context is provided
  if (props.projectContext && Object.keys(props.projectContext).length > 0) {
    await loadTemplates()
  }
})

async function loadTemplates() {
  loading.value = true
  try {
    const result = await tplStore.matchTemplates(
      props.moduleKey,
      props.projectContext,
      props.selectedTemplates
    )
    compatible.value = result.compatible || []
    incompatible.value = result.incompatible || []
    showTemplateList.value = true
  } catch (e) {
    console.error('[TemplateSelector] match failed:', e)
  } finally {
    loading.value = false
  }
}

function selectAI() {
  showTemplateList.value = false
  emit('selectAI')
}

function isInCompatGroup(tpl: GenerationTemplate): boolean {
  if (!tpl.compatibility_group) return false
  for (const tplId of Object.values(props.selectedTemplates)) {
    if (!tplId) continue
    // Check already loaded templates for compat group match
    const allTpls = [...compatible.value, ...incompatible.value]
    const selected = allTpls.find(t => String(t.template.id) === String(tplId))
    if (selected && selected.template.compatibility_group === tpl.compatibility_group) {
      return true
    }
  }
  return false
}

function getPreviewText(tpl: GenerationTemplate): string {
  const data = tpl.output_data
  if (!data) return '(空数据)'
  if (typeof data === 'string') return data.slice(0, 80) + (data.length > 80 ? '...' : '')

  // Extract a meaningful preview based on module
  if (data.description) return String(data.description).slice(0, 100)
  if (data.name) return String(data.name)
  if (data.world_type) return `${data.world_type} - ${data.description || '详见数据'}`
  if (Array.isArray(data)) return `共 ${data.length} 项数据`

  const keys = Object.keys(data)
  if (keys.length > 0) return `包含: ${keys.slice(0, 3).join(', ')}`
  return '(结构化数据)'
}

function togglePreview(tpl: GenerationTemplate) {
  previewingId.value = previewingId.value === tpl.id ? null : tpl.id
}

async function applySelected() {
  if (!selectedTemplateId.value) return

  const matchResult = compatible.value.find(r => r.template.id === selectedTemplateId.value)
  if (!matchResult) return

  const tpl = matchResult.template

  try {
    const result = await tplStore.applyTemplate(tpl.id, props.projectId)
    if (result.success) {
      emit('selectTemplate', result.data, tpl)
      emit('close')
    }
  } catch (e) {
    console.error('[TemplateSelector] apply failed:', e)
  }
}
</script>

<style scoped>
.ts-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}
.ts-modal {
  background: #fff;
  border-radius: 16px;
  padding: 28px 32px;
  width: 640px;
  max-width: 90vw;
  max-height: 80vh;
  overflow-y: auto;
  position: relative;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}
.ts-close {
  position: absolute;
  top: 12px;
  right: 16px;
  background: none;
  border: none;
  font-size: 28px;
  cursor: pointer;
  color: #999;
  line-height: 1;
}
.ts-header {
  margin-bottom: 20px;
}
.ts-header h3 {
  margin: 0 0 4px;
  font-size: 22px;
  color: #333;
}
.ts-subtitle {
  margin: 0;
  color: #888;
  font-size: 14px;
}
.ts-options {
  display: flex;
  gap: 16px;
  margin-bottom: 20px;
}
.ts-option-btn {
  flex: 1;
  padding: 16px;
  border: 2px solid #e8e8e8;
  border-radius: 12px;
  background: #fafafa;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  transition: all 0.2s;
}
.ts-option-btn:hover {
  border-color: #1890ff;
  background: #e6f7ff;
}
.ts-option-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.ts-option-icon {
  font-size: 32px;
}
.ts-option-label {
  font-size: 16px;
  font-weight: 600;
  color: #333;
}
.ts-option-desc {
  font-size: 12px;
  color: #888;
}
.ts-template-section {
  border-top: 1px solid #eee;
  padding-top: 16px;
}
.ts-loading {
  text-align: center;
  padding: 40px;
  color: #888;
}
.ts-section {
  margin-bottom: 16px;
}
.ts-section-title {
  font-size: 15px;
  color: #555;
  margin: 0 0 10px;
  display: flex;
  align-items: center;
  gap: 12px;
}
.ts-toggle-btn {
  font-size: 12px;
  background: none;
  border: none;
  color: #1890ff;
  cursor: pointer;
}
.ts-card {
  border: 1px solid #e8e8e8;
  border-radius: 10px;
  padding: 14px 16px;
  margin-bottom: 10px;
  cursor: pointer;
  transition: all 0.2s;
}
.ts-card:hover {
  border-color: #1890ff;
  box-shadow: 0 2px 8px rgba(24, 144, 255, 0.15);
}
.ts-card-selected {
  border-color: #1890ff;
  background: #e6f7ff;
}
.ts-card-disabled {
  opacity: 0.5;
  cursor: default;
}
.ts-card-disabled:hover {
  border-color: #e8e8e8;
  box-shadow: none;
}
.ts-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}
.ts-card-name {
  font-weight: 600;
  font-size: 15px;
  color: #333;
}
.ts-card-score {
  font-size: 13px;
  color: #1890ff;
  font-weight: 600;
}
.ts-card-meta {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  margin-bottom: 6px;
}
.ts-tag {
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 4px;
  background: #f0f0f0;
  color: #666;
}
.ts-tag-used { background: #e6f7ff; color: #1890ff; }
.ts-tag-rated { background: #fff7e6; color: #fa8c16; }
.ts-tag-same { background: #f6ffed; color: #52c41a; }
.ts-card-preview {
  font-size: 13px;
  color: #888;
  line-height: 1.5;
}
.ts-card-reason {
  font-size: 12px;
  color: #d9363e;
  margin-top: 4px;
}
.ts-preview-btn {
  margin-top: 8px;
  font-size: 12px;
  background: none;
  border: 1px solid #ddd;
  border-radius: 4px;
  padding: 4px 10px;
  cursor: pointer;
  color: #1890ff;
}
.ts-preview-btn:hover {
  border-color: #1890ff;
}
.ts-detail {
  margin-top: 10px;
  background: #f9f9f9;
  border-radius: 8px;
  padding: 10px;
  max-height: 200px;
  overflow-y: auto;
}
.ts-detail pre {
  margin: 0;
  font-size: 12px;
  color: #555;
  white-space: pre-wrap;
  word-break: break-all;
}
.ts-empty {
  text-align: center;
  padding: 40px;
  color: #aaa;
  font-size: 14px;
}
.ts-actions {
  display: flex;
  gap: 12px;
  margin-top: 16px;
  justify-content: flex-end;
  border-top: 1px solid #eee;
  padding-top: 16px;
}
.ts-btn {
  padding: 10px 20px;
  border: 1px solid #ddd;
  border-radius: 8px;
  background: #fff;
  cursor: pointer;
  font-size: 14px;
}
.ts-btn:hover {
  border-color: #999;
}
.ts-btn-primary {
  background: #1890ff;
  color: #fff;
  border-color: #1890ff;
}
.ts-btn-primary:hover {
  background: #40a9ff;
  border-color: #40a9ff;
}
</style>
