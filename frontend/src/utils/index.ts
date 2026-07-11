export function generateId(): string {
  return 'pj-' + Date.now().toString(36) + '-' + Math.random().toString(36).slice(2, 8)
}

export function formatDate(d?: string | Date): string {
  const date = d ? new Date(d) : new Date()
  return date.toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' })
}

export function debounce<T extends (...args: any[]) => any>(fn: T, ms: number): T {
  let timer: any
  return ((...args: any[]) => {
    clearTimeout(timer)
    timer = setTimeout(() => fn(...args), ms)
  }) as T
}
