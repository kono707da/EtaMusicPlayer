<script setup>
import { cn } from '@/lib/utils'

defineOptions({ inheritAttrs: false })

const props = defineProps({
  class: { type: null, default: undefined }
})
</script>

<template>
  <thead v-bind="$attrs" :class="cn('[&_tr]:border-b', props.class)">
    <slot />
  </thead>
</template>
