<template>
  <div class="space-y-6">
    <div class="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 p-6">
      <div class="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between mb-5">
        <div>
          <h2 class="text-lg font-semibold text-slate-900 dark:text-white">AWS Credentials</h2>
          <p class="text-sm text-slate-600 dark:text-slate-400">Export temporary AWS keys for MediaLive input changes.</p>
        </div>
        <span
          :class="[
            'inline-flex w-fit px-3 py-1 rounded-full text-xs font-medium',
            store.awsCredentials?.configured
              ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
              : 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
          ]"
        >
          {{ store.awsCredentials?.configured ? 'Configured' : 'Not configured' }}
        </span>
      </div>

      <form @submit.prevent="saveAwsCredentials" class="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">Access Key</label>
          <input v-model="awsForm.access_key_id" type="text" required class="input-field" placeholder="AWS_ACCESS_KEY_ID" />
        </div>
        <div>
          <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">Secret Key</label>
          <input v-model="awsForm.secret_access_key" type="password" required class="input-field" placeholder="AWS_SECRET_ACCESS_KEY" />
        </div>
        <div>
          <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">Session Token</label>
          <input v-model="awsForm.session_token" type="password" required class="input-field" placeholder="AWS_SESSION_TOKEN" />
        </div>
        <div>
          <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">Region</label>
          <input v-model="awsForm.region" type="text" required class="input-field" placeholder="us-east-1" />
        </div>
        <div class="lg:col-span-2 flex flex-col sm:flex-row gap-3">
          <button type="submit" :disabled="store.loading" class="btn-primary">
            {{ store.loading ? 'Exporting...' : 'Export Credentials' }}
          </button>
          <button type="button" @click="showExportCommands" class="btn-secondary">
            Show Export Commands
          </button>
        </div>
      </form>

      <pre v-if="exportCommands" class="mt-4 whitespace-pre-wrap rounded-lg bg-slate-950 text-slate-100 p-4 text-xs overflow-x-auto">{{ exportCommands }}</pre>
    </div>

    <div class="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 p-6">
      <h2 class="text-lg font-semibold text-slate-900 dark:text-white mb-5">Schedule Input URL Change</h2>

      <form @submit.prevent="scheduleInputChange" class="space-y-5">
        <div>
          <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">MediaLive Channel</label>
          <select v-model="selectedChannel" required class="input-field">
            <option value="">Choose a channel...</option>
            <option v-for="channel in store.medialiveChannels" :key="channel.arn" :value="JSON.stringify(channel)">
              {{ channel.name }} ({{ channel.arn.split(':').pop() }})
            </option>
          </select>
          <input v-model="customArn" type="text" class="input-field mt-3" placeholder="Or paste a MediaLive channel ARN" />
        </div>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">Mode</label>
            <select v-model="mode" class="input-field">
              <option value="update">Update to new URL</option>
              <option value="rollback">Rollback to last URL</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">Date</label>
            <input v-model="date" type="date" required class="input-field" />
          </div>
          <div>
            <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">Time</label>
            <input v-model="time" type="time" required class="input-field" />
          </div>
        </div>

        <div v-if="mode === 'update'">
          <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">New HLS URL</label>
          <input v-model="targetUrl" type="url" required class="input-field" placeholder="https://example.com/live/playlist.m3u8" />
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">Timezone</label>
            <select v-model="timezone" class="input-field">
              <option value="UTC">UTC</option>
              <option value="Asia/Kolkata">Asia/Kolkata (IST)</option>
              <option value="America/New_York">America/New_York (EST)</option>
              <option value="America/Los_Angeles">America/Los_Angeles (PST)</option>
              <option value="Europe/London">Europe/London (GMT)</option>
              <option value="Asia/Tokyo">Asia/Tokyo (JST)</option>
            </select>
          </div>
          <label class="flex items-center gap-3 pt-7 text-sm text-slate-700 dark:text-slate-300">
            <input v-model="precheck" type="checkbox" class="h-4 w-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500" />
            Precheck HLS playlist before update
          </label>
        </div>

        <div v-if="selectedArn" class="rounded-lg bg-slate-50 dark:bg-slate-700 p-4 text-sm text-slate-700 dark:text-slate-300">
          <p><span class="font-medium">Channel ARN:</span> {{ selectedArn }}</p>
          <p v-if="date && time" class="mt-1"><span class="font-medium">Scheduled for:</span> {{ date }} {{ time }} ({{ timezone }})</p>
          <p v-if="inputDetails" class="mt-1"><span class="font-medium">Current URL:</span> {{ inputDetails.current_url || 'Unavailable' }}</p>
        </div>

        <div class="flex flex-col sm:flex-row gap-3">
          <button type="button" @click="loadInputDetails" :disabled="!selectedArn || store.loading" class="btn-secondary">
            Check Current Input
          </button>
          <button type="submit" :disabled="!canSchedule || store.loading" class="btn-primary">
            {{ store.loading ? 'Scheduling...' : 'Schedule Input Change' }}
          </button>
          <button type="button" @click="resetScheduleForm" class="btn-secondary">Clear</button>
        </div>
      </form>
    </div>

    <div class="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 overflow-hidden">
      <div class="p-6 border-b border-slate-200 dark:border-slate-700 flex items-center justify-between">
        <h2 class="text-lg font-semibold text-slate-900 dark:text-white">MediaLive Input Jobs</h2>
        <button @click="store.fetchMediaLiveJobs" class="btn-secondary">Refresh</button>
      </div>
      <div v-if="store.medialiveJobs.length === 0" class="p-8 text-center text-slate-500 dark:text-slate-400">No MediaLive input jobs</div>
      <div v-else class="divide-y divide-slate-200 dark:divide-slate-700">
        <div v-for="job in store.medialiveJobs" :key="job.id" class="p-5">
          <div class="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
            <div class="min-w-0">
              <p class="font-semibold text-slate-900 dark:text-white">{{ job.name }}</p>
              <p class="text-xs text-slate-500 dark:text-slate-400 break-all">{{ job.arn }}</p>
              <p class="text-sm text-slate-600 dark:text-slate-300 mt-2">
                {{ job.mode === 'rollback' ? 'Rollback' : 'Update' }} scheduled {{ job.time_until }}
              </p>
              <p v-if="job.target_url" class="text-xs text-slate-500 dark:text-slate-400 break-all mt-1">{{ job.target_url }}</p>
            </div>
            <div class="flex items-center gap-2">
              <span :class="statusClass(job.status)">{{ formatStatus(job.status) }}</span>
              <button @click="toggleLogs(job.id)" class="btn-secondary">Logs</button>
              <button v-if="job.status === 'waiting' || job.status === 'running'" @click="store.cancelMediaLiveJob(job.id)" class="btn-danger">Cancel</button>
            </div>
          </div>
          <pre v-if="openLogJob === job.id" class="mt-4 whitespace-pre-wrap rounded-lg bg-slate-950 text-slate-100 p-4 text-xs overflow-x-auto">{{ jobLogs }}</pre>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useStore } from '../stores/main'

