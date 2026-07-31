<template>
  <div class="ak-page">
    <div class="ak-header">
      <h2>API 密钥</h2>
      <p class="ak-desc">管理用于访问 API 的密钥，密钥创建后仅显示一次</p>
    </div>

    <div class="ak-current">
      <label>当前使用密钥</label>
      <div class="ak-current-row">
        <input
          :value="currentKey"
          type="password"
          placeholder="未配置。输入密钥用于认证 API 请求"
          class="ak-input"
          @input="onKeyInput"
        />
        <button v-if="currentKey" class="ak-btn" @click="clearKey">清除</button>
      </div>
      <p v-if="keyStatus" class="ak-status">{{ keyStatus }}</p>
    </div>

    <div class="ak-create">
      <h3>创建新密钥</h3>
      <div class="ak-create-row">
        <input
          v-model="createForm.name"
          type="text"
          placeholder="密钥名称 (必填)"
          class="ak-input"
        />
        <input
          v-model="createForm.description"
          type="text"
          placeholder="描述 (可选)"
          class="ak-input"
        />
        <button class="ak-btn ak-btn-primary" :disabled="creating" @click="createKey">
          {{ creating ? '创建中...' : '创建' }}
        </button>
      </div>
      <p v-if="createError" class="ak-error">{{ createError }}</p>
    </div>

    <div v-if="newRawKey" class="ak-raw-key">
      <h3>新密钥已创建</h3>
      <p class="ak-raw-warning">此密钥仅显示一次，请立即复制并妥善保存</p>
      <div class="ak-raw-row">
        <code class="ak-raw-value">{{ newRawKey }}</code>
        <button class="ak-btn ak-btn-primary" @click="copyRawKey">复制</button>
        <button class="ak-btn" @click="newRawKey = ''">关闭</button>
      </div>
    </div>

    <div class="ak-list">
      <h3>密钥列表</h3>
      <div v-if="loading" class="ak-loading">加载中...</div>
      <div v-else-if="loadError" class="ak-error">
        <p>加载失败: {{ loadError }}</p>
        <button class="ak-btn ak-btn-sm" @click="loadKeys">重试</button>
      </div>
      <div v-else-if="keys.length === 0" class="ak-empty">暂无密钥，请在上方创建</div>
      <table v-else class="ak-table">
        <thead>
          <tr>
            <th>名称</th>
            <th>描述</th>
            <th>状态</th>
            <th>创建时间</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="k in keys" :key="k.id">
            <td>{{ k.name }}</td>
            <td>{{ k.description || '—' }}</td>
            <td><span :class="['ak-badge', k.isActive ? 'ak-badge-active' : 'ak-badge-revoked']">{{ k.isActive ? '活跃' : '已撤销' }}</span></td>
            <td>{{ formatDate(k.createdAt) }}</td>
            <td>
              <button
                v-if="k.isActive"
                class="ak-btn ak-btn-sm ak-btn-danger"
                @click="confirmRevoke(k)"
              >
                撤销
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="revokingKey" class="ak-overlay" @click.self="revokingKey = null">
      <div class="ak-modal">
        <h3>撤销密钥</h3>
        <p>确认撤销「{{ revokingKey.name }}」？撤销后该密钥将无法继续认证。</p>
        <div class="ak-modal-actions">
          <button class="ak-btn ak-btn-danger" :disabled="revoking" @click="doRevoke">
            {{ revoking ? '撤销中...' : '确认撤销' }}
          </button>
          <button class="ak-btn" @click="revokingKey = null">取消</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { getStoredApiKey, setStoredApiKey } from '../api/auth'
import {
  createApiKey,
  listApiKeys,
  revokeApiKey,
  type ApiKeyCreatePayload,
  type ApiKeyRecord,
} from '../api/apiKeys'

const currentKey = ref(getStoredApiKey())
const keyStatus = ref('')
const keys = ref<ApiKeyRecord[]>([])
const loading = ref(false)
const loadError = ref('')
const creating = ref(false)
const createError = ref('')
const createForm = ref<ApiKeyCreatePayload>({ name: '', description: '' })
const newRawKey = ref('')
const revokingKey = ref<ApiKeyRecord | null>(null)
const revoking = ref(false)

function onKeyInput(e: Event) {
  const value = (e.target as HTMLInputElement).value
  currentKey.value = value
  setStoredApiKey(value)
  keyStatus.value = value ? '已保存到当前会话' : ''
}

