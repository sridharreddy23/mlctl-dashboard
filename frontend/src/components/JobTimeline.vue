<template>
  <div class="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 p-6">
    <h2 class="text-lg font-semibold text-slate-900 dark:text-white mb-4">Job Timeline</h2>

    <div v-if="timelineJobs.length === 0" class="text-center py-6">
      <p class="text-slate-500 dark:text-slate-400 text-sm">No scheduled jobs to display</p>
    </div>

    <div v-else class="space-y-2">
      <!-- Time axis labels -->
      <div class="flex items-center gap-2 mb-3">
        <div class="w-28 flex-shrink-0"></div>
        <div class="flex-1 flex justify-between text-xs text-slate-400 dark:text-slate-500 font-mono">
          <span>{{ formatHour(rangeStart) }}</span>
          <span>{{ formatHour(rangeMid) }}</span>
          <span>{{ formatHour(rangeEnd) }}</span>
        </div>
      </div>

      <!-- Channel rows -->
      <div v-for="row in timelineRows" :key="row.channel" class="flex items-center gap-2">
        <div class="w-28 flex-shrink-0 text-xs text-slate-600 dark:text-slate-400 truncate font-medium" :title="row.channel">
          {{ row.channel }}
        </div>
        <div class="flex-1 relative h-8 bg-slate-100 dark:bg-slate-700/50 rounded-full overflow-hidden">
          <!-- Now indicator -->
          <div
            class="absolute top-0 bottom-0 w-px bg-slate-400 dark:bg-slate-500 z-10"
            :style="{ left: nowPosition + '%' }"
          >
            <div class="absolute -top-1 -left-1 w-2 h-2 rounded-full bg-slate-500 dark:bg-slate-400"></div>
          </div>

          <!-- Job blocks -->
          <div
            v-for="job in row.jobs"
            :key="job.id"
            :title="`${job.name} — ${formatStatus(job.status)} — ${new Date(job.time).toLocaleString()}`"
            :class="[
              'absolute top-1 bottom-1 rounded-full min-w-[8px] cursor-default transition-all',
              jobBlockColor(job.status)
            ]"
            :style="{ left: job.leftPct + '%', width: Math.max(job.widthPct, 1) + '%' }"
          ></div>
        </div>
      </div>

      <!-- Legend -->
      <div class="flex flex-wrap gap-4 mt-3 pt-3 border-t border-slate-200 dark:border-slate-700">
        <div v-for="item in legend" :key="item.label" class="flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400">
          <span :class="['w-3 h-3 rounded-full', item.color]"></span>
          {{ item.label }}
        </div>
        <div class="flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400">
          <span class="w-3 h-px bg-slate-400 dark:bg-slate-500"></span>
          Now
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useStore } from '../stores/main'
import { formatStatus } from '../utils/status'
import type { Job, MediaLiveJob } from '../stores/main'

const store = useStore()

const RANGE_HOURS = 24

const now = Date.now()
const rangeStart = new Date(now - 2 * 3600 * 1000)
const rangeEnd = new Date(now + (RANGE_HOURS - 2) * 3600 * 1000)
const rangeMid = new Date((rangeStart.getTime() + rangeEnd.getTime()) / 2)
const totalMs = rangeEnd.getTime() - rangeStart.getTime()

const nowPosition = computed(() => {
  return ((Date.now() - rangeStart.getTime()) / totalMs) * 100
})

const formatHour = (d: Date) => {
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false })
}

// Combine restart jobs and MediaLive jobs
const timelineJobs = computed(() => {
  const all: Array<{ id: string; name: string; time: string; status: string }> = []
  store.jobs.forEach(j => all.push(j))
  store.medialiveJobs.forEach(j => all.push(j))
  return all.filter(j => {
    const t = new Date(j.time).getTime()
    return t >= rangeStart.getTime() && t <= rangeEnd.getTime()
  })
})

interface TimelineRow {
  channel: string
  jobs: Array<{ id: string; name: string; status: string; time: string; leftPct: number; widthPct: number }>
}

const timelineRows = computed((): TimelineRow[] => {
  const grouped: Record<string, typeof timelineJobs.value> = {}
  timelineJobs.value.forEach(j => {
    const key = j.name || 'Unknown'
    if (!grouped[key]) grouped[key] = []
    grouped[key].push(j)
  })

  return Object.entries(grouped).map(([channel, jobs]) => ({
    channel,
    jobs: jobs.map(j => {
      const t = new Date(j.time).getTime()
      const leftPct = ((t - rangeStart.getTime()) / totalMs) * 100
      return { ...j, leftPct: Math.max(0, Math.min(leftPct, 99)), widthPct: 2 }
    })
  }))
})

const jobBlockColor = (status: string) => {
  if (status === 'done') return 'bg-green-500'
  if (status === 'running') return 'bg-blue-500 animate-pulse'
  if (status === 'failed') return 'bg-red-500'
  if (status === 'cancelled') return 'bg-slate-400'
  return 'bg-yellow-500'
}

const legend = [
  { label: 'Waiting', color: 'bg-yellow-500' },
  { label: 'Running', color: 'bg-blue-500' },
  { label: 'Done', color: 'bg-green-500' },
  { label: 'Failed', color: 'bg-red-500' },
  { label: 'Cancelled', color: 'bg-slate-400' },
]
</script>
