<template>
  <UiCard>
    <template #header>
      <div class="flex w-full flex-wrap items-center justify-between gap-3">
        <div>
          <h2 class="text-lg font-semibold text-slate-900 dark:text-white">Channel Status</h2>
          <p v-if="loading" class="text-xs text-primary-600 dark:text-primary-400">Checking channels…</p>
          <p v-else-if="lastRefreshed" class="text-xs text-slate-500 dark:text-slate-400">Updated {{ lastRefreshed }}</p>
        </div>
        <div class="flex items-center gap-2">
          <UiSelect v-model="statusFilter" class="w-40 text-sm">
            <option value="">All states</option>
            <option value="RUNNING">Running</option>
            <option value="IDLE">Standby (Idle)</option>
            <option value="STARTING">Starting</option>
            <option value="STOPPING">Stopping</option>
            <option value="UNKNOWN">Unknown</option>
          </UiSelect>
          <UiButton variant="secondary" size="sm" :loading="loading" @click="refresh">Refresh</UiButton>
        </div>
      </div>
    </template>

    <div
      v-if="statusMessage && !loading"
      class="mb-4 rounded-lg border border-warning-200 bg-warning-50 px-4 py-3 text-sm text-warning-800 dark:border-warning-800 dark:bg-warning-950/40 dark:text-warning-200"
      role="alert"
    >
      {{ statusMessage }}
    </div>

    <UiEmptyState
      v-if="filteredStatuses.length === 0 && !loading && !statusMessage"
      title="No channels"
      description="Add channels to ~/bin/config/channels.json and reload from Settings."
      :icon="Radio"
    >
      <RouterLink to="/settings" class="mt-2 text-sm font-medium text-primary-600 hover:underline dark:text-primary-400">
        Open Settings
      </RouterLink>
    </UiEmptyState>

    <UiEmptyState
      v-else-if="filteredStatuses.length === 0 && !loading && statusMessage"
      title="Cannot load channel status"
      :description="statusMessage"
      :icon="AlertCircle"
    />

    <div v-else class="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
      <div
        v-for="ch in filteredStatuses"
        :key="ch.arn"
        :class="['rounded-lg border p-4 transition-ui', statusCardStyle(ch.status)]"
      >
        <div class="mb-1 flex items-center gap-2">
          <component
            :is="statusIconComponent(ch.status)"
            class="h-4 w-4 shrink-0"
            :class="[
              statusTextColor(ch.status),
              ['STARTING', 'STOPPING'].includes(ch.status.toUpperCase()) ? 'animate-spin-slow' : '',
            ]"
          />
          <p class="truncate text-sm font-medium text-slate-900 dark:text-white">{{ ch.name }}</p>
        </div>
        <p class="font-mono text-xs font-semibold" :class="statusTextColor(ch.status)">{{ ch.status }}</p>
        <p class="mt-1 truncate text-xs text-slate-500 dark:text-slate-400">{{ ch.arn.split(':').pop() }}</p>
        <p v-if="ch.error" class="mt-2 text-xs text-danger-600 dark:text-danger-400" :title="ch.error">
          {{ truncateError(ch.error) }}
        </p>
        <div class="mt-3 border-t pt-2" :class="statusDividerClass(ch.status)">
          <button
            type="button"
            class="flex w-full items-center justify-center gap-1 text-xs font-medium text-slate-400 transition-colors hover:text-primary-600 dark:text-slate-500 dark:hover:text-primary-400"
            @click="quickSchedule(ch.arn)"
          >
            <Calendar class="h-3.5 w-3.5" />
            Schedule Restart
          </button>
        </div>
      </div>

      <template v-if="loading && statuses.length === 0">
        <UiSkeleton v-for="i in 3" :key="'skel-' + i" height="5rem" class="rounded-lg" />
      </template>
    </div>
  </UiCard>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { Circle, CircleDot, AlertCircle, HelpCircle, Radio, Loader2, Calendar } from 'lucide-vue-next'
