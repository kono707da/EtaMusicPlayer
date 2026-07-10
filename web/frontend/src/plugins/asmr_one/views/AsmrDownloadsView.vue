<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  ArrowLeft,
  RefreshCw,
  Loader2,
  CheckCircle2,
  AlertCircle,
  Clock,
  XCircle,
  Trash2,
  Ban,
  Download,
  Image as ImageIcon
} from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Empty } from '@/components/ui/empty'
import { useToast } from '@/components/ui/toast/use-toast'
import CoverPickerDialog from '@/components/CoverPickerDialog.vue'
import { listDownloads, getDownload, cancelDownload, deleteDownload } from '../api'

const router = useRouter()
const toast = useToast()

const tasks = ref([])
const loading = ref(false)
const expandedTaskId = ref(null)
const expandedTask = ref(null)
const expandedLoading = ref(false)
let pollTimer = null

// 封面选择器
const coverPickerOpen = ref(false)
const coverPickerTaskId = ref(null)
const coverPickerWorkId = ref(null)

const hasRunning = computed(() =>
  tasks.value.some((t) => t.status === 'running' || t.status === 'pending')
)

async function load() {
  loading.value = true
  try {
    const data = await listDownloads()
    tasks.value = data.tasks
  } catch (e) {
    toast.error('加载失败', e?.response?.data?.detail || e.message, e)
  } finally {
    loading.value = false
  }
}

async function pollRunning() {
  if (!hasRunning.value) return
  await load()
}

async function toggleExpand(task) {
  if (expandedTaskId.value === task.id) {
    expandedTaskId.value = null
    expandedTask.value = null
    return
  }
  expandedTaskId.value = task.id
  expandedLoading.value = true
  try {
    expandedTask.value = await getDownload(task.id)
  } finally {
    expandedLoading.value = false
  }
}

async function onCancel(task) {
  try {
    await cancelDownload(task.id)
    toast.success('已请求取消')
    await load()
  } catch (e) {
    toast.error('取消失败', e?.response?.data?.detail || e.message, e)
  }
}

async function onDelete(task) {
  try {
    await deleteDownload(task.id)
    toast.success('已删除')
    await load()
  } catch (e) {
    toast.error('删除失败', e?.response?.data?.detail || e.message, e)
  }
}

function onChangeCover(task) {
  coverPickerTaskId.value = task.id
  coverPickerWorkId.value = task.work_id
  coverPickerOpen.value = true
}

async function onCoverApplied() {
  await load()
}

function statusMeta(status) {
  switch (status) {
    case 'pending':
      return { icon: Clock, color: 'text-muted-foreground', label: '等待中' }
    case 'running':
      return { icon: Loader2, color: 'text-blue-400', label: '下载中', spin: true }
    case 'completed':
      return { icon: CheckCircle2, color: 'text-emerald-400', label: '已完成' }
    case 'partial':
      return { icon: AlertCircle, color: 'text-amber-400', label: '部分完成' }
    case 'failed':
      return { icon: XCircle, color: 'text-destructive', label: '失败' }
    case 'canceled':
      return { icon: Ban, color: 'text-muted-foreground', label: '已取消' }
    default:
      return { icon: Clock, color: 'text-muted-foreground', label: status }
  }
}

function progressPercent(task) {
  const total = task.total_files || 0
  if (total === 0) return 0
  const done = (task.completed_files || 0) + (task.skipped_files || 0)
  return Math.round((done / total) * 100)
}

function formatTime(s) {
  if (!s) return '--'
  try {
    return new Date(s).toLocaleString('zh-CN', { hour12: false })
  } catch {
    return s
  }
}

onMounted(() => {
  load()
  pollTimer = setInterval(pollRunning, 3000)
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})
</script>

