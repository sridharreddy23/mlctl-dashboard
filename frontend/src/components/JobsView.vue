<template>
  <div class="space-y-6">
    <div>
      <h2 class="page-title">Jobs</h2>
      <p class="page-subtitle">Monitor and manage scheduled restarts</p>
    </div>

    <UiCard padding="sm" class="sticky top-[4.5rem] z-10">
      <div class="flex flex-col gap-3 sm:flex-row">
        <UiInput v-model="searchQuery" placeholder="Search by name or ARN..." class="flex-1" />
        <UiSelect v-model="statusFilter" class="sm:w-44">
          <option value="">All Statuses</option>
          <option value="waiting">Waiting</option>
          <option value="running">Running</option>
          <option value="done">Done</option>
          <option value="failed">Failed</option>
          <option value="cancelled">Cancelled</option>
        </UiSelect>
        <div class="flex gap-2">
          <UiButton variant="secondary" size="sm" @click="store.exportJobsCSV()">
            <Download class="h-4 w-4" />
            Export
          </UiButton>
          <UiButton variant="secondary" size="sm" @click="showPurge = true">
            <Trash2 class="h-4 w-4" />
            Purge
          </UiButton>
        </div>
      </div>
    </UiCard>

    <UiTabs v-model="activeJobTab" :tabs="jobTabs" @update:model-value="onTabChange" />

    <UiCard v-if="activeJobTab === 'active'" padding="none" class="overflow-hidden">
      <UiEmptyState v-if="filteredActive.length === 0" :title="emptyTitle" :icon="List" />
      <div v-else class="divide-y divide-slate-200 dark:divide-slate-700">
        <JobCard v-for="job in filteredActive" :key="job.id" :job="job" @retry="onRetry" />
      </div>
    </UiCard>

    <UiCard v-if="activeJobTab === 'completed'" padding="none" class="overflow-hidden">
      <UiEmptyState v-if="filteredCompleted.length === 0" :title="emptyTitle" :icon="List" />
      <div v-else class="divide-y divide-slate-200 dark:divide-slate-700">
        <JobCard v-for="job in filteredCompleted" :key="job.id" :job="job" @retry="onRetry" />
      </div>
    </UiCard>

    <UiCard v-if="activeJobTab === 'all'" padding="none" class="overflow-hidden">
      <UiEmptyState v-if="filteredAll.length === 0" :title="emptyTitle" :icon="List" />
      <div v-else class="divide-y divide-slate-200 dark:divide-slate-700">
        <JobCard v-for="job in filteredAll" :key="job.id" :job="job" @retry="onRetry" />
      </div>
    </UiCard>

    <ConfirmModal :visible="showPurge" title="Purge Old Jobs" confirm-text="Purge" :dangerous="true" @confirm="doPurge" @cancel="showPurge = false">
      <p>Remove completed, failed, and cancelled jobs older than:</p>
      <UiSelect v-model="purgeDays" class="mt-2">
        <option :value="1">1 day</option>
        <option :value="3">3 days</option>
        <option :value="7">7 days</option>
        <option :value="30">30 days</option>
      </UiSelect>
    </ConfirmModal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Download, Trash2, List } from 'lucide-vue-next'
import { useStore } from '../stores/main'
import JobCard from './JobCard.vue'
import ConfirmModal from './ConfirmModal.vue'
import UiCard from './ui/UiCard.vue'
import UiButton from './ui/UiButton.vue'
import UiInput from './ui/UiInput.vue'
import UiSelect from './ui/UiSelect.vue'
import UiTabs from './ui/UiTabs.vue'
import UiEmptyState from './ui/UiEmptyState.vue'

const props = defineProps<{ initialTab?: string }>()

const store = useStore()
const route = useRoute()
const router = useRouter()

const validTabs = ['active', 'completed', 'all'] as const
const activeJobTab = ref(
  props.initialTab && validTabs.includes(props.initialTab as typeof validTabs[number])
    ? props.initialTab
    : 'active'
)
const searchQuery = ref('')
const statusFilter = ref('')
const showPurge = ref(false)
const purgeDays = ref('7')

watch(() => route.params.tab, (tab) => {
  if (typeof tab === 'string' && validTabs.includes(tab as typeof validTabs[number])) {
    activeJobTab.value = tab
  }
})

const onTabChange = (tab: string) => {
  router.replace(tab === 'active' ? '/jobs' : `/jobs/${tab}`)
}

const filterJobs = (jobs: typeof store.jobs) =>
  jobs.filter(j => {
    if (statusFilter.value && j.status !== statusFilter.value) return false
    if (searchQuery.value) {
      const q = searchQuery.value.toLowerCase()
      if (!j.name.toLowerCase().includes(q) && !j.arn.toLowerCase().includes(q)) return false
    }
    return true
  })

const filteredActive = computed(() => filterJobs(store.activeJobs))
const filteredCompleted = computed(() => filterJobs(store.completedJobs))
const filteredAll = computed(() => filterJobs(store.jobs))

const jobTabs = computed(() => [
  { id: 'active', label: `Active (${filteredActive.value.length})` },
  { id: 'completed', label: `Completed (${filteredCompleted.value.length})` },
  { id: 'all', label: `All (${filteredAll.value.length})` },
])

const emptyTitle = computed(() =>
  searchQuery.value || statusFilter.value ? 'No matching jobs' : 'No jobs in this view'
)

const onRetry = async (payload: { jobId?: string; name: string; arn: string; time: string }) => {
  if (payload.jobId) {
    await store.retryJob(payload.jobId)
    return
  }
  const scheduledTime = payload.time.includes('T') ? payload.time : `${payload.time}`
  await store.scheduleRestart(payload.name, payload.arn, scheduledTime, 'Asia/Kolkata')
}

const doPurge = async () => {
  showPurge.value = false
  await store.purgeJobs(parseInt(purgeDays.value, 10))
}
</script>
