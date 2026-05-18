<template>
  <button
    :type="type"
    :disabled="disabled || loading"
    :class="[sizeClass, variantClass, block ? 'w-full' : '', className]"
    @click="$emit('click', $event)"
  >
    <Loader2 v-if="loading" class="h-4 w-4 animate-spin-slow shrink-0" aria-hidden="true" />
    <slot />
  </button>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Loader2 } from 'lucide-vue-next'

const props = withDefaults(defineProps<{
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost'
  size?: 'sm' | 'md' | 'lg'
  type?: 'button' | 'submit' | 'reset'
  loading?: boolean
  disabled?: boolean
  block?: boolean
  class?: string
}>(), {
  variant: 'primary',
  size: 'md',
  type: 'button',
  loading: false,
  disabled: false,
  block: false,
  class: '',
})

defineEmits<{ click: [event: MouseEvent] }>()

const className = computed(() => props.class)

const variantClass = computed(() => {
  const map = {
    primary: 'btn-primary gap-2',
    secondary: 'btn-secondary gap-2',
    danger: 'btn-danger gap-2',
    ghost: 'btn-ghost gap-2',
  }
  return map[props.variant]
})

const sizeClass = computed(() => {
  if (props.size === 'sm') return 'text-xs px-3 py-1.5'
  if (props.size === 'lg') return 'text-base px-6 py-3'
  return ''
})
</script>
