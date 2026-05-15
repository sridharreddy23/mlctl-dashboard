<template>
  <div class="space-y-6">
    <!-- API Configuration -->
    <div class="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 p-6">
      <h2 class="text-lg font-semibold text-slate-900 dark:text-white mb-4">API Configuration</h2>

      <div v-if="configStatus?.configured" class="mb-6 p-4 bg-green-50 dark:bg-green-950 border border-green-200 dark:border-green-800 rounded-lg flex items-center space-x-3">
        <span class="text-2xl">✓</span>
        <div>
          <p class="font-medium text-green-800 dark:text-green-200">Configured</p>
          <p class="text-sm text-green-700 dark:text-green-300">Environment variables are set</p>
        </div>
      </div>

      <form @submit.prevent="handleConfigSubmit" class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">Client ID</label>
          <input
            v-model="formData.client_id"
            type="text"
            placeholder="ML_CLIENT_ID"
            required
            class="w-full px-4 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white placeholder-slate-400 dark:placeholder-slate-500 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">Client Secret</label>
          <input
            v-model="formData.client_secret"
            type="password"
            placeholder="ML_CLIENT_SECRET"
            required
            class="w-full px-4 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white placeholder-slate-400 dark:placeholder-slate-500 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">Base URL</label>
          <input
            v-model="formData.base_url"
            type="url"
            placeholder="https://api.example.com"
            required
            class="w-full px-4 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white placeholder-slate-400 dark:placeholder-slate-500 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">BLIP Domain</label>
          <input
            v-model="formData.blip_domain"
            type="text"
            placeholder="your-domain"
            required
            class="w-full px-4 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white placeholder-slate-400 dark:placeholder-slate-500 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        <button
          type="submit"
          :disabled="configLoading"
          class="w-full px-6 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-400 text-white font-semibold rounded-lg transition-colors flex items-center justify-center space-x-2"
        >
          <span v-if="!configLoading">Save Configuration</span>
          <span v-else class="flex items-center space-x-2">
            <span class="animate-spin-slow w-4 h-4 border-2 border-white border-t-transparent rounded-full"></span>
            <span>Saving...</span>
          </span>
        </button>
      </form>
    </div>

    <!-- Channels Configuration -->
    <div class="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 p-6">
      <h2 class="text-lg font-semibold text-slate-900 dark:text-white mb-4">Channels Configuration</h2>
      <p class="text-sm text-slate-600 dark:text-slate-400 mb-4">
        Channels are loaded from: <code class="bg-slate-100 dark:bg-slate-700 px-2 py-1 rounded">~/bin/config/channels.json</code>
      </p>
      <button
        @click="loadChannels"
        :disabled="channelsLoading"
        class="px-6 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-400 text-white font-semibold rounded-lg transition-colors flex items-center space-x-2"
      >
        <span v-if="!channelsLoading">Reload Channels</span>
        <span v-else class="flex items-center space-x-2">
          <span class="animate-spin-slow w-4 h-4 border-2 border-white border-t-transparent rounded-full"></span>
          <span>Loading...</span>
        </span>
      </button>
      <p class="text-sm text-slate-600 dark:text-slate-400 mt-3">
        Channels loaded: <span class="font-semibold">{{ store.channels.length }}</span>
      </p>
    </div>

    <!-- About -->
    <div class="bg-gradient-to-r from-blue-600 to-blue-700 rounded-xl shadow-sm p-6 text-white">
      <h2 class="text-lg font-semibold mb-2">MLCtl Dashboard</h2>
      <p class="text-blue-100 text-sm mb-4">Professional MediaLive Control Center</p>
      <p class="text-xs text-blue-200">Version 1.0.0 • Built with Vue 3 + FastAPI</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useStore } from '../stores/main'

const store = useStore()
const configLoading = ref(false)
const channelsLoading = ref(false)
const configStatus = ref<any>(null)

const formData = reactive({
  client_id: '',
  client_secret: '',
  base_url: '',
  blip_domain: ''
})

const handleConfigSubmit = async () => {
  if (!formData.client_id || !formData.client_secret || !formData.base_url || !formData.blip_domain) {
    alert('All fields are required')
    return
  }

  configLoading.value = true
  try {
    await store.updateConfig(formData)
    configStatus.value = store.config
  } finally {
    configLoading.value = false
  }
}

const loadChannels = async () => {
  channelsLoading.value = true
  try {
    await store.fetchChannels()
  } finally {
    channelsLoading.value = false
  }
}

onMounted(async () => {
  configStatus.value = store.config || {}
})
</script>
