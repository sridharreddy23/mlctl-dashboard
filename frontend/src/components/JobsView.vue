<template>
  <div class="space-y-6">
    <!-- Tabs -->
    <div class="flex space-x-4 border-b border-slate-200 dark:border-slate-800">
      <button
        v-for="tab in jobTabs"
        :key="tab.id"
        @click="activeJobTab = tab.id"
        :class="[
          'px-4 py-2 font-medium text-sm border-b-2 transition-colors',
          activeJobTab === tab.id
            ? 'border-blue-600 text-blue-600 dark:text-blue-400'
            : 'border-transparent text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
        ]"
      >
        {{ tab.label }}
      </button>
    </div>

    <!-- Active Jobs List -->
    <div v-if="activeJobTab === 'active'" class="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 overflow-hidden">
      <div v-if="store.activeJobs.length === 0" class="p-8 text-center">
        <p class="text-slate-500 dark:text-slate-400">No active jobs</p>
      </div>
      <div v-else class="divide-y divide-slate-200 dark:divide-slate-700">
        <JobCard v-for="job in store.activeJobs" :key="job.id" :job="job" />
      </div>
    </div>

    <!-- Completed Jobs List -->
    <div v-if="activeJobTab === 'completed'" class="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 overflow-hidden">
      <div v-if="store.completedJobs.length === 0" class="p-8 text-center">
        <p class="text-slate-500 dark:text-slate-400">No completed jobs</p>
      </div>
      <div v-else class="divide-y divide-slate-200 dark:divide-slate-700">
        <JobCard v-for="job in store.completedJobs" :key="job.id" :job="job" />
      </div>
    </div>

    <!-- All Jobs List -->
    <div v-if="activeJobTab === 'all'" class="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 overflow-hidden">
      <div v-if="store.jobs.length === 0" class="p-8 text-center">
        <p class="text-slate-500 dark:text-slate-400">No jobs</p>
      </div>
      <div v-else class="divide-y divide-slate-200 dark:divide-slate-700">
        <JobCard v-for="job in store.jobs" :key="job.id" :job="job" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useStore } from '../stores/main'
import JobCard from './JobCard.vue'

const store = useStore()
const activeJobTab = ref('active')

const jobTabs = [
  { id: 'active', label: `Active (${store.activeJobs.length})` },
  { id: 'completed', label: `Completed (${store.completedJobs.length})` },
  { id: 'all', label: `All (${store.jobs.length})` }
]
</script>
