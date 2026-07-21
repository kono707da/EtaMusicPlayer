<script setup>
const { ref, computed, watch, onMounted } = window.__etamusic.vue
const { useRouter, useRoute } = window.__etamusic.vueRouter
const { Input, Button, Badge, Empty, useToast } = window.__etamusic.ui
const {
  Select, SelectTrigger, SelectValue, SelectContent, SelectItem
} = window.__etamusic.ui
const {
  Search, Headphones, Download, Settings, Loader2,
  Tag, Mic2, Users, X, Home, Captions
} = window.__etamusic.icons
import {
  coverUrl,
  searchWorks,
  listWorks,
  listByTag,
  listByVa,
  listByCircle
} from '../api'
import {
  PRESET_TAGS,
  getRecentTags,
  getRecentVas,
  getRecentCircles
} from '../history'

const router = useRouter()
const route = useRoute()
const toast = useToast()

// 排序选项
const ORDER_OPTIONS = [
  { value: 'create_date', label: '最新收录' },
  { value: 'release', label: '发售日' },
  { value: 'dl_count', label: '销量' },
  { value: 'rate_average_2dp', label: '评分' },
  { value: 'review_count', label: '评价数' },
  { value: 'price', label: '价格' }
]

// 每页数量选项
const PAGE_SIZE_OPTIONS = [24, 30, 60, 120]

// 跳页步长选项
const JUMP_STEP_OPTIONS = [3, 5, 10, 20]

// 搜索栏输入（独立于 route.query.q）
const keywordInput = ref('')

// 排序参数（独立于 route，但会反映到 query）
const orderBy = ref(route.query.orderBy || 'create_date')
const sortDir = ref(route.query.sort || 'desc')

// 分页
const page = ref(Number(route.query.page) || 1)
const pageSize = ref(Number(route.query.pageSize) || 30)

// 仅看字幕
const subtitleOnly = ref(Number(route.query.subtitle) === 1)

// 跳页
const jumpStep = ref(5)
const jumpInput = ref('')

// 数据
const loading = ref(false)
const result = ref({
  works: [],
  pagination: { totalCount: 0, currentPage: 1, totalPage: 1 }
})

// 侧边栏最近访问
const recentTags = ref([])
const recentVas = ref([])
const recentCircles = ref([])

// 当前模式
const mode = computed(() => {
  if (route.query.q) return 'search'
  if (route.query.tag) return 'tag'
  if (route.query.va) return 'va'
  if (route.query.circle) return 'circle'
  return 'home'
})

const currentFilterLabel = computed(() => {
  switch (mode.value) {
    case 'search':
      return `关键词: ${route.query.q}`
    case 'tag':
      return `标签: ${route.query.tagName || route.query.tag}`
    case 'va':
      return `声优: ${route.query.vaName || route.query.va}`
    case 'circle':
      return `社团: ${route.query.circleName || route.query.circle}`
    default:
      return '全部作品'
  }
})

const hasResult = computed(() => result.value.works.length > 0)

// 标签是否被选中
function isTagActive(tagId) {
  return mode.value === 'tag' && String(route.query.tag) === String(tagId)
}

// 加载数据
async function load() {
  loading.value = true
  try {
    let data
    const m = mode.value
    const sub = subtitleOnly.value ? 1 : 0
    if (m === 'search') {
      data = await searchWorks(
        route.query.q,
        page.value,
        pageSize.value,
        orderBy.value,
        sortDir.value,
        sub
      )
    } else if (m === 'tag') {
      data = await listByTag(
        Number(route.query.tag),
        page.value,
        pageSize.value,
        orderBy.value,
        sortDir.value,
        sub
      )
    } else if (m === 'va') {
      data = await listByVa(
        route.query.va,
        page.value,
        pageSize.value,
        orderBy.value,
        sortDir.value,
        sub
      )
    } else if (m === 'circle') {
      data = await listByCircle(
        Number(route.query.circle),
        page.value,
        pageSize.value,
        orderBy.value,
        sortDir.value,
        sub
      )
    } else {
      data = await listWorks(
        page.value,
        pageSize.value,
        orderBy.value,
        sortDir.value,
        sub
      )
    }
    result.value = data
  } catch (e) {
    toast.error('加载失败', e?.response?.data?.detail || e.message, e)
    result.value = { works: [], pagination: { totalCount: 0, totalPage: 1 } }
  } finally {
    loading.value = false
  }
}

