<template>
  <section :class="['card', paddingClass, className]">
    <header v-if="title || $slots.header" class="mb-4 flex items-start justify-between gap-4">
      <slot name="header">
        <div>
          <h2 v-if="title" class="text-lg font-semibold text-slate-900 dark:text-white">{{ title }}</h2>
          <p v-if="subtitle" class="mt-1 text-sm text-slate-500 dark:text-slate-400">{{ subtitle }}</p>
        </div>
      </slot>
      <slot name="actions" />
    </header>
    <slot />
    <footer v-if="$slots.footer" class="mt-4 border-t border-slate-200 pt-4 dark:border-slate-700">
      <slot name="footer" />
    </footer>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(defineProps<{
  title?: string
  subtitle?: string
  padding?: 'none' | 'sm' | 'md' | 'lg'
  class?: string
}>(), {
  padding: 'md',
  class: '',
})

const className = computed(() => props.class)
const paddingClass = computed(() => {
  if (props.padding === 'none') return ''
  if (props.padding === 'sm') return 'p-4'
  if (props.padding === 'lg') return 'p-8'
  return 'p-6'
})
</script>
