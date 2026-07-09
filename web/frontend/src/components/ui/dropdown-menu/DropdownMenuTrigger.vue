<script setup>
import { DropdownMenuTrigger } from 'reka-ui'

defineOptions({ inheritAttrs: false })

const props = defineProps({
  asChild: { type: Boolean, default: false },
  as: { type: null, default: undefined }
})
</script>

<template>
  <DropdownMenuTrigger v-bind="$attrs" :as="as" :as-child="asChild">
    <slot />
  </DropdownMenuTrigger>
</template>
