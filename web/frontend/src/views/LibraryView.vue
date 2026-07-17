<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useNodesStore } from '../stores/nodes'
import { useLibraryStore } from '../stores/library'
import { usePlayerStore } from '../stores/player'
import { usePluginsStore } from '../stores/plugins'
import TrackTable from '../components/TrackTable.vue'
import { Button } from '@/components/ui/button'
import { Empty } from '@/components/ui/empty'
import { useToast } from '@/components/ui/toast/use-toast'
import { Files, RefreshCw, ListPlus, Play, Network, HardDrive } from 'lucide-vue-next'

const router = useRouter()
const nodesStore = useNodesStore()
const libraryStore = useLibraryStore()
const player = usePlayerStore()
const pluginsStore = usePluginsStore()
const toast = useToast()

// 当前选中的来源（左侧树点击后）
const currentSelection = ref(null) // {type, nodeId, nodeName, playlistId}

// 是否展示来源列（跨节点搜索时）
const showSource = computed(() => libraryStore.mode === 'search')

// 选中的曲目（多选）
const selectedTracks = ref([])

// 是否有任何节点（在线或离线，离线节点也会展示缓存数据）
const hasAnyNode = computed(() => nodesStore.nodes.length > 0)

// 本地节点状态（用于空状态展示引导）
const localNodeAvailable = computed(() => pluginsStore.localNode?.available)

function onSelectionChange(rows) {
  selectedTracks.value = rows
}

// 树选择回调
function onSelect(payload) {
  currentSelection.value = payload
}

// 分页
function onPageChange(p) {
  libraryStore.setPage(p)
}

// 播放全部（跨节点：每条曲目自带 __nodeId）
// 离线节点曲目（__nodeOffline=true）会被过滤掉，无法播放
function playAll() {
  if (libraryStore.tracks.length === 0) {
    toast.warning('当前曲目列表为空')
    return
  }
  const playable = libraryStore.tracks.filter((t) => !t.__nodeOffline)
  const skipped = libraryStore.tracks.length - playable.length
  if (playable.length === 0) {
    toast.warning('节点离线无法播放', '当前列表全部曲目来自离线节点')
    return
  }
  if (skipped > 0) {
    toast.info(`已跳过 ${skipped} 首离线曲目`)
  }
  player.playTracks(playable, 0)
}

// 把选中曲目加入队列（离线曲目会被过滤掉）
function addSelectedToQueue() {
  if (selectedTracks.value.length === 0) {
    toast.warning('请先选择曲目')
    return
  }
  const playable = selectedTracks.value.filter((t) => !t.__nodeOffline)
  if (playable.length === 0) {
    toast.warning('离线曲目无法加入队列', '请选择在线节点的曲目')
    return
  }
  const skipped = selectedTracks.value.length - playable.length
  if (skipped > 0) {
    toast.info(`已跳过 ${skipped} 首离线曲目`)
  }
  player.appendTracks(playable)
  toast.success(`已加入 ${playable.length} 首到播放队列`)
}

// 刷新当前视图
function refreshCurrent() {
  if (libraryStore.mode === 'search') {
    libraryStore.globalSearch(libraryStore.keyword)
  } else if (libraryStore.mode === 'all' || libraryStore.mode === 'empty') {
    libraryStore.loadAllTracks()
  }
}

function goNodes() {
  router.push('/nodes')
}

function goPlugins() {
  router.push('/plugins')
}

onMounted(async () => {
  // 若无任何节点，探测本地节点状态（用于空状态引导）
  if (!hasAnyNode.value) {
    await pluginsStore.syncLocalNode(nodesStore)
  }
})

// 监听搜索关键字清空 → 回到全部音乐
watch(
  () => libraryStore.keyword,
  (v) => {
    if (!v && libraryStore.mode === 'search') {
      libraryStore.loadAllTracks()
    }
  }
)
</script>

<template>
  <div class="flex h-full flex-col gap-4">
    <!-- 工具栏 -->
    <div class="flex items-center justify-between gap-3">
      <div class="flex items-center gap-2">
        <Files class="h-5 w-5 text-primary" />
        <h2 class="text-lg font-semibold tracking-tight text-foreground">
          {{ currentSelection?.type === 'playlist'
            ? currentSelection.label
            : currentSelection?.type === 'all'
            ? (currentSelection.nodeName || '全部音乐')
            : '全部音乐' }}
        </h2>
      </div>
      <div class="flex items-center gap-2">
        <Button variant="secondary" size="sm" @click="refreshCurrent">
          <RefreshCw class="h-4 w-4" />
          刷新
        </Button>
        <Button variant="ghost" size="sm" @click="addSelectedToQueue" :disabled="selectedTracks.length === 0">
          <ListPlus class="h-4 w-4" />
          加入队列
        </Button>
        <Button variant="gold" size="sm" @click="playAll" :disabled="libraryStore.tracks.length === 0">
          <Play class="h-4 w-4" />
          播放全部
        </Button>
      </div>
    </div>

    <!-- 曲目表 -->
    <div v-if="hasAnyNode" class="flex-1 min-h-0 flex flex-col">
      <TrackTable
        :tracks="libraryStore.tracks"
        :loading="libraryStore.loading"
        :show-source="showSource"
        :show-pagination="false"
        :total="libraryStore.tracksTotal"
        :page="libraryStore.page"
        :page-size="libraryStore.pageSize"
        @selection-change="onSelectionChange"
        @page-change="onPageChange"
      />
    </div>

    <!-- 无任何节点（在线/离线都没有）：空状态引导 -->
    <Empty
      v-else
      :icon="Network"
      title="尚未添加任何节点"
      description="请前往节点管理添加远程节点，或启用本地节点插件"
      class="flex-1"
    >
      <div class="flex flex-col items-center gap-3">
        <Button variant="gold" @click="goPlugins">
          <HardDrive class="h-4 w-4" />
          前往启用本地节点
        </Button>
        <Button variant="ghost" @click="goNodes">
          去节点管理 / 设置
        </Button>
      </div>
    </Empty>
  </div>
</template>
