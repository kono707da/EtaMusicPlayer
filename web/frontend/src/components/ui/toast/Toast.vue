<script setup>
import { CheckCircle2, XCircle, AlertTriangle, Info, X } from 'lucide-vue-next'
import { cn } from '@/lib/utils'

const props = defineProps({
  type: { type: String, default: 'default' },
  title: { type: String, default: '' },
  description: { type: String, default: '' },
  class: { type: null, default: undefined }
})

const emit = defineEmits(['close'])

const iconMap = {
  success: CheckCircle2,
  error: XCircle,
  warning: AlertTriangle,
  info: Info,
  default: Info
}

const accentMap = {
  success: 'border-l-emerald-500',
  error: 'border-l-red-500',
  warning: 'border-l-amber-500',
  info: 'border-l-primary',
  default: 'border-l-border'
}

const iconColorMap = {
  success: 'text-emerald-400',
  error: 'text-red-400',
  warning: 'text-amber-400',
  info: 'text-primary',
  default: 'text-muted-foreground'
}
</script>

<template>
  <div
    :class="
      cn(
        'flex items-start gap-3 rounded-md border border-l-4 bg-popover p-4 shadow-lg min-w-[280px] animate-fade-in',
        accentMap[type],
        props.class
      )
    "
    role="status"
  >
    <component
      :is="iconMap[type] || Info"
      class="h-5 w-5 mt-0.5 shrink-0"
      :class="iconColorMap[type]"
    />
    <div class="flex-1 min-w-0">
      <div v-if="title" class="text-sm font-medium text-foreground">
        {{ title }}
      </div>
      <div v-if="description" class="text-sm text-muted-foreground mt-0.5">
        {{ description }}
      </div>
    </div>
    <button
      class="shrink-0 text-muted-foreground transition-colors hover:text-foreground focus:outline-none"
      @click="emit('close')"
    >
      <X class="h-4 w-4" />
    </button>
  </div>
</template>
