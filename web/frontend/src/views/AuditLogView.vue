<script setup>
import { ref, onMounted, computed } from 'vue'
import { useToast } from '@/components/ui/toast/use-toast'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '@/components/ui/select'
import {
  Table, TableHeader, TableBody, TableRow, TableHead, TableCell
} from '@/components/ui/table'
import { Pagination } from '@/components/ui/pagination'
import { RefreshCw, Loader2, Search } from 'lucide-vue-next'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { useTargetNode } from '../composables/use-target-node'
import { getAuditLogs } from '../api/node'

const { targetNode, nodeMissing, nodeMissingMessage } = useTargetNode()
const toast = useToast()

const logs = ref([])
const loading = ref(false)
const page = ref(1)
const total = ref(0)
const size = ref(50)
const filterAction = ref('')
const filterUsername = ref('')
const filterTargetType = ref('')

const actionLabels = {
  scan: '扫描',
  upload: '上传',
  user_create: '创建用户',
  user_update: '更新用户',
  user_delete: '删除用户',
  watch_dir_create: '创建监控目录',
  watch_dir_update: '更新监控目录',
  watch_dir_delete: '删除监控目录',
}

const totalPages = computed(() => Math.ceil(total.value / size.value) || 1)

async function loadLogs() {
  const node = targetNode.value
  if (!node || !node.token) return
  loading.value = true
  try {
    const params = { page: page.value, size: size.value }
    if (filterAction.value) params.action = filterAction.value
    if (filterUsername.value) params.username = filterUsername.value
    if (filterTargetType.value) params.target_type = filterTargetType.value
    const data = await getAuditLogs(node, params)
    logs.value = data.items || []
    total.value = data.total || 0
  } catch (e) {
    toast.error('加载审计日志失败', e.message || String(e), e)
  } finally {
    loading.value = false
  }
}

function formatTime(iso) {
  if (!iso) return '—'
  const d = new Date(iso)
  return d.toLocaleString('zh-CN', { hour12: false })
}

function formatDetail(detail) {
  if (!detail) return '—'
  try {
    return JSON.stringify(detail, null, 2)
  } catch {
    return String(detail)
  }
}

function onPageChange(p) {
  page.value = p
  loadLogs()
}

onMounted(() => loadLogs())
</script>

<template>
  <div class="space-y-5">
    <Alert v-if="nodeMissing" variant="destructive" class="mb-4">
      <AlertDescription>{{ nodeMissingMessage }}</AlertDescription>
    </Alert>
    <div class="flex items-center justify-between">
      <h2 class="text-xl font-bold text-foreground">审计日志</h2>
      <Button variant="outline" size="sm" :disabled="loading" @click="loadLogs">
        <RefreshCw v-if="!loading" class="mr-2 h-4 w-4" />
        <Loader2 v-else class="mr-2 h-4 w-4 animate-spin" />
        刷新
      </Button>
    </div>

    <!-- 过滤器 -->
    <div class="flex items-center gap-3">
      <Select v-model="filterAction" @update:model-value="() => { page = 1; loadLogs() }">
        <SelectTrigger class="w-36">
          <SelectValue placeholder="全部操作" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="">全部操作</SelectItem>
          <SelectItem v-for="(label, key) in actionLabels" :key="key" :value="key">{{ label }}</SelectItem>
        </SelectContent>
      </Select>
      <Select v-model="filterTargetType" @update:model-value="() => { page = 1; loadLogs() }">
        <SelectTrigger class="w-36">
          <SelectValue placeholder="全部目标" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="">全部目标</SelectItem>
          <SelectItem value="user">用户</SelectItem>
          <SelectItem value="watch_dir">监控目录</SelectItem>
          <SelectItem value="file">文件</SelectItem>
        </SelectContent>
      </Select>
      <div class="relative w-40">
        <Search class="pointer-events-none absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
        <Input v-model="filterUsername" placeholder="按用户名过滤" class="h-9 pl-8" @keyup.enter="() => { page = 1; loadLogs() }" />
      </div>
    </div>

    <!-- 日志表格 -->
    <div class="rounded-lg border border-border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead class="w-16">#</TableHead>
            <TableHead class="w-40">时间</TableHead>
            <TableHead>用户</TableHead>
            <TableHead class="w-28">操作</TableHead>
            <TableHead>目标</TableHead>
            <TableHead>详情</TableHead>
            <TableHead class="w-20">IP</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          <TableRow v-for="log in logs" :key="log.id">
            <TableCell class="font-mono text-xs">{{ log.id }}</TableCell>
            <TableCell class="text-xs text-muted-foreground">{{ formatTime(log.timestamp) }}</TableCell>
            <TableCell class="text-sm">{{ log.username || '—' }}</TableCell>
            <TableCell>
              <Badge variant="outline" class="bg-primary/10 text-primary border-primary/20">
                {{ actionLabels[log.action] || log.action }}
              </Badge>
            </TableCell>
            <TableCell class="text-xs">
              <span v-if="log.target_type">{{ log.target_type }}#{{ log.target_id ?? '—' }}</span>
              <span v-else class="text-muted-foreground">—</span>
            </TableCell>
            <TableCell class="max-w-md">
              <pre v-if="log.detail" class="overflow-auto whitespace-pre-wrap break-all text-xs text-muted-foreground max-h-20">{{ formatDetail(log.detail) }}</pre>
              <span v-else class="text-muted-foreground">—</span>
            </TableCell>
            <TableCell class="text-xs text-muted-foreground">{{ log.client_ip || '—' }}</TableCell>
          </TableRow>
          <TableRow v-if="logs.length === 0">
            <TableCell :colspan="7" class="py-12 text-center text-sm text-muted-foreground">
              {{ loading ? '加载中...' : '暂无审计日志' }}
            </TableCell>
          </TableRow>
        </TableBody>
      </Table>
    </div>

    <!-- 分页 -->
    <div v-if="total > size" class="flex justify-center">
      <Pagination :total="totalPages" :page="page" @change="onPageChange" />
    </div>
  </div>
</template>
