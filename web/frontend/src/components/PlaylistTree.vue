<script setup>
import { ref, computed, onMounted, nextTick, provide } from 'vue'
import { useRouter } from 'vue-router'
import {
  Server, Music2, Unplug, ChevronRight, ChevronDown,
  RefreshCw, Plus, FolderPlus, Trash2, Pencil
} from 'lucide-vue-next'
import { useNodesStore } from '../stores/nodes'
import { useLibraryStore } from '../stores/library'
import { useToast } from '@/components/ui/toast/use-toast'
import { useConfirm } from '@/composables/use-confirm'
import {
  updatePlaylist, deletePlaylist,
  createPlaylistFolder, updatePlaylistFolder, deletePlaylistFolder
} from '../api/node'
import {
  updateClientPlaylist, deleteClientPlaylist,
  createClientPlaylistFolder, updateClientPlaylistFolder, deleteClientPlaylistFolder
} from '../api/client_playlist'
import { Button } from '@/components/ui/button'
import { Empty } from '@/components/ui/empty'
import NewPlaylistDialog from './NewPlaylistDialog.vue'
import PlaylistTreeNode from './PlaylistTreeNode.vue'

const emit = defineEmits(['select'])
const router = useRouter()
const nodesStore = useNodesStore()
const libraryStore = useLibraryStore()
const toast = useToast()
const { confirm } = useConfirm()

// ==================== 树构建 ====================
/**
 * 构建文件夹子树（递归）
 * @param {Number|null} parentFolderId 父文件夹 id（null=根）
 * @param {Array} folders 扁平文件夹列表
 * @param {Array} playlists 扁平播放列表列表（含 folder_id）
 * @param {Object} ctx 分组上下文 { idPrefix, typePrefix, nodeId, nodeName, isOffline }
 */
function buildSubtree(parentFolderId, folders, playlists, ctx) {
  const childFolders = folders.filter((f) => (f.parent_id ?? null) === parentFolderId)
  const childPlaylists = playlists.filter((p) => (p.folder_id ?? null) === parentFolderId)

  const folderNodes = childFolders.map((f) => ({
    id: `${ctx.idPrefix}-folder-${f.id}`,
    type: `${ctx.typePrefix}-folder`,
    label: f.name,
    isFolder: true,
    isLeaf: false,
    isSystem: false,
    isOffline: ctx.isOffline,
    folderId: f.id,
    nodeId: ctx.nodeId,
    nodeName: ctx.nodeName,
    canCreate: !ctx.isOffline,
    children: buildSubtree(f.id, folders, playlists, ctx)
  }))

  const playlistNodes = childPlaylists.map((p) => ({
    id: `${ctx.idPrefix}-pl-${p.id}`,
    type: `${ctx.typePrefix}-playlist`,
    label: p.name,
    isFolder: false,
    isLeaf: true,
    isSystem: false,
    isOffline: ctx.isOffline,
    playlistId: p.id,
    folderId: p.folder_id,
    nodeId: ctx.nodeId,
    nodeName: ctx.nodeName
  }))

  // 文件夹在前，播放列表在后
  return [...folderNodes, ...playlistNodes]
}

/**
 * 树节点数据：节点分组 + 客户端分组
 * 每个分组的 rootChildren 包含系统列表 + 根级文件夹 + 根级播放列表
 */
