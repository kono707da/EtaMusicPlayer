<script setup>
import { useRouter } from 'vue-router'
import WorkCard from './WorkCard.vue'
import { Empty } from '@/components/ui/empty'
import { Headphones } from 'lucide-vue-next'

defineProps({
  works: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false }
})

const router = useRouter()

function openWork(id) {
  router.push(`/asmr/work/${id}`)
}
</script>

<template>
  <div class="flex-1 min-h-0 overflow-auto">
    <div v-if="loading" class="flex h-full items-center justify-center text-muted-foreground">
      <div class="h-6 w-6 border-2 border-primary border-t-transparent rounded-full animate-spin mr-2" />
      加载中...
    </div>

    <Empty
      v-else-if="works.length === 0"
      :icon="Headphones"
      title="没有找到作品"
      class="h-full"
    />

    <div v-else class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4 pb-4">
      <WorkCard
        v-for="w in works"
        :key="w.id"
        :work="w"
        @click="openWork"
      />
    </div>
  </div>
</template>
