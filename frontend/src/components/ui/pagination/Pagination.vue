<script setup>
import { computed, ref } from 'vue'
import { ChevronLeft, ChevronRight } from 'lucide-vue-next'
import { Button } from '../button'
import { cn } from '@/lib/utils'

const props = defineProps({
  page: { type: Number, required: true },
  pageSize: { type: Number, default: 20 },
  total: { type: Number, default: 0 },
  showJump: { type: Boolean, default: true },
  class: { type: null, default: undefined }
})

const emit = defineEmits(['update:page', 'change'])

const totalPages = computed(() =>
  Math.max(1, Math.ceil(props.total / props.pageSize))
)

// 页码列表：当前页前后 2 页，超出用省略号
const pageList = computed(() => {
  const cur = props.page
  const total = totalPages.value
  const pages = []

  if (total <= 7) {
    for (let i = 1; i <= total; i++) pages.push(i)
    return pages
  }

  pages.push(1)
  const left = Math.max(2, cur - 2)
  const right = Math.min(total - 1, cur + 2)

  if (left > 2) pages.push('...')
  for (let i = left; i <= right; i++) pages.push(i)
  if (right < total - 1) pages.push('...')
  pages.push(total)

  return pages
})

function go(p) {
  if (p < 1 || p > totalPages.value || p === props.page) return
  emit('update:page', p)
  emit('change', p)
}

const jumpValue = ref('')

function onJump() {
  const n = parseInt(jumpValue.value, 10)
  if (!Number.isNaN(n)) {
    go(n)
    jumpValue.value = ''
  }
}
</script>

<template>
  <div
    :class="
      cn('flex flex-wrap items-center gap-2 text-sm text-muted-foreground', props.class)
    "
  >
    <span>共 {{ total }} 条</span>

    <Button
      variant="ghost"
      size="icon"
      class="h-9 w-9"
      :disabled="page <= 1"
      @click="go(page - 1)"
    >
      <ChevronLeft class="h-4 w-4" />
    </Button>

    <template v-for="(p, i) in pageList" :key="i">
      <span v-if="p === '...'" class="px-1 select-none">…</span>
      <Button
        v-else
        :variant="p === page ? 'gold' : 'ghost'"
        size="icon"
        class="h-9 w-9 text-xs"
        @click="go(p)"
      >
        {{ p }}
      </Button>
    </template>

    <Button
      variant="ghost"
      size="icon"
      class="h-9 w-9"
      :disabled="page >= totalPages"
      @click="go(page + 1)"
    >
      <ChevronRight class="h-4 w-4" />
    </Button>

    <template v-if="showJump">
      <span class="ml-2">前往</span>
      <input
        v-model="jumpValue"
        class="h-9 w-12 rounded-md border border-input bg-background px-2 text-sm text-center focus:outline-none focus:ring-1 focus:ring-ring"
        @keyup.enter="onJump"
      />
      <span>页</span>
    </template>
  </div>
</template>
