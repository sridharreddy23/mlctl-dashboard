<template>
  <div class="p-4 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors">
    <div class="flex items-start justify-between">
      <div class="flex-1 min-w-0">
        <div class="flex items-center space-x-3">
          <div class="flex-1">
            <p class="font-semibold text-slate-900 dark:text-white">{{ job.name }}</p>
            <p class="text-xs text-slate-500 dark:text-slate-400 truncate mt-1">{{ job.arn }}</p>
          </div>
        </div>
      </div>

      <div class="flex items-center space-x-4 ml-4">
        <div class="text-right">
          <p class="text-sm font-medium" :class="getStatusColor(job.status)">{{ formatStatus(job.status) }}</p>
          <p class="text-xs text-slate-500 dark:text-slate-400">{{ job.time_until }}</p>
        </div>
        
        <div class="flex items-center space-x-2">
          <button
            v-if="job.status === 'waiting'"
            @click="openLogs"
            class="px-3 py-1 text-xs font-medium bg-slate-100 dark:bg-slate-700 hover:bg-slate-200 dark:hover:bg-slate-600 text-slate-700 dark:text-slate-300 rounded transition-colors"
          >
            Logs
          </button>
          <button
            v-else-if="job.status !== 'done' && job.status !== 'failed' && job.status !== 'cancelled'"
            @click="openLogs"
            class="px-3 py-1 text-xs font-medium bg-slate-100 dark:bg-slate-700 hover:bg-slate-200 dark:hover:bg-slate-600 text-slate-700 dark:text-slate-300 rounded transition-colors"
          >
            Logs
          </button>
          <button
            v-if="job.status === 'waiting' || job.status === 'running'"
            @click="cancelJob"
            :disabled="cancelling"
            class="px-3 py-1 text-xs font-medium bg-red-100 dark:bg-red-900 hover:bg-red-200 dark:hover:bg-red-800 disabled:opacity-50 text-red-700 dark:text-red-300 rounded transition-colors"
          >
            {{ cancelling ? 'Cancelling...' : 'Cancel' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Logs Modal -->
    <Teleport to="body">
      <div v-if="showLogs" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
        <div class="bg-white dark:bg-slate-800 rounded-xl shadow-xl w-full max-w-2xl max-h-[80vh] flex flex-col">
          <div class="flex items-center justify-between p-6 border-b border-slate-200 dark:border-slate-700">
            <h3 class="text-lg font-semibold text-slate-900 dark:text-white">Job Logs - {{ job.id }}</h3>
            <button @click="showLogs = false" class="text-slate-500 hover:text-slate-700 dark:hover:text-slate-300 text-2xl">✕</button>
          </div>

          <div class="flex-1 overflow-y-auto p-6 bg-slate-900 font-mono text-sm text-slate-100">
            <div v-if="logsLoading" class="flex items-center justify-center h-32">
              <span class="text-slate-400">Loading logs...</span>
            </div>
            <pre v-else>{{ logs }}</pre>
          </div>

          <div class="p-4 border-t border-slate-200 dark:border-slate-700 flex justify-end space-x-2">
            <button @click="refreshLogs" class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition-colors">
              Refresh
            </button>
            <button @click="showLogs = false" class="px-4 py-2 bg-slate-200 dark:bg-slate-700 hover:bg-slate-300 dark:hover:bg-slate-600 text-slate-900 dark:text-white rounded-lg text-sm font-medium transition-colors">
              Close
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useStore } from '../stores/main'
import type { Job } from '../stores/main'

const props = defineProps<{ job: Job }>()
const store = useStore()

const showLogs = ref(false)
const logs = ref('')
const logsLoading = ref(false)
const cancelling = ref(false)

const formatStatus = (status: string): string => {
  const map: Record<string, string> = {
    'waiting': 'Waiting',
    'running': 'Running',
    'done': 'Done',
    'failed': 'Failed',
    'cancelled': 'Cancelled'
  }
  return map[status] || status
}

const getStatusColor = (status: string): string => {
  const map: Record<string, string> = {
    'waiting': 'text-yellow-600 dark:text-yellow-400',
    'running': 'text-blue-600 dark:text-blue-400',
    'done': 'text-green-600 dark:text-green-400',
    'failed': 'text-red-600 dark:text-red-400',
    'cancelled': 'text-slate-600 dark:text-slate-400'
  }
  return map[status] || ''
}

const openLogs = async () => {
  showLogs.value = true
  await refreshLogs()
}

const refreshLogs = async () => {
  logsLoading.value = true
  try {
    logs.value = await store.getJobLogs(props.job.id)
  } finally {
    logsLoading.value = false
  }
}

const cancelJob = async () => {
  if (!confirm('Are you sure you want to cancel this job?')) return
  
  cancelling.value = true
  try {
    await store.cancelJob(props.job.id)
  } finally {
    cancelling.value = false
  }
}
</script>
