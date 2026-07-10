<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useNodesStore } from '../stores/nodes'
import { useAuthStore } from '../stores/auth'
import { usePluginsStore } from '../stores/plugins'
import NodeForm from '../components/NodeForm.vue'
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
  testRemoteNode,
  loginRemoteNode,
  activateRemoteNode
} from '../api/plugin'
import { Plus, Loader2, HardDrive, Server, Zap, Pencil, Trash2, LogIn, LogOut, Star } from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()
const nodesStore = useNodesStore()
const authStore = useAuthStore()
const pluginsStore = usePluginsStore()
const toast = useToast()
const { confirm } = useConfirm()

const formVisible = ref(false)
const editingNode = ref(null)
const presetNode = ref(null)
const loggingId = ref(null)

const localNode = computed(() => pluginsStore.localNode)
const localNodeRecord = computed(() =>
  nodesStore.nodes.find((n) => n.baseUrl === '/local_node')
)

const remoteNodeList = ref([])
const remoteNodeLoading = ref(false)
const remoteNodeDialogVisible = ref(false)
const editingRemoteNodeId = ref(null)
const remoteNodeSaving = ref(false)
const testingNodeId = ref(null)

// 自动健康检测状态：nodeId -> { status, message, checking }
// status: 'checking' | 'online' | 'offline' | 'auth_failed' | ''
const nodeHealth = reactive({})
const autoChecking = ref(false)

const remoteNodeForm = reactive({
  name: '',
  url: '',
  username: 'admin',
  password: '',
  verify_ssl: true,
  enabled: true
})

const remoteNodeErrors = reactive({})

const isEditingRemoteNode = computed(() => editingRemoteNodeId.value !== null)

async function loadRemoteNodes() {
  remoteNodeLoading.value = true
  try {
    remoteNodeList.value = await listRemoteNodes()
    // 加载完成后自动健康检测
    autoCheckAllHealth()
  } catch (e) {
    toast.error('加载远程节点失败', e.response?.data?.detail || e.message)
  } finally {
    remoteNodeLoading.value = false
  }
}

// 对单个节点执行健康检测
// success=true => online；连接失败 => offline；认证失败 => auth_failed
async function checkOneHealth(row, { silent = false } = {}) {
  nodeHealth[row.id] = { status: 'checking', message: '', checking: true }
  try {
    const result = await testRemoteNode(row.id)
    if (result.success) {
      nodeHealth[row.id] = { status: 'online', message: result.message, checking: false }
      // 测试通过且未登录，自动静默登录
      if (!isRemoteNodeLoggedIn(row)) {
        try {
          await loginRemoteNodeAction(row, { silent: true })
        } catch { /* 登录失败不阻塞健康检测展示 */ }
      }
    } else {
      const msg = result.message || ''
      // 区分离线 vs 认证失败
      const isAuth = /认证失败|HTTP 4\d\d|401|403/.test(msg)
      nodeHealth[row.id] = {
        status: isAuth ? 'auth_failed' : 'offline',
        message: msg,
        checking: false
      }
      if (!silent) {
        toast.error('连接测试失败', msg)
      }
    }
  } catch (e) {
    const msg = e.response?.data?.detail || e.message
    nodeHealth[row.id] = { status: 'offline', message: msg, checking: false }
    if (!silent) toast.error('连接测试失败', msg)
  }
}

// 进入页面自动并行检测所有节点
async function autoCheckAllHealth() {
  if (remoteNodeList.value.length === 0) return
  autoChecking.value = true
  // 并行检测，每个节点独立处理，互不阻塞
  await Promise.allSettled(remoteNodeList.value.map((row) => checkOneHealth(row, { silent: true })))
  autoChecking.value = false
}

function openAddRemote() {
  editingNode.value = null
  presetNode.value = null
  formVisible.value = true
}

function openEdit(node) {
  editingNode.value = node
  presetNode.value = null
  formVisible.value = true
}

function onSaved(payload) {
  if (payload.id) {
    nodesStore.updateNode(payload.id, {
      name: payload.name,
      baseUrl: payload.baseUrl,
      username: payload.username,
      password: payload.password,
      token: payload.token,
      userInfo: payload.userInfo
    })
    toast.success('节点已更新并登录')
    if (payload.id === nodesStore.activeNodeId) {
      authStore.restoreFromNode(nodesStore.activeNode)
    }
  } else {
    nodesStore.addNode({
      name: payload.name,
      baseUrl: payload.baseUrl,
      username: payload.username,
      password: payload.password
    })
    const added = nodesStore.nodes[nodesStore.nodes.length - 1]
    nodesStore.updateNode(added.id, {
      token: payload.token,
      userInfo: payload.userInfo
    })
    nodesStore.setActive(added.id)
    nodesStore.authVersion++
    toast.success('节点已添加并登录')
  }
  if (route.query.redirect) {
    router.replace(route.query.redirect)
  }
}