function clearKey() {
  currentKey.value = ''
  setStoredApiKey('')
  keyStatus.value = '已清除'
}

async function loadKeys() {
  loading.value = true
  loadError.value = ''
  try {
    keys.value = await listApiKeys()
  } catch (e: any) {
    loadError.value = e.message || String(e)
  } finally {
    loading.value = false
  }
}

async function createKey() {
  if (!createForm.value.name.trim()) {
    createError.value = '请填写密钥名称'
    return
  }
  creating.value = true
  createError.value = ''
  try {
    const result = await createApiKey({
      name: createForm.value.name.trim(),
      description: createForm.value.description?.trim() || '',
    })
    newRawKey.value = result.rawKey || ''
    createForm.value = { name: '', description: '' }
    await loadKeys()
  } catch (e: any) {
    createError.value = e.message || String(e)
  } finally {
    creating.value = false
  }
}

async function copyRawKey() {
  try {
    await navigator.clipboard.writeText(newRawKey.value)
    createError.value = '已复制到剪贴板'
  } catch {
    createError.value = '复制失败，请手动复制'
  }
}

function confirmRevoke(k: ApiKeyRecord) {
  revokingKey.value = k
}

async function doRevoke() {
  if (!revokingKey.value) return
  revoking.value = true
  try {
    await revokeApiKey(revokingKey.value.id)
    revokingKey.value = null
    await loadKeys()
  } catch (e: any) {
    loadError.value = e.message || String(e)
  } finally {
    revoking.value = false
  }
}

function formatDate(value: string): string {
  if (!value) return '—'
  return value.replace('T', ' ').slice(0, 19)
}

onMounted(loadKeys)
</script>

<style scoped>
.ak-page {
  padding: 16px;
  max-width: 860px;
  margin: 0 auto;
}
.ak-header h2 { margin: 0 0 4px; }
.ak-desc { margin: 0 0 16px; color: #666; }
.ak-current, .ak-create, .ak-list {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
}
.ak-current label { font-weight: 600; display: block; margin-bottom: 8px; }
.ak-current-row, .ak-create-row, .ak-raw-row, .ak-modal-actions { display: flex; gap: 8px; }
.ak-current-row .ak-input { flex: 1; }
.ak-input {
  flex: 1;
  padding: 8px 10px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
}
.ak-btn {
  padding: 8px 14px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  background: #fff;
  cursor: pointer;
  font-size: 14px;
  white-space: nowrap;
}
.ak-btn:hover { background: #f3f4f6; }
.ak-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.ak-btn-primary { background: #2563eb; border-color: #2563eb; color: #fff; }
.ak-btn-primary:hover { background: #1d4ed8; }
.ak-btn-danger { background: #dc2626; border-color: #dc2626; color: #fff; }
.ak-btn-danger:hover { background: #b91c1c; }
.ak-btn-sm { padding: 4px 10px; font-size: 13px; }
.ak-status { margin: 8px 0 0; color: #16a34a; font-size: 13px; }
.ak-error { color: #dc2626; font-size: 14px; margin: 8px 0; }
.ak-loading, .ak-empty { color: #6b7280; padding: 16px 0; text-align: center; }
.ak-raw-key {
  background: #fefce8;
  border: 1px solid #fde047;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
}
.ak-raw-key h3 { margin: 0 0 4px; }
.ak-raw-warning { color: #a16207; margin: 0 0 8px; }
.ak-raw-value {
  flex: 1;
  padding: 8px;
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  overflow-x: auto;
  user-select: all;
  font-size: 13px;
}
.ak-table { width: 100%; border-collapse: collapse; font-size: 14px; }
.ak-table th, .ak-table td { text-align: left; padding: 8px; border-bottom: 1px solid #f3f4f6; }
.ak-table th { color: #6b7280; font-weight: 600; }
.ak-badge { padding: 2px 8px; border-radius: 9999px; font-size: 12px; }
.ak-badge-active { background: #dcfce7; color: #16a34a; }
.ak-badge-revoked { background: #fee2e2; color: #dc2626; }
.ak-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}
.ak-modal {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  max-width: 420px;
  width: 90%;
}
.ak-modal h3 { margin: 0 0 8px; }
.ak-modal p { margin: 0 0 16px; color: #374151; }
.ak-modal-actions { justify-content: flex-end; }
</style>
