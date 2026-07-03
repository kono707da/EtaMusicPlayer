<script setup>
import { DialogDescription } from 'reka-ui'
import { cn } from '@/lib/utils'

defineOptions({ inheritAttrs: false })

const props = defineProps({
  asChild: { type: Boolean, default: false },
  class: { type: null, default: undefined }
})
</script>

<template>
  <DialogDescription v-bind="$attrs" :as-child="asChild" :class="cn('text-sm text-muted-foreground', props.class)">
    <slot />
  </DialogDescription>
</template>
