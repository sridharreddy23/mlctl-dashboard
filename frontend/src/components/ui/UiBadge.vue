<template>
  <span :class="badgeClass">
    <slot>{{ label }}</slot>
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { formatStatus, getStatusBgColor } from '../../utils/status'

const props = withDefaults(defineProps<{
  status?: string
  label?: string
  variant?: 'status' | 'neutral' | 'primary'
}>(), {
  variant: 'status',
})

const badgeClass = computed(() => {
  const base = 'badge'
  if (props.variant === 'neutral') {
    return `${base} bg-slate-100 text-slate-700 dark:bg-slate-700 dark:text-slate-200`
  }
  if (props.variant === 'primary') {
    return `${base} bg-primary-100 text-primary-800 dark:bg-primary-900 dark:text-primary-200`
  }
  if (props.status) {
    return `${base} ${getStatusBgColor(props.status)}`
  }
  return base
})

const label = computed(() => props.label || (props.status ? formatStatus(props.status) : ''))
</script>
