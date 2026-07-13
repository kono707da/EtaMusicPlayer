<script setup>
import { ref, onMounted, onBeforeUnmount, computed } from 'vue'
import { useToast } from '@/components/ui/toast/use-toast'
import { useConfirm } from '@/composables/use-confirm'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '@/components/ui/select'
import {
  Table, TableHeader, TableBody, TableRow, TableHead, TableCell
} from '@/components/ui/table'
import { Pagination } from '@/components/ui/pagination'
import { RefreshCw, Loader2, X, Clock, Activity } from 'lucide-vue-next'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { useTargetNode } from '../composables/use-target-node'
import { listTasks, cancelTask } from '../api/node'

const { targetNode, nodeMissing, nodeMissingMessage } = useTargetNode()
const toast = useToast()
const { confirm } = useConfirm()

const tasks = ref([])
const loading = ref(false)
const page = ref(1)
const total = ref(0)
const size = ref(20)
const filterStatus = ref('')
const filterType = ref('')
let timer = null

const statusColors = {
  pending: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
  running: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  completed: 'bg-green-500/20 text-green-400 border-green-500/30',
  failed: 'bg-red-500/20 text-red-400 border-red-500/30',
  cancelled: 'bg-gray-500/20 text-gray-400 border-gray-500/30',
}

const statusLabels = {
  pending: '等待中',
  running: '执行中',
  completed: '已完成',
  failed: '失败',
  cancelled: '已取消',
}

const taskTypeLabels = {
  scan: '扫描',
  upload: '上传',
  playlist_add: '播放列表添加',
  playlist_remove: '播放列表移除',
  playlist_reorder: '播放列表排序',
  metadata_update: '元数据更新',
  metadata_rename: '文件重命名',
  watch_dir_create: '创建监控目录',
  watch_dir_update: '更新监控目录',
  watch_dir_delete: '删除监控目录',
  user_create: '创建用户',
  user_update: '更新用户',
  user_delete: '删除用户',
  permission_grant: '授权',
  permission_revoke: '撤销授权',
  dedup_update: '去重更新',
}

const totalPages = computed(() => Math.ceil(total.value / size.value) || 1)

async function loadTasks() {
  const node = targetNode.value
  if (!node || !node.token) return
  loading.value = true
  try {
    const params = { page: page.value, size: size.value }
    if (filterStatus.value) params.status = filterStatus.value
    if (filterType.value) params.task_type = filterType.value
    const data = await listTasks(node, params)
    tasks.value = data.items || []
    total.value = data.total || 0
  } catch (e) {
    toast.error('加载任务列表失败', e.message || String(e), e)
  } finally {
    loading.value = false
  }
}

async function onCancel(task) {
  const ok = await confirm(`确定取消任务 #${task.id} 吗？`, { title: '取消任务', type: 'warning' })
  if (!ok) return
  try {
    await cancelTask(targetNode.value, task.id)
    toast.success('任务已取消')
    loadTasks()
  } catch (e) {
    toast.error('取消任务失败', e.message || String(e), e)
  }
}

function formatTime(iso) {
  if (!iso) return '—'
  const d = new Date(iso)
  return d.toLocaleString('zh-CN', { hour12: false })
}

function onPageChange(p) {
  page.value = p
  loadTasks()
}

onMounted(() => {
  loadTasks()
  // 5 秒自动刷新
  timer = setInterval(loadTasks, 5000)
})
onBeforeUnmount(() => {
  if (timer) clearInterval(timer)
})
</script>

<template>
  <div class="space-y-5">
    <Alert v-if="nodeMissing" variant="destructive" class="mb-4">
      <AlertDescription>{{ nodeMissingMessage }}</AlertDescription>
    </Alert>
    <div class="flex items-center justify-between">
      <h2 class="text-xl font-bold text-foreground">任务管理</h2>
      <Button variant="outline" size="sm" :disabled="loading" @click="loadTasks">
        <RefreshCw v-if="!loading" class="mr-2 h-4 w-4" />
        <Loader2 v-else class="mr-2 h-4 w-4 animate-spin" />
        刷新
      </Button>
    </div>

    <!-- 过滤器 -->
    <div class="flex items-center gap-3">
      <Select v-model="filterStatus" @update:model-value="() => { page = 1; loadTasks() }">
        <SelectTrigger class="w-36">
          <SelectValue placeholder="全部状态" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="">全部状态</SelectItem>
          <SelectItem v-for="(label, key) in statusLabels" :key="key" :value="key">{{ label }}</SelectItem>
        </SelectContent>
      </Select>
      <Select v-model="filterType" @update:model-value="() => { page = 1; loadTasks() }">
        <SelectTrigger class="w-40">
          <SelectValue placeholder="全部类型" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="">全部类型</SelectItem>
          <SelectItem v-for="(label, key) in taskTypeLabels" :key="key" :value="key">{{ label }}</SelectItem>
        </SelectContent>
      </Select>
    </div>

    <!-- 任务表格 -->
    <div class="rounded-lg border border-border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead class="w-16">#</TableHead>
            <TableHead>类型</TableHead>
            <TableHead class="w-24">状态</TableHead>
            <TableHead class="w-28">进度</TableHead>
            <TableHead>提交者</TableHead>
            <TableHead>提交时间</TableHead>
            <TableHead>完成时间</TableHead>
            <TableHead class="w-20">操作</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          <TableRow v-for="task in tasks" :key="task.id">
            <TableCell class="font-mono text-xs">{{ task.id }}</TableCell>
            <TableCell>
              <div class="flex items-center gap-2">
                <Activity class="h-3.5 w-3.5 text-muted-foreground" />
                <span>{{ taskTypeLabels[task.task_type] || task.task_type }}</span>
              </div>
            </TableCell>
            <TableCell>
              <Badge :class="statusColors[task.status] || ''" variant="outline">
                {{ statusLabels[task.status] || task.status }}
              </Badge>
            </TableCell>
            <TableCell>
              <div v-if="task.status === 'running'" class="flex items-center gap-2">
                <div class="h-1.5 w-16 rounded-full bg-secondary overflow-hidden">
                  <div class="h-full bg-primary rounded-full transition-all" :style="{ width: `${task.progress}%` }" />
                </div>
                <span class="text-xs text-muted-foreground">{{ task.progress }}%</span>
              </div>
              <span v-else class="text-xs text-muted-foreground">—</span>
            </TableCell>
            <TableCell class="text-sm">{{ task.submitted_by || '—' }}</TableCell>
            <TableCell class="text-xs text-muted-foreground">{{ formatTime(task.submitted_at) }}</TableCell>
            <TableCell class="text-xs text-muted-foreground">{{ formatTime(task.finished_at) }}</TableCell>
            <TableCell>
              <Button v-if="task.status === 'pending'" variant="ghost" size="sm" @click="onCancel(task)">
                <X class="h-3.5 w-3.5 text-red-400" />
              </Button>
            </TableCell>
          </TableRow>
          <TableRow v-if="tasks.length === 0">
            <TableCell :colspan="8" class="py-12 text-center text-sm text-muted-foreground">
              {{ loading ? '加载中...' : '暂无任务' }}
            </TableCell>
          </TableRow>
        </TableBody>
      </Table>
    </div>

    <!-- 分页 -->
    <div v-if="total > size" class="flex justify-center">
      <Pagination :total="totalPages" :page="page" @change="onPageChange" />
    </div>
  </div>
</template>
