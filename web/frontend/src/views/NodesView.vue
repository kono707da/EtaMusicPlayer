<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useNodesStore } from '../stores/nodes'
import { useAuthStore } from '../stores/auth'
import { usePluginsStore } from '../stores/plugins'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell
} from '@/components/ui/table'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter
} from '@/components/ui/dialog'
import { useToast } from '@/components/ui/toast/use-toast'
import { useConfirm } from '@/composables/use-confirm'
import {
  listRemoteNodes,
  createRemoteNode,
  updateRemoteNode,
  deleteRemoteNode,
  loginRemoteNode
} from '../api/plugin'
import { Plus, Loader2, HardDrive, Server, Zap, Pencil, Trash2, CircleAlert, Settings, AlertTriangle, Info, CheckCircle2 } from 'lucide-vue-next'
import { FEATURE_REGISTRY } from '../config/version'

const route = useRoute()
const router = useRouter()
const nodesStore = useNodesStore()
const authStore = useAuthStore()
const pluginsStore = usePluginsStore()
const toast = useToast()
const { confirm } = useConfirm()

const localNode = computed(() => pluginsStore.localNode)

const remoteNodeList = ref([])
const remoteNodeLoading = ref(false)
const remoteNodeDialogVisible = ref(false)
const editingRemoteNodeId = ref(null)
const remoteNodeSaving = ref(false)

// 自动健康检测状态：nodeId -> { status, message, checking }
// status: 'checking' | 'online' | 'offline' | 'auth_failed' | ''
const nodeHealth = reactive({})
const autoChecking = ref(false)

const remoteNodeForm = reactive({
  name: '',
  url: '',
  username: 'admin',
  password: '',
  verify_ssl: true
})

const remoteNodeErrors = reactive({})
// 对话框内联错误提示（保存/登录失败时直接显示在表单顶部）
const remoteNodeSaveError = ref('')

const isEditingRemoteNode = computed(() => editingRemoteNodeId.value !== null)

async function loadRemoteNodes() {
  remoteNodeLoading.value = true
  try {
    remoteNodeList.value = await listRemoteNodes()
    autoCheckAllHealth()
  } catch (e) {
    toast.error('加载远程节点失败', e.response?.data?.detail || e.message, e)
  } finally {
    remoteNodeLoading.value = false
  }
}

// 健康检测 + 版本校验 + 登录
// 流程：先版本校验 → 拿到版本信息但不兼容才标记 incompatible；
//       网络不可达（拿不到版本信息）继续走登录验证 → 由登录结果判定 offline / auth_failed
// 成功 => online + 已登录；认证失败 => auth_failed；版本不兼容 => incompatible；网络不可达 => offline
async function checkOneHealth(row, { silent = false } = {}) {
  nodeHealth[row.id] = { status: 'checking', message: '', checking: true }
  const nodeId = `remote-${row.id}`

  // Step 1: 版本校验（仅当真正拿到版本信息且不兼容时才拦截）
  // 网络错误（节点未启动）会抛出异常，进入 catch 后继续 Step 2 登录验证
  try {
    const compat = await nodesStore.checkNodeVersion(nodeId)
    if (compat.result === 'incompatible') {
      nodeHealth[row.id] = {
        status: 'incompatible',
        message: compat.reason,
        checking: false
      }
      if (!silent) toast.error('版本不兼容', compat.reason)
      return
    }
  } catch (e) {
    // 版本校验网络失败（节点未启动或 /api/version 不可达）
    // 继续走 Step 2 登录验证，由登录结果决定最终状态
  }

  // Step 2: 登录验证
  try {
    const result = await loginRemoteNode(row.id)
    // 登录成功 => 在线
    nodeHealth[row.id] = { status: 'online', message: '连接正常', checking: false }
    // 更新 nodesStore 中的 token（同时保留版本校验结果）
    syncRemoteNodeToStore(row, result)
    if (!silent) toast.success(`已连接：${row.name}`)
  } catch (e) {
    const status = e.response?.status
    const isAuth = status === 401 || status === 403
    // 离线时给出具体原因（<=15字）：节点未启动 / 网络不通 / 连接超时
    const offlineMsg = formatOfflineReason(e)
    nodeHealth[row.id] = {
      status: isAuth ? 'auth_failed' : 'offline',
      message: isAuth ? (e.response?.data?.detail || '用户名或密码错误') : offlineMsg,
      checking: false
    }
    if (!silent) {
      toast.error(isAuth ? '认证失败：凭证错误' : '节点离线：' + offlineMsg, nodeHealth[row.id].message, e)
    }
  }
}

