<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useNodesStore } from '../stores/nodes'
import { useAuthStore } from '../stores/auth'
import {
  getPlaylists,
  createPlaylist,
  updatePlaylist,
  deletePlaylist,
  getPlaylistDetail,
  getTracks,
  addTracksToPlaylist,
  removeTracksFromPlaylist
} from '../api/node'
import {
  listClientPlaylists,
  createClientPlaylist,
  updateClientPlaylist,
  deleteClientPlaylist,
  listClientPlaylistItems,
  addClientPlaylistItems,
  removeClientPlaylistItems
} from '../api/client_playlist'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import {
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem
} from '@/components/ui/select'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter
} from '@/components/ui/dialog'
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell
} from '@/components/ui/table'
import { Empty } from '@/components/ui/empty'
import { useToast } from '@/components/ui/toast/use-toast'
import { useConfirm } from '@/composables/use-confirm'
import { Plus, RefreshCw, Loader2 } from 'lucide-vue-next'

const nodesStore = useNodesStore()
const authStore = useAuthStore()
const toast = useToast()
const { confirm } = useConfirm()

// 当前管理范围：'client' = 本机客户端播放列表，'remote-<id>' = 节点播放列表
const selectedScope = ref('client')

const playlists = ref([])
const loading = ref(false)

// 当前选中的播放列表详情
const currentPlaylist = ref(null)
const detailTracks = ref([])
const detailLoading = ref(false)

// 创建/编辑对话框
const dialogVisible = ref(false)
const editing = ref(null)
const form = ref({ name: '', description: '' })

// 从曲库添加曲目对话框
const addDialogVisible = ref(false)
const candidateTracks = ref([])
const selectedCandidate = ref([])
const candidateLoading = ref(false)

// 当前选中详情中的曲目
const selectedDetailTracks = ref([])

const isClientScope = computed(() => selectedScope.value === 'client')

const scopeOptions = computed(() => {
  const opts = [{ value: 'client', label: '本机（客户端）' }]
  nodesStore.loggedInNodes.forEach((n) => {
    opts.push({ value: n.id, label: n.name })
  })
  return opts
})

const currentNode = computed(() => {
  if (isClientScope.value) return null
  return nodesStore.getNode(selectedScope.value)
})

const isAdmin = computed(() => authStore.isAdmin)

async function loadPlaylists() {
  loading.value = true
  try {
    if (isClientScope.value) {
      const data = await listClientPlaylists()
      playlists.value = Array.isArray(data) ? data : data.items || []
    } else {
      const node = currentNode.value
      if (!node) {
        playlists.value = []
        return
      }
      const data = await getPlaylists(node)
      playlists.value = Array.isArray(data) ? data : data.items || []
    }
  } catch (e) {
    toast.error('获取播放列表失败', e?.response?.data?.detail || e.message || e, e)
    playlists.value = []
  } finally {
    loading.value = false
  }
}

async function viewDetail(pl) {
  currentPlaylist.value = pl
  await loadDetail()
}

async function loadDetail() {
  if (!currentPlaylist.value) return
  detailLoading.value = true
  try {
    if (isClientScope.value) {
      const items = await listClientPlaylistItems(currentPlaylist.value.id)
      detailTracks.value = items.map((it) => ({
        id: it.id,
        track_id: it.track_id,
        title: it.title,
        artist: it.artist,
        album: it.album,
        duration: it.duration,
        __clientItemId: it.id
      }))
    } else {
      const node = currentNode.value
      if (!node) {
        detailTracks.value = []
        return
      }
      const data = await getPlaylistDetail(node, currentPlaylist.value.id)
      const items = data.items || []
      detailTracks.value = items.map((it) => it.track || it).filter(Boolean)
    }
  } catch (e) {
    toast.error('获取曲目失败', e?.response?.data?.detail || e.message || e, e)
    detailTracks.value = []
  } finally {
    detailLoading.value = false
  }
}

function openCreate() {
  editing.value = null
  form.value = { name: '', description: '' }
  dialogVisible.value = true
}

function openEdit(pl) {
  editing.value = pl
  form.value = { name: pl.name, description: pl.description || '' }
  dialogVisible.value = true
}

async function onSave() {
  if (!form.value.name) {
    toast.warning('请输入名称')
    return
  }
  try {
    if (isClientScope.value) {
      if (editing.value) {
        await updateClientPlaylist(editing.value.id, form.value)
        toast.success('已更新')
      } else {
        await createClientPlaylist(form.value.name, form.value.description)
        toast.success('已创建')
      }
    } else {
      const node = currentNode.value
      if (!node) {
        toast.error('节点未连接')
        return
      }
      if (editing.value) {
        await updatePlaylist(node, editing.value.id, form.value)
        toast.success('已更新')
      } else {
        await createPlaylist(node, form.value)
        toast.success('已创建')
      }
    }
    dialogVisible.value = false
    await loadPlaylists()
  } catch (e) {
    toast.error('保存失败', e?.response?.data?.detail || e.message, e)
  }
}

