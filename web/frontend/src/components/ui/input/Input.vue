<script setup>
import { cn } from '@/lib/utils'

defineOptions({
  inheritAttrs: false
})

const props = defineProps({
  type: { type: String, default: 'text' },
  class: { type: null, default: undefined }
})

const modelValue = defineModel()
</script>

<template>
  <input
    v-model="modelValue"
    :type="type"
    v-bind="$attrs"
    :class="
      cn(
        'flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50',
        props.class
      )
    "
  />
</template>
