<template>
  <div class="tree-node" :style="{ paddingLeft: depth * 18 + 'px' }">
    <div class="tree-line" @click="expanded = !expanded">
      <span class="tree-toggle">{{ hasChildren ? (expanded ? 'v' : '>') : ' ' }}</span>
      <span class="tree-key">{{ nodeKey }}</span>
    </div>
    <div v-if="expanded" class="tree-children">
      <template v-if="typeof nodeValue === 'object' && nodeValue !== null">
        <TreeNode v-for="(v, k) in nodeValue" :key="k" :node-key="String(k)" :node-value="v" :depth="depth + 1" />
      </template>
      <div v-else class="tree-val">{{ nodeValue }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

defineOptions({ name: 'TreeNode' })

const props = defineProps<{ nodeKey: string; nodeValue: any; depth: number }>()
const expanded = ref(props.depth < 2)
const hasChildren = computed(() => {
  return props.nodeValue !== null && typeof props.nodeValue === 'object'
})
</script>

<style scoped>
.tree-node { font-size: 14px; margin: 2px 0; }
.tree-line { cursor: pointer; display: flex; align-items: center; padding: 3px 0; border-radius: 4px; }
.tree-line:hover { background: #f0f4ff; }
.tree-toggle { width: 16px; text-align: center; font-family: monospace; color: #888; font-size: 12px; }
.tree-key { font-weight: 600; color: var(--primary); }
.tree-children { margin: 2px 0; }
.tree-val { padding: 2px 0 2px 16px; color: #555; white-space: pre-wrap; word-break: break-word; }
</style>
