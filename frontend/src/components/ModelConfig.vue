<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-card">
      <button class="modal-close" @click="$emit('close')">&times;</button>
      <h3>大模型配置</h3>
      <div v-if="!settings.models.length" style="color:#999;padding:8px 0;text-align:center;font-size:11px">暂无模型配置，点击下方"添加模型"开始配置</div>
      <div v-for="m in settings.models" :key="m.id" class="model-item" :class="{ selected: m.id === settings.activeModelId }">
        <div>
          <div class="model-name">{{ m.name }}</div>
          <div class="model-endpoint">{{ m.endpoint }}</div>
        </div>
        <div>
          <button v-if="m.id !== settings.activeModelId" class="model-act-btn sel" @click="setActive(m.id)">使用</button>
          <span v-else style="font-size:9px;color:#11998e">当前</span>
          <button class="model-act-btn test" @click="startEdit(m); handleTest()">测</button>
          <button class="model-act-btn edit" @click="startEdit(m)">编</button>
          <button class="model-act-btn del" @click="handleDelete(m.id)">删</button>
        </div>
      </div>
      <button class="add-model-btn" @click="openAddForm">{{ showAddForm ? '- 取消' : '+ 添加模型' }}</button>
      <div v-if="showAddForm">
        <div class="form-group"><label>模型名称</label><input v-model="form.name" placeholder="如: My Custom Model"></div>
        <div class="form-group"><label>API 地址</label><input v-model="form.endpoint" placeholder="https://api.example.com/v1/chat/completions"></div>
        <div class="form-group"><label>API Key</label><input v-model="form.apiKey" type="password" placeholder="sk-xxx"></div>
      <div class="form-group"><label>模型标识</label><input v-model="form.model" placeholder="如: gpt-4o-mini, claude-3-sonnet"></div>
      <div style="display:flex;gap:6px;margin-top:8px">
        <button class="btn btn-dl" style="flex:1" @click="handleSave">保存</button>
        <button class="btn" style="flex:1;background:#11998e;color:#fff" :disabled="testing" @click="handleTest">
          {{ testing ? '测试中...' : '测试连接' }}
        </button>
        <button class="btn" style="flex:1;background:#ccc" @click="closeForm">取消</button>
      </div>
      <div v-if="testResult" :class="['test-result', testResult.ok ? 'ok' : 'fail']">
        {{ testResult.ok ? '✅' : '❌' }} {{ testResult.msg }}
      </div>
    </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, watch } from 'vue'
import { useSettingsStore } from '../stores/settings'
import { testModelConnection } from '../api/v2'
import type { ModelConfig } from '../api/client'
import { useToastStore } from '../stores/toast'

defineEmits<{ close: [] }>()

const settings = useSettingsStore()
const toastStore = useToastStore()

const showAddForm = ref(false)
const editingId = ref('')
const form = reactive({ name: '', endpoint: '', apiKey: '', model: '' })
const testing = ref(false)
const testResult = ref<{ ok: boolean; msg: string } | null>(null)

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

function openAddForm() {
  if (!showAddForm.value) {
    editingId.value = ''
    form.name = ''
    form.endpoint = ''
    form.apiKey = ''
    form.model = ''
  }
  showAddForm.value = !showAddForm.value
}

function closeForm() {
  showAddForm.value = false
  editingId.value = ''
  form.name = ''
  form.endpoint = ''
  form.apiKey = ''
  form.model = ''
}

async function handleDelete(id: string) {
  const ok = window.confirm('确定删除此模型配置？')
  if (!ok) return
  settings.removeModel(id)
  toastStore.success('模型已删除')
}

function handleSave() {
  if (!form.name || !form.endpoint || !form.apiKey || !form.model) {
    toastStore.error('请填写所有字段')
    return
  }
  if (editingId.value) {
    settings.updateModel(editingId.value, { ...form })
    toastStore.success('模型已更新')
  } else {
    settings.addModel({ id: 'm' + Date.now(), ...form })
    toastStore.success('模型已添加')
  }
  if (!settings.activeModelId && settings.models.length) {
    settings.setActive(settings.models[settings.models.length - 1].id)
  }
  closeForm()
}

async function handleTest() {
  if (!form.endpoint || !form.apiKey || !form.model) {
    testResult.value = { ok: false, msg: '请先填写 API 地址、API Key 和模型标识' }
    return
  }
  testing.value = true
  testResult.value = null
  try {
    const res = await testModelConnection(form.endpoint, form.apiKey, form.model)
    if (res.ok) {
      testResult.value = { ok: true, msg: `连接成功${res.response ? '：' + res.response : ''}` }
    } else {
      testResult.value = { ok: false, msg: res.error || '连接失败' }
    }
  } catch (e: any) {
    testResult.value = { ok: false, msg: e.message || '网络错误' }
  } finally {
    testing.value = false
  }
}
</script>
