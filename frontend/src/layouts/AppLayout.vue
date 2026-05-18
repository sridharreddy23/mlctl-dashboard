<template>
  <div class="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900">
    <a href="#main-content" class="skip-link">Skip to main content</a>

    <header class="sticky top-0 z-40 border-b border-slate-200 bg-white/95 backdrop-blur dark:border-slate-800 dark:bg-slate-900/95">
      <div class="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-3 sm:px-6 lg:px-8">
        <div class="flex items-center gap-3">
          <div class="flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-primary-600 to-primary-700">
            <span class="text-sm font-bold text-white">ML</span>
          </div>
          <div class="hidden sm:block">
            <h1 class="text-lg font-bold text-slate-900 dark:text-white">MLCtl Dashboard</h1>
            <p class="text-xs text-slate-500 dark:text-slate-400">MediaLive Control Center</p>
          </div>
            <p class="text-[10px] text-slate-400 sm:hidden">Made by Sridhar</p>
        </div>

        <div class="flex items-center gap-2">
          <span
            :class="[
              'hidden items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium sm:inline-flex',
              healthClass,
            ]"
            :title="healthTitle"
          >
            <span class="h-1.5 w-1.5 rounded-full" :class="healthDotClass" />
            {{ healthLabel }}
          </span>

          <button type="button" class="btn-ghost" title="Keyboard shortcuts (Shift+?)" @click="showHelp = true">
            <HelpCircle class="h-5 w-5" />
            <span class="sr-only">Keyboard shortcuts</span>
          </button>

          <button type="button" class="btn-ghost" title="Toggle dark mode" @click="toggleDark">
            <Moon v-if="!isDark" class="h-5 w-5" />
            <Sun v-else class="h-5 w-5" />
          </button>
        </div>
      </div>
    </header>

    <div class="mx-auto flex max-w-7xl gap-0 lg:gap-8">
      <aside class="hidden w-56 shrink-0 flex-col border-r border-slate-200 px-3 py-6 dark:border-slate-800 lg:flex">
        <nav class="space-y-1" aria-label="Main navigation">
          <RouterLink
            v-for="(item, idx) in navItems"
            :key="item.to"
            :to="item.to"
            :class="['nav-item', isActive(item.to) ? 'nav-item-active' : 'nav-item-inactive']"
          >
            <component :is="item.icon" class="h-5 w-5 shrink-0" />
            <span class="flex-1">{{ item.label }}</span>
            <span
              v-if="item.to === '/jobs' && totalActiveJobs > 0"
              class="rounded-full bg-primary-500 px-1.5 py-0.5 text-[10px] font-bold leading-none text-white"
            >{{ totalActiveJobs }}</span>
            <span v-else class="font-mono text-xs text-slate-400">{{ idx + 1 }}</span>
          </RouterLink>
        </nav>
        <p class="mt-auto px-3 pt-8 text-xs text-slate-400 dark:text-slate-500">
          Made by <span class="font-medium text-slate-600 dark:text-slate-300">Sridhar</span>
        </p>
      </aside>

      <main id="main-content" class="min-w-0 flex-1 px-4 py-6 pb-24 sm:px-6 lg:px-8 lg:pb-8">
        <RouterView v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" class="animate-fade-in space-y-6" />
          </transition>
        </RouterView>
      </main>
    </div>

    <nav class="fixed bottom-0 left-0 right-0 z-40 border-t border-slate-200 bg-white/95 backdrop-blur dark:border-slate-800 dark:bg-slate-900/95 lg:hidden" aria-label="Mobile navigation">
      <div class="flex justify-around px-1 py-2">
        <RouterLink
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          :class="[
            'flex flex-1 flex-col items-center gap-0.5 rounded-lg py-1.5 text-[10px] font-medium transition-ui',
            isActive(item.to) ? 'text-primary-600 dark:text-primary-400' : 'text-slate-500 dark:text-slate-400',
          ]"
        >
          <span class="relative">
            <component :is="item.icon" class="h-5 w-5" />
            <span
              v-if="item.to === '/jobs' && totalActiveJobs > 0"
              class="absolute -right-2 -top-1 flex h-3.5 w-3.5 items-center justify-center rounded-full bg-primary-500 text-[8px] font-bold text-white"
            >{{ totalActiveJobs > 9 ? '9+' : totalActiveJobs }}</span>
          </span>
          {{ item.shortLabel }}
        </RouterLink>
      </div>
    </nav>

    <ToastNotifications />
    <KeyboardHelpModal :visible="showHelp" @close="showHelp = false" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter, RouterLink, RouterView } from 'vue-router'