async function onLogin(node) {
  loggingId.value = node.id
  try {
    await nodesStore.loginNode(node.id)
    authStore.restoreFromNode(nodesStore.activeNode)
    toast.success(`已登录节点：${node.name}`)
    if (route.query.redirect) {
      router.replace(route.query.redirect)
    }
  } catch (e) {
    toast.error('登录失败', e.response?.data?.detail || e.message)
  } finally {
    loggingId.value = null
  }
}

async function onLogout(node) {
  const ok = await confirm(`确定登出节点「${node.name}」？配置保留，可重新登录。`, {
    title: '提示',
    type: 'warning'
  })
  if (!ok) return
  nodesStore.logoutNode(node.id)
  authStore.restoreFromNode(nodesStore.activeNode)
  toast.success('已登出')
}

async function onDelete(node) {
  const ok = await confirm(`确定删除节点「${node.name}」？该节点的本地凭证将被清除。`, {
    title: '提示',
    type: 'danger'
  })
  if (!ok) return
  nodesStore.removeNode(node.id)
  authStore.restoreFromNode(nodesStore.activeNode)
  toast.success('已删除')
}

function setActive(node) {
  nodesStore.setActive(node.id)
  authStore.restoreFromNode(node)
  toast.success(`已切换到节点：${node.name}`)
}

function openAddRemoteNode() {
  editingRemoteNodeId.value = null
  remoteNodeForm.name = ''
  remoteNodeForm.url = 'http://127.0.0.1:8001'
  remoteNodeForm.username = 'admin'
  remoteNodeForm.password = ''
  remoteNodeForm.verify_ssl = true
  remoteNodeForm.enabled = true
  Object.keys(remoteNodeErrors).forEach((k) => delete remoteNodeErrors[k])
  remoteNodeDialogVisible.value = true
}

