<template>
  <div class="p-4 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors">
    <div class="flex items-start justify-between">
      <div class="flex-1 min-w-0">
        <p class="font-semibold text-slate-900 dark:text-white">{{ job.name }}</p>
        <p class="text-xs text-slate-500 dark:text-slate-400 truncate mt-1">{{ job.arn }}</p>
        <!-- Client-side countdown for active jobs -->
        <p v-if="job.status === 'waiting'" class="text-xs text-blue-600 dark:text-blue-400 font-mono mt-1">⏱ {{ countdown }}</p>
      </div>
      <div class="flex items-center space-x-4 ml-4">
        <div class="text-right">
          <p class="text-sm font-medium" :class="getStatusColor(job.status)">{{ formatStatus(job.status) }}</p>
          <p class="text-xs text-slate-500 dark:text-slate-400">{{ job.time_until }}</p>
        </div>
        <div class="flex items-center space-x-2">
          <button @click="openLogs" class="px-3 py-1 text-xs font-medium bg-slate-100 dark:bg-slate-700 hover:bg-slate-200 dark:hover:bg-slate-600 text-slate-700 dark:text-slate-300 rounded transition-colors">Logs</button>
          <button v-if="job.status === 'failed' || job.status === 'done'" @click="retry" class="px-3 py-1 text-xs font-medium bg-blue-100 dark:bg-blue-900 hover:bg-blue-200 dark:hover:bg-blue-800 text-blue-700 dark:text-blue-300 rounded transition-colors">Retry</button>
          <button v-if="job.status === 'waiting' || job.status === 'running'" @click="cancelJob" :disabled="cancelling" class="px-3 py-1 text-xs font-medium bg-red-100 dark:bg-red-900 hover:bg-red-200 dark:hover:bg-red-800 disabled:opacity-50 text-red-700 dark:text-red-300 rounded transition-colors">{{ cancelling ? '...' : 'Cancel' }}</button>
        </div>
      </div>
    </div>

    <!-- Logs Modal with WebSocket streaming -->
    <Teleport to="body">
      <div v-if="showLogs" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" @keydown.escape="showLogs = false">
        <div class="bg-white dark:bg-slate-800 rounded-xl shadow-xl w-full max-w-2xl max-h-[80vh] flex flex-col">
          <div class="flex items-center justify-between p-6 border-b border-slate-200 dark:border-slate-700">
            <div>
              <h3 class="text-lg font-semibold text-slate-900 dark:text-white">Job Logs — {{ job.id }}</h3>
              <p v-if="wsConnected" class="text-xs text-green-600 dark:text-green-400 mt-1">● Live streaming</p>
              <p v-else class="text-xs text-slate-400 mt-1">○ HTTP polling</p>
            </div>
            <button @click="closeLogs" class="text-slate-500 hover:text-slate-700 dark:hover:text-slate-300 text-2xl">✕</button>
          </div>
          <div ref="logsContainer" class="flex-1 overflow-y-auto p-6 bg-slate-900 font-mono text-sm text-slate-100">
            <div v-if="logsLoading" class="flex items-center justify-center h-32"><span class="text-slate-400">Loading logs...</span></div>
            <pre v-else class="whitespace-pre-wrap">{{ logs }}</pre>
          </div>
          <div class="p-4 border-t border-slate-200 dark:border-slate-700 flex justify-end space-x-2">
            <button @click="refreshLogs" class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition-colors">Refresh</button>
            <button @click="closeLogs" class="px-4 py-2 bg-slate-200 dark:bg-slate-700 hover:bg-slate-300 dark:hover:bg-slate-600 text-slate-900 dark:text-white rounded-lg text-sm font-medium transition-colors">Close</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onUnmounted, computed } from 'vue'
import { useStore } from '../stores/main'
import type { Job } from '../stores/main'
import { formatStatus, getStatusColor } from '../utils/status'
import { useCountdown } from '../utils/countdown'

const props = defineProps<{ job: Job }>()
const emit = defineEmits(['retry'])
const store = useStore()

const showLogs = ref(false)
const logs = ref('')
const logsLoading = ref(false)
const cancelling = ref(false)
const logsContainer = ref<HTMLElement | null>(null)
const wsConnected = ref(false)
let ws: WebSocket | null = null

// Client-side countdown ticker
const countdown = useCountdown(() => props.job.time)

const scrollToBottom = () => {
  nextTick(() => {
    if (logsContainer.value) logsContainer.value.scrollTop = logsContainer.value.scrollHeight
  })
}

const connectWebSocket = () => {
  try {
    const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:'
    ws = new WebSocket(`${protocol}//${location.host}/ws/logs/${props.job.id}`)
    ws.onopen = () => { wsConnected.value = true }
    ws.onmessage = (event) => {
      logs.value += event.data
      scrollToBottom()
    }
    ws.onclose = () => { wsConnected.value = false }
    ws.onerror = () => { wsConnected.value = false }
  } catch {
    wsConnected.value = false
  }
}

const openLogs = async () => {
  showLogs.value = true
  await refreshLogs()
  connectWebSocket()
}

const closeLogs = () => {
  showLogs.value = false
  if (ws) { ws.close(); ws = null }
  wsConnected.value = false
}

const refreshLogs = async () => {
  logsLoading.value = true
  try {
    logs.value = await store.getJobLogs(props.job.id)
    scrollToBottom()
  } finally {
    logsLoading.value = false
  }
}

const cancelJob = async () => {
  cancelling.value = true
  try { await store.cancelJob(props.job.id) } finally { cancelling.value = false }
}

const retry = () => {
  emit('retry', { name: props.job.name, arn: props.job.arn, time: props.job.time })
}

onUnmounted(() => {
  if (ws) { ws.close(); ws = null }
})
</script>
