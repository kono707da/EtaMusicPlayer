<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { Download, Loader2, Link, Music, Settings, List } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { useToast } from '@/components/ui/toast/use-toast'
import { parseVideo, createDownload, getTargetNodes } from '../api'

const router = useRouter()
const toast = useToast()

const url = ref('')
const parsing = ref(false)
const downloading = ref(false)
const videoInfo = ref(null)
const parseError = ref('')
const watchDirs = ref([])
const selectedPage = ref(0)
const audioQuality = ref('30280')
const outputFormat = ref('mp3')
const targetWatchDirId = ref('')
const targetSubdir = ref('B站音频')

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

async function handleParse() {
  if (!url.value.trim()) {
    toast.error('请输入B站视频链接')
    return
  }
  parsing.value = true
  parseError.value = ''
  videoInfo.value = null
  try {
    const data = await parseVideo(url.value.trim())
    videoInfo.value = data
    if (data.pages && data.pages.length > 1) {
      selectedPage.value = 0
    }
  } catch (e) {
    parseError.value = e?.response?.data?.detail || e.message || '解析失败'
  } finally {
    parsing.value = false
  }
}

async function handleDownload() {
  if (!videoInfo.value) return
  downloading.value = true
  try {
    const data = {
      url: url.value.trim(),
      page_index: selectedPage.value,
      audio_quality: parseInt(audioQuality.value),
      output_format: outputFormat.value,
      target_watch_dir_id: targetWatchDirId.value ? parseInt(targetWatchDirId.value) : null,
      target_subdir: targetSubdir.value || 'B站音频'
    }
    const result = await createDownload(data)
    toast.success('下载任务已创建')
    router.push('/bili/tasks')
  } catch (e) {
    toast.error('创建下载失败', e?.response?.data?.detail || e.message, e)
  } finally {
    downloading.value = false
  }
}

async function loadWatchDirs() {
  try {
    const data = await getTargetNodes()
    watchDirs.value = data || []
    if (watchDirs.value.length > 0 && !targetWatchDirId.value) {
      targetWatchDirId.value = String(watchDirs.value[0].id)
    }
  } catch (e) {
    // ignore
  }
}

loadWatchDirs()
</script>

<template>
  <div class="max-w-3xl mx-auto p-6 space-y-6">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold">B站音频下载</h1>
      <div class="flex gap-2">
        <Button variant="outline" size="sm" @click="router.push('/bili/tasks')">
          <List class="w-4 h-4 mr-1" /> 下载任务
        </Button>
        <Button variant="outline" size="sm" @click="router.push('/bili/settings')">
          <Settings class="w-4 h-4 mr-1" /> 设置
        </Button>
      </div>
    </div>

    <div class="space-y-4">
      <div class="space-y-2">
        <Label class="text-base font-medium">视频链接</Label>
        <div class="flex gap-2">
          <Input v-model="url" placeholder="粘贴B站视频链接（BV号或完整URL）"
            @keyup.enter="handleParse" class="flex-1" />
          <Button @click="handleParse" :disabled="parsing || !url.trim()">
            <Loader2 v-if="parsing" class="w-4 h-4 mr-2 animate-spin" />
            <Link v-else class="w-4 h-4 mr-2" />
            解析
          </Button>
        </div>
        <p v-if="parseError" class="text-red-500 text-sm">{{ parseError }}</p>
      </div>

      <div v-if="videoInfo" class="border rounded-lg p-4 space-y-4">
        <div class="flex gap-4">
          <img v-if="videoInfo.cover_url" :src="videoInfo.cover_url"
            class="w-40 h-24 object-cover rounded border bg-muted"
            @error="($event.target).style.display = 'none'" />
          <div class="flex-1 min-w-0">
            <h2 class="text-lg font-semibold truncate">{{ videoInfo.title }}</h2>
            <p v-if="videoInfo.upper_name" class="text-sm text-muted-foreground mt-1">
              UP主: {{ videoInfo.upper_name }}
            </p>
            <p v-if="videoInfo.duration" class="text-sm text-muted-foreground">
              时长: {{ Math.floor(videoInfo.duration / 60) }}:{{ String(videoInfo.duration % 60).padStart(2, '0') }}
            </p>
            <a v-if="videoInfo.source_url" :href="videoInfo.source_url" target="_blank"
              class="text-xs text-blue-500 hover:underline">
              {{ videoInfo.source_url }}
            </a>
          </div>
        </div>

        <div v-if="videoInfo.pages && videoInfo.pages.length > 1" class="space-y-2">
          <Label>选择分P</Label>
          <Select v-model="selectedPage">
            <SelectTrigger>
              <SelectValue placeholder="选择分P" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem v-for="(p, i) in videoInfo.pages" :key="i"
                :value="String(i)">
                P{{ p.page }}: {{ p.part }} ({{ Math.floor(p.duration / 60) }}:{{ String(p.duration % 60).padStart(2, '0') }})
              </SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div class="grid grid-cols-2 gap-4">
          <div class="space-y-2">
            <Label>音质</Label>
            <Select v-model="audioQuality">
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem v-for="q in qualityOptions" :key="q.value" :value="q.value">
                  {{ q.label }}
                </SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div class="space-y-2">
            <Label>输出格式</Label>
            <Select v-model="outputFormat">
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem v-for="f in formatOptions" :key="f.value" :value="f.value">
                  {{ f.label }}
                </SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        <div class="grid grid-cols-2 gap-4">
          <div class="space-y-2">
            <Label>保存目录</Label>
            <Select v-model="targetWatchDirId">
              <SelectTrigger>
                <SelectValue placeholder="选择监控目录" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem v-for="d in watchDirs" :key="d.id" :value="String(d.id)">
                  {{ d.path }}
                </SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div class="space-y-2">
            <Label>子目录</Label>
            <Input v-model="targetSubdir" placeholder="B站音频" />
          </div>
        </div>

        <Button @click="handleDownload" :disabled="downloading" class="w-full" size="lg">
          <Download v-if="!downloading" class="w-5 h-5 mr-2" />
          <Loader2 v-else class="w-5 h-5 mr-2 animate-spin" />
          下载音频
        </Button>
      </div>

      <div v-else class="text-center text-muted-foreground py-12 border rounded-lg border-dashed">
        <Music class="w-16 h-16 mx-auto mb-4 opacity-20" />
        <p class="text-lg">粘贴B站视频链接，提取音频并入库</p>
        <p class="text-sm mt-2">支持 BV号、av号、完整链接</p>
      </div>
    </div>
  </div>
</template>
