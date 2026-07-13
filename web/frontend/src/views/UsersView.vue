<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useToast } from '@/components/ui/toast/use-toast'
import { useConfirm } from '@/composables/use-confirm'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter
} from '@/components/ui/dialog'
import { Switch } from '@/components/ui/switch'
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell
} from '@/components/ui/table'
import {
  Loader2,
  RefreshCw,
  Plus,
  Pencil,
  Trash2,
  Shield,
  Eye,
  EyeOff,
  Inbox
} from 'lucide-vue-next'
import { useTargetNode } from '../composables/use-target-node'
import { Alert, AlertDescription } from '@/components/ui/alert'
import {
  getUsers,
  createUser,
  updateUser,
  deleteUser
} from '../api/node'

const { targetNode, nodeMissing, nodeMissingMessage } = useTargetNode()
const toast = useToast()
const { confirm } = useConfirm()

const users = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const editing = ref(null)
const showPassword = ref(false)

const form = reactive({
  username: '',
  password: '',
  is_admin: false
})

async function loadUsers() {
  const node = targetNode.value
  if (!node) return
  loading.value = true
  try {
    const data = await getUsers(node)
    users.value = Array.isArray(data) ? data : data.items || []
  } catch (e) {
    toast.error('获取用户列表失败', e.message || String(e), e)
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editing.value = null
  form.username = ''
  form.password = ''
  form.is_admin = false
  showPassword.value = false
  dialogVisible.value = true
}

function openEdit(row) {
  editing.value = row
  form.username = row.username
  form.password = '' // 编辑时不预填密码
  form.is_admin = !!row.is_admin
  showPassword.value = false
  dialogVisible.value = true
}

async function onSave() {
  if (!form.username) {
    toast.warning('请输入用户名')
    return
  }
  if (!editing.value && !form.password) {
    toast.warning('请输入密码')
    return
  }
  const node = targetNode.value
  try {
    if (editing.value) {
      const payload = { username: form.username, is_admin: form.is_admin }
      if (form.password) payload.password = form.password
      await updateUser(node, editing.value.id, payload)
      toast.success('已更新')
    } else {
      await createUser(node, {
        username: form.username,
        password: form.password,
        is_admin: form.is_admin
      })
      toast.success('已创建')
    }
    dialogVisible.value = false
    await loadUsers()
  } catch (e) {
    toast.error('保存失败', e.response?.data?.detail || e.message, e)
  }
}

async function onDelete(row) {
  const ok = await confirm(`确定删除用户「${row.username}」？`, {
    title: '删除用户',
    type: 'danger'
  })
  if (!ok) return
  const node = targetNode.value
  try {
    await deleteUser(node, row.id)
    toast.success('已删除')
    await loadUsers()
  } catch (e) {
    toast.error('删除失败', e.response?.data?.detail || e.message, e)
  }
}

onMounted(() => {
  loadUsers()
})
</script>

<template>
  <div class="space-y-6">
    <Alert v-if="nodeMissing" variant="destructive" class="mb-4">
      <AlertDescription>{{ nodeMissingMessage }}</AlertDescription>
    </Alert>
    <div class="flex items-center justify-between">
      <h2 class="text-2xl font-bold tracking-tight">用户管理</h2>
      <div class="flex gap-2">
        <Button variant="secondary" :disabled="loading" @click="loadUsers">
          <Loader2 v-if="loading" class="h-4 w-4 animate-spin" />
          <RefreshCw v-else class="h-4 w-4" />
          刷新
        </Button>
        <Button @click="openCreate">
          <Plus class="h-4 w-4" />
          新建用户
        </Button>
      </div>
    </div>

    <Card>
      <CardContent class="pt-6">
        <div class="relative rounded-md border border-border">
          <Table>
            <TableHeader>
              <TableRow class="hover:bg-transparent">
                <TableHead class="w-12">#</TableHead>
                <TableHead class="min-w-[160px]">用户名</TableHead>
                <TableHead class="w-32">角色</TableHead>
                <TableHead class="min-w-[160px]">创建时间</TableHead>
                <TableHead class="w-40 text-right">操作</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              <TableRow v-for="(row, i) in users" :key="row.id">
                <TableCell class="text-muted-foreground">{{ i + 1 }}</TableCell>
                <TableCell class="font-medium text-foreground">{{ row.username }}</TableCell>
                <TableCell>
                  <Badge :variant="row.is_admin ? 'default' : 'secondary'">
                    <Shield v-if="row.is_admin" class="mr-1 h-3 w-3" />
                    {{ row.is_admin ? '管理员' : '普通用户' }}
                  </Badge>
                </TableCell>
                <TableCell class="text-muted-foreground">{{ row.created_at || '—' }}</TableCell>
                <TableCell>
                  <div class="flex justify-end gap-1">
                    <Button variant="ghost" size="sm" @click="openEdit(row)">
                      <Pencil class="h-3.5 w-3.5" />
                      编辑
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      class="text-destructive hover:text-destructive"
                      @click="onDelete(row)"
                    >
                      <Trash2 class="h-3.5 w-3.5" />
                      删除
                    </Button>
                  </div>
                </TableCell>
              </TableRow>
              <TableRow v-if="users.length === 0 && !loading" class="hover:bg-transparent">
                <TableCell colspan="5">
                  <div class="flex flex-col items-center justify-center py-10 text-muted-foreground">
                    <Inbox class="h-10 w-10 mb-2 opacity-50" />
                    <span class="text-sm">暂无用户</span>
                  </div>
                </TableCell>
              </TableRow>
            </TableBody>
          </Table>
          <div
            v-if="loading"
            class="absolute inset-0 flex items-center justify-center rounded-md bg-background/60 backdrop-blur-sm"
          >
            <Loader2 class="h-5 w-5 animate-spin text-primary" />
          </div>
        </div>
      </CardContent>
    </Card>

    <!-- 新建/编辑用户对话框 -->
    <Dialog :open="dialogVisible" @update:open="(v) => (dialogVisible = v)">
      <DialogContent class="max-w-md">
        <DialogHeader>
          <DialogTitle>{{ editing ? '编辑用户' : '新建用户' }}</DialogTitle>
          <DialogDescription>
            {{ editing ? '修改用户信息，密码留空则不修改' : '创建一个新用户账号' }}
          </DialogDescription>
        </DialogHeader>

        <div class="space-y-4">
          <div class="space-y-2">
            <Label for="user-username">用户名</Label>
            <Input id="user-username" v-model="form.username" placeholder="请输入用户名" />
          </div>
          <div class="space-y-2">
            <Label for="user-password">{{ editing ? '新密码' : '密码' }}</Label>
            <div class="relative">
              <Input
                id="user-password"
                v-model="form.password"
                :type="showPassword ? 'text' : 'password'"
                :placeholder="editing ? '留空则不修改' : '请输入密码'"
                class="pr-10"
              />
              <button
                type="button"
                class="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground transition-colors hover:text-foreground"
                @click="showPassword = !showPassword"
              >
                <Eye v-if="!showPassword" class="h-4 w-4" />
                <EyeOff v-else class="h-4 w-4" />
              </button>
            </div>
          </div>
          <div class="flex items-center justify-between rounded-md border border-border p-3">
            <div class="flex flex-col gap-0.5">
              <Label for="user-admin" class="cursor-pointer">管理员</Label>
              <span class="text-xs text-muted-foreground">管理员可访问所有管理功能</span>
            </div>
            <Switch id="user-admin" v-model:checked="form.is_admin" />
          </div>
        </div>

        <DialogFooter class="gap-2">
          <Button variant="ghost" @click="dialogVisible = false">取消</Button>
          <Button variant="gold" @click="onSave">保存</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  </div>
</template>
