<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  Server, Library, ListMusic, Unplug, ChevronRight, ChevronDown,
  RefreshCw, Inbox, Plus, Music2
} from 'lucide-vue-next'
import { useNodesStore } from '../stores/nodes'
import { useLibraryStore } from '../stores/library'
import { useToast } from '@/components/ui/toast/use-toast'
import { createPlaylist } from '../api/node'
import { createClientPlaylist } from '../api/client_playlist'
import { Button } from '@/components/ui/button'
import { Empty } from '@/components/ui/empty'

const emit = defineEmits(['select'])
const router = useRouter()
const nodesStore = useNodesStore()
const libraryStore = useLibraryStore()
const toast = useToast()

// 树节点数据：节点分组 + 客户端分组
const treeData = computed(() => {
  const loggedNodes = nodesStore.loggedInNodes
  const groups = []

  // 每个已登录节点一个分组
  loggedNodes.forEach((n) => {
    const nodePlaylists = libraryStore.nodePlaylists[n.id] || []
    const inbox = nodePlaylists.find((p) => p.is_system && p.name === '收集箱')
    const custom = nodePlaylists.filter((p) => !p.is_system)
    groups.push({
      id: `node-${n.id}`,
      type: 'node-group',
      label: n.name,
      nodeId: n.id,
      nodeName: n.name,
      canCreate: true,
      children: [
        {
          id: `node-${n.id}-all`,
          label: '全部音乐',
          type: 'node-all',
          nodeId: n.id,
          nodeName: n.name,
          isLeaf: true
        },
        ...(inbox
          ? [{
              id: `node-${n.id}-inbox`,
              label: '收集箱',
              type: 'node-inbox',
              nodeId: n.id,
              nodeName: n.name,
              playlistId: inbox.id,
              isLeaf: true
            }]
          : []),
        ...custom.map((p) => ({
          id: `node-${n.id}-pl-${p.id}`,
          label: p.name,
          type: 'node-playlist',
          nodeId: n.id,
          nodeName: n.name,
          playlistId: p.id,
          isLeaf: true
        }))
      ]
    })
  })

  // 客户端分组
  const clientCustom = (libraryStore.clientPlaylists || []).filter((p) => !p.is_system)
  groups.push({
    id: 'client-group',
    type: 'client-group',
    label: '本机',
    canCreate: true,
    children: [
      {
        id: 'client-all',
        label: '全部音乐',
        type: 'client-all',
        isLeaf: true
      },
      ...clientCustom.map((p) => ({
        id: `client-pl-${p.id}`,
        label: p.name,
        type: 'client-playlist',
        playlistId: p.id,
        isLeaf: true
      }))
    ]
  })

  return groups
})

const currentKey = ref('')
const expandedIds = ref([])

function isExpanded(id) {
  return expandedIds.value.includes(id)
}
function toggleExpand(id) {
  const idx = expandedIds.value.indexOf(id)
  if (idx > -1) expandedIds.value.splice(idx, 1)
  else expandedIds.value.push(id)
}

function childIcon(type) {
  if (type === 'node-all' || type === 'client-all') return Library
  if (type === 'node-inbox') return Inbox
  return ListMusic
}

function groupIcon(type) {
  if (type === 'client-group') return Music2
  return Server
}

function onNodeClick(data) {
  currentKey.value = data.id
  if (data.type === 'node-group' || data.type === 'client-group') {
    return
  }

  libraryStore.resetPaging()

  if (data.type === 'node-all') {
    libraryStore.loadNodeAllTracks(data.nodeId)
  } else if (data.type === 'node-inbox' || data.type === 'node-playlist') {
    libraryStore.loadNodePlaylistTracks(data.nodeId, data.playlistId)
  } else if (data.type === 'client-all') {
    libraryStore.loadAllTracks()
  } else if (data.type === 'client-playlist') {
    libraryStore.loadClientPlaylistTracks(data.playlistId)
  }

  emit('select', data)
}

/**
 * 在节点/客户端分组下新建播放列表（默认名，可在播放列表页重命名）
 */
