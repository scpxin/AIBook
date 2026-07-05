<template>
  <div class="tabs">
    <router-link to="/download" class="tab">小说下载</router-link>
    <router-link to="/create" class="tab">AI创作</router-link>
    <router-link to="/craft" class="tab">网文技法</router-link>
  </div>
</template>

<script setup lang="ts">
</script>

<style scoped>
.tabs {
  display: flex;
  max-width: 900px;
  margin: 16px auto 0;
  padding: 0 20px;
  gap: 6px;
}
.tab {
  flex: 1;
  padding: 12px;
  text-align: center;
  background: #fff;
  border-radius: 10px 10px 0 0;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  color: #888;
  border-bottom: 3px solid transparent;
  transition: .2s;
  text-decoration: none;
}
.tab.active { color: var(--primary); border-bottom-color: var(--primary); }
.tab.router-link-active { color: var(--primary); border-bottom-color: var(--primary); }
.tab:hover { color: var(--primary); }
</style>
