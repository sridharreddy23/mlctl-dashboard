<template>
  <div class="space-y-6">
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

    <!-- Channel Status Grid -->
    <ChannelStatusGrid />

    <!-- Job Timeline -->
    <JobTimeline />

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
            <div v-if="job.status === 'waiting'" class="animate-pulse-soft w-2 h-2 bg-yellow-500 rounded-full"></div>
            <div v-else-if="job.status === 'running'" class="animate-spin-slow w-2 h-2 bg-blue-500 rounded-full"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- Recent Activity -->
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
          <span :class="['px-3 py-1 rounded-full text-xs font-medium', getStatusBgColor(job.status)]">{{ formatStatus(job.status) }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useStore } from '../stores/main'
import { formatStatus, getStatusColor, getStatusBgColor } from '../utils/status'
import ChannelStatusGrid from './ChannelStatusGrid.vue'
import JobTimeline from './JobTimeline.vue'

const store = useStore()
const completedCount = computed(() => store.jobs.filter(j => j.status === 'done').length)
const failedCount = computed(() => store.jobs.filter(j => j.status === 'failed').length)
const recentJobs = computed(() => store.completedJobs.slice(0, 5))
</script>
