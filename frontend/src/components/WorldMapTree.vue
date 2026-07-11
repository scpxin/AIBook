<template>
  <div class="world-map-tree">
    <div v-if="!structure || !structure.levels" class="empty">暂无世界结构数据</div>
    <div v-else class="tree">
      <div v-for="(level, idx) in structure.levels" :key="idx" class="tree-level">
        <div class="level-label">{{ level.name }}</div>
        <div class="level-nodes">
          <div v-for="node in level.nodes" :key="node" class="tree-node">{{ node }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{ structure: any }>()
</script>

<style scoped>
.empty { color: #999; font-size: 17px; padding: 26px; text-align: center; }
.tree { display: flex; flex-direction: column; gap: 16px; }
.tree-level { border: 1px solid #eee; border-radius: 8px; padding: 13px; }
.level-label { font-weight: 600; font-size: 18px; margin-bottom: 10px; color: var(--primary); }
.level-nodes { display: flex; flex-wrap: wrap; gap: 8px; }
.tree-node { font-size: 16px; padding: 4px 10px; background: #f0f8ff; border-radius: 5px; border: 1px solid #d6e4f0; }
</style>
