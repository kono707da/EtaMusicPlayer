<script setup>
import { DialogClose } from 'reka-ui'

defineOptions({ inheritAttrs: false })

const props = defineProps({
  asChild: { type: Boolean, default: false },
  as: { type: null, default: undefined }
})
</script>

<template>
  <DialogClose v-bind="$attrs" :as="as" :as-child="asChild">
    <slot />
  </DialogClose>
</template>
