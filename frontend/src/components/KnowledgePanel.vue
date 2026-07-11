<template>
  <div class="knowledge-panel panel">
    <div class="panel-header" @click="expanded = !expanded">
      <span>知识库</span>
      <span class="toggle">{{ expanded ? '▼' : '▶' }}</span>
    </div>
    <div v-if="expanded" class="panel-body">
      <div v-if="loading" class="loading">加载中...</div>
      <div v-else-if="!state.characterStates || !Object.keys(state.characterStates).length" class="empty">
        暂无数据
      </div>
      <div v-else>
        <div v-for="(val, key) in state.characterStates" :key="key" class="knowledge-item">
          <span class="key">{{ key }}</span>
          <span class="val">{{ typeof val === 'object' ? JSON.stringify(val) : val }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useKnowledgeStore } from '../stores/knowledge'

const props = defineProps<{ projectId: string }>()
const knowledge = useKnowledgeStore()
const expanded = ref(true)
const loading = ref(false)
const state = ref(knowledge.state)

watch(() => props.projectId, async (pid) => {
  if (pid) {
    loading.value = true
    await knowledge.loadSnapshot(pid)
    state.value = knowledge.state
    loading.value = false
  }
}, { immediate: true })

watch(() => knowledge.state, (newState) => {
  state.value = newState
})
</script>

<style scoped>
.panel { margin-bottom: 16px; border: 1px solid #eee; border-radius: 8px; background: #fff; }
.panel-header { padding: 10px 12px; font-weight: 600; font-size: 17px; cursor: pointer; display: flex; justify-content: space-between; }
.panel-body { padding: 0 12px 12px; max-height: 260px; overflow-y: auto; }
.toggle { font-size: 13px; }
.loading, .empty { color: #999; font-size: 16px; padding: 10px 0; }
.knowledge-item { display: flex; font-size: 14px; padding: 4px 0; border-bottom: 1px solid #f5f5f5; }
.knowledge-item .key { font-weight: 600; margin-right: 8px; color: #555; flex-shrink: 0; }
.knowledge-item .val { color: #888; word-break: break-all; }
</style>