// 根据错误对象归纳离线原因（<=15字，区分错误类型便于排查）
function formatOfflineReason(e) {
  const code = e?.code || ''
  const msg = String(e?.message || '')
  if (code === 'ECONNABORTED' || msg.includes('timeout')) return '节点连接超时未响应'
  if (code === 'ERR_NETWORK' || msg.includes('Network Error')) return '节点未启动或网络不通'
  if (e?.response?.status === 404) return '节点接口不存在，需升级'
  if (e?.response?.status === 502 || e?.response?.status === 503) return '节点服务暂不可用'
  return '节点未启动或网络不通'
}

// 进入页面自动并行检测所有节点
async function autoCheckAllHealth() {
  if (remoteNodeList.value.length === 0) return
  autoChecking.value = true
  await Promise.allSettled(remoteNodeList.value.map((row) => checkOneHealth(row, { silent: true })))
  autoChecking.value = false
}

// 将远程节点登录结果同步到 nodesStore
function syncRemoteNodeToStore(row, loginResult) {
  const nodeId = `remote-${row.id}`
  const nodeData = {
    id: nodeId,
    name: row.name,
    baseUrl: row.url,
    username: row.username,
    password: '',
    token: loginResult.access_token,
    userInfo: loginResult.user_info
  }
  const existing = nodesStore.nodes.find((n) => n.id === nodeId)
  if (existing) {
    nodesStore.updateNode(nodeId, {
      token: loginResult.access_token,
      userInfo: loginResult.user_info,
      name: row.name,
      baseUrl: row.url
    })
  } else {
    nodesStore.addNode(nodeData)
  }
}

function openAddRemoteNode() {
  editingRemoteNodeId.value = null
  remoteNodeForm.name = ''
  remoteNodeForm.url = 'http://127.0.0.1:8001'
  remoteNodeForm.username = 'admin'
  remoteNodeForm.password = ''
  remoteNodeForm.verify_ssl = true
  Object.keys(remoteNodeErrors).forEach((k) => delete remoteNodeErrors[k])
  remoteNodeSaveError.value = ''
  remoteNodeDialogVisible.value = true
}

function openEditRemoteNode(row) {
  editingRemoteNodeId.value = row.id
  remoteNodeForm.name = row.name || ''
  remoteNodeForm.url = row.url || ''
  remoteNodeForm.username = row.username || 'admin'
  remoteNodeForm.password = ''
  remoteNodeForm.verify_ssl = row.verify_ssl !== false
  Object.keys(remoteNodeErrors).forEach((k) => delete remoteNodeErrors[k])
  remoteNodeSaveError.value = ''
  remoteNodeDialogVisible.value = true
}

function validateRemoteNode() {
  Object.keys(remoteNodeErrors).forEach((k) => delete remoteNodeErrors[k])
  if (!remoteNodeForm.name) remoteNodeErrors.name = '请输入节点名称'
  if (!remoteNodeForm.url) remoteNodeErrors.url = '请输入节点 URL'
  else if (!/^https?:\/\/.+/.test(remoteNodeForm.url))
    remoteNodeErrors.url = '请输入完整 URL（如 http://127.0.0.1:8001）'
  if (!remoteNodeForm.username) remoteNodeErrors.username = '请输入用户名'
  return Object.keys(remoteNodeErrors).length === 0
}

