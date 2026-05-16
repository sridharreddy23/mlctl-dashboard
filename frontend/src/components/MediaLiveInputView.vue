<template>
  <div class="space-y-6">
    <!-- AWS Credentials -->
    <div class="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 p-6">
      <div class="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between mb-5">
        <div>
          <h2 class="text-lg font-semibold text-slate-900 dark:text-white">AWS Credentials</h2>
          <p class="text-sm text-slate-600 dark:text-slate-400">Export temporary AWS keys for MediaLive input changes.</p>
        </div>
        <div class="flex items-center gap-2">
          <!-- Token expiry warning -->
          <span v-if="tokenExpiryWarning" class="inline-flex px-3 py-1 rounded-full text-xs font-medium bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200">
            ⚠️ {{ tokenExpiryWarning }}
          </span>
          <span :class="['inline-flex px-3 py-1 rounded-full text-xs font-medium', store.awsCredentials?.configured ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' : 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200']">
            {{ store.awsCredentials?.configured ? 'Configured' : 'Not configured' }}
          </span>
        </div>
      </div>

      <!-- Paste Helper -->
      <div class="mb-4">
        <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">Quick Paste (JSON, CLI, or Export commands)</label>
        <textarea
          v-model="pasteInput"
          @input="parsePastedCredentials"
          rows="3"
          class="input-field font-mono text-xs"
          placeholder='Paste AWS JSON, aws configure output, or export commands...\n{"AccessKeyId": "...", "SecretAccessKey": "...", "SessionToken": "..."}'
        ></textarea>
        <p v-if="pasteStatus" class="mt-1 text-xs" :class="pasteStatus === 'Parsed!' ? 'text-green-600' : 'text-slate-500'">{{ pasteStatus }}</p>
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
          <button type="submit" :disabled="store.loading" class="btn-primary">{{ store.loading ? 'Exporting...' : 'Export Credentials' }}</button>
          <button type="button" @click="showExportCommands" class="btn-secondary">Show Export Commands</button>
        </div>
      </form>
      <pre v-if="exportCommands" class="mt-4 whitespace-pre-wrap rounded-lg bg-slate-950 text-slate-100 p-4 text-xs overflow-x-auto">{{ exportCommands }}</pre>
    </div>

    <!-- Schedule Input URL Change -->
    <div class="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 p-6">
      <h2 class="text-lg font-semibold text-slate-900 dark:text-white mb-5">Schedule Input URL Change</h2>
      <form @submit.prevent="requestConfirmation" class="space-y-5">
        <div>
          <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">MediaLive Channel</label>
          <select v-model="selectedChannelArn" required class="input-field">
            <option value="">Choose a channel...</option>
            <option v-for="channel in store.medialiveChannels" :key="channel.arn" :value="channel.arn">{{ channel.name }} ({{ channel.arn.split(':').pop() }})</option>
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

        <!-- Token expiry scheduling warning -->
        <div v-if="schedulePastTokenExpiry" class="bg-orange-50 dark:bg-orange-950 border border-orange-200 dark:border-orange-800 rounded-lg p-4 text-sm text-orange-800 dark:text-orange-200">
          ⚠️ <strong>Warning:</strong> The scheduled time is past the estimated AWS session token expiry. The job may fail due to expired credentials.
        </div>

        <div class="flex flex-col sm:flex-row gap-3">
          <button type="button" @click="loadInputDetails" :disabled="!selectedArn || store.loading" class="btn-secondary">Check Current Input</button>
          <button type="submit" :disabled="!canSchedule || store.loading" class="btn-primary">{{ store.loading ? 'Scheduling...' : 'Schedule Input Change' }}</button>
          <button type="button" @click="resetScheduleForm" class="btn-secondary">Clear</button>
        </div>
      </form>
    </div>

    <!-- MediaLive Input Jobs -->
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
              <p class="text-sm text-slate-600 dark:text-slate-300 mt-2">{{ job.mode === 'rollback' ? 'Rollback' : 'Update' }} scheduled {{ job.time_until }}</p>
              <p v-if="job.target_url" class="text-xs text-slate-500 dark:text-slate-400 break-all mt-1">{{ job.target_url }}</p>
            </div>
            <div class="flex items-center gap-2">
              <span :class="statusBadgeClass(job.status)">{{ formatStatus(job.status) }}</span>
              <button @click="toggleLogs(job.id)" class="btn-secondary">Logs</button>
              <button v-if="job.status === 'waiting' || job.status === 'running'" @click="store.cancelMediaLiveJob(job.id)" class="btn-danger">Cancel</button>
            </div>
          </div>
          <pre v-if="openLogJob === job.id" class="mt-4 whitespace-pre-wrap rounded-lg bg-slate-950 text-slate-100 p-4 text-xs overflow-x-auto">{{ jobLogs }}</pre>
        </div>
      </div>
    </div>

    <!-- Confirmation Modal -->
    <ConfirmModal
      :visible="showConfirm"
      title="Confirm Input URL Change"
      confirm-text="Schedule"
      @confirm="scheduleInputChange"
      @cancel="showConfirm = false"
    >
      <p><strong>Channel:</strong> {{ selectedName }}</p>
      <p><strong>Mode:</strong> {{ mode === 'rollback' ? 'Rollback' : 'Update' }}</p>
      <p v-if="mode === 'update'"><strong>Target URL:</strong> {{ targetUrl }}</p>
      <p><strong>Scheduled:</strong> {{ date }} {{ time }} ({{ timezone }})</p>
    </ConfirmModal>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useStore } from '../stores/main'
