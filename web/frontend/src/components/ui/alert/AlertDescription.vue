<script setup>
import { cn } from '@/lib/utils'

const props = defineProps({
  class: { type: null, default: undefined }
})
</script>

<template>
  <div :class="cn('text-sm text-muted-foreground [&_p]:leading-relaxed', props.class)">
    <slot />
  </div>
</template>
