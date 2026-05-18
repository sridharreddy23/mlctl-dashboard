<template>
  <div class="space-y-6">
    <div>
      <h2 class="page-title">Schedule Restart</h2>
      <p class="page-subtitle">Select channels and schedule MediaLive restarts</p>
    </div>

    <UiCard padding="lg">
      <form class="space-y-6" @submit.prevent="requestConfirmation">

        <!-- ── Channel Picker ─────────────────────────────── -->
        <div>
          <div class="mb-3 flex items-center justify-between gap-3">
            <label class="text-sm font-medium text-slate-700 dark:text-slate-300">
              Channels
              <span v-if="selectedArns.length" class="ml-2 inline-flex items-center rounded-full bg-primary-100 px-2 py-0.5 text-xs font-semibold text-primary-700 dark:bg-primary-900/50 dark:text-primary-300">
                {{ selectedArns.length }} selected
              </span>
            </label>
            <div class="flex items-center gap-2">
              <button
                v-if="filteredChannels.length > 0 && selectedArns.length < filteredChannels.length"
                type="button"
                class="text-xs font-medium text-primary-600 hover:text-primary-800 dark:text-primary-400 dark:hover:text-primary-300"
                @click="selectAll"
              >Select all</button>
              <span v-if="filteredChannels.length > 0 && selectedArns.length > 0 && selectedArns.length < filteredChannels.length" class="text-xs text-slate-300 dark:text-slate-600">·</span>
              <button
                v-if="selectedArns.length > 0"
                type="button"
                class="text-xs font-medium text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-200"
                @click="selectedArns = []"
              >Clear</button>
            </div>
          </div>

          <!-- Search -->
          <div class="relative mb-3">
            <Search class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <input
              v-model="channelSearch"
              type="search"
              placeholder="Filter channels…"
              class="input-field pl-9 pr-4 py-2 text-sm"
            />
          </div>

          <!-- Favorites shortcut -->
          <div v-if="favoriteArns.length > 0 && channelSearch === ''" class="mb-2 flex flex-wrap gap-1.5">
            <button
              v-for="arn in favoritesInStore"
              :key="arn"
              type="button"
              :class="[
                'inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium transition-colors duration-150',
                selectedArns.includes(arn)
                  ? 'border-warning-400 bg-warning-100 text-warning-800 dark:border-warning-600 dark:bg-warning-900/40 dark:text-warning-300'
                  : 'border-slate-200 bg-slate-50 text-slate-600 hover:border-warning-300 hover:bg-warning-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300',
              ]"
              @click="toggleArn(arn)"
            >
              <Star class="h-3 w-3 fill-warning-400 text-warning-400" />
              {{ channelNameForArn(arn) }}
            </button>
          </div>

          <!-- Empty state -->
          <div v-if="store.channels.length === 0" class="rounded-lg border border-dashed border-slate-300 p-8 text-center dark:border-slate-600">
            <Radio class="mx-auto mb-2 h-8 w-8 text-slate-300 dark:text-slate-600" />
            <p class="text-sm text-slate-500 dark:text-slate-400">No channels loaded</p>
            <RouterLink to="/settings" class="mt-1 inline-block text-xs font-medium text-primary-600 hover:underline dark:text-primary-400">Configure in Settings →</RouterLink>
          </div>

          <!-- No results -->
          <div v-else-if="filteredChannels.length === 0" class="rounded-lg border border-dashed border-slate-300 p-6 text-center dark:border-slate-600">
            <p class="text-sm text-slate-500 dark:text-slate-400">No channels match "<span class="font-mono">{{ channelSearch }}</span>"</p>
          </div>

          <!-- Channel cards grid -->
          <div v-else class="grid grid-cols-1 gap-2 sm:grid-cols-2">
            <button
              v-for="ch in filteredChannels"
              :key="ch.arn"
              type="button"
              :class="[
                'group relative flex w-full items-start gap-3 rounded-xl border p-3.5 text-left transition-all duration-150 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-1',
                selectedArns.includes(ch.arn)
                  ? 'border-primary-400 bg-primary-50 shadow-sm ring-1 ring-primary-400 dark:border-primary-600 dark:bg-primary-950/40 dark:ring-primary-600'
                  : 'border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-800/50 dark:hover:border-slate-600 dark:hover:bg-slate-800',
              ]"
              @click="toggleArn(ch.arn)"
            >
              <!-- Selection indicator -->
              <span :class="[
                'mt-0.5 flex h-4.5 w-4.5 shrink-0 items-center justify-center rounded-full border-2 transition-colors duration-150',
                selectedArns.includes(ch.arn)
                  ? 'border-primary-500 bg-primary-500'
                  : 'border-slate-300 bg-white dark:border-slate-600 dark:bg-slate-700',
              ]">
                <Check v-if="selectedArns.includes(ch.arn)" class="h-2.5 w-2.5 text-white" />
              </span>

              <!-- Channel info -->
              <div class="min-w-0 flex-1">
                <p class="truncate text-sm font-semibold leading-snug" :class="selectedArns.includes(ch.arn) ? 'text-primary-900 dark:text-primary-100' : 'text-slate-900 dark:text-white'">
                  {{ ch.name }}
                </p>
                <p class="mt-0.5 truncate font-mono text-xs text-slate-400 dark:text-slate-500">
                  {{ ch.arn.split(':').pop() }}
                </p>
              </div>

              <!-- Favorite toggle -->
              <button
                type="button"
                :title="isFavorite(ch.arn) ? 'Remove from favorites' : 'Add to favorites'"
                class="shrink-0 rounded p-0.5 opacity-0 transition-all duration-150 group-hover:opacity-100"
                :class="isFavorite(ch.arn) ? '!opacity-100' : ''"
                @click.stop="toggleFavorite(ch.arn)"
              >
                <Star
                  class="h-3.5 w-3.5 transition-colors duration-150"
                  :class="isFavorite(ch.arn) ? 'fill-warning-400 text-warning-400' : 'text-slate-300 hover:text-warning-400 dark:text-slate-600'"
                />
              </button>
            </button>
          </div>
        </div>

        <!-- ── Date, Time, Timezone ──────────────────────── -->
        <div class="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <UiInput v-model="date" label="Date" type="date" required />
          <UiInput v-model="time" label="Time" type="time" required />
          <UiSelect v-model="timezone" label="Timezone">
            <option v-for="tz in tzOptions" :key="tz" :value="tz">{{ tz }}</option>
          </UiSelect>
        </div>

        <!-- ── Scheduled time preview ────────────────────── -->
        <div v-if="date && time" class="flex items-center gap-2 rounded-lg border border-primary-200 bg-primary-50 px-4 py-3 dark:border-primary-800 dark:bg-primary-950/50">
          <Clock class="h-4 w-4 shrink-0 text-primary-500" />
          <p class="text-sm text-primary-900 dark:text-primary-200">
            <span class="font-medium">Scheduled for:</span> {{ formatScheduledTime() }}
            <span v-if="timeUntil" class="ml-2 text-xs text-primary-500">({{ timeUntil }})</span>
          </p>
        </div>

        <!-- ── Submit ─────────────────────────────────────── -->
        <div class="flex gap-3">
          <UiButton type="submit" variant="primary" class="flex-1" :loading="store.loading" :disabled="selectedArns.length === 0 || !date || !time">
            {{ selectedArns.length > 1 ? `Schedule ${selectedArns.length} Restarts` : 'Schedule Restart' }}
          </UiButton>
          <UiButton type="button" variant="secondary" @click="resetForm">Clear</UiButton>
        </div>
      </form>
    </UiCard>

    <!-- Confirm modal -->
    <ConfirmModal :visible="showConfirm" title="Confirm Scheduled Restart" confirm-text="Schedule" @confirm="handleSubmit" @cancel="showConfirm = false">
      <p>Scheduling <strong>{{ selectedArns.length }}</strong> channel restart(s):</p>
      <ul class="mt-2 max-h-40 space-y-1 overflow-y-auto">
        <li v-for="arn in selectedArns" :key="arn" class="truncate rounded bg-slate-100 p-2 font-mono text-xs dark:bg-slate-700">
          {{ channelNameForArn(arn) }} — {{ arn.split(':').pop() }}
        </li>
      </ul>
      <p class="mt-2">Scheduled for: <strong>{{ formatScheduledTime() }}</strong></p>
      <p v-if="timeUntil" class="mt-1 text-xs text-slate-500">That's {{ timeUntil }} from now</p>
    </ConfirmModal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute, RouterLink } from 'vue-router'
