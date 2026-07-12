<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { useToast } from '@/components/ui/toast/use-toast'
import { useConfirm } from '@/composables/use-confirm'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Switch } from '@/components/ui/switch'
import { Badge } from '@/components/ui/badge'
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell
} from '@/components/ui/table'
import { RefreshCw, Loader2, Plus, Trash2, Play, FolderOpen } from 'lucide-vue-next'
import { useAuthStore } from '../stores/auth'
import {
  triggerScan,
  getScanStatus,
  getWatchDirs,
  addWatchDir,
  deleteWatchDir
} from '../api/node'
import PathPickerDialog from '@/components/PathPickerDialog.vue'

const authStore = useAuthStore()
const toast = useToast()
const { confirm } = useConfirm()

// 最近一次扫描任务状态
const lastTask = ref(null)
const dirs = ref([])
const loading = ref(false)
const triggering = ref(false)
const newDir = ref({ path: '', recursive: true, enabled: true })
let timer = null
const pathPickerOpen = ref(false)

function onOpenPathPicker() {
  pathPickerOpen.value = true
}
function onPathPicked(p) {
  newDir.value.path = p
}

// 拉取最近一次任务状态（如有 task_id 缓存）
async function refreshTask() {
  const node = authStore.localNode
  if (!node || !lastTask.value?.id) return
  try {
    lastTask.value = await getScanStatus(node, lastTask.value.id)
  } catch (e) {
    /* 静默 */
  }
}

async function refreshDirs() {
  const node = authStore.localNode
  if (!node) return
  loading.value = true
  try {
    const data = await getWatchDirs(node)
    dirs.value = Array.isArray(data) ? data : data.items || []
  } catch (e) {
    dirs.value = []
  } finally {
    loading.value = false
  }
}

async function onTrigger(watchDirId) {
  const node = authStore.localNode
  triggering.value = true
  try {
    // 后端同步执行扫描，请求返回时扫描已完成
    const task = await triggerScan(node, watchDirId ? { watch_dir_id: watchDirId } : {})
    lastTask.value = task
    toast.success(
      `扫描完成`,
      `新增 ${task.new_tracks ?? 0}，更新 ${task.updated_tracks ?? 0}`
    )
    await refreshDirs()
  } catch (e) {
    toast.error('触发失败', e.response?.data?.detail || e.message, e)
  } finally {
    triggering.value = false
  }
}

async function onAddDir() {
  if (!newDir.value.path) {
    toast.warning('请输入目录路径')
    return
  }
  const node = authStore.localNode
  try {
    await addWatchDir(node, {
      path: newDir.value.path,
      recursive: newDir.value.recursive,
      enabled: newDir.value.enabled
    })
    toast.success('已添加')
    newDir.value.path = ''
    refreshDirs()
  } catch (e) {
    toast.error('添加失败', e.response?.data?.detail || e.message, e)
  }
}

async function onRemoveDir(row) {
  const ok = await confirm(
    `移除监控目录「${row.path}」？该目录下的曲目记录将被删除。`,
    { title: '移除目录', type: 'danger' }
  )
  if (!ok) return
  const node = authStore.localNode
  try {
    await deleteWatchDir(node, row.id)
    toast.success('已移除')
    refreshDirs()
  } catch (e) {
    toast.error('移除失败', e.message || String(e), e)
  }
}

onMounted(() => {
  refreshDirs()
  // 定期刷新任务状态（仅当有进行中的任务时）
  timer = setInterval(refreshTask, 5000)
})

onBeforeUnmount(() => {
  if (timer) clearInterval(timer)
})

function taskTagVariant(status) {
  if (status === 'completed') return 'success'
  if (status === 'running') return 'default'
  if (status === 'failed') return 'destructive'
  return 'secondary'
}
</script>

