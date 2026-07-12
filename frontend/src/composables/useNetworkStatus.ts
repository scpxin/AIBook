import { ref, onMounted, onUnmounted } from 'vue'

const isOnline = ref(typeof navigator !== 'undefined' ? navigator.onLine : true)
let onlineHandler: (() => void) | null = null
let offlineHandler: (() => void) | null = null

export function useNetworkStatus() {
  onMounted(() => {
    onlineHandler = () => { isOnline.value = true }
    offlineHandler = () => { isOnline.value = false }
    window.addEventListener('online', onlineHandler)
    window.addEventListener('offline', offlineHandler)
  })

  onUnmounted(() => {
    if (onlineHandler) window.removeEventListener('online', onlineHandler)
    if (offlineHandler) window.removeEventListener('offline', offlineHandler)
  })

  return {
    isOnline,
  }
}
