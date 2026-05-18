<template>
  <div class="space-y-6">
    <div>
      <h2 class="page-title">MediaLive Inputs</h2>
      <p class="page-subtitle">AWS credentials and scheduled input URL changes</p>
    </div>

    <!-- AWS Credentials -->
    <UiCard>
      <template #header>
        <div>
          <h2 class="text-lg font-semibold text-slate-900 dark:text-white">AWS Credentials</h2>
          <p class="mt-1 text-sm text-slate-600 dark:text-slate-400">Export temporary AWS keys for MediaLive input changes.</p>
        </div>
      </template>
      <template #actions>
        <div class="flex items-center gap-2">
          <span v-if="tokenExpiryWarning" class="badge bg-warning-100 text-warning-800 dark:bg-warning-900 dark:text-warning-200">
            ⚠️ {{ tokenExpiryWarning }}
          </span>
          <UiBadge
            :label="store.awsCredentials?.configured ? 'Configured' : 'Not configured'"
            :variant="store.awsCredentials?.configured ? 'primary' : 'neutral'"
          />
        </div>
      </template>

      <!-- Paste Helper (collapsible) -->
      <div class="mb-4">
        <button
          type="button"
          class="flex w-full items-center justify-between rounded-lg border border-slate-200 px-4 py-2.5 text-sm text-slate-600 transition-colors hover:bg-slate-50 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-700/50"
          @click="showPasteHelper = !showPasteHelper"
        >
          <span class="font-medium">Import credentials (JSON / export commands)</span>
          <ChevronDown class="h-4 w-4 transition-transform duration-200" :class="{ 'rotate-180': showPasteHelper }" />
        </button>
        <div v-if="showPasteHelper" class="mt-2">
          <textarea
            v-model="pasteInput"
            @input="parsePastedCredentials"
            rows="3"
            class="input-field font-mono text-xs"
            placeholder='{"AccessKeyId": "...", "SecretAccessKey": "...", "SessionToken": "..."}'
          ></textarea>
          <p v-if="pasteStatus" class="mt-1 text-xs" :class="pasteStatus === 'Parsed!' ? 'text-success-600' : 'text-slate-500'">{{ pasteStatus }}</p>
        </div>
      </div>

      <form @submit.prevent="saveAwsCredentials" class="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <UiInput v-model="awsForm.access_key_id" label="Access Key" placeholder="AWS_ACCESS_KEY_ID" required />
        <UiInput v-model="awsForm.secret_access_key" label="Secret Key" type="password" placeholder="AWS_SECRET_ACCESS_KEY" required />
        <UiInput v-model="awsForm.session_token" label="Session Token" type="password" placeholder="AWS_SESSION_TOKEN" required />
        <UiInput v-model="awsForm.region" label="Region" placeholder="us-east-1" required />
        <div class="flex flex-col gap-3 sm:flex-row lg:col-span-2">
          <UiButton type="submit" variant="primary" :loading="store.loading">Export Credentials</UiButton>
          <UiButton type="button" variant="secondary" @click="showExportCommands">Show Export Commands</UiButton>
        </div>
      </form>
      <pre v-if="exportCommands" class="mt-4 overflow-x-auto whitespace-pre-wrap rounded-lg bg-slate-950 p-4 text-xs text-slate-100">{{ exportCommands }}</pre>
    </UiCard>

    <!-- Schedule Input URL Change -->
    <UiCard title="Schedule Input URL Change">
      <form @submit.prevent="requestConfirmation" class="space-y-5">
        <div>
          <UiSelect v-model="selectedChannelArn" label="MediaLive Channel" required>
            <option value="">Choose a channel...</option>
            <option v-for="channel in store.medialiveChannels" :key="channel.arn" :value="channel.arn">
              {{ channel.name }} ({{ channel.arn.split(':').pop() }})
            </option>
          </UiSelect>
          <UiInput v-model="customArn" placeholder="Or paste a MediaLive channel ARN" wrapper-class="mt-3" />
        </div>

        <!-- Input details display -->
        <div v-if="inputDetails" class="rounded-lg border border-primary-200 bg-primary-50 p-4 dark:border-primary-800 dark:bg-primary-950/50">
          <p class="text-sm font-medium text-primary-900 dark:text-primary-200">Current Input Details</p>
          <div class="mt-2 space-y-1 font-mono text-xs text-primary-700 dark:text-primary-300">
            <p>Channel ID: {{ inputDetails.channel_id }}</p>
            <p>Input ID: {{ inputDetails.input_id }}</p>
            <p>State: {{ inputDetails.state }}</p>
            <p>Current URL: {{ inputDetails.current_url }}</p>
          </div>
        </div>

        <div class="grid grid-cols-1 gap-4 md:grid-cols-3">
          <UiSelect v-model="mode" label="Mode">
            <option value="update">Update to new URL</option>
            <option value="rollback">Rollback to last URL</option>
          </UiSelect>
          <UiInput v-model="date" label="Date" type="date" required />
          <UiInput v-model="time" label="Time" type="time" required />
        </div>

        <UiInput v-if="mode === 'update'" v-model="targetUrl" label="New HLS URL" type="url" placeholder="https://example.com/live/playlist.m3u8" required />

        <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
          <UiSelect v-model="timezone" label="Timezone">
            <option v-for="tz in tzOptions" :key="tz" :value="tz">{{ tz }}</option>
          </UiSelect>
          <label class="flex items-center gap-3 pt-7 text-sm text-slate-700 dark:text-slate-300">
            <input v-model="precheck" type="checkbox" class="h-4 w-4 rounded border-slate-300 text-primary-600 focus:ring-primary-500" />
            Precheck HLS playlist before update
          </label>
        </div>

        <!-- Token expiry scheduling warning -->
        <div v-if="schedulePastTokenExpiry" class="rounded-lg border border-warning-200 bg-warning-50 p-4 text-sm text-warning-800 dark:border-warning-800 dark:bg-warning-950 dark:text-warning-200">
          ⚠️ <strong>Warning:</strong> The scheduled time is past the estimated AWS session token expiry. The job may fail due to expired credentials.
        </div>

        <div class="flex flex-col gap-3 sm:flex-row">
          <UiButton type="button" variant="secondary" :disabled="!selectedArn || store.loading" @click="loadInputDetails">Check Current Input</UiButton>
          <UiButton type="submit" variant="primary" :disabled="!canSchedule || store.loading" :loading="store.loading">Schedule Input Change</UiButton>
          <UiButton type="button" variant="secondary" @click="resetScheduleForm">Clear</UiButton>
        </div>
      </form>
    </UiCard>

    <!-- MediaLive Input Jobs -->
    <UiCard padding="none">
      <template #header>
        <h2 class="text-lg font-semibold text-slate-900 dark:text-white">MediaLive Input Jobs</h2>
      </template>
      <template #actions>
        <UiButton variant="secondary" size="sm" @click="store.fetchMediaLiveJobs">Refresh</UiButton>
      </template>

      <UiEmptyState v-if="store.medialiveJobs.length === 0" icon="list" message="No MediaLive input jobs" class="py-8" />

      <div v-else class="divide-y divide-slate-200 dark:divide-slate-700">
        <div
          v-for="job in store.medialiveJobs"
          :key="job.id"
          :class="['border-l-4 p-5', mlJobBorderClass(job.status)]"
        >
          <div class="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
            <div class="min-w-0">
              <p class="font-semibold text-slate-900 dark:text-white">{{ job.name }}</p>
              <p class="break-all text-xs text-slate-500 dark:text-slate-400">{{ job.arn }}</p>
              <p class="mt-2 text-sm text-slate-600 dark:text-slate-300">{{ job.mode === 'rollback' ? 'Rollback' : 'Update' }} scheduled {{ job.time_until }}</p>
              <p v-if="job.target_url" class="mt-1 break-all text-xs text-slate-500 dark:text-slate-400">{{ job.target_url }}</p>
            </div>
            <div class="flex items-center gap-2">
              <UiBadge :status="job.status" />
              <UiButton variant="secondary" size="sm" @click="toggleLogs(job.id)">Logs</UiButton>
              <UiButton
                v-if="job.status === 'waiting' || job.status === 'running'"
                variant="danger"
                size="sm"
                @click="store.cancelMediaLiveJob(job.id)"
              >Cancel</UiButton>
            </div>
          </div>
          <pre v-if="openLogJob === job.id" class="mt-4 overflow-x-auto whitespace-pre-wrap rounded-lg bg-slate-950 p-4 text-xs text-slate-100">{{ jobLogs }}</pre>
        </div>
      </div>
    </UiCard>

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
import { detectTimezone, timezoneOptions } from '../utils/timezone'
import { ChevronDown } from 'lucide-vue-next'
import ConfirmModal from './ConfirmModal.vue'
import UiCard from './ui/UiCard.vue'
import UiButton from './ui/UiButton.vue'
import UiInput from './ui/UiInput.vue'
import UiSelect from './ui/UiSelect.vue'
import UiBadge from './ui/UiBadge.vue'
import UiEmptyState from './ui/UiEmptyState.vue'

const store = useStore()
const selectedChannelArn = ref('')
const customArn = ref('')
const mode = ref('update')
const targetUrl = ref('')
const detectedTz = detectTimezone()
const timezone = ref(detectedTz)
const tzOptions = timezoneOptions(detectedTz)
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

// Collapse paste area when credentials are already configured; expand when not
const showPasteHelper = ref(!store.awsCredentials?.configured)

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

// Status left border for ML jobs
const mlJobBorderClass = (status: string) => {
  const map: Record<string, string> = {
    waiting: 'border-l-warning-400',
    running: 'border-l-primary-500',
    done: 'border-l-success-500',
    failed: 'border-l-danger-500',
    cancelled: 'border-l-slate-300 dark:border-l-slate-600',
  }
  return map[status] ?? 'border-l-slate-200 dark:border-l-slate-700'
}

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
