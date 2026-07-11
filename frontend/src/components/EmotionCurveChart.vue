<template>
  <div class="emotion-curve-wrapper">
    <svg :width="svgWidth" :height="height" class="emotion-curve">
      <polyline
        :points="points"
        fill="none"
        stroke="var(--primary)"
        stroke-width="2"
      />
      <circle v-for="(p, idx) in pointCoords" :key="idx" :cx="p.x" :cy="p.y" r="3" fill="var(--primary)" />
    </svg>
    <div v-if="!curve || !curve.length" class="empty">暂无情绪数据</div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  curve: number[]
  height?: number
}>()

const svgWidth = 200
const computedHeight = computed(() => props.height || 40)

const points = computed(() => {
  if (!props.curve || !props.curve.length) return ''
  const max = 10
  const step = svgWidth / Math.max(props.curve.length - 1, 1)
  return props.curve.map((v, i) => {
    const x = i * step
    const y = computedHeight.value - (v / max) * computedHeight.value
    return `${x},${y}`
  }).join(' ')
})

const pointCoords = computed(() => {
  if (!props.curve || !props.curve.length) return []
  const max = 10
  const step = svgWidth / Math.max(props.curve.length - 1, 1)
  return props.curve.map((v, i) => ({
    x: i * step,
    y: computedHeight.value - (v / max) * computedHeight.value,
  }))
})
</script>

<style scoped>
.emotion-curve-wrapper { position: relative; }
.emotion-curve { display: block; }
.empty { position: absolute; top: 0; left: 0; right: 0; text-align: center; font-size: 14px; color: #999; }
</style>
