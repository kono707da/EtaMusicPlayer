<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useToast } from '@/components/ui/toast/use-toast'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { Slider } from '@/components/ui/slider'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '@/components/ui/select'
import { Save, Loader2, Settings, Headphones, Music, RefreshCw, Download, ScrollText } from 'lucide-vue-next'
import { usePluginsStore } from '../stores/plugins'
import { useNodesStore } from '../stores/nodes'
import { getSystemLogs } from '../api/plugin'

// 插件 API 采用动态 import：插件未启用时不会加载其模块代码
const toast = useToast()
const pluginsStore = usePluginsStore()
const nodesStore = useNodesStore()

// ============ Tab 管理 ============
const activeTab = ref('system')

const tabs = computed(() => {
  const t = [{ key: 'system', label: '系统', icon: Settings }]
  if (pluginsStore.enabledNames.includes('asmr_one')) {
    t.push({ key: 'asmr', label: 'ASMR', icon: Headphones })
  }
  if (pluginsStore.enabledNames.includes('bili_audio')) {
    t.push({ key: 'bili', label: 'B站音频', icon: Music })
  }
  return t
})

// 当前激活标签页对应的插件被禁用时，回退到系统标签页
watch(tabs, (newTabs) => {
  if (!newTabs.some((t) => t.key === activeTab.value)) {
    activeTab.value = 'system'
  }
})

// ============ 系统设置 ============
const systemForm = ref({
  volume: 0.8,
  autoPlayNext: true,
})
const systemSaving = ref(false)

function loadSystemSettings() {
  const vol = localStorage.getItem('etamusic_volume')
  systemForm.value.volume = vol !== null ? parseFloat(vol) : 0.8
  systemForm.value.autoPlayNext = localStorage.getItem('etamusic_auto_play_next') !== 'false'
}

async function saveSystemSettings() {
  systemSaving.value = true
  try {
    localStorage.setItem('etamusic_volume', String(systemForm.value.volume))
    localStorage.setItem('etamusic_auto_play_next', String(systemForm.value.autoPlayNext))
    toast.success('系统设置已保存')
  } finally {
    systemSaving.value = false
  }
}

// ============ 系统日志 ============
const logLevel = ref('ERROR')
const logLines = ref(500)
const logText = ref('')
const logLoading = ref(false)
const logMeta = ref({ file_path: '', file_size: 0, exists: false, total_returned: 0 })

function lineClass(line) {
  if (/\[ERROR\]/.test(line) || /\[CRITICAL\]/.test(line)) return 'log-err'
  if (/\[WARNING\]/.test(line)) return 'log-warn'
  if (/\[INFO\]/.test(line)) return 'log-info'
  return 'log-other'
}

async function loadLogs() {
  logLoading.value = true
  try {
    const data = await getSystemLogs({ lines: logLines.value, level: logLevel.value })
    logText.value = (data.lines || []).join('\n')
    logMeta.value = {
      file_path: data.file_path || '',
      file_size: data.file_size || 0,
      exists: data.exists !== false,
      total_returned: data.total_returned || 0
    }
  } catch (e) {
    logText.value = ''
    toast.error('加载日志失败', e?.response?.data?.detail || e.message)
  } finally {
    logLoading.value = false
  }
}

