<template>
  <div class="space-y-6">
    <div class="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 p-8">
      <h2 class="text-2xl font-bold text-slate-900 dark:text-white mb-6">Schedule Channel Restart</h2>
      <form @submit.prevent="requestConfirmation" class="space-y-6">
        <!-- Channel Selection (multi-select for bulk) -->
        <div>
          <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-3">Select Channels</label>
          <div class="space-y-2 max-h-48 overflow-y-auto border border-slate-200 dark:border-slate-700 rounded-lg p-3">
            <label v-for="ch in store.channels" :key="ch.arn" class="flex items-center gap-3 p-2 rounded hover:bg-slate-50 dark:hover:bg-slate-700 cursor-pointer">
              <input type="checkbox" :value="ch.arn" v-model="selectedArns" class="h-4 w-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500" />
              <div class="min-w-0">
                <p class="text-sm font-medium text-slate-900 dark:text-white truncate">{{ ch.name }}</p>
                <p class="text-xs text-slate-500 dark:text-slate-400 truncate">{{ ch.arn.split(':').pop() }}</p>
              </div>
            </label>
          </div>
          <p class="mt-2 text-xs text-slate-500 dark:text-slate-400">{{ selectedArns.length }} channel(s) selected</p>
        </div>

        <!-- Timezone -->
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

        <!-- Date & Time -->
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

        <div v-if="date && time" class="bg-blue-50 dark:bg-blue-950 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
          <p class="text-sm text-blue-900 dark:text-blue-200"><span class="font-medium">Scheduled for:</span> {{ formatScheduledTime() }}</p>
        </div>

        <div class="flex space-x-4">
          <button type="submit" :disabled="store.loading || selectedArns.length === 0 || !date || !time" class="flex-1 px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-400 text-white font-semibold rounded-lg transition-colors">
            {{ selectedArns.length > 1 ? `Schedule ${selectedArns.length} Restarts` : 'Schedule Restart' }}
          </button>
          <button type="button" @click="resetForm" class="px-6 py-3 bg-slate-200 dark:bg-slate-700 hover:bg-slate-300 dark:hover:bg-slate-600 text-slate-900 dark:text-white font-semibold rounded-lg transition-colors">Clear</button>
        </div>
      </form>
    </div>

    <!-- Confirmation Modal -->
    <ConfirmModal
      :visible="showConfirm"
      title="Confirm Scheduled Restart"
      confirm-text="Schedule"
      @confirm="handleSubmit"
      @cancel="showConfirm = false"
    >
      <p>You are about to schedule <strong>{{ selectedArns.length }}</strong> channel restart(s):</p>
      <ul class="mt-2 space-y-1">
        <li v-for="arn in selectedArns" :key="arn" class="text-xs font-mono bg-slate-100 dark:bg-slate-700 p-2 rounded truncate">{{ channelNameForArn(arn) }} — {{ arn.split(':').pop() }}</li>
      </ul>
      <p class="mt-2">Scheduled for: <strong>{{ formatScheduledTime() }}</strong></p>
    </ConfirmModal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useStore } from '../stores/main'
import ConfirmModal from './ConfirmModal.vue'

const store = useStore()
const selectedArns = ref<string[]>([])
const timezone = ref('Asia/Kolkata')
const date = ref('')
const time = ref('')
const showConfirm = ref(false)

const emit = defineEmits(['scheduled'])

const channelNameForArn = (arn: string) => {
  return store.channels.find(c => c.arn === arn)?.name || arn.split(':').pop() || 'Channel'
}

const formatScheduledTime = () => {
  if (!date.value || !time.value) return ''
  const dateStr = new Date(date.value).toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })
  return `${dateStr} at ${time.value} (${timezone.value})`
}

const resetForm = () => {
  selectedArns.value = []
  timezone.value = 'Asia/Kolkata'
  date.value = ''
  time.value = ''
}

const requestConfirmation = () => {
  if (selectedArns.value.length === 0 || !date.value || !time.value) return
  showConfirm.value = true
}

const handleSubmit = async () => {
  showConfirm.value = false
  const scheduledTime = `${date.value}T${time.value}:00`

  for (const arn of selectedArns.value) {
    const name = channelNameForArn(arn)
    try {
      await store.scheduleRestart(name, arn, scheduledTime, timezone.value)
    } catch (err) {
      console.error(`Failed to schedule ${name}:`, err)
    }
  }

  resetForm()
  emit('scheduled')
}

onMounted(() => { store.fetchChannels() })
</script>
