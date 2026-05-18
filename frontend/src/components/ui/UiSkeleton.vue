<template>
  <div :class="['animate-pulse rounded-lg bg-slate-200 dark:bg-slate-700', className]" :style="style" />
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(defineProps<{
  width?: string
  height?: string
  class?: string
}>(), {
  width: '100%',
  height: '1rem',
  class: '',
})

const className = computed(() => props.class)
const style = computed(() => ({ width: props.width, height: props.height }))
</script>
