<template>
  <div class="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900">
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
        <div class="flex items-center space-x-2">
          <button @click="enableNotifications" class="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800" title="Enable notifications">
            <span class="text-xl">{{ notificationsEnabled ? '🔔' : '🔕' }}</span>
          </button>
          <button @click="toggleDarkMode" class="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800" title="Toggle dark mode">
            <span v-if="!isDark" class="text-xl">🌙</span>
            <span v-else class="text-xl">☀️</span>
          </button>
        </div>
      </div>
    </header>

    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div class="flex space-x-4 mb-8 border-b border-slate-200 dark:border-slate-800">
        <button
          v-for="(tab, idx) in tabs"
          :key="tab.id"
          @click="activeTab = tab.id"
          :class="[
            'px-4 py-3 font-medium text-sm border-b-2 transition-colors',
            activeTab === tab.id
              ? 'border-blue-600 text-blue-600 dark:text-blue-400'
              : 'border-transparent text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
          ]"
        >
          <span class="hidden sm:inline">{{ tab.label }}</span>
          <span class="sm:hidden">{{ tab.icon }}</span>
          <span class="ml-1 text-xs text-slate-400 dark:text-slate-600 font-mono">{{ idx + 1 }}</span>
        </button>
      </div>

      <div class="space-y-6">
        <DashboardView v-if="activeTab === 'dashboard'" />
        <ScheduleView v-if="activeTab === 'schedule'" @scheduled="handleScheduled" />
        <JobsView v-if="activeTab === 'jobs'" />
        <MediaLiveInputView v-if="activeTab === 'medialive-inputs'" />
        <SettingsView v-if="activeTab === 'settings'" />
      </div>
    </main>

    <ToastNotifications />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useStore } from './stores/main'
import DashboardView from './components/DashboardView.vue'
import ScheduleView from './components/ScheduleView.vue'
import JobsView from './components/JobsView.vue'
import SettingsView from './components/SettingsView.vue'
import MediaLiveInputView from './components/MediaLiveInputView.vue'
import ToastNotifications from './components/ToastNotifications.vue'
import { requestNotificationPermission, detectJobChanges } from './utils/notifications'

const store = useStore()
const activeTab = ref('dashboard')
const isDark = ref(false)
const notificationsEnabled = ref(false)
let jobStatuses: Record<string, string> = {}

const tabs = [
  { id: 'dashboard', label: '📊 Dashboard', icon: '📊' },
  { id: 'schedule', label: '⏱️ Schedule', icon: '⏱️' },
  { id: 'jobs', label: '📋 Jobs', icon: '📋' },
  { id: 'medialive-inputs', label: '🎚️ Inputs', icon: '🎚️' },
  { id: 'settings', label: '⚙️ Settings', icon: '⚙️' }
]

const toggleDarkMode = () => {
  isDark.value = !isDark.value
  document.documentElement.classList.toggle('dark')
  localStorage.setItem('mlctl-dark-mode', String(isDark.value))
}

const enableNotifications = async () => {
  const granted = await requestNotificationPermission()
  notificationsEnabled.value = granted
  store.addToast(
    granted ? 'Browser notifications enabled' : 'Notification permission denied',
    granted ? 'success' : 'warning',
    3000
  )
}

// Keyboard shortcuts
const handleKeydown = (e: KeyboardEvent) => {
  // Ignore if typing in an input/textarea/select
  const tag = (e.target as HTMLElement)?.tagName
  if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return

  if (e.key === 'Escape') {
    // Close modals — handled by individual components via event propagation
    return
  }

  if (e.key === 'r' && !e.ctrlKey && !e.metaKey) {
    store.fetchJobs()
    store.fetchMediaLiveJobs()
    store.addToast('Jobs refreshed', 'info', 2000)
    return
  }

  const idx = parseInt(e.key, 10)
  if (idx >= 1 && idx <= tabs.length) {
    activeTab.value = tabs[idx - 1].id
  }
}

let pollInterval: ReturnType<typeof setInterval> | null = null

onMounted(() => {
  // Restore dark mode
  if (localStorage.getItem('mlctl-dark-mode') === 'true') {
    isDark.value = true
    document.documentElement.classList.add('dark')
  }

  // Check notification permission
  if ('Notification' in window && Notification.permission === 'granted') {
    notificationsEnabled.value = true
  }

  store.fetchConfig()
  store.fetchJobs()

  // Keyboard shortcuts
  document.addEventListener('keydown', handleKeydown)

  // Poll jobs every 10s with browser notification detection
  pollInterval = setInterval(async () => {
    await store.fetchJobs()
    await store.fetchMediaLiveJobs()

    // Detect state changes for browser notifications
    if (notificationsEnabled.value) {
      const allJobs = [...store.jobs, ...store.medialiveJobs]
      jobStatuses = detectJobChanges(jobStatuses, allJobs)
    }
  }, 10000)

  // Initialize job status tracking
  setTimeout(() => {
    const allJobs = [...store.jobs, ...store.medialiveJobs]
    allJobs.forEach(j => { jobStatuses[j.id] = j.status })
  }, 2000)
})

onUnmounted(() => {
  if (pollInterval) clearInterval(pollInterval)
  document.removeEventListener('keydown', handleKeydown)
})

const handleScheduled = () => { activeTab.value = 'jobs' }
</script>