// 搜索
function doSearch() {
  const k = keywordInput.value.trim()
  const sub = subtitleOnly.value ? 1 : undefined
  if (!k) {
    router.push({ path: '/asmr', query: { ...(sub ? { subtitle: sub } : {}), orderBy: orderBy.value, sort: sortDir.value, page: 1 } })
    return
  }
  router.push({
    path: '/asmr',
    query: { q: k, orderBy: orderBy.value, sort: sortDir.value, page: 1, ...(sub ? { subtitle: sub } : {}) }
  })
}

function onSearchEnter() {
  doSearch()
}

// 切换标签/声优/社团
function filterByTag(tag) {
  const sub = subtitleOnly.value ? 1 : undefined
  router.push({
    path: '/asmr',
    query: { tag: tag.id, tagName: tag.name, orderBy: orderBy.value, sort: sortDir.value, page: 1, ...(sub ? { subtitle: sub } : {}) }
  })
}

function filterByVa(va) {
  const sub = subtitleOnly.value ? 1 : undefined
  router.push({
    path: '/asmr',
    query: { va: va.id, vaName: va.name, orderBy: orderBy.value, sort: sortDir.value, page: 1, ...(sub ? { subtitle: sub } : {}) }
  })
}

function filterByCircle(circle) {
  const sub = subtitleOnly.value ? 1 : undefined
  router.push({
    path: '/asmr',
    query: { circle: circle.id, circleName: circle.name, orderBy: orderBy.value, sort: sortDir.value, page: 1, ...(sub ? { subtitle: sub } : {}) }
  })
}

function goHome() {
  const sub = subtitleOnly.value ? 1 : undefined
  router.push({
    path: '/asmr',
    query: { orderBy: orderBy.value, sort: sortDir.value, page: 1, ...(sub ? { subtitle: sub } : {}) }
  })
}

function clearFilter() {
  goHome()
}

function goPage(p) {
  const q = { ...route.query, page: p }
  router.push({ path: '/asmr', query: q })
}

function clampPage(p, total) {
  if (!total || total < 1) return 1
  p = Math.floor(Number(p))
  if (!Number.isFinite(p) || p < 1) return 1
  if (p > total) return total
  return p
}

function jumpForward() {
  const total = result.value.pagination?.totalPage || 1
  goPage(clampPage(page.value + jumpStep.value, total))
}

function jumpBackward() {
  const total = result.value.pagination?.totalPage || 1
  goPage(clampPage(page.value - jumpStep.value, total))
}

function onJumpSubmit() {
  const v = Number(jumpInput.value)
  if (!Number.isFinite(v) || v < 1) {
    jumpInput.value = ''
    return
  }
  const total = result.value.pagination?.totalPage || 1
  goPage(clampPage(v, total))
  jumpInput.value = ''
}

function onOrderByChange(v) {
  orderBy.value = v
  const q = { ...route.query, orderBy: v, page: 1 }
  router.push({ path: '/asmr', query: q })
}

function onSortDirChange(v) {
  sortDir.value = v
  const q = { ...route.query, sort: v, page: 1 }
  router.push({ path: '/asmr', query: q })
}

function onPageSizeChange(v) {
  pageSize.value = v
  const q = { ...route.query, pageSize: v, page: 1 }
  router.push({ path: '/asmr', query: q })
}

function onSubtitleToggle() {
  subtitleOnly.value = !subtitleOnly.value
  const q = { ...route.query, page: 1 }
  if (subtitleOnly.value) {
    q.subtitle = 1
  } else {
    delete q.subtitle
  }
  router.push({ path: '/asmr', query: q })
}

