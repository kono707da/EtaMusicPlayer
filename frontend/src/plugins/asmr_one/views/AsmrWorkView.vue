<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  ArrowLeft,
  Loader2,
  Download,
  CheckSquare,
  Square,
  ExternalLink,
  HardDrive,
  Star,
  Heart,
  Sparkles,
  X,
  FileText,
  FileImage,
  Play
} from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '@/components/ui/select'
import { Switch } from '@/components/ui/switch'
import { Empty } from '@/components/ui/empty'
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription
} from '@/components/ui/dialog'
import { useToast } from '@/components/ui/toast/use-toast'
import FileTree from '../components/FileTree.vue'
import CoverPickerDialog from '@/components/CoverPickerDialog.vue'
import WorkCard from '../components/WorkCard.vue'
import {
  coverUrl,
  getWork,
  getWorkTracks,
  previewText,
  listTargetNodes,
  createDownload,
  getWorkNeighbors,
  upsertReview,
  deleteReview,
  getWorkInPlaylists,
  addToPlaylist,
  removeFromPlaylist
} from '../api'
import { addRecentTag, addRecentVa, addRecentCircle } from '../history'
import { useAsmrAccountStore } from '../store'

const router = useRouter()
const route = useRoute()
const toast = useToast()
const account = useAsmrAccountStore()

const workId = computed(() => Number(route.params.id))
const work = ref(null)
const tracksData = ref({ tree: [], files: [], total: 0, total_size: 0 })
const loading = ref(true)
const tracksLoading = ref(true)

// 选中的文件路径
const selectedPaths = ref(new Set())

// 目标节点
const targetNodes = ref([])
const selectedNodeId = ref('local_node')
// 选中的 watch_dir
const selectedWatchDirId = ref(null)

// 提交中
const submitting = ref(false)

// 下载选项：是否嵌入封面
const embedCover = ref(true)
const selectedCoverType = ref('main')  // main / sam / 240x240

// 下载完成后的封面选择器（给已完成的任务换封面）
const coverPickerOpen = ref(false)
const coverPickerTaskId = ref(null)

// 文件预览
const previewFile = ref(null)      // { node, fullPath, type }
const previewLoading = ref(false)
const previewContent = ref('')     // 文本内容
const showPreview = ref(false)

// 评价
const myRating = ref(0)
const myReviewText = ref('')
const reviewSaving = ref(false)

// 收藏
const inPlaylist = ref(false)
const playlistId = ref(null)
const favLoading = ref(false)

// 相似推荐
const neighbors = ref([])
const neighborsLoading = ref(false)

// 派生值
const selectedFiles = computed(() =>
  tracksData.value.files.filter((f) => selectedPaths.value.has(f.path))
)
const selectedSize = computed(() =>
  selectedFiles.value.reduce((sum, f) => sum + (f.size || 0), 0)
)
const watchDirs = computed(() => {
  const n = targetNodes.value.find((x) => x.id === selectedNodeId.value)
  return n?.watch_dirs || []
})

function toggleSelection({ paths, selected }) {
  const next = new Set(selectedPaths.value)
  for (const p of paths) {
    if (selected) next.add(p)
    else next.delete(p)
  }
  selectedPaths.value = next
}

function selectAll() {
  selectedPaths.value = new Set(tracksData.value.files.map((f) => f.path))
}

function selectNone() {
  selectedPaths.value = new Set()
}

// 文件预览
async function handlePreview(payload) {
  previewFile.value = payload
  previewContent.value = ''
  showPreview.value = true

  if (payload.type === 'text') {
    previewLoading.value = true
    try {
      // 兼容两种字段命名：flatten_file_tree 拍平后用 stream_url/url，原始 tree 用 mediaStreamUrl/mediaDownloadUrl
      const url = payload.node.stream_url || payload.node.mediaStreamUrl
        || payload.node.url || payload.node.mediaDownloadUrl
      if (!url) {
        previewContent.value = '（无法获取文件 URL）'
        return
      }
      previewContent.value = await previewText(url)
    } catch (e) {
      previewContent.value = `加载失败: ${e?.response?.data?.detail || e.message}`
    } finally {
      previewLoading.value = false
    }
  }
}

