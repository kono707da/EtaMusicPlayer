<script setup>
import { computed, ref, watch, nextTick, onUnmounted } from 'vue'
import { Check, Loader2, Play, Plus, Columns3, Music, Pencil, ListMusic } from 'lucide-vue-next'
import { useToast } from '@/components/ui/toast/use-toast'
import { usePlayerStore } from '../stores/player'
import { useAuthStore } from '../stores/auth'
import { useLibraryStore } from '../stores/library'
import { getCoverUrl, updateMetadataField, addTracksToPlaylist } from '../api/node'
import { addClientPlaylistItems } from '../api/client_playlist'
import AddToPlaylistDialog from './AddToPlaylistDialog.vue'
import MetadataPanel from './MetadataPanel.vue'
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell
} from '@/components/ui/table'
import { Pagination } from '@/components/ui/pagination'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'

const props = defineProps({
  // 曲目数组
  tracks: { type: Array, default: () => [] },
  // 来源节点信息（用于播放时标注）
  nodeId: { type: [Number, String], default: null },
  nodeName: { type: String, default: '' },
  // 是否显示来源节点列（跨节点搜索时显示）
  showSource: { type: Boolean, default: false },
  // 是否显示分页
  showPagination: { type: Boolean, default: true },
  total: { type: Number, default: 0 },
  page: { type: Number, default: 1 },
  pageSize: { type: Number, default: 20 },
  loading: { type: Boolean, default: false }
})

const emit = defineEmits([
  'page-change',
  'selection-change',
  'row-dblclick',
  'metadata-updated'
])

const player = usePlayerStore()
const toast = useToast()
const authStore = useAuthStore()
const libraryStore = useLibraryStore()

// 加入到播放列表对话框
const addToPlaylistVisible = ref(false)
const addToPlaylistTracks = ref([])

// ==================== 列配置 ====================

const STORAGE_KEY = 'trackTable.visibleColumns'

/**
 * 列目录：覆盖 TrackOut 全部字段 + 封面缩略图 + 行号
 * 每列定义: { key, label, category, defaultVisible, width, cellClass }
 */
const COLUMN_CATALOG = [
  // 基础（默认显示）
  { key: 'cover', label: '封面', category: 'basic', defaultVisible: true, width: 'w-14' },
  { key: 'index', label: '#', category: 'basic', defaultVisible: true, width: 'w-10' },
  { key: 'title', label: '标题', category: 'basic', defaultVisible: true, cellClass: 'font-medium text-foreground' },
  { key: 'artist', label: '艺术家', category: 'basic', defaultVisible: true },
  { key: 'album', label: '专辑', category: 'basic', defaultVisible: true },
  { key: 'duration', label: '时长', category: 'basic', defaultVisible: true, width: 'w-20', cellClass: 'tabular-nums' },
  // 元数据
  { key: 'album_artist', label: '专辑艺术家', category: 'metadata' },
  { key: 'track_no', label: '音轨号', category: 'metadata', width: 'w-16', cellClass: 'tabular-nums' },
  { key: 'year', label: '年份', category: 'metadata', width: 'w-16', cellClass: 'tabular-nums' },
  { key: 'genre', label: '流派', category: 'metadata' },
  // 音频质量
  { key: 'ext', label: '格式', category: 'quality', width: 'w-16' },
  { key: 'bitrate', label: '比特率', category: 'quality', width: 'w-24', cellClass: 'tabular-nums' },
  { key: 'sample_rate', label: '采样率', category: 'quality', width: 'w-24', cellClass: 'tabular-nums' },
  { key: 'channels', label: '声道', category: 'quality', width: 'w-20' },
  { key: 'format_priority', label: '格式优先级', category: 'quality', width: 'w-24', cellClass: 'tabular-nums' },
  { key: 'quality_score', label: '质量评分', category: 'quality', width: 'w-20', cellClass: 'tabular-nums' },
  // 文件信息
  { key: 'file_size', label: '文件大小', category: 'file', width: 'w-24', cellClass: 'tabular-nums' },
  { key: 'filename', label: '文件名', category: 'file' },
  { key: 'rel_path', label: '相对路径', category: 'file' },
  { key: 'cover_embedded', label: '内嵌封面', category: 'file', width: 'w-20' },
  { key: 'lyrics_embedded', label: '内嵌歌词', category: 'file', width: 'w-20' },
  // 时间戳
  { key: 'created_at', label: '创建时间', category: 'timestamps', width: 'w-36', cellClass: 'tabular-nums' },
  { key: 'updated_at', label: '更新时间', category: 'timestamps', width: 'w-36', cellClass: 'tabular-nums' },
  // 系统
  { key: 'id', label: 'ID', category: 'system', width: 'w-16', cellClass: 'tabular-nums' },
  { key: 'watch_dir_id', label: '监控目录ID', category: 'system', width: 'w-24', cellClass: 'tabular-nums' }
]

