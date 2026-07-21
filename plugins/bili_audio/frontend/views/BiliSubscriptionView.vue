<script setup>
const { ref, reactive, onMounted } = window.__etamusic.vue
const {
  Button, Input, Label,
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
  useToast
} = window.__etamusic.ui
const { BookmarkIcon, Loader2, RefreshCw, Trash2, CheckCircle, XCircle } = window.__etamusic.icons
import { createSubscription, listSubscriptions, checkSubscription, deleteSubscription, updateSubscription } from '../api'

const toast = useToast()

const subscriptions = ref([])
const loading = ref(false)
const adding = ref(false)
const newUrl = ref('')
const newQuality = ref('30280')
const newFormat = ref('mp3')
const checkingMap = reactive({})
const checkResults = reactive({})

const qualityOptions = [
  { value: '30216', label: '64kbps' },
  { value: '30232', label: '132kbps' },
  { value: '30280', label: '192kbps（推荐）' },
  { value: '30251', label: 'Hi-Res 无损' }
]

const formatOptions = [
  { value: 'mp3', label: 'MP3' },
  { value: 'm4a', label: 'M4A (AAC)' }
]

const qualityMap = { 30216: '64kbps', 30232: '132kbps', 30280: '192kbps', 30250: 'Dolby', 30251: 'Hi-Res' }
const qualityLabel = (q) => qualityMap[q] || `${q}kbps`

const statusMap = {
  active: { label: '正常', color: 'text-green-500' },
  error: { label: '错误', color: 'text-red-500' },
  paused: { label: '已暂停', color: 'text-muted-foreground' }
}

function formatTime(iso) {
  if (!iso) return '-'
  try {
    return new Date(iso).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
  } catch {
    return iso
  }
}

async function fetchList() {
  loading.value = true
  try {
    const data = await listSubscriptions()
    subscriptions.value = data.items || []
  } catch (e) {
    toast.error('获取订阅列表失败', e?.response?.data?.detail || e.message, e)
  } finally {
    loading.value = false
  }
}

async function handleAdd() {
  if (!newUrl.value.trim() || adding.value) return
  adding.value = true
  try {
    await createSubscription({
      url: newUrl.value.trim(),
      auto_download: true,
      audio_quality: parseInt(newQuality.value),
      output_format: newFormat.value,
    })
    newUrl.value = ''
    toast.success('订阅添加成功')
    await fetchList()
  } catch (e) {
    toast.error('添加订阅失败', e?.response?.data?.detail || e.message, e)
  } finally {
    adding.value = false
  }
}

async function handleCheck(subId) {
  checkingMap[subId] = true
  checkResults[subId] = ''
  try {
    const result = await checkSubscription(subId)
    if (result.error) {
      checkResults[subId] = `检查失败: ${result.error}`
      toast.error('检查更新失败', result.error)
    } else {
      checkResults[subId] = `发现 ${result.total_archives || 0} 个视频，新增下载 ${result.new_downloads || 0} 个`
      toast.success('检查完成', `新增下载 ${result.new_downloads || 0} 个`)
    }
    await fetchList()
  } catch (e) {
    const msg = e?.response?.data?.detail || e.message
    checkResults[subId] = `检查失败: ${msg}`
    toast.error('检查更新失败', msg, e)
  } finally {
    checkingMap[subId] = false
  }
}

async function handleToggleAutoDownload(sub) {
  try {
    await updateSubscription(sub.id, { auto_download: !sub.auto_download })
    sub.auto_download = !sub.auto_download
    toast.success(sub.auto_download ? '已开启自动下载' : '已关闭自动下载')
  } catch (e) {
    toast.error('更新订阅失败', e?.response?.data?.detail || e.message, e)
  }
}

async function handleDelete(subId) {
  try {
    await deleteSubscription(subId)
    toast.success('订阅已删除')
    await fetchList()
  } catch (e) {
    toast.error('删除订阅失败', e?.response?.data?.detail || e.message, e)
  }
}

onMounted(fetchList)
</script>

