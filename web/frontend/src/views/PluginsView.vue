<script setup>
import { ref, computed, onMounted } from 'vue'
import {
  listPlugins,
  syncRegistry,
  enablePlugin,
  disablePlugin,
  deletePlugin,
  restartServer,
  analyzeChanges,
  listOnlinePlugins,
  getOnlineRegistryStatus,
  refreshOnlineRegistry,
  installOnlinePlugin,
  updateOnlinePlugin,
  importPlugin
} from '../api/plugin'
import axios from 'axios'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Switch } from '@/components/ui/switch'
import { Alert, AlertDescription } from '@/components/ui/alert'
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell
} from '@/components/ui/table'
import { useToast } from '@/components/ui/toast/use-toast'
import { useConfirm } from '@/composables/use-confirm'
import {
  RefreshCw, Trash2, Package, Loader2, Save, XCircle,
  Download, Cloud, CloudOff, ArrowUpCircle, CheckCircle2,
  XCircle as XCircleIcon, AlertTriangle, Wifi, WifiOff,
  Upload, FileArchive, Link2
} from 'lucide-vue-next'

const toast = useToast()
const { confirm } = useConfirm()

const plugins = ref([])
const loading = ref(false)
const syncing = ref(false)
const applying = ref(false)
const toggling = ref(null)
const pendingChanges = ref({})

const onlinePlugins = ref([])
const onlineLoading = ref(false)
const onlineAvailable = ref(false)
const onlineError = ref('')
const etaWebVersion = ref('')
const installing = ref(null)
const updating = ref(null)

const activeTab = ref('installed')

// 手动导入相关
const importing = ref(false)
const dragOver = ref(false)
const fileInput = ref(null)

async function load() {
  loading.value = true
  try {
    plugins.value = await listPlugins()
  } catch (e) {
    toast.error('加载插件列表失败', e.response?.data?.detail || e.message, e)
  } finally {
    loading.value = false
  }
}

async function loadOnline() {
  onlineLoading.value = true
  try {
    const status = await getOnlineRegistryStatus()
    onlineAvailable.value = status.available
    etaWebVersion.value = status.eta_web_version
    onlineError.value = status.error || ''
    if (status.available) {
      onlinePlugins.value = await listOnlinePlugins()
    }
  } catch (e) {
    onlineAvailable.value = false
    onlineError.value = e.response?.data?.detail || e.message
  } finally {
    onlineLoading.value = false
  }
}

async function onRefreshOnline() {
  onlineLoading.value = true
  try {
    await refreshOnlineRegistry()
    onlinePlugins.value = await listOnlinePlugins()
    toast.success('在线注册表已刷新')
  } catch (e) {
    toast.error('刷新失败', e.response?.data?.detail || e.message, e)
  } finally {
    onlineLoading.value = false
  }
}

async function onInstall(plugin) {
  const ok = await confirm(
    `确定安装插件「${plugin.display_name || plugin.name}」v${plugin.online_version}？\n\n将从 GitHub 下载插件文件并安装 Python 依赖，安装后需要重启服务才能生效。`,
    { title: '安装插件', type: 'info' }
  )
  if (!ok) return
  installing.value = plugin.name
  try {
    const result = await installOnlinePlugin(plugin.name)
    toast.success(result.message, result.details || '')
    await load()
    await loadOnline()
  } catch (e) {
    toast.error('安装失败', e.response?.data?.detail || e.message, e)
  } finally {
    installing.value = null
  }
}

async function onUpdate(plugin) {
  const ok = await confirm(
    `确定更新插件「${plugin.display_name || plugin.name}」到 v${plugin.online_version}？\n\n将覆盖当前安装的版本，更新后需要重启服务才能生效。`,
    { title: '更新插件', type: 'info' }
  )
  if (!ok) return
  updating.value = plugin.name
  try {
    const result = await updateOnlinePlugin(plugin.name)
    toast.success(result.message, result.details || '')
    await load()
    await loadOnline()
  } catch (e) {
    toast.error('更新失败', e.response?.data?.detail || e.message, e)
  } finally {
    updating.value = null
  }
}