const CATEGORY_LABELS = {
  basic: '基础',
  metadata: '元数据',
  quality: '音频质量',
  file: '文件信息',
  timestamps: '时间戳',
  system: '系统'
}

const CATEGORY_ORDER = ['basic', 'metadata', 'quality', 'file', 'timestamps', 'system']

// 按分类分组的列目录（用于列设置面板）
const catalogGroups = computed(() =>
  CATEGORY_ORDER.map((cat) => ({
    category: cat,
    label: CATEGORY_LABELS[cat],
    columns: COLUMN_CATALOG.filter((c) => c.category === cat)
  }))
)

// 加载持久化的列配置
function loadVisibleColumns() {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved) {
      const arr = JSON.parse(saved)
      if (Array.isArray(arr)) {
        // 过滤掉已不存在的列
        const validKeys = new Set(COLUMN_CATALOG.map((c) => c.key))
        return new Set(arr.filter((k) => validKeys.has(k)))
      }
    }
  } catch {
    // ignore
  }
  return new Set(COLUMN_CATALOG.filter((c) => c.defaultVisible).map((c) => c.key))
}

const visibleColumns = ref(loadVisibleColumns())

// 持久化
watch(
  visibleColumns,
  (val) => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify([...val]))
    } catch {
      // ignore
    }
  },
  { deep: true }
)

function toggleColumn(key) {
  const next = new Set(visibleColumns.value)
  if (next.has(key)) next.delete(key)
  else next.add(key)
  visibleColumns.value = next
}

// 当前激活的列（按 CATALOG 顺序）
const activeColumns = computed(() =>
  COLUMN_CATALOG.filter((c) => visibleColumns.value.has(c.key))
)

// 列设置面板
const showColumnPanel = ref(false)

function closeColumnPanel() {
  showColumnPanel.value = false
}

// ==================== 多选（单击/Ctrl/Shift） ====================

const selection = ref([])
// shift 连选的起点索引
const lastSelectedIndex = ref(null)

function isSelected(row) {
  return selection.value.some((r) => r.id === row.id)
}

function onRowClick(row, idx, event) {
  // 正在行内编辑时不处理选中
  if (inlineEdit.value.rowId != null) return

  if (event.ctrlKey || event.metaKey) {
    // Ctrl/Cmd+Click：切换该行选中
    const i = selection.value.findIndex((r) => r.id === row.id)
    if (i > -1) {
      selection.value.splice(i, 1)
    } else {
      selection.value.push(row)
    }
    lastSelectedIndex.value = idx
  } else if (event.shiftKey && lastSelectedIndex.value != null) {
    // Shift+Click：从上次选中的起点到当前行范围选中
    const start = Math.min(lastSelectedIndex.value, idx)
    const end = Math.max(lastSelectedIndex.value, idx)
    selection.value = tableData.value.slice(start, end + 1)
  } else {
    // 普通单击：只选中该行
    selection.value = [row]
    lastSelectedIndex.value = idx
  }
  emit('selection-change', selection.value)
}

// ESC 清空选中
function onKeydownEsc(e) {
  if (e.key === 'Escape' && selection.value.length > 0 && inlineEdit.value.rowId == null) {
    selection.value = []
    lastSelectedIndex.value = null
    emit('selection-change', selection.value)
  }
}
if (typeof window !== 'undefined') {
  window.addEventListener('keydown', onKeydownEsc)
}
onUnmounted(() => {
  if (typeof window !== 'undefined') {
    window.removeEventListener('keydown', onKeydownEsc)
  }
})

// 全选（Ctrl+A 在表格内时可用，暂不绑定快捷键，保留方法供外部调用）
function selectAll() {
  selection.value = [...tableData.value]
  emit('selection-change', selection.value)
}

// ==================== 播放 ====================

