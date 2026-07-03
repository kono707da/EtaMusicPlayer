<script setup>
import { DialogTitle } from 'reka-ui'
import { cn } from '@/lib/utils'

defineOptions({ inheritAttrs: false })

const props = defineProps({
  asChild: { type: Boolean, default: false },
  class: { type: null, default: undefined }
})
</script>

<template>
  <DialogTitle v-bind="$attrs" :as-child="asChild" :class="cn('text-lg font-semibold leading-none tracking-tight', props.class)">
    <slot />
  </DialogTitle>
</template>
