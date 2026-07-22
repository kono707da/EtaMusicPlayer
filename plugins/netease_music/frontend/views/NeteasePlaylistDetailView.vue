<script setup>
/**
 * 网易云歌单详情视图
 *
 * 依赖通过 window.__etamusic 取用。
 */
const { ref, computed, onMounted, watch } = window.__etamusic.vue
const { useRoute, useRouter } = window.__etamusic.vueRouter
const {
  ArrowLeft, Music, Loader2, Play, Plus, Clock, ListMusic, AlertCircle, Download
} = window.__etamusic.icons
const { Button, Badge, Empty, useToast } = window.__etamusic.ui
const { usePlayerStore } = window.__etamusic.stores

import { getPlaylistDetail, buildPlayableTracks, downloadSongs } from '../api'

const route = useRoute()
const router = useRouter()
const toast = useToast()
const playerStore = usePlayerStore()

const playlistId = computed(() => Number(route.params.id))

// 歌单信息
const playlist = ref(null)
// 曲目列表（网易云原始结构）
const songs = ref([])
const loading = ref(false)
const playingAll = ref(false)
const preparingIds = ref(new Set())
const downloadingIds = ref(new Set())
const downloadingAll = ref(false)

const hasSongs = computed(() => songs.value.length > 0)

/**
 * 加载歌单详情和曲目列表
 */
