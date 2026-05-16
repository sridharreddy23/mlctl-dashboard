<template>
  <div class="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 p-6">
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-lg font-semibold text-slate-900 dark:text-white">Channel Status</h2>
      <button @click="refresh" :disabled="loading" class="px-3 py-1 text-xs font-medium bg-slate-100 dark:bg-slate-700 hover:bg-slate-200 dark:hover:bg-slate-600 text-slate-700 dark:text-slate-300 rounded transition-colors disabled:opacity-50">
        {{ loading ? 'Refreshing...' : 'Refresh' }}
      </button>
    </div>

    <div v-if="statuses.length === 0 && !loading" class="text-center py-6">
      <p class="text-slate-500 dark:text-slate-400 text-sm">No channels configured</p>
    </div>

    <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
      <div
        v-for="ch in statuses"
        :key="ch.arn"
        :class="[
          'rounded-lg border p-4 transition-colors',
          statusCardStyle(ch.status)
        ]"
      >
        <div class="flex items-center gap-2 mb-1">
          <span class="text-lg">{{ statusIcon(ch.status) }}</span>
          <p class="font-medium text-sm text-slate-900 dark:text-white truncate">{{ ch.name }}</p>
        </div>
        <p class="text-xs font-mono font-semibold" :class="statusTextColor(ch.status)">{{ ch.status }}</p>
        <p class="text-xs text-slate-500 dark:text-slate-400 mt-1 truncate">{{ ch.arn.split(':').pop() }}</p>
      </div>

      <!-- Skeleton loaders -->
      <div v-if="loading && statuses.length === 0" v-for="i in 3" :key="'skel-'+i" class="rounded-lg border border-slate-200 dark:border-slate-700 p-4 animate-pulse">
        <div class="h-4 bg-slate-200 dark:bg-slate-700 rounded w-3/4 mb-2"></div>
        <div class="h-3 bg-slate-200 dark:bg-slate-700 rounded w-1/2 mb-1"></div>
        <div class="h-3 bg-slate-200 dark:bg-slate-700 rounded w-2/3"></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useStore } from '../stores/main'

const store = useStore()
const loading = ref(false)
const statuses = ref<Array<{name: string; arn: string; status: string}>>([])

const refresh = async () => {
  loading.value = true
  try {
    const resp = await store.api.get('/channels/status')
    statuses.value = resp.data
  } catch {
    // silent — the dashboard shouldn't break if channels can't be reached
  } finally {
    loading.value = false
  }
}

const statusIcon = (status: string) => {
  if (status === 'RUNNING') return '🟢'
  if (status === 'IDLE') return '🟡'
  if (status === 'STOPPING' || status === 'STARTING') return '🔵'
  if (status === 'UNKNOWN') return '⚪'
  return '🔴'
}

const statusCardStyle = (status: string) => {
  if (status === 'RUNNING') return 'border-green-200 dark:border-green-800 bg-green-50/50 dark:bg-green-950/30'
  if (status === 'IDLE') return 'border-yellow-200 dark:border-yellow-800 bg-yellow-50/50 dark:bg-yellow-950/30'
  if (status === 'UNKNOWN') return 'border-slate-200 dark:border-slate-700 bg-slate-50/50 dark:bg-slate-800/50'
  return 'border-red-200 dark:border-red-800 bg-red-50/50 dark:bg-red-950/30'
}

const statusTextColor = (status: string) => {
  if (status === 'RUNNING') return 'text-green-700 dark:text-green-400'
  if (status === 'IDLE') return 'text-yellow-700 dark:text-yellow-400'
  if (status === 'UNKNOWN') return 'text-slate-500 dark:text-slate-400'
  return 'text-red-700 dark:text-red-400'
}

onMounted(() => {
  refresh()
})
</script>
