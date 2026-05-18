<template>
  <Teleport to="body">
    <div
      class="pointer-events-none fixed bottom-20 right-4 z-50 flex w-full max-w-sm flex-col-reverse gap-3 lg:bottom-4"
      role="status"
      aria-live="polite"
    >
      <transition-group name="toast">
        <div
          v-for="toast in visibleToasts"
          :key="toast.id"
          :class="[
            'pointer-events-auto overflow-hidden rounded-lg border p-4 shadow-elevated',
            toastBoxClass(toast.type),
          ]"
        >
          <div class="flex items-start gap-3">
            <component :is="toastIcon(toast.type)" class="mt-0.5 h-5 w-5 shrink-0" :class="toastIconClass(toast.type)" />
            <p class="min-w-0 flex-1 text-sm font-medium leading-snug break-words" :class="toastTextClass(toast.type)">
              {{ toast.message }}
            </p>
            <button
              type="button"
              class="shrink-0 rounded p-0.5 opacity-70 transition-ui hover:opacity-100"
              :class="toastTextClass(toast.type)"
              :aria-label="`Dismiss: ${toast.message}`"
              @click="store.removeToast(toast.id)"
            >
              <X class="h-4 w-4" />
            </button>
          </div>
          <div class="mt-2 h-0.5 overflow-hidden rounded-full bg-black/15 dark:bg-white/20">
            <div class="toast-progress h-full opacity-60" :class="toastProgressClass(toast.type)" />
          </div>
        </div>
      </transition-group>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { CheckCircle2, AlertCircle, AlertTriangle, Info, X } from 'lucide-vue-next'
import { useStore } from '../stores/main'
import type { Toast } from '../stores/main'

const store = useStore()
const MAX_TOASTS = 3

const visibleToasts = computed(() => store.toasts.slice(-MAX_TOASTS))

const toastBoxClass = (type: Toast['type']) => {
  const map: Record<Toast['type'], string> = {
    success: 'border-green-300 bg-green-50 dark:border-green-600 dark:bg-green-950',
    error: 'border-red-300 bg-red-50 dark:border-red-600 dark:bg-red-950',
    warning: 'border-amber-300 bg-amber-50 dark:border-amber-600 dark:bg-amber-950',
    info: 'border-sky-300 bg-sky-50 dark:border-sky-600 dark:bg-sky-950',
  }
  return map[type] || map.info
}

const toastTextClass = (type: Toast['type']) => {
  const map: Record<Toast['type'], string> = {
    success: 'text-green-900 dark:text-green-100',
    error: 'text-red-900 dark:text-red-100',
    warning: 'text-amber-900 dark:text-amber-100',
    info: 'text-sky-900 dark:text-sky-100',
  }
  return map[type] || map.info
}

const toastIconClass = (type: Toast['type']) => {
  const map: Record<Toast['type'], string> = {
    success: 'text-green-600 dark:text-green-400',
    error: 'text-red-600 dark:text-red-400',
    warning: 'text-amber-600 dark:text-amber-400',
    info: 'text-sky-600 dark:text-sky-400',
  }
  return map[type] || map.info
}

const toastProgressClass = (type: Toast['type']) => {
  const map: Record<Toast['type'], string> = {
    success: 'bg-green-600 dark:bg-green-400',
    error: 'bg-red-600 dark:bg-red-400',
    warning: 'bg-amber-600 dark:bg-amber-400',
    info: 'bg-sky-600 dark:bg-sky-400',
  }
  return map[type] || map.info
}

const toastIcon = (type: Toast['type']) => {
  const map = {
    success: CheckCircle2,
    error: AlertCircle,
    warning: AlertTriangle,
    info: Info,
  }
  return map[type] || Info
}
</script>

<style scoped>
.toast-enter-active {
  transition: all 0.3s ease-out;
}
.toast-leave-active {
  transition: all 0.2s ease-in;
}
.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateX(100%);
}
.toast-move {
  transition: transform 0.3s ease;
}
.toast-progress {
  width: 100%;
  animation: toast-shrink 5s linear forwards;
}
@keyframes toast-shrink {
  from { width: 100%; }
  to { width: 0%; }
}
@media (prefers-reduced-motion: reduce) {
  .toast-progress {
    animation: none;
    width: 100%;
  }
}
</style>