function openWork(id) {
  router.push(`/asmr/work/${id}`)
}

function goDownloads() {
  router.push('/asmr/downloads')
}

function goSettings() {
  router.push('/asmr/settings')
}

// 监听 route 变化重新加载
watch(
  () => route.query,
  (q) => {
    orderBy.value = q.orderBy || 'create_date'
    sortDir.value = q.sort || 'desc'
    page.value = Number(q.page) || 1
    pageSize.value = Number(q.pageSize) || 30
    subtitleOnly.value = Number(q.subtitle) === 1
    if (q.q) keywordInput.value = q.q
    load()
  },
  { deep: true }
)

function formatNumber(n) {
  if (!n) return '0'
  if (n >= 10000) return (n / 10000).toFixed(1) + 'w'
  if (n >= 1000) return (n / 1000).toFixed(1) + 'k'
  return String(n)
}

onMounted(() => {
  recentTags.value = getRecentTags()
  recentVas.value = getRecentVas()
  recentCircles.value = getRecentCircles()
  if (route.query.q) keywordInput.value = route.query.q
  load()
})
</script>

<template>
  <div class="flex h-full gap-4">
    <!-- 侧边栏 -->
    <aside class="hidden md:flex w-56 shrink-0 flex-col gap-4 overflow-y-auto pb-4">
      <!-- 首页 -->
      <div>
        <Button
          :variant="mode === 'home' ? 'gold' : 'ghost'"
          size="sm"
          class="w-full justify-start"
          @click="goHome"
        >
          <Home class="h-4 w-4" />
          全部作品
        </Button>
      </div>

      <!-- 预设标签 -->
      <div class="flex flex-col gap-1.5">
        <div class="flex items-center gap-1.5 text-xs font-medium text-muted-foreground px-1">
          <Tag class="h-3 w-3" />
          热门标签
        </div>
        <div class="flex flex-wrap gap-1">
          <Badge
            v-for="t in PRESET_TAGS"
            :key="t.id"
            :variant="isTagActive(t.id) ? 'default' : 'outline'"
            class="cursor-pointer text-xs"
            @click="filterByTag(t)"
          >
            {{ t.name }}
          </Badge>
        </div>
      </div>

      <!-- 最近访问的标签 -->
      <div v-if="recentTags.length > 0" class="flex flex-col gap-1.5">
        <div class="flex items-center gap-1.5 text-xs font-medium text-muted-foreground px-1">
          <Tag class="h-3 w-3" />
          最近访问的标签
        </div>
        <div class="flex flex-wrap gap-1">
          <Badge
            v-for="t in recentTags"
            :key="t.id"
            :variant="isTagActive(t.id) ? 'default' : 'outline'"
            class="cursor-pointer text-xs"
            @click="filterByTag(t)"
          >
            {{ t.name }}
          </Badge>
        </div>
      </div>

      <!-- 最近访问的声优 -->
      <div v-if="recentVas.length > 0" class="flex flex-col gap-1.5">
        <div class="flex items-center gap-1.5 text-xs font-medium text-muted-foreground px-1">
          <Mic2 class="h-3 w-3" />
          最近访问的声优
        </div>
        <div class="flex flex-col gap-1">
          <button
            v-for="v in recentVas"
            :key="v.id"
            class="text-left text-xs px-2 py-1 rounded hover:bg-accent truncate"
            :class="mode === 'va' && route.query.va === v.id ? 'bg-accent text-foreground' : 'text-muted-foreground'"
            @click="filterByVa(v)"
          >
            {{ v.name }}
          </button>
        </div>
      </div>

      <!-- 最近访问的社团 -->
      <div v-if="recentCircles.length > 0" class="flex flex-col gap-1.5">
        <div class="flex items-center gap-1.5 text-xs font-medium text-muted-foreground px-1">
          <Users class="h-3 w-3" />
          最近访问的社团
        </div>
        <div class="flex flex-col gap-1">
          <button
            v-for="c in recentCircles"
            :key="c.id"
            class="text-left text-xs px-2 py-1 rounded hover:bg-accent truncate"
            :class="mode === 'circle' && String(route.query.circle) === String(c.id) ? 'bg-accent text-foreground' : 'text-muted-foreground'"
            @click="filterByCircle(c)"
          >
            {{ c.name }}
          </button>
        </div>
      </div>
    </aside>

    <!-- 主区域 -->
    <div class="flex-1 min-w-0 flex flex-col gap-3">
      <!-- 顶部标题栏 -->
      <div class="flex items-center justify-between gap-3">
        <div class="flex items-center gap-2">
          <Headphones class="h-5 w-5 text-primary" />
          <h2 class="text-lg font-semibold tracking-tight text-foreground">ASMR 资源</h2>
          <Badge variant="outline" class="ml-1 text-muted-foreground">asmr.one</Badge>
        </div>
        <div class="flex items-center gap-2">
          <Button variant="ghost" size="sm" @click="goDownloads">
            <Download class="h-4 w-4" />
            下载任务
          </Button>
          <Button variant="ghost" size="sm" @click="goSettings">
            <Settings class="h-4 w-4" />
            设置
          </Button>
        </div>
      </div>

      <!-- 搜索栏 + 排序 -->
      <div class="flex flex-wrap items-center gap-2">
        <div class="relative flex-1 min-w-[200px] max-w-xl">
          <Search class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            v-model="keywordInput"
            placeholder="搜索关键词（如：asmr、催眠、耳语）..."
            class="h-9 pl-9"
            @keyup.enter="onSearchEnter"
          />
        </div>
        <Button variant="gold" size="sm" :disabled="loading" @click="onSearchEnter">
          <Loader2 v-if="loading" class="h-4 w-4 animate-spin" />
          搜索
        </Button>

        <div class="flex items-center gap-1.5 ml-auto">
          <Select :model-value="orderBy" @update:model-value="onOrderByChange">
            <SelectTrigger class="h-9 w-[120px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem v-for="o in ORDER_OPTIONS" :key="o.value" :value="o.value">
                {{ o.label }}
              </SelectItem>
            </SelectContent>
          </Select>
          <Select :model-value="sortDir" @update:model-value="onSortDirChange">
            <SelectTrigger class="h-9 w-[80px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="desc">降序</SelectItem>
              <SelectItem value="asc">升序</SelectItem>
            </SelectContent>
          </Select>
          <Select :model-value="String(pageSize)" @update:model-value="(v) => onPageSizeChange(Number(v))">
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
            :variant="subtitleOnly ? 'gold' : 'outline'"
            size="sm"
            class="h-9 gap-1.5"
            :title="subtitleOnly ? '当前仅显示含字幕作品，点击取消' : '仅显示含字幕作品'"
            @click="onSubtitleToggle"
          >
            <Captions class="h-4 w-4" />
            字幕
          </Button>
        </div>
      </div>

      <!-- 当前筛选条件 -->
      <div v-if="mode !== 'home' || subtitleOnly" class="flex items-center gap-2 text-sm flex-wrap">
        <span class="text-muted-foreground">当前筛选:</span>
        <Badge v-if="mode !== 'home'" variant="gold" class="gap-1">
          {{ currentFilterLabel }}
          <button class="ml-0.5 hover:bg-primary/20 rounded" @click="clearFilter">
            <X class="h-3 w-3" />
          </button>
        </Badge>
        <Badge v-if="subtitleOnly" variant="gold" class="gap-1">
          <Captions class="h-3 w-3" />
          含字幕
          <button class="ml-0.5 hover:bg-primary/20 rounded" @click="onSubtitleToggle">
            <X class="h-3 w-3" />
          </button>
        </Badge>
        <span v-if="result.pagination?.totalCount" class="text-xs text-muted-foreground">
          (共 {{ formatNumber(result.pagination.totalCount) }} 个作品)
        </span>
      </div>

      <!-- 结果 -->
      <div class="flex-1 min-h-0 overflow-auto">
        <div v-if="loading && !hasResult" class="flex h-full items-center justify-center text-muted-foreground">
          <Loader2 class="mr-2 h-5 w-5 animate-spin" />
          加载中...
        </div>

        <Empty
          v-else-if="!hasResult"
          :icon="Headphones"
          title="没有找到作品"
          description="试试其他关键词或筛选条件"
          class="h-full"
        />

        <div v-else class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4 pb-4">
          <div
            v-for="w in result.works"
            :key="w.id"
            class="group cursor-pointer rounded-lg border border-border bg-card/40 overflow-hidden transition-all hover:border-primary/60 hover:shadow-lg"
            @click="openWork(w.id)"
          >
            <div class="aspect-square relative overflow-hidden bg-muted">
              <img
                :src="coverUrl(w.id)"
                :alt="w.title"
                loading="lazy"
                class="absolute inset-0 h-full w-full object-cover transition-transform group-hover:scale-105"
              />
              <div class="absolute top-2 right-2 flex flex-col gap-1 items-end">
                <Badge v-if="w.nsfw" variant="destructive" class="text-[10px]">R18</Badge>
                <Badge variant="secondary" class="text-[10px]">{{ formatNumber(w.dl_count) }} DL</Badge>
              </div>
            </div>
            <div class="p-2.5">
              <div class="line-clamp-2 text-sm font-medium text-foreground min-h-[2.5rem]">{{ w.title }}</div>
              <div class="mt-1.5 flex items-center justify-between text-xs text-muted-foreground">
                <span class="truncate max-w-[60%]">{{ w.name || '—' }}</span>
                <span>★ {{ w.rate_average_2dp || '—' }}</span>
              </div>
              <div class="mt-1 text-[10px] text-muted-foreground">{{ w.release }}</div>
            </div>
          </div>
        </div>

        <!-- 分页 -->
        <div
          v-if="hasResult && result.pagination && result.pagination.totalPage > 1"
          class="flex flex-wrap items-center justify-center gap-2 py-4"
        >
          <Select :model-value="String(jumpStep)" @update:model-value="(v) => (jumpStep = Number(v))">
            <SelectTrigger class="h-8 w-[70px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem v-for="n in JUMP_STEP_OPTIONS" :key="n" :value="String(n)">
                {{ n }}页
              </SelectItem>
            </SelectContent>
          </Select>
          <Button
            variant="outline"
            size="sm"
            class="h-8"
            :disabled="page <= 1 || loading"
            :title="`后退 ${jumpStep} 页`"
            @click="jumpBackward"
          >
            «{{ jumpStep }}
          </Button>
          <Button variant="ghost" size="sm" class="h-8" :disabled="page <= 1 || loading" @click="goPage(page - 1)">
            上一页
          </Button>
          <div class="flex items-center gap-1.5">
            <Input
              v-model="jumpInput"
              type="number"
              min="1"
              :max="result.pagination.totalPage"
              :placeholder="String(page)"
              class="h-8 w-16 text-center"
              @keyup.enter="onJumpSubmit"
            />
            <span class="text-sm text-muted-foreground">/ {{ result.pagination.totalPage }}</span>
            <Button variant="outline" size="sm" class="h-8" :disabled="loading" @click="onJumpSubmit">
              跳转
            </Button>
          </div>
          <Button
            variant="ghost"
            size="sm"
            class="h-8"
            :disabled="page >= result.pagination.totalPage || loading"
            @click="goPage(page + 1)"
          >
            下一页
          </Button>
          <Button
            variant="outline"
            size="sm"
            class="h-8"
            :disabled="page >= result.pagination.totalPage || loading"
            :title="`前进 ${jumpStep} 页`"
            @click="jumpForward"
          >
            {{ jumpStep }}»
          </Button>
          <span class="ml-1 text-xs text-muted-foreground">
            (共 {{ formatNumber(result.pagination.totalCount) }} 个作品)
          </span>
        </div>
      </div>
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
