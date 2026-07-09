<script setup>
import { DropdownMenuSeparator } from 'reka-ui'
import { cn } from '@/lib/utils'

defineOptions({ inheritAttrs: false })

const props = defineProps({
  class: { type: null, default: undefined }
})
</script>

<template>
  <DropdownMenuSeparator v-bind="$attrs" :class="cn('-mx-1 my-1 h-px bg-muted', props.class)" />
</template>
