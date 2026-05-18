<template>
  <div class="block" :class="wrapperClass">
    <label v-if="label" :for="selectId" class="mb-2 block text-sm font-medium text-slate-700 dark:text-slate-300">
      {{ label }}
      <span v-if="required" class="text-danger-500">*</span>
    </label>
    <select
      :id="selectId"
      :value="modelValue"
      :required="required"
      :disabled="disabled"
      :class="['input-field', error ? 'input-field-error' : '', selectClass]"
      @change="$emit('update:modelValue', ($event.target as HTMLSelectElement).value)"
    >
      <slot />
    </select>
    <p v-if="error" class="mt-1 text-xs text-danger-600 dark:text-danger-400">{{ error }}</p>
    <p v-else-if="hint" class="mt-1 text-xs text-slate-500 dark:text-slate-400">{{ hint }}</p>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(defineProps<{
  modelValue?: string
  label?: string
  hint?: string
  error?: string
  required?: boolean
  disabled?: boolean
  id?: string
  wrapperClass?: string
  selectClass?: string
}>(), {
  modelValue: '',
  required: false,
  disabled: false,
})

defineEmits<{ 'update:modelValue': [value: string] }>()

const selectId = computed(() => props.id || `select-${Math.random().toString(36).slice(2, 9)}`)
</script>
