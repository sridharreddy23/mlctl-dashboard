<template>
  <div class="space-y-6">
    <div class="flex items-end justify-between gap-4">
      <div>
        <h2 class="page-title">Dashboard</h2>
        <p class="page-subtitle">Overview of jobs and channel health</p>
      </div>
      <div class="flex items-center gap-3">
        <span v-if="timeAgoStr" class="hidden text-xs text-slate-400 dark:text-slate-500 sm:block">Updated {{ timeAgoStr }}</span>
        <button
          type="button"
          class="btn-ghost flex items-center gap-1.5 text-xs"
          :class="{ 'pointer-events-none opacity-50': refreshing }"
          @click="refreshAll"
        >
          <RefreshCw class="h-3.5 w-3.5" :class="{ 'animate-spin': refreshing }" />
          Refresh
        </button>
        <RouterLink to="/jobs" class="text-sm font-medium text-primary-600 hover:text-primary-700 dark:text-primary-400">View all →</RouterLink>
      </div>
    </div>

    <div class="grid grid-cols-1 gap-4 md:grid-cols-4">
      <UiCard v-for="stat in stats" :key="stat.label" padding="md" :class="stat.cardClass">
        <div class="flex items-start justify-between">
          <div>
            <p class="text-sm font-medium text-slate-600 dark:text-slate-400">{{ stat.label }}</p>
            <p class="mt-2 text-3xl font-bold" :class="stat.valueClass">{{ stat.value }}</p>
          </div>
          <component :is="stat.icon" class="h-8 w-8 opacity-80" :class="stat.iconClass" aria-hidden="true" />
        </div>
        <div class="mt-3 h-1 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-700">
          <div class="h-full rounded-full transition-all" :class="stat.barClass" :style="{ width: stat.barWidth }" />
        </div>
      </UiCard>
    </div>

    <ChannelStatusGrid />


    <UiCard title="Active Jobs">
      <UiEmptyState
        v-if="store.activeJobs.length === 0"
        title="No active jobs"
        description="Scheduled restarts will appear here."
        :icon="Clock"
      />
      <div v-else class="space-y-3">
        <div
          v-for="job in store.activeJobs"
          :key="job.id"
          class="flex items-center justify-between rounded-lg bg-slate-50 p-4 transition-ui hover:bg-slate-100 dark:bg-slate-700/50 dark:hover:bg-slate-700"
        >
          <div class="min-w-0 flex-1">
            <p class="truncate font-medium text-slate-900 dark:text-white">{{ job.name }}</p>
            <p class="truncate text-xs text-slate-500 dark:text-slate-400">{{ job.arn }}</p>
          </div>
          <div class="ml-4 flex items-center gap-4">
            <div class="text-right">
              <UiBadge :status="job.status" />
              <p class="mt-1 text-xs text-slate-500 dark:text-slate-400">{{ job.time_until }}</p>
            </div>
            <span v-if="job.status === 'waiting'" class="h-2 w-2 animate-pulse-soft rounded-full bg-warning-500" />
            <span v-else-if="job.status === 'running'" class="h-2 w-2 animate-spin-slow rounded-full bg-primary-500" />
          </div>
        </div>
      </div>
    </UiCard>

    <UiCard title="Recent Activity">
      <UiEmptyState
        v-if="recentJobs.length === 0"
        title="No completed jobs yet"
        :icon="History"
      />
      <div v-else class="space-y-2">
        <div
          v-for="job in recentJobs"
          :key="job.id"
          class="flex items-center justify-between border-b border-slate-200 py-3 last:border-b-0 dark:border-slate-700"
        >
          <div>
            <p class="text-sm font-medium text-slate-900 dark:text-white">{{ job.name }}</p>
            <p class="text-xs text-slate-500 dark:text-slate-400">{{ humanizeRelativeTime(job.time) }}</p>
          </div>
          <UiBadge :status="job.status" />
        </div>
      </div>
    </UiCard>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { RouterLink } from 'vue-router'
import { Briefcase, PlayCircle, CheckCircle2, XCircle, Clock, History, RefreshCw } from 'lucide-vue-next'
import { useStore } from '../stores/main'
import { humanizeRelativeTime } from '../utils/status'
import ChannelStatusGrid from './ChannelStatusGrid.vue'
import UiCard from './ui/UiCard.vue'
import UiBadge from './ui/UiBadge.vue'
import UiEmptyState from './ui/UiEmptyState.vue'

const store = useStore()
const refreshing = ref(false)
const lastUpdated = ref(Date.now())
const timeAgoStr = ref('')
let timeAgoTimer: ReturnType<typeof setInterval> | null = null

const updateTimeAgo = () => {
  const secs = Math.round((Date.now() - lastUpdated.value) / 1000)
  if (secs < 10) timeAgoStr.value = 'just now'
  else if (secs < 60) timeAgoStr.value = `${secs}s ago`
  else timeAgoStr.value = `${Math.floor(secs / 60)}m ago`
}

const refreshAll = async () => {
  refreshing.value = true
  try {
    await store.fetchJobs()
    await store.fetchMediaLiveJobs()
    lastUpdated.value = Date.now()
    timeAgoStr.value = 'just now'
  } finally {
    refreshing.value = false
  }
}

const total = computed(() => store.jobs.length || 1)
const completedCount = computed(() => store.jobs.filter(j => j.status === 'done').length)
const failedCount = computed(() => store.jobs.filter(j => j.status === 'failed').length)


const pct = (n: number) => `${Math.round((n / total.value) * 100)}%`

const stats = computed(() => [
  {
    label: 'Total Jobs',
    value: store.jobs.length,
    icon: Briefcase,
    valueClass: 'text-slate-900 dark:text-white',
    iconClass: 'text-slate-400',
    barClass: 'bg-slate-400',
    barWidth: '100%',
    cardClass: '',
  },
  {
    label: 'Active',
    value: store.activeJobs.length,
    icon: PlayCircle,
    valueClass: 'text-primary-600',
    iconClass: 'text-primary-500',
    barClass: 'bg-primary-500',
    barWidth: pct(store.activeJobs.length),
    cardClass: '',
  },
  {
    label: 'Completed',
    value: completedCount.value,
    icon: CheckCircle2,
    valueClass: 'text-success-600',
    iconClass: 'text-success-500',
    barClass: 'bg-success-500',
    barWidth: pct(completedCount.value),
    cardClass: '',
  },
  {
    label: 'Failed',
    value: failedCount.value,
    icon: XCircle,
    valueClass: 'text-danger-600',
    iconClass: 'text-danger-500',
    barClass: 'bg-danger-500',
    barWidth: pct(failedCount.value),
    cardClass: '',
  },
])

const recentJobs = computed(() =>
  [...store.completedJobs]
    .sort((a, b) => (b.time || '').localeCompare(a.time || ''))
    .slice(0, 8)
)

onMounted(() => {
  lastUpdated.value = Date.now()
  timeAgoStr.value = 'just now'
  timeAgoTimer = setInterval(updateTimeAgo, 10000)
})

onUnmounted(() => {
  if (timeAgoTimer) clearInterval(timeAgoTimer)
})
</script>
