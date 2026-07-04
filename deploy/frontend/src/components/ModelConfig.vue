<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-card">
      <button class="modal-close" @click="$emit('close')">&times;</button>
      <h3>大模型配置</h3>
      <div v-if="!settings.models.length" style="color:#999;padding:8px 0;text-align:center;font-size:11px">暂无配置，选择预设一键添加</div>
      <div v-for="m in settings.models" :key="m.id" class="model-item" :class="{ selected: m.id === settings.activeModelId }">
        <div>
          <div class="model-name">{{ m.name }}</div>
          <div class="model-endpoint">{{ m.endpoint }}</div>
        </div>
        <div>
          <button v-if="m.id !== settings.activeModelId" class="model-act-btn sel" @click="setActive(m.id)">使用</button>
          <span v-else style="font-size:9px;color:#11998e">当前</span>
          <button class="model-act-btn edit" @click="startEdit(m)">编</button>
          <button class="model-act-btn del" @click="handleDelete(m.id)">删</button>
        </div>
      </div>
      <button class="add-model-btn" @click="showAddForm = !showAddForm">{{ showAddForm ? '- 取消' : '+ 添加模型' }}</button>
      <div v-if="showAddForm">
        <div class="form-group"><label>模型名称</label><input v-model="form.name" placeholder="如: DeepSeek V3"></div>
        <div class="form-group"><label>API 地址</label><input v-model="form.endpoint" placeholder="https://api.deepseek.com/v1/chat/completions"></div>
        <div class="form-group"><label>API Key</label><input v-model="form.apiKey" type="password" placeholder="sk-xxx"></div>
        <div class="form-group"><label>模型标识</label><input v-model="form.model" placeholder="如: deepseek-chat, glm-4-flash"></div>
        <div style="display:flex;gap:6px;margin-top:8px">
          <button class="btn btn-dl" style="flex:1" @click="handleSave">保存</button>
          <button class="btn" style="flex:1;background:#ccc" @click="showAddForm = false">取消</button>
        </div>
      </div>
      <div class="preset-btns">
        <button class="add-model-btn preset-btn" @click="fillPreset('智谱 GLM-4-Flash', 'https://open.bigmodel.cn/api/paas/v4/chat/completions', 'glm-4-flash')">智谱 GLM-4-Flash（免费）</button>
        <button class="add-model-btn preset-btn" @click="fillPreset('DeepSeek V3', 'https://api.deepseek.com/v1/chat/completions', 'deepseek-chat')">DeepSeek V3</button>
        <button class="add-model-btn preset-btn" @click="fillPreset('通义千问 Turbo', 'https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions', 'qwen-turbo')">通义千问 Turbo</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useSettingsStore } from '../stores/settings'
import type { ModelConfig } from '../api/client'

defineEmits<{ close: [] }>()
const settings = useSettingsStore()

const showAddForm = ref(false)
const editingId = ref('')
const form = reactive({ name: '', endpoint: '', apiKey: '', model: '' })

function setActive(id: string) {
  settings.setActive(id)
}

function startEdit(m: ModelConfig) {
  editingId.value = m.id
  form.name = m.name
  form.endpoint = m.endpoint
  form.apiKey = m.apiKey
  form.model = m.model
  showAddForm.value = true
}

function handleDelete(id: string) {
  if (!confirm('确定删除？')) return
  settings.removeModel(id)
}

function handleSave() {
  if (!form.name || !form.endpoint || !form.apiKey || !form.model) {
    alert('请填写所有字段')
    return
  }
  if (editingId.value) {
    settings.updateModel(editingId.value, { ...form })
  } else {
    settings.addModel({ id: 'm' + Date.now(), ...form })
  }
  if (!settings.activeModelId && settings.models.length) {
    settings.setActive(settings.models[settings.models.length - 1].id)
  }
  showAddForm.value = false
  editingId.value = ''
  form.name = ''
  form.endpoint = ''
  form.apiKey = ''
  form.model = ''
}

function fillPreset(name: string, endpoint: string, model: string) {
  editingId.value = ''
  form.name = name
  form.endpoint = endpoint
  form.model = model
  form.apiKey = ''
  showAddForm.value = true
}
</script>
