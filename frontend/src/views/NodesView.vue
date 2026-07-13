<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useNodesStore } from '../stores/nodes'
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
import { useToast } from '@/components/ui/toast/use-toast'
import { useConfirm } from '@/composables/use-confirm'
import { Plus, Loader2, HardDrive, Server, Settings } from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()
const nodesStore = useNodesStore()
const pluginsStore = usePluginsStore()
const toast = useToast()
const { confirm } = useConfirm()

const formVisible = ref(false)
const editingNode = ref(null)
const presetNode = ref(null)
const loggingId = ref(null)

// 本地节点状态（来自 pluginsStore，应用启动时已同步）
const localNode = computed(() => pluginsStore.localNode)
// 本地节点在 nodes store 中的记录（自动连接后已有 token）
const localNodeRecord = computed(() =>
  nodesStore.nodes.find((n) => n.baseUrl === '/local_node')
)

// 远程节点 = 所有非 /local_node 的节点
const remoteNodes = computed(() =>
  nodesStore.nodes.filter((n) => n.baseUrl !== '/local_node')
)

const hasRemoteNodes = computed(() => remoteNodes.value.length > 0)

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
  toast.success('已登出')
}

async function onDelete(node) {
  const ok = await confirm(`确定删除节点「${node.name}」？该节点的本地凭证将被清除。`, {
    title: '提示',
    type: 'danger'
  })
  if (!ok) return
  nodesStore.removeNode(node.id)
  toast.success('已删除')
}

// 跳转到该节点的管理页面（带 ?nodeId=）
function onManage(node) {
  router.push({ path: '/admin/scan', query: { nodeId: node.id } })
}

// 进入页面时再同步一次本地节点状态（确保最新）
onMounted(() => {
  pluginsStore.syncLocalNode(nodesStore)
})
</script>

<template>
  <div class="flex flex-col gap-6">
    <div class="flex items-center justify-between">
      <h2 class="text-2xl font-bold tracking-tight text-gold-gradient">节点管理</h2>
      <Button @click="openAddRemote">
        <Plus class="h-4 w-4" />
        添加远程节点
      </Button>
    </div>

    <!-- 本地节点卡片（置顶） -->
    <div class="rounded-lg border border-primary/30 bg-card shadow-sm overflow-hidden">
      <div class="flex items-center gap-3 border-b border-border bg-primary/5 px-4 py-2.5">
        <HardDrive class="h-4 w-4 text-primary" />
        <span class="text-sm font-medium text-foreground">本机节点</span>
        <span class="text-xs text-muted-foreground">由 local_node 插件提供，插件启用即自动连接</span>
      </div>

      <!-- 加载中 -->
      <div v-if="!localNode" class="flex items-center gap-2 px-4 py-6 text-muted-foreground">
        <Loader2 class="h-4 w-4 animate-spin" />
        正在获取本地节点状态...
      </div>

      <!-- 插件未安装/未启用 -->
      <div v-else-if="!localNode?.available" class="px-4 py-6">
        <div class="flex items-center gap-2 text-muted-foreground mb-2">
          <Server class="h-5 w-5" />
          <span class="font-medium text-foreground">本地节点不可用</span>
        </div>
        <p class="text-sm text-muted-foreground">
          {{ localNode?.message || '请前往插件管理启用 local_node 插件' }}
        </p>
        <Button variant="secondary" size="sm" class="mt-3" @click="$router.push('/plugins')">
          前往插件管理
        </Button>
      </div>

      <!-- 本地节点已连接（自动） -->
      <div v-else class="flex items-center justify-between gap-4 px-4 py-4">
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
            v-if="localNodeRecord && localNodeRecord.userInfo?.is_admin"
            variant="ghost"
            size="sm"
            @click="onManage(localNodeRecord)"
          >
            <Settings class="h-4 w-4" />
            管理
          </Button>
        </div>
      </div>
    </div>

    <!-- 远程节点列表 -->
    <div class="flex flex-col gap-3">
      <div class="flex items-center gap-2">
        <Server class="h-4 w-4 text-muted-foreground" />
        <span class="text-sm font-medium text-muted-foreground">远程节点</span>
      </div>

      <Alert v-if="!hasRemoteNodes" class="border-border">
        <AlertDescription class="text-muted-foreground">
          尚未配置远程节点。点击右上角『添加远程节点』连接其他主机。
        </AlertDescription>
      </Alert>

      <div v-if="hasRemoteNodes" class="rounded-lg border bg-card shadow-sm">
        <Table>
          <TableHeader>
            <TableRow class="hover:bg-transparent">
              <TableHead>名称</TableHead>
              <TableHead>Base URL</TableHead>
              <TableHead class="w-[120px]">用户名</TableHead>
              <TableHead class="w-[120px]">登录状态</TableHead>
              <TableHead class="w-[320px]">操作</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            <TableRow v-for="row in remoteNodes" :key="row.id">
              <TableCell class="font-medium text-foreground">{{ row.name }}</TableCell>
              <TableCell class="text-muted-foreground">{{ row.baseUrl }}</TableCell>
              <TableCell class="text-muted-foreground">{{ row.username }}</TableCell>
              <TableCell>
                <Badge v-if="row.token" variant="success">已登录</Badge>
                <Badge v-else variant="secondary">未登录</Badge>
              </TableCell>
              <TableCell>
                <div class="flex flex-wrap items-center gap-1">
                  <Button
                    v-if="!row.token"
                    variant="ghost"
                    size="sm"
                    :disabled="loggingId === row.id"
                    @click="onLogin(row)"
                  >
                    <Loader2 v-if="loggingId === row.id" class="h-4 w-4 animate-spin" />
                    登录
                  </Button>
                  <Button
                    v-if="row.token && row.userInfo?.is_admin"
                    variant="ghost"
                    size="sm"
                    @click="onManage(row)"
                  >
                    <Settings class="h-4 w-4" />
                    管理
                  </Button>
                  <Button v-if="row.token" variant="ghost" size="sm" @click="onLogout(row)">
                    登出
                  </Button>
                  <Button variant="ghost" size="sm" @click="openEdit(row)">编辑</Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    class="text-destructive hover:text-destructive"
                    @click="onDelete(row)"
                  >
                    删除
                  </Button>
                </div>
              </TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </div>
    </div>

    <NodeForm v-model:visible="formVisible" :node="editingNode" :preset="presetNode" @saved="onSaved" />
  </div>
</template>