// 双击播放当前列表
// 注意：模板 v-for 渲染的是 tableData（props.tracks 的克隆），不能用 indexOf(row)
// 必须传 idx（相对于 tableData 的下标 = 相对于 props.tracks 的下标）
function onRowDblclick(row, idx) {
  emit('row-dblclick', row)
  if (row.__nodeId == null) {
    toast.warning('缺少来源节点信息', '无法播放')
    return
  }
  const startIndex = (idx != null && idx >= 0) ? idx : 0
  player.playTracks(props.tracks, startIndex)
}

// ==================== 右键菜单 ====================

const contextMenu = ref({ visible: false, x: 0, y: 0, row: null })
function onRowContextmenu(row, idx, event) {
  event.preventDefault()
  // 右键的行不在当前选中中时，把选中重置为该行
  if (!isSelected(row)) {
    selection.value = [row]
    lastSelectedIndex.value = idx
    emit('selection-change', selection.value)
  }
  contextMenu.value = {
    visible: true,
    x: event.clientX,
    y: event.clientY,
    row
  }
}
function closeContextMenu() {
  contextMenu.value.visible = false
  closeColumnPanel()
}

// 右键：添加到播放队列
function addToQueue() {
  const row = contextMenu.value.row
  if (!row) return
  player.appendTracks([row])
  toast.success('已加入播放队列')
  closeContextMenu()
}

// 右键：加入到播放列表
function addToPlaylist() {
  const tracks = selection.value.length > 0 ? selection.value : [contextMenu.value.row]
  addToPlaylistTracks.value = tracks.filter(Boolean)
  addToPlaylistVisible.value = true
  closeContextMenu()
}

function onAddToPlaylistDone() {
  addToPlaylistVisible.value = false
  toast.success('已添加到播放列表')
}

// 右键：播放此曲
function playThis() {
  const row = contextMenu.value.row
  if (!row) return
  onRowDblclick(row)
  closeContextMenu()
}

// 右键：编辑元数据（调出右侧 MetadataPanel）
// 右键时已同步选中状态，这里直接用 selection
const metadataPanelVisible = ref(false)
const metadataPanelTracks = ref([])
function editMetadata() {
  if (selection.value.length === 0) {
    closeContextMenu()
    return
  }
  metadataPanelTracks.value = selection.value.slice()
  metadataPanelVisible.value = true
  closeContextMenu()
}

// MetadataPanel 保存成功后的回调
function onMetadataUpdated() {
  emit('metadata-updated')
}

// ==================== 行内双击编辑 ====================

// 可行内编辑的字段（与后端 EDITABLE_FIELDS 一致）
const INLINE_EDITABLE_FIELDS = new Set([
  'title', 'artist', 'album', 'album_artist', 'track_no', 'year', 'genre'
])

// 行内编辑状态：{ rowId, field, value, saving }
const inlineEdit = ref({ rowId: null, field: null, value: '', saving: false })
const inlineEditInputRef = ref(null)

function isInlineEditing(row, colKey) {
  return inlineEdit.value.rowId === row.id && inlineEdit.value.field === colKey
}

function startInlineEdit(row, colKey, event) {
  // 仅 admin 可编辑
  if (!authStore.isAdmin) {
    toast.warning('需要管理员权限', '只有管理员可以编辑元数据')
    return
  }
  if (!INLINE_EDITABLE_FIELDS.has(colKey)) return
  // 阻止冒泡到 onRowDblclick（避免触发播放）
  if (event) {
    event.stopPropagation()
    event.preventDefault()
  }
  inlineEdit.value = {
    rowId: row.id,
    field: colKey,
    value: row[colKey] != null ? String(row[colKey]) : '',
    saving: false
  }
  nextTick(() => {
    if (inlineEditInputRef.value) {
      inlineEditInputRef.value.focus()
      inlineEditInputRef.value.select()
    }
  })
}

