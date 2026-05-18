<template>
  <div class="flex gap-1 border-b border-slate-200 dark:border-slate-800" role="tablist" :class="className">
    <button
      v-for="tab in tabs"
      :key="tab.id"
      type="button"
      role="tab"
      :aria-selected="modelValue === tab.id"
      :class="[
        'border-b-2 px-4 py-2.5 text-sm font-medium transition-ui focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500',
        modelValue === tab.id
          ? 'border-primary-600 text-primary-600 dark:border-primary-400 dark:text-primary-400'
          : 'border-transparent text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-200',
      ]"
      @click="$emit('update:modelValue', tab.id)"
    >
      {{ tab.label }}
    </button>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

export interface TabItem {
  id: string
  label: string
}

const props = withDefaults(defineProps<{
  tabs: TabItem[]
  modelValue: string
  class?: string
}>(), {
  class: '',
})

defineEmits<{ 'update:modelValue': [id: string] }>()

const className = computed(() => props.class)
</script>