import { Star, Search, Check, Clock, Radio } from 'lucide-vue-next'
import { useStore } from '../stores/main'
import ConfirmModal from './ConfirmModal.vue'
import UiCard from './ui/UiCard.vue'
import UiButton from './ui/UiButton.vue'
import UiInput from './ui/UiInput.vue'
import UiSelect from './ui/UiSelect.vue'
import { detectTimezone, timezoneOptions } from '../utils/timezone'
import { loadFavoriteArns, toggleFavoriteArn, sortChannelsByFavorites } from '../utils/favorites'

const store = useStore()
const router = useRouter()
const route = useRoute()

const selectedArns = ref<string[]>([])
const channelSearch = ref('')
const favoriteArns = ref<string[]>(loadFavoriteArns())

const detectedTz = detectTimezone()
const timezone = ref(detectedTz)
const tzOptions = timezoneOptions(detectedTz)
const date = ref('')
const time = ref('')
const showConfirm = ref(false)

// ── Channel helpers ──────────────────────────────────────

const sortedChannels = computed(() => sortChannelsByFavorites(store.channels))

const filteredChannels = computed(() => {
  const q = channelSearch.value.trim().toLowerCase()
  if (!q) return sortedChannels.value
  return sortedChannels.value.filter(ch =>
    ch.name.toLowerCase().includes(q) || ch.arn.toLowerCase().includes(q)
  )
})

