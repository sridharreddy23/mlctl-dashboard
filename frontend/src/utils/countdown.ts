import { ref, onMounted, onUnmounted, watch } from 'vue'

/**
 * Composable that provides a reactive, auto-updating relative time string.
 * Updates every second for active countdowns.
 */
export function useCountdown(isoTime: () => string, isActive: () => boolean) {
  const display = ref('')
  let timer: ReturnType<typeof setInterval> | null = null

  const update = () => {
    const t = isoTime()
    if (!t) { display.value = '-'; return }
    try {
      const target = new Date(t).getTime()
      const now = Date.now()
      const diff = Math.floor((target - now) / 1000)
      if (diff > 0) {
        const h = Math.floor(diff / 3600)
        const m = Math.floor((diff % 3600) / 60)
        const s = diff % 60
        display.value = h > 0 ? `${h}h ${m}m ${s}s` : m > 0 ? `${m}m ${s}s` : `${s}s`
      } else {
        const absDiff = Math.abs(diff)
        const h = Math.floor(absDiff / 3600)
        const m = Math.floor((absDiff % 3600) / 60)
        display.value = h > 0 ? `${h}h ${m}m ago` : `${m}m ago`
      }
    } catch {
      display.value = '-'
    }
  }

  watch(isActive, (active) => {
    if (active) {
      if (!timer) timer = setInterval(update, 1000)
    } else {
      if (timer) {
        clearInterval(timer)
        timer = null
      }
    }
    update()
  }, { immediate: true })

  onUnmounted(() => {
    if (timer) clearInterval(timer)
  })

  return display
}
