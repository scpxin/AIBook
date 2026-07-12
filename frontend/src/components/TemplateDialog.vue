<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-card template-dialog">
      <button class="modal-close" @click="$emit('close')">&times;</button>
      <h3>{{ isEdit ? '编辑模板' : '保存为模板' }}</h3>
      <div class="form-group">
        <label>模板名称 <span class="required">*</span></label>
        <input v-model="form.name" placeholder="如: 玄幻修仙模板" maxlength="50" />
      </div>
      <div class="form-group">
        <label>图标</label>
        <div class="icon-picker">
          <button v-for="ic in icons" :key="ic" class="icon-option" :class="{ active: form.icon === ic }" @click="form.icon = ic">{{ ic }}</button>
        </div>
      </div>
      <div class="form-group">
        <label>类型 <span class="required">*</span></label>
        <select v-model="form.genre">
          <option v-for="g in genres" :key="g" :value="g">{{ g }}</option>
        </select>
      </div>
      <div class="form-group">
        <label>创意描述 <span class="required">*</span></label>
        <textarea v-model="form.prompt" placeholder="至少10个字..." rows="4" />
        <span class="char-count" :class="{ error: form.prompt.length < 10 }">{{ form.prompt.length }}/2000</span>
      </div>
      <div class="form-group">
        <label>参考作品</label>
        <input v-model="form.reference" placeholder="可选，如: 斗破苍穹" maxlength="200" />
      </div>
      <div class="form-actions">
        <button class="btn-save" :disabled="!canSave || saving" @click="handleSave">
          {{ saving ? '保存中...' : (isEdit ? '更新' : '保存') }}
        </button>
        <button class="btn-cancel" @click="$emit('close')">取消</button>
      </div>
      <div v-if="error" class="error-msg">{{ error }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, computed, onMounted } from 'vue'
import { createTemplate, updateTemplate } from '../api/v2'
import { useToastStore } from '../stores/toast'
import type { IdeaTemplate } from '../types/v2'

const props = defineProps<{
  template?: IdeaTemplate | null
  projectId: string
  presetName?: string
  presetGenre?: string
  presetPrompt?: string
  presetReference?: string
}>()

const emit = defineEmits<{ close: []; saved: [template: IdeaTemplate] }>()

const toast = useToastStore()
const genres = ['玄幻', '都市', '科幻', '言情', '悬疑', '历史', '游戏', '轻小说', '自定义']
const icons = ['💡', '🗡', '🏙', '🚀', '💕', '🔮', '📜', '🎮', '🎭', '⚔', '🔬', '🌟']

const isEdit = computed(() => !!props.template)

const form = reactive({
  name: '',
  icon: '💡',
  genre: '',
  prompt: '',
  reference: '',
})

const saving = ref(false)
const error = ref('')

const canSave = computed(() =>
  form.name.trim().length > 0 &&
  form.prompt.trim().length >= 10 &&
  form.genre.length > 0
)

onMounted(() => {
  if (props.template) {
    form.name = props.template.name
    form.icon = props.template.icon
    form.genre = props.template.genre
    form.prompt = props.template.prompt
    form.reference = props.template.reference
  } else {
    form.name = props.presetName || ''
    form.genre = props.presetGenre || ''
    form.prompt = props.presetPrompt || ''
    form.reference = props.presetReference || ''
  }
})

async function handleSave() {
  if (!canSave.value) return
  saving.value = true
  error.value = ''
  try {
    if (isEdit.value && props.template) {
      const res = await updateTemplate(props.template.id, {
        name: form.name.trim(),
        icon: form.icon,
        genre: form.genre,
        prompt: form.prompt.trim(),
        reference: form.reference.trim(),
      })
      toast.success('模板已更新')
      emit('saved', res.template)
    } else {
      const res = await createTemplate({
        project_id: props.projectId,
        name: form.name.trim(),
        icon: form.icon,
        genre: form.genre,
        prompt: form.prompt.trim(),
        reference: form.reference.trim(),
      })
      toast.success('模板保存成功')
      emit('saved', res.template)
    }
    emit('close')
  } catch (e: any) {
    error.value = e.message || '保存失败'
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.template-dialog { max-width: 480px; }
.form-group { margin-bottom: 14px; }
.form-group label { display: block; font-weight: 600; margin-bottom: 4px; font-size: 14px; }
.required { color: #ff4d4f; }
.form-group input, .form-group select, .form-textarea { width: 100%; padding: 8px 10px; border: 1px solid #ddd; border-radius: 5px; font-size: 15px; }
.form-group textarea { width: 100%; padding: 8px 10px; border: 1px solid #ddd; border-radius: 5px; font-size: 15px; resize: vertical; }
.char-count { font-size: 12px; color: #999; float: right; }
.char-count.error { color: #ff4d4f; }
.icon-picker { display: flex; gap: 6px; flex-wrap: wrap; }
.icon-option { width: 36px; height: 36px; border: 1px solid #ddd; border-radius: 6px; background: #fff; cursor: pointer; font-size: 18px; }
.icon-option.active { border-color: var(--primary); background: #f0f8ff; }
.form-actions { display: flex; gap: 10px; margin-top: 16px; }
.btn-save { flex: 1; padding: 10px; background: var(--primary); color: #fff; border: none; border-radius: 6px; cursor: pointer; font-size: 15px; }
.btn-save:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-cancel { flex: 1; padding: 10px; background: #f5f5f5; border: 1px solid #ddd; border-radius: 6px; cursor: pointer; font-size: 15px; }
.error-msg { color: #ff4d4f; margin-top: 10px; font-size: 14px; }
</style>
