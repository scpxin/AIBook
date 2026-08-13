<template>
  <div class="header">
    <h1>AI创作平台</h1>
    <p>智能写作 · 一站式创作体验</p>
    <button class="settings-btn" @click="showSettings = true">&#9881; 模型配置</button>
    <router-link to="/api-keys" class="settings-btn">&#128273; API 密钥</router-link>
  </div>

  <TabBar />

  <div class="container">
    <router-view v-slot="{ Component }">
      <keep-alive>
        <component :is="Component" />
      </keep-alive>
    </router-view>
  </div>

  <ModelConfig v-if="showSettings" @close="showSettings = false" />
  <AppConfirmDialog />
  <ToastContainer />
</template>

<script setup lang="ts">
import { onErrorCaptured } from 'vue'
import TabBar from './components/TabBar.vue'
import ModelConfig from './components/ModelConfig.vue'
import AppConfirmDialog from './components/AppConfirmDialog.vue'
import ToastContainer from './components/ToastContainer.vue'
import { useSettingsPanel } from './composables/useSettingsPanel'

const { showSettings } = useSettingsPanel()

onErrorCaptured((err, instance, info) => {
  console.error('[App Error]', err, info)
  return false
})
</script>
