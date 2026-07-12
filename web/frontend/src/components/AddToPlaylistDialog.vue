<script setup>
import { ref, computed, watch } from 'vue'
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { useToast } from '@/components/ui/toast/use-toast'
import { useNodesStore } from '../stores/nodes'
import { useLibraryStore } from '../stores/library'
import { addTracksToPlaylist } from '../api/node'
import { addClientPlaylistItems } from '../api/client_playlist'
import { Server, Music2, Loader2, ListMusic } from 'lucide-vue-next'

const props = defineProps({
  visible: { type: Boolean, default: false },
  tracks: { type: Array, default: () => [] }
})
const emit = defineEmits(['update:visible', 'added'])

const nodesStore = useNodesStore()
const libraryStore = useLibraryStore()
const toast = useToast()

const loading = ref(false)
const expandedGroups = ref(new Set())

// 可加入的播放列表：客户端 + 各节点
// 客户端播放列表可接受任何节点的曲目
// 节点播放列表只能接受本节点曲目
const playlistGroups = computed(() => {
  const groups = []

  // 客户端播放列表（可跨节点）
  const clientCustom = (libraryStore.clientPlaylists || []).filter((p) => !p.is_system)
  if (clientCustom.length > 0) {
    groups.push({
      id: 'client',
      label: '本机',
      icon: Music2,
      playlists: clientCustom.map((p) => ({ ...p, groupType: 'client' }))
    })
  }

  // 各节点的播放列表
  nodesStore.loggedInNodes.forEach((n) => {
    const nodePlaylists = (libraryStore.nodePlaylists[n.id] || []).filter((p) => !p.is_system)
    if (nodePlaylists.length > 0) {
      groups.push({
        id: `node-${n.id}`,
        label: n.name,
        icon: Server,
        nodeId: n.id,
        playlists: nodePlaylists.map((p) => ({ ...p, groupType: 'node', nodeId: n.id }))
      })
    }
  })

  return groups
})

watch(
  () => props.visible,
  (v) => {
    if (v) {
      // 打开时默认展开所有分组
      expandedGroups.value = new Set(playlistGroups.value.map((g) => g.id))
    }
  }
)

function toggleGroup(id) {
  const next = new Set(expandedGroups.value)
  if (next.has(id)) next.delete(id)
  else next.add(id)
  expandedGroups.value = next
}

async function addToTarget(playlist, groupType, nodeId) {
  if (props.tracks.length === 0) {
    toast.warning('没有可添加的曲目')
    return
  }
  loading.value = true
  try {
    if (groupType === 'client') {
      // 客户端播放列表：每条曲目带自己的 node_id
      const items = props.tracks.map((t) => ({
        track_id: t.id,
        node_id: String(t.__nodeId),
        title: t.title || '',
        artist: t.artist || '',
        album: t.album || '',
        duration: t.duration || 0
      }))
      await addClientPlaylistItems(playlist.id, items)
    } else {
      // 节点播放列表：只能添加本节点曲目，过滤掉其他节点的
      const nodeTracks = props.tracks.filter((t) => t.__nodeId === nodeId)
      if (nodeTracks.length === 0) {
        toast.warning('该播放列表只接受本节点的曲目', '选中曲目均不来自此节点')
        return
      }
      const trackIds = nodeTracks.map((t) => t.id)
      const node = nodesStore.getNode(nodeId)
      await addTracksToPlaylist(node, playlist.id, trackIds)
    }
    emit('added', { playlist, count: props.tracks.length })
  } catch (e) {
    toast.error('添加失败', e?.response?.data?.detail || e.message, e)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <Dialog :open="visible" @update:open="(v) => emit('update:visible', v)">
    <DialogContent class="max-w-md">
      <DialogHeader>
        <DialogTitle>加入到播放列表</DialogTitle>
        <DialogDescription>
          选择目标播放列表（{{ tracks.length }} 首曲目）
        </DialogDescription>
      </DialogHeader>

      <div class="max-h-[400px] overflow-auto">
        <div v-if="playlistGroups.length === 0" class="py-8 text-center text-sm text-muted-foreground">
          暂无可用播放列表，请先在曲库树中创建
        </div>

        <template v-for="group in playlistGroups" :key="group.id">
          <!-- 分组标题 -->
          <div
            class="flex items-center gap-2 rounded-md px-2 py-2 cursor-pointer hover:bg-accent/50"
            @click="toggleGroup(group.id)"
          >
            <component :is="group.icon" class="h-4 w-4 text-muted-foreground" />
            <span class="flex-1 text-sm font-medium text-foreground">{{ group.label }}</span>
            <span class="text-xs text-muted-foreground">{{ group.playlists.length }}</span>
          </div>

          <!-- 分组下的播放列表 -->
          <div v-if="expandedGroups.has(group.id)" class="ml-4 space-y-0.5">
            <div
              v-for="pl in group.playlists"
              :key="pl.id"
              class="flex items-center gap-2 rounded-md px-2 py-1.5 cursor-pointer text-sm text-foreground hover:bg-accent/50"
              @click="!loading && addToTarget(pl, pl.groupType, pl.nodeId)"
            >
              <ListMusic class="h-4 w-4 text-muted-foreground" />
              <span class="truncate flex-1">{{ pl.name }}</span>
              <Loader2 v-if="loading" class="h-3.5 w-3.5 animate-spin text-muted-foreground" />
            </div>
          </div>
        </template>
      </div>
    </DialogContent>
  </Dialog>
</template>
