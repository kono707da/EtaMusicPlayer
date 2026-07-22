<script setup>
/**
 * 网易云搜索视图
 *
 * 依赖通过 window.__etamusic 取用（vue/vue-router/ui/icons/stores），
 * store 和 api 通过相对路径 import。
 */
const { ref, computed, onMounted, watch } = window.__etamusic.vue
const { useRoute, useRouter } = window.__etamusic.vueRouter
const {
  Search, Music, Loader2, Play, Plus, Flame, X, AlertCircle, Download
} = window.__etamusic.icons
const { Input, Button, Badge, Empty, useToast } = window.__etamusic.ui
const { usePlayerStore } = window.__etamusic.stores

import { useNeteaseStore } from '../store'
import { search, searchHot, buildPlayableTracks, downloadSongs } from '../api'

const route = useRoute()
const router = useRouter()
const toast = useToast()
const playerStore = usePlayerStore()
const neteaseStore = useNeteaseStore()

// 搜索框输入（独立于 route.query.q，支持输入时不立即触发）
const keywordInput = ref(route.query.q || '')

// 搜索结果
const loading = ref(false)
const result = ref({ songs: [], songCount: 0 })
const hotList = ref([])
const hotLoading = ref(false)

// 当前搜索关键词
const currentKeyword = computed(() => route.query.q || '')

// 防止重复获取播放 URL
const preparingIds = ref(new Set())
const downloadingIds = ref(new Set())

const hasResult = computed(() => result.value.songs.length > 0)

/**
 * 加载热搜词
 */
async function loadHot() {
  hotLoading.value = true
  try {
    const data = await searchHot()
    hotList.value = (data?.result?.hots || []).slice(0, 20)
  } catch (e) {
    // 静默失败，热搜不是关键功能
    hotList.value = []
  } finally {
    hotLoading.value = false
  }
}

/**
 * 执行搜索
 */
async function load() {
  const kw = currentKeyword.value
  if (!kw) {
    result.value = { songs: [], songCount: 0 }
    return
  }
  loading.value = true
  try {
    const offset = (Number(route.query.page) || 1) - 1
    const data = await search(kw, 1, 50, Math.max(0, offset) * 50)
    result.value = {
      songs: data?.result?.songs || [],
      songCount: data?.result?.songCount || 0
    }
  } catch (e) {
    toast.error('搜索失败：' + (e.message || '未知错误'))
    result.value = { songs: [], songCount: 0 }
  } finally {
    loading.value = false
  }
}

/**
 * 触发搜索（按钮/回车）
 */
function doSearch() {
  const k = keywordInput.value.trim()
  if (!k) {
    toast.error('请输入搜索关键词')
    return
  }
  if (k === currentKeyword.value) {
    // 关键词相同，直接重新加载
    load()
    return
  }
  router.push({ path: '/netease/search', query: { q: k, page: 1 } })
}

/**
 * 点击热搜词
 */
function searchHotWord(word) {
  keywordInput.value = word
  router.push({ path: '/netease/search', query: { q: word, page: 1 } })
}

/**
 * 清空搜索
 */
function clearSearch() {
  keywordInput.value = ''
  router.push({ path: '/netease/search' })
}

/**
 * 播放单首歌曲：构建 track 后立即播放
 */
async function playSong(song) {
  if (preparingIds.value.has(song.id)) return
  preparingIds.value.add(song.id)
  try {
    const tracks = await buildPlayableTracks([song], 'standard')
    if (tracks.length === 0) {
      toast.error(`「${song.name}」无可用播放源（VIP/版权限制）`)
      return
    }
    playerStore.playTracks(tracks, 0)
    toast.success(`正在播放：${song.name}`)
  } catch (e) {
    toast.error('播放失败：' + (e.message || '未知错误'))
  } finally {
    preparingIds.value.delete(song.id)
  }
}

/**
 * 播放全部搜索结果
 */