function closePreview() {
  showPreview.value = false
  previewFile.value = null
  previewContent.value = ''
}

async function loadWork() {
  loading.value = true
  try {
    work.value = await getWork(workId.value)
  } catch (e) {
    toast.error('加载作品失败', e?.response?.data?.detail || e.message)
  } finally {
    loading.value = false
  }
}

async function loadTracks() {
  tracksLoading.value = true
  try {
    const data = await getWorkTracks(workId.value)
    tracksData.value = data
    // 默认全选 audio 文件
    selectedPaths.value = new Set(data.files.map((f) => f.path))
  } catch (e) {
    toast.error('加载文件树失败', e?.response?.data?.detail || e.message)
  } finally {
    tracksLoading.value = false
  }
}

async function loadTargetNodes() {
  try {
    const data = await listTargetNodes()
    targetNodes.value = data.nodes || []
    if (targetNodes.value.length > 0) {
      selectedNodeId.value = targetNodes.value[0].id
      const wds = targetNodes.value[0].watch_dirs || []
      if (wds.length > 0) selectedWatchDirId.value = wds[0].id
    }
  } catch (e) {
    console.error('加载目标节点失败:', e)
  }
}

function onNodeChange(id) {
  selectedNodeId.value = id
  const n = targetNodes.value.find((x) => x.id === id)
  const wds = n?.watch_dirs || []
  selectedWatchDirId.value = wds.length > 0 ? wds[0].id : null
}

async function submitDownload() {
  if (selectedFiles.value.length === 0) {
    toast.warning('请至少选择一个文件')
    return
  }
  if (!selectedWatchDirId.value) {
    toast.warning('请选择目标监控目录')
    return
  }
  submitting.value = true
  try {
    // 推导元数据：专辑=作品标题，艺术家=声优名（逗号分隔），专辑艺术家=社团名
    const w = work.value || {}
    const artist = (w.vas || []).map((v) => v.name).filter(Boolean).join(', ') || ''
    const metadata = {
      album: w.title || '',
      artist: artist,
      album_artist: w.name || '',
      cover_type: embedCover.value ? selectedCoverType.value : null
    }
    const payload = {
      work_id: w.id,
      work_title: w.title,
      source_id: w.source_id,
      target_node_id: selectedNodeId.value,
      watch_dir_id: selectedWatchDirId.value,
      selected_paths: Array.from(selectedPaths.value),
      files: selectedFiles.value,
      metadata
    }
    const task = await createDownload(payload)
    toast.success(`已创建下载任务 #${task.id}（${selectedFiles.value.length} 个文件）`)
    router.push('/asmr/downloads')
  } catch (e) {
    toast.error('创建下载任务失败', e?.response?.data?.detail || e.message)
  } finally {
    submitting.value = false
  }
}