<template>
  <div class="max-w-4xl mx-auto p-6 space-y-6">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold">订阅管理</h1>
      <Button variant="outline" size="sm" @click="fetchList" :disabled="loading">
        <RefreshCw class="w-4 h-4 mr-1" :class="{ 'animate-spin': loading }" /> 刷新
      </Button>
    </div>

    <div class="border rounded-lg p-4 space-y-3">
      <Label class="text-sm font-medium">添加订阅</Label>
      <div class="flex gap-2">
        <Input
          v-model="newUrl"
          placeholder="输入B站合集链接，如 https://space.bilibili.com/27492426/lists/506549"
          class="flex-1"
          @keyup.enter="handleAdd"
        />
        <Select v-model="newQuality">
          <SelectTrigger class="w-[160px]">
            <SelectValue placeholder="音质" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem v-for="q in qualityOptions" :key="q.value" :value="q.value">
              {{ q.label }}
            </SelectItem>
          </SelectContent>
        </Select>
        <Select v-model="newFormat">
          <SelectTrigger class="w-[120px]">
            <SelectValue placeholder="格式" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem v-for="f in formatOptions" :key="f.value" :value="f.value">
              {{ f.label }}
            </SelectItem>
          </SelectContent>
        </Select>
        <Button @click="handleAdd" :disabled="!newUrl.trim() || adding">
          <Loader2 v-if="adding" class="w-4 h-4 mr-2 animate-spin" />
          <BookmarkIcon v-else class="w-4 h-4 mr-2" />
          {{ adding ? '添加中...' : '添加' }}
        </Button>
      </div>
    </div>

    <div v-if="loading && subscriptions.length === 0" class="flex items-center gap-2 text-muted-foreground py-8 justify-center">
      <Loader2 class="w-5 h-5 animate-spin" /> 加载中...
    </div>

    <div v-else-if="subscriptions.length === 0" class="text-center text-muted-foreground py-12 border rounded-lg border-dashed">
      <BookmarkIcon class="w-12 h-12 mx-auto mb-3 opacity-30" />
      <p>暂无订阅，请添加B站合集链接</p>
    </div>

    <div v-else class="space-y-3">
      <div
        v-for="sub in subscriptions"
        :key="sub.id"
        class="border rounded-lg p-4 hover:bg-accent/50 transition-colors space-y-2"
      >
        <div class="flex items-start justify-between gap-3">
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 mb-1">
              <span class="font-medium truncate">{{ sub.title || '未命名合集' }}</span>
              <span :class="statusMap[sub.status]?.color" class="text-xs font-medium">
                {{ statusMap[sub.status]?.label || sub.status }}
              </span>
            </div>
            <p class="text-sm text-muted-foreground">{{ sub.upper_name || '未知UP主' }}</p>
          </div>
          <div class="flex items-center gap-1 shrink-0">
            <Button
              variant="outline"
              size="sm"
              @click="handleCheck(sub.id)"
              :disabled="checkingMap[sub.id]"
            >
              <Loader2 v-if="checkingMap[sub.id]" class="w-3 h-3 mr-1 animate-spin" />
              <RefreshCw v-else class="w-3 h-3 mr-1" />
              {{ checkingMap[sub.id] ? '检查中...' : '检查更新' }}
            </Button>
            <Button
              :variant="sub.auto_download ? 'default' : 'outline'"
              size="sm"
              @click="handleToggleAutoDownload(sub)"
            >
              {{ sub.auto_download ? '自动下载' : '手动' }}
            </Button>
            <Button
              variant="ghost"
              size="icon"
              @click="handleDelete(sub.id)"
              title="删除"
            >
              <Trash2 class="w-4 h-4 text-red-500" />
            </Button>
          </div>
        </div>
        <div class="flex items-center gap-4 text-xs text-muted-foreground">
          <span>视频: {{ sub.downloaded_count ?? 0 }}/{{ sub.video_count ?? 0 }}</span>
          <span>音质: {{ qualityLabel(sub.audio_quality) }}</span>
          <span>格式: {{ (sub.output_format || 'mp3').toUpperCase() }}</span>
          <span v-if="sub.last_checked_at">上次检查: {{ formatTime(sub.last_checked_at) }}</span>
        </div>
        <div v-if="checkResults[sub.id]" class="text-xs text-muted-foreground bg-muted/50 rounded px-2 py-1">
          {{ checkResults[sub.id] }}
        </div>
      </div>
    </div>
  </div>
</template>
