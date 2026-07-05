<template>
  <div class="foreshadow-panel panel">
    <div class="panel-header" @click="expanded = !expanded">
      <span>伏笔</span>
      <span class="toggle">{{ expanded ? '▼' : '▶' }}</span>
    </div>
    <div v-if="expanded" class="panel-body">
      <div v-if="!pending.length && !resolved.length" class="empty">暂无伏笔</div>
      <div v-if="pending.length" class="fs-section">
        <div class="fs-title">待收 ({{ pending.length }})</div>
        <div v-for="f in pending" :key="f.id" class="fs-item pending">
          <span class="fs-name">{{ f.name }}</span>
          <span class="fs-ch">第{{ f.setupChapter }}章</span>
        </div>
      </div>
      <div v-if="resolved.length" class="fs-section">
        <div class="fs-title">已收 ({{ resolved.length }})</div>
        <div v-for="f in resolved" :key="f.id" class="fs-item resolved">
          <span class="fs-name">{{ f.name }}</span>
          <span class="fs-ch">第{{ f.payoffChapter }}章</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useKnowledgeStore } from '../stores/knowledge'

const props = defineProps<{ projectId: string }>()
const knowledge = useKnowledgeStore()
const expanded = ref(true)
const foreshadows = ref<any[]>([])

const pending = computed(() => foreshadows.value.filter(f => f.status === 'pending'))
const resolved = computed(() => foreshadows.value.filter(f => f.status === 'resolved'))

watch(() => props.projectId, async (pid) => {
  if (pid) {
    await knowledge.loadForeshadows(pid)
    foreshadows.value = knowledge.foreshadows
  }
}, { immediate: true })

watch(() => knowledge.foreshadows, (val) => {
  foreshadows.value = val
})
</script>

<style scoped>
.panel { margin-bottom: 12px; border: 1px solid #eee; border-radius: 6px; background: #fff; }
.panel-header { padding: 8px 12px; font-weight: 600; font-size: 13px; cursor: pointer; display: flex; justify-content: space-between; }
.panel-body { padding: 0 12px 12px; max-height: 200px; overflow-y: auto; }
.toggle { font-size: 10px; }
.empty { color: #999; font-size: 12px; padding: 8px 0; }
.fs-section { margin-bottom: 8px; }
.fs-title { font-size: 11px; font-weight: 600; color: #666; padding: 4px 0; }
.fs-item { display: flex; font-size: 11px; padding: 3px 0; justify-content: space-between; }
.fs-item.pending { color: #fa8c16; }
.fs-item.resolved { color: #52c41a; text-decoration: line-through; }
.fs-name { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.fs-ch { color: #999; flex-shrink: 0; margin-left: 4px; }
</style>
