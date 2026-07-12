<template>
  <Teleport to="body">
    <div class="sav-overlay" @click.self="$emit('close')">
      <div class="sav-modal">
        <button class="sav-close" @click="$emit('close')">&times;</button>
        <h3>保存为模板</h3>
        <p class="sav-desc">将本次AI生成结果保存为模板，后续项目可直接复用，无需再次消耗token</p>

        <div class="sav-field">
          <label>模板名称</label>
          <input
            v-model="templateName"
            :placeholder="suggestedName"
            class="sav-input"
          />
        </div>

        <div class="sav-field">
          <label>题材标签</label>
          <input v-model="genre" placeholder="如：玄幻" class="sav-input" />
        </div>

        <div class="sav-field">
          <label>世界类型</label>
          <input v-model="worldType" placeholder="如：东方玄幻" class="sav-input" />
        </div>

        <div class="sav-field">
          <label>风格</label>
          <input v-model="tone" placeholder="如：热血" class="sav-input" />
        </div>

        <div class="sav-actions">
          <button class="sav-btn sav-btn-primary" @click="saveTemplate" :disabled="saving">
            {{ saving ? '保存中...' : '保存模板' }}
          </button>
          <button class="sav-btn" @click="$emit('close')">跳过</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import type { GenerationTemplate } from '../composables/useTemplateStore'

const props = defineProps<{
  projectId: string
  moduleKey: string
  moduleData: any
  inputContext: Record<string, any>
  suggestedName?: string
}>()

const emit = defineEmits<{
  close: []
  saved: [template: GenerationTemplate]
}>()

const templateName = ref('')
const genre = ref(props.inputContext?.genre || '')
const worldType = ref(props.inputContext?.world_type || '')
const tone = ref(props.inputContext?.tone || '')
const saving = ref(false)

onMounted(() => {
  if (props.suggestedName) {
    templateName.value = props.suggestedName
  }
})

async function saveTemplate() {
  if (!templateName.value.trim()) {
    templateName.value = props.suggestedName || `${props.moduleKey}-模板`
  }

  saving.value = true
  try {
    const { createGenerationTemplate } = await import('../api/v2')
    const result = await createGenerationTemplate({
      name: templateName.value.trim(),
      module_key: props.moduleKey,
      output_data: props.moduleData,
      input_context: props.inputContext,
      genre: genre.value,
      world_type: worldType.value,
      tone: tone.value,
      source_project_id: props.projectId,
    })
    if (result.template) {
      emit('saved', result.template)
    }
    emit('close')
  } catch (e) {
    console.error('[SaveAsTemplate] save failed:', e)
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.sav-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1001;
}
.sav-modal {
  background: #fff;
  border-radius: 16px;
  padding: 28px 32px;
  width: 440px;
  max-width: 90vw;
  position: relative;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}
.sav-close {
  position: absolute;
  top: 12px; right: 16px;
  background: none; border: none;
  font-size: 28px; cursor: pointer; color: #999;
}
.sav-modal h3 {
  margin: 0 0 8px;
  font-size: 20px;
}
.sav-desc {
  margin: 0 0 20px;
  color: #888;
  font-size: 14px;
  line-height: 1.5;
}
.sav-field {
  margin-bottom: 14px;
}
.sav-field label {
  display: block;
  font-size: 13px;
  color: #555;
  margin-bottom: 4px;
  font-weight: 500;
}
.sav-input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 14px;
  outline: none;
  box-sizing: border-box;
}
.sav-input:focus {
  border-color: #1890ff;
}
.sav-actions {
  display: flex;
  gap: 12px;
  margin-top: 20px;
  justify-content: flex-end;
}
.sav-btn {
  padding: 10px 20px;
  border: 1px solid #ddd;
  border-radius: 8px;
  background: #fff;
  cursor: pointer;
  font-size: 14px;
}
.sav-btn:hover { border-color: #999; }
.sav-btn-primary {
  background: #1890ff;
  color: #fff;
  border-color: #1890ff;
}
.sav-btn-primary:hover { background: #40a9ff; border-color: #40a9ff; }
.sav-btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }
</style>
