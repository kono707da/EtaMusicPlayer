<script setup>
import { computed, ref } from 'vue'
import { Check, Square, Loader2, Play, Plus } from 'lucide-vue-next'
import { useToast } from '@/components/ui/toast/use-toast'
import { usePlayerStore } from '../stores/player'
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
  'row-dblclick'
])

const player = usePlayerStore()
const toast = useToast()

// 多选
const selection = ref([])
const currentRow = ref(null)

function onSelectionChange(rows) {
  selection.value = rows
  emit('selection-change', rows)
}

function toggleRow(row) {
  const idx = selection.value.indexOf(row)
  if (idx > -1) selection.value.splice(idx, 1)
  else selection.value.push(row)
  emit('selection-change', selection.value)
}

function toggleAll() {
  if (allChecked.value) {
    selection.value = []
  } else {
    selection.value = [...tableData.value]
  }
  emit('selection-change', selection.value)
}

const allChecked = computed(
  () => tableData.value.length > 0 && selection.value.length === tableData.value.length
)

// 双击播放当前列表
function onRowDblclick(row) {
  emit('row-dblclick', row)
  const nodeId = row.__nodeId || props.nodeId
  const nodeName = row.__nodeName || props.nodeName
  if (nodeId == null) {
    toast.warning('缺少来源节点信息', '无法播放')
    return
  }
  player.playTracks(props.tracks, nodeId, nodeName, props.tracks.indexOf(row))
}

// 右键菜单
const contextMenu = ref({ visible: false, x: 0, y: 0, row: null })
function onRowContextmenu(row, event) {
  event.preventDefault()
  contextMenu.value = {
    visible: true,
    x: event.clientX,
    y: event.clientY,
    row
  }
}
function closeContextMenu() {
  contextMenu.value.visible = false
}

// 右键：添加到播放队列
function addToQueue() {
  const row = contextMenu.value.row
  if (!row) return
  const nodeId = row.__nodeId || props.nodeId
  const nodeName = row.__nodeName || props.nodeName
  player.appendTracks([row], nodeId, nodeName)
  toast.success('已加入播放队列')
  closeContextMenu()
}

// 右键：播放此曲
function playThis() {
  const row = contextMenu.value.row
  if (!row) return
  onRowDblclick(row)
  closeContextMenu()
}

// 分页变化
function onPageChange(p) {
  emit('page-change', p)
}

// 表格列：标题/艺术家/专辑/时长/来源
const tableData = computed(() =>
  props.tracks.map((t) => ({
    ...t,
    __nodeId: t.__nodeId || props.nodeId,
    __nodeName: t.__nodeName || props.nodeName
  }))
)

function formatDuration(sec) {
  if (!sec) return '--:--'
  const m = Math.floor(sec / 60)
  const s = Math.floor(sec % 60)
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}
</script>

<template>
  <div class="relative flex flex-1 min-h-0 flex-col" @click="closeContextMenu">
    <!-- 表格容器（含 loading 覆盖层） -->
    <div class="relative flex-1 min-h-0">
      <Table>
        <TableHeader>
          <TableRow class="hover:bg-transparent border-border">
            <TableHead class="w-11">
              <button
                class="flex h-5 w-5 items-center justify-center rounded text-muted-foreground transition-colors hover:text-primary"
                :class="allChecked ? 'text-primary' : ''"
                @click.stop="toggleAll"
              >
                <Check v-if="allChecked" class="h-4 w-4" />
                <Square v-else class="h-4 w-4" />
              </button>
            </TableHead>
            <TableHead class="w-12 text-xs font-medium uppercase tracking-wider text-muted-foreground">#</TableHead>
            <TableHead class="text-xs font-medium uppercase tracking-wider text-muted-foreground">标题</TableHead>
            <TableHead class="text-xs font-medium uppercase tracking-wider text-muted-foreground">艺术家</TableHead>
            <TableHead class="text-xs font-medium uppercase tracking-wider text-muted-foreground">专辑</TableHead>
            <TableHead class="w-20 text-xs font-medium uppercase tracking-wider text-muted-foreground">时长</TableHead>
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
            :class="currentRow === row ? 'bg-primary/10' : ''"
            @click="currentRow = row"
            @dblclick="onRowDblclick(row)"
            @contextmenu="onRowContextmenu(row, $event)"
          >
            <TableCell>
              <button
                class="flex h-5 w-5 items-center justify-center rounded transition-colors"
                :class="selection.includes(row) ? 'text-primary' : 'text-muted-foreground hover:text-foreground'"
                @click.stop="toggleRow(row)"
              >
                <Check v-if="selection.includes(row)" class="h-4 w-4" />
                <Square v-else class="h-4 w-4" />
              </button>
            </TableCell>
            <TableCell class="text-muted-foreground">{{ idx + 1 }}</TableCell>
            <TableCell class="font-medium text-foreground">{{ row.title }}</TableCell>
            <TableCell class="text-muted-foreground">{{ row.artist }}</TableCell>
            <TableCell class="text-muted-foreground">{{ row.album }}</TableCell>
            <TableCell class="text-muted-foreground tabular-nums">{{ formatDuration(row.duration) }}</TableCell>
            <TableCell v-if="showSource">
              <Badge variant="outline" class="font-normal text-muted-foreground">
                {{ row.__nodeName }}
              </Badge>
            </TableCell>
          </TableRow>
          <!-- 空状态 -->
          <TableRow v-if="tableData.length === 0 && !loading" class="hover:bg-transparent">
            <TableCell :colspan="showSource ? 7 : 6" class="text-center text-muted-foreground py-12">
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

    <!-- 分页 -->
    <div v-if="showPagination" class="mt-5 flex justify-center">
      <Pagination
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
    </ul>
  </div>
</template>
