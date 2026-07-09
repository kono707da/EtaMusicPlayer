<script setup>
import { cn } from '@/lib/utils'

defineOptions({ inheritAttrs: false })

const props = defineProps({
  class: { type: null, default: undefined }
})
</script>

<template>
  <div class="relative w-full overflow-auto">
    <table v-bind="$attrs" :class="cn('w-full caption-bottom text-sm', props.class)">
      <slot />
    </table>
  </div>
</template>
