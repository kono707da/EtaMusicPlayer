<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Server, Library, ListMusic, Unplug, ChevronRight, ChevronDown, RefreshCw, Inbox } from 'lucide-vue-next'
import { useNodesStore } from '../stores/nodes'
import { useLibraryStore } from '../stores/library'
import { Button } from '@/components/ui/button'
import { Empty } from '@/components/ui/empty'

const emit = defineEmits(['select'])
const router = useRouter()
const nodesStore = useNodesStore()
const libraryStore = useLibraryStore()

// 树节点数据：仅展示已登录节点 > 播放列表 + "全部音乐"
const treeData = computed(() => {
  const loggedNodes = nodesStore.loggedInNodes
  if (loggedNodes.length === 0) return []
  return loggedNodes.map((n) => ({
    id: `node-${n.id}`,
    label: n.name,
    type: 'node',
    nodeId: n.id,
    nodeName: n.name,
    children: [
      {
        id: `node-${n.id}-all`,
        label: '全部音乐',
        type: 'all',
        nodeId: n.id,
        nodeName: n.name,
        isLeaf: true
      },
      ...((() => {
        const inbox = (libraryStore.playlists || []).find(
          (p) => p.is_system && p.name === '收集箱' && p.__nodeId === n.id
        )
        return inbox
          ? [
              {
                id: `node-${n.id}-inbox`,
                label: '收集箱',
                type: 'inbox',
                nodeId: n.id,
                nodeName: n.name,
                playlistId: inbox.id,
                isLeaf: true
              }
            ]
          : []
      })()),
      ...((libraryStore.playlists || [])
        .filter((p) => !p.is_system && p.__nodeId === n.id)
        .map((p) => ({
          id: `node-${n.id}-pl-${p.id}`,
          label: p.name,
          type: 'playlist',
          nodeId: n.id,
          nodeName: n.name,
          playlistId: p.id,
          isSystem: false,
          isLeaf: true
        })))
    ]
  }))
})

const currentKey = ref('')
// 展开节点 id 列表
const expandedIds = ref([])

function isExpanded(id) {
  return expandedIds.value.includes(id)
}
function toggleExpand(id) {
  const idx = expandedIds.value.indexOf(id)
  if (idx > -1) expandedIds.value.splice(idx, 1)
  else expandedIds.value.push(id)
}

// 子节点图标
function childIcon(type) {
  if (type === 'all') return Library
  if (type === 'inbox') return Inbox
  return ListMusic
}

function onNodeClick(data) {
  currentKey.value = data.id
  // 点击节点行仅展开/折叠，不再切换激活节点
  if (data.type === 'node') {
    toggleExpand(data.id)
    return
  }

  // 选中"全部音乐"或"播放列表"
  if (data.type === 'all') {
    libraryStore.resetPaging()
    libraryStore.loadAllTracks()
    emit('select', { type: 'all', nodeId: data.nodeId, nodeName: data.nodeName })
  } else if (data.type === 'inbox') {
    libraryStore.resetPaging()
    libraryStore.loadPlaylistTracks({ id: data.playlistId, nodeId: data.nodeId })
    emit('select', {
      type: 'inbox',
      nodeId: data.nodeId,
      nodeName: data.nodeName,
      playlistId: data.playlistId
    })
  } else if (data.type === 'playlist') {
    libraryStore.resetPaging()
    libraryStore.loadPlaylistTracks({ id: data.playlistId, nodeId: data.nodeId })
    emit('select', {
      type: 'playlist',
      nodeId: data.nodeId,
      nodeName: data.nodeName,
      playlistId: data.playlistId
    })
  }
}

function goNodes() {
  router.push('/nodes')
}

onMounted(() => {
  // 默认展开第一个已登录节点
  const first = nodesStore.loggedInNodes[0]
  if (first) {
    expandedIds.value = [`node-${first.id}`]
    currentKey.value = `node-${first.id}-all`
  }
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
        @click="libraryStore.refreshPlaylists()"
      >
        <RefreshCw class="h-3.5 w-3.5" />
        刷新
      </Button>
    </div>

    <!-- 无任何已登录节点：引导 -->
    <div
      v-if="treeData.length === 0"
      class="flex flex-1 flex-col items-center justify-center gap-4 px-4 py-8"
    >
      <Empty :icon="Unplug" description="尚未登录任何节点" />
      <Button variant="default" size="sm" @click="goNodes">
        去添加 / 登录节点
      </Button>
    </div>

    <!-- 手写递归树（两级：节点 > 子项） -->
    <div v-else class="flex-1 overflow-auto px-2 pb-3">
      <template v-for="node in treeData" :key="node.id">
        <!-- 一级：节点 -->
        <div
          class="group flex items-center gap-1 rounded-md px-1.5 py-1.5 text-sm cursor-pointer transition-colors hover:bg-accent/50"
          :class="isExpanded(node.id) ? 'bg-accent/30' : ''"
          @click="onNodeClick(node)"
        >
          <button
            class="flex h-5 w-5 shrink-0 items-center justify-center rounded text-muted-foreground hover:bg-accent hover:text-foreground"
            @click.stop="toggleExpand(node.id)"
          >
            <component
              :is="isExpanded(node.id) ? ChevronDown : ChevronRight"
              class="h-4 w-4"
            />
          </button>
          <Server
            class="h-4 w-4 shrink-0 text-muted-foreground"
          />
          <span
            class="truncate text-foreground"
          >
            {{ node.label }}
          </span>
        </div>

        <!-- 二级：子节点 -->
        <div v-if="isExpanded(node.id)" class="ml-4 mt-0.5 space-y-0.5">
          <div
            v-for="child in node.children"
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
