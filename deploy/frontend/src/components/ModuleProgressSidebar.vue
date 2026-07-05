<template>
  <div class="module-progress-sidebar">
    <div class="progress-header">
      <div class="progress-pct">{{ progressPct }}%</div>
      <div class="progress-bar">
        <div class="progress-fill" :style="{ width: progressPct + '%' }"></div>
      </div>
    </div>
    <div class="module-list">
      <div
        v-for="(mod, idx) in modules"
        :key="mod.name"
        class="module-item"
        :class="{
          active: mod.name === currentModule,
          done: mod.status === 'done',
          generating: mod.status === 'generating',
          failed: mod.status === 'failed',
          locked: mod.status === 'locked',
        }"
        @click="mod.status !== 'locked' && $emit('select', mod.name)"
      >
        <span class="module-idx">{{ idx + 1 }}</span>
        <span class="module-name">{{ mod.displayName }}</span>
        <span v-if="mod.status === 'done'" class="module-icon">&#10003;</span>
        <span v-else-if="mod.status === 'generating'" class="module-icon spin">&#9696;</span>
        <span v-else-if="mod.status === 'failed'" class="module-icon">&#10007;</span>
        <span v-else-if="mod.status === 'locked'" class="module-icon">&#128274;</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  modules: any[]
  currentModule: string
  progressPct: number
}>()

defineEmits<{
  select: [moduleName: string]
}>()
</script>

<style scoped>
.module-progress-sidebar {
  width: 200px;
  background: #fff;
  border-right: 1px solid #eee;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
}
.progress-header { padding: 16px; border-bottom: 1px solid #eee; }
.progress-pct { font-size: 24px; font-weight: 700; color: var(--primary); text-align: center; }
.progress-bar { height: 4px; background: #eee; border-radius: 2px; margin-top: 8px; }
.progress-fill { height: 100%; background: var(--primary); border-radius: 2px; transition: width 0.3s; }
.module-list { flex: 1; overflow-y: auto; padding: 8px 0; }
.module-item {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  cursor: pointer;
  transition: 0.15s;
  border-left: 3px solid transparent;
}
.module-item:hover { background: #f5f5f5; }
.module-item.active { background: #e8f4fd; border-left-color: var(--primary); }
.module-item.locked { opacity: 0.4; cursor: not-allowed; }
.module-item.done .module-name { color: #52c41a; }
.module-item.failed .module-name { color: #ff4d4f; }
.module-idx {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: #f0f0f0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  margin-right: 8px;
  flex-shrink: 0;
}
.module-item.active .module-idx { background: var(--primary); color: #fff; }
.module-item.done .module-idx { background: #52c41a; color: #fff; }
.module-name { flex: 1; font-size: 13px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.module-icon { font-size: 14px; margin-left: 4px; }
.module-item.done .module-icon { color: #52c41a; }
.module-item.failed .module-icon { color: #ff4d4f; }
.spin { animation: spin 1s linear infinite; display: inline-block; }
@keyframes spin { from { transform: rotate(0); } to { transform: rotate(360deg); } }
</style>
