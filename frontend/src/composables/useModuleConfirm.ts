import { ref } from 'vue'
import { useConfirm } from './useConfirm'
import { useToast } from './useToast'

export interface ModuleConfirmOptions {
  moduleName: string
  saveFn: () => Promise<void>
  onComplete?: () => void
}

export function useModuleConfirm() {
  const confirm = useConfirm()
  const toast = useToast()
  const completing = ref(false)

  async function confirmAndComplete(options: ModuleConfirmOptions): Promise<boolean> {
    const { moduleName, saveFn, onComplete } = options

    const ok = await confirm.confirm({
      message: `确定完成「${moduleName}」模块？`,
      detail: '确认后将保存当前数据并进入下一模块',
      type: 'info',
    })
    if (!ok) return false

    completing.value = true
    try {
      await saveFn()
      toast.success(`${moduleName}已保存`)
      onComplete?.()
      return true
    } catch (e: any) {
      toast.error(`保存失败: ${e?.message || '未知错误'}`)
      return false
    } finally {
      completing.value = false
    }
  }

  return {
    confirmAndComplete,
    completing,
  }
}
