<script setup>
import { ref, computed, onMounted } from 'vue'
import {
  listPlugins,
  syncRegistry,
  enablePlugin,
  disablePlugin,
  deletePlugin,
  restartServer,
  analyzeChanges
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
import { RefreshCw, Trash2, Package, Loader2, Save, XCircle } from 'lucide-vue-next'

const toast = useToast()
const { confirm } = useConfirm()

const plugins = ref([])
const loading = ref(false)
const syncing = ref(false)
const applying = ref(false) // 正在保存并重启
const toggling = ref(null)
// 待保存的变更：{ pluginName: desiredEnabled }
// Switch 切换只写入这里，不立即调后端
const pendingChanges = ref({})

async function load() {
  loading.value = true
  try {
    plugins.value = await listPlugins()
  } catch (e) {
    toast.error('加载插件列表失败', e.response?.data?.detail || e.message)
  } finally {
    loading.value = false
  }
}

// Switch 的有效显示值：pending 优先，否则原始值
function effectiveEnabled(plugin) {
  if (pendingChanges.value[plugin.name] !== undefined) {
    return pendingChanges.value[plugin.name]
  }
  return plugin.enabled
}

// 是否有未保存的变更
const hasPendingChanges = computed(
  () => Object.keys(pendingChanges.value).length > 0
)

// 变更摘要
const pendingSummary = computed(() => {
  const entries = Object.entries(pendingChanges.value)
  if (entries.length === 0) return ''
  const parts = entries.map(([name, enabled]) => {
    const action = enabled ? '启用' : '禁用'
    return `${action} ${name}`
  })
  return parts.join('，')
})

// 受影响的插件数量
const pendingCount = computed(() => Object.keys(pendingChanges.value).length)

function onToggle(plugin, newValue) {
  // 只记录到 pendingChanges，不调后端
  if (newValue === plugin.enabled) {
    // 恢复到原始值，删除 pending 记录
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
    toast.error('同步失败', e.response?.data?.detail || e.message)
  } finally {
    syncing.value = false
  }
}

async function onApplyChanges() {
  const changes = Object.entries(pendingChanges.value)
  if (changes.length === 0) return

  applying.value = true
  try {
    // 1. 先分析变更是否需要重启
    const analysis = await analyzeChanges(pendingChanges.value)

    // 2. 根据分析结果给用户不同的确认提示
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

    // 3. 批量提交 enable/disable 到数据库
    for (const [name, enabled] of changes) {
      if (enabled) {
        await enablePlugin(name)
      } else {
        await disablePlugin(name)
      }
    }

    // 4. 根据是否需要重启走不同路径
    if (analysis.needs_restart) {
      // 触发服务器重启
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
      // 无需重启，仅刷新页面
      toast.success('变更已保存，正在刷新页面...')
      setTimeout(() => window.location.reload(), 600)
    }
  } catch (e) {
    toast.error('应用变更失败', e.message || '未知错误')
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
  } catch (e) {
    toast.error('删除失败', e.response?.data?.detail || e.message)
  }
}

function stateBadge(plugin) {
  if (!plugin.files_present) {
    return { label: '文件缺失', variant: 'destructive' }
  }
  if (plugin.loaded) {
    return { label: '运行中', variant: 'success' }
  }
  if (plugin.enabled) {
    return { label: '待重启', variant: 'default' }
  }
  return { label: '已禁用', variant: 'secondary' }
}

onMounted(load)
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

    <Alert class="border-primary/30 bg-primary/5">
      <AlertDescription class="text-muted-foreground">
        插件提供访问端的扩展能力（如本地节点）。切换开关后点击「保存生效」，
        系统将自动重启访问端服务并刷新页面，变更随即生效。
      </AlertDescription>
    </Alert>

    <!-- 待保存变更提示条 -->
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
        尚未发现任何插件。请将插件目录放入 backend/app/plugins/ 下，然后点击『扫描插件』。
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
              {{ p.name }}
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