function downloadLogs() {
  if (!logText.value) {
    toast.error('日志为空', '没有可下载的内容')
    return
  }
  const stamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19)
  const blob = new Blob([logText.value], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `eta_web_${logLevel.value}_${stamp}.log`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

function formatSize(bytes) {
  if (!bytes) return '0 B'
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(2)} MB`
}

// ============ ASMR 设置 ============
const asmrForm = ref({
  proxy_url: '',
  verify_ssl: true,
  subdir: '',
  default_watch_dir_id: '',
  cache_pool_size_mb: '500'
})
const asmrLoading = ref(false)
const asmrSaving = ref(false)
const watchDirs = ref([])

async function loadAsmrSettings() {
  asmrLoading.value = true
  try {
    const { getSettings: getAsmrSettings } = await import('../plugins/asmr_one/api')
    const data = await getAsmrSettings()
    asmrForm.value = {
      proxy_url: data.proxy_url ?? '',
      verify_ssl: data.verify_ssl !== 'false' && data.verify_ssl !== '0',
      subdir: data.subdir ?? '',
      default_watch_dir_id: data.default_watch_dir_id ?? '',
      cache_pool_size_mb: data.cache_pool_size_mb ?? '500'
    }
    // 尝试加载监控目录列表
    const node = nodesStore.activeNode
    if (node) {
      try {
        const { listWatchDirs } = await import('../api/node')
        const dirs = await listWatchDirs(node)
        watchDirs.value = dirs || []
      } catch { /* 静默 */ }
    }
  } catch (e) {
    toast.error('加载 ASMR 设置失败', e?.response?.data?.detail || e.message)
  } finally {
    asmrLoading.value = false
  }
}

async function saveAsmrSettings() {
  asmrSaving.value = true
  try {
    const { updateSettings: updateAsmrSettings } = await import('../plugins/asmr_one/api')
    await updateAsmrSettings({
      ...asmrForm.value,
      verify_ssl: asmrForm.value.verify_ssl ? 'true' : 'false'
    })
    toast.success('ASMR 设置已保存')
  } catch (e) {
    toast.error('保存失败', e?.response?.data?.detail || e.message)
  } finally {
    asmrSaving.value = false
  }
}

// ============ B站音频设置 ============
const biliForm = ref({
  proxy_url: '',
  sessdata: '',
  cache_pool_size_mb: '500'
})
const biliLoading = ref(false)
const biliSaving = ref(false)

async function loadBiliSettings() {
  biliLoading.value = true
  try {
    const { getSettings: getBiliSettings } = await import('../plugins/bili_audio/api')
    const data = await getBiliSettings()
    biliForm.value = {
      proxy_url: data.proxy_url ?? '',
      sessdata: data.sessdata ?? '',
      cache_pool_size_mb: data.cache_pool_size_mb ?? '500'
    }
  } catch (e) {
    toast.error('加载B站设置失败', e?.response?.data?.detail || e.message)
  } finally {
    biliLoading.value = false
  }
}

async function saveBiliSettings() {
  biliSaving.value = true
  try {
    const { updateSettings: updateBiliSettings } = await import('../plugins/bili_audio/api')
    const updates = [
      { key: 'proxy_url', value: biliForm.value.proxy_url },
      { key: 'sessdata', value: biliForm.value.sessdata },
      { key: 'cache_pool_size_mb', value: biliForm.value.cache_pool_size_mb }
    ]
    await updateBiliSettings(updates)
    toast.success('B站设置已保存')
  } catch (e) {
    toast.error('保存失败', e?.response?.data?.detail || e.message)
  } finally {
    biliSaving.value = false
  }
}

// ============ 初始化 ============
onMounted(() => {
  loadSystemSettings()
  loadLogs()
  if (pluginsStore.enabledNames.includes('asmr_one')) loadAsmrSettings()
  if (pluginsStore.enabledNames.includes('bili_audio')) loadBiliSettings()
})
</script>

<template>
  <div class="space-y-5">
    <h2 class="text-xl font-bold text-foreground">设置</h2>

    <!-- Tab 导航 -->
    <div class="flex gap-1 border-b border-border">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        class="flex items-center gap-2 px-4 py-2.5 text-sm font-medium transition-colors border-b-2 -mb-px"
        :class="activeTab === tab.key
          ? 'border-primary text-primary'
          : 'border-transparent text-muted-foreground hover:text-foreground'"
        @click="activeTab = tab.key"
      >
        <component :is="tab.icon" class="h-4 w-4" />
        {{ tab.label }}
      </button>
    </div>

    <!-- 系统设置 -->
    <div v-show="activeTab === 'system'" class="space-y-4">
      <div class="max-w-xl space-y-4">
      <Card class="border-border bg-card/40">
        <CardHeader>
          <CardTitle class="text-base">播放器</CardTitle>
        </CardHeader>
        <CardContent class="space-y-5">
          <!-- 音量 -->
          <div class="space-y-2">
            <div class="flex items-center justify-between">
              <Label>默认音量</Label>
              <span class="text-sm text-muted-foreground">{{ Math.round(systemForm.volume * 100) }}%</span>
            </div>
            <Slider
              :model-value="[Math.round(systemForm.volume * 100)]"
              :max="100"
              :step="1"
              @update:model-value="(v) => systemForm.volume = (v[0] / 100)"
            />
            <p class="text-xs text-muted-foreground">页面刷新后恢复此音量设置</p>
          </div>

          <!-- 自动播放下一首 -->
          <div class="flex items-center justify-between gap-3">
            <div class="flex flex-col gap-1">
              <Label>自动播放下一首</Label>
              <p class="text-xs text-muted-foreground">当前曲目播放完毕后自动播放队列中的下一首</p>
            </div>
            <Switch v-model:checked="systemForm.autoPlayNext" />
          </div>
        </CardContent>
      </Card>

      <div class="flex justify-end">
        <Button variant="gold" :disabled="systemSaving" @click="saveSystemSettings">
          <Loader2 v-if="systemSaving" class="h-4 w-4 animate-spin" />
          <Save v-else class="h-4 w-4" />
          保存
        </Button>
      </div>
      </div>

      <!-- 日志查看 -->
      <Card class="border-border bg-card/40">
        <CardHeader>
          <div class="flex items-center justify-between gap-3 flex-wrap">
            <CardTitle class="text-base flex items-center gap-2">
              <ScrollText class="h-4 w-4" />
              日志查看
            </CardTitle>
            <div class="flex items-center gap-2 flex-wrap">
              <Select :model-value="logLevel" @update:model-value="(v) => { logLevel = v; loadLogs() }">
                <SelectTrigger class="w-[140px] h-8">
                  <SelectValue placeholder="级别" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ALL">全部</SelectItem>
                  <SelectItem value="DEBUG">DEBUG+</SelectItem>
                  <SelectItem value="INFO">INFO+</SelectItem>
                  <SelectItem value="WARNING">WARNING+</SelectItem>
                  <SelectItem value="ERROR">ERROR+</SelectItem>
                  <SelectItem value="CRITICAL">CRITICAL</SelectItem>
                </SelectContent>
              </Select>
              <Select :model-value="String(logLines)" @update:model-value="(v) => { logLines = Number(v); loadLogs() }">
                <SelectTrigger class="w-[110px] h-8">
                  <SelectValue placeholder="行数" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="100">100 行</SelectItem>
                  <SelectItem value="500">500 行</SelectItem>
                  <SelectItem value="1000">1000 行</SelectItem>
                  <SelectItem value="2000">2000 行</SelectItem>
                </SelectContent>
              </Select>
              <Button variant="outline" size="sm" :disabled="logLoading" @click="loadLogs">
                <Loader2 v-if="logLoading" class="h-4 w-4 animate-spin" />
                <RefreshCw v-else class="h-4 w-4" />
                刷新
              </Button>
              <Button variant="outline" size="sm" :disabled="logLoading || !logText" @click="downloadLogs">
                <Download class="h-4 w-4" />
                下载
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div class="flex flex-col gap-2">
            <div class="flex items-center justify-between text-xs text-muted-foreground flex-wrap gap-2">
              <span>文件：{{ logMeta.file_path || '未生成' }}</span>
              <span>
                共 {{ logMeta.total_returned }} 行 ·
                大小 {{ formatSize(logMeta.file_size) }}
                <span v-if="!logMeta.exists" class="text-destructive">（文件不存在）</span>
              </span>
            </div>
            <div class="log-view">
              <pre v-if="logText" class="log-pre"><code><template v-for="(line, i) in logText.split('\n')" :key="i"><span :class="lineClass(line)">{{ line }}
</span></template></code></pre>
              <div v-else-if="logLoading" class="flex items-center justify-center py-8 text-muted-foreground">
                <Loader2 class="mr-2 h-4 w-4 animate-spin" /> 加载中...
              </div>
              <div v-else class="flex items-center justify-center py-8 text-muted-foreground text-sm">
                无日志记录
              </div>
            </div>
            <p class="text-xs text-muted-foreground">
              用于排查后端报错（如加载远程节点失败 500 等）。默认显示 ERROR 及以上级别，切换级别可查看更多。
            </p>
          </div>
        </CardContent>
      </Card>
    </div>

    <!-- ASMR 设置（插件未启用时不渲染） -->
    <div v-if="pluginsStore.enabledNames.includes('asmr_one') && activeTab === 'asmr'" class="max-w-xl">
      <div v-if="asmrLoading" class="flex items-center justify-center py-12 text-muted-foreground">
        <Loader2 class="mr-2 h-5 w-5 animate-spin" /> 加载中...
      </div>
      <div v-else class="space-y-4">
        <Card class="border-border bg-card/40">
          <CardContent class="pt-5 space-y-4">
            <div class="flex flex-col gap-1.5">
              <Label>代理地址</Label>
              <Input v-model="asmrForm.proxy_url" placeholder="http://127.0.0.1:7897" />
              <p class="text-xs text-muted-foreground">访问 asmr.one 时使用的 HTTP 代理。留空则不使用代理。</p>
            </div>

            <div class="flex items-center justify-between gap-3">
              <div class="flex flex-col gap-1">
                <Label>验证 SSL 证书</Label>
                <p class="text-xs text-muted-foreground">通过代理访问时如遇 SSL 错误，可关闭此选项。</p>
              </div>
              <Switch v-model:checked="asmrForm.verify_ssl" />
            </div>

            <div class="flex flex-col gap-1.5">
              <Label>下载子目录</Label>
              <Input v-model="asmrForm.subdir" placeholder="ASMR" />
              <p class="text-xs text-muted-foreground">
                文件将下载到 {watch_dir}/{子目录}/{作品名}/。留空表示直接放在 watch_dir 根下。
              </p>
            </div>

            <div class="flex flex-col gap-1.5">
              <Label>默认监控目录</Label>
              <Select v-model="asmrForm.default_watch_dir_id">
                <SelectTrigger>
                  <SelectValue placeholder="不指定" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">不指定</SelectItem>
                  <SelectItem v-for="d in watchDirs" :key="d.id" :value="String(d.id)">
                    {{ d.name }} ({{ d.path }})
                  </SelectItem>
                </SelectContent>
              </Select>
              <p class="text-xs text-muted-foreground">下载文件默认推送到此监控目录</p>
            </div>

            <div class="flex flex-col gap-1.5">
              <Label>缓存池大小（MB）</Label>
              <Input v-model="asmrForm.cache_pool_size_mb" type="number" placeholder="500" />
              <p class="text-xs text-muted-foreground">远程节点下载时访问端缓存的临时文件最大大小（MB）</p>
            </div>
          </CardContent>
        </Card>

        <div class="flex justify-end">
          <Button variant="gold" :disabled="asmrSaving" @click="saveAsmrSettings">
            <Loader2 v-if="asmrSaving" class="h-4 w-4 animate-spin" />
            <Save v-else class="h-4 w-4" />
            保存
          </Button>
        </div>
      </div>
    </div>

    <!-- B站音频设置（插件未启用时不渲染） -->
    <div v-if="pluginsStore.enabledNames.includes('bili_audio') && activeTab === 'bili'" class="max-w-xl">
      <div v-if="biliLoading" class="flex items-center justify-center py-12 text-muted-foreground">
        <Loader2 class="mr-2 h-5 w-5 animate-spin" /> 加载中...
      </div>
      <div v-else class="space-y-4">
        <Card class="border-border bg-card/40">
          <CardContent class="pt-5 space-y-4">
            <div class="flex flex-col gap-1.5">
              <Label>代理地址</Label>
              <Input v-model="biliForm.proxy_url" placeholder="http://127.0.0.1:7897（留空则不使用代理）" />
              <p class="text-xs text-muted-foreground">访问B站API时使用的HTTP代理</p>
            </div>

            <div class="flex flex-col gap-1.5">
              <Label>SESSDATA Cookie</Label>
              <Input v-model="biliForm.sessdata" type="password" placeholder="B站登录Cookie（可选）" />
              <p class="text-xs text-muted-foreground">部分视频需要登录才能获取音频流。从浏览器Cookie中复制SESSDATA值。</p>
            </div>

            <div class="flex flex-col gap-1.5">
              <Label>缓存池大小（MB）</Label>
              <Input v-model="biliForm.cache_pool_size_mb" type="number" placeholder="500" />
              <p class="text-xs text-muted-foreground">远程节点下载时访问端缓存的临时文件最大大小（MB）</p>
            </div>
          </CardContent>
        </Card>

        <div class="flex justify-end">
          <Button variant="gold" :disabled="biliSaving" @click="saveBiliSettings">
            <Loader2 v-if="biliSaving" class="h-4 w-4 animate-spin" />
            <Save v-else class="h-4 w-4" />
            保存
          </Button>
        </div>
      </div>
    </div>
  </div>
</template>
