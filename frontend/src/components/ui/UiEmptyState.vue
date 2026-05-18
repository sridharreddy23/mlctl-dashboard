<template>
  <div class="flex flex-col items-center justify-center py-12 text-center">
    <component v-if="icon" :is="icon" class="mb-4 h-10 w-10 text-slate-400 dark:text-slate-500" aria-hidden="true" />
    <h3 v-if="title" class="text-sm font-semibold text-slate-900 dark:text-white">{{ title }}</h3>
    <p v-if="description" class="mt-1 max-w-sm text-sm text-slate-500 dark:text-slate-400">{{ description }}</p>
    <div v-if="$slots.default" class="mt-4">
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Component } from 'vue'

defineProps<{
  title?: string
  description?: string
  icon?: Component
}>()
</script>
