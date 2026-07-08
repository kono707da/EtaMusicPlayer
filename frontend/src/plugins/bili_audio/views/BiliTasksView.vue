<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { Download, Trash2, X, Loader2, RefreshCw, Music } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { useToast } from '@/components/ui/toast/use-toast'
import { listDownloads, cancelDownload, deleteDownload } from '../api'

const router = useRouter()
const toast = useToast()

const tasks = ref([])
const total = ref(0)
const page = ref(1)
const loading = ref(false)
let pollTimer = null

const statusMap = {
  pending: { label: '等待中', color: 'text-yellow-500' },
  running: { label: '下载中', color: 'text-blue-500' },
  completed: { label: '已完成', color: 'text-green-500' },
  failed: { label: '失败', color: 'text-red-500' },
  canceled: { label: '已取消', color: 'text-gray-500' },
  partial: { label: '部分完成', color: 'text-orange-500' }
}

async function load() {
  loading.value = true
  try {
    const data = await listDownloads(page.value, 20)
    tasks.value = data.items || []
    total.value = data.total || 0
  } catch (e) {
    toast.error('加载失败', e?.response?.data?.detail || e.message)
  } finally {
    loading.value = false
  }
}

async function handleCancel(taskId) {
  try {
    await cancelDownload(taskId)
    toast.success('已取消')
    load()
  } catch (e) {
    toast.error('取消失败', e?.response?.data?.detail || e.message)
  }
}

async function handleDelete(taskId) {
  try {
    await deleteDownload(taskId)
    toast.success('已删除')
    load()
  } catch (e) {
    toast.error('删除失败', e?.response?.data?.detail || e.message)
  }
}

function formatSize(bytes) {
  if (!bytes) return '-'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / 1024 / 1024).toFixed(1) + ' MB'
}

function formatTime(iso) {
  if (!iso) return '-'
  return new Date(iso).toLocaleString('zh-CN')
}

onMounted(() => {
  load()
  pollTimer = setInterval(load, 5000)
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})
</script>

<template>
  <div class="max-w-4xl mx-auto p-6 space-y-4">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold">B站下载任务</h1>
      <div class="flex gap-2">
        <Button variant="outline" size="sm" @click="load" :disabled="loading">
          <RefreshCw class="w-4 h-4 mr-1" :class="{ 'animate-spin': loading }" /> 刷新
        </Button>
        <Button size="sm" @click="router.push('/bili')">
          <Download class="w-4 h-4 mr-1" /> 新建下载
        </Button>
      </div>
    </div>

    <div v-if="loading && tasks.length === 0" class="flex items-center gap-2 text-muted-foreground py-8 justify-center">
      <Loader2 class="w-5 h-5 animate-spin" /> 加载中...
    </div>

    <div v-else-if="tasks.length === 0" class="text-center text-muted-foreground py-12">
      <Music class="w-12 h-12 mx-auto mb-3 opacity-30" />
      <p>暂无下载任务</p>
      <Button variant="outline" class="mt-4" @click="router.push('/bili')">
        <Download class="w-4 h-4 mr-1" /> 从B站下载音频
      </Button>
    </div>

    <div v-else class="space-y-3">
      <div v-for="task in tasks" :key="task.id"
        class="border rounded-lg p-4 hover:bg-accent/50 transition-colors">
        <div class="flex items-start justify-between gap-3">
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 mb-1">
              <span class="font-medium truncate">{{ task.title || task.bvid }}</span>
              <span :class="statusMap[task.status]?.color" class="text-xs font-medium">
                {{ statusMap[task.status]?.label || task.status }}
              </span>
            </div>
            <div class="text-sm text-muted-foreground space-y-0.5">
              <div v-if="task.upper_name">UP主: {{ task.upper_name }}</div>
              <div v-if="task.page_title">分P: {{ task.page_title }}</div>
              <div class="flex items-center gap-3">
                <span>{{ task.output_format?.toUpperCase() }}</span>
                <span v-if="task.file_size">{{ formatSize(task.file_size) }}</span>
                <span>{{ formatTime(task.created_at) }}</span>
              </div>
              <div v-if="task.status === 'running'" class="mt-2">
                <div class="w-full bg-secondary rounded-full h-1.5">
                  <div class="bg-primary h-1.5 rounded-full transition-all"
                    :style="{ width: task.progress + '%' }"></div>
                </div>
                <span class="text-xs">{{ task.progress.toFixed(1) }}%</span>
              </div>
              <div v-if="task.error_message" class="text-red-500 text-xs mt-1">
                {{ task.error_message }}
              </div>
            </div>
          </div>
          <div class="flex gap-1 shrink-0">
            <Button v-if="task.status === 'pending' || task.status === 'running'"
              variant="ghost" size="icon" @click="handleCancel(task.id)" title="取消">
              <X class="w-4 h-4" />
            </Button>
            <Button v-if="task.status !== 'pending' && task.status !== 'running'"
              variant="ghost" size="icon" @click="handleDelete(task.id)" title="删除">
              <Trash2 class="w-4 h-4" />
            </Button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