async function playAll() {
  if (!hasResult.value) return
  // 限制前 100 首，避免一次请求过多 URL
  const songs = result.value.songs.slice(0, 100)
  loading.value = true
  try {
    const tracks = await buildPlayableTracks(songs, 'standard')
    if (tracks.length === 0) {
      toast.error('当前搜索结果无可用播放源（VIP/版权限制）')
      return
    }
    playerStore.playTracks(tracks, 0)
    toast.success(`已加入播放队列：${tracks.length} 首`)
  } catch (e) {
    toast.error('加入播放队列失败：' + (e.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

/**
 * 追加单首到队列
 */
async function appendSong(song) {
  if (preparingIds.value.has(song.id)) return
  preparingIds.value.add(song.id)
  try {
    const tracks = await buildPlayableTracks([song], 'standard')
    if (tracks.length === 0) {
      toast.error(`「${song.name}」无可用播放源（VIP/版权限制）`)
      return
    }
    playerStore.appendTracks(tracks)
    toast.success(`已加入队列：${song.name}`)
  } catch (e) {
    toast.error('加入队列失败：' + (e.message || '未知错误'))
  } finally {
    preparingIds.value.delete(song.id)
  }
}

/**
 * 下载单首歌曲
 */
async function downloadSong(song) {
  if (downloadingIds.value.has(song.id)) return
  downloadingIds.value.add(song.id)
  try {
    const result = await downloadSongs([song.id], { level: 'exhigh' })
    toast.success(result.message || '下载任务已创建')
  } catch (e) {
    toast.error('下载失败：' + (e.message || '未知错误'))
  } finally {
    downloadingIds.value.delete(song.id)
  }
}

/**
 * 下载全部搜索结果
 */
async function downloadAll() {
  if (!hasResult.value) return
  const songs = result.value.songs.slice(0, 100)
  loading.value = true
  try {
    const ids = songs.map((s) => s.id)
    const result = await downloadSongs(ids, { level: 'exhigh' })
    toast.success(result.message || '下载任务已创建')
  } catch (e) {
    toast.error('下载失败：' + (e.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

/**
 * 格式化时长（秒 → mm:ss）
 */
function formatDuration(sec) {
  if (!sec || sec <= 0) return '--:--'
  const m = Math.floor(sec / 60)
  const s = Math.floor(sec % 60)
  return `${m}:${String(s).padStart(2, '0')}`
}

/**
 * 判断是否当前播放
 */
function isCurrentPlaying(song) {
  const cur = playerStore.currentTrack
  return cur && cur.id === song.id && cur.__source === 'netease'
}

// 监听 route.query.q 变化重新加载
watch(
  () => route.query,
  (q) => {
    if (q.q !== keywordInput.value) {
      keywordInput.value = q.q || ''
    }
    if (q.q) {
      load()
    } else {
      result.value = { songs: [], songCount: 0 }
    }
  },
  { deep: true }
)

onMounted(() => {
  if (!neteaseStore.loaded) {
    neteaseStore.load()
  }
  // 首次进入若无搜索词，加载热搜
  if (!currentKeyword.value) {
    loadHot()
  } else {
    load()
  }
})
</script>

<template>
  <div class="flex h-full flex-col gap-3">
    <!-- 顶部标题 -->
    <div class="flex items-center justify-between gap-3">
      <div class="flex items-center gap-2">
        <Music class="h-5 w-5 text-primary" />
        <h2 class="text-lg font-semibold tracking-tight">网易云搜索</h2>
        <Badge v-if="result.songCount" variant="outline" class="text-muted-foreground">
          共 {{ result.songCount }} 首
        </Badge>
      </div>
      <div class="flex items-center gap-2">
        <Button
          v-if="hasResult"
          variant="secondary"
          size="sm"
          :disabled="loading"
          @click="downloadAll"
        >
          <Download class="h-4 w-4" />
          下载全部
        </Button>
        <Button
          v-if="hasResult"
          variant="gold"
          size="sm"
          :disabled="loading"
          @click="playAll"
        >
          <Loader2 v-if="loading" class="h-4 w-4 animate-spin" />
          <Play v-else class="h-4 w-4" />
          播放全部
        </Button>
      </div>
    </div>

    <!-- 搜索栏 -->
    <div class="flex items-center gap-2">
      <div class="relative flex-1 max-w-2xl">
        <Search class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          v-model="keywordInput"
          placeholder="搜索歌曲、歌手、专辑..."
          class="h-9 pl-9 pr-9"
          @keyup.enter="doSearch"
        />
        <button
          v-if="keywordInput"
          class="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
          @click="keywordInput = ''"
        >
          <X class="h-4 w-4" />
        </button>
      </div>
      <Button variant="gold" size="sm" :disabled="loading" @click="doSearch">
        <Loader2 v-if="loading" class="h-4 w-4 animate-spin" />
        <Search v-else class="h-4 w-4" />
        搜索
      </Button>
      <Button v-if="currentKeyword" variant="ghost" size="sm" @click="clearSearch">
        <X class="h-4 w-4" />
        清空
      </Button>
    </div>

    <!-- 内容区 -->
    <div class="flex-1 min-h-0 overflow-auto">
      <!-- 加载中（首次加载） -->
      <div v-if="loading && !hasResult" class="flex h-full items-center justify-center text-muted-foreground">
        <Loader2 class="mr-2 h-5 w-5 animate-spin" />
        搜索中...
      </div>

      <!-- 无搜索词：显示热搜 -->
      <div v-else-if="!currentKeyword" class="flex flex-col gap-4">
        <div class="flex items-center gap-2 text-sm text-muted-foreground">
          <Flame class="h-4 w-4 text-primary" />
          热门搜索
        </div>
        <div v-if="hotLoading" class="flex items-center text-muted-foreground text-sm">
          <Loader2 class="mr-2 h-4 w-4 animate-spin" />
          加载中...
        </div>
        <div v-else-if="hotList.length === 0" class="text-sm text-muted-foreground">
          暂无热搜
        </div>
        <div v-else class="flex flex-wrap gap-2">
          <Badge
            v-for="(h, i) in hotList"
            :key="h.first"
            variant="outline"
            class="cursor-pointer px-3 py-1.5 text-sm hover:bg-accent"
            @click="searchHotWord(h.first)"
          >
            <span class="text-muted-foreground mr-1.5">{{ i + 1 }}.</span>
            {{ h.first }}
          </Badge>
        </div>
      </div>

      <!-- 无结果 -->
      <Empty
        v-else-if="!hasResult"
        :icon="AlertCircle"
        title="没有找到相关歌曲"
        description="试试其他关键词"
        class="h-full"
      />

      <!-- 搜索结果列表 -->
      <div v-else class="flex flex-col gap-1 pb-4">
        <div
          v-for="(song, idx) in result.songs"
          :key="song.id"
          class="group flex items-center gap-3 px-3 py-2 rounded-md cursor-pointer transition-colors hover:bg-accent/50"
          :class="{ 'bg-primary/10': isCurrentPlaying(song) }"
          @dblclick="playSong(song)"
        >
          <!-- 序号 / 播放按钮 -->
          <div class="w-8 h-8 flex items-center justify-center shrink-0">
            <Loader2
              v-if="preparingIds.has(song.id)"
              class="h-4 w-4 animate-spin text-muted-foreground"
            />
            <button
              v-else
              class="opacity-0 group-hover:opacity-100 transition-opacity"
              :class="{ '!opacity-100': isCurrentPlaying(song) }"
              @click.stop="playSong(song)"
            >
              <Play
                class="h-4 w-4"
                :class="isCurrentPlaying(song) ? 'text-primary' : 'text-foreground'"
              />
            </button>
            <span
              v-if="!preparingIds.has(song.id) && !isCurrentPlaying(song)"
              class="text-sm text-muted-foreground group-hover:hidden"
            >{{ idx + 1 }}</span>
          </div>

          <!-- 封面 -->
          <img
            v-if="song.al?.picUrl"
            :src="song.al.picUrl"
            :alt="song.name"
            class="h-10 w-10 rounded object-cover shrink-0"
            referrerpolicy="no-referrer"
            loading="lazy"
          />
          <div v-else class="h-10 w-10 rounded bg-muted flex items-center justify-center shrink-0">
            <Music class="h-4 w-4 text-muted-foreground" />
          </div>

          <!-- 标题 / 艺术家 -->
          <div class="flex-1 min-w-0 flex flex-col gap-0.5">
            <div class="text-sm font-medium truncate" :title="song.name">
              {{ song.name }}
              <span v-if="song.alia?.length" class="text-muted-foreground text-xs ml-1">
                ({{ song.alia[0] }})
              </span>
            </div>
            <div class="text-xs text-muted-foreground truncate">
              {{ (song.ar || []).map((a) => a.name).join(' / ') || '未知艺术家' }}
              <span v-if="song.al?.name" class="mx-1">·</span>
              <span v-if="song.al?.name" class="truncate">{{ song.al.name }}</span>
            </div>
          </div>

          <!-- 时长 -->
          <div class="text-xs text-muted-foreground shrink-0 hidden sm:block">
            {{ formatDuration(Math.floor((song.dt || 0) / 1000)) }}
          </div>

          <!-- 操作按钮 -->
          <div class="flex items-center gap-1 shrink-0">
            <Button
              variant="ghost"
              size="sm"
              class="h-8 w-8 p-0"
              :disabled="downloadingIds.has(song.id)"
              title="下载"
              @click.stop="downloadSong(song)"
            >
              <Loader2 v-if="downloadingIds.has(song.id)" class="h-4 w-4 animate-spin" />
              <Download v-else class="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              class="h-8 w-8 p-0"
              :disabled="preparingIds.has(song.id)"
              title="加入队列"
              @click.stop="appendSong(song)"
            >
              <Plus class="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
