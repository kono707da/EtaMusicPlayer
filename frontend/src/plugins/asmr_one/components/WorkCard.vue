<script setup>
import { Badge } from '@/components/ui/badge'
import { coverUrl } from '../api'

defineProps({
  work: { type: Object, required: true }
})

const emit = defineEmits(['click'])

function formatNumber(n) {
  if (!n) return '0'
  if (n >= 10000) return (n / 10000).toFixed(1) + 'w'
  if (n >= 1000) return (n / 1000).toFixed(1) + 'k'
  return String(n)
}
</script>

<template>
  <div
    class="group cursor-pointer rounded-lg border border-border bg-card/40 overflow-hidden transition-all hover:border-primary/60 hover:shadow-lg"
    @click="emit('click', work.id)"
  >
    <div class="aspect-square relative overflow-hidden bg-muted">
      <img
        :src="coverUrl(work.id)"
        :alt="work.title"
        loading="lazy"
        class="absolute inset-0 h-full w-full object-cover transition-transform group-hover:scale-105"
      />
      <div class="absolute top-2 right-2 flex flex-col gap-1 items-end">
        <Badge v-if="work.nsfw" variant="destructive" class="text-[10px]">R18</Badge>
        <Badge variant="secondary" class="text-[10px]">{{ formatNumber(work.dl_count) }} DL</Badge>
      </div>
    </div>
    <div class="p-2.5">
      <div class="line-clamp-2 text-sm font-medium text-foreground min-h-[2.5rem]">{{ work.title }}</div>
      <div class="mt-1.5 flex items-center justify-between text-xs text-muted-foreground">
        <span class="truncate max-w-[60%]">{{ work.name || '—' }}</span>
        <span>★ {{ work.rate_average_2dp || '—' }}</span>
      </div>
      <div class="mt-1 text-[10px] text-muted-foreground">{{ work.release }}</div>
    </div>
  </div>
</template>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