import { formatStatus, statusBadgeClass } from '../utils/status'
import ConfirmModal from './ConfirmModal.vue'

const store = useStore()
const selectedChannelArn = ref('')
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
const showConfirm = ref(false)
const pasteInput = ref('')
const pasteStatus = ref('')

const awsForm = reactive({ access_key_id: '', secret_access_key: '', session_token: '', region: 'us-east-1' })

const selectedChannelObj = computed(() => {
  if (!selectedChannelArn.value) return null
  return store.medialiveChannels.find(ch => ch.arn === selectedChannelArn.value) || null
})
const selectedArn = computed(() => customArn.value.trim() || selectedChannelObj.value?.arn || '')
const selectedName = computed(() => selectedChannelObj.value?.name || selectedArn.value.split(':').pop() || 'MediaLive Channel')
const canSchedule = computed(() => {
  if (!selectedArn.value || !date.value || !time.value) return false
  if (mode.value === 'update' && !targetUrl.value) return false
  return true
})

// Token expiry warning
const TOKEN_TTL_MS = 3600 * 1000 // 1 hour default
const tokenExpiryWarning = computed(() => {
  const exportedAt = store.awsCredentials?.exported_at
  if (!exportedAt) return ''
  const expiresAt = new Date(exportedAt).getTime() + TOKEN_TTL_MS
  const remaining = expiresAt - Date.now()
  if (remaining <= 0) return 'Token likely expired'
  const mins = Math.floor(remaining / 60000)
  if (mins < 15) return `Expires in ${mins}m`
  return ''
})

const schedulePastTokenExpiry = computed(() => {
  if (!store.awsCredentials?.exported_at || !date.value || !time.value) return false
  const expiresAt = new Date(store.awsCredentials.exported_at).getTime() + TOKEN_TTL_MS
  const scheduledAt = new Date(`${date.value}T${time.value}:00`).getTime()
  return scheduledAt > expiresAt
})

// Credential paste parser
const parsePastedCredentials = () => {
  const text = pasteInput.value.trim()
  if (!text) { pasteStatus.value = ''; return }

  // Try JSON format: {"AccessKeyId": "...", ...} or {"Credentials": {"AccessKeyId": ...}}
  try {
    let obj = JSON.parse(text)
    if (obj.Credentials) obj = obj.Credentials
    if (obj.AccessKeyId || obj.access_key_id) {
      awsForm.access_key_id = obj.AccessKeyId || obj.access_key_id || ''
      awsForm.secret_access_key = obj.SecretAccessKey || obj.secret_access_key || ''
      awsForm.session_token = obj.SessionToken || obj.session_token || ''
      if (obj.Region || obj.region) awsForm.region = obj.Region || obj.region
      pasteStatus.value = 'Parsed!'
      return
    }
  } catch { /* not JSON */ }

  // Try export commands or key=value lines
  const keyMap: Record<string, keyof typeof awsForm> = {
    'aws_access_key_id': 'access_key_id',
    'aws_secret_access_key': 'secret_access_key',
    'aws_session_token': 'session_token',
    'aws_region': 'region',
    'aws_default_region': 'region',
  }
  let matched = 0
  for (const line of text.split('\n')) {
    const cleaned = line.replace(/^export\s+/i, '').trim()
    const eqIdx = cleaned.indexOf('=')
    if (eqIdx === -1) continue
    const key = cleaned.slice(0, eqIdx).toLowerCase().trim()
    let val = cleaned.slice(eqIdx + 1).trim().replace(/^['"]|['"]$/g, '')
    const formKey = keyMap[key]
    if (formKey) { (awsForm as any)[formKey] = val; matched++ }
  }
  pasteStatus.value = matched > 0 ? 'Parsed!' : 'Could not parse — try JSON or export format'
}

const credentialPayload = () => ({ access_key_id: awsForm.access_key_id, secret_access_key: awsForm.secret_access_key, session_token: awsForm.session_token, region: awsForm.region })

const saveAwsCredentials = async () => { await store.updateAwsCredentials(credentialPayload()) }
const showExportCommands = async () => { exportCommands.value = await store.getAwsExportCommands() }
const loadInputDetails = async () => { inputDetails.value = await store.getMediaLiveInputDetails({ ...credentialPayload(), arn: selectedArn.value }) }

const requestConfirmation = () => {
  if (!canSchedule.value) return
  showConfirm.value = true
}

const scheduleInputChange = async () => {
  showConfirm.value = false
  await store.scheduleMediaLiveInputUrl({
    ...credentialPayload(), arn: selectedArn.value, channel_name: selectedName.value,
    mode: mode.value, target_url: mode.value === 'update' ? targetUrl.value : '',
    scheduled_time: `${date.value}T${time.value}:00`, timezone: timezone.value, precheck: precheck.value
  })
  resetScheduleForm()
}

const resetScheduleForm = () => {
  selectedChannelArn.value = ''; customArn.value = ''; mode.value = 'update'
  targetUrl.value = ''; date.value = ''; time.value = ''; inputDetails.value = null
}

const toggleLogs = async (jobId: string) => {
  if (openLogJob.value === jobId) { openLogJob.value = ''; jobLogs.value = ''; return }
  openLogJob.value = jobId
  jobLogs.value = await store.getMediaLiveJobLogs(jobId)
}

onMounted(async () => {
  await Promise.all([store.fetchAwsCredentials(), store.fetchMediaLiveChannels(), store.fetchMediaLiveJobs()])
  if (store.awsCredentials?.region) awsForm.region = store.awsCredentials.region
})
</script>
