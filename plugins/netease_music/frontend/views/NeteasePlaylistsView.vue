<script setup>
/**
 * 网易云我的歌单视图
 *
 * 依赖通过 window.__etamusic 取用。
 */
const { ref, computed, onMounted } = window.__etamusic.vue
const { useRouter } = window.__etamusic.vueRouter
const {
  ListMusic, Loader2, RefreshCw, Music, User, AlertCircle
} = window.__etamusic.icons
const { Button, Badge, Empty, useToast } = window.__etamusic.ui

import { useNeteaseStore } from '../store'
import { getMyPlaylists } from '../api'

const router = useRouter()
const toast = useToast()
const neteaseStore = useNeteaseStore()

const loading = ref(false)
const playlists = ref([])

const hasData = computed(() => playlists.value.length > 0)

/**
 * 加载我的歌单
 */
async function load() {
  if (!neteaseStore.isLoggedIn) {
    playlists.value = []
    return
  }
  loading.value = true
  try {
    const data = await getMyPlaylists()
    playlists.value = data?.playlist || []
  } catch (e) {
    toast.error('获取歌单失败：' + (e.message || '未知错误'))
    playlists.value = []
  } finally {
    loading.value = false
  }
}

/**
 * 跳转歌单详情
 */
function openDetail(playlist) {
  router.push(`/netease/playlist/${playlist.id}`)
}

/**
 * 格式化播放数
 */
function formatCount(n) {
  if (!n) return '0'
  if (n >= 100000000) return (n / 100000000).toFixed(1) + '亿'
  if (n >= 10000) return (n / 10000).toFixed(1) + '万'
  return String(n)
}

/**
 * 跳转登录
 */
function goLogin() {
  router.push('/netease')
}

onMounted(() => {
  if (!neteaseStore.loaded) {
    neteaseStore.load().then(() => {
      if (neteaseStore.isLoggedIn) load()
    })
  } else if (neteaseStore.isLoggedIn) {
    load()
  }
})
</script>

<template>
  <div class="flex h-full flex-col gap-3">
    <!-- 顶部标题 -->
    <div class="flex items-center justify-between gap-3">
      <div class="flex items-center gap-2">
        <ListMusic class="h-5 w-5 text-primary" />
        <h2 class="text-lg font-semibold tracking-tight">我的歌单</h2>
        <Badge v-if="hasData" variant="outline" class="text-muted-foreground">
          {{ playlists.length }} 个
        </Badge>
      </div>
      <Button
        v-if="neteaseStore.isLoggedIn"
        variant="ghost"
        size="sm"
        :disabled="loading"
        @click="load"
      >
        <RefreshCw v-if="loading" class="h-4 w-4 animate-spin" />
        <RefreshCw v-else class="h-4 w-4" />
        刷新
      </Button>
    </div>

    <!-- 内容区 -->
    <div class="flex-1 min-h-0 overflow-auto">
      <!-- 未登录 -->
      <Empty
        v-if="!neteaseStore.isLoggedIn && neteaseStore.loaded"
        :icon="User"
        title="未登录网易云账号"
        description="请先扫码登录后查看我的歌单"
        class="h-full"
      >
        <Button variant="gold" size="sm" @click="goLogin">
          去登录
        </Button>
      </Empty>

      <!-- 加载中 -->
      <div v-else-if="loading && !hasData" class="flex h-full items-center justify-center text-muted-foreground">
        <Loader2 class="mr-2 h-5 w-5 animate-spin" />
        加载中...
      </div>

      <!-- 无歌单 -->
      <Empty
        v-else-if="!hasData && neteaseStore.loaded"
        :icon="AlertCircle"
        title="暂无歌单"
        description="当前账号没有创建或收藏任何歌单"
        class="h-full"
      />

      <!-- 歌单网格 -->
      <div v-else class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4 pb-4">
        <div
          v-for="pl in playlists"
          :key="pl.id"
          class="group cursor-pointer rounded-lg border border-border bg-card/40 overflow-hidden transition-all hover:border-primary/60 hover:shadow-lg"
          @click="openDetail(pl)"
        >
          <div class="aspect-square relative overflow-hidden bg-muted">
            <img
              v-if="pl.coverImgUrl"
              :src="pl.coverImgUrl"
              :alt="pl.name"
              loading="lazy"
              referrerpolicy="no-referrer"
              class="absolute inset-0 h-full w-full object-cover transition-transform group-hover:scale-105"
            />
            <div v-else class="absolute inset-0 flex items-center justify-center">
              <Music class="h-10 w-10 text-muted-foreground" />
            </div>
            <div class="absolute top-2 right-2">
              <Badge variant="secondary" class="text-[10px]">
                {{ formatCount(pl.trackCount) }} 首
              </Badge>
            </div>
            <div class="absolute bottom-2 right-2">
              <Badge v-if="pl.playCount" variant="secondary" class="text-[10px]">
                ▶ {{ formatCount(pl.playCount) }}
              </Badge>
            </div>
          </div>
          <div class="p-2.5">
            <div class="line-clamp-2 text-sm font-medium text-foreground min-h-[2.5rem]">
              {{ pl.name }}
            </div>
            <div class="mt-1.5 flex items-center justify-between text-xs text-muted-foreground">
              <span class="truncate">{{ pl.creator?.nickname || '—' }}</span>
              <Badge v-if="pl.creator?.userId === Number(neteaseStore.currentUid)" variant="outline" class="text-[10px]">
                我创建
              </Badge>
              <Badge v-else variant="outline" class="text-[10px]">收藏</Badge>
            </div>
          </div>
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
