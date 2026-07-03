<script setup>
import { DropdownMenuItem } from 'reka-ui'
import { cn } from '@/lib/utils'

defineOptions({ inheritAttrs: false })

const props = defineProps({
  asChild: { type: Boolean, default: false },
  as: { type: null, default: undefined },
  disabled: { type: Boolean, default: false },
  variant: { type: String, default: 'default' },
  class: { type: null, default: undefined }
})
</script>

<template>
  <DropdownMenuItem
    v-bind="$attrs"
    :as="as"
    :as-child="asChild"
    :disabled="disabled"
    :data-variant="variant"
    :class="
      cn(
        'relative flex cursor-default select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none transition-colors focus:bg-accent focus:text-accent-foreground data-[disabled]:pointer-events-none data-[disabled]:opacity-50 data-[variant=destructive]:text-destructive data-[variant=destructive]:focus:bg-destructive/10',
        props.class
      )
    "
  >
    <slot />
  </DropdownMenuItem>
</template>
