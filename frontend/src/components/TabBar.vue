<template>
  <div class="tabs">
    <router-link to="/download" class="tab">小说下载</router-link>
    <router-link to="/create-v2" class="tab tab-primary">创作V2</router-link>
    <router-link to="/modules" class="tab">模块总览</router-link>
  </div>
</template>

<script setup lang="ts">
</script>

<style scoped>
.tabs {
  display: flex;
  max-width: 1560px;
  margin: 21px auto 0;
  padding: 0 16px;
  gap: 8px;
}
.tab {
  flex: 1;
  padding: 16px 8px;
  text-align: center;
  background: #fff;
  border-radius: 13px 10px 0 0;
  font-size: 17px;
  font-weight: 600;
  cursor: pointer;
  color: #888;
  border-bottom: 4px solid transparent;
  transition: .2s;
  text-decoration: none;
  white-space: nowrap;
}
.tab.active { color: var(--primary); border-bottom-color: var(--primary); }
.tab.router-link-active { color: var(--primary); border-bottom-color: var(--primary); }
.tab:hover { color: var(--primary); }
.tab-primary { background: linear-gradient(135deg, #e8f4fd, #f0f0ff); }
</style>
