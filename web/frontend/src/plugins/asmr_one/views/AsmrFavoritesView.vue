<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  ArrowLeft, Heart, Loader2, RefreshCw, ListMusic, Plus, Trash2, Folder
} from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Empty } from '@/components/ui/empty'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription
} from '@/components/ui/dialog'
import { useToast } from '@/components/ui/toast/use-toast'
import {
  listPlaylists, deletePlaylist, getPlaylistMetadata, getPlaylistWorks,
  createPlaylist, removeFromPlaylist, getDefaultPlaylist
} from '../api'
import { useAsmrAccountStore } from '../store'

const router = useRouter()
const toast = useToast()
const account = useAsmrAccountStore()

const playlists = ref([])
const defaultPlaylistId = ref(null)
const selectedId = ref(null)
const selectedDetail = ref(null)
const loading = ref(false)
const detailLoading = ref(false)

// 作品分页
const worksPage = ref(1)
const worksPageSize = ref(50)
const worksTotal = ref(0)
const worksTotalPage = ref(1)

// 创建对话框
const showCreate = ref(false)
const newName = ref('')
const newDesc = ref('')
const creating = ref(false)

async function load() {
  if (!account.isLoggedIn) {
    router.push('/asmr/account')
    return
  }
  loading.value = true
  try {
    const [list, dp] = await Promise.all([listPlaylists(1, 100), getDefaultPlaylist()])
    playlists.value = list.playlists || []
    defaultPlaylistId.value = dp?.id || null
    // 默认选中第一个（或默认收藏夹）
    if (playlists.value.length > 0) {
      const first = playlists.value.find(p => p.id === defaultPlaylistId.value) || playlists.value[0]
      await selectPlaylist(first.id)
    } else {
      selectedId.value = null
      selectedDetail.value = null
    }
  } catch (e) {
    toast.error('加载失败', e?.response?.data?.detail || e.message)
  } finally {
    loading.value = false
  }
}

async function selectPlaylist(id) {
  if (selectedId.value === id && selectedDetail.value) return
  selectedId.value = id
  selectedDetail.value = null
  worksPage.value = 1
  detailLoading.value = true
  try {
    // metadata 提供名称/描述（不含作品），works 接口提供实际作品列表
    const [meta, worksData] = await Promise.all([
      getPlaylistMetadata(id),
      getPlaylistWorks(id, worksPage.value, worksPageSize.value)
    ])
    selectedDetail.value = meta
    selectedDetail.value.works = worksData.works || []
    const pag = worksData.pagination || {}
    worksTotal.value = pag.totalCount || selectedDetail.value.works.length
    worksTotalPage.value = pag.totalPage || Math.ceil(worksTotal.value / worksPageSize.value) || 1
  } catch (e) {
    toast.error('加载播放列表失败', e?.response?.data?.detail || e.message)
  } finally {
    detailLoading.value = false
  }
}

async function changeWorksPage(p) {
  if (!selectedId.value || p < 1 || p > worksTotalPage.value) return
  worksPage.value = p
  detailLoading.value = true
  try {
    const worksData = await getPlaylistWorks(selectedId.value, worksPage.value, worksPageSize.value)
    if (selectedDetail.value) selectedDetail.value.works = worksData.works || []
    const pag = worksData.pagination || {}
    worksTotal.value = pag.totalCount || (selectedDetail.value?.works?.length || 0)
    worksTotalPage.value = pag.totalPage || Math.ceil(worksTotal.value / worksPageSize.value) || 1
  } catch (e) {
    toast.error('加载失败', e?.response?.data?.detail || e.message)
  } finally {
    detailLoading.value = false
  }
}

async function handleDeletePlaylist(pl) {
  if (!confirm(`确定要删除播放列表「${pl.name}」吗？此操作不可撤销。`)) return
  try {
    await deletePlaylist(pl.id)
    toast.success('已删除', `播放列表「${pl.name}」已删除`)
    if (selectedId.value === pl.id) {
      selectedId.value = null
      selectedDetail.value = null
    }
    await load()
  } catch (e) {
    toast.error('删除失败', e?.response?.data?.detail || e.message)
  }
}

