<script setup>
import {
  SliderRoot,
  SliderTrack,
  SliderRange,
  SliderThumb
} from 'reka-ui'
import { cn } from '@/lib/utils'

const props = defineProps({
  modelValue: { type: Array, default: () => [] },
  defaultValue: { type: Array, default: undefined },
  min: { type: Number, default: 0 },
  max: { type: Number, default: 100 },
  step: { type: Number, default: 1 },
  disabled: { type: Boolean, default: false },
  orientation: { type: String, default: 'horizontal' },
  class: { type: null, default: undefined }
})

const emits = defineEmits(['update:modelValue'])
</script>

<template>
  <SliderRoot
    :model-value="modelValue"
    :default-value="defaultValue"
    :min="min"
    :max="max"
    :step="step"
    :disabled="disabled"
    :orientation="orientation"
    :class="
      cn(
        'relative flex w-full touch-none select-none items-center',
        props.class
      )
    "
    @update:model-value="emits('update:modelValue', $event)"
  >
    <SliderTrack
      class="relative h-1 w-full grow overflow-hidden rounded-full bg-secondary"
    >
      <SliderRange class="absolute h-full bg-primary" />
    </SliderTrack>
    <SliderThumb
      class="block h-3 w-3 rounded-full border border-primary bg-primary ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50"
    />
  </SliderRoot>
</template>
