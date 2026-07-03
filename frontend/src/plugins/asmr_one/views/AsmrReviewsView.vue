<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowLeft, Star, Loader2, Trash2, RefreshCw } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Empty } from '@/components/ui/empty'
import { useToast } from '@/components/ui/toast/use-toast'
import { coverUrl, listReviews, deleteReview } from '../api'
import { useAsmrAccountStore } from '../store'

const router = useRouter()
const toast = useToast()
const account = useAsmrAccountStore()

const reviews = ref([])
const loading = ref(false)
const page = ref(1)
const total = ref(0)

async function load() {
  if (!account.isLoggedIn) {
    router.push('/asmr/account')
    return
  }
  loading.value = true
  try {
    const data = await listReviews('create_date', 'desc', page.value)
    reviews.value = data.reviews || data.works || []
    total.value = data.pagination?.totalCount || reviews.value.length
  } catch (e) {
    toast.error('加载失败', e?.response?.data?.detail || e.message)
  } finally {
    loading.value = false
  }
}

async function onDelete(review) {
  const workId = review.work_id || review.id
  try {
    await deleteReview(workId)
    toast.success('已删除评价')
    await load()
  } catch (e) {
    toast.error('删除失败', e?.response?.data?.detail || e.message)
  }
}

function openWork(workId) {
  router.push(`/asmr/work/${workId}`)
}

function formatTime(s) {
  if (!s) return '--'
  try {
    return new Date(s).toLocaleString('zh-CN', { hour12: false })
  } catch {
    return s
  }
}

onMounted(() => {
  if (!account.loaded) account.load().then(load)
  else load()
})
</script>

<template>
  <div class="flex h-full flex-col gap-4">
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-3">
        <Button variant="ghost" size="sm" @click="router.push('/asmr')">
          <ArrowLeft class="h-4 w-4" />
          返回
        </Button>
        <h2 class="text-lg font-semibold">我的评价</h2>
        <Badge variant="outline" class="text-xs">共 {{ total }} 条</Badge>
      </div>
      <Button variant="ghost" size="sm" :disabled="loading" @click="load">
        <RefreshCw class="h-4 w-4" :class="{ 'animate-spin': loading }" />
        刷新
      </Button>
    </div>

    <div class="flex-1 min-h-0 overflow-auto">
      <div v-if="loading && reviews.length === 0" class="flex items-center justify-center py-12 text-muted-foreground">
        <Loader2 class="mr-2 h-5 w-5 animate-spin" />
        加载中...
      </div>

      <Empty
        v-else-if="reviews.length === 0"
        :icon="Star"
        title="还没有评价"
        description="在作品详情页可以给作品打分评价"
        class="h-full"
      >
        <Button variant="gold" @click="router.push('/asmr')">去浏览</Button>
      </Empty>

      <div v-else class="flex flex-col gap-2 pb-4">
        <div
          v-for="r in reviews"
          :key="r.id || r.work_id"
          class="flex gap-3 rounded-lg border border-border bg-card/40 p-3"
        >
          <img
            v-if="r.work_id || r.id"
            :src="coverUrl(r.work_id || r.id)"
            class="h-20 w-20 rounded-md object-cover border border-border shrink-0 cursor-pointer"
            @click="openWork(r.work_id || r.id)"
          />
          <div class="flex-1 min-w-0 flex flex-col gap-1">
            <div class="flex items-center gap-2">
              <span class="text-sm font-medium text-foreground truncate">
                {{ r.work_title || r.title || ('#' + (r.work_id || r.id)) }}
              </span>
              <Badge variant="gold" class="shrink-0">
                <Star class="h-3 w-3" />
                {{ r.rating }}
              </Badge>
            </div>
            <div v-if="r.review_text" class="text-sm text-muted-foreground line-clamp-3">
              {{ r.review_text }}
            </div>
            <div class="flex items-center justify-between mt-auto">
              <span class="text-xs text-muted-foreground">{{ formatTime(r.create_date || r.updated_at) }}</span>
              <Button
                variant="ghost"
                size="sm"
                class="text-destructive h-7"
                @click="onDelete(r)"
              >
                <Trash2 class="h-3 w-3" />
                删除
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.line-clamp-3 {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
