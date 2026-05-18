<template>
  <div class="space-y-6">
    <div>
      <h2 class="page-title">Settings</h2>
      <p class="page-subtitle">API credentials and channel configuration</p>
    </div>

    <UiCard title="API Configuration">
      <div v-if="configStatus?.configured" class="mb-6 flex items-center gap-3 rounded-lg border border-success-200 bg-success-50 p-4 dark:border-success-600/30 dark:bg-success-50/10">
        <CheckCircle2 class="h-6 w-6 text-success-600" />
        <div>
          <p class="font-medium text-success-800 dark:text-success-200">Configured</p>
          <p class="text-sm text-success-700 dark:text-success-300">Environment variables are set</p>
        </div>
      </div>

      <form class="space-y-4" @submit.prevent="handleConfigSubmit">
        <UiInput v-model="formData.client_id" label="Client ID" placeholder="ML_CLIENT_ID" required />

        <!-- Client Secret with show/hide toggle -->
        <div>
          <label class="mb-2 block text-sm font-medium text-slate-700 dark:text-slate-300">
            Client Secret <span class="text-danger-500">*</span>
          </label>
          <div class="relative">
            <input
              v-model="formData.client_secret"
              :type="showSecret ? 'text' : 'password'"
              placeholder="ML_CLIENT_SECRET"
              required
              class="input-field pr-10"
            />
            <button
              type="button"
              class="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
              :title="showSecret ? 'Hide secret' : 'Show secret'"
              @click="showSecret = !showSecret"
            >
              <Eye v-if="!showSecret" class="h-4 w-4" />
              <EyeOff v-else class="h-4 w-4" />
            </button>
          </div>
        </div>

        <UiInput v-model="formData.base_url" label="Base URL" type="url" placeholder="https://api.example.com" required />
        <UiInput v-model="formData.blip_domain" label="BLIP Domain" placeholder="your-domain" required />
        <UiButton type="submit" variant="primary" block :loading="configLoading">Save Configuration</UiButton>
      </form>

      <!-- Test Connection -->
      <div class="mt-4 border-t border-slate-200 pt-4 dark:border-slate-700">
        <div class="flex items-center gap-3">
          <UiButton variant="secondary" :loading="testLoading" @click="testConnection">
            <Wifi class="h-4 w-4" />
            Test Connection
          </UiButton>
          <div v-if="testResult" :class="[
            'flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium',
            testResult.ok
              ? 'bg-success-50 text-success-700 dark:bg-success-950/30 dark:text-success-400'
              : 'bg-danger-50 text-danger-700 dark:bg-danger-950/30 dark:text-danger-400',
          ]">
            <CheckCircle2 v-if="testResult.ok" class="h-4 w-4" />
            <XCircle v-else class="h-4 w-4" />
            {{ testResult.message }}
          </div>
        </div>
      </div>
    </UiCard>

    <UiCard title="Channels Configuration">
      <p class="mb-4 text-sm text-slate-600 dark:text-slate-400">
        Channels are loaded from:
        <code class="rounded bg-slate-100 px-2 py-1 dark:bg-slate-700">~/bin/config/channels.json</code>
      </p>
      <UiButton variant="primary" :loading="channelsLoading" @click="loadChannels">Reload Channels</UiButton>
      <p class="mt-3 text-sm text-slate-600 dark:text-slate-400">
        Channels loaded: <span class="font-semibold text-slate-900 dark:text-white">{{ store.channels.length }}</span>
      </p>
    </UiCard>

    <div class="rounded-xl bg-gradient-to-r from-primary-600 to-primary-700 p-6 text-white shadow-elevated">
      <h2 class="text-lg font-semibold">MLCtl Dashboard</h2>
      <p class="mb-4 text-sm text-primary-100">Professional MediaLive Control Center</p>
      <p class="text-xs text-primary-200">Version 1.2.0 · Vue 3 + FastAPI</p>
      <p class="mt-2 text-sm text-primary-100">Made by <span class="font-semibold">Sridhar</span></p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { CheckCircle2, XCircle, Eye, EyeOff, Wifi } from 'lucide-vue-next'
import { useStore } from '../stores/main'
import UiCard from './ui/UiCard.vue'
import UiButton from './ui/UiButton.vue'
import UiInput from './ui/UiInput.vue'

const store = useStore()
const configLoading = ref(false)
const channelsLoading = ref(false)
const testLoading = ref(false)
const showSecret = ref(false)
const configStatus = ref<any>(null)
const testResult = ref<{ ok: boolean; message: string } | null>(null)

const formData = reactive({
  client_id: '',
  client_secret: '',
  base_url: '',
  blip_domain: '',
})

const handleConfigSubmit = async () => {
  if (!formData.client_id || !formData.client_secret || !formData.base_url || !formData.blip_domain) {
    store.addToast('All fields are required', 'error')
    return
  }
  configLoading.value = true
  try {
    await store.updateConfig(formData)
    configStatus.value = store.config
    testResult.value = null
  } finally {
    configLoading.value = false
  }
}

const testConnection = async () => {
  testLoading.value = true
  testResult.value = null
  try {
    const data = await store.checkHealth()
    testResult.value = data.configured
      ? { ok: true, message: 'Connected — API is configured' }
      : { ok: false, message: 'Reachable but not configured — check credentials' }
  } catch {
    testResult.value = { ok: false, message: 'Cannot reach backend — is it running?' }
  } finally {
    testLoading.value = false
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

onMounted(() => {
  configStatus.value = store.config || {}
})
</script>
