<script setup>
import { SelectValue } from 'reka-ui'

defineOptions({ inheritAttrs: false })

const props = defineProps({
  placeholder: { type: String, default: undefined }
})
</script>

<template>
  <SelectValue v-bind="$attrs" :placeholder="placeholder">
    <slot />
  </SelectValue>
</template>