async function handleCreate() {
  if (!newName.value.trim()) {
    toast.error('请输入名称')
    return
  }
  creating.value = true
  try {
    await createPlaylist(newName.value.trim(), 0, newDesc.value.trim())
    toast.success('已创建', `播放列表「${newName.value.trim()}」已创建`)
    showCreate.value = false
    newName.value = ''
    newDesc.value = ''
    await load()
  } catch (e) {
    toast.error('创建失败', e?.response?.data?.detail || e.message)
  } finally {
    creating.value = false
  }
}

async function handleRemoveWork(workId) {
  if (!selectedId.value) return
  try {
    await removeFromPlaylist(selectedId.value, [workId])
    // 从详情中移除
    if (selectedDetail.value?.works) {
      selectedDetail.value.works = selectedDetail.value.works.filter(w => w.id !== workId)
    }
    // 更新计数
    if (worksTotal.value > 0) worksTotal.value -= 1
    const pl = playlists.value.find(p => p.id === selectedId.value)
    if (pl && pl.works_count > 0) pl.works_count -= 1
    toast.success('已移除')
  } catch (e) {
    toast.error('移除失败', e?.response?.data?.detail || e.message)
  }
}

function openWork(id) {
  router.push(`/asmr/work/${id}`)
}

function isDefault(id) {
  return id === defaultPlaylistId.value
}

onMounted(() => {
  if (!account.loaded) account.load().then(load)
  else load()
})
</script>

