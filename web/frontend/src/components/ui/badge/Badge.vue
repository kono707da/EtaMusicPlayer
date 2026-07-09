<script>
import { cva } from 'class-variance-authority'

export const badgeVariants = cva(
  'inline-flex items-center rounded-md border-transparent px-2.5 py-0.5 text-xs font-semibold transition-colors',
  {
    variants: {
      variant: {
        default: 'bg-primary text-primary-foreground',
        secondary: 'bg-secondary text-secondary-foreground',
        outline: 'border border-border text-foreground',
        destructive: 'bg-destructive text-destructive-foreground',
        success: 'bg-emerald-600/20 text-emerald-400'
      }
    },
    defaultVariants: {
      variant: 'default'
    }
  }
)
</script>

<script setup>
import { cn } from '@/lib/utils'

const props = defineProps({
  variant: { type: String, default: 'default' },
  class: { type: null, default: undefined }
})
</script>

<template>
  <span :class="cn(badgeVariants({ variant }), props.class)">
    <slot />
  </span>
</template>
