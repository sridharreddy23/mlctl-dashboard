<template>
  <div class="space-y-6">
    <!-- Stats Cards -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
      <div class="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 p-6">
        <p class="text-slate-600 dark:text-slate-400 text-sm font-medium">Total Jobs</p>
        <p class="text-3xl font-bold text-slate-900 dark:text-white mt-2">{{ store.jobs.length }}</p>
      </div>

      <div class="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 p-6">
        <p class="text-slate-600 dark:text-slate-400 text-sm font-medium">Active</p>
        <p class="text-3xl font-bold text-blue-600 mt-2">{{ store.activeJobs.length }}</p>
      </div>

      <div class="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 p-6">
        <p class="text-slate-600 dark:text-slate-400 text-sm font-medium">Completed</p>
        <p class="text-3xl font-bold text-green-600 mt-2">{{ completedCount }}</p>
      </div>

      <div class="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 p-6">
        <p class="text-slate-600 dark:text-slate-400 text-sm font-medium">Failed</p>
        <p class="text-3xl font-bold text-red-600 mt-2">{{ failedCount }}</p>
      </div>
    </div>

    <!-- Active Jobs -->
    <div class="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 p-6">
      <h2 class="text-lg font-semibold text-slate-900 dark:text-white mb-4">Active Jobs</h2>
      <div v-if="store.activeJobs.length === 0" class="text-center py-8">
        <p class="text-slate-500 dark:text-slate-400">No active jobs</p>
      </div>
      <div v-else class="space-y-3">
        <div v-for="job in store.activeJobs" :key="job.id" class="flex items-center justify-between p-4 bg-slate-50 dark:bg-slate-700 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-600 transition-colors">
          <div class="flex-1 min-w-0">
            <p class="font-medium text-slate-900 dark:text-white truncate">{{ job.name }}</p>
            <p class="text-xs text-slate-500 dark:text-slate-400 truncate">{{ job.arn }}</p>
          </div>
          <div class="flex items-center space-x-4 ml-4">
            <div class="text-right">
              <p class="text-sm font-medium" :class="getStatusColor(job.status)">{{ formatStatus(job.status) }}</p>
              <p class="text-xs text-slate-500 dark:text-slate-400">{{ job.time_until }}</p>
            </div>
            <div class="flex items-center space-x-2">
              <div v-if="job.status === 'waiting'" class="animate-pulse-soft w-2 h-2 bg-yellow-500 rounded-full"></div>
              <div v-else-if="job.status === 'running'" class="animate-spin-slow w-2 h-2 bg-blue-500 rounded-full"></div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Recent Completed Jobs -->
    <div class="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 p-6">
      <h2 class="text-lg font-semibold text-slate-900 dark:text-white mb-4">Recent Activity</h2>
      <div v-if="recentJobs.length === 0" class="text-center py-8">
        <p class="text-slate-500 dark:text-slate-400">No completed jobs yet</p>
      </div>
      <div v-else class="space-y-2">
        <div v-for="job in recentJobs" :key="job.id" class="flex items-center justify-between p-3 border-b border-slate-200 dark:border-slate-700 last:border-b-0">
          <div class="flex-1">
            <p class="font-medium text-sm text-slate-900 dark:text-white">{{ job.name }}</p>
            <p class="text-xs text-slate-500 dark:text-slate-400">{{ job.time_until }}</p>
          </div>
          <span :class="['px-3 py-1 rounded-full text-xs font-medium', getStatusBgColor(job.status)]">
            {{ formatStatus(job.status) }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useStore } from '../stores/main'

const store = useStore()

const completedCount = computed(() => {
  return store.jobs.filter(j => j.status === 'done').length
})

const failedCount = computed(() => {
  return store.jobs.filter(j => j.status === 'failed').length
})

const recentJobs = computed(() => {
  return store.completedJobs.slice(0, 5)
})

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

const getStatusBgColor = (status: string): string => {
  const map: Record<string, string> = {
    'done': 'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200',
    'failed': 'bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200',
    'cancelled': 'bg-slate-100 dark:bg-slate-700 text-slate-800 dark:text-slate-200',
    'waiting': 'bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200',
    'running': 'bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200'
  }
  return map[status] || ''
}
</script>