<template>
  <div class="flex h-full flex-col gap-3">
    <!-- 顶栏 -->
    <div class="flex items-center justify-between shrink-0">
      <div class="flex items-center gap-3">
        <Button variant="ghost" size="sm" @click="router.push('/asmr')">
          <ArrowLeft class="h-4 w-4" />
          返回
        </Button>
        <h2 class="text-lg font-semibold">我的播放列表</h2>
        <Badge v-if="playlists.length" variant="outline" class="text-xs">
          {{ playlists.length }} 个
        </Badge>
      </div>
      <div class="flex gap-2">
        <Button variant="gold" size="sm" @click="showCreate = true">
          <Plus class="h-4 w-4" />
          新建
        </Button>
        <Button variant="ghost" size="sm" :disabled="loading" @click="load">
          <RefreshCw class="h-4 w-4" :class="{ 'animate-spin': loading }" />
          刷新
        </Button>
      </div>
    </div>

    <!-- 主体：左侧列表 + 右侧详情 -->
    <div class="flex-1 min-h-0 flex gap-3">
      <!-- 左侧：播放列表列表 -->
      <div class="w-64 shrink-0 flex flex-col gap-1 overflow-auto pr-1 border-r border-border">
        <div v-if="loading" class="flex items-center justify-center py-8 text-muted-foreground">
          <Loader2 class="mr-2 h-4 w-4 animate-spin" />
          加载中...
        </div>
        <Empty
          v-else-if="playlists.length === 0"
          :icon="Folder"
          title="还没有播放列表"
          description="点击右上角「新建」创建"
          class="py-8"
        />
        <button
          v-for="pl in playlists"
          :key="pl.id"
          class="group flex items-start gap-2 rounded-md border border-transparent px-3 py-2 text-left transition-colors hover:bg-accent/30"
          :class="{
            'border-primary bg-accent/40': selectedId === pl.id,
            'opacity-60': isDefault(pl.id)
          }"
          @click="selectPlaylist(pl.id)"
        >
          <ListMusic class="mt-0.5 h-4 w-4 shrink-0 text-primary" />
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-1">
              <span class="text-sm font-medium truncate">{{ pl.name }}</span>
              <Heart v-if="isDefault(pl.id)" class="h-3 w-3 text-primary shrink-0" />
            </div>
            <div class="text-[10px] text-muted-foreground">
              {{ pl.works_count || 0 }} 个作品
            </div>
          </div>
          <span
            v-if="!isDefault(pl.id)"
            class="opacity-0 group-hover:opacity-100 transition-opacity shrink-0"
            @click.stop="handleDeletePlaylist(pl)"
          >
            <Trash2 class="h-3.5 w-3.5 text-destructive hover:text-destructive/80" />
          </span>
        </button>
      </div>

      <!-- 右侧：选中播放列表的作品 -->
      <div class="flex-1 min-w-0 flex flex-col overflow-auto">
        <div v-if="!selectedId" class="flex items-center justify-center h-full text-muted-foreground text-sm">
          <Folder class="mr-2 h-5 w-5" />
          请从左侧选择一个播放列表
        </div>

        <div v-else-if="detailLoading" class="flex items-center justify-center py-12 text-muted-foreground">
          <Loader2 class="mr-2 h-5 w-5 animate-spin" />
          加载中...
        </div>

        <template v-else-if="selectedDetail">
          <!-- 播放列表信息 -->
          <div class="shrink-0 rounded-lg border border-border bg-card/40 p-3 mb-3 flex items-center gap-3">
            <ListMusic class="h-5 w-5 text-primary" />
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2">
                <span class="text-sm font-medium truncate">{{ selectedDetail.name }}</span>
                <Heart v-if="isDefault(selectedDetail.id)" class="h-3.5 w-3.5 text-primary" />
              </div>
              <div class="text-xs text-muted-foreground truncate">
                {{ selectedDetail.description || '无描述' }} ·
                {{ worksTotal }} 个作品
              </div>
            </div>
          </div>

          <Empty
            v-if="!selectedDetail.works || selectedDetail.works.length === 0"
            :icon="Heart"
            title="播放列表为空"
            description="在作品详情页可将作品加入此播放列表"
            class="flex-1"
          >
            <Button variant="gold" @click="router.push('/asmr')">去浏览</Button>
          </Empty>

          <div v-else class="flex flex-col gap-2 pb-4">
            <div
              v-for="w in selectedDetail.works"
              :key="w.id"
              class="group flex gap-3 rounded-lg border border-border bg-card/40 p-3 cursor-pointer hover:bg-accent/30"
              @click="openWork(w.id)"
            >
              <img
                :src="`/api/asmr/cover/${w.id}`"
                class="h-16 w-16 rounded-md object-cover border border-border shrink-0"
              />
              <div class="flex-1 min-w-0 flex flex-col gap-1">
                <div class="text-sm font-medium text-foreground truncate">{{ w.title }}</div>
                <div class="text-xs text-muted-foreground truncate">{{ w.name || '—' }}</div>
                <div class="flex items-center gap-2 text-[10px] text-muted-foreground mt-auto">
                  <span v-if="w.release">{{ w.release }}</span>
                  <span v-if="w.dl_count">· {{ w.dl_count }} DL</span>
                  <span v-if="w.rate_average_2dp">· ★ {{ w.rate_average_2dp }}</span>
                </div>
              </div>
              <span
                class="opacity-0 group-hover:opacity-100 transition-opacity shrink-0 self-center"
                @click.stop="handleRemoveWork(w.id)"
              >
                <Trash2 class="h-4 w-4 text-destructive hover:text-destructive/80" />
              </span>
            </div>

            <!-- 分页 -->
            <div v-if="worksTotalPage > 1" class="flex items-center justify-center gap-2 pt-3 shrink-0">
              <Button variant="outline" size="sm" :disabled="worksPage <= 1" @click="changeWorksPage(worksPage - 1)">
                上一页
              </Button>
              <span class="text-sm text-muted-foreground">
                {{ worksPage }} / {{ worksTotalPage }}
              </span>
              <Button variant="outline" size="sm" :disabled="worksPage >= worksTotalPage" @click="changeWorksPage(worksPage + 1)">
                下一页
              </Button>
            </div>
          </div>
        </template>
      </div>
    </div>

    <!-- 创建对话框 -->
    <Dialog v-model:open="showCreate">
      <DialogContent class="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>新建播放列表</DialogTitle>
          <DialogDescription>创建一个新的播放列表来整理你喜欢的作品</DialogDescription>
        </DialogHeader>
        <div class="flex flex-col gap-3 py-2">
          <div class="flex flex-col gap-1.5">
            <Label for="pl-name">名称</Label>
            <Input id="pl-name" v-model="newName" placeholder="播放列表名称" @keyup.enter="handleCreate" />
          </div>
          <div class="flex flex-col gap-1.5">
            <Label for="pl-desc">描述（可选）</Label>
            <textarea
              id="pl-desc"
              v-model="newDesc"
              placeholder="简单描述..."
              rows="2"
              class="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
            />
          </div>
        </div>
        <DialogFooter>
          <Button variant="ghost" @click="showCreate = false">取消</Button>
          <Button variant="gold" :disabled="creating || !newName.trim()" @click="handleCreate">
            <Loader2 v-if="creating" class="mr-2 h-4 w-4 animate-spin" />
            创建
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  </div>
</template>
