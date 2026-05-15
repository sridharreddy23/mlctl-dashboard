<template>
  <div class="space-y-6">
    <div class="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 p-8">
      <h2 class="text-2xl font-bold text-slate-900 dark:text-white mb-6">Schedule Channel Restart</h2>

      <form @submit.prevent="handleSubmit" class="space-y-6">
        <!-- Channel Selection -->
        <div>
          <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-3">Select Channel</label>
          <select v-model="selectedChannel" required class="w-full px-4 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent">
            <option value="">Choose a channel...</option>
            <option v-for="ch in store.channels" :key="ch.arn" :value="JSON.stringify(ch)">
              {{ ch.name }} ({{ ch.arn.split(':').pop() }})
            </option>
          </select>
          <p v-if="selectedChannelObj" class="mt-2 text-xs text-slate-500 dark:text-slate-400">
            ARN: {{ selectedChannelObj.arn }}
          </p>
        </div>

        <!-- Timezone Selection -->
        <div>
          <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-3">Timezone</label>
          <select v-model="timezone" class="w-full px-4 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent">
            <option value="UTC">UTC</option>
            <option value="Asia/Kolkata">Asia/Kolkata (IST)</option>
            <option value="America/New_York">America/New_York (EST)</option>
            <option value="America/Los_Angeles">America/Los_Angeles (PST)</option>
            <option value="Europe/London">Europe/London (GMT)</option>
            <option value="Asia/Tokyo">Asia/Tokyo (JST)</option>
          </select>
        </div>

        <!-- Date & Time Selection -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-3">Date</label>
            <input v-model="date" type="date" required class="w-full px-4 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent" />
          </div>
          <div>
            <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-3">Time</label>
            <input v-model="time" type="time" required class="w-full px-4 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent" />
          </div>
        </div>

        <!-- Scheduled Time Display -->
        <div v-if="date && time" class="bg-blue-50 dark:bg-blue-950 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
          <p class="text-sm text-blue-900 dark:text-blue-200">
            <span class="font-medium">Scheduled for:</span> {{ formatScheduledTime() }}
          </p>
        </div>

        <!-- Submit Button -->
        <div class="flex space-x-4">
          <button
            type="submit"
            :disabled="store.loading || !selectedChannel || !date || !time"
            class="flex-1 px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-400 text-white font-semibold rounded-lg transition-colors flex items-center justify-center space-x-2"
          >
            <span v-if="!store.loading">Schedule Restart</span>
            <span v-else class="flex items-center space-x-2">
              <span class="animate-spin-slow w-4 h-4 border-2 border-white border-t-transparent rounded-full"></span>
              <span>Scheduling...</span>
            </span>
          </button>
          <button
            type="button"
            @click="resetForm"
            class="px-6 py-3 bg-slate-200 dark:bg-slate-700 hover:bg-slate-300 dark:hover:bg-slate-600 text-slate-900 dark:text-white font-semibold rounded-lg transition-colors"
          >
            Clear
          </button>
        </div>
      </form>
    </div>

    <!-- Recent Scheduled -->
    <div v-if="recentScheduled.length > 0" class="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 p-6">
      <h3 class="text-lg font-semibold text-slate-900 dark:text-white mb-4">Recent Schedules</h3>
      <div class="space-y-3">
        <div v-for="job in recentScheduled" :key="job.id" class="flex items-center justify-between p-4 bg-slate-50 dark:bg-slate-700 rounded-lg">
          <div>
            <p class="font-medium text-slate-900 dark:text-white">{{ job.name }}</p>
            <p class="text-xs text-slate-500 dark:text-slate-400">{{ formatJobTime(job.time) }}</p>
          </div>
          <span :class="['px-3 py-1 rounded-full text-xs font-medium', job.status === 'done' ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' : 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200']">
            {{ formatStatus(job.status) }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useStore } from '../stores/main'

const store = useStore()
const selectedChannel = ref('')
const timezone = ref('Asia/Kolkata')
const date = ref('')
const time = ref('')

const selectedChannelObj = computed(() => {
  if (!selectedChannel.value) return null
  try {
    return JSON.parse(selectedChannel.value)
  } catch {
    return null
  }
})

const recentScheduled = computed(() => {
  return store.jobs.filter(j => j.status === 'waiting' || j.status === 'running').slice(0, 3)
})

const formatScheduledTime = () => {
  if (!date.value || !time.value) return ''
  const dateStr = new Date(date.value).toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })
  return `${dateStr} at ${time.value} (${timezone.value})`
}

const formatJobTime = (isoTime: string) => {
  try {
    const dt = new Date(isoTime)
    return dt.toLocaleString()
  } catch {
    return isoTime
  }
}

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

const resetForm = () => {
  selectedChannel.value = ''
  timezone.value = 'Asia/Kolkata'
  date.value = ''
  time.value = ''
}

const handleSubmit = async () => {
  if (!selectedChannelObj.value || !date.value || !time.value) return

  const scheduledTime = `${date.value}T${time.value}:00`

  try {
    await store.scheduleRestart(
      selectedChannelObj.value.name,
      selectedChannelObj.value.arn,
      scheduledTime,
      timezone.value
    )
    resetForm()
    emit('scheduled')
  } catch (err) {
    console.error('Failed to schedule:', err)
  }
}

const emit = defineEmits(['scheduled'])

onMounted(() => {
  store.fetchChannels()
})
</script>
