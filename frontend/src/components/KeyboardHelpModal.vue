<template>
  <Teleport to="body">
    <div
      v-if="visible"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="shortcuts-title"
      @click.self="close"
    >
      <div ref="panelRef" class="card w-full max-w-md animate-slide-up p-6 shadow-elevated">
        <div class="mb-4 flex items-center justify-between">
          <h2 id="shortcuts-title" class="text-lg font-semibold text-slate-900 dark:text-white">Keyboard shortcuts</h2>
          <button type="button" class="btn-ghost p-1" aria-label="Close" @click="close">
            <X class="h-5 w-5" />
          </button>
        </div>
        <dl class="space-y-3 text-sm">
          <div v-for="row in shortcuts" :key="row.keys" class="flex justify-between gap-4">
            <dt class="font-mono text-xs text-slate-500 dark:text-slate-400">{{ row.keys }}</dt>
            <dd class="text-slate-700 dark:text-slate-300">{{ row.action }}</dd>
          </div>
        </dl>
        <div class="mt-6 flex justify-end">
          <UiButton variant="secondary" size="sm" @click="close">Close</UiButton>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { toRef } from 'vue'
import { X } from 'lucide-vue-next'
import { useModal } from '../composables/useModal'
import UiButton from './ui/UiButton.vue'

const props = defineProps<{ visible: boolean }>()
const emit = defineEmits<{ close: [] }>()

const close = () => emit('close')
const { panelRef } = useModal(toRef(props, 'visible'), close)

const shortcuts = [
  { keys: '1 – 5', action: 'Navigate main sections' },
  { keys: 'r', action: 'Refresh jobs' },
  { keys: 'Shift + ?', action: 'Show this help' },
  { keys: 'Esc', action: 'Close dialogs' },
]
</script>
