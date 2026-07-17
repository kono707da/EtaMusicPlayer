<script setup>
/**
 * 删除曲目文件对话框（1.2.1）
 *
 * 流程：
 * 1. 确认状态：展示曲目信息 + 警告（永久删除文件 + 清理所有播放列表引用）
 * 2. 提交：调用 POST /api/tracks/{id}/delete 提交任务，获取 task_id
 * 3. 轮询：每 1 秒 GET /api/tasks/{task_id} 直到 status=succeeded/failed/cancelled
 * 4. 完成：展示结果（已删除文件、已清理 N 个播放列表项）
 *
 * 节点删除任务成功后由父组件（TrackTable）负责：
 * - 从播放队列移除
 * - 触发后台同步（让 sync_service 清理客户端播放列表引用）
 * - 重新加载当前视图
 */
import { ref, watch, computed, onUnmounted } from 'vue'
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { useToast } from '@/components/ui/toast/use-toast'
import { useNodesStore } from '../stores/nodes'
import { requestTrackDelete, getTask } from '../api/node'
import { removeClientPlaylistTrackReferences } from '../api/client_playlist'
import { Trash2, Loader2, AlertTriangle, CheckCircle2, XCircle } from 'lucide-vue-next'

const props = defineProps({
  visible: { type: Boolean, default: false },
  track: { type: Object, default: null }
})
const emit = defineEmits(['update:visible', 'done', 'cancel'])

const nodesStore = useNodesStore()
const toast = useToast()

// 状态机：'confirm' | 'submitting' | 'polling' | 'success' | 'error'
const phase = ref('confirm')
const taskId = ref(null)
const taskResult = ref(null)
const errorMessage = ref('')
// 客户端播放列表清理结果
const clientCleanupRemoved = ref(0)
const clientCleanupDone = ref(false)

// 轮询定时器
let pollTimer = null

// 当前曲目来源节点（用于 API 调用）
const sourceNode = computed(() => {
  if (!props.track?.__nodeId) return null
  return nodesStore.getNode(props.track.__nodeId)
})

// 客户端格式 node_id（用于清理客户端播放列表引用）
const clientNodeId = computed(() => {
  if (!props.track?.__nodeId) return null
  return `remote-${props.track.__nodeId}`
})

// 对话框打开时重置状态
watch(
  () => props.visible,
  (v) => {
    if (v) {
      phase.value = 'confirm'
      taskId.value = null
      taskResult.value = null
      errorMessage.value = ''
      clientCleanupRemoved.value = 0
      clientCleanupDone.value = false
      stopPolling()
    }
  }
)

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

onUnmounted(() => {
  stopPolling()
})

function closeDialog() {
  emit('update:visible', false)
}

function cancelDialog() {
  stopPolling()
  emit('cancel')
  emit('update:visible', false)
}

// 主流程：提交删除任务 + 轮询
async function confirmDelete() {
  const track = props.track
  const node = sourceNode.value
  if (!track || !node) {
    toast.error('删除失败', '缺少曲目或节点信息')
    return
  }

  phase.value = 'submitting'
  try {
    // 1. 提交任务
    const task = await requestTrackDelete(node, track.id)
    taskId.value = task.id
    phase.value = 'polling'
    // 2. 开始轮询
    startPolling(node)
  } catch (e) {
    const detail = e?.response?.data?.detail || e?.message || '未知错误'
    errorMessage.value = detail
    phase.value = 'error'
    toast.error('删除失败', detail, e)
  }
}

function startPolling(node) {
  stopPolling()
  pollTimer = setInterval(async () => {
    try {
      const task = await getTask(node, taskId.value)
      if (task.status === 'succeeded') {
        stopPolling()
        taskResult.value = task.result || {}
        // 节点任务成功后，立即调用访问端清理客户端引用（与 sync_service 双保险）
        await cleanupClientReferences()
        phase.value = 'success'
      } else if (task.status === 'failed' || task.status === 'cancelled') {
        stopPolling()
        errorMessage.value = task.error_message || `任务${task.status === 'failed' ? '失败' : '已取消'}`
        phase.value = 'error'
      }
      // pending / running 继续轮询
    } catch (e) {
      stopPolling()
      const detail = e?.response?.data?.detail || e?.message || '轮询失败'
      errorMessage.value = detail
      phase.value = 'error'
      // 轮询失败不弹 toast，因为对话框本身会展示错误
    }
  }, 1000)
}

// 清理客户端播放列表引用（节点删除成功后立即调用，不依赖同步）
async function cleanupClientReferences() {
  if (!clientNodeId.value || !props.track) return
  try {
    const r = await removeClientPlaylistTrackReferences(
      clientNodeId.value,
      props.track.id
    )
    clientCleanupRemoved.value = r.removed || 0
  } catch (e) {
    // 清理失败不阻塞：sync_service 增量同步时也会清理
    console.warn('[DeleteTrackDialog] 客户端引用清理失败:', e)
  }
  clientCleanupDone.value = true
}

function onDoneClick() {
  emit('done', taskResult.value)
}