// 保存远程节点：必须登录成功才保存
async function saveRemoteNode() {
  if (!validateRemoteNode()) return
  remoteNodeSaving.value = true
  remoteNodeSaveError.value = ''
  const isNew = !editingRemoteNodeId.value
  let createdNodeId = null
  try {
    const payload = {
      name: remoteNodeForm.name,
      url: remoteNodeForm.url.replace(/\/$/, ''),
      username: remoteNodeForm.username,
      verify_ssl: remoteNodeForm.verify_ssl,
      enabled: true
    }
    if (remoteNodeForm.password) {
      payload.password = remoteNodeForm.password
    }
    if (editingRemoteNodeId.value) {
      await updateRemoteNode(editingRemoteNodeId.value, payload)
    } else {
      const created = await createRemoteNode(payload)
      createdNodeId = created.id
    }

    // 登录验证：必须成功才保留节点
    const nodeId = editingRemoteNodeId.value || createdNodeId
    try {
      // 先做版本校验（仅拦截真正不兼容；网络错误继续尝试登录）
      const storeNodeId = `remote-${nodeId}`
      // 确保 store 中已有该节点（版本校验需要 baseUrl）
      const existing = nodesStore.nodes.find((n) => n.id === storeNodeId)
      if (!existing) {
        nodesStore.addNode({
          id: storeNodeId,
          name: remoteNodeForm.name,
          baseUrl: payload.url,
          username: remoteNodeForm.username,
          password: '',
          token: '',
          userInfo: null
        })
      }
      let compat = null
      try {
        compat = await nodesStore.checkNodeVersion(storeNodeId)
        if (compat.result === 'incompatible') {
          // 版本不兼容：删除新建的节点配置，不保留
          if (isNew && createdNodeId) {
            try { await deleteRemoteNode(createdNodeId) } catch { /* 忽略回滚错误 */ }
          }
          nodesStore.removeNode(storeNodeId)
          remoteNodeSaveError.value = compat.reason
          toast.error('版本不兼容', compat.reason)
          return
        }
      } catch (versionErr) {
        // 版本校验网络失败（节点未启动等），继续尝试登录以判定最终状态
        compat = null
      }

      const loginResult = await loginRemoteNode(nodeId)
      // 登录成功，同步到 store
      const row = remoteNodeList.value.find((r) => r.id === nodeId) || {
        id: nodeId,
        name: remoteNodeForm.name,
        url: payload.url,
        username: remoteNodeForm.username
      }
      syncRemoteNodeToStore(row, loginResult)
      nodeHealth[nodeId] = { status: 'online', message: '连接正常', checking: false }
      nodesStore.authVersion++
      // 部分兼容时提示
      if (compat && compat.result === 'partial') {
        const labels = compat.missingFeatures
          .map((f) => FEATURE_REGISTRY[f]?.label || f)
          .join('、')
        toast.warning('已连接但部分功能不可用', `不可用：${labels}`)
      } else {
        toast.success(isNew ? '节点已添加并登录' : '节点已更新并登录')
      }
      remoteNodeDialogVisible.value = false
      await loadRemoteNodes()
      if (route.query.redirect) {
        router.replace(route.query.redirect)
      }
    } catch (loginErr) {
      // 登录失败：新建节点则回滚删除
      if (isNew && createdNodeId) {
        try { await deleteRemoteNode(createdNodeId) } catch { /* 忽略回滚错误 */ }
      }
      const status = loginErr.response?.status
      const isAuth = status === 401 || status === 403
      // 内联错误提示：直接在对话框内显示具体原因（<=15字）
      const detail = isAuth ? '认证失败：用户名或密码错' : '节点离线：' + formatOfflineReason(loginErr)
      remoteNodeSaveError.value = detail
      toast.error(
        isNew ? '添加失败：登录验证未通过' : '更新失败：登录验证未通过',
        detail,
        loginErr
      )
    }
  } catch (e) {
    // 创建/更新本身失败
    if (isNew && createdNodeId) {
      try { await deleteRemoteNode(createdNodeId) } catch { /* 忽略回滚错误 */ }
    }
    const errMsg = e.response?.data?.detail || e.message
    remoteNodeSaveError.value = '保存失败：' + (errMsg ? String(errMsg).slice(0, 12) : '未知错误')
    toast.error('保存远程节点失败', errMsg, e)
  } finally {
    remoteNodeSaving.value = false
  }
}

