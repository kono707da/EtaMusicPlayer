<script setup>
import { DialogTrigger } from 'reka-ui'

defineOptions({ inheritAttrs: false })

const props = defineProps({
  asChild: { type: Boolean, default: false },
  as: { type: null, default: undefined }
})
</script>

<template>
  <DialogTrigger v-bind="$attrs" :as="as" :as-child="asChild">
    <slot />
  </DialogTrigger>
</template>