const treeData = computed(() => {
  const allNodes = nodesStore.nodes
  const groups = []

  allNodes.forEach((n) => {
    const isOffline = !n.token
    const nodePlaylists = libraryStore.nodePlaylists[n.id] || []
    const nodeFolders = libraryStore.nodeFolders[n.id] || []
    const inbox = nodePlaylists.find((p) => p.is_system && p.name === '收集箱')
    const custom = nodePlaylists.filter((p) => !p.is_system)
    const rootCustom = custom.filter((p) => p.folder_id == null)

    const ctx = {
      idPrefix: `node-${n.id}`,
      typePrefix: 'node',
      nodeId: n.id,
      nodeName: n.name,
      isOffline
    }

    const systemChildren = [
      {
        id: `node-${n.id}-all`,
        label: '全部音乐',
        type: 'node-all',
        nodeId: n.id,
        nodeName: n.name,
        isLeaf: true,
        isSystem: true,
        isOffline
      },
      ...(inbox
        ? [{
            id: `node-${n.id}-inbox`,
            label: '收集箱',
            type: 'node-inbox',
            nodeId: n.id,
            nodeName: n.name,
            playlistId: inbox.id,
            isLeaf: true,
            isSystem: true,
            isOffline
          }]
        : [])
    ]

    const subtree = buildSubtree(null, nodeFolders, custom, ctx)
    // 根级自定义播放列表（无文件夹归属）排在文件夹之后
    const rootPlaylistNodes = rootCustom.map((p) => ({
      id: `node-${n.id}-pl-${p.id}`,
      label: p.name,
      type: 'node-playlist',
      nodeId: n.id,
      nodeName: n.name,
      playlistId: p.id,
      isLeaf: true,
      isSystem: false,
      isOffline
    }))

    groups.push({
      id: `node-${n.id}`,
      type: 'node-group',
      label: n.name,
      nodeId: n.id,
      nodeName: n.name,
      canCreate: !isOffline,
      isOffline,
      rootChildren: [...systemChildren, ...subtree.filter((n) => n.isFolder), ...rootPlaylistNodes]
    })
  })

  // 客户端分组
  const clientPlaylists = libraryStore.clientPlaylists || []
  const clientFolders = libraryStore.clientFolders || []
  const clientAll = clientPlaylists.find((p) => p.is_system && p.name === '全部音乐')
  const clientCustom = clientPlaylists.filter((p) => !p.is_system)
  const clientRootCustom = clientCustom.filter((p) => p.folder_id == null)

  const clientCtx = {
    idPrefix: 'client',
    typePrefix: 'client',
    nodeId: null,
    nodeName: '本机',
    isOffline: false
  }
  const clientSubtree = buildSubtree(null, clientFolders, clientCustom, clientCtx)
  const clientRootPlaylistNodes = clientRootCustom.map((p) => ({
    id: `client-pl-${p.id}`,
    label: p.name,
    type: 'client-playlist',
    playlistId: p.id,
    isLeaf: true,
    isSystem: false
  }))

  groups.push({
    id: 'client-group',
    type: 'client-group',
    label: '本机',
    canCreate: true,
    rootChildren: [
      {
        id: 'client-all',
        label: '全部音乐',
        type: 'client-all',
        isLeaf: true,
        isSystem: true,
        playlistId: clientAll?.id
      },
      ...clientSubtree.filter((n) => n.isFolder),
      ...clientRootPlaylistNodes
    ]
  })

  return groups
})

// ==================== 状态 ====================
const currentKey = ref('')
const expandedIds = ref([])
const dragging = ref(null)
// 拖拽悬停在根级分组上的高亮
const dragOverGroup = ref('')

// 新建播放列表弹窗
const newPlaylistDialog = ref({ open: false, group: null, folderId: null })

// 新建文件夹弹窗
const newFolderDialog = ref({ open: false, group: null, parentId: null, name: '' })

// 原地重命名状态
const renaming = ref({ id: '', value: '', saving: false })
const renameInputEl = ref(null)
function setRenameRef(el) {
  if (el) renameInputEl.value = el
}

// 右键菜单状态
const contextMenu = ref({ visible: false, x: 0, y: 0, item: null })

// 提供给子组件的状态
provide('playlistTreeState', {
  expandedIds,
  renaming,
  currentKey,
  dragging
})

// ==================== 工具方法 ====================
function isExpanded(id) {
  return expandedIds.value.includes(id)
}
function toggleExpand(id) {
  const idx = expandedIds.value.indexOf(id)
  if (idx > -1) expandedIds.value.splice(idx, 1)
  else expandedIds.value.push(id)
}

function groupIcon(type) {
  if (type === 'client-group') return Music2
  return Server
}

/**
 * 检查 folder 是否在 candidate 的子树中（含自身）
 * 用于拖拽时防止把 candidate 移到 folder（folder 是 candidate 的后代会导致循环）
 */
function isDescendantOf(candidate, folder) {
  if (!candidate || !folder) return false
  if (candidate.id === folder.id) return true

  function findNode(node, targetId) {
    if (node.id === targetId) return node
    if (node.children) {
      for (const c of node.children) {
        const found = findNode(c, targetId)
        if (found) return found
      }
    }
    return null
  }
  for (const group of treeData.value) {
    for (const root of group.rootChildren || []) {
      const candidateNode = findNode(root, candidate.id)
      if (candidateNode) {
        return findNode(candidateNode, folder.id) !== null
      }
    }
  }
  return false
}

