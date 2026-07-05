<template>
  <select :value="modelValue" @change="$emit('change', Number(($event.target as HTMLSelectElement).value))" style="flex:1;padding:7px;border:1px solid #ddd;border-radius:4px;font-size:12px">
    <option v-for="(m, i) in settings.models" :key="m.id" :value="i">{{ m.name }}</option>
  </select>
</template>

<script setup lang="ts">
import { useSettingsStore } from '../stores/settings'

defineProps<{
  modelValue: number
}>()

defineEmits<{ change: [index: number] }>()

const settings = useSettingsStore()
</script>