async function commitInlineEdit(row) {
  if (inlineEdit.value.saving) return
  const { rowId, field, value } = inlineEdit.value
  if (rowId == null || !field) return

  const oldValue = row[field] != null ? String(row[field]) : ''
  const newValue = value ?? ''
  // 值未变化直接退出
  if (oldValue === newValue) {
    inlineEdit.value = { rowId: null, field: null, value: '', saving: false }
    return
  }

  const node = authStore.localNode
  if (!node) {
    toast.error('编辑失败', '未连接节点')
    inlineEdit.value = { rowId: null, field: null, value: '', saving: false }
    return
  }

  inlineEdit.value.saving = true
  try {
    await updateMetadataField(node, [rowId], field, newValue)
    // 更新本地行数据
    if (field === 'track_no' || field === 'year') {
      row[field] = newValue ? parseInt(newValue, 10) : null
    } else {
      row[field] = newValue
    }
    toast.success(`已更新 ${row.title || '该曲目'} 的 ${field}`)
    emit('metadata-updated')
  } catch (e) {
    const detail = e?.response?.data?.detail || e?.message || '未知错误'
    toast.error('编辑失败', `字段 ${field} 保存失败：${detail}`, e)
  } finally {
    inlineEdit.value = { rowId: null, field: null, value: '', saving: false }
  }
}

function cancelInlineEdit() {
  if (inlineEdit.value.saving) return
  inlineEdit.value = { rowId: null, field: null, value: '', saving: false }
}

function onInlineEditKeydown(row, event) {
  if (event.key === 'Enter') {
    event.preventDefault()
    commitInlineEdit(row)
  } else if (event.key === 'Escape') {
    event.preventDefault()
    cancelInlineEdit()
  }
}

// ==================== 分页 ====================

function onPageChange(p) {
  emit('page-change', p)
}

// ==================== 表格数据 ====================

const tableData = computed(() =>
  props.tracks.map((t) => ({
    ...t,
    __nodeId: t.__nodeId || props.nodeId,
    __nodeName: t.__nodeName || props.nodeName
  }))
)

// 空状态 colspan
const emptyColspan = computed(() => 1 + activeColumns.value.length + (props.showSource ? 1 : 0))

// ==================== 格式化器 ====================

function formatDuration(sec) {
  if (sec == null) return '--:--'
  const m = Math.floor(sec / 60)
  const s = Math.floor(sec % 60)
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}

function formatBitrate(bps) {
  if (!bps) return '--'
  return `${Math.round(bps / 1000)} kbps`
}

function formatSampleRate(hz) {
  if (!hz) return '--'
  if (hz >= 1000) return `${(hz / 1000).toFixed(1)} kHz`
  return `${hz} Hz`
}

function formatChannels(ch) {
  if (ch == null) return '--'
  if (ch === 1) return '单声道'
  if (ch === 2) return '立体声'
  return `${ch} 声道`
}

