import { ref, readonly, onBeforeUnmount } from 'vue'

export interface ConfirmOptions {
  title?: string
  message: string
  confirmText?: string
  cancelText?: string
  type?: 'warning' | 'danger' | 'info'
  detail?: string
}

interface QueueItem {
  opts: ConfirmOptions
  resolve: (value: boolean) => void
  componentId: symbol
}

const visible = ref(false)
const options = ref<ConfirmOptions>({ message: '' })
const queue: QueueItem[] = []
const MAX_QUEUE_SIZE = 3
let overflowHandler: ((opts: ConfirmOptions) => void) | null = null

function processQueue() {
  if (queue.length === 0) {
    visible.value = false
    return
  }
  const item = queue[0]
  options.value = {
    title: item.opts.title || '确认操作',
    message: item.opts.message,
    confirmText: item.opts.confirmText || '确定',
    cancelText: item.opts.cancelText || '取消',
    type: item.opts.type || 'warning',
    detail: item.opts.detail,
  }
  visible.value = true
}

export function useConfirm() {
  const componentId = Symbol('confirm')

  function confirm(opts: ConfirmOptions): Promise<boolean> {
    if (queue.length >= MAX_QUEUE_SIZE) {
      if (overflowHandler) overflowHandler(opts)
      else {
        try { console.warn('[useConfirm] queue full, confirm suppressed:', opts.message) } catch (_e) { /* noop */ }
      }
      return Promise.resolve(false)
    }
    return new Promise<boolean>((resolve) => {
      queue.push({ opts, resolve, componentId })
      if (queue.length === 1) processQueue()
    })
  }

  function handleConfirm() {
    const item = queue.shift()
    item?.resolve(true)
    processQueue()
  }

  function handleCancel() {
    const item = queue.shift()
    item?.resolve(false)
    processQueue()
  }

  onBeforeUnmount(() => {
    for (let i = queue.length - 1; i >= 0; i--) {
      if (queue[i].componentId === componentId) {
        queue[i].resolve(false)
        queue.splice(i, 1)
      }
    }
    if (queue.length > 0) processQueue()
  })

  return {
    confirm,
    visible: readonly(visible),
    options: readonly(options),
    handleConfirm,
    handleCancel,
  }
}

export function setConfirmOverflowHandler(handler: (opts: ConfirmOptions) => void) {
  overflowHandler = handler
}

let instance: ReturnType<typeof useConfirm> | null = null

export function setupConfirm() {
  if (!instance) { instance = useConfirm() }
  return instance
}
