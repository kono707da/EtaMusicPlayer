<script setup>
import {
  DropdownMenuContent,
  DropdownMenuPortal
} from 'reka-ui'
import { cn } from '@/lib/utils'

defineOptions({ inheritAttrs: false })

const props = defineProps({
  sideOffset: { type: Number, default: 4 },
  align: { type: String, default: 'start' },
  side: { type: String, default: undefined },
  class: { type: null, default: undefined }
})
</script>

<template>
  <DropdownMenuPortal>
    <DropdownMenuContent
      v-bind="$attrs"
      :side-offset="sideOffset"
      :align="align"
      :side="side"
      :class="
        cn(
          'z-50 min-w-[8rem] overflow-hidden rounded-md border bg-popover p-1 text-popover-foreground shadow-md data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0',
          props.class
        )
      "
    >
      <slot />
    </DropdownMenuContent>
  </DropdownMenuPortal>
</template>