async function onDelete(pl) {
  if (pl.is_system) {
    toast.warning('系统列表不可删除')
    return
  }
  const ok = await confirm(`确定删除播放列表「${pl.name}」？`, {
    title: '提示',
    type: 'warning'
  })
  if (!ok) return
  try {
    if (isClientScope.value) {
      await deleteClientPlaylist(pl.id)
    } else {
      const node = currentNode.value
      if (!node) {
        toast.error('节点未连接')
        return
      }
      await deletePlaylist(node, pl.id)
    }
    toast.success('已删除')
    if (currentPlaylist.value?.id === pl.id) {
      currentPlaylist.value = null
      detailTracks.value = []
    }
    await loadPlaylists()
  } catch (e) {
    toast.error('删除失败', e?.response?.data?.detail || e.message, e)
  }
}

function onDetailSelectionChange(rows) {
  selectedDetailTracks.value = rows
}

async function removeFromPlaylist() {
  if (selectedDetailTracks.value.length === 0) {
    toast.warning('请先选择要移除的曲目')
    return
  }
  const ok = await confirm(
    `从播放列表移除 ${selectedDetailTracks.value.length} 首曲目？`,
    { title: '提示', type: 'warning' }
  )
  if (!ok) return
  try {
    if (isClientScope.value) {
      const itemIds = selectedDetailTracks.value.map((t) => t.__clientItemId || t.id)
      await removeClientPlaylistItems(currentPlaylist.value.id, itemIds)
    } else {
      const node = currentNode.value
      if (!node) {
        toast.error('节点未连接')
        return
      }
      await removeTracksFromPlaylist(
        node,
        currentPlaylist.value.id,
        selectedDetailTracks.value.map((t) => t.id)
      )
    }
    toast.success('已移除')
    await loadDetail()
  } catch (e) {
    toast.error('移除失败', e?.response?.data?.detail || e.message || e, e)
  }
}

async function openAddDialog() {
  if (!currentPlaylist.value) {
    toast.warning('请先选择播放列表')
    return
  }
  selectedCandidate.value = []
  addDialogVisible.value = true
  candidateLoading.value = true
  try {
    if (isClientScope.value) {
      // 客户端播放列表：聚合所有已登录节点的曲目
      const loggedIn = nodesStore.loggedInNodes
      const results = await Promise.allSettled(
        loggedIn.map(async (n) => {
          const data = await getTracks(n, { page: 1, page_size: 200 })
          const items = data.items || data.tracks || []
          return items.map((t) => ({
            ...t,
            __nodeId: n.id,
            __nodeName: n.name
          }))
        })
      )
      const merged = []
      results.forEach((r) => {
        if (r.status === 'fulfilled') merged.push(...r.value)
      })
      candidateTracks.value = merged
    } else {
      const node = currentNode.value
      if (!node) {
        candidateTracks.value = []
        return
      }
      const data = await getTracks(node, { page: 1, page_size: 100 })
      candidateTracks.value = data.items || data.tracks || []
    }
  } catch (e) {
    toast.error('加载曲库失败', e?.response?.data?.detail || e.message || e, e)
    candidateTracks.value = []
  } finally {
    candidateLoading.value = false
  }
}

async function addCandidates() {
  if (selectedCandidate.value.length === 0) {
    toast.warning('请选择要添加的曲目')
    return
  }
  try {
    if (isClientScope.value) {
      const items = selectedCandidate.value.map((t) => ({
        track_id: t.id,
        node_id: t.__nodeId,
        title: t.title,
        artist: t.artist,
        album: t.album,
        duration: t.duration
      }))
      await addClientPlaylistItems(currentPlaylist.value.id, items)
    } else {
      const node = currentNode.value
      if (!node) {
        toast.error('节点未连接')
        return
      }
      await addTracksToPlaylist(
        node,
        currentPlaylist.value.id,
        selectedCandidate.value.map((t) => t.id)
      )
    }
    toast.success(`已添加 ${selectedCandidate.value.length} 首`)
    addDialogVisible.value = false
    await loadDetail()
  } catch (e) {
    toast.error('添加失败', e?.response?.data?.detail || e.message, e)
  }
}