// 跳转到该节点的管理页面
function goManage(row) {
  const nodeId = `remote-${row.id}`
  router.push({ path: '/admin/scan', query: { nodeId } })
}

// 跳转到本地节点的管理页面
function goManageLocal() {
  const localNode = nodesStore.nodes.find((n) => n.baseUrl === '/local_node')
  if (localNode) {
    router.push({ path: '/admin/scan', query: { nodeId: localNode.id } })
  } else {
    router.push('/admin/scan')
  }
}

// 删除 = 退出登录 + 删除配置
async function confirmDeleteRemoteNode(row) {
  const ok = await confirm(`确定删除远程节点「${row.name}」？将同时退出登录并删除配置。`, {
    title: '提示',
    type: 'danger'
  })
  if (!ok) return
  try {
    await deleteRemoteNode(row.id)
    // 从 store 移除（退出登录）
    nodesStore.removeNode(`remote-${row.id}`)
    nodesStore.authVersion++
    delete nodeHealth[row.id]
    toast.success('已删除并退出登录')
    await loadRemoteNodes()
  } catch (e) {
    toast.error('删除远程节点失败', e.response?.data?.detail || e.message, e)
  }
}

// 节点详情对话框（展示版本不兼容/部分功能缺失等信息）
const detailDialogVisible = ref(false)
const detailNode = ref(null)
const detailCompat = ref(null)

function showNodeDetail(row) {
  const nodeId = `remote-${row.id}`
  const node = nodesStore.getNode(nodeId)
  detailNode.value = { ...row, nodeId }
  detailCompat.value = node?.compatibility || null
  detailDialogVisible.value = true
}

function getFeatureLabel(feat) {
  return FEATURE_REGISTRY[feat]?.label || feat
}

function getFeatureDescription(feat) {
  return FEATURE_REGISTRY[feat]?.description || ''
}

onMounted(() => {
  pluginsStore.syncLocalNode(nodesStore)
  loadRemoteNodes()
})
</script>

