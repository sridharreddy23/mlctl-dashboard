<template>
  <Teleport to="body">
    <div v-if="visible" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" @click.self="cancel">
      <div class="bg-white dark:bg-slate-800 rounded-xl shadow-xl w-full max-w-md overflow-hidden animate-in">
        <div class="p-6">
          <h3 class="text-lg font-semibold text-slate-900 dark:text-white mb-2">{{ title }}</h3>
          <div class="text-sm text-slate-600 dark:text-slate-300 space-y-2">
            <slot />
          </div>
        </div>
        <div class="px-6 pb-6 flex gap-3 justify-end">
          <button
            @click="cancel"
            class="px-5 py-2 bg-slate-200 dark:bg-slate-700 hover:bg-slate-300 dark:hover:bg-slate-600 text-slate-900 dark:text-white font-medium rounded-lg transition-colors text-sm"
          >
            {{ cancelText }}
          </button>
          <button
            @click="confirm"
            :class="[
              'px-5 py-2 font-medium rounded-lg transition-colors text-sm text-white',
              dangerous
                ? 'bg-red-600 hover:bg-red-700'
                : 'bg-blue-600 hover:bg-blue-700'
            ]"
          >
            {{ confirmText }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
defineProps<{
  visible: boolean
  title: string
  confirmText?: string
  cancelText?: string
  dangerous?: boolean
}>()

const emit = defineEmits(['confirm', 'cancel'])

const confirm = () => emit('confirm')
const cancel = () => emit('cancel')
</script>

<style scoped>
.animate-in {
  animation: modal-in 0.2s ease-out;
}
@keyframes modal-in {
  from { opacity: 0; transform: scale(0.95) translateY(10px); }
  to { opacity: 1; transform: scale(1) translateY(0); }
}
</style>
