import { ref } from 'vue'

const showSettings = ref(false)

export function useSettingsPanel() {
  return { showSettings }
}