<template>
  <div class="flex h-full flex-col gap-4">
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-3">
        <Button variant="ghost" size="sm" @click="router.push('/asmr')">
          <ArrowLeft class="h-4 w-4" />
          返回搜索
        </Button>
        <h2 class="text-lg font-semibold">下载任务</h2>
      </div>
      <Button variant="ghost" size="sm" :disabled="loading" @click="load">
        <RefreshCw class="h-4 w-4" :class="{ 'animate-spin': loading }" />
        刷新
      </Button>
    </div>

    <div class="flex-1 min-h-0 overflow-auto">
      <Empty
        v-if="tasks.length === 0"
        :icon="Download"
        title="还没有下载任务"
        description="去搜索作品并创建下载任务"
        class="h-full"
      >
        <Button variant="gold" @click="router.push('/asmr')">去搜索</Button>
      </Empty>

      <div v-else class="flex flex-col gap-2 pb-4">
        <div
          v-for="t in tasks"
          :key="t.id"
          class="rounded-lg border border-border bg-card/40 overflow-hidden"
        >
          <!-- 任务头部 -->
          <div
            class="flex items-center gap-3 px-4 py-3 cursor-pointer hover:bg-accent/30"
            @click="toggleExpand(t)"
          >
            <component
              :is="statusMeta(t.status).icon"
              class="h-4 w-4 shrink-0"
              :class="[statusMeta(t.status).color, { 'animate-spin': statusMeta(t.status).spin }]"
            />
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2">
                <span class="text-sm font-medium text-foreground truncate">#{{ t.id }} {{ t.work_title }}</span>
                <Badge variant="outline" class="text-xs shrink-0">{{ statusMeta(t.status).label }}</Badge>
              </div>
              <div class="text-xs text-muted-foreground mt-0.5">
                {{ t.completed_files }} 完成 / {{ t.skipped_files }} 跳过 / {{ t.failed_files }} 失败
                · 共 {{ t.total_files }} 个文件
                <span class="ml-2">·</span>
                {{ formatTime(t.created_at) }}
              </div>
            </div>

            <!-- 操作按钮 -->
            <div class="flex items-center gap-1 shrink-0" @click.stop>
              <Button
                v-if="t.status === 'running' || t.status === 'pending'"
                variant="ghost"
                size="sm"
                @click="onCancel(t)"
              >
                <Ban class="h-3.5 w-3.5" />
                取消
              </Button>
              <Button
                v-if="['completed', 'partial'].includes(t.status)"
                variant="ghost"
                size="sm"
                @click="onChangeCover(t)"
              >
                <ImageIcon class="h-3.5 w-3.5" />
                {{ t.cover_applied ? '换封面' : '设封面' }}
              </Button>
              <Button
                v-if="!['running', 'pending'].includes(t.status)"
                variant="ghost"
                size="sm"
                @click="onDelete(t)"
              >
                <Trash2 class="h-3.5 w-3.5" />
                删除
              </Button>
            </div>
          </div>

          <!-- 进度条 -->
          <div v-if="t.status === 'running' || t.status === 'pending'" class="h-1 bg-secondary">
            <div
              class="h-full bg-primary transition-all"
              :style="{ width: progressPercent(t) + '%' }"
            />
          </div>

          <!-- 展开详情 -->
          <div v-if="expandedTaskId === t.id" class="border-t border-border p-4 bg-secondary/20">
            <div v-if="expandedLoading" class="flex justify-center py-4">
              <Loader2 class="h-4 w-4 animate-spin text-muted-foreground" />
            </div>
            <template v-else-if="expandedTask">
              <!-- 当前文件 -->
              <div v-if="expandedTask.current_file" class="mb-3 text-sm">
                <div class="text-xs text-muted-foreground mb-1">当前文件</div>
                <div class="text-foreground truncate">{{ expandedTask.current_file }}</div>
                <div class="text-xs text-muted-foreground mt-0.5">
                  {{ expandedTask.current_file_done }} / {{ expandedTask.current_file_size }} bytes
                </div>
              </div>

              <!-- 错误 -->
              <div v-if="expandedTask.error_message" class="mb-3 rounded-md bg-destructive/10 border border-destructive/30 p-2.5">
                <div class="text-xs text-destructive font-medium mb-1">错误信息</div>
                <pre class="text-xs text-destructive/90 whitespace-pre-wrap font-mono">{{ expandedTask.error_message }}</pre>
              </div>

              <!-- 文件列表 -->
              <div v-if="expandedTask.files?.length" class="text-sm">
                <div class="text-xs text-muted-foreground mb-2">文件详情</div>
                <div class="max-h-60 overflow-auto rounded-md border border-border">
                  <table class="w-full text-xs">
                    <thead class="bg-secondary/50 sticky top-0">
                      <tr>
                        <th class="text-left p-2 font-medium">路径</th>
                        <th class="text-left p-2 font-medium w-20">状态</th>
                        <th class="text-right p-2 font-medium w-28">大小</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr
                        v-for="f in expandedTask.files"
                        :key="f.path"
                        class="border-t border-border"
                      >
                        <td class="p-2 break-all">{{ f.path }}</td>
                        <td class="p-2">
                          <Badge
                            :variant="f.status === 'completed' ? 'default' : f.status === 'failed' ? 'destructive' : 'outline'"
                            class="text-[10px]"
                          >
                            {{ f.status }}
                          </Badge>
                        </td>
                        <td class="p-2 text-right tabular-nums">
                          {{ f.done }}/{{ f.size }}
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            </template>
          </div>
        </div>
      </div>
    </div>

    <!-- 封面选择器 -->
    <CoverPickerDialog
      v-model:open="coverPickerOpen"
      :task-id="coverPickerTaskId"
      :work-id="coverPickerWorkId"
      @applied="onCoverApplied"
    />
  </div>
</template>