function openEditRemoteNode(row) {
  editingRemoteNodeId.value = row.id
  remoteNodeForm.name = row.name || ''
  remoteNodeForm.url = row.url || ''
  remoteNodeForm.username = row.username || 'admin'
  remoteNodeForm.password = ''
  remoteNodeForm.verify_ssl = row.verify_ssl !== false
  remoteNodeForm.enabled = row.enabled !== false
  Object.keys(remoteNodeErrors).forEach((k) => delete remoteNodeErrors[k])
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

async function saveRemoteNode() {
  if (!validateRemoteNode()) return
  remoteNodeSaving.value = true
  try {
    const payload = {
      name: remoteNodeForm.name,
      url: remoteNodeForm.url.replace(/\/$/, ''),
      username: remoteNodeForm.username,
      verify_ssl: remoteNodeForm.verify_ssl,
      enabled: remoteNodeForm.enabled
    }
    if (remoteNodeForm.password) {
      payload.password = remoteNodeForm.password
    }
    if (editingRemoteNodeId.value) {
      await updateRemoteNode(editingRemoteNodeId.value, payload)
      toast.success('远程节点已更新')
    } else {
      await createRemoteNode(payload)
      toast.success('远程节点已添加')
    }
    remoteNodeDialogVisible.value = false
    await loadRemoteNodes()
  } catch (e) {
    toast.error('保存远程节点失败', e.response?.data?.detail || e.message)
  } finally {
    remoteNodeSaving.value = false
  }
}

async function confirmDeleteRemoteNode(row) {
  const ok = await confirm(`确定删除远程节点「${row.name}」？`, {
    title: '提示',
    type: 'danger'
  })
  if (!ok) return
  try {
    await deleteRemoteNode(row.id)
    toast.success('已删除')
    await loadRemoteNodes()
  } catch (e) {
    toast.error('删除远程节点失败', e.response?.data?.detail || e.message)
  }
}

async function testRemoteNodeConnection(row) {
  testingNodeId.value = row.id
  try {
    await checkOneHealth(row)
    const h = nodeHealth[row.id]
    if (h && h.status === 'online') {
      toast.success('连接测试成功', h.message)
    }
  } finally {
    testingNodeId.value = null
  }
}

async function loginRemoteNodeAction(row, { silent = false } = {}) {
  loggingId.value = row.id
  try {
    const result = await loginRemoteNode(row.id)
    const nodeData = {
      id: `remote-${row.id}`,
      name: row.name,
      baseUrl: row.url,
      username: row.username,
      password: '',
      token: result.access_token,
      userInfo: result.user_info
    }
    const existing = nodesStore.nodes.find((n) => n.id === nodeData.id)
    if (existing) {
      nodesStore.updateNode(nodeData.id, {
        token: result.access_token,
        userInfo: result.user_info,
        name: row.name,
        baseUrl: row.url
      })
    } else {
      nodesStore.addNode(nodeData)
      nodesStore.updateNode(nodeData.id, {
        token: result.access_token,
        userInfo: result.user_info
      })
    }
    nodesStore.setActive(nodeData.id)
    nodesStore.authVersion++
    authStore.restoreFromNode(nodesStore.activeNode)
    if (!silent) toast.success(`已登录节点：${row.name}`)
    if (route.query.redirect) {
      router.replace(route.query.redirect)
    }
  } catch (e) {
    if (!silent) toast.error('登录失败', e.response?.data?.detail || e.message)
    throw e
  } finally {
    loggingId.value = null
  }
}

async function activateRemoteNodeAction(row) {
  try {
    await activateRemoteNode(row.id)
    await loadRemoteNodes()
    toast.success(`已设为当前节点：${row.name}`)
  } catch (e) {
    toast.error('设置失败', e.response?.data?.detail || e.message)
  }
}

function isRemoteNodeLoggedIn(row) {
  return !!nodesStore.nodes.find((n) => n.id === `remote-${row.id}`)?.token
}

function isRemoteNodeActive(row) {
  return nodesStore.activeNodeId === `remote-${row.id}`
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
              <Badge v-if="localNodeRecord && localNodeRecord.id === nodesStore.activeNodeId" variant="default">
                当前
              </Badge>
            </div>
            <div class="text-xs text-muted-foreground">
              {{ localNode.base_url }} · admin · v{{ localNode.version }}
            </div>
          </div>
        </div>

        <div class="flex items-center gap-2">
          <Button
            v-if="localNodeRecord && localNodeRecord.id !== nodesStore.activeNodeId"
            variant="ghost"
            size="sm"
            @click="setActive(localNodeRecord)"
          >
            设为当前
          </Button>
          <span v-else class="text-xs text-muted-foreground">插件启用即保持连接</span>
        </div>
      </div>
    </div>

    <!-- 远程节点（统一管理） -->
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
              <TableHead class="w-[80px]">状态</TableHead>
              <TableHead class="w-[110px]">连接</TableHead>
              <TableHead class="w-[80px]">登录</TableHead>
              <TableHead class="w-[280px]">操作</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            <TableRow v-for="row in remoteNodeList" :key="row.id">
              <TableCell>
                <Badge v-if="isRemoteNodeActive(row)" variant="success">当前</Badge>
              </TableCell>
              <TableCell class="font-medium text-foreground">{{ row.name }}</TableCell>
              <TableCell class="text-muted-foreground">{{ row.url }}</TableCell>
              <TableCell class="text-muted-foreground">{{ row.username }}</TableCell>
              <TableCell>
                <Badge v-if="row.enabled" variant="success">启用</Badge>
                <Badge v-else variant="secondary">禁用</Badge>
              </TableCell>
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
                <Badge v-if="isRemoteNodeLoggedIn(row)" variant="success">已登录</Badge>
                <Badge v-else variant="secondary">未登录</Badge>
              </TableCell>
              <TableCell>
                <div class="flex flex-wrap items-center gap-1">
                  <Button
                    v-if="isRemoteNodeLoggedIn(row) && !isRemoteNodeActive(row)"
                    variant="ghost"
                    size="sm"
                    @click="activateRemoteNodeAction(row)"
                  >
                    <Star class="h-4 w-4" />
                    设为当前
                  </Button>
                  <Button
                    v-if="!isRemoteNodeLoggedIn(row)"
                    variant="ghost"
                    size="sm"
                    :disabled="loggingId === row.id"
                    @click="loginRemoteNodeAction(row)"
                  >
                    <Loader2 v-if="loggingId === row.id" class="h-4 w-4 animate-spin" />
                    <LogIn v-else class="h-4 w-4" />
                    登录
                  </Button>
                  <Button
                    v-if="isRemoteNodeLoggedIn(row)"
                    variant="ghost"
                    size="sm"
                    @click="onLogout(nodesStore.nodes.find((n) => n.id === `remote-${row.id}`))"
                  >
                    <LogOut class="h-4 w-4" />
                    登出
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    :disabled="testingNodeId === row.id"
                    @click="testRemoteNodeConnection(row)"
                  >
                    <Loader2 v-if="testingNodeId === row.id" class="h-4 w-4 animate-spin" />
                    <Zap v-else class="h-4 w-4" />
                    测试
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
            配置远程 eta_node 实例的连接信息。节点可用于浏览曲库和下载推送。
          </DialogDescription>
        </DialogHeader>

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

          <div class="flex items-center justify-between gap-3">
            <div class="flex flex-col gap-1">
              <Label>启用</Label>
              <p class="text-xs text-muted-foreground">禁用后下载插件不会使用此节点。</p>
            </div>
            <Switch v-model:checked="remoteNodeForm.enabled" />
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

    <NodeForm v-model:visible="formVisible" :node="editingNode" :preset="presetNode" @saved="onSaved" />
  </div>
</template>