// ==================== 点击/加载 ====================
function onNodeClick(data) {
  if (renaming.value.id) return // 编辑中不切换
  currentKey.value = data.id
  // 文件夹点击切换展开
  if (data.isFolder) {
    toggleExpand(data.id)
    return
  }
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

// ==================== 新建播放列表 ====================
function onCreatePlaylist(group, folderId = null) {
  newPlaylistDialog.value = { open: true, group, folderId }
}

async function onPlaylistCreated() {
  await libraryStore.refreshAllPlaylists()
}

// ==================== 新建文件夹 ====================
function onCreateFolder(group, parentId = null) {
  newFolderDialog.value = {
    open: true,
    group,
    parentId,
    name: ''
  }
}

async function onSubmitCreateFolder() {
  const name = (newFolderDialog.value.name || '').trim()
  if (!name) {
    toast.warning('文件夹名称不能为空')
    return
  }
  const { group, parentId } = newFolderDialog.value
  try {
    if (group.type === 'node-group') {
      const node = nodesStore.getNode(group.nodeId)
      if (!node || !node.token) {
        toast.error('节点未连接')
        return
      }
      await createPlaylistFolder(node, { name, parent_id: parentId })
    } else {
      await createClientPlaylistFolder(name, parentId)
    }
    await libraryStore.refreshAllPlaylists()
    toast.success('已创建文件夹')
    // 自动展开父文件夹
    if (parentId != null) {
      const parentIdStr = `${group.id}-folder-${parentId}`
      if (!expandedIds.value.includes(parentIdStr)) {
        expandedIds.value.push(parentIdStr)
      }
    }
    newFolderDialog.value.open = false
  } catch (e) {
    toast.error('创建文件夹失败', e?.response?.data?.detail || e.message || String(e), e)
  }
}

// ==================== 双击重命名 ====================
function startRename(item, event) {
  if (item.isSystem) return
  if (item.isOffline) {
    toast.warning('节点离线无法重命名', '该对象来源节点当前不可用')
    return
  }
  event.stopPropagation()
  renaming.value = {
    id: item.id,
    value: item.label,
    saving: false
  }
  nextTick(() => {
    if (renameInputEl.value) {
      renameInputEl.value.focus()
      renameInputEl.value.select()
    }
  })
}

async function commitRename(item) {
  if (renaming.value.saving) return
  if (renaming.value.id !== item.id) return
  const newName = (renaming.value.value || '').trim()
  if (!newName) {
    toast.warning('名称不能为空')
    return
  }
  if (newName === item.label) {
    renaming.value = { id: '', value: '', saving: false }
    return
  }

  renaming.value.saving = true
  try {
    if (item.type === 'node-playlist') {
      const node = nodesStore.getNode(item.nodeId)
      if (!node) {
        toast.error('节点未连接')
        return
      }
      await updatePlaylist(node, item.playlistId, { name: newName })
    } else if (item.type === 'client-playlist') {
      await updateClientPlaylist(item.playlistId, { name: newName })
    } else if (item.type === 'node-folder') {
      const node = nodesStore.getNode(item.nodeId)
      if (!node) {
        toast.error('节点未连接')
        return
      }
      await updatePlaylistFolder(node, item.folderId, { name: newName })
    } else if (item.type === 'client-folder') {
      await updateClientPlaylistFolder(item.folderId, { name: newName })
    }
    await libraryStore.refreshAllPlaylists()
    toast.success('已重命名')
  } catch (e) {
    toast.error('重命名失败', e?.response?.data?.detail || e.message || String(e), e)
  } finally {
    renaming.value = { id: '', value: '', saving: false }
  }
}

function cancelRename() {
  if (renaming.value.saving) return
  renaming.value = { id: '', value: '', saving: false }
}

function onRenameKeydown(item, event) {
  if (event.key === 'Enter') {
    event.preventDefault()
    commitRename(item)
  } else if (event.key === 'Escape') {
    event.preventDefault()
    cancelRename()
  }
}

// ==================== 右键菜单 ====================
function onContextmenu(item, event) {
  event.preventDefault()
  event.stopPropagation()
  if (item.isSystem) return
  if (item.isOffline) {
    toast.warning('节点离线无法操作', '该对象来源节点当前不可用')
    return
  }
  closeContextMenu()
  contextMenu.value = {
    visible: true,
    x: event.clientX,
    y: event.clientY,
    item
  }
}

function closeContextMenu() {
  contextMenu.value.visible = false
}

async function onDeleteFromMenu() {
  const item = contextMenu.value.item
  closeContextMenu()
  if (!item || item.isSystem) return

  const isFolder = item.isFolder
  const message = isFolder
    ? `确定删除文件夹「${item.label}」？文件夹内所有子文件夹和播放列表将一并删除，操作不可恢复。`
    : `确定删除播放列表「${item.label}」？该操作不可恢复。`

  const ok = await confirm(message, {
    title: isFolder ? '删除文件夹' : '删除播放列表',
    type: 'warning'
  })
  if (!ok) return

  try {
    if (item.type === 'node-playlist') {
      const node = nodesStore.getNode(item.nodeId)
      if (!node) {
        toast.error('节点未连接')
        return
      }
      await deletePlaylist(node, item.playlistId)
    } else if (item.type === 'client-playlist') {
      await deleteClientPlaylist(item.playlistId)
    } else if (item.type === 'node-folder') {
      const node = nodesStore.getNode(item.nodeId)
      if (!node) {
        toast.error('节点未连接')
        return
      }
      await deletePlaylistFolder(node, item.folderId)
    } else if (item.type === 'client-folder') {
      await deleteClientPlaylistFolder(item.folderId)
    }
    if (currentKey.value === item.id) {
      currentKey.value = 'client-all'
      libraryStore.loadAllTracks()
    }
    await libraryStore.refreshAllPlaylists()
    toast.success(isFolder ? '文件夹已删除' : '已删除')
  } catch (e) {
    toast.error('删除失败', e?.response?.data?.detail || e.message || String(e), e)
  }
}

async function onRenameFromMenu() {
  const item = contextMenu.value.item
  closeContextMenu()
  if (!item || item.isSystem) return
  // 触发原地重命名
  renaming.value = {
    id: item.id,
    value: item.label,
    saving: false
  }
  nextTick(() => {
    if (renameInputEl.value) {
      renameInputEl.value.focus()
      renameInputEl.value.select()
    }
  })
}

function onCreateSubfolderFromMenu() {
  const item = contextMenu.value.item
  closeContextMenu()
  if (!item || !item.isFolder) return
  const groupId = item.type.startsWith('node-') ? `node-${item.nodeId}` : 'client-group'
  const targetGroup = treeData.value.find((g) => g.id === groupId)
  if (!targetGroup) return
  onCreateFolder(targetGroup, item.folderId)
}

function onCreatePlaylistFromMenu() {
  const item = contextMenu.value.item
  closeContextMenu()
  if (!item || !item.isFolder) return
  const groupId = item.type.startsWith('node-') ? `node-${item.nodeId}` : 'client-group'
  const targetGroup = treeData.value.find((g) => g.id === groupId)
  if (!targetGroup) return
  onCreatePlaylist(targetGroup, item.folderId)
}

// 全局点击关闭右键菜单
function onGlobalClick() {
  if (contextMenu.value.visible) closeContextMenu()
}

// ==================== 拖拽移动 ====================
async function onDropToFolder(dragged, targetFolder) {
  if (!dragged || !targetFolder || !targetFolder.isFolder) return
  if (dragged.id === targetFolder.id) return
  if (isDescendantOf(targetFolder, dragged)) {
    toast.warning('无法移动', '目标文件夹是源文件夹的后代')
    return
  }

  try {
    if (dragged.type === 'node-playlist') {
      const node = nodesStore.getNode(dragged.nodeId)
      if (!node) {
        toast.error('节点未连接')
        return
      }
      await updatePlaylist(node, dragged.playlistId, { folder_id: targetFolder.folderId })
    } else if (dragged.type === 'client-playlist') {
      await updateClientPlaylist(dragged.playlistId, { folder_id: targetFolder.folderId })
    } else if (dragged.type === 'node-folder') {
      const node = nodesStore.getNode(dragged.nodeId)
      if (!node) {
        toast.error('节点未连接')
        return
      }
      await updatePlaylistFolder(node, dragged.folderId, { parent_id: targetFolder.folderId })
    } else if (dragged.type === 'client-folder') {
      await updateClientPlaylistFolder(dragged.folderId, { parent_id: targetFolder.folderId })
    }
    // 展开目标文件夹以显示移动后的内容
    if (!expandedIds.value.includes(targetFolder.id)) {
      expandedIds.value.push(targetFolder.id)
    }
    await libraryStore.refreshAllPlaylists()
    toast.success('已移动')
  } catch (e) {
    toast.error('移动失败', e?.response?.data?.detail || e.message || String(e), e)
  }
}

/**
 * 拖拽到分组标题（移到根级）
 */
async function onDropToGroup(event, group) {
  event.preventDefault()
  dragOverGroup.value = ''
  if (!dragging.value) return
  const dragged = dragging.value
  // 仅处理同分组内的拖拽到根级
  const dragGroupId = dragged.type.startsWith('node-') ? `node-${dragged.nodeId}` : 'client-group'
  if (dragGroupId !== group.id) {
    toast.warning('无法跨分组移动')
    return
  }

  try {
    if (dragged.type === 'node-playlist') {
      const node = nodesStore.getNode(dragged.nodeId)
      if (!node) return
      await updatePlaylist(node, dragged.playlistId, { folder_id: 0 })
    } else if (dragged.type === 'client-playlist') {
      await updateClientPlaylist(dragged.playlistId, { folder_id: 0 })
    } else if (dragged.type === 'node-folder') {
      const node = nodesStore.getNode(dragged.nodeId)
      if (!node) return
      await updatePlaylistFolder(node, dragged.folderId, { parent_id: 0 })
    } else if (dragged.type === 'client-folder') {
      await updateClientPlaylistFolder(dragged.folderId, { parent_id: 0 })
    }
    await libraryStore.refreshAllPlaylists()
    toast.success('已移到根级')
  } catch (e) {
    toast.error('移动失败', e?.response?.data?.detail || e.message || String(e), e)
  }
}

function onGroupDragOver(event, group) {
  if (!dragging.value) return
  const dragGroupId = dragging.value.type.startsWith('node-')
    ? `node-${dragging.value.nodeId}`
    : 'client-group'
  if (dragGroupId !== group.id) return
  event.preventDefault()
  event.dataTransfer.dropEffect = 'move'
  dragOverGroup.value = group.id
}

function onGroupDragLeave() {
  dragOverGroup.value = ''
}

// ==================== 提供给子组件的方法 ====================
provide('playlistTreeActions', {
  onNodeClick,
  toggleExpand,
  startRename,
  commitRename,
  onContextmenu,
  onRenameKeydown,
  setRenameRef,
  onDropToFolder,
  isDescendantOf
})

function goNodes() {
  router.push('/nodes')
}

onMounted(() => {
  expandedIds.value = treeData.value.map((g) => g.id)
  currentKey.value = 'client-all'
  libraryStore.loadAllTracks()
  if (typeof window !== 'undefined') {
    window.addEventListener('click', onGlobalClick)
    window.addEventListener('blur', closeContextMenu)
  }
})
</script>

<template>
  <div class="flex h-full flex-col" @contextmenu.prevent>
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

    <!-- 无任何节点：引导 -->
    <div
      v-if="nodesStore.nodes.length === 0"
      class="flex flex-1 flex-col items-center justify-center gap-4 px-4 py-8"
    >
      <Empty :icon="Unplug" description="尚未添加任何节点" />
      <Button variant="default" size="sm" @click="goNodes">
        去添加 / 登录节点
      </Button>
    </div>

    <!-- 树：节点分组 + 客户端分组 -->
    <div v-else class="flex-1 overflow-auto px-2 pb-3">
      <template v-for="group in treeData" :key="group.id">
        <!-- 一级：分组标题 -->
        <div
          class="group flex items-center gap-1 rounded-md px-1.5 py-1.5 text-sm cursor-pointer transition-colors hover:bg-accent/50"
          :class="[
            isExpanded(group.id) ? 'bg-accent/30' : '',
            group.isOffline ? 'opacity-60' : '',
            dragOverGroup === group.id ? 'ring-2 ring-primary ring-inset' : ''
          ]"
          :title="group.isOffline ? '节点离线·展示缓存数据' : ''"
          @click="onNodeClick(group)"
          @dragover="onGroupDragOver($event, group)"
          @dragleave="onGroupDragLeave"
          @drop="onDropToGroup($event, group)"
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
          <span
            v-if="group.isOffline"
            class="text-[10px] text-amber-500 shrink-0"
            title="节点离线"
          >离线</span>
          <!-- 新建文件夹 -->
          <button
            v-if="group.canCreate"
            class="flex h-5 w-5 shrink-0 items-center justify-center rounded text-muted-foreground hover:bg-accent hover:text-primary"
            title="新建文件夹"
            @click.stop="onCreateFolder(group, null)"
          >
            <FolderPlus class="h-4 w-4" />
          </button>
          <!-- 新建播放列表 -->
          <button
            v-if="group.canCreate"
            class="flex h-5 w-5 shrink-0 items-center justify-center rounded text-muted-foreground hover:bg-accent hover:text-primary"
            title="新建播放列表"
            @click.stop="onCreatePlaylist(group, null)"
          >
            <Plus class="h-4 w-4" />
          </button>
        </div>

        <!-- 根级子节点（系统列表 + 根文件夹 + 根播放列表） -->
        <div v-if="isExpanded(group.id)" class="mt-0.5 space-y-0.5">
          <PlaylistTreeNode
            v-for="child in group.rootChildren"
            :key="child.id"
            :node="child"
            :level="1"
          />
        </div>
      </template>
    </div>

    <!-- 右键菜单 -->
    <div
      v-if="contextMenu.visible"
      class="fixed z-50 min-w-[160px] rounded-md border border-border bg-popover p-1 shadow-md"
      :style="{ left: contextMenu.x + 'px', top: contextMenu.y + 'px' }"
      @click.stop
    >
      <!-- 文件夹：新建子项 -->
      <template v-if="contextMenu.item && contextMenu.item.isFolder">
        <button
          class="flex w-full items-center gap-2 rounded px-2 py-1.5 text-sm text-foreground hover:bg-accent"
          @click="onCreateSubfolderFromMenu"
        >
          <FolderPlus class="h-4 w-4" />
          新建子文件夹
        </button>
        <button
          class="flex w-full items-center gap-2 rounded px-2 py-1.5 text-sm text-foreground hover:bg-accent"
          @click="onCreatePlaylistFromMenu"
        >
          <Plus class="h-4 w-4" />
          新建播放列表
        </button>
        <div class="my-1 h-px bg-border" />
      </template>
      <!-- 重命名 -->
      <button
        v-if="contextMenu.item && !contextMenu.item.isSystem"
        class="flex w-full items-center gap-2 rounded px-2 py-1.5 text-sm text-foreground hover:bg-accent"
        @click="onRenameFromMenu"
      >
        <Pencil class="h-4 w-4" />
        重命名
      </button>
      <!-- 删除 -->
      <button
        v-if="contextMenu.item && !contextMenu.item.isSystem"
        class="flex w-full items-center gap-2 rounded px-2 py-1.5 text-sm text-destructive hover:bg-destructive/10"
        @click="onDeleteFromMenu"
      >
        <Trash2 class="h-4 w-4" />
        {{ contextMenu.item && contextMenu.item.isFolder ? '删除文件夹' : '删除播放列表' }}
      </button>
    </div>

    <!-- 新建播放列表弹窗 -->
    <NewPlaylistDialog
      v-model:open="newPlaylistDialog.open"
      :group="newPlaylistDialog.group"
      :folder-id="newPlaylistDialog.folderId"
      @created="onPlaylistCreated"
    />

    <!-- 新建文件夹弹窗 -->
    <div
      v-if="newFolderDialog.open"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      @click.self="newFolderDialog.open = false"
    >
      <div class="w-80 rounded-md border border-border bg-popover p-4 shadow-lg">
        <div class="mb-3 text-sm font-semibold">新建文件夹</div>
        <input
          v-model="newFolderDialog.name"
          class="w-full rounded-md border border-border bg-background px-3 py-2 text-sm outline-none focus:ring-1 focus:ring-primary"
          placeholder="文件夹名称"
          autofocus
          @keydown.enter="onSubmitCreateFolder"
          @keydown.escape="newFolderDialog.open = false"
        >
        <div class="mt-4 flex justify-end gap-2">
          <Button variant="outline" size="sm" @click="newFolderDialog.open = false">取消</Button>
          <Button size="sm" @click="onSubmitCreateFolder">创建</Button>
        </div>
      </div>
    </div>
  </div>
</template>
