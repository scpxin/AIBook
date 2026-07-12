import { ref, onMounted, type Ref } from 'vue'
import { getModuleData } from '../api/v2'

export function useModuleDataLoader(moduleName: string, projectId: Ref<string>) {
  const loading = ref(true)
  const loadError = ref('')
  const data = ref<any>(null)

  async function load() {
    loading.value = true
    loadError.value = ''
    try {
      const result = await getModuleData(projectId.value, moduleName)
      data.value = result?.data || null
    } catch (e: any) {
      loadError.value = e?.message || '加载数据失败'
    } finally {
      loading.value = false
    }
  }

  onMounted(load)

  return { loading, loadError, data, reload: load }
}