// 重试：回到确认状态
function retry() {
  phase.value = 'confirm'
  taskId.value = null
  taskResult.value = null
  errorMessage.value = ''
  clientCleanupRemoved.value = 0
  clientCleanupDone.value = false
}
</script>

<template>
  <Dialog :open="visible" @update:open="(v) => emit('update:visible', v)">
    <DialogContent class="max-w-md">
      <DialogHeader>
        <DialogTitle class="flex items-center gap-2">
          <Trash2 class="h-5 w-5 text-destructive" />
          删除曲目文件
        </DialogTitle>
        <DialogDescription v-if="phase === 'confirm'">
          此操作将永久删除音频文件，不可恢复
        </DialogDescription>
        <DialogDescription v-else-if="phase === 'polling' || phase === 'submitting'">
          正在执行删除任务...
        </DialogDescription>
        <DialogDescription v-else-if="phase === 'success'">
          删除任务已完成
        </DialogDescription>
        <DialogDescription v-else>
          删除任务失败
        </DialogDescription>
      </DialogHeader>

      <!-- 确认状态 -->
      <div v-if="phase === 'confirm'" class="space-y-4">
        <!-- 曲目信息 -->
        <div class="rounded-md border border-border bg-muted/30 p-3">
          <div class="text-sm font-medium text-foreground truncate">
            {{ track?.title || '未知曲目' }}
          </div>
          <div class="mt-0.5 text-xs text-muted-foreground truncate">
            {{ track?.artist || '未知艺术家' }}
            <span v-if="track?.album"> · {{ track.album }}</span>
          </div>
          <div class="mt-1 text-xs text-muted-foreground">
            来源节点：{{ track?.__nodeName || sourceNode?.name || '未知' }}
          </div>
        </div>

        <!-- 警告 -->
        <div class="flex items-start gap-2 rounded-md border border-destructive/30 bg-destructive/5 p-3 text-sm text-destructive">
          <AlertTriangle class="mt-0.5 h-4 w-4 flex-shrink-0" />
          <div class="space-y-1">
            <div>将永久删除音频文件</div>
            <div class="text-xs text-muted-foreground">
              同时清理该曲目在所有播放列表中的引用（节点 + 客户端）
            </div>
          </div>
        </div>

        <div class="flex justify-end gap-2">
          <Button variant="ghost" @click="cancelDialog">取消</Button>
          <Button variant="destructive" @click="confirmDelete">
            <Trash2 class="h-4 w-4" />
            确认删除
          </Button>
        </div>
      </div>

      <!-- 提交中 / 轮询中 -->
      <div v-else-if="phase === 'submitting' || phase === 'polling'" class="space-y-4 py-4">
        <div class="flex flex-col items-center gap-3 text-center">
          <Loader2 class="h-8 w-8 animate-spin text-primary" />
          <div class="text-sm text-muted-foreground">
            {{ phase === 'submitting' ? '正在提交删除任务...' : '正在删除文件并清理引用...' }}
          </div>
          <div v-if="taskId" class="text-xs text-muted-foreground/60">
            任务 #{{ taskId }}
          </div>
        </div>
      </div>

      <!-- 成功 -->
      <div v-else-if="phase === 'success'" class="space-y-4">
        <div class="flex items-start gap-2 rounded-md border border-emerald-500/30 bg-emerald-500/5 p-3 text-sm text-emerald-600 dark:text-emerald-400">
          <CheckCircle2 class="mt-0.5 h-4 w-4 flex-shrink-0" />
          <div class="space-y-1">
            <div>曲目文件已删除</div>
            <ul class="text-xs text-muted-foreground space-y-0.5">
              <li v-if="taskResult?.file_deleted">
                · 音频文件已永久删除
              </li>
              <li v-if="taskResult?.file_missing">
                · 文件原本已不存在
              </li>
              <li v-if="taskResult?.removed_node_playlist_items > 0">
                · 节点侧清理了 {{ taskResult.removed_node_playlist_items }} 个播放列表引用
              </li>
              <li v-if="clientCleanupRemoved > 0">
                · 客户端侧清理了 {{ clientCleanupRemoved }} 个播放列表引用
              </li>
              <li v-if="taskResult?.warning" class="text-amber-600 dark:text-amber-400">
                · {{ taskResult.warning }}
              </li>
            </ul>
          </div>
        </div>

        <div class="flex justify-end">
          <Button variant="ghost" @click="onDoneClick">完成</Button>
        </div>
      </div>

      <!-- 失败 -->
      <div v-else class="space-y-4">
        <div class="flex items-start gap-2 rounded-md border border-destructive/30 bg-destructive/5 p-3 text-sm text-destructive">
          <XCircle class="mt-0.5 h-4 w-4 flex-shrink-0" />
          <div class="space-y-1">
            <div>删除失败</div>
            <div class="text-xs text-muted-foreground">{{ errorMessage }}</div>
          </div>
        </div>

        <div class="flex justify-end gap-2">
          <Button variant="ghost" @click="cancelDialog">关闭</Button>
          <Button variant="secondary" @click="retry">重试</Button>
        </div>
      </div>
    </DialogContent>
  </Dialog>
</template>
