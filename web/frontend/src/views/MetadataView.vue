<script setup>
import { ref, onMounted } from 'vue'
import { RefreshCw, Pencil, Wand2, AlertCircle } from 'lucide-vue-next'
import { useAuthStore } from '../stores/auth'
import { useLibraryStore } from '../stores/library'
import { getTracks } from '../api/node'
import TrackTable from '../components/TrackTable.vue'
import MetadataPanel from '../components/MetadataPanel.vue'
import RenameDialog from '../components/RenameDialog.vue'
import { Button } from '@/components/ui/button'
import { Alert, AlertTitle, AlertDescription } from '@/components/ui/alert'
import { useToast } from '@/components/ui/toast/use-toast'

const authStore = useAuthStore()
const libraryStore = useLibraryStore()
const toast = useToast()

const tracks = ref([])
const loading = ref(false)
const selectedTracks = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(50)

const metadataVisible = ref(false)
const renameVisible = ref(false)

async function loadTracks() {
  const node = authStore.localNode
  if (!node) return
  loading.value = true
  try {
    const data = await getTracks(node, {
      page: page.value,
      page_size: pageSize.value
    })
    tracks.value = data.items || data.tracks || []
    total.value = data.total || tracks.value.length
  } catch (e) {
    toast.error('加载曲目失败', e.message || String(e), e)
  } finally {
    loading.value = false
  }
}

function onSelectionChange(rows) {
  selectedTracks.value = rows
}

function onPageChange(p) {
  page.value = p
  loadTracks()
}

function openMetadata() {
  if (selectedTracks.value.length === 0) {
    toast.warning('请先选择曲目')
    return
  }
  metadataVisible.value = true
}

function openRename() {
  if (selectedTracks.value.length === 0) {
    toast.warning('请先选择曲目')
    return
  }
  renameVisible.value = true
}

async function onUpdated() {
  await loadTracks()
}

onMounted(() => {
  loadTracks()
})
</script>

<template>
  <div class="flex flex-col gap-4">
    <!-- 顶部标题 + 操作 -->
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div class="flex items-center gap-2.5">
        <span class="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/15 text-primary">
          <Wand2 class="h-4 w-4" />
        </span>
        <h2 class="m-0 text-2xl font-bold tracking-tight text-foreground">元数据批量编辑</h2>
      </div>
      <div class="flex items-center gap-2">
        <Button variant="secondary" @click="loadTracks">
          <RefreshCw class="h-4 w-4" />
          刷新
        </Button>
        <Button
          :disabled="selectedTracks.length === 0"
          @click="openMetadata"
        >
          <Pencil class="h-4 w-4" />
          批量编辑字段
        </Button>
        <Button
          :disabled="selectedTracks.length === 0"
          @click="openRename"
        >
          <Wand2 class="h-4 w-4" />
          重命名预览 / 执行
        </Button>
      </div>
    </div>

    <!-- 提示 -->
    <Alert>
      <AlertCircle class="h-4 w-4 text-primary" />
      <AlertTitle>操作提示</AlertTitle>
      <AlertDescription>
        从下方表格中选择曲目，然后使用顶部按钮进行批量元数据编辑或重命名。
      </AlertDescription>
    </Alert>

    <!-- 加载遮罩 -->
    <div class="relative">
      <TrackTable
        :tracks="tracks"
        :node-id="authStore.localNode?.id"
        :node-name="authStore.localNode?.name || ''"
        :loading="loading"
        :total="total"
        :page="page"
        :page-size="pageSize"
        :show-pagination="true"
        @selection-change="onSelectionChange"
        @page-change="onPageChange"
      />
      <div
        v-if="loading"
        class="absolute inset-0 z-10 flex items-center justify-center bg-background/60 backdrop-blur-sm"
      >
        <RefreshCw class="h-6 w-6 animate-spin text-primary" />
      </div>
    </div>

    <MetadataPanel
      v-model:visible="metadataVisible"
      :tracks="selectedTracks"
      @updated="onUpdated"
    />

    <RenameDialog
      v-model:visible="renameVisible"
      :tracks="selectedTracks"
      @applied="onUpdated"
    />
  </div>
</template>
