<template>
  <div class="source-tabs">
    <div v-for="tab in tabs" :key="tab.value" class="source-tab" :class="{ active: modelValue === tab.value }" @click="$emit('change', tab.value)">{{ tab.label }}</div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  tabs: { label: string; value: string }[]
  modelValue: string
}>()

defineEmits<{ change: [value: string] }>()
</script>
