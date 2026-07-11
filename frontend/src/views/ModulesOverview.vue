<template>
  <div class="modules-overview">
    <div class="overview-header">
      <h2>19模块流水线总览</h2>
      <p class="sub">查看所有模块的生成状态与依赖关系</p>
    </div>

    <div v-if="loading" class="loading">加载中...</div>
    <div v-else-if="!modules.length" class="empty">暂无模块数据</div>

    <div v-else class="modules-grid">
      <div
        v-for="(mod, idx) in modules"
        :key="mod.name"
        class="module-card"
        :class="{
          done: getModuleStatus(mod.name) === 'done',
          active: getModuleStatus(mod.name) === 'generating',
          failed: getModuleStatus(mod.name) === 'failed',
          locked: getModuleStatus(mod.name) === 'locked',
        }"
        @click="navigateToModule(mod.name)"
      >
        <div class="card-header">
          <span class="card-idx">{{ idx + 1 }}</span>
          <span class="card-name">{{ mod.display_name || mod.name }}</span>
          <span class="card-layer">{{ mod.layer }}</span>
        </div>
        <div class="card-body">
          <div v-if="mod.dependencies?.length" class="card-deps">
            依赖: {{ mod.dependencies.join(', ') }}
          </div>
          <div v-else class="card-deps no-deps">无前置依赖</div>
        </div>
        <div class="card-footer">
          <span class="card-status-badge" :class="'badge-' + (getModuleStatus(mod.name) || 'pending')">
            {{ statusText(getModuleStatus(mod.name)) }}
          </span>
        </div>
      </div>
    </div>

    <div v-if="modules.length" class="overview-actions">
      <router-link to="/create-v2" class="btn-goto">进入流水线编辑器</router-link>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { usePipelineStore } from '../stores/pipeline'

const router = useRouter()
const pipeline = usePipelineStore()
const modules = ref<any[]>([])
const statuses = ref<Record<string, any>>({})
const loading = ref(true)

function getModuleStatus(name: string): string {
  return statuses.value[name] || 'pending'
}

function statusText(s: string): string {
  const map: Record<string, string> = { done: '已完成', generating: '生成中', failed: '失败', locked: '未解锁', pending: '待开始' }
  return map[s] || '待开始'
}

function navigateToModule(name: string) {
  if (getModuleStatus(name) !== 'locked') {
    router.push(`/create-v2/${name}`)
  }
}

onMounted(async () => {
  try {
    await pipeline.loadModules()
    modules.value = pipeline.modules
    const pid = pipeline.currentProjectId || ''
    if (pid) {
      await pipeline.loadStatus(pid)
      statuses.value = pipeline.progress?.modules || {}
    }
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.modules-overview {
  max-width: 1600px;
  margin: 0 auto;
  padding: 28px 16px;
}
.overview-header { margin-bottom: 28px; }
.overview-header h2 { font-size: 28px; margin: 0 0 6px; }
.sub { color: #888; font-size: 16px; margin: 0; }
.loading, .empty { text-align: center; padding: 80px 28px; color: #999; font-size: 18px; }
.modules-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 14px;
}
.module-card {
  background: #fff;
  border-radius: 16px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0,0,0,.06);
  cursor: pointer;
  transition: .2s;
  border: 2px solid transparent;
}
.module-card:hover { transform: translateY(-2px); box-shadow: 0 4px 16px rgba(0,0,0,.1); }
.module-card.done { border-color: #52c41a; }
.module-card.active { border-color: var(--primary); }
.module-card.failed { border-color: #ff4d4f; }
.module-card.locked { opacity: 0.5; cursor: not-allowed; }
.card-header { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }
.card-idx { width: 32px; height: 32px; border-radius: 50%; background: #f0f0f0; display: flex; align-items: center; justify-content: center; font-size: 16px; font-weight: 700; flex-shrink: 0; }
.done .card-idx { background: #52c41a; color: #fff; }
.active .card-idx { background: var(--primary); color: #fff; }
.failed .card-idx { background: #ff4d4f; color: #fff; }
.card-name { font-size: 18px; font-weight: 600; flex: 1; }
.card-layer { font-size: 14px; color: #888; background: #f0f0f0; padding: 2px 8px; border-radius: 4px; }
.card-body { margin-bottom: 10px; }
.card-deps { font-size: 15px; color: #666; }
.no-deps { color: #bbb; }
.card-footer { display: flex; justify-content: flex-end; }
.card-status-badge { font-size: 14px; padding: 3px 10px; border-radius: 6px; font-weight: 600; }
.badge-done { background: #f6ffed; color: #52c41a; }
.badge-generating { background: #e6f7ff; color: #1890ff; }
.badge-failed { background: #fff1f0; color: #ff4d4f; }
.badge-locked { background: #f5f5f5; color: #999; }
.badge-pending { background: #fffbe6; color: #faad14; }
.overview-actions { margin-top: 28px; text-align: center; }
.btn-goto { display: inline-block; padding: 14px 28px; background: var(--primary); color: #fff; border-radius: 10px; text-decoration: none; font-size: 16px; font-weight: 600; }
</style>
