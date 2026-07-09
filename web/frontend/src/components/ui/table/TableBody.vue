<script setup>
import { cn } from '@/lib/utils'

defineOptions({ inheritAttrs: false })

const props = defineProps({
  class: { type: null, default: undefined }
})
</script>

<template>
  <tbody v-bind="$attrs" :class="cn('[&_tr:last-child]:border-0', props.class)">
    <slot />
  </tbody>
</template>