import {
  LayoutDashboard,
  Calendar,
  List,
  Radio,
  Settings,
  Moon,
  Sun,
  HelpCircle,
} from 'lucide-vue-next'
import { useStore } from '../stores/main'
import ToastNotifications from '../components/ToastNotifications.vue'
import KeyboardHelpModal from '../components/KeyboardHelpModal.vue'

const store = useStore()
const route = useRoute()
const router = useRouter()
const showHelp = ref(false)
const healthStatus = ref<'ok' | 'degraded' | 'offline'>('offline')

const totalActiveJobs = computed(() => store.activeJobs.length + store.activeMediaLiveJobs.length)

// Simple dark mode toggle — replaces @vueuse/core useDark
const DARK_KEY = 'mlctl-dark-mode'
const isDark = ref(false)

const applyDark = (dark: boolean) => {
  isDark.value = dark
  document.documentElement.classList.toggle('dark', dark)
  localStorage.setItem(DARK_KEY, dark ? 'true' : 'false')
}

const initDark = () => {
  const stored = localStorage.getItem(DARK_KEY)
  if (stored !== null) {
    applyDark(stored === 'true')
  } else {
    applyDark(window.matchMedia('(prefers-color-scheme: dark)').matches)
  }
}

const toggleDark = () => applyDark(!isDark.value)

const navItems = [
  { to: '/', label: 'Dashboard', shortLabel: 'Home', icon: LayoutDashboard },
  { to: '/schedule', label: 'Schedule', shortLabel: 'Schedule', icon: Calendar },
  { to: '/jobs', label: 'Jobs', shortLabel: 'Jobs', icon: List },
  { to: '/medialive', label: 'MediaLive Inputs', shortLabel: 'Inputs', icon: Radio },
  { to: '/settings', label: 'Settings', shortLabel: 'Settings', icon: Settings },
]

const isActive = (path: string) => {
  if (path === '/') return route.path === '/'
  return route.path.startsWith(path)
}

const healthLabel = computed(() => {
  if (healthStatus.value === 'ok') return 'Connected'
  if (healthStatus.value === 'degraded') return 'Not configured'
  return 'Offline'
})

const healthClass = computed(() => {
  if (healthStatus.value === 'ok') return 'bg-success-50 text-success-700 dark:bg-success-50/10 dark:text-success-500'
  if (healthStatus.value === 'degraded') return 'bg-warning-50 text-warning-600 dark:bg-warning-50/10 dark:text-warning-500'
  return 'bg-danger-50 text-danger-600 dark:bg-danger-50/10 dark:text-danger-500'
})

const healthDotClass = computed(() => {
  if (healthStatus.value === 'ok') return 'bg-success-500'
  if (healthStatus.value === 'degraded') return 'bg-warning-500'
  return 'bg-danger-500'
})

const healthTitle = computed(() => `API health: ${healthLabel.value}`)

const checkHealth = async () => {
  try {
    const data = await store.checkHealth()
    healthStatus.value = data.configured ? 'ok' : 'degraded'
  } catch {
    healthStatus.value = 'offline'
  }
}

const handleKeydown = (e: KeyboardEvent) => {
  const tag = (e.target as HTMLElement)?.tagName
  if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return

  if (e.key === '?' && e.shiftKey) {
    e.preventDefault()
    showHelp.value = true
    return
  }

  if (e.key === 'r' && !e.ctrlKey && !e.metaKey) {
    store.fetchJobs()
    store.fetchMediaLiveJobs()
    checkHealth()
    store.addToast('Jobs refreshed', 'info', 2000)
    return
  }

  const idx = parseInt(e.key, 10)
  if (idx >= 1 && idx <= navItems.length) {
    router.push(navItems[idx - 1].to)
  }
}

let pollInterval: ReturnType<typeof setInterval> | null = null
let healthInterval: ReturnType<typeof setInterval> | null = null

onMounted(async () => {
  initDark()

  await store.fetchConfig()
  await store.fetchJobs()
  await checkHealth()

  document.addEventListener('keydown', handleKeydown)

  pollInterval = setInterval(async () => {
    await store.fetchJobs()
    await store.fetchMediaLiveJobs()
  }, 15000)

  healthInterval = setInterval(checkHealth, 60000)
})

onUnmounted(() => {
  if (pollInterval) clearInterval(pollInterval)
  if (healthInterval) clearInterval(healthInterval)
  document.removeEventListener('keydown', handleKeydown)
})
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