async function load() {
  if (!playlistId.value) return
  loading.value = true
  playlist.value = null
  songs.value = []
  try {
    const data = await getPlaylistDetail(playlistId.value)
    const pl = data?.playlist
    if (!pl) {
      toast.error('歌单不存在或已被删除')
      return
    }
    playlist.value = pl
    songs.value = pl.tracks || []
  } catch (e) {
    toast.error('加载歌单失败：' + (e.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

/**
 * 播放全部
 */
async function playAll() {
  if (!hasSongs.value) return
  if (playerStore.queue.value.length > 0 && playerStore.currentTrack?.__source === 'netease'
      && playerStore.queue.value.every((q) => q.track.__source === 'netease')
      && playerStore.queue.value.length === songs.value.length) {
    // 队列已是当前歌单：切换为从头开始
    playerStore.jumpTo(0)
    return
  }
  playingAll.value = true
  try {
    // 限制前 200 首，避免一次请求过多 URL（网易云批量接口有上限）
    const list = songs.value.slice(0, 200)
    const tracks = await buildPlayableTracks(list, 'standard')
    if (tracks.length === 0) {
      toast.error('当前歌单无可用播放源（VIP/版权限制）')
      return
    }
    playerStore.playTracks(tracks, 0)
    toast.success(`已加入播放队列：${tracks.length} 首`)
  } catch (e) {
    toast.error('加入播放队列失败：' + (e.message || '未知错误'))
  } finally {
    playingAll.value = false
  }
}

/**
 * 播放单首
 */
async function playSong(song, index) {
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
 * 下载整个歌单（前 200 首）
 */
async function downloadAll() {
  if (!hasSongs.value) return
  downloadingAll.value = true
  try {
    const list = songs.value.slice(0, 200)
    const ids = list.map((s) => s.id)
    const result = await downloadSongs(ids, { level: 'exhigh' })
    toast.success(result.message || '下载任务已创建')
  } catch (e) {
    toast.error('下载失败：' + (e.message || '未知错误'))
  } finally {
    downloadingAll.value = false
  }
}

/**
 * 返回上一页
 */
function goBack() {
  // 优先返回我的歌单页
  if (window.history.length > 1) {
    router.back()
  } else {
    router.push('/netease/playlists')
  }
}

/**
 * 格式化时长
 */
function formatDuration(sec) {
  if (!sec || sec <= 0) return '--:--'
  const m = Math.floor(sec / 60)
  const s = Math.floor(sec % 60)
  return `${m}:${String(s).padStart(2, '0')}`
}

/**
 * 格式化数字
 */
function formatCount(n) {
  if (!n) return '0'
  if (n >= 100000000) return (n / 100000000).toFixed(1) + '亿'
  if (n >= 10000) return (n / 10000).toFixed(1) + '万'
  return String(n)
}

/**
 * 是否当前播放
 */
function isCurrentPlaying(song) {
  const cur = playerStore.currentTrack
  return cur && cur.id === song.id && cur.__source === 'netease'
}

// 监听路由参数变化
watch(
  () => route.params.id,
  (newId) => {
    if (newId) load()
  }
)

onMounted(() => {
  load()
})
</script>

<template>
  <div class="flex h-full flex-col gap-3">
    <!-- 顶部返回 -->
    <div class="flex items-center gap-2">
      <Button variant="ghost" size="sm" @click="goBack">
        <ArrowLeft class="h-4 w-4" />
        返回
      </Button>
    </div>

    <!-- 加载中 -->
    <div v-if="loading && !playlist" class="flex-1 flex items-center justify-center text-muted-foreground">
      <Loader2 class="mr-2 h-5 w-5 animate-spin" />
      加载中...
    </div>

    <!-- 歌单不存在 -->
    <Empty
      v-else-if="!playlist"
      :icon="AlertCircle"
      title="歌单不存在"
      description="歌单可能已被删除或链接无效"
      class="h-full"
    />

    <!-- 歌单详情 -->
    <template v-else>
      <!-- 歌单信息卡 -->
      <div class="flex gap-4 p-4 rounded-lg border border-border bg-card/40">
        <img
          v-if="playlist.coverImgUrl"
          :src="playlist.coverImgUrl"
          :alt="playlist.name"
          class="h-32 w-32 rounded-lg object-cover shrink-0"
          referrerpolicy="no-referrer"
        />
        <div v-else class="h-32 w-32 rounded-lg bg-muted flex items-center justify-center shrink-0">
          <Music class="h-12 w-12 text-muted-foreground" />
        </div>

        <div class="flex-1 min-w-0 flex flex-col gap-2">
          <div class="flex items-center gap-2 flex-wrap">
            <Badge v-if="playlist.creator?.userId === playlist.userId" variant="gold">我创建</Badge>
            <Badge v-else variant="outline">收藏</Badge>
            <h2 class="text-xl font-semibold truncate">{{ playlist.name }}</h2>
          </div>
          <div class="flex items-center gap-3 text-sm text-muted-foreground flex-wrap">
            <span>{{ playlist.creator?.nickname || '—' }}</span>
            <span class="flex items-center gap-1">
              <ListMusic class="h-3.5 w-3.5" />
              {{ playlist.trackCount || songs.length }} 首
            </span>
            <span v-if="playlist.playCount" class="flex items-center gap-1">
              <Play class="h-3.5 w-3.5" />
              {{ formatCount(playlist.playCount) }} 次播放
            </span>
          </div>
          <p v-if="playlist.description" class="text-xs text-muted-foreground line-clamp-2">
            {{ playlist.description }}
          </p>
          <div class="flex items-center gap-2 mt-auto">
            <Button
              variant="secondary"
              size="sm"
              :disabled="downloadingAll || !hasSongs"
              @click="downloadAll"
            >
              <Loader2 v-if="downloadingAll" class="h-4 w-4 animate-spin" />
              <Download v-else class="h-4 w-4" />
              下载全部
            </Button>
            <Button
              variant="gold"
              size="sm"
              :disabled="playingAll || !hasSongs"
              @click="playAll"
            >
              <Loader2 v-if="playingAll" class="h-4 w-4 animate-spin" />
              <Play v-else class="h-4 w-4" />
              播放全部
            </Button>
          </div>
        </div>
      </div>

      <!-- 曲目列表 -->
      <div class="flex-1 min-h-0 overflow-auto">
        <Empty
          v-if="!hasSongs && !loading"
          :icon="AlertCircle"
          title="歌单内暂无曲目"
          description="可能需要登录后才能查看完整曲目"
          class="h-full"
        />

        <div v-else class="flex flex-col gap-1 pb-4">
          <div
            v-for="(song, idx) in songs"
            :key="song.id"
            class="group flex items-center gap-3 px-3 py-2 rounded-md cursor-pointer transition-colors hover:bg-accent/50"
            :class="{ 'bg-primary/10': isCurrentPlaying(song) }"
            @dblclick="playSong(song, idx)"
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
                @click.stop="playSong(song, idx)"
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
            <div class="text-xs text-muted-foreground shrink-0 hidden sm:flex items-center gap-1">
              <Clock class="h-3 w-3" />
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
    </template>
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
