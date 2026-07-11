<template>
  <div class="consistency-panel panel">
    <div class="panel-header" @click="expanded = !expanded">
      <span>一致性</span>
      <span class="toggle">{{ expanded ? '▼' : '▶' }}</span>
    </div>
    <div v-if="expanded" class="panel-body">
      <div v-if="!issues.length" class="empty">暂无一致性问题</div>
      <div v-else class="issues-list">
        <div v-for="(issue, idx) in issues" :key="idx" class="issue-item" :class="issue.severity">
          <span class="issue-type">{{ issue.type }}</span>
          <span class="issue-msg">{{ issue.message }}</span>
        </div>
      </div>
      <button class="btn-check" @click="runCheck" :disabled="checking">
        {{ checking ? '检查中...' : '运行检查' }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useKnowledgeStore } from '../stores/knowledge'

const props = defineProps<{ projectId: string }>()
const knowledge = useKnowledgeStore()
const expanded = ref(true)
const issues = ref<any[]>([])
const checking = ref(false)

watch(() => props.projectId, async (pid) => {
  if (pid) {
    await knowledge.loadConsistencyReports(pid)
    issues.value = knowledge.latestReport?.issues || []
  }
}, { immediate: true })

async function runCheck() {
  checking.value = true
  try {
    await knowledge.executeConsistencyCheck(props.projectId)
    issues.value = knowledge.latestReport?.issues || []
  } finally {
    checking.value = false
  }
}
</script>

<style scoped>
.panel { margin-bottom: 16px; border: 1px solid #eee; border-radius: 8px; background: #fff; }
.panel-header { padding: 10px 12px; font-weight: 600; font-size: 17px; cursor: pointer; display: flex; justify-content: space-between; }
.panel-body { padding: 0 12px 12px; }
.toggle { font-size: 13px; }
.empty { color: #52c41a; font-size: 16px; padding: 10px 0; }
.issues-list { max-height: 195px; overflow-y: auto; }
.issue-item { font-size: 14px; padding: 5px 0; border-bottom: 1px solid #f5f5f5; display: flex; gap: 8px; }
.issue-type { font-weight: 600; flex-shrink: 0; }
.issue-item.error .issue-type { color: #ff4d4f; }
.issue-item.warning .issue-type { color: #fa8c16; }
.issue-item.info .issue-type { color: #1890ff; }
.issue-msg { color: #666; word-break: break-all; }
.btn-check { margin-top: 10px; width: 100%; padding: 8px; background: #f5f5f5; border: 1px solid #ddd; border-radius: 5px; font-size: 16px; cursor: pointer; }
.btn-check:disabled { opacity: 0.6; cursor: wait; }
</style>
