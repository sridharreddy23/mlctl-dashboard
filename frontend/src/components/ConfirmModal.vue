<template>
  <Teleport to="body">
    <div
      v-if="visible"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
      role="dialog"
      aria-modal="true"
      :aria-labelledby="titleId"
      @click.self="cancel"
    >
      <div ref="panelRef" class="card w-full max-w-md animate-slide-up overflow-hidden shadow-elevated">
        <div class="p-6">
          <h3 :id="titleId" class="mb-2 text-lg font-semibold text-slate-900 dark:text-white">{{ title }}</h3>
          <div class="space-y-2 text-sm text-slate-600 dark:text-slate-300">
            <slot />
          </div>
        </div>
        <div class="flex justify-end gap-3 px-6 pb-6">
          <UiButton variant="secondary" size="sm" @click="cancel">{{ cancelText }}</UiButton>
          <UiButton :variant="dangerous ? 'danger' : 'primary'" size="sm" @click="confirm">{{ confirmText }}</UiButton>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, toRef } from 'vue'
import { useModal } from '../composables/useModal'
import UiButton from './ui/UiButton.vue'

const props = withDefaults(defineProps<{
  visible: boolean
  title: string
  confirmText?: string
  cancelText?: string
  dangerous?: boolean
}>(), {
  confirmText: 'Confirm',
  cancelText: 'Cancel',
  dangerous: false,
})

const emit = defineEmits(['confirm', 'cancel'])

const titleId = computed(() => `modal-title-${props.title.replace(/\s+/g, '-').toLowerCase()}`)

const confirm = () => emit('confirm')
const cancel = () => emit('cancel')
const { panelRef } = useModal(toRef(props, 'visible'), cancel)
</script>
