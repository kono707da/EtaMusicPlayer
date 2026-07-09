<script>
import { cva } from 'class-variance-authority'

export const alertVariants = cva(
  'relative w-full rounded-lg border p-4',
  {
    variants: {
      variant: {
        default: 'bg-card text-card-foreground border-border',
        destructive:
          'border-destructive/50 text-destructive bg-destructive/10 [&>svg]:text-destructive'
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
  <div :class="cn(alertVariants({ variant }), props.class)" role="alert">
    <slot />
  </div>
</template>