async function onCreatePlaylist(group) {
  try {
    if (group.type === 'node-group') {
      const node = nodesStore.getNode(group.nodeId)
      if (!node || !node.token) {
        toast.error('节点未登录，无法创建播放列表')
        return
      }
      await createPlaylist(node, { name: '新建播放列表', description: '' })
      toast.success('已在节点上创建播放列表，可前往播放列表页重命名')
    } else if (group.type === 'client-group') {
      await createClientPlaylist('新建播放列表', '')
      toast.success('已创建客户端播放列表，可前往播放列表页重命名')
    }
    await libraryStore.refreshAllPlaylists()
  } catch (e) {
    toast.error('创建播放列表失败', e.message || String(e), e)
  }
}

function goNodes() {
  router.push('/nodes')
}

onMounted(() => {
  // 默认展开所有分组
  expandedIds.value = treeData.value.map((g) => g.id)
  // 默认选中客户端"全部音乐"
  currentKey.value = 'client-all'
  libraryStore.loadAllTracks()
})
</script>

<template>
  <div class="flex h-full flex-col">
    <!-- 标题栏 -->
    <div class="flex items-center justify-between px-4 pt-4 pb-3">
      <span class="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
        曲库
      </span>
      <Button
        variant="ghost"
        size="sm"
        class="h-7 gap-1 px-2 text-xs text-muted-foreground hover:text-foreground"
        @click="libraryStore.refreshAllPlaylists()"
      >
        <RefreshCw class="h-3.5 w-3.5" />
        刷新
      </Button>
    </div>

    <!-- 无任何已登录节点：引导 -->
    <div
      v-if="nodesStore.loggedInNodes.length === 0"
      class="flex flex-1 flex-col items-center justify-center gap-4 px-4 py-8"
    >
      <Empty :icon="Unplug" description="尚未登录任何节点" />
      <Button variant="default" size="sm" @click="goNodes">
        去添加 / 登录节点
      </Button>
    </div>

    <!-- 树：节点分组 + 客户端分组 -->
    <div v-else class="flex-1 overflow-auto px-2 pb-3">
      <template v-for="group in treeData" :key="group.id">
        <!-- 一级：分组标题（节点名 / 本机） + + 号 -->
        <div
          class="group flex items-center gap-1 rounded-md px-1.5 py-1.5 text-sm cursor-pointer transition-colors hover:bg-accent/50"
          :class="isExpanded(group.id) ? 'bg-accent/30' : ''"
          @click="onNodeClick(group)"
        >
          <button
            class="flex h-5 w-5 shrink-0 items-center justify-center rounded text-muted-foreground hover:bg-accent hover:text-foreground"
            @click.stop="toggleExpand(group.id)"
          >
            <component
              :is="isExpanded(group.id) ? ChevronDown : ChevronRight"
              class="h-4 w-4"
            />
          </button>
          <component :is="groupIcon(group.type)" class="h-4 w-4 shrink-0 text-muted-foreground" />
          <span class="truncate flex-1 text-foreground font-medium">{{ group.label }}</span>
          <!-- + 号：新建播放列表 -->
          <button
            v-if="group.canCreate"
            class="flex h-5 w-5 shrink-0 items-center justify-center rounded text-muted-foreground hover:bg-accent hover:text-primary"
            title="新建播放列表"
            @click.stop="onCreatePlaylist(group)"
          >
            <Plus class="h-4 w-4" />
          </button>
        </div>

        <!-- 二级：子节点（全部音乐 / 收集箱 / 播放列表） -->
        <div v-if="isExpanded(group.id)" class="ml-4 mt-0.5 space-y-0.5">
          <div
            v-for="child in group.children"
            :key="child.id"
            class="flex items-center gap-2 rounded-md px-2 py-1.5 text-sm cursor-pointer transition-colors"
            :class="currentKey === child.id
              ? 'bg-primary/10 text-primary'
              : 'text-foreground hover:bg-accent/50'"
            @click="onNodeClick(child)"
          >
            <component
              :is="childIcon(child.type)"
              class="h-4 w-4 shrink-0"
              :class="currentKey === child.id ? 'text-primary' : 'text-muted-foreground'"
            />
            <span class="truncate">{{ child.label }}</span>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>