async function onImport(file) {
  if (!file) return
  if (!file.name.toLowerCase().endsWith('.zip')) {
    toast.error('文件格式错误', '请上传 .zip 格式的插件包')
    return
  }
  importing.value = true
  try {
    const result = await importPlugin(file)
    toast.success(result.message, result.details || '')
    await load()
    await loadOnline()
  } catch (e) {
    const detail = e.response?.data?.detail || e.message
    toast.error('导入失败', detail, e)
  } finally {
    importing.value = false
  }
}

function onDrop(e) {
  dragOver.value = false
  const files = e.dataTransfer?.files
  if (files && files.length > 0) {
    onImport(files[0])
  }
}

function onFileSelect(e) {
  const files = e.target?.files
  if (files && files.length > 0) {
    onImport(files[0])
  }
  // 重置 input 以允许重复选择同一文件
  if (fileInput.value) {
    fileInput.value.value = ''
  }
}

function effectiveEnabled(plugin) {
  if (pendingChanges.value[plugin.name] !== undefined) {
    return pendingChanges.value[plugin.name]
  }
  return plugin.enabled
}

const hasPendingChanges = computed(
  () => Object.keys(pendingChanges.value).length > 0
)

const pendingSummary = computed(() => {
  const entries = Object.entries(pendingChanges.value)
  if (entries.length === 0) return ''
  const parts = entries.map(([name, enabled]) => {
    const action = enabled ? '启用' : '禁用'
    return `${action} ${name}`
  })
  return parts.join('，')
})

const pendingCount = computed(() => Object.keys(pendingChanges.value).length)

function onToggle(plugin, newValue) {
  if (newValue === plugin.enabled) {
    const next = { ...pendingChanges.value }
    delete next[plugin.name]
    pendingChanges.value = next
  } else {
    pendingChanges.value = { ...pendingChanges.value, [plugin.name]: newValue }
  }
}

function discardChanges() {
  pendingChanges.value = {}
}

async function onSync() {
  syncing.value = true
  try {
    const result = await syncRegistry()
    toast.success(result.message || '同步完成')
    await load()
  } catch (e) {
    toast.error('同步失败', e.response?.data?.detail || e.message, e)
  } finally {
    syncing.value = false
  }
}

async function onApplyChanges() {
  const changes = Object.entries(pendingChanges.value)
  if (changes.length === 0) return

  applying.value = true
  try {
    const analysis = await analyzeChanges(pendingChanges.value)

    let confirmMsg = ''
    if (analysis.needs_restart) {
      const affectedDesc = analysis.affected
        .map((a) => `${a.action === 'enable' ? '启用' : '禁用'} ${a.name}`)
        .join('，')
      confirmMsg = `将应用以下变更：${pendingSummary.value}\n\n其中 ${affectedDesc} 需要重启访问端服务（约 5-10 秒中断），重启完成后页面将自动刷新。是否继续？`
    } else {
      confirmMsg = `将应用以下变更：${pendingSummary.value}\n\n变更无需重启服务器，保存后页面将自动刷新。是否继续？`
    }

    const ok = await confirm(confirmMsg, {
      title: analysis.needs_restart ? '保存并重启' : '保存并刷新',
      type: analysis.needs_restart ? 'warning' : 'info'
    })
    if (!ok) {
      applying.value = false
      return
    }

    for (const [name, enabled] of changes) {
      if (enabled) {
        await enablePlugin(name)
      } else {
        await disablePlugin(name)
      }
    }

    if (analysis.needs_restart) {
      try {
        await restartServer()
      } catch (e) {
        console.log('restart 请求已发送（进程退出可能导致连接错误，属正常）')
      }
      toast.info('正在重启访问端服务...', '请等待 5-10 秒')
      await waitForServer(30000, 1000)
      toast.success('服务已恢复，正在刷新页面...')
      setTimeout(() => window.location.reload(), 800)
    } else {
      toast.success('变更已保存，正在刷新页面...')
      setTimeout(() => window.location.reload(), 600)
    }
  } catch (e) {
    toast.error('应用变更失败', e.message || '未知错误', e)
    applying.value = false
    await load()
    pendingChanges.value = {}
  }
}

