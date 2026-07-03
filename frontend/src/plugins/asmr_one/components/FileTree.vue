<script setup>
import { computed, ref } from 'vue'
import {
  Folder,
  FolderOpen,
  FileAudio,
  FileText,
  ChevronRight,
  Check,
  Square,
  Eye,
  Play,
  FileImage
} from 'lucide-vue-next'

const props = defineProps({
  node: { type: Object, required: true },
  level: { type: Number, default: 0 },
  selectedPaths: { type: Set, default: () => new Set() },
  pathPrefix: { type: String, default: '' }
})

const emit = defineEmits(['toggle', 'preview'])

const expanded = ref(props.node.type === 'folder' ? props.level < 1 : false)

const isFolder = computed(() => props.node.type === 'folder')
const isAudio = computed(() => props.node.type === 'audio')
const isFile = computed(() => props.node.type === 'file')

// 文件扩展名分类
const ext = computed(() => {
  const title = props.node.title || ''
  const i = title.lastIndexOf('.')
  return i >= 0 ? title.slice(i + 1).toLowerCase() : ''
})
const isImage = computed(() => ['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp', 'svg'].includes(ext.value))
const isText = computed(() => ['txt', 'md', 'lyc', 'srt', 'vtt', 'json', 'lrc'].includes(ext.value))
const isVideo = computed(() => ['mp4', 'webm', 'mkv', 'avi', 'mov'].includes(ext.value))
const canPreview = computed(() => isAudio.value || isImage.value || isText.value || isVideo.value)

const hasChildren = computed(
  () => isFolder.value && Array.isArray(props.node.children) && props.node.children.length > 0
)

const fullPath = computed(() => {
  const p = props.node.title || ''
  return props.pathPrefix ? `${props.pathPrefix}/${p}` : p
})

const allLeafPaths = computed(() => {
  if (!isFolder.value) return [fullPath.value]
  const out = []
  const walk = (n, prefix) => {
    const p = n.title || ''
    const cur = prefix ? `${prefix}/${p}` : p
    if (n.type === 'folder') {
      for (const c of n.children || []) walk(c, cur)
    } else {
      out.push(cur)
    }
  }
  walk(props.node, props.pathPrefix)
  return out
})

const checked = computed(() => {
  if (isFolder.value) {
    const leaves = allLeafPaths.value
    return leaves.length > 0 && leaves.every((p) => props.selectedPaths.has(p))
  }
  return props.selectedPaths.has(fullPath.value)
})

function toggleFolder() {
  if (isFolder.value) expanded.value = !expanded.value
}

function onPreview(e) {
  e.stopPropagation()
  emit('preview', {
    node: props.node,
    fullPath: fullPath.value,
    type: isAudio.value ? 'audio' : isImage.value ? 'image' : isVideo.value ? 'video' : isText.value ? 'text' : 'other'
  })
}

function onChildPreview(payload) {
  emit('preview', payload)
}

function onCheck(e) {
  e.stopPropagation()
  const paths = allLeafPaths.value
  emit('toggle', { paths, selected: !checked.value })
}

function onChildToggle(payload) {
  emit('toggle', payload)
}

function formatSize(bytes) {
  if (!bytes) return ''
  if (bytes >= 1024 * 1024 * 1024) return (bytes / 1024 / 1024 / 1024).toFixed(2) + ' GB'
  if (bytes >= 1024 * 1024) return (bytes / 1024 / 1024).toFixed(1) + ' MB'
  if (bytes >= 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return bytes + ' B'
}

function formatDuration(sec) {
  if (!sec) return ''
  const m = Math.floor(sec / 60)
  const s = Math.floor(sec % 60)
  return `${m}:${String(s).padStart(2, '0')}`
}
</script>

<template>
  <div>
    <div
      class="flex items-center gap-2 py-1.5 px-2 rounded hover:bg-accent/50 cursor-pointer"
      :style="{ paddingLeft: `${level * 16 + 8}px` }"
      @click="isFolder ? toggleFolder() : onCheck($event)"
    >
      <button class="flex h-4 w-4 items-center justify-center" @click.stop="onCheck">
        <Check v-if="checked" class="h-4 w-4 text-primary" />
        <Square v-else class="h-3.5 w-3.5 text-muted-foreground" />
      </button>

      <button v-if="isFolder" class="flex h-4 w-4 items-center justify-center" @click.stop="toggleFolder">
        <ChevronRight class="h-3.5 w-3.5 transition-transform" :class="{ 'rotate-90': expanded }" />
      </button>
      <Folder v-if="isFolder && !expanded" class="h-4 w-4 text-amber-400" />
      <FolderOpen v-else-if="isFolder && expanded" class="h-4 w-4 text-amber-400" />
      <FileAudio v-else-if="isAudio" class="h-4 w-4 text-emerald-400" />
      <FileImage v-else-if="isImage" class="h-4 w-4 text-sky-400" />
      <FileText v-else class="h-4 w-4 text-muted-foreground" />

      <span class="flex-1 truncate text-sm" :class="isFolder ? 'font-medium text-foreground' : 'text-muted-foreground'">
        {{ node.title }}
      </span>

      <span v-if="isAudio && node.duration" class="text-xs text-muted-foreground tabular-nums">
        {{ formatDuration(node.duration) }}
      </span>
      <span v-if="node.size" class="text-xs text-muted-foreground tabular-nums">
        {{ formatSize(node.size) }}
      </span>

      <!-- 预览按钮 -->
      <button
        v-if="canPreview"
        class="flex h-5 w-5 items-center justify-center rounded hover:bg-accent text-muted-foreground hover:text-primary shrink-0"
        title="预览"
        @click="onPreview"
      >
        <Play v-if="isAudio || isVideo" class="h-3.5 w-3.5" />
        <Eye v-else class="h-3.5 w-3.5" />
      </button>
    </div>

    <div v-if="isFolder && expanded && hasChildren">
      <FileTree
        v-for="(child, idx) in node.children"
        :key="idx"
        :node="child"
        :level="level + 1"
        :selected-paths="selectedPaths"
        :path-prefix="fullPath"
        @toggle="onChildToggle"
        @preview="onChildPreview"
      />
    </div>
  </div>
</template>
