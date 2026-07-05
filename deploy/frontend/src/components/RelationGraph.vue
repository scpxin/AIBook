<template>
  <div class="relation-graph">
    <div v-if="!characters.length" class="empty">暂无角色数据</div>
    <svg v-else :width="width" :height="height" class="graph-svg">
      <line
        v-for="(rel, idx) in relationLines"
        :key="'line-' + idx"
        :x1="rel.x1" :y1="rel.y1" :x2="rel.x2" :y2="rel.y2"
        :stroke="rel.color || '#999'" stroke-width="1.5"
      />
      <g v-for="(node, idx) in nodes" :key="'node-' + idx">
        <circle :cx="node.x" :cy="node.y" :r="20" fill="#e8f4fd" stroke="var(--primary)" stroke-width="1.5" />
        <text :x="node.x" :y="node.y + 4" text-anchor="middle" font-size="11" fill="#333">{{ node.label }}</text>
      </g>
    </svg>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  characters: any[]
  relations?: any[]
}>()

const width = 500
const height = 300

const nodes = computed(() => {
  const chars = props.characters.filter(c => c.name).slice(0, 10)
  const angleStep = (2 * Math.PI) / chars.length
  const cx = width / 2
  const cy = height / 2
  const r = Math.min(cx, cy) - 40
  return chars.map((c: any, i: number) => ({
    x: cx + r * Math.cos(i * angleStep - Math.PI / 2),
    y: cy + r * Math.sin(i * angleStep - Math.PI / 2),
    label: c.name?.slice(0, 4) || '',
  }))
})

const relationLines = computed(() => {
  const lines: any[] = []
  if (!props.relations || !props.relations.length) {
    const n = nodes.value
    for (let i = 0; i < n.length - 1; i++) {
      lines.push({ x1: n[i].x, y1: n[i].y, x2: n[i + 1].x, y2: n[i + 1].y })
    }
    if (n.length > 2) {
      lines.push({ x1: n[n.length - 1].x, y1: n[n.length - 1].y, x2: n[0].x, y2: n[0].y })
    }
    return lines
  }
  for (const rel of props.relations) {
    const from = nodes.value.find(n => n.label === (rel.from || '').slice(0, 4))
    const to = nodes.value.find(n => n.label === (rel.to || '').slice(0, 4))
    if (from && to) {
      lines.push({ x1: from.x, y1: from.y, x2: to.x, y2: to.y })
    }
  }
  return lines
})
</script>

<style scoped>
.relation-graph { display: flex; justify-content: center; padding: 10px; }
.empty { color: #999; font-size: 13px; padding: 20px; }
.graph-svg { max-width: 100%; }
</style>
