<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowLeft, Flame, Sparkles, Loader2 } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem
} from '@/components/ui/select'
import { useToast } from '@/components/ui/toast/use-toast'
import WorkGrid from '../components/WorkGrid.vue'
import { getPopular, getRecommendations } from '../api'
import { useAsmrAccountStore } from '../store'

const router = useRouter()
const toast = useToast()
const account = useAsmrAccountStore()

const PAGE_SIZE_OPTIONS = [24, 30, 60, 120]

const tab = ref('popular') // popular | recommendations
const works = ref([])
const loading = ref(false)
const page = ref(1)
const pageSize = ref(30)
const totalPage = ref(1)

async function load() {
  loading.value = true
  try {
    const data =
      tab.value === 'popular'
        ? await getPopular(page.value, pageSize.value)
        : await getRecommendations(page.value, pageSize.value)
    works.value = data.works || []
    totalPage.value = data.pagination?.totalPage || 1
  } catch (e) {
    toast.error('加载失败', e?.response?.data?.detail || e.message, e)
    works.value = []
  } finally {
    loading.value = false
  }
}

function switchTab(t) {
  if (tab.value === t) return
  if (t === 'recommendations' && !account.isLoggedIn) {
    toast.warning('个性化推荐需要登录')
    router.push('/asmr/account')
    return
  }
  tab.value = t
  page.value = 1
  load()
}

function onPageSizeChange(v) {
  pageSize.value = Number(v)
  page.value = 1
  load()
}

function goPage(p) {
  page.value = p
  load()
}

onMounted(() => {
  if (!account.loaded) account.load()
  load()
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
        <Flame class="h-5 w-5 text-primary" />
        <h2 class="text-lg font-semibold">推荐</h2>
      </div>
      <div class="flex items-center gap-2">
        <Select :model-value="String(pageSize)" @update:model-value="onPageSizeChange">
          <SelectTrigger class="h-9 w-[90px]">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem v-for="n in PAGE_SIZE_OPTIONS" :key="n" :value="String(n)">
              {{ n }}/页
            </SelectItem>
          </SelectContent>
        </Select>
        <Button
          :variant="tab === 'popular' ? 'gold' : 'ghost'"
          size="sm"
          @click="switchTab('popular')"
        >
          <Flame class="h-4 w-4" />
          热门
        </Button>
        <Button
          :variant="tab === 'recommendations' ? 'gold' : 'ghost'"
          size="sm"
          @click="switchTab('recommendations')"
        >
          <Sparkles class="h-4 w-4" />
          个性化
          <Badge v-if="!account.isLoggedIn" variant="outline" class="ml-1 text-[10px]">需登录</Badge>
        </Button>
      </div>
    </div>

    <WorkGrid :works="works" :loading="loading" />

    <div
      v-if="works.length > 0 && totalPage > 1"
      class="flex items-center justify-center gap-2 py-2"
    >
      <Button variant="ghost" size="sm" :disabled="page <= 1 || loading" @click="goPage(page - 1)">
        上一页
      </Button>
      <span class="text-sm text-muted-foreground">{{ page }} / {{ totalPage }}</span>
      <Button
        variant="ghost"
        size="sm"
        :disabled="page >= totalPage || loading"
        @click="goPage(page + 1)"
      >
        下一页
      </Button>
    </div>
  </div>
</template>