<template>
  <div class="flex flex-col gap-6">
    <div class="flex items-center justify-between">
      <h2 class="text-2xl font-bold tracking-tight text-gold-gradient">节点管理</h2>
      <div class="flex items-center gap-2">
        <Button variant="outline" size="sm" :disabled="autoChecking || remoteNodeLoading" @click="autoCheckAllHealth">
          <Loader2 v-if="autoChecking" class="h-4 w-4 animate-spin" />
          <Zap v-else class="h-4 w-4" />
          重新检测
        </Button>
        <Button @click="openAddRemoteNode">
          <Plus class="h-4 w-4" />
          添加远程节点
        </Button>
      </div>
    </div>

    <!-- 本地节点卡片 -->
    <div v-if="localNode?.available" class="rounded-lg border border-primary/30 bg-card shadow-sm overflow-hidden">
      <div class="flex items-center gap-3 border-b border-border bg-primary/5 px-4 py-2.5">
        <HardDrive class="h-4 w-4 text-primary" />
        <span class="text-sm font-medium text-foreground">本机节点</span>
        <span class="text-xs text-muted-foreground">由 local_node 插件提供，插件启用即自动连接</span>
      </div>

      <div class="flex items-center justify-between gap-4 px-4 py-4">
        <div class="flex items-center gap-4">
          <div class="flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10">
            <HardDrive class="h-6 w-6 text-primary" />
          </div>
          <div class="flex flex-col gap-1">
            <div class="flex items-center gap-2">
              <span class="font-medium text-foreground">本地节点</span>
              <Badge variant="success">已连接</Badge>
            </div>
            <div class="text-xs text-muted-foreground">
              {{ localNode.base_url }} · admin · v{{ localNode.version }}
            </div>
          </div>
        </div>

        <div class="flex items-center gap-2">
          <span class="text-xs text-muted-foreground">插件启用即保持连接</span>
          <Button
            v-if="authStore.isAdmin"
            variant="ghost"
            size="sm"
            @click="goManageLocal"
          >
            <Settings class="h-4 w-4" />
            管理
          </Button>
        </div>
      </div>
    </div>

    <!-- 远程节点 -->
    <div class="flex flex-col gap-3">
      <div class="flex items-center gap-2">
        <Server class="h-4 w-4 text-muted-foreground" />
        <span class="text-sm font-medium text-muted-foreground">远程节点</span>
      </div>

      <div v-if="remoteNodeLoading" class="flex items-center gap-2 py-4 text-muted-foreground">
        <Loader2 class="h-4 w-4 animate-spin" />
        加载中...
      </div>

      <Alert v-if="!remoteNodeLoading && remoteNodeList.length === 0" class="border-border">
        <AlertDescription class="text-muted-foreground">
          尚未配置远程节点。点击右上角『添加远程节点』连接其他主机。
        </AlertDescription>
      </Alert>

      <div v-if="!remoteNodeLoading && remoteNodeList.length > 0" class="rounded-lg border bg-card shadow-sm">
        <Table>
          <TableHeader>
            <TableRow class="hover:bg-transparent">
              <TableHead class="w-[64px]"></TableHead>
              <TableHead>名称</TableHead>
              <TableHead>URL</TableHead>
              <TableHead class="w-[100px]">用户名</TableHead>
              <TableHead class="w-[120px]">状态</TableHead>
              <TableHead class="w-[200px]">操作</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            <TableRow v-for="row in remoteNodeList" :key="row.id">
              <TableCell></TableCell>
              <TableCell class="font-medium text-foreground">{{ row.name }}</TableCell>
              <TableCell class="text-muted-foreground">{{ row.url }}</TableCell>
              <TableCell class="text-muted-foreground">{{ row.username }}</TableCell>
              <TableCell>
                <div v-if="nodeHealth[row.id]?.checking" class="flex items-center gap-1">
                  <Loader2 class="h-3 w-3 animate-spin" />
                  <span class="text-xs text-muted-foreground">检测中</span>
                </div>
                <span
                  v-else-if="nodeHealth[row.id]?.status === 'online'"
                  class="inline-flex items-center gap-1 text-xs text-emerald-500 font-medium"
                  :title="nodeHealth[row.id].message"
                >
                  ● 在线
                </span>
                <span
                  v-else-if="nodeHealth[row.id]?.status === 'incompatible'"
                  class="inline-flex items-center gap-1 text-xs text-destructive font-medium"
                  :title="nodeHealth[row.id].message"
                >
                  ● 版本不兼容
                </span>
                <span
                  v-else-if="nodeHealth[row.id]?.status === 'auth_failed'"
                  class="inline-flex items-center gap-1 text-xs text-amber-500 font-medium"
                  :title="nodeHealth[row.id].message"
                >
                  ● 认证失败
                </span>
                <span
                  v-else-if="nodeHealth[row.id]?.status === 'offline'"
                  class="inline-flex items-center gap-1 text-xs text-destructive font-medium"
                  :title="nodeHealth[row.id].message"
                >
                  ● 离线
                </span>
                <span v-else class="text-xs text-muted-foreground">—</span>
              </TableCell>
              <TableCell>
                <div class="flex flex-wrap items-center gap-1">
                  <Button
                    variant="ghost"
                    size="sm"
                    :disabled="!nodeHealth[row.id] || nodeHealth[row.id]?.status !== 'online'"
                    @click="goManage(row)"
                  >
                    <Settings class="h-4 w-4" />
                    管理
                  </Button>
                  <Button
                    v-if="nodeHealth[row.id]?.status === 'incompatible' || nodeHealth[row.id]?.status === 'auth_failed' || nodeHealth[row.id]?.status === 'offline'"
                    variant="ghost"
                    size="sm"
                    @click="showNodeDetail(row)"
                  >
                    <Info class="h-4 w-4" />
                    详情
                  </Button>
                  <Button variant="ghost" size="sm" @click="openEditRemoteNode(row)">
                    <Pencil class="h-4 w-4" />
                    编辑
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    class="text-destructive hover:text-destructive"
                    @click="confirmDeleteRemoteNode(row)"
                  >
                    <Trash2 class="h-4 w-4" />
                    删除
                  </Button>
                </div>
              </TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </div>
    </div>

    <!-- 远程节点编辑对话框 -->
    <Dialog :open="remoteNodeDialogVisible" @update:open="(v) => !v && (remoteNodeDialogVisible = false)">
      <DialogContent class="max-w-md">
        <DialogHeader>
          <DialogTitle>
            {{ isEditingRemoteNode ? '编辑远程节点' : '添加远程节点' }}
          </DialogTitle>
          <DialogDescription>
            配置远程 eta_node 实例的连接信息。保存时会自动验证登录，登录成功才会保留。
          </DialogDescription>
        </DialogHeader>

        <Alert v-if="remoteNodeSaveError" variant="destructive" class="flex items-start gap-3 border-l-4">
          <CircleAlert class="h-4 w-4 mt-0.5 shrink-0" />
          <AlertDescription class="text-destructive font-medium">
            {{ remoteNodeSaveError }}
          </AlertDescription>
        </Alert>

        <div class="space-y-4">
          <div class="space-y-2">
            <Label for="rn-name">节点名称</Label>
            <Input
              id="rn-name"
              v-model="remoteNodeForm.name"
              placeholder="如：远程节点A"
              class="bg-secondary/60"
            />
            <p v-if="remoteNodeErrors.name" class="text-xs text-destructive">{{ remoteNodeErrors.name }}</p>
          </div>

          <div class="space-y-2">
            <Label for="rn-url">节点 URL</Label>
            <Input
              id="rn-url"
              v-model="remoteNodeForm.url"
              placeholder="http://127.0.0.1:8001"
              class="bg-secondary/60"
            />
            <p v-if="remoteNodeErrors.url" class="text-xs text-destructive">{{ remoteNodeErrors.url }}</p>
          </div>

          <div class="space-y-2">
            <Label for="rn-user">用户名</Label>
            <Input id="rn-user" v-model="remoteNodeForm.username" class="bg-secondary/60" />
            <p v-if="remoteNodeErrors.username" class="text-xs text-destructive">{{ remoteNodeErrors.username }}</p>
          </div>

          <div class="space-y-2">
            <Label for="rn-pwd">密码</Label>
            <Input
              id="rn-pwd"
              v-model="remoteNodeForm.password"
              type="password"
              :placeholder="isEditingRemoteNode ? '留空表示不修改' : '请输入密码'"
              class="bg-secondary/60"
            />
          </div>

          <div class="flex items-center justify-between gap-3">
            <div class="flex flex-col gap-1">
              <Label>验证 SSL 证书</Label>
              <p class="text-xs text-muted-foreground">如遇 SSL 错误可关闭此选项。</p>
            </div>
            <Switch v-model:checked="remoteNodeForm.verify_ssl" />
          </div>
        </div>

        <DialogFooter class="gap-2">
          <Button variant="ghost" @click="remoteNodeDialogVisible = false">取消</Button>
          <Button variant="gold" :disabled="remoteNodeSaving" @click="saveRemoteNode">
            <Loader2 v-if="remoteNodeSaving" class="h-4 w-4 animate-spin" />
            保存
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>

    <!-- 节点详情对话框（版本校验信息） -->
    <Dialog :open="detailDialogVisible" @update:open="(v) => !v && (detailDialogVisible = false)">
      <DialogContent class="max-w-lg">
        <DialogHeader>
          <DialogTitle>节点详情：{{ detailNode?.name }}</DialogTitle>
          <DialogDescription>
            版本校验与功能兼容性信息
          </DialogDescription>
        </DialogHeader>

        <div v-if="detailCompat" class="space-y-3">
          <!-- 兼容性状态 -->
          <div class="flex items-start gap-2 rounded-md border p-3"
            :class="{
              'border-destructive/40 bg-destructive/5': detailCompat.result === 'incompatible',
              'border-amber-500/40 bg-amber-500/5': detailCompat.result === 'partial',
              'border-emerald-500/40 bg-emerald-500/5': detailCompat.result === 'ok'
            }"
          >
            <CircleAlert v-if="detailCompat.result === 'incompatible'" class="h-4 w-4 mt-0.5 shrink-0 text-destructive" />
            <AlertTriangle v-else-if="detailCompat.result === 'partial'" class="h-4 w-4 mt-0.5 shrink-0 text-amber-500" />
            <component :is="CheckCircle2" v-else class="h-4 w-4 mt-0.5 shrink-0 text-emerald-500" />
            <div class="flex-1 text-sm">
              <p v-if="detailCompat.result === 'incompatible'" class="font-medium text-destructive">
                版本不兼容，无法连接
              </p>
              <p v-else-if="detailCompat.result === 'partial'" class="font-medium text-amber-600">
                部分功能不可用
              </p>
              <p v-else class="font-medium text-emerald-600">完全兼容</p>
              <p v-if="detailCompat.reason" class="mt-1 text-muted-foreground">{{ detailCompat.reason }}</p>
            </div>
          </div>

          <!-- 版本信息 -->
          <div v-if="detailCompat.versionInfo" class="rounded-md border border-border p-3 space-y-1.5 text-sm">
            <div class="flex justify-between">
              <span class="text-muted-foreground">Node 版本</span>
              <span class="font-mono">v{{ detailCompat.versionInfo.version }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-muted-foreground">API 协议版本</span>
              <span class="font-mono">v{{ detailCompat.versionInfo.api_version }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-muted-foreground">支持功能数</span>
              <span class="font-mono">{{ detailCompat.versionInfo.features?.length || 0 }} 项</span>
            </div>
          </div>

          <!-- 缺失功能列表 -->
          <div v-if="detailCompat.missingFeatures && detailCompat.missingFeatures.length > 0">
            <p class="text-sm font-medium mb-2">不可用的功能：</p>
            <div class="space-y-1">
              <div
                v-for="feat in detailCompat.missingFeatures"
                :key="feat"
                class="flex items-start gap-2 rounded-md bg-muted/40 px-3 py-1.5 text-sm"
              >
                <span class="font-medium">{{ getFeatureLabel(feat) }}</span>
                <span class="text-muted-foreground text-xs mt-0.5">{{ getFeatureDescription(feat) }}</span>
              </div>
            </div>
            <p class="text-xs text-muted-foreground mt-2">
              这些功能已禁用，请升级 node 到最新版本以获得完整体验。
            </p>
          </div>
        </div>

        <div v-else class="text-sm text-muted-foreground py-4 text-center">
          暂无版本校验信息，请点击「重新检测」
        </div>

        <DialogFooter>
          <Button variant="ghost" @click="detailDialogVisible = false">关闭</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  </div>
</template>
