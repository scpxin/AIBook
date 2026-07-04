<template>
  <div class="tabs">
    <div class="tab" :class="{ active: active === 0 }" @click="$emit('change', 0)">小说下载</div>
    <div class="tab" :class="{ active: active === 1 }" @click="$emit('change', 1)">AI创作</div>
    <div class="tab" :class="{ active: active === 2 }" @click="$emit('change', 2)">网文技法</div>
  </div>
</template>

<script setup lang="ts">
defineProps<{ active: number }>()
defineEmits<{ change: [tab: number] }>()
</script>

<style scoped>
.tabs {
  display: flex;
  max-width: 900px;
  margin: 16px auto 0;
  padding: 0 20px;
  gap: 6px;
}
.tab {
  flex: 1;
  padding: 12px;
  text-align: center;
  background: #fff;
  border-radius: 10px 10px 0 0;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  color: #888;
  border-bottom: 3px solid transparent;
  transition: .2s;
}
.tab.active { color: var(--primary); border-bottom-color: var(--primary); }
.tab:hover { color: var(--primary); }
</style>
