<template>
  <Teleport to="body">
    <div class="fixed bottom-4 right-4 z-50 flex flex-col-reverse gap-3 max-w-sm w-full pointer-events-none">
      <transition-group name="toast">
        <div
          v-for="toast in store.toasts"
          :key="toast.id"
          :class="[
            'pointer-events-auto rounded-lg shadow-lg border p-4 flex items-start gap-3 backdrop-blur-sm transition-all duration-300',
            toastStyles[toast.type] || toastStyles.info
          ]"
        >
          <span class="text-lg flex-shrink-0 mt-0.5">{{ toastIcons[toast.type] || 'ℹ️' }}</span>
          <div class="flex-1 min-w-0">
            <p class="text-sm font-medium leading-snug break-words">{{ toast.message }}</p>
          </div>
          <button
            @click="store.removeToast(toast.id)"
            class="flex-shrink-0 opacity-60 hover:opacity-100 text-sm leading-none"
          >✕</button>
        </div>
      </transition-group>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { useStore } from '../stores/main'

const store = useStore()

const toastStyles: Record<string, string> = {
  success: 'bg-green-50/95 dark:bg-green-950/95 border-green-200 dark:border-green-800 text-green-900 dark:text-green-100',
  error: 'bg-red-50/95 dark:bg-red-950/95 border-red-200 dark:border-red-800 text-red-900 dark:text-red-100',
  warning: 'bg-yellow-50/95 dark:bg-yellow-950/95 border-yellow-200 dark:border-yellow-800 text-yellow-900 dark:text-yellow-100',
  info: 'bg-blue-50/95 dark:bg-blue-950/95 border-blue-200 dark:border-blue-800 text-blue-900 dark:text-blue-100',
}

const toastIcons: Record<string, string> = {
  success: '✓',
  error: '⚠️',
  warning: '⚡',
  info: 'ℹ️',
}
</script>

<style scoped>
.toast-enter-active {
  transition: all 0.3s ease-out;
}
.toast-leave-active {
  transition: all 0.2s ease-in;
}
.toast-enter-from {
  opacity: 0;
  transform: translateX(100%);
}
.toast-leave-to {
  opacity: 0;
  transform: translateX(100%);
}
.toast-move {
  transition: transform 0.3s ease;
}
</style>
