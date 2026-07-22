<script setup>
import { computed, inject, ref } from 'vue'
import {
  ChevronRight, ChevronDown, Folder, FolderOpen, ListMusic, Library, Inbox
} from 'lucide-vue-next'

defineOptions({ name: 'PlaylistTreeNode' })

const props = defineProps({
  node: { type: Object, required: true },
  level: { type: Number, default: 0 }
})

// 注入共享状态与方法（由 PlaylistTree 提供）
const treeState = inject('playlistTreeState')
const treeActions = inject('playlistTreeActions')

// 本节点是否正在被拖拽
const isDragOver = ref(false)

const isExpanded = computed(() => treeState.expandedIds.value.includes(props.node.id))
const isRenaming = computed(() => treeState.renaming.value.id === props.node.id)
const isCurrent = computed(() => treeState.currentKey.value === props.node.id)
const isOffline = computed(() => !!props.node.isOffline)

const isFolder = computed(() => !!props.node.isFolder)
const isSystem = computed(() => !!props.node.isSystem)
const canDrag = computed(() => !isSystem.value && !isOffline.value)

function nodeIcon() {
  if (isFolder.value) return isExpanded.value ? FolderOpen : Folder
  const t = props.node.type
  if (t === 'node-all' || t === 'client-all') return Library
  if (t === 'node-inbox') return Inbox
  return ListMusic
}

function onClick() {
  treeActions.onNodeClick(props.node)
}

function onToggleExpand(event) {
  event.stopPropagation()
  treeActions.toggleExpand(props.node.id)
}

function onDblClick(event) {
  treeActions.startRename(props.node, event)
}

function onContextmenu(event) {
  treeActions.onContextmenu(props.node, event)
}

function onRenameKeydown(event) {
  treeActions.onRenameKeydown(props.node, event)
}

function onRenameBlur() {
  treeActions.commitRename(props.node)
}

function onDragStart(event) {
  if (!canDrag.value) {
    event.preventDefault()
    return
  }
  treeState.dragging.value = props.node
  event.dataTransfer.effectAllowed = 'move'
  // Firefox 需要 setData 才能触发拖拽
  event.dataTransfer.setData('text/plain', String(props.node.id))
}

function onDragEnd() {
  treeState.dragging.value = null
  isDragOver.value = false
}

function onDragOver(event) {
  // 仅文件夹可作为 drop 目标；非系统列表（全部音乐/收集箱）不能放入
  if (!isFolder.value) return
  if (!treeState.dragging.value) return
  // 不能拖到自身
  if (treeState.dragging.value.id === props.node.id) return
  // 防止将文件夹拖入自己的后代
  if (treeActions.isDescendantOf(treeState.dragging.value, props.node)) return
  event.preventDefault()
  event.dataTransfer.dropEffect = 'move'
  isDragOver.value = true
}

function onDragLeave() {
  isDragOver.value = false
}

function onDrop(event) {
  event.preventDefault()
  isDragOver.value = false
  if (!isFolder.value || !treeState.dragging.value) return
  treeActions.onDropToFolder(treeState.dragging.value, props.node)
}
</script>

<template>
  <div>
    <div
      class="flex items-center gap-1.5 rounded-md py-1.5 pr-2 text-sm cursor-pointer transition-colors select-none"
      :class="[
        isCurrent ? 'bg-primary/10 text-primary' : 'text-foreground hover:bg-accent/50',
        isOffline ? 'opacity-60' : '',
        isDragOver ? 'ring-2 ring-primary ring-inset bg-primary/5' : ''
      ]"
      :style="{ paddingLeft: (level * 14 + 8) + 'px' }"
      :draggable="canDrag"
      @click="onClick"
      @dblclick="onDblClick"
      @contextmenu="onContextmenu"
      @dragstart="onDragStart"
      @dragend="onDragEnd"
      @dragover="onDragOver"
      @dragleave="onDragLeave"
      @drop="onDrop"
    >
      <!-- 展开/折叠箭头（仅文件夹） -->
      <button
        v-if="isFolder"
        class="flex h-5 w-5 shrink-0 items-center justify-center rounded text-muted-foreground hover:bg-accent hover:text-foreground"
        @click="onToggleExpand"
      >
        <component :is="isExpanded ? ChevronDown : ChevronRight" class="h-4 w-4" />
      </button>
      <!-- 占位（叶子节点保持对齐） -->
      <span v-else class="w-5 shrink-0" />

      <component
        :is="nodeIcon()"
        class="h-4 w-4 shrink-0"
        :class="isCurrent ? 'text-primary' : 'text-muted-foreground'"
      />

      <!-- 原地重命名输入框 -->
      <input
        v-if="isRenaming"
        :ref="treeActions.setRenameRef"
        v-model="treeState.renaming.value.value"
        class="flex-1 min-w-0 bg-secondary/80 border border-primary rounded px-1.5 py-0.5 text-sm text-foreground outline-none focus:ring-1 focus:ring-primary"
        :disabled="treeState.renaming.value.saving"
        @click.stop
        @dblclick.stop
        @keydown="onRenameKeydown"
        @blur="onRenameBlur"
      />
      <span v-else class="truncate flex-1">{{ node.label }}</span>

      <!-- 离线标记 -->
      <span v-if="isOffline" class="text-[10px] text-amber-500 shrink-0">离线</span>
    </div>

    <!-- 文件夹子节点（递归） -->
    <template v-if="isFolder && isExpanded">
      <PlaylistTreeNode
        v-for="child in node.children"
        :key="child.id"
        :node="child"
        :level="level + 1"
      />
      <!-- 空文件夹提示 -->
      <div
        v-if="!node.children || node.children.length === 0"
        class="text-xs text-muted-foreground italic"
        :style="{ paddingLeft: ((level + 1) * 14 + 8 + 21) + 'px' }"
      >
        （空）
      </div>
    </template>
  </div>
</template>
