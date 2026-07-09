<script setup>
import { Label as LabelRoot } from 'reka-ui'
import { cn } from '@/lib/utils'

defineOptions({ inheritAttrs: false })

const props = defineProps({
  asChild: { type: Boolean, default: false },
  for: { type: String, default: undefined },
  class: { type: null, default: undefined }
})
</script>

<template>
  <LabelRoot v-bind="$attrs" :as-child="asChild" :for="props.for" :class="cn('text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70', props.class)">
    <slot />
  </LabelRoot>
</template>