function formatFileSize(bytes) {
  if (!bytes) return '--'
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`
}

function formatBool(v) {
  return v ? '是' : '否'
}

function formatDateTime(dt) {
  if (!dt) return '--'
  try {
    const d = new Date(dt)
    return d.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch {
    return String(dt)
  }
}

function formatCell(row, col) {
  const v = row[col.key]
  switch (col.key) {
    case 'duration':
      return formatDuration(v)
    case 'bitrate':
      return formatBitrate(v)
    case 'sample_rate':
      return formatSampleRate(v)
    case 'channels':
      return formatChannels(v)
    case 'file_size':
      return formatFileSize(v)
    case 'cover_embedded':
    case 'lyrics_embedded':
      return formatBool(v)
    case 'created_at':
    case 'updated_at':
      return formatDateTime(v)
    case 'ext':
      return v ? String(v).toUpperCase() : '--'
    default:
      return v ?? '--'
  }
}

// ==================== 封面 URL ====================

// 已登录节点 id → node 的映射（用于按 track.__nodeId 查找节点生成封面 URL）
const nodeMap = computed(() => {
  const map = new Map()
  for (const n of nodesStore.loggedInNodes) {
    map.set(n.id, n)
  }
  return map
})

function getTrackCoverUrl(row) {
  // 不再仅依赖 cover_embedded：后端 /cover 端点会回退到同级目录 cover.jpg
  const nodeId = row.__nodeId
  if (nodeId == null) return ''
  const node = nodeMap.value.get(nodeId)
  if (!node) return ''
  return getCoverUrl(node, row.id)
}

// 封面加载失败时隐藏 img
function onCoverError(e) {
  e.target.style.display = 'none'
}
</script>

<template>
  <div class="relative flex flex-1 min-h-0 flex-col select-none" @click="closeContextMenu">
    <!-- 表格容器（含 loading 覆盖层） -->
    <div class="relative flex-1 min-h-0 overflow-auto">
      <Table container-class="overflow-visible">
        <TableHeader class="sticky top-0 z-20 bg-card">
          <TableRow class="hover:bg-transparent border-border">
            <!-- 动态列 -->
            <TableHead
              v-for="col in activeColumns"
              :key="col.key"
              class="text-xs font-medium uppercase tracking-wider text-muted-foreground whitespace-nowrap"
              :class="col.width || ''"
            >
              {{ col.label }}
            </TableHead>
            <!-- 来源节点列（条件显示） -->
            <TableHead v-if="showSource" class="w-28 text-xs font-medium uppercase tracking-wider text-muted-foreground">
              来源节点
            </TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          <TableRow
            v-for="(row, idx) in tableData"
            :key="row.id ?? idx"
            class="cursor-pointer"
            :class="isSelected(row) ? 'bg-primary/10' : ''"
            @click="onRowClick(row, idx, $event)"
            @dblclick="onRowDblclick(row, idx)"
            @contextmenu="onRowContextmenu(row, idx, $event)"
          >
            <!-- 动态单元格 -->
            <TableCell
              v-for="col in activeColumns"
              :key="col.key"
              class="text-muted-foreground"
              :class="col.cellClass || ''"
            >
              <!-- 封面缩略图 -->
              <template v-if="col.key === 'cover'">
                <div class="h-10 w-10 overflow-hidden rounded bg-muted/40 flex items-center justify-center">
                  <img
                    v-if="getTrackCoverUrl(row)"
                    :src="getTrackCoverUrl(row)"
                    :alt="row.title || ''"
                    loading="lazy"
                    class="h-full w-full object-cover"
                    @error="onCoverError"
                  />
                  <Music v-else class="h-4 w-4 text-muted-foreground/50" />
                </div>
              </template>
              <!-- 行号 -->
              <template v-else-if="col.key === 'index'">
                {{ idx + 1 }}
              </template>
              <!-- 文本类列：单行省略 + tooltip，可编辑字段支持双击行内编辑 -->
              <template v-else-if="['title','artist','album','album_artist','genre','filename','rel_path'].includes(col.key)">
                <div class="flex items-center" :class="inlineEdit.saving ? 'opacity-60' : ''">
                  <Input
                    v-if="isInlineEditing(row, col.key)"
                    ref="inlineEditInputRef"
                    v-model="inlineEdit.value"
                    type="text"
                    class="h-7 w-full max-w-[260px] bg-background select-text"
                    :class="(col.key === 'track_no' || col.key === 'year') ? 'tabular-nums' : ''"
                    :disabled="inlineEdit.saving"
                    @keydown="onInlineEditKeydown(row, $event)"
                    @blur="commitInlineEdit(row)"
                  />
                  <div
                    v-else
                    class="truncate max-w-[280px] cursor-text rounded px-0.5"
                    :class="INLINE_EDITABLE_FIELDS.has(col.key) ? 'hover:ring-1 hover:ring-primary/40 hover:bg-primary/5' : ''"
                    :title="formatCell(row, col)"
                    @dblclick="INLINE_EDITABLE_FIELDS.has(col.key) && startInlineEdit(row, col.key, $event)"
                  >{{ formatCell(row, col) }}</div>
                </div>
              </template>
              <!-- track_no / year 这类数字字段也允许双击编辑 -->
              <template v-else-if="['track_no','year'].includes(col.key)">
                <div class="flex items-center" :class="inlineEdit.saving ? 'opacity-60' : ''">
                  <Input
                    v-if="isInlineEditing(row, col.key)"
                    ref="inlineEditInputRef"
                    v-model="inlineEdit.value"
                    type="number"
                    class="h-7 w-20 tabular-nums bg-background select-text"
                    :disabled="inlineEdit.saving"
                    @keydown="onInlineEditKeydown(row, $event)"
                    @blur="commitInlineEdit(row)"
                  />
                  <div
                    v-else
                    class="cursor-text rounded px-0.5 tabular-nums hover:ring-1 hover:ring-primary/40 hover:bg-primary/5"
                    @dblclick="startInlineEdit(row, col.key, $event)"
                  >{{ formatCell(row, col) }}</div>
                </div>
              </template>
              <!-- 格式化后的字段值 -->
              <template v-else>
                {{ formatCell(row, col) }}
              </template>
            </TableCell>
            <!-- 来源节点单元格 -->
            <TableCell v-if="showSource">
              <Badge variant="outline" class="font-normal text-muted-foreground">
                {{ row.__nodeName }}
              </Badge>
            </TableCell>
          </TableRow>
          <!-- 空状态 -->
          <TableRow v-if="tableData.length === 0 && !loading" class="hover:bg-transparent">
            <TableCell :colspan="emptyColspan" class="text-center text-muted-foreground py-12">
              暂无曲目
            </TableCell>
          </TableRow>
        </TableBody>
      </Table>

      <!-- Loading 覆盖层 -->
      <div
        v-if="loading"
        class="absolute inset-0 flex items-center justify-center rounded-md bg-background/60 backdrop-blur-sm"
      >
        <Loader2 class="h-6 w-6 animate-spin text-primary" />
      </div>
    </div>

    <!-- 底部工具栏：列设置 + 分页 -->
    <div class="mt-5 flex items-center justify-between gap-3">
      <!-- 列设置 -->
      <div class="relative" @click.stop>
        <Button variant="ghost" size="sm" @click="showColumnPanel = !showColumnPanel">
          <Columns3 class="h-4 w-4" />
          列设置
        </Button>
        <!-- 列设置浮层 -->
        <div
          v-if="showColumnPanel"
          class="absolute bottom-full left-0 z-50 mb-2 w-64 rounded-md border border-border bg-popover p-1.5 shadow-lg"
        >
          <div class="max-h-[400px] overflow-auto p-1">
            <div
              v-for="group in catalogGroups"
              :key="group.category"
              class="mb-1"
            >
              <div class="px-2 py-1.5 text-xs font-semibold text-muted-foreground">
                {{ group.label }}
              </div>
              <button
                v-for="col in group.columns"
                :key="col.key"
                type="button"
                class="flex w-full items-center gap-2 rounded px-2 py-1.5 text-sm text-foreground transition-colors hover:bg-accent"
                @click="toggleColumn(col.key)"
              >
                <Check
                  v-if="visibleColumns.has(col.key)"
                  class="h-4 w-4 text-primary"
                />
                <Square
                  v-else
                  class="h-4 w-4 text-muted-foreground/40"
                />
                <span>{{ col.label }}</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- 分页 -->
      <Pagination
        v-if="showPagination"
        :page="page"
        :page-size="pageSize"
        :total="total"
        @update:page="onPageChange"
      />
    </div>

    <!-- 右键菜单 -->
    <ul
      v-if="contextMenu.visible"
      class="fixed z-[3000] m-0 min-w-[180px] list-none rounded-md border border-border bg-popover p-1.5 shadow-lg"
      :style="{ left: contextMenu.x + 'px', top: contextMenu.y + 'px' }"
      @click.stop
    >
      <li
        class="flex cursor-pointer items-center gap-2 rounded px-2.5 py-2 text-sm text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
        @click="playThis"
      >
        <Play class="h-4 w-4" />
        播放此曲
      </li>
      <li
        class="flex cursor-pointer items-center gap-2 rounded px-2.5 py-2 text-sm text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
        @click="addToQueue"
      >
        <Plus class="h-4 w-4" />
        添加到播放队列
      </li>
      <li
        class="flex cursor-pointer items-center gap-2 rounded px-2.5 py-2 text-sm text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
        @click="addToPlaylist"
      >
        <ListMusic class="h-4 w-4" />
        加入到播放列表
        <span v-if="selection.length > 1" class="ml-auto text-[10px] text-muted-foreground/60">
          {{ selection.length }} 首
        </span>
      </li>
      <li
        v-if="authStore.isAdmin"
        class="flex cursor-pointer items-center gap-2 rounded px-2.5 py-2 text-sm text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
        @click="editMetadata"
      >
        <Pencil class="h-4 w-4" />
        编辑元数据
        <span class="ml-auto text-[10px] text-muted-foreground/60">
          {{ selection.length > 1 ? `${selection.length} 首` : '单首' }}
        </span>
      </li>
    </ul>

    <!-- 加入到播放列表对话框 -->
    <AddToPlaylistDialog
      v-model:visible="addToPlaylistVisible"
      :tracks="addToPlaylistTracks"
      @added="onAddToPlaylistDone"
    />

    <!-- 元数据批量编辑抽屉 -->
    <MetadataPanel
      v-model:visible="metadataPanelVisible"
      :tracks="metadataPanelTracks"
      @updated="onMetadataUpdated"
    />
  </div>
</template>
