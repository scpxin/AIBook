import { ref } from 'vue'

type SaveFn = () => Promise<void>

const _pendingSaves = ref<Set<SaveFn>>(new Set())

export function registerSaveFn(fn: SaveFn) {
   _pendingSaves.value.add(fn)
   return () => { _pendingSaves.value.delete(fn) }
}

export async function flushAllSaves(): Promise<void> {
   const fns = Array.from(_pendingSaves.value)
   await Promise.all(fns.map(fn => fn().catch(() => {})))
}