async function waitForServer(timeoutMs = 30000, intervalMs = 1000) {
  const start = Date.now()
  while (Date.now() - start < timeoutMs) {
    try {
      const resp = await axios.get('/health', { timeout: 3000 })
      if (resp.status === 200) return true
    } catch (e) {
      // 服务还没起来，继续等
    }
    await new Promise((r) => setTimeout(r, intervalMs))
  }
  throw new Error('等待服务恢复超时（30 秒）')
}

async function onDelete(plugin) {
  const ok = await confirm(
    `确定删除插件「${plugin.name}」？将同时删除插件文件与数据库记录，此操作不可恢复。`,
    { title: '危险操作', type: 'danger' }
  )
  if (!ok) return
  try {
    const result = await deletePlugin(plugin.name)
    toast.success(result.message || '已删除')
    await load()
    await loadOnline()
  } catch (e) {
    toast.error('删除失败', e.response?.data?.detail || e.message, e)
  }
}

function stateBadge(plugin) {
  if (!plugin.files_present) {
    return { label: '文件缺失', variant: 'destructive' }
  }
  if (plugin.is_library) {
    return { label: '可用', variant: 'success' }
  }
  if (plugin.loaded) {
    return { label: '运行中', variant: 'success' }
  }
  if (plugin.enabled) {
    return { label: '待重启', variant: 'default' }
  }
  return { label: '已禁用', variant: 'secondary' }
}

function compatIcon(compatible) {
  if (compatible === true) return 'check'
  if (compatible === false) return 'x'
  return 'unknown'
}

function categoryLabel(cat) {
  const map = { core: '核心', download: '下载', library: '库', other: '其他', unknown: '未知' }
  return map[cat] || cat
}

function parseDependentBy(plugin) {
  try {
    return JSON.parse(plugin.dependent_by || '[]')
  } catch {
    return []
  }
}

function parseDependencies(plugin) {
  try {
    return JSON.parse(plugin.dependencies || '[]')
  } catch {
    return []
  }
}

onMounted(() => {
  load()
  loadOnline()
})
</script>

