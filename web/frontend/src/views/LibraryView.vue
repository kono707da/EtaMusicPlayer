<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useNodesStore } from '../stores/nodes'
import { useAuthStore } from '../stores/auth'
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
const authStore = useAuthStore()
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

// 是否有已登录节点（控制空状态引导）
const hasLoggedInNode = computed(() => nodesStore.loggedInNodes.length > 0)

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

// 播放全部
function playAll() {
  if (libraryStore.tracks.length === 0) {
    toast.warning('当前曲目列表为空')
    return
  }
  const node = nodesStore.activeNode
  if (!node) return
  player.playTracks(libraryStore.tracks, node.id, node.name, 0)
}

// 把选中曲目加入队列
function addSelectedToQueue() {
  if (selectedTracks.value.length === 0) {
    toast.warning('请先选择曲目')
    return
  }
  const node = nodesStore.activeNode
  if (!node) return
  player.appendTracks(selectedTracks.value, node.id, node.name)
  toast.success(`已加入 ${selectedTracks.value.length} 首到播放队列`)
}

function goNodes() {
  router.push('/nodes')
}

function goPlugins() {
  router.push('/plugins')
}

onMounted(async () => {
  // 若已有激活且已登录的节点，自动加载全部音乐
  if (hasLoggedInNode.value && nodesStore.activeNode?.token) {
    libraryStore.refreshPlaylists()
    libraryStore.loadAllTracks()
  } else {
    // 探测本地节点状态（用于空状态显示引导）
    await pluginsStore.syncLocalNode(nodesStore)
    // 同步后若本地节点已自动连接，加载曲库
    if (hasLoggedInNode.value && nodesStore.activeNode?.token) {
      authStore.restoreFromNode(nodesStore.activeNode)
      libraryStore.refreshPlaylists()
      libraryStore.loadAllTracks()
    }
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
        <Button variant="secondary" size="sm" @click="libraryStore.refresh()">
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
    <div v-if="hasLoggedInNode" class="flex-1 min-h-0 flex flex-col">
      <TrackTable
        :tracks="libraryStore.tracks"
        :loading="libraryStore.loading"
        :show-source="showSource"
        :show-pagination="false"
        :node-id="nodesStore.activeNode?.id"
        :node-name="nodesStore.activeNode?.name"
        :total="libraryStore.tracksTotal"
        :page="libraryStore.page"
        :page-size="libraryStore.pageSize"
        @selection-change="onSelectionChange"
        @page-change="onPageChange"
      />
    </div>

    <!-- 无任何已登录节点：空状态引导 -->
    <Empty
      v-else
      :icon="Network"
      title="尚未连接任何节点"
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
