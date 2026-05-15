<template>
  <div class="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900">
    <!-- Header -->
    <header class="sticky top-0 z-40 bg-white dark:bg-slate-900 shadow-sm border-b border-slate-200 dark:border-slate-800">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between">
        <div class="flex items-center space-x-3">
          <div class="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-600 to-blue-700 flex items-center justify-center">
            <span class="text-white font-bold">ML</span>
          </div>
          <div>
            <h1 class="text-xl font-bold text-slate-900 dark:text-white">MLCtl Dashboard</h1>
            <p class="text-xs text-slate-500 dark:text-slate-400">MediaLive Control Center</p>
          </div>
        </div>
        <button @click="toggleDarkMode" class="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800">
          <span v-if="!isDark" class="text-2xl">🌙</span>
          <span v-else class="text-2xl">☀️</span>
        </button>
      </div>
    </header>

    <!-- Alerts -->
    <div v-if="store.error || store.successMessage" class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-4 space-y-2">
      <div v-if="store.error" class="bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-800 rounded-lg p-4 flex items-start space-x-3">
        <span class="text-xl">⚠️</span>
        <div>
          <p class="font-semibold text-red-800 dark:text-red-200">Error</p>
          <p class="text-sm text-red-700 dark:text-red-300">{{ store.error }}</p>
        </div>
        <button @click="store.clearMessages" class="ml-auto text-red-600 hover:text-red-800">✕</button>
      </div>
      <div v-if="store.successMessage" class="bg-green-50 dark:bg-green-950 border border-green-200 dark:border-green-800 rounded-lg p-4 flex items-start space-x-3">
        <span class="text-xl">✓</span>
        <div>
          <p class="font-semibold text-green-800 dark:text-green-200">Success</p>
          <p class="text-sm text-green-700 dark:text-green-300">{{ store.successMessage }}</p>
        </div>
        <button @click="store.clearMessages" class="ml-auto text-green-600 hover:text-green-800">✕</button>
      </div>
    </div>

    <!-- Main Content -->
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <!-- Navigation Tabs -->
      <div class="flex space-x-4 mb-8 border-b border-slate-200 dark:border-slate-800">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          @click="activeTab = tab.id"
          :class="[
            'px-4 py-3 font-medium text-sm border-b-2 transition-colors',
            activeTab === tab.id
              ? 'border-blue-600 text-blue-600 dark:text-blue-400'
              : 'border-transparent text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
          ]"
        >
          {{ tab.label }}
        </button>
      </div>

      <!-- Tab Content -->
      <div class="space-y-6">
        <!-- Dashboard Tab -->
        <DashboardView v-if="activeTab === 'dashboard'" />

        <!-- Schedule Tab -->
        <ScheduleView v-if="activeTab === 'schedule'" @scheduled="handleScheduled" />

        <!-- Jobs Tab -->
        <JobsView v-if="activeTab === 'jobs'" />

        <!-- MediaLive Input Tab -->
        <MediaLiveInputView v-if="activeTab === 'medialive-inputs'" />

        <!-- Settings Tab -->
        <SettingsView v-if="activeTab === 'settings'" />
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useStore } from './stores/main'
import DashboardView from './components/DashboardView.vue'
import ScheduleView from './components/ScheduleView.vue'
import JobsView from './components/JobsView.vue'
import SettingsView from './components/SettingsView.vue'
import MediaLiveInputView from './components/MediaLiveInputView.vue'

const store = useStore()
const activeTab = ref('dashboard')
const isDark = ref(false)

const tabs = [
  { id: 'dashboard', label: '📊 Dashboard' },
  { id: 'schedule', label: '⏱️ Schedule' },
  { id: 'jobs', label: '📋 Jobs' },
  { id: 'medialive-inputs', label: '🎚️ Inputs' },
  { id: 'settings', label: '⚙️ Settings' }
]

const toggleDarkMode = () => {
  isDark.value = !isDark.value
  document.documentElement.classList.toggle('dark')
}

onMounted(() => {
  store.fetchConfig()
  store.fetchJobs()
  
  // Refresh jobs every 10 seconds
  const interval = setInterval(() => {
    store.fetchJobs()
    store.fetchMediaLiveJobs()
  }, 10000)
})

const handleScheduled = () => {
  activeTab.value = 'jobs'
}
</script>
