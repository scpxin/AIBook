<template>
  <div class="timeline-chart">
    <div v-if="!events || !events.length" class="empty">暂无事件数据</div>
    <div v-else class="timeline">
      <div v-for="(evt, idx) in events" :key="idx" class="timeline-item" :class="{ editable }">
        <div class="timeline-marker"></div>
        <div class="timeline-content">
          <div class="event-name">{{ evt.name || evt.title }}</div>
          <div class="event-time">{{ evt.time || evt.chapter || '' }}</div>
          <div v-if="evt.description" class="event-desc">{{ evt.description }}</div>
        </div>
        <div v-if="editable" class="event-actions">
          <button @click="$emit('reorder', moveEvent(idx, -1))" class="btn-move">&#9650;</button>
          <button @click="$emit('reorder', moveEvent(idx, 1))" class="btn-move">&#9660;</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{
  events: any[]
  editable?: boolean
}>()

const emit = defineEmits<{
  reorder: [newEvents: any[]]
}>()

function moveEvent(idx: number, direction: number): any[] {
  const newEvents = [...props.events]
  const target = idx + direction
  if (target < 0 || target >= newEvents.length) return newEvents
  ;[newEvents[idx], newEvents[target]] = [newEvents[target], newEvents[idx]]
  return newEvents
}
</script>

<style scoped>
.empty { color: #999; font-size: 13px; padding: 20px; text-align: center; }
.timeline { position: relative; padding-left: 20px; }
.timeline::before { content: ''; position: absolute; left: 6px; top: 0; bottom: 0; width: 2px; background: #e0e0e0; }
.timeline-item { position: relative; padding: 8px 0 8px 16px; display: flex; align-items: flex-start; gap: 10px; }
.timeline-item.editable { cursor: grab; }
.timeline-marker { position: absolute; left: -17px; top: 14px; width: 10px; height: 10px; border-radius: 50%; background: var(--primary); border: 2px solid #fff; box-shadow: 0 0 0 1px var(--primary); }
.timeline-content { flex: 1; }
.event-name { font-weight: 600; font-size: 13px; }
.event-time { font-size: 11px; color: #999; }
.event-desc { font-size: 12px; color: #666; margin-top: 2px; }
.event-actions { display: flex; flex-direction: column; gap: 2px; }
.btn-move { background: none; border: 1px solid #ddd; border-radius: 3px; cursor: pointer; font-size: 10px; padding: 0 4px; }
.btn-move:hover { background: #f0f0f0; }
</style>