// ---- 手动多选辅助 ----
function isSelectedIn(track, list) {
  return list.some((t) => (t.__clientItemId || t.id) === (track.__clientItemId || track.id))
}
function allSelectedIn(rows, list) {
  return rows.length > 0 && rows.every((t) => isSelectedIn(t, list))
}
function toggleDetailTrack(track) {
  const next = isSelectedIn(track, selectedDetailTracks.value)
    ? selectedDetailTracks.value.filter((t) => (t.__clientItemId || t.id) !== (track.__clientItemId || track.id))
    : [...selectedDetailTracks.value, track]
  onDetailSelectionChange(next)
}
function toggleDetailAll() {
  onDetailSelectionChange(
    allSelectedIn(detailTracks.value, selectedDetailTracks.value)
      ? []
      : detailTracks.value.slice()
  )
}
function toggleCandidateTrack(track) {
  selectedCandidate.value = isSelectedIn(track, selectedCandidate.value)
    ? selectedCandidate.value.filter((t) => t.id !== track.id)
    : [...selectedCandidate.value, track]
}
function toggleCandidateAll() {
  selectedCandidate.value = allSelectedIn(
    candidateTracks.value,
    selectedCandidate.value
  )
    ? []
    : candidateTracks.value.slice()
}

// 切换范围时重新加载
watch(selectedScope, () => {
  currentPlaylist.value = null
  detailTracks.value = []
  loadPlaylists()
})

onMounted(() => {
  loadPlaylists()
})
</script>