import { useStore, type ChannelStatusItem } from '../stores/main'
import UiCard from './ui/UiCard.vue'
import UiButton from './ui/UiButton.vue'
import UiSelect from './ui/UiSelect.vue'
import UiEmptyState from './ui/UiEmptyState.vue'
import UiSkeleton from './ui/UiSkeleton.vue'

const store = useStore()
const router = useRouter()
const loading = ref(false)
const statuses = ref<ChannelStatusItem[]>([])
const statusFilter = ref('')
const statusMessage = ref('')
const lastRefreshed = ref('')

const filteredStatuses = computed(() => {
  if (!statusFilter.value) return statuses.value
  return statuses.value.filter(ch => ch.status === statusFilter.value)
})

const truncateError = (msg: string) => (msg.length > 80 ? `${msg.slice(0, 77)}...` : msg)

let refreshAbort: AbortController | null = null

const quickSchedule = (arn: string) => {
  router.push({ path: '/schedule', query: { arn } })
}

const refresh = async () => {
  if (refreshAbort) refreshAbort.abort()
  refreshAbort = new AbortController()

  loading.value = true
  statusMessage.value = ''
  try {
    const data = await store.fetchChannelStatuses()
    if (refreshAbort?.signal.aborted) return

    if (Array.isArray(data)) {
      statuses.value = data
    } else {
      statuses.value = data.channels || []
      statusMessage.value = data.message || ''
      if (data.configured === false) {
        statusMessage.value = data.message || 'Configure API credentials in Settings.'
      }
    }

    if (statuses.value.length > 0 && store.channels.length === 0) {
      await store.fetchChannels().catch(() => {})
    }

    lastRefreshed.value = new Date().toLocaleTimeString()
  } catch (err: any) {
    if (err?.code === 'ERR_CANCELED') return
    if (statuses.value.length === 0) statuses.value = []
    statusMessage.value = err.response?.data?.detail || err.message || 'Failed to load channel status'
    store.addToast(statusMessage.value, 'error')
  } finally {
    if (!refreshAbort?.signal.aborted) loading.value = false
  }
}

const statusIconComponent = (status: string) => {
  const s = status.toUpperCase()
  if (s === 'RUNNING') return CircleDot
  if (s === 'IDLE') return Circle
  if (s === 'STARTING' || s === 'STOPPING') return Loader2
  if (s === 'UNKNOWN') return HelpCircle
  return AlertCircle
}

const statusCardStyle = (status: string) => {
  const s = status.toUpperCase()
  if (s === 'RUNNING')  return 'border-success-200 bg-success-50/50 dark:border-success-800 dark:bg-success-950/30'
  if (s === 'IDLE')     return 'border-slate-200 bg-slate-50 dark:border-slate-700 dark:bg-slate-800/30'
  if (s === 'STARTING' || s === 'STOPPING') return 'border-warning-200 bg-warning-50/50 dark:border-warning-800 dark:bg-warning-950/30'
  if (s === 'UNKNOWN')  return 'border-slate-200 bg-slate-50/50 dark:border-slate-700 dark:bg-slate-800/50'
  return 'border-danger-200 bg-danger-50/50 dark:border-danger-800 dark:bg-danger-950/30'
}

const statusDividerClass = (status: string) => {
  const s = status.toUpperCase()
  if (s === 'RUNNING')  return 'border-success-200/60 dark:border-success-800/40'
  if (s === 'IDLE')     return 'border-slate-200 dark:border-slate-700'
  if (s === 'STARTING' || s === 'STOPPING') return 'border-warning-200/60 dark:border-warning-800/40'
  return 'border-slate-200 dark:border-slate-700'
}

const statusTextColor = (status: string) => {
  const s = status.toUpperCase()
  if (s === 'RUNNING')  return 'text-success-700 dark:text-success-400'
  if (s === 'IDLE')     return 'text-slate-500 dark:text-slate-400'
  if (s === 'STARTING' || s === 'STOPPING') return 'text-warning-700 dark:text-warning-400'
  if (s === 'UNKNOWN')  return 'text-slate-500 dark:text-slate-400'
  return 'text-danger-700 dark:text-danger-400'
}

onMounted(() => { refresh() })
</script>
