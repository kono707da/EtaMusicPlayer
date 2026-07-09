<script setup>
import { DropdownMenuLabel } from 'reka-ui'
import { cn } from '@/lib/utils'

defineOptions({ inheritAttrs: false })

const props = defineProps({
  asChild: { type: Boolean, default: false },
  class: { type: null, default: undefined }
})
</script>

<template>
  <DropdownMenuLabel v-bind="$attrs" :as-child="asChild" :class="cn('px-2 py-1.5 text-sm font-semibold', props.class)">
    <slot />
  </DropdownMenuLabel>
</template>
