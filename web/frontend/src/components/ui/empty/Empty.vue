<script setup>
import { cn } from '@/lib/utils'

const props = defineProps({
  icon: { type: null, default: undefined },
  title: { type: String, default: '' },
  description: { type: String, default: '' },
  class: { type: null, default: undefined }
})
</script>

<template>
  <div
    :class="
      cn('flex flex-col items-center justify-center py-12 px-4 text-center', props.class)
    "
  >
    <component
      :is="icon"
      v-if="icon"
      class="h-12 w-12 text-muted-foreground/50 mb-4"
    />
    <h3 v-if="title" class="text-base font-medium text-foreground mb-1">
      {{ title }}
    </h3>
    <p v-if="description" class="text-sm text-muted-foreground">
      {{ description }}
    </p>
    <div v-if="$slots.default" class="mt-4">
      <slot />
    </div>
  </div>
</template>