function formatSize(bytes) {
  if (!bytes) return '0 B'
  if (bytes >= 1024 * 1024 * 1024) return (bytes / 1024 / 1024 / 1024).toFixed(2) + ' GB'
  if (bytes >= 1024 * 1024) return (bytes / 1024 / 1024).toFixed(1) + ' MB'
  if (bytes >= 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return bytes + ' B'
}

function formatDuration(sec) {
  if (!sec) return '--:--'
  const h = Math.floor(sec / 3600)
  const m = Math.floor((sec % 3600) / 60)
  const s = Math.floor(sec % 60)
  if (h > 0) return `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
  return `${m}:${String(s).padStart(2, '0')}`
}

function openOriginal() {
  if (work.value?.source_url) {
    window.open(work.value.source_url, '_blank')
  }
}

// 跳转到标签/声优/社团筛选
function filterByTag(tag) {
  addRecentTag({ id: tag.id, name: tag.name })
  router.push({
    path: '/asmr',
    query: { tag: tag.id, tagName: tag.name, page: 1 }
  })
}

function filterByVa(va) {
  addRecentVa({ id: va.id, name: va.name })
  router.push({
    path: '/asmr',
    query: { va: va.id, vaName: va.name, page: 1 }
  })
}

function filterByCircle() {
  if (!work.value) return
  const id = work.value.circle_id
  const name = work.value.name || ''
  if (!id) return
  addRecentCircle({ id, name })
  router.push({
    path: '/asmr',
    query: { circle: id, circleName: name, page: 1 }
  })
}

onMounted(() => {
  loadWork()
  loadTracks()
  loadTargetNodes()
  loadNeighbors()
  if (account.isLoggedIn) loadReviewAndFav()
})

// 相似推荐
async function loadNeighbors() {
  neighborsLoading.value = true
  try {
    const data = await getWorkNeighbors(workId.value)
    neighbors.value = data.works || []
  } catch (e) {
    neighbors.value = []
  } finally {
    neighborsLoading.value = false
  }
}

// 评价 + 收藏状态
async function loadReviewAndFav() {
  // 加载收藏状态
  try {
    const data = await getWorkInPlaylists(workId.value)
    const playlists = data.playlists || []
    if (playlists.length > 0) {
      const first = playlists[0]
      playlistId.value = first.id
      inPlaylist.value = true
    }
  } catch (e) {
    // 静默
  }
  // 加载已有评价
  try {
    const { listReviews } = await import('../api')
    const data = await listReviews()
    const list = data.reviews || data.works || []
    const mine = list.find((r) => (r.work_id || r.id) === workId.value)
    if (mine) {
      myRating.value = mine.rating || 0
      myReviewText.value = mine.review_text || mine.review || ''
    }
  } catch (e) {
    // 静默
  }
}

// 提交评价
async function submitReview() {
  if (myRating.value === 0) {
    toast.warning('请先选择评分')
    return
  }
  reviewSaving.value = true
  try {
    await upsertReview(workId.value, myRating.value, myReviewText.value)
    toast.success('评价已提交')
  } catch (e) {
    toast.error('提交失败', e?.response?.data?.detail || e.message)
  } finally {
    reviewSaving.value = false
  }
}

// 删除评价
async function removeReview() {
  reviewSaving.value = true
  try {
    await deleteReview(workId.value)
    myRating.value = 0
    myReviewText.value = ''
    toast.success('已删除评价')
  } catch (e) {
    toast.error('删除失败', e?.response?.data?.detail || e.message)
  } finally {
    reviewSaving.value = false
  }
}

// 切换收藏
async function toggleFavorite() {
  if (!account.isLoggedIn) {
    toast.warning('请先登录')
    router.push('/asmr/account')
    return
  }
  favLoading.value = true
  try {
    if (inPlaylist.value && playlistId.value) {
      await removeFromPlaylist(playlistId.value, [workId.value])
      inPlaylist.value = false
      toast.success('已取消收藏')
    } else {
      // 如果没有默认收藏夹，先创建一个
      if (!playlistId.value) {
        const { createPlaylist, getDefaultPlaylist } = await import('../api')
        try {
          const dp = await getDefaultPlaylist()
          playlistId.value = dp.id
        } catch (e) {
          // 没有默认收藏夹，创建一个
          const created = await createPlaylist('我的收藏', 0, '默认收藏夹', [workId.value])
          playlistId.value = created.id
          inPlaylist.value = true
          toast.success('已收藏（新建收藏夹）')
          return
        }
      }
      await addToPlaylist(playlistId.value, [workId.value])
      inPlaylist.value = true
      toast.success('已收藏')
    }
  } catch (e) {
    toast.error('操作失败', e?.response?.data?.detail || e.message)
  } finally {
    favLoading.value = false
  }
}

function setRating(n) {
  myRating.value = n
}

function openNeighbor(id) {
  router.push(`/asmr/work/${id}`)
}
</script>

<template>
  <div class="flex flex-col gap-4">
    <!-- 顶部 -->
    <div class="flex items-center gap-3 shrink-0">
      <Button variant="ghost" size="sm" @click="router.back()">
        <ArrowLeft class="h-4 w-4" />
        返回
      </Button>
      <div class="flex-1" />
      <Button v-if="work?.source_url" variant="ghost" size="sm" @click="openOriginal">
        <ExternalLink class="h-4 w-4" />
        原站
      </Button>
    </div>

    <!-- 加载中 -->
    <div v-if="loading" class="flex items-center justify-center py-12 text-muted-foreground">
      <Loader2 class="mr-2 h-5 w-5 animate-spin" />
      加载作品信息...
    </div>

    <template v-else-if="work">
      <!-- 作品信息 -->
      <div class="flex gap-5 rounded-lg border border-border bg-card/40 p-4">
        <img
          :src="coverUrl(work.id)"
          :alt="work.title"
          class="h-40 w-40 rounded-md object-cover border border-border shrink-0"
        />
        <div class="flex-1 min-w-0 flex flex-col gap-2">
          <div class="flex items-start gap-2">
            <h2 class="text-xl font-semibold text-foreground flex-1">{{ work.title }}</h2>
            <Button
              variant="ghost"
              size="sm"
              :disabled="favLoading"
              :class="inPlaylist ? 'text-rose-500' : 'text-muted-foreground'"
              @click="toggleFavorite"
            >
              <Loader2 v-if="favLoading" class="h-4 w-4 animate-spin" />
              <Heart v-else class="h-4 w-4" :fill="inPlaylist ? 'currentColor' : 'none'" />
              {{ inPlaylist ? '已收藏' : '收藏' }}
            </Button>
            <Badge v-if="work.nsfw" variant="destructive">R18</Badge>
          </div>
          <div class="text-sm text-muted-foreground">
            社团：
            <button
              v-if="work.circle_id"
              class="text-primary hover:underline"
              @click="filterByCircle"
            >
              {{ work.name || '—' }}
            </button>
            <span v-else>{{ work.name || '—' }}</span>
            <span class="mx-2">·</span>
            发布：{{ work.release || '—' }}
            <span class="mx-2">·</span>
            时长：{{ formatDuration(work.duration) }}
          </div>
          <div class="text-sm text-muted-foreground">
            评分：★ {{ work.rate_average_2dp || '—' }}（{{ work.rate_count }} 人）
            <span class="mx-2">·</span>
            下载：{{ work.dl_count }} 次
            <span class="mx-2">·</span>
            价格：¥{{ work.price }}
          </div>
          <div class="flex flex-wrap gap-1.5 mt-1">
            <Badge
              v-for="t in (work.tags || []).slice(0, 12)"
              :key="t.id"
              variant="outline"
              class="cursor-pointer font-normal text-xs hover:border-primary/60 hover:text-primary"
              @click="filterByTag(t)"
            >
              {{ t.name }}
            </Badge>
          </div>
          <div v-if="work.vas?.length" class="text-xs text-muted-foreground mt-1">
            声优：
            <template v-for="(v, idx) in work.vas" :key="v.id">
              <span v-if="idx > 0">、</span>
              <button class="text-primary hover:underline" @click="filterByVa(v)">
                {{ v.name }}
              </button>
            </template>
          </div>
        </div>
      </div>

      <!-- 文件树 + 下载面板 -->
      <div class="grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-4">
        <!-- 文件树 -->
        <div class="flex flex-col rounded-lg border border-border bg-card/40 overflow-hidden">
          <div class="flex items-center justify-between px-4 py-2.5 border-b border-border">
            <div class="flex items-center gap-2 text-sm font-medium">
              <span>文件列表</span>
              <Badge variant="outline" class="text-xs">
                {{ tracksData.total }} 个文件 / {{ formatSize(tracksData.total_size) }}
              </Badge>
            </div>
            <div class="flex items-center gap-2 text-xs">
              <button class="text-primary hover:underline" @click="selectAll">
                <CheckSquare class="inline h-3.5 w-3.5" /> 全选
              </button>
              <button class="text-muted-foreground hover:underline" @click="selectNone">
                <Square class="inline h-3.5 w-3.5" /> 清空
              </button>
            </div>
          </div>
          <div class="overflow-auto p-2 max-h-[480px]">
            <div v-if="tracksLoading" class="flex items-center justify-center py-8 text-muted-foreground">
              <Loader2 class="mr-2 h-4 w-4 animate-spin" />
              加载文件树...
            </div>
            <Empty
              v-else-if="tracksData.tree.length === 0"
              :icon="HardDrive"
              title="无可下载文件"
              class="py-8"
            />
            <FileTree
              v-for="(node, idx) in tracksData.tree"
              :key="idx"
              :node="node"
              :level="0"
              :selected-paths="selectedPaths"
              :path-prefix="''"
              @toggle="toggleSelection"
              @preview="handlePreview"
            />
          </div>
        </div>

        <!-- 下载面板 -->
        <div class="flex flex-col rounded-lg border border-border bg-card/40 p-4 gap-3">
          <div class="text-sm font-medium">下载到节点</div>

          <div class="flex flex-col gap-1.5">
            <label class="text-xs text-muted-foreground">目标节点</label>
            <Select :model-value="selectedNodeId" @update:model-value="onNodeChange">
              <SelectTrigger class="h-9">
                <SelectValue placeholder="选择节点" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem v-for="n in targetNodes" :key="n.id" :value="n.id">
                  {{ n.name }}
                </SelectItem>
              </SelectContent>
            </Select>
            <p v-if="targetNodes.length === 0" class="text-xs text-amber-400">
              没有可用的目标节点（请启用 local_node 插件）
            </p>
          </div>

          <div class="flex flex-col gap-1.5">
            <label class="text-xs text-muted-foreground">监控目录</label>
            <Select v-model="selectedWatchDirId">
              <SelectTrigger class="h-9">
                <SelectValue placeholder="选择目录" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem
                  v-for="wd in watchDirs"
                  :key="wd.id"
                  :value="wd.id"
                >
                  {{ wd.path }}
                </SelectItem>
              </SelectContent>
            </Select>
            <p v-if="watchDirs.length === 0" class="text-xs text-amber-400">
              该节点未配置监控目录，请先到「扫描管理」添加
            </p>
          </div>

          <div class="rounded-md bg-secondary/40 p-2.5 text-xs">
            <div class="flex justify-between">
              <span class="text-muted-foreground">已选文件</span>
              <span class="text-foreground font-medium">{{ selectedFiles.length }} / {{ tracksData.total }}</span>
            </div>
            <div class="flex justify-between mt-1">
              <span class="text-muted-foreground">总大小</span>
              <span class="text-foreground font-medium">{{ formatSize(selectedSize) }}</span>
            </div>
          </div>

          <!-- 元数据预览：自动填充专辑/艺术家 -->
          <div class="rounded-md bg-secondary/40 p-2.5 text-xs space-y-1">
            <div class="text-muted-foreground mb-1">下载后将自动写入以下标签：</div>
            <div class="flex justify-between gap-2">
              <span class="text-muted-foreground shrink-0">专辑</span>
              <span class="text-foreground truncate" :title="work?.title">{{ work?.title || '—' }}</span>
            </div>
            <div class="flex justify-between gap-2">
              <span class="text-muted-foreground shrink-0">艺术家</span>
              <span class="text-foreground truncate" :title="(work?.vas || []).map(v => v.name).join(', ')">
                {{ (work?.vas || []).map(v => v.name).join(', ') || '—' }}
              </span>
            </div>
            <div class="flex justify-between gap-2">
              <span class="text-muted-foreground shrink-0">专辑艺术家</span>
              <span class="text-foreground truncate" :title="work?.name">{{ work?.name || '—' }}</span>
            </div>
          </div>

          <!-- 封面选择 -->
          <div class="rounded-md border border-border p-2.5 space-y-2">
            <div class="flex items-center justify-between">
              <label class="text-xs text-muted-foreground">嵌入封面到音频文件</label>
              <Switch v-model:checked="embedCover" />
            </div>
            <div v-if="embedCover" class="grid grid-cols-3 gap-2">
              <button
                v-for="t in [{v:'main',l:'主封面'},{v:'sam',l:'小图'},{v:'240x240',l:'240'}]"
                :key="t.v"
                type="button"
                class="relative rounded border-2 overflow-hidden aspect-square"
                :class="selectedCoverType === t.v
                  ? 'border-primary'
                  : 'border-transparent hover:border-border'"
                @click="selectedCoverType = t.v"
              >
                <img
                  v-if="work"
                  :src="coverUrl(work.id, t.v)"
                  :alt="t.l"
                  class="h-full w-full object-cover"
                  loading="lazy"
                />
                <span class="absolute bottom-0 left-0 right-0 bg-black/60 text-white text-[10px] py-0.5 text-center">
                  {{ t.l }}
                </span>
              </button>
            </div>
          </div>

          <Button
            variant="gold"
            :disabled="submitting || selectedFiles.length === 0 || !selectedWatchDirId"
            @click="submitDownload"
          >
            <Loader2 v-if="submitting" class="h-4 w-4 animate-spin" />
            <Download v-else class="h-4 w-4" />
            创建下载任务
          </Button>

          <p class="text-[11px] text-muted-foreground leading-relaxed">
            文件将下载到：<br />
            <code class="text-foreground">{{ watchDirs.find(w => w.id === selectedWatchDirId)?.path || '...' }}/{ASMR 子目录}/{{ work.title || '作品名' }}/...</code>
            <br /><br />
            下载完成后会自动写入标签并触发扫描入库。
          </p>
        </div>
      </div>

      <!-- 评价区 -->
      <div class="rounded-lg border border-border bg-card/40 p-4">
        <div class="flex items-center gap-2 mb-3">
          <Star class="h-4 w-4 text-amber-400" />
          <span class="text-sm font-medium">我的评价</span>
          <span v-if="!account.isLoggedIn" class="text-xs text-muted-foreground">
            （请先
            <router-link to="/asmr/account" class="text-primary hover:underline">登录</router-link>
            后评价）
          </span>
        </div>

        <template v-if="account.isLoggedIn">
          <div class="flex items-center gap-1 mb-3">
            <span class="text-xs text-muted-foreground mr-2">评分：</span>
            <button
              v-for="n in 10"
              :key="n"
              type="button"
              class="p-0.5"
              :class="n <= myRating ? 'text-amber-400' : 'text-muted-foreground/40 hover:text-muted-foreground'"
              @click="setRating(n)"
            >
              <Star class="h-4 w-4" :fill="n <= myRating ? 'currentColor' : 'none'" />
            </button>
            <span class="ml-2 text-xs text-muted-foreground">{{ myRating }}/10</span>
          </div>

          <textarea
            v-model="myReviewText"
            placeholder="写下你的评价（可选）..."
            class="mb-3 min-h-[80px] w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
            :disabled="reviewSaving"
          />

          <div class="flex items-center gap-2">
            <Button
              size="sm"
              :disabled="reviewSaving || myRating === 0"
              @click="submitReview"
            >
              <Loader2 v-if="reviewSaving" class="h-3.5 w-3.5 animate-spin" />
              {{ myRating > 0 ? '更新评价' : '提交评价' }}
            </Button>
            <Button
              v-if="myRating > 0"
              size="sm"
              variant="outline"
              :disabled="reviewSaving"
              @click="removeReview"
            >
              删除评价
            </Button>
          </div>
        </template>

        <div v-else class="text-sm text-muted-foreground py-2">
          登录后可以为本作品打分并撰写评价。
        </div>
      </div>

      <!-- 相似推荐 -->
      <div class="rounded-lg border border-border bg-card/40 p-4">
        <div class="flex items-center gap-2 mb-3">
          <Sparkles class="h-4 w-4 text-primary" />
          <span class="text-sm font-medium">相似推荐</span>
        </div>

        <div v-if="neighborsLoading" class="flex items-center justify-center py-6 text-muted-foreground">
          <Loader2 class="mr-2 h-4 w-4 animate-spin" />
          加载中...
        </div>

        <div v-else-if="neighbors.length === 0" class="text-sm text-muted-foreground py-4 text-center">
          暂无相似推荐
        </div>

        <div v-else class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
          <WorkCard
            v-for="item in neighbors"
            :key="item.id"
            :work="item"
            @click="openNeighbor(item.id)"
          />
        </div>
      </div>
    </template>

    <!-- 文件预览弹窗 -->
    <Dialog :open="showPreview" @update:open="(v) => { if (!v) closePreview() }">
      <DialogContent class="sm:max-w-2xl max-h-[85vh] flex flex-col">
        <DialogHeader class="shrink-0">
          <DialogTitle class="flex items-center gap-2 pr-6">
            <Play v-if="previewFile?.type === 'audio' || previewFile?.type === 'video'" class="h-4 w-4 shrink-0 text-emerald-400" />
            <FileImage v-else-if="previewFile?.type === 'image'" class="h-4 w-4 shrink-0 text-sky-400" />
            <FileText v-else-if="previewFile?.type === 'text'" class="h-4 w-4 shrink-0 text-muted-foreground" />
            <span class="truncate">{{ previewFile?.node?.title || '预览' }}</span>
          </DialogTitle>
          <DialogDescription class="truncate">
            {{ previewFile?.fullPath }}
            <span v-if="previewFile?.node?.size" class="ml-2">· {{ formatSize(previewFile.node.size) }}</span>
            <span v-if="previewFile?.node?.duration" class="ml-2">· {{ formatDuration(previewFile.node.duration) }}</span>
          </DialogDescription>
        </DialogHeader>

        <div class="flex-1 overflow-auto min-h-0">
          <!-- 音频播放 -->
          <div v-if="previewFile?.type === 'audio'" class="flex flex-col items-center gap-4 py-4">
            <div class="w-32 h-32 rounded-lg bg-gradient-to-br from-emerald-500/20 to-primary/20 flex items-center justify-center">
              <Play class="h-12 w-12 text-emerald-400" fill="currentColor" />
            </div>
            <audio
              :key="previewFile.node.stream_url || previewFile.node.mediaStreamUrl || previewFile.node.url || previewFile.node.mediaDownloadUrl"
              :src="previewFile.node.stream_url || previewFile.node.mediaStreamUrl || previewFile.node.url || previewFile.node.mediaDownloadUrl"
              controls
              autoplay
              class="w-full"
            >
              您的浏览器不支持音频播放
            </audio>
            <p class="text-xs text-muted-foreground">
              如果无法播放，可能是文件需要登录才能访问
            </p>
          </div>

          <!-- 视频播放 -->
          <div v-else-if="previewFile?.type === 'video'" class="flex justify-center">
            <video
              :key="previewFile.node.stream_url || previewFile.node.mediaStreamUrl || previewFile.node.url || previewFile.node.mediaDownloadUrl"
              :src="previewFile.node.stream_url || previewFile.node.mediaStreamUrl || previewFile.node.url || previewFile.node.mediaDownloadUrl"
              controls
              autoplay
              class="max-w-full max-h-[60vh] rounded"
            >
              您的浏览器不支持视频播放
            </video>
          </div>

          <!-- 图片预览 -->
          <div v-else-if="previewFile?.type === 'image'" class="flex justify-center">
            <img
              :src="previewFile.node.url || previewFile.node.mediaDownloadUrl"
              :alt="previewFile.node.title"
              class="max-w-full max-h-[60vh] rounded-lg border border-border object-contain"
              @error="$event.target.style.display='none'; $event.target.nextElementSibling.style.display='block'"
            />
            <p class="hidden text-sm text-muted-foreground py-8 text-center">
              图片加载失败（可能需要登录或文件不存在）
            </p>
          </div>

          <!-- 文本预览 -->
          <div v-else-if="previewFile?.type === 'text'">
            <div v-if="previewLoading" class="flex items-center justify-center py-8 text-muted-foreground">
              <Loader2 class="mr-2 h-4 w-4 animate-spin" />
              加载文本内容...
            </div>
            <pre v-else class="text-sm text-foreground whitespace-pre-wrap break-all p-3 bg-secondary/30 rounded-md font-mono">{{ previewContent || '（空文件）' }}</pre>
          </div>

          <!-- 不支持的类型 -->
          <div v-else class="flex items-center justify-center py-8 text-muted-foreground text-sm">
            此文件类型不支持预览
          </div>
        </div>
      </DialogContent>
    </Dialog>
  </div>
</template>