const store = useStore()
const selectedChannel = ref('')
const customArn = ref('')
const mode = ref('update')
const targetUrl = ref('')
const timezone = ref('Asia/Kolkata')
const date = ref('')
const time = ref('')
const precheck = ref(true)
const exportCommands = ref('')
const inputDetails = ref<any>(null)
const openLogJob = ref('')
const jobLogs = ref('')

const awsForm = reactive({
  access_key_id: '',
  secret_access_key: '',
  session_token: '',
  region: 'us-east-1'
})

const selectedChannelObj = computed(() => {
  if (!selectedChannel.value) return null
  try {
    return JSON.parse(selectedChannel.value)
  } catch {
    return null
  }
})

const selectedArn = computed(() => customArn.value.trim() || selectedChannelObj.value?.arn || '')
const selectedName = computed(() => selectedChannelObj.value?.name || selectedArn.value.split(':').pop() || 'MediaLive Channel')
const canSchedule = computed(() => {
  if (!selectedArn.value || !date.value || !time.value) return false
  if (mode.value === 'update' && !targetUrl.value) return false
  return true
})

const credentialPayload = () => ({
  access_key_id: awsForm.access_key_id,
  secret_access_key: awsForm.secret_access_key,
  session_token: awsForm.session_token,
  region: awsForm.region
})

const saveAwsCredentials = async () => {
  await store.updateAwsCredentials(credentialPayload())
}

const showExportCommands = async () => {
  exportCommands.value = await store.getAwsExportCommands()
}

const loadInputDetails = async () => {
  inputDetails.value = await store.getMediaLiveInputDetails({
    ...credentialPayload(),
    arn: selectedArn.value
  })
}

const scheduleInputChange = async () => {
  if (!canSchedule.value) return
  await store.scheduleMediaLiveInputUrl({
    ...credentialPayload(),
    arn: selectedArn.value,
    channel_name: selectedName.value,
    mode: mode.value,
    target_url: mode.value === 'update' ? targetUrl.value : '',
    scheduled_time: `${date.value}T${time.value}:00`,
    timezone: timezone.value,
    precheck: precheck.value
  })
  resetScheduleForm()
}

const resetScheduleForm = () => {
  selectedChannel.value = ''
  customArn.value = ''
  mode.value = 'update'
  targetUrl.value = ''
  date.value = ''
  time.value = ''
  inputDetails.value = null
}

const toggleLogs = async (jobId: string) => {
  if (openLogJob.value === jobId) {
    openLogJob.value = ''
    jobLogs.value = ''
    return
  }
  openLogJob.value = jobId
  jobLogs.value = await store.getMediaLiveJobLogs(jobId)
}

const formatStatus = (status: string) => {
  const map: Record<string, string> = {
    waiting: 'Waiting',
    running: 'Running',
    done: 'Done',
    failed: 'Failed',
    cancelled: 'Cancelled'
  }
  return map[status] || status
}

const statusClass = (status: string) => {
  const base = 'px-3 py-1 rounded-full text-xs font-medium'
  if (status === 'done') return `${base} bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200`
  if (status === 'failed') return `${base} bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200`
  if (status === 'cancelled') return `${base} bg-slate-100 text-slate-800 dark:bg-slate-700 dark:text-slate-200`
  if (status === 'running') return `${base} bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200`
  return `${base} bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200`
}

onMounted(async () => {
  await Promise.all([
    store.fetchAwsCredentials(),
    store.fetchMediaLiveChannels(),
    store.fetchMediaLiveJobs()
  ])
  if (store.awsCredentials?.region) {
    awsForm.region = store.awsCredentials.region
  }
})
</script>
