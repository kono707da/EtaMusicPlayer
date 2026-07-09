<script setup>
import { cn } from '@/lib/utils'

defineOptions({ inheritAttrs: false })

const props = defineProps({
  class: { type: null, default: undefined }
})
</script>

<template>
  <tr
    v-bind="$attrs"
    :class="
      cn(
        'border-b border-border transition-colors hover:bg-accent/50 data-[state=selected]:bg-accent',
        props.class
      )
    "
  >
    <slot />
  </tr>
</template>