<template>
  <div class="relative flex flex-col gap-6">
    <div class="flex items-center justify-between">
      <h2 class="text-2xl font-bold tracking-tight text-gold-gradient">
        插件管理
      </h2>
      <div class="flex items-center gap-2">
        <Button variant="secondary" :disabled="syncing" @click="onSync">
          <RefreshCw v-if="syncing" class="h-4 w-4 animate-spin" />
          <Package v-else class="h-4 w-4" />
          扫描插件
        </Button>
      </div>
    </div>

    <!-- Tab 切换 -->
    <div class="flex border-b border-border">
      <button
        class="px-4 py-2 text-sm font-medium transition-colors border-b-2 -mb-px"
        :class="activeTab === 'installed'
          ? 'border-primary text-primary'
          : 'border-transparent text-muted-foreground hover:text-foreground'"
        @click="activeTab = 'installed'"
      >
        已安装 ({{ plugins.length }})
      </button>
      <button
        class="px-4 py-2 text-sm font-medium transition-colors border-b-2 -mb-px"
        :class="activeTab === 'online'
          ? 'border-primary text-primary'
          : 'border-transparent text-muted-foreground hover:text-foreground'"
        @click="activeTab = 'online'"
      >
        <Cloud v-if="onlineAvailable" class="inline h-4 w-4 mr-1" />
        <CloudOff v-else class="inline h-4 w-4 mr-1" />
        在线插件 ({{ onlinePlugins.length }})
      </button>
      <button
        class="px-4 py-2 text-sm font-medium transition-colors border-b-2 -mb-px"
        :class="activeTab === 'import'
          ? 'border-primary text-primary'
          : 'border-transparent text-muted-foreground hover:text-foreground'"
        @click="activeTab = 'import'"
      >
        <Upload class="inline h-4 w-4 mr-1" />
        导入
      </button>
    </div>

    <!-- ===== 已安装插件 Tab ===== -->
    <template v-if="activeTab === 'installed'">
      <Alert class="border-primary/30 bg-primary/5">
        <AlertDescription class="text-muted-foreground">
          插件提供访问端的扩展能力（如本地节点）。切换开关后点击「保存生效」，
          系统将自动重启访问端服务并刷新页面，变更随即生效。
        </AlertDescription>
      </Alert>

      <Alert
        v-if="hasPendingChanges"
        class="border-primary bg-primary/10 shadow-gold-glow"
      >
        <AlertDescription class="flex items-center justify-between gap-4">
          <div class="flex flex-col gap-1">
            <span class="font-medium text-primary">
              有 {{ pendingCount }} 项待保存变更
            </span>
            <span class="text-sm text-muted-foreground">
              {{ pendingSummary }} · 保存后自动重启服务并刷新页面
            </span>
          </div>
          <div class="flex items-center gap-2">
            <Button variant="ghost" size="sm" :disabled="applying" @click="discardChanges">
              <XCircle class="h-4 w-4" />
              放弃
            </Button>
            <Button variant="gold" size="sm" :disabled="applying" @click="onApplyChanges">
              <Save v-if="!applying" class="h-4 w-4" />
              <Loader2 v-else class="h-4 w-4 animate-spin" />
              保存生效
            </Button>
          </div>
        </AlertDescription>
      </Alert>

      <Alert v-if="loading && plugins.length === 0" class="border-border">
        <AlertDescription class="flex items-center gap-2">
          <Loader2 class="h-4 w-4 animate-spin" />
          正在加载插件列表...
        </AlertDescription>
      </Alert>

      <Alert v-if="!loading && plugins.length === 0" class="border-border">
        <AlertDescription>
          尚未安装任何插件。切换到「在线插件」标签页浏览并安装可用插件。
        </AlertDescription>
      </Alert>

      <div v-if="plugins.length > 0" class="rounded-lg border bg-card shadow-sm">
        <Table>
          <TableHeader>
            <TableRow class="hover:bg-transparent">
              <TableHead class="w-[80px]">状态</TableHead>
              <TableHead>插件名</TableHead>
              <TableHead class="w-[80px]">版本</TableHead>
              <TableHead>说明</TableHead>
              <TableHead class="w-[100px]">启用</TableHead>
              <TableHead class="w-[100px]">操作</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            <TableRow v-for="p in plugins" :key="p.id">
              <TableCell>
                <Badge :variant="stateBadge(p).variant">
                  {{ stateBadge(p).label }}
                </Badge>
              </TableCell>
              <TableCell class="font-mono font-medium text-foreground">
                <div class="flex items-center gap-2">
                  {{ p.name }}
                  <Badge v-if="p.is_library" variant="secondary" class="text-xs">库</Badge>
                  <Badge v-if="p.is_dependency" variant="outline" class="text-xs">依赖</Badge>
                </div>
                <div v-if="parseDependentBy(p).length > 0" class="text-xs text-muted-foreground mt-1">
                  被 {{ parseDependentBy(p).join('、') }} 依赖
                </div>
                <div v-if="parseDependencies(p).length > 0" class="text-xs text-muted-foreground mt-1">
                  依赖 {{ parseDependencies(p).map(d => d.name).join('、') }}
                </div>
              </TableCell>
              <TableCell class="text-muted-foreground">{{ p.version }}</TableCell>
              <TableCell class="text-muted-foreground">{{ p.description }}</TableCell>
              <TableCell>
                <Switch
                  :model-value="effectiveEnabled(p)"
                  :disabled="toggling === p.name || !p.files_present || applying"
                  @update:model-value="(v) => onToggle(p, v)"
                />
              </TableCell>
              <TableCell>
                <Button
                  variant="ghost"
                  size="sm"
                  class="text-destructive hover:text-destructive"
                  :disabled="p.loaded"
                  @click="onDelete(p)"
                >
                  <Trash2 class="h-4 w-4" />
                </Button>
              </TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </div>
    </template>

    <!-- ===== 在线插件 Tab ===== -->
    <template v-if="activeTab === 'online'">
      <!-- 连接状态 -->
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2 text-sm">
          <Wifi v-if="onlineAvailable" class="h-4 w-4 text-green-500" />
          <WifiOff v-else class="h-4 w-4 text-red-500" />
          <span v-if="onlineAvailable" class="text-muted-foreground">
            在线注册表已连接 · 访问端版本 v{{ etaWebVersion }}
          </span>
          <span v-else class="text-red-500">
            无法连接在线注册表{{ onlineError ? '：' + onlineError : '' }}
          </span>
        </div>
        <Button
          variant="secondary"
          size="sm"
          :disabled="onlineLoading"
          @click="onRefreshOnline"
        >
          <RefreshCw v-if="onlineLoading" class="h-4 w-4 animate-spin" />
          <Cloud v-else class="h-4 w-4" />
          刷新
        </Button>
      </div>

      <Alert v-if="onlineLoading && onlinePlugins.length === 0" class="border-border">
        <AlertDescription class="flex items-center gap-2">
          <Loader2 class="h-4 w-4 animate-spin" />
          正在从 GitHub 获取在线插件列表...
        </AlertDescription>
      </Alert>

      <Alert v-if="!onlineLoading && !onlineAvailable" class="border-destructive/50 bg-destructive/5">
        <AlertDescription class="flex items-center gap-2">
          <CloudOff class="h-4 w-4" />
          无法连接在线注册表。请检查网络连接后重试。
        </AlertDescription>
      </Alert>

      <div v-if="onlinePlugins.length > 0" class="rounded-lg border bg-card shadow-sm">
        <Table>
          <TableHeader>
            <TableRow class="hover:bg-transparent">
              <TableHead class="w-[60px]">图标</TableHead>
              <TableHead>插件名</TableHead>
              <TableHead class="w-[70px]">分类</TableHead>
              <TableHead class="w-[90px]">在线版本</TableHead>
              <TableHead class="w-[90px]">本地版本</TableHead>
              <TableHead class="w-[90px]">兼容性</TableHead>
              <TableHead>说明</TableHead>
              <TableHead class="w-[120px]">操作</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            <TableRow v-for="p in onlinePlugins" :key="p.name">
              <TableCell>
                <Package class="h-5 w-5 text-muted-foreground" />
              </TableCell>
              <TableCell>
                <div class="font-medium text-foreground">{{ p.display_name || p.name }}</div>
                <div class="text-xs text-muted-foreground font-mono">{{ p.name }}</div>
                <div v-if="p.is_library" class="mt-1">
                  <Badge variant="secondary" class="text-xs">库类型</Badge>
                </div>
                <div v-if="p.dependencies && p.dependencies.length > 0" class="text-xs text-muted-foreground mt-1">
                  依赖 {{ p.dependencies.map(d => d.name).join('、') }}
                </div>
              </TableCell>
              <TableCell>
                <Badge variant="secondary">{{ categoryLabel(p.category) }}</Badge>
              </TableCell>
              <TableCell class="font-mono text-sm">
                v{{ p.online_version || '-' }}
              </TableCell>
              <TableCell class="font-mono text-sm">
                <span v-if="p.installed">v{{ p.local_version }}</span>
                <span v-else class="text-muted-foreground">-</span>
              </TableCell>
              <TableCell>
                <div v-if="p.compatible === true" class="flex items-center gap-1 text-green-600">
                  <CheckCircle2 class="h-4 w-4" />
                  <span class="text-xs">兼容</span>
                </div>
                <div v-else-if="p.compatible === false" class="flex items-center gap-1 text-red-500">
                  <XCircleIcon class="h-4 w-4" />
                  <span class="text-xs" :title="p.compatibility_reason">不兼容</span>
                </div>
                <div v-else class="flex items-center gap-1 text-yellow-500">
                  <AlertTriangle class="h-4 w-4" />
                  <span class="text-xs" :title="p.compatibility_reason">未知</span>
                </div>
              </TableCell>
              <TableCell class="text-sm text-muted-foreground">
                {{ p.description }}
              </TableCell>
              <TableCell>
                <div class="flex items-center gap-1">
                  <Button
                    v-if="!p.installed && p.can_install"
                    variant="default"
                    size="sm"
                    :disabled="installing === p.name"
                    @click="onInstall(p)"
                  >
                    <Loader2 v-if="installing === p.name" class="h-4 w-4 animate-spin" />
                    <Download v-else class="h-4 w-4" />
                    安装
                  </Button>
                  <Button
                    v-else-if="p.can_update"
                    variant="default"
                    size="sm"
                    :disabled="updating === p.name"
                    @click="onUpdate(p)"
                  >
                    <Loader2 v-if="updating === p.name" class="h-4 w-4 animate-spin" />
                    <ArrowUpCircle v-else class="h-4 w-4" />
                    更新
                  </Button>
                  <Badge v-else-if="p.installed && !p.can_update" variant="success">
                    已是最新
                  </Badge>
                  <Badge v-else-if="!p.compatible" variant="destructive">
                    不兼容
                  </Badge>
                  <Badge v-else-if="!p.online_available" variant="secondary">
                    仅本地
                  </Badge>
                </div>
              </TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </div>
    </template>

    <!-- ===== 手动导入 Tab ===== -->
    <template v-if="activeTab === 'import'">
      <Alert class="border-primary/30 bg-primary/5">
        <AlertDescription class="text-muted-foreground">
          手动导入插件 zip 包。系统会自动校验包结构、SHA256（如在线注册表声明）和依赖关系。
          导入后需要重启服务才能生效。
        </AlertDescription>
      </Alert>

      <!-- 拖拽区域 -->
      <div
        class="rounded-lg border-2 border-dashed p-8 text-center transition-colors"
        :class="dragOver
          ? 'border-primary bg-primary/10'
          : 'border-border hover:border-primary/50'"
        @dragover.prevent="dragOver = true"
        @dragleave.prevent="dragOver = false"
        @drop.prevent="onDrop"
      >
        <input
          ref="fileInput"
          type="file"
          accept=".zip"
          class="hidden"
          @change="onFileSelect"
        />
        <div v-if="importing" class="flex flex-col items-center gap-3">
          <Loader2 class="h-10 w-10 animate-spin text-primary" />
          <div class="text-sm text-muted-foreground">正在导入插件...</div>
        </div>
        <div v-else class="flex flex-col items-center gap-3">
          <FileArchive class="h-12 w-12 text-muted-foreground" />
          <div class="text-base font-medium text-foreground">
            拖拽插件 zip 包到此处
          </div>
          <div class="text-sm text-muted-foreground">或</div>
          <Button variant="secondary" @click="fileInput?.click()">
            <Upload class="h-4 w-4" />
            选择文件
          </Button>
          <div class="text-xs text-muted-foreground mt-2">
            支持 .zip 格式，最大 100MB
          </div>
        </div>
      </div>

      <!-- 导入说明 -->
      <div class="rounded-lg border bg-card p-4 space-y-2">
        <div class="flex items-center gap-2 text-sm font-medium text-foreground">
          <Link2 class="h-4 w-4" />
          导入须知
        </div>
        <ul class="text-sm text-muted-foreground space-y-1 pl-6 list-disc">
          <li>zip 包应包含插件目录结构（如 <code class="text-xs">asmr_one/eta_asmr/plugin.py</code>）</li>
          <li>系统会自动检测插件名和包名</li>
          <li>如在线注册表声明了 SHA256，将自动校验完整性</li>
          <li>含依赖的插件会自动安装缺失的依赖（需联网）</li>
          <li>已知插件会覆盖更新，导入前会自动备份</li>
        </ul>
      </div>
    </template>

    <!-- 重启/刷新遮罩 -->
    <div
      v-if="applying"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm"
    >
      <div class="flex flex-col items-center gap-4 text-center">
        <Loader2 class="h-12 w-12 animate-spin text-primary" />
        <div class="text-lg font-medium text-foreground">正在应用插件变更</div>
        <div class="text-sm text-muted-foreground">
          页面将在片刻后自动刷新...
        </div>
      </div>
    </div>
  </div>
</template>