<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <h2 class="text-2xl font-bold tracking-tight">扫描管理</h2>
      <div class="flex gap-2">
        <Button variant="secondary" @click="refreshDirs">
          <RefreshCw class="h-4 w-4" />
          刷新目录
        </Button>
        <Button :disabled="triggering" @click="onTrigger(null)">
          <Loader2 v-if="triggering" class="h-4 w-4 animate-spin" />
          <Play v-else class="h-4 w-4" />
          扫描全部目录
        </Button>
      </div>
    </div>

    <!-- 最近一次扫描任务 -->
    <Card v-if="lastTask">
      <CardHeader>
        <CardTitle>最近一次扫描任务</CardTitle>
      </CardHeader>
      <CardContent>
        <div class="grid grid-cols-2 gap-x-8 gap-y-3 text-sm">
          <div class="flex items-center justify-between border-b border-border pb-2">
            <span class="text-muted-foreground">任务ID</span>
            <span class="font-medium text-foreground">{{ lastTask.id }}</span>
          </div>
          <div class="flex items-center justify-between border-b border-border pb-2">
            <span class="text-muted-foreground">状态</span>
            <Badge :variant="taskTagVariant(lastTask.status)">{{ lastTask.status }}</Badge>
          </div>
          <div class="flex items-center justify-between border-b border-border pb-2">
            <span class="text-muted-foreground">开始时间</span>
            <span class="font-medium text-foreground">{{ lastTask.started_at || '—' }}</span>
          </div>
          <div class="flex items-center justify-between border-b border-border pb-2">
            <span class="text-muted-foreground">结束时间</span>
            <span class="font-medium text-foreground">{{ lastTask.finished_at || '—' }}</span>
          </div>
          <div class="flex items-center justify-between border-b border-border pb-2">
            <span class="text-muted-foreground">总文件数</span>
            <span class="font-medium text-foreground">{{ lastTask.total_files ?? 0 }}</span>
          </div>
          <div class="flex items-center justify-between border-b border-border pb-2">
            <span class="text-muted-foreground">已处理</span>
            <span class="font-medium text-foreground">{{ lastTask.processed_files ?? 0 }}</span>
          </div>
          <div class="flex items-center justify-between border-b border-border pb-2">
            <span class="text-muted-foreground">新增曲目</span>
            <span class="font-medium text-foreground">{{ lastTask.new_tracks ?? 0 }}</span>
          </div>
          <div class="flex items-center justify-between border-b border-border pb-2">
            <span class="text-muted-foreground">更新曲目</span>
            <span class="font-medium text-foreground">{{ lastTask.updated_tracks ?? 0 }}</span>
          </div>
          <div class="col-span-2 flex items-start justify-between border-b border-border pb-2 gap-4">
            <span class="text-muted-foreground shrink-0">错误信息</span>
            <span class="font-medium text-foreground text-right break-all">{{ lastTask.error_message || '—' }}</span>
          </div>
        </div>
      </CardContent>
    </Card>

    <!-- 监控目录 -->
    <Card>
      <CardHeader>
        <CardTitle>监控目录</CardTitle>
      </CardHeader>
      <CardContent class="space-y-4">
        <div class="flex flex-wrap items-end gap-4">
          <div class="flex flex-col gap-1.5">
        <Label>路径</Label>
        <div class="flex gap-2">
          <Input
            v-model="newDir.path"
            placeholder="如：D:/Music"
            class="w-80"
            @keyup.enter="onAddDir"
          />
          <Button variant="outline" @click="onOpenPathPicker" title="浏览选择目录">
            <FolderOpen class="h-4 w-4" />
            浏览
          </Button>
        </div>
      </div>
      <div class="flex flex-col gap-1.5">
        <Label>递归</Label>
        <Switch v-model:checked="newDir.recursive" />
      </div>
      <div class="flex flex-col gap-1.5">
        <Label>启用</Label>
        <Switch v-model:checked="newDir.enabled" />
      </div>
      <Button @click="onAddDir">
        <Plus class="h-4 w-4" />
        添加
      </Button>
    </div>

        <div class="relative rounded-md border border-border">
          <Table>
            <TableHeader>
              <TableRow class="hover:bg-transparent">
                <TableHead class="min-w-[280px]">目录</TableHead>
                <TableHead class="w-20">递归</TableHead>
                <TableHead class="w-20">启用</TableHead>
                <TableHead class="min-w-[160px]">上次扫描</TableHead>
                <TableHead class="w-44 text-right">操作</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              <TableRow v-for="row in dirs" :key="row.id">
                <TableCell class="font-medium text-foreground truncate max-w-[280px]">
                  {{ row.path }}
                </TableCell>
                <TableCell>
                  <Badge :variant="row.recursive ? 'success' : 'secondary'">
                    {{ row.recursive ? '是' : '否' }}
                  </Badge>
                </TableCell>
                <TableCell>
                  <Badge :variant="row.enabled ? 'success' : 'destructive'">
                    {{ row.enabled ? '是' : '否' }}
                  </Badge>
                </TableCell>
                <TableCell class="text-muted-foreground">
                  {{ row.last_scanned_at || '—' }}
                </TableCell>
                <TableCell>
                  <div class="flex justify-end gap-1">
                    <Button variant="ghost" size="sm" @click="onTrigger(row.id)">
                      <Play class="h-3.5 w-3.5" />
                      扫描
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      class="text-destructive hover:text-destructive"
                      @click="onRemoveDir(row)"
                    >
                      <Trash2 class="h-3.5 w-3.5" />
                      移除
                    </Button>
                  </div>
                </TableCell>
              </TableRow>
              <TableRow v-if="dirs.length === 0 && !loading" class="hover:bg-transparent">
                <TableCell colspan="5" class="text-center text-muted-foreground py-10">
                  暂无监控目录
                </TableCell>
              </TableRow>
            </TableBody>
          </Table>
          <div
            v-if="loading"
            class="absolute inset-0 flex items-center justify-center rounded-md bg-background/60 backdrop-blur-sm"
          >
            <Loader2 class="h-5 w-5 animate-spin text-primary" />
          </div>
        </div>
      </CardContent>
    </Card>

    <!-- 路径选择对话框 -->
    <PathPickerDialog
      v-model:open="pathPickerOpen"
      :node="authStore.localNode"
      title="选择监控目录"
      @select="onPathPicked"
    />
  </div>
</template>
