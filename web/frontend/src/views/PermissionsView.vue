<script setup>
import { ref, onMounted, watch } from 'vue'
import { useToast } from '@/components/ui/toast/use-toast'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem
} from '@/components/ui/select'
import { Empty } from '@/components/ui/empty'
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell
} from '@/components/ui/table'
import { Loader2, Network, ShieldCheck, ShieldOff, Shield, Inbox } from 'lucide-vue-next'
import { useAuthStore } from '../stores/auth'
import {
  getPlaylists,
  getUsers,
  getPermissions,
  grantPermission,
  revokePermission
} from '../api/node'

const authStore = useAuthStore()
const toast = useToast()

const playlists = ref([])
const users = ref([])
const selectedPlaylistId = ref(null)
const permissions = ref([]) // 当前播放列表已授权用户
const loading = ref(false)

async function loadPlaylists() {
  const node = authStore.localNode
  if (!node) return
  try {
    const data = await getPlaylists(node)
    playlists.value = Array.isArray(data) ? data : data.items || []
  } catch (e) {
    toast.error('获取播放列表失败', e.message || String(e), e)
  }
}

async function loadUsers() {
  const node = authStore.localNode
  if (!node) return
  try {
    const data = await getUsers(node)
    users.value = Array.isArray(data) ? data : data.items || []
  } catch (e) {
    toast.error('获取用户列表失败', e.message || String(e), e)
  }
}

async function loadPermissions() {
  if (!selectedPlaylistId.value) return
  const node = authStore.localNode
  loading.value = true
  try {
    // 后端 GET /api/permissions?playlist_id=，返回 PermissionOut 列表（含 id, user_id）
    const data = await getPermissions(node, { playlist_id: selectedPlaylistId.value })
    permissions.value = Array.isArray(data) ? data : data.items || []
  } catch (e) {
    permissions.value = []
  } finally {
    loading.value = false
  }
}

watch(selectedPlaylistId, () => {
  loadPermissions()
})

async function onGrant(userId) {
  const node = authStore.localNode
  try {
    await grantPermission(node, selectedPlaylistId.value, userId)
    toast.success('已授权')
    await loadPermissions()
  } catch (e) {
    toast.error('授权失败', e.response?.data?.detail || e.message, e)
  }
}

async function onRevoke(userId) {
  // 找到该用户对应的权限记录 id
  const perm = permissions.value.find((p) => p.user_id === userId)
  if (!perm) {
    toast.warning('未找到授权记录')
    return
  }
  const node = authStore.localNode
  try {
    await revokePermission(node, perm.id)
    toast.success('已撤销')
    await loadPermissions()
  } catch (e) {
    toast.error('撤销失败', e.response?.data?.detail || e.message, e)
  }
}

// 该用户是否已被授权访问当前播放列表
function isAuthorized(userId) {
  return permissions.value.some((p) => p.user_id === userId)
}

onMounted(() => {
  loadPlaylists()
  loadUsers()
})
</script>

<template>
  <div class="space-y-6">
    <div>
      <h2 class="text-2xl font-bold tracking-tight">播放列表授权管理</h2>
    </div>

    <!-- 顶部：选择播放列表 -->
    <Card>
      <CardContent class="pt-6">
        <div class="flex flex-col gap-1.5 w-72">
          <Label>播放列表</Label>
          <Select v-model="selectedPlaylistId">
            <SelectTrigger>
              <SelectValue placeholder="选择播放列表" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem
                v-for="p in playlists"
                :key="p.id"
                :value="p.id"
              >
                {{ p.name }}
              </SelectItem>
            </SelectContent>
          </Select>
        </div>
      </CardContent>
    </Card>

    <!-- 用户授权表 -->
    <Card>
      <CardHeader>
        <CardTitle class="flex items-center gap-2">
          <Network class="h-4 w-4 text-primary" />
          用户授权
          <span class="text-sm font-normal text-muted-foreground">
            （{{ permissions.length }} 已授权 / {{ users.length }} 总用户）
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <Empty
          v-if="!selectedPlaylistId"
          :icon="Inbox"
          title="请先选择播放列表"
          description="选择上方的播放列表后即可管理用户授权"
        />
        <div v-else class="relative rounded-md border border-border">
          <Table>
            <TableHeader>
              <TableRow class="hover:bg-transparent">
                <TableHead class="min-w-[160px]">用户名</TableHead>
                <TableHead class="w-28">角色</TableHead>
                <TableHead class="w-28">授权状态</TableHead>
                <TableHead class="w-32 text-right">操作</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              <TableRow v-for="row in users" :key="row.id">
                <TableCell class="font-medium text-foreground">{{ row.username }}</TableCell>
                <TableCell>
                  <Badge :variant="row.is_admin ? 'default' : 'secondary'">
                    <Shield
                      v-if="row.is_admin"
                      class="mr-1 h-3 w-3"
                    />
                    {{ row.is_admin ? '管理员' : '普通用户' }}
                  </Badge>
                </TableCell>
                <TableCell>
                  <Badge :variant="isAuthorized(row.id) ? 'success' : 'secondary'">
                    {{ isAuthorized(row.id) ? '已授权' : '未授权' }}
                  </Badge>
                </TableCell>
                <TableCell>
                  <div class="flex justify-end">
                    <Button
                      v-if="!isAuthorized(row.id)"
                      variant="ghost"
                      size="sm"
                      @click="onGrant(row.id)"
                    >
                      <ShieldCheck class="h-3.5 w-3.5" />
                      授权
                    </Button>
                    <Button
                      v-else
                      variant="ghost"
                      size="sm"
                      class="text-destructive hover:text-destructive"
                      @click="onRevoke(row.id)"
                    >
                      <ShieldOff class="h-3.5 w-3.5" />
                      撤销
                    </Button>
                  </div>
                </TableCell>
              </TableRow>
              <TableRow v-if="users.length === 0 && !loading" class="hover:bg-transparent">
                <TableCell colspan="4" class="text-center text-muted-foreground py-10">
                  暂无用户
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
  </div>
</template>