const favoritesInStore = computed(() =>
  favoriteArns.value.filter(arn => store.channels.some(ch => ch.arn === arn))
)

const isFavorite = (arn: string) => favoriteArns.value.includes(arn)

const toggleFavorite = (arn: string) => {
  favoriteArns.value = toggleFavoriteArn(arn)
}

const toggleArn = (arn: string) => {
  const idx = selectedArns.value.indexOf(arn)
  if (idx >= 0) selectedArns.value.splice(idx, 1)
  else selectedArns.value.push(arn)
}

const selectAll = () => {
  selectedArns.value = filteredChannels.value.map(ch => ch.arn)
}

const channelNameForArn = (arn: string) =>
  store.channels.find(c => c.arn === arn)?.name || arn.split(':').pop() || 'Channel'

// ── Time helpers ─────────────────────────────────────────

const setSmartDefaults = () => {
  const now = new Date()
  date.value = now.toISOString().slice(0, 10)
  // Round up to next :00 or :30 boundary
  const m = now.getMinutes() < 30 ? 30 : 60
  const rounded = new Date(now)
  rounded.setMinutes(m, 0, 0)
  time.value = rounded.toTimeString().slice(0, 5)
}

const formatScheduledTime = () => {
  if (!date.value || !time.value) return ''
  const dateStr = new Date(date.value).toLocaleDateString('en-US', {
    weekday: 'long', year: 'numeric', month: 'long', day: 'numeric',
  })
  return `${dateStr} at ${time.value} (${timezone.value})`
}

const timeUntil = computed(() => {
  if (!date.value || !time.value) return ''
  try {
    const target = new Date(`${date.value}T${time.value}:00`).getTime()
    const diff = Math.floor((target - Date.now()) / 1000)
    if (diff <= 0) return 'in the past'
    const h = Math.floor(diff / 3600)
    const m = Math.floor((diff % 3600) / 60)
    if (h > 24) {
      const days = Math.floor(h / 24)
      return `in ${days} day${days > 1 ? 's' : ''}`
    }
    return h > 0 ? `in ${h}h ${m}m` : `in ${m}m`
  } catch {
    return ''
  }
})

// ── Form actions ──────────────────────────────────────────

const resetForm = () => {
  selectedArns.value = []
  channelSearch.value = ''
  setSmartDefaults()
  timezone.value = detectedTz
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
  router.push('/jobs')
}

onMounted(async () => {
  await store.fetchChannels()
  setSmartDefaults()
  // Pre-select channel from ?arn= query param (set by Quick Schedule button)
  const queryArn = route.query.arn
  if (queryArn && typeof queryArn === 'string' && store.channels.some(ch => ch.arn === queryArn)) {
    selectedArns.value = [queryArn]
  }
})
</script>