<template>
  <div class="flex flex-col gap-6">
    <div class="flex items-center justify-between">
      <h2 class="text-2xl font-bold tracking-tight text-gold-gradient">
        播放列表管理
      </h2>
      <div class="flex items-center gap-2">
        <Select v-model="selectedScope">
          <SelectTrigger class="w-[200px]">
            <SelectValue placeholder="选择范围" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem v-for="opt in scopeOptions" :key="opt.value" :value="opt.value">
              {{ opt.label }}
            </SelectItem>
          </SelectContent>
        </Select>
        <Button @click="openCreate">
          <Plus class="h-4 w-4" />
          新建播放列表
        </Button>
        <Button variant="secondary" @click="loadPlaylists">
          <RefreshCw class="h-4 w-4" />
          刷新
        </Button>
      </div>
    </div>

    <div class="grid grid-cols-1 gap-4 lg:grid-cols-3">
      <!-- 左：播放列表 -->
      <Card class="lg:col-span-1">
        <CardHeader>
          <CardTitle class="text-base">
            {{ isClientScope ? '本机播放列表' : '节点播放列表' }}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow class="hover:bg-transparent">
                <TableHead>名称</TableHead>
                <TableHead class="w-[80px]">类型</TableHead>
                <TableHead class="w-[120px]">操作</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              <TableRow v-if="loading">
                <TableCell :colspan="3" class="py-8 text-center text-muted-foreground">
                  <Loader2 class="mx-auto mb-2 h-5 w-5 animate-spin" />
                  加载中...
                </TableCell>
              </TableRow>
              <TableRow
                v-for="pl in playlists"
                v-else
                :key="pl.id"
                class="cursor-pointer"
                @click="viewDetail(pl)"
              >
                <TableCell class="font-medium text-foreground">{{ pl.name }}</TableCell>
                <TableCell>
                  <Badge v-if="pl.is_system" variant="default">系统</Badge>
                  <Badge v-else variant="secondary">自定义</Badge>
                </TableCell>
                <TableCell>
                  <div class="flex items-center gap-1">
                    <Button
                      variant="ghost"
                      size="sm"
                      :disabled="pl.is_system"
                      @click.stop="openEdit(pl)"
                    >
                      编辑
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      class="text-destructive hover:text-destructive"
                      :disabled="pl.is_system"
                      @click.stop="onDelete(pl)"
                    >
                      删除
                    </Button>
                  </div>
                </TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <!-- 右：详情 -->
      <Card class="lg:col-span-2">
        <CardHeader>
          <div class="flex items-center justify-between">
            <CardTitle class="text-base">
              曲目详情
              <span
                v-if="currentPlaylist"
                class="ml-2 text-xs font-normal text-muted-foreground"
              >
                {{ currentPlaylist.name }}
              </span>
            </CardTitle>
            <div v-if="currentPlaylist" class="flex items-center gap-2">
              <Button variant="secondary" size="sm" @click="openAddDialog">
                从曲库添加
              </Button>
              <Button
                variant="destructive"
                size="sm"
                :disabled="selectedDetailTracks.length === 0"
                @click="removeFromPlaylist"
              >
                批量移除
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <Empty
            v-if="!currentPlaylist"
            description="请选择左侧的播放列表"
          />
          <Table v-else>
            <TableHeader>
              <TableRow class="hover:bg-transparent">
                <TableHead class="w-[44px]">
                  <input
                    type="checkbox"
                    class="h-4 w-4 rounded border-input accent-primary"
                    :checked="
                      allSelectedIn(detailTracks, selectedDetailTracks)
                    "
                    @change="toggleDetailAll"
                  />
                </TableHead>
                <TableHead class="w-[50px]">#</TableHead>
                <TableHead>标题</TableHead>
                <TableHead>艺术家</TableHead>
                <TableHead>专辑</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              <TableRow v-if="detailLoading">
                <TableCell :colspan="5" class="py-8 text-center text-muted-foreground">
                  <Loader2 class="mx-auto mb-2 h-5 w-5 animate-spin" />
                  加载中...
                </TableCell>
              </TableRow>
              <template v-else>
                <TableRow v-for="(t, i) in detailTracks" :key="t.__clientItemId || t.id">
                  <TableCell>
                    <input
                      type="checkbox"
                      class="h-4 w-4 rounded border-input accent-primary"
                      :checked="isSelectedIn(t, selectedDetailTracks)"
                      @change="toggleDetailTrack(t)"
                    />
                  </TableCell>
                  <TableCell class="text-muted-foreground">{{ i + 1 }}</TableCell>
                  <TableCell class="font-medium text-foreground">{{ t.title }}</TableCell>
                  <TableCell class="text-muted-foreground">{{ t.artist }}</TableCell>
                  <TableCell class="text-muted-foreground">{{ t.album }}</TableCell>
                </TableRow>
              </template>
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>

    <!-- 新建/编辑 -->
    <Dialog :open="dialogVisible" @update:open="(v) => (dialogVisible = v)">
      <DialogContent class="max-w-md">
        <DialogHeader>
          <DialogTitle>{{ editing ? '编辑播放列表' : '新建播放列表' }}</DialogTitle>
          <DialogDescription>
            {{ editing ? '修改播放列表信息' : '创建一个新的播放列表' }}
          </DialogDescription>
        </DialogHeader>
        <div class="space-y-4">
          <div class="space-y-2">
            <Label for="pl-name">名称</Label>
            <Input id="pl-name" v-model="form.name" class="bg-secondary/60" />
          </div>
          <div class="space-y-2">
            <Label for="pl-desc">描述</Label>
            <textarea
              id="pl-desc"
              v-model="form.description"
              class="flex min-h-[80px] w-full rounded-md border border-input bg-secondary/60 px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
            />
          </div>
        </div>
        <DialogFooter class="gap-2">
          <Button variant="ghost" @click="dialogVisible = false">取消</Button>
          <Button @click="onSave">保存</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>

    <!-- 从曲库添加 -->
    <Dialog :open="addDialogVisible" @update:open="(v) => (addDialogVisible = v)">
      <DialogContent class="max-w-2xl">
        <DialogHeader>
          <DialogTitle>从曲库添加曲目</DialogTitle>
          <DialogDescription>
            选择要添加到当前播放列表的曲目
          </DialogDescription>
        </DialogHeader>
        <div class="max-h-[400px] overflow-auto rounded-md border">
          <Table>
            <TableHeader class="sticky top-0 bg-card">
              <TableRow class="hover:bg-transparent">
                <TableHead class="w-[44px]">
                  <input
                    type="checkbox"
                    class="h-4 w-4 rounded border-input accent-primary"
                    :checked="
                      allSelectedIn(candidateTracks, selectedCandidate)
                    "
                    @change="toggleCandidateAll"
                  />
                </TableHead>
                <TableHead>标题</TableHead>
                <TableHead>艺术家</TableHead>
                <TableHead>专辑</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              <TableRow v-if="candidateLoading">
                <TableCell :colspan="4" class="py-8 text-center text-muted-foreground">
                  <Loader2 class="mx-auto mb-2 h-5 w-5 animate-spin" />
                  加载中...
                </TableCell>
              </TableRow>
              <template v-else>
                <TableRow v-for="t in candidateTracks" :key="t.id">
                  <TableCell>
                    <input
                      type="checkbox"
                      class="h-4 w-4 rounded border-input accent-primary"
                      :checked="isSelectedIn(t, selectedCandidate)"
                      @change="toggleCandidateTrack(t)"
                    />
                  </TableCell>
                  <TableCell class="font-medium text-foreground">{{ t.title }}</TableCell>
                  <TableCell class="text-muted-foreground">{{ t.artist }}</TableCell>
                  <TableCell class="text-muted-foreground">{{ t.album }}</TableCell>
                </TableRow>
              </template>
            </TableBody>
          </Table>
        </div>
        <DialogFooter class="gap-2">
          <Button variant="ghost" @click="addDialogVisible = false">取消</Button>
          <Button variant="gold" :disabled="selectedCandidate.length === 0" @click="addCandidates">
            添加 {{ selectedCandidate.length }} 首
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  </div>
</template>
