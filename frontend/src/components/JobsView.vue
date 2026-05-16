<template>
  <div class="space-y-6">
    <!-- Search & Filter Bar -->
    <div class="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 p-4">
      <div class="flex flex-col sm:flex-row gap-3">
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Search by name or ARN..."
          class="flex-1 px-4 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white placeholder-slate-400 focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
        />
        <select v-model="statusFilter" class="px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white text-sm">
          <option value="">All Statuses</option>
          <option value="waiting">Waiting</option>
          <option value="running">Running</option>
          <option value="done">Done</option>
          <option value="failed">Failed</option>
          <option value="cancelled">Cancelled</option>
        </select>
        <div class="flex gap-2">
          <button @click="store.exportJobsCSV()" class="btn-secondary text-sm whitespace-nowrap">📥 Export CSV</button>
          <button @click="showPurge = true" class="btn-secondary text-sm whitespace-nowrap">🗑️ Purge Old</button>
        </div>
      </div>
    </div>

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
      >{{ tab.label }}</button>
    </div>

    <!-- Active -->
    <div v-if="activeJobTab === 'active'" class="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 overflow-hidden">
      <div v-if="filteredActive.length === 0" class="p-8 text-center">
        <p class="text-slate-500 dark:text-slate-400">{{ searchQuery || statusFilter ? 'No matching jobs' : 'No active jobs' }}</p>
      </div>
      <div v-else class="divide-y divide-slate-200 dark:divide-slate-700">
        <JobCard v-for="job in filteredActive" :key="job.id" :job="job" @retry="$emit('retry', $event)" />
      </div>
    </div>

    <!-- Completed -->
    <div v-if="activeJobTab === 'completed'" class="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 overflow-hidden">
      <div v-if="filteredCompleted.length === 0" class="p-8 text-center">
        <p class="text-slate-500 dark:text-slate-400">{{ searchQuery || statusFilter ? 'No matching jobs' : 'No completed jobs' }}</p>
      </div>
      <div v-else class="divide-y divide-slate-200 dark:divide-slate-700">
        <JobCard v-for="job in filteredCompleted" :key="job.id" :job="job" @retry="$emit('retry', $event)" />
      </div>
    </div>

    <!-- All -->
    <div v-if="activeJobTab === 'all'" class="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 overflow-hidden">
      <div v-if="filteredAll.length === 0" class="p-8 text-center">
        <p class="text-slate-500 dark:text-slate-400">{{ searchQuery || statusFilter ? 'No matching jobs' : 'No jobs' }}</p>
      </div>
      <div v-else class="divide-y divide-slate-200 dark:divide-slate-700">
        <JobCard v-for="job in filteredAll" :key="job.id" :job="job" @retry="$emit('retry', $event)" />
      </div>
    </div>

    <!-- Purge Modal -->
    <ConfirmModal
      :visible="showPurge"
      title="Purge Old Jobs"
      confirm-text="Purge"
      :dangerous="true"
      @confirm="doPurge"
      @cancel="showPurge = false"
    >
      <p>Remove completed, failed, and cancelled jobs older than:</p>
      <select v-model="purgeDays" class="mt-2 px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white text-sm w-full">
        <option :value="1">1 day</option>
        <option :value="3">3 days</option>
        <option :value="7">7 days</option>
        <option :value="30">30 days</option>
      </select>
    </ConfirmModal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useStore } from '../stores/main'
import JobCard from './JobCard.vue'
import ConfirmModal from './ConfirmModal.vue'

const store = useStore()
const activeJobTab = ref('active')
const searchQuery = ref('')
const statusFilter = ref('')
const showPurge = ref(false)
const purgeDays = ref(7)

defineEmits(['retry'])

const filterJobs = (jobs: typeof store.jobs) => {
  return jobs.filter(j => {
    if (statusFilter.value && j.status !== statusFilter.value) return false
    if (searchQuery.value) {
      const q = searchQuery.value.toLowerCase()
      if (!j.name.toLowerCase().includes(q) && !j.arn.toLowerCase().includes(q)) return false
    }
    return true
  })
}

const filteredActive = computed(() => filterJobs(store.activeJobs))
const filteredCompleted = computed(() => filterJobs(store.completedJobs))
const filteredAll = computed(() => filterJobs(store.jobs))

const jobTabs = computed(() => [
  { id: 'active', label: `Active (${filteredActive.value.length})` },
  { id: 'completed', label: `Completed (${filteredCompleted.value.length})` },
  { id: 'all', label: `All (${filteredAll.value.length})` }
])

const doPurge = async () => {
  showPurge.value = false
  await store.purgeJobs(purgeDays.value)
}
</script>
