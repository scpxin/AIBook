<template>
  <div class="module-result-card">
    <div class="card-header">
      <span class="module-name">{{ displayName }}</span>
      <span class="module-status" :class="status">{{ statusText }}</span>
    </div>
    <div v-if="summary" class="card-summary">{{ summary }}</div>
    <div v-if="data" class="card-data">
      <pre>{{ JSON.stringify(data, null, 2) }}</pre>
    </div>
    <div v-if="loading" class="card-loading">生成中...</div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  displayName: string
  status: string
  statusText?: string
  summary?: string
  data?: any
  loading?: boolean
}>()
</script>

<style scoped>
.module-result-card { border: 1px solid #eee; border-radius: 8px; padding: 16px; background: #fff; }
.card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.module-name { font-weight: 600; font-size: 15px; }
.module-status { font-size: 12px; padding: 2px 8px; border-radius: 4px; }
.module-status.done { background: #f6ffed; color: #52c41a; }
.module-status.generating { background: #e6f7ff; color: #1890ff; }
.module-status.pending { background: #fff7e6; color: #fa8c16; }
.module-status.failed { background: #fff1f0; color: #ff4d4f; }
.card-summary { font-size: 13px; color: #666; line-height: 1.6; }
.card-data pre { font-size: 11px; background: #f9f9f9; padding: 8px; border-radius: 4px; overflow-x: auto; max-height: 200px; margin: 8px 0 0; }
.card-loading { color: var(--primary); font-size: 13px; text-align: center; padding: 10px; }
</style>
