<template>
  <div :class="['border-l-4 p-4 transition-ui hover:bg-slate-50 dark:hover:bg-slate-700/50', statusBorderClass]">
    <div class="flex items-start justify-between gap-4">
      <div class="min-w-0 flex-1">
        <p class="font-semibold text-slate-900 dark:text-white">{{ job.name }}</p>
        <p class="mt-1 truncate text-xs text-slate-500 dark:text-slate-400">{{ job.arn }}</p>
        <p v-if="job.status === 'waiting'" class="mt-1 font-mono text-xs text-primary-600 dark:text-primary-400">{{ countdown }}</p>
      </div>
      <div class="flex shrink-0 flex-col items-end gap-2 sm:flex-row sm:items-center">
        <div class="text-right">
          <UiBadge :status="job.status" />
          <p class="mt-1 text-xs text-slate-500 dark:text-slate-400">{{ job.time_until }}</p>
        </div>
        <div class="flex flex-wrap justify-end gap-2">
          <UiButton variant="ghost" size="sm" title="Copy ARN" @click="copyArn">
            <Copy class="h-3.5 w-3.5" />
          </UiButton>
          <UiButton variant="secondary" size="sm" @click="openLogs">Logs</UiButton>
          <UiButton v-if="job.status === 'failed' || job.status === 'done'" variant="primary" size="sm" @click="retry">Retry</UiButton>
          <UiButton
            v-if="job.status === 'waiting' || job.status === 'running'"
            variant="danger"
            size="sm"
            :loading="cancelling"
            @click="cancelJob"
          >Cancel</UiButton>
        </div>
      </div>
    </div>

    <Teleport to="body">
      <div
        v-if="showLogs"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
        role="dialog"
        aria-modal="true"
        aria-labelledby="logs-title"
        @click.self="closeLogs"
      >
        <div ref="panelRef" class="card flex max-h-[80vh] w-full max-w-2xl flex-col shadow-elevated">
          <div class="flex items-center justify-between border-b border-slate-200 p-6 dark:border-slate-700">
            <div>
              <h3 id="logs-title" class="text-lg font-semibold text-slate-900 dark:text-white">Job Logs — {{ job.id }}</h3>
              <p v-if="isActiveJob" class="mt-0.5 flex items-center gap-1 text-xs text-success-600 dark:text-success-400">
                <span class="h-1.5 w-1.5 animate-pulse rounded-full bg-success-500" />
                Auto-refreshing every 3s
              </p>
            </div>
            <button type="button" class="btn-ghost p-1" aria-label="Close logs" @click="closeLogs">
              <X class="h-5 w-5" />
            </button>
          </div>
          <div ref="logsContainer" class="flex-1 overflow-y-auto bg-slate-900 p-6 font-mono text-sm text-slate-100">
            <div v-if="logsLoading" class="flex h-32 items-center justify-center text-slate-400">Loading logs...</div>
            <pre v-else-if="logs" class="whitespace-pre-wrap">{{ logs }}</pre>
            <p v-else class="text-slate-500">No logs yet.</p>
          </div>
          <div class="flex justify-end gap-2 border-t border-slate-200 p-4 dark:border-slate-700">
            <UiButton variant="primary" size="sm" :loading="logsLoading" @click="refreshLogs">Refresh</UiButton>
            <UiButton variant="secondary" size="sm" @click="closeLogs">Close</UiButton>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, toRef, onUnmounted } from 'vue'
import { Copy, X } from 'lucide-vue-next'
import { useStore } from '../stores/main'
import type { Job } from '../stores/main'
import { useCountdown } from '../utils/countdown'
import { useModal } from '../composables/useModal'
import UiBadge from './ui/UiBadge.vue'
import UiButton from './ui/UiButton.vue'

const props = defineProps<{ job: Job }>()
const emit = defineEmits<{ retry: [payload: { jobId: string; name: string; arn: string; time: string }] }>()
const store = useStore()

const showLogs = ref(false)
const logs = ref('')
const logsLoading = ref(false)
const cancelling = ref(false)
const logsContainer = ref<HTMLElement | null>(null)
let logInterval: ReturnType<typeof setInterval> | null = null

const countdown = useCountdown(() => props.job.time, () => props.job.status === 'waiting')

const isActiveJob = computed(() => props.job.status === 'waiting' || props.job.status === 'running')

// Left border colour by status
const statusBorderClass = computed(() => {
  const map: Record<string, string> = {
    waiting: 'border-l-warning-400',
    running: 'border-l-primary-500',
    done:    'border-l-success-500',
    failed:  'border-l-danger-500',
    cancelled: 'border-l-slate-300 dark:border-l-slate-600',
  }
  return map[props.job.status] ?? 'border-l-slate-200 dark:border-l-slate-700'
})

// Log auto-refresh
const stopLogRefresh = () => {
  if (logInterval) { clearInterval(logInterval); logInterval = null }
}

const startLogRefresh = () => {
  stopLogRefresh()
  logInterval = setInterval(async () => {
    if (!showLogs.value || !isActiveJob.value) { stopLogRefresh(); return }
    await refreshLogs()
  }, 3000)
}

const closeLogs = () => {
  stopLogRefresh()
  showLogs.value = false
}

const { panelRef } = useModal(toRef(showLogs), closeLogs)

const refreshLogs = async () => {
  logsLoading.value = true
  try {
    logs.value = await store.getJobLogs(props.job.id)
  } finally {
    logsLoading.value = false
  }
}

const openLogs = async () => {
  showLogs.value = true
  await refreshLogs()
  if (isActiveJob.value) startLogRefresh()
}

const cancelJob = async () => {
  cancelling.value = true
  try { await store.cancelJob(props.job.id) }
  finally { cancelling.value = false }
}

const retry = () => emit('retry', { jobId: props.job.id, name: props.job.name, arn: props.job.arn, time: props.job.time })

const copyArn = async () => {
  try {
    await navigator.clipboard.writeText(props.job.arn)
    store.addToast('ARN copied', 'success', 2000)
  } catch {
    store.addToast('Could not copy ARN', 'error', 2000)
  }
}

onUnmounted(stopLogRefresh)
</script>
