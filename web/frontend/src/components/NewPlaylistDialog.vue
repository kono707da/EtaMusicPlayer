<script setup>
import { ref, computed, watch } from 'vue'
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Select, SelectTrigger, SelectValue, SelectContent, SelectItem
} from '@/components/ui/select'
import { useToast } from '@/components/ui/toast/use-toast'
import { useNodesStore } from '../stores/nodes'
import { useLibraryStore } from '../stores/library'
import {
  createPlaylist, getWatchDirs, browseDirectories, submitM3uImport
} from '../api/node'
import { createClientPlaylist } from '../api/client_playlist'
import {
  Loader2, Folder, FileText, ChevronUp, ArrowRight, HardDrive
} from 'lucide-vue-next'

const props = defineProps({
  open: { type: Boolean, default: false },
  group: { type: Object, default: null },
  folderId: { type: Number, default: null }
})
const emit = defineEmits(['update:open', 'created'])

const toast = useToast()
const nodesStore = useNodesStore()
const libraryStore = useLibraryStore()

// 表单状态
const playlistName = ref('')
const submitting = ref(false)
// 目标文件夹（0=根级，正整数=文件夹 id）
const targetFolderId = ref(0)

// m3u 导入相关
const isNodeGroup = computed(() => props.group?.type === 'node-group')
const importMode = ref('blank')          // 'blank' | 'm3u'
const fileMode = ref('single')           // 'single' | 'folder'
const copyMode = ref('copy')             // 'copy' | 'move'
const watchDirs = ref([])
const watchDirId = ref(null)
const selectedPath = ref('')             // 单文件模式：m3u 文件路径；文件夹模式：文件夹路径

// 文件浏览器（内嵌于本弹窗）
const browserOpen = ref(false)
const browserCurrentPath = ref('')
const browserDisplayPath = ref('')
const browserEntries = ref([])
const browserLoading = ref(false)
const browserHistory = ref([])

const node = computed(() => {
  if (!isNodeGroup.value) return null
  return nodesStore.getNode(props.group?.nodeId)
})

// 该节点是否支持 m3u 导入功能
const supportsM3uImport = computed(() => {
  if (!isNodeGroup.value || !node.value) return false
  return nodesStore.hasFeature(node.value.id, 'import_m3u')
})

/**
 * 当前分组可选的文件夹列表（扁平），用于目标文件夹下拉框
 * 返回 [{ id, name, pathDisplay }]
 */
const folderOptions = computed(() => {
  let folders = []
  if (isNodeGroup.value && props.group?.nodeId != null) {
    folders = libraryStore.nodeFolders[props.group.nodeId] || []
  } else {
    folders = libraryStore.clientFolders || []
  }
  if (!folders.length) return []
  // 构建 id -> folder 映射，计算路径显示
  const byId = new Map(folders.map((f) => [f.id, f]))
  function pathOf(f) {
    const parts = []
    let cur = f
    const guard = new Set()
    while (cur && !guard.has(cur.id)) {
      guard.add(cur.id)
      parts.unshift(cur.name)
      cur = cur.parent_id != null ? byId.get(cur.parent_id) : null
    }
    return parts.join(' / ')
  }
  return folders.map((f) => ({ id: f.id, name: f.name, pathDisplay: pathOf(f) }))
})

const canSubmit = computed(() => {
  if (submitting.value) return false
  const name = playlistName.value.trim()
  if (importMode.value === 'blank') {
    return !!name
  }
  // m3u 导入
  if (!isNodeGroup.value) return false
  if (!watchDirId.value) return false
  if (!selectedPath.value) return false
  return true
})

watch(
  () => props.open,
  (v) => {
    if (v) {
      playlistName.value = ''
      importMode.value = 'blank'
      fileMode.value = 'single'
      copyMode.value = 'copy'
      selectedPath.value = ''
      watchDirId.value = null
      watchDirs.value = []
      browserOpen.value = false
      browserEntries.value = []
      browserCurrentPath.value = ''
      browserDisplayPath.value = ''
      browserHistory.value = []
      // 从 folderId prop 初始化目标文件夹（0=根级）
      targetFolderId.value = props.folderId ?? 0
      if (isNodeGroup.value) {
        loadWatchDirs()
      }
    }
  }
)

async function loadWatchDirs() {
  if (!node.value) return
  try {
    const list = await getWatchDirs(node.value)
    watchDirs.value = list || []
    if (watchDirs.value.length > 0 && !watchDirId.value) {
      watchDirId.value = watchDirs.value[0].id
    }
  } catch (e) {
    toast.error('读取监控目录失败', e?.response?.data?.detail || e.message, e)
  }
}

// ============ 文件浏览器 ============
async function openBrowser() {
  if (!node.value) {
    toast.error('节点未连接')
    return
  }
  browserOpen.value = true
  browserHistory.value = []
  await loadBrowserDir('')
}

async function loadBrowserDir(path) {
  if (!node.value) return
  browserLoading.value = true
  try {
    // includeFiles=true 仅在单文件模式下需要
    const includeFiles = fileMode.value === 'single'
    const data = await browseDirectories(node.value, path, includeFiles)
    browserCurrentPath.value = data.path || ''
    browserEntries.value = data.entries || []
    browserDisplayPath.value = data.path || ''
  } catch (e) {
    toast.error('读取目录失败', e?.response?.data?.detail || e.message, e)
    browserEntries.value = []
  } finally {
    browserLoading.value = false
  }
}

function onClickEntry(entry) {
  if (entry.is_file) {
    // 单文件模式：选中 m3u 文件
    selectedPath.value = entry.path
    browserOpen.value = false
    if (!playlistName.value.trim()) {
      playlistName.value = entry.name.replace(/\.(m3u8?|M3U8?)$/i, '')
    }
    return
  }
  // 文件夹：进入子目录（单文件和文件夹模式都进入下级，
  // 文件夹模式下通过「选择此文件夹」按钮确认当前目录作为目标）
  if (browserCurrentPath.value) browserHistory.value.push(browserCurrentPath.value)
  loadBrowserDir(entry.path)
}

function onBrowserGoUp() {
  if (browserHistory.value.length > 0) {
    const prev = browserHistory.value.pop()
    loadBrowserDir(prev)
    return
  }
  loadBrowserDir('')
}

function onBrowserConfirmFolder() {
  if (fileMode.value !== 'folder') return
  const p = browserDisplayPath.value.trim()
  if (!p) {
    toast.warning('请选择或输入一个目录路径')
    return
  }
  selectedPath.value = p
  browserOpen.value = false
}

function onBrowserCancel() {
  browserOpen.value = false
}

function onSwitchFileMode(mode) {
  fileMode.value = mode
  selectedPath.value = ''
  // 切换模式后重新加载当前目录，按需附带 m3u 文件
  if (browserOpen.value) {
    loadBrowserDir(browserCurrentPath.value)
  }
}

// ============ 提交 ============
async function onSubmit() {
  const name = playlistName.value.trim()
  // 0 → null（根级）
  const folderId = targetFolderId.value === 0 ? null : targetFolderId.value
  if (importMode.value === 'blank') {
    if (!name) {
      toast.warning('请输入播放列表名称')
      return
    }
    submitting.value = true
    try {
      if (isNodeGroup.value) {
        if (!node.value || !node.value.token) {
          toast.error('节点未登录，无法创建')
          return
        }
        await createPlaylist(node.value, {
          name,
          description: '',
          folder_id: folderId
        })
      } else {
        await createClientPlaylist(name, '', folderId)
      }
      await libraryStore.refreshAllPlaylists()
      toast.success('已创建播放列表')
      emit('created', { name })
      emit('update:open', false)
    } catch (e) {
      toast.error('创建播放列表失败', e?.response?.data?.detail || e.message, e)
    } finally {
      submitting.value = false
    }
    return
  }

  // m3u 导入
  if (!isNodeGroup.value) {
    toast.error('本机播放列表不支持 m3u 导入')
    return
  }
  if (!node.value) {
    toast.error('节点未连接')
    return
  }
  if (!watchDirId.value) {
    toast.warning('请选择入库目标监控目录')
    return
  }
  if (!selectedPath.value) {
    toast.warning('请先选择 m3u 文件或文件夹')
    return
  }

  const payload = {
    watch_dir_id: watchDirId.value,
    mode: copyMode.value,
    playlist_name: name || undefined,
    target_folder_id: folderId ?? undefined
  }
  if (fileMode.value === 'single') {
    payload.m3u_path = selectedPath.value
  } else {
    payload.folder_path = selectedPath.value
  }

  submitting.value = true
  try {
    const task = await submitM3uImport(node.value, payload)
    toast.success('已提交导入任务', `任务 #${task.id}，请到任务队列查看进度`)
    emit('created', { taskId: task.id, importM3u: true })
    emit('update:open', false)
  } catch (e) {
    toast.error('提交导入任务失败', e?.response?.data?.detail || e.message, e)
  } finally {
    submitting.value = false
  }
}

function onCancel() {
  if (submitting.value) return
  emit('update:open', false)
}
</script>

<template>
  <Dialog :open="open" @update:open="(v) => emit('update:open', v)">
    <DialogContent class="max-w-2xl">
      <DialogHeader>
        <DialogTitle>新建播放列表</DialogTitle>
        <DialogDescription>
          {{ isNodeGroup ? `在节点「${group?.nodeName || group?.label}」下创建` : '在本机创建' }}
        </DialogDescription>
      </DialogHeader>

      <!-- 名称 -->
      <div class="space-y-1.5">
        <Label>播放列表名称</Label>
        <Input
          v-model="playlistName"
          placeholder="留空将使用 m3u 文件名（m3u 导入模式）"
          :disabled="submitting"
        />
      </div>

      <!-- 目标文件夹 -->
      <div class="space-y-1.5">
        <Label>目标文件夹</Label>
        <Select v-model="targetFolderId" :disabled="submitting">
          <SelectTrigger class="w-full">
            <SelectValue placeholder="根级（无文件夹）" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem :value="0">根级（无文件夹）</SelectItem>
            <SelectItem
              v-for="f in folderOptions"
              :key="f.id"
              :value="f.id"
            >
              {{ f.pathDisplay }}
            </SelectItem>
          </SelectContent>
        </Select>
        <p v-if="folderOptions.length === 0" class="text-xs text-muted-foreground">
          暂无文件夹，播放列表将创建在根级
        </p>
        <p
          v-if="importMode === 'm3u' && fileMode === 'folder' && targetFolderId !== 0"
          class="text-xs text-muted-foreground"
        >
          文件夹导入将保留 m3u 相对层级，并挂在此目标文件夹下
        </p>
      </div>

      <!-- 节点分组：可选 m3u 导入 -->
      <div v-if="isNodeGroup" class="space-y-3">
        <div class="flex items-center gap-3">
          <Label class="cursor-pointer">
            <input
              type="radio"
              value="blank"
              v-model="importMode"
              :disabled="submitting"
              class="mr-2"
            />
            空白播放列表
          </Label>
          <Label :class="supportsM3uImport ? 'cursor-pointer' : 'cursor-not-allowed opacity-50'">
            <input
              type="radio"
              value="m3u"
              v-model="importMode"
              :disabled="submitting || !supportsM3uImport"
              class="mr-2"
            />
            从本机 m3u 文件导入
            <span v-if="!supportsM3uImport" class="text-xs text-muted-foreground ml-1">
              （节点版本不支持）
            </span>
          </Label>
        </div>

        <!-- m3u 导入选项 -->
        <div v-if="importMode === 'm3u'" class="rounded-md border border-border p-3 space-y-3 bg-muted/30">
          <!-- 模式：单文件 / 文件夹 -->
          <div class="flex items-center gap-3">
            <Label class="cursor-pointer">
              <input
                type="radio"
                value="single"
                v-model="fileMode"
                :disabled="submitting"
                class="mr-2"
                @change="onSwitchFileMode('single')"
              />
              单个 m3u 文件
            </Label>
            <Label class="cursor-pointer">
              <input
                type="radio"
                value="folder"
                v-model="fileMode"
                :disabled="submitting"
                class="mr-2"
                @change="onSwitchFileMode('folder')"
              />
              文件夹（递归导入所有 m3u）
            </Label>
          </div>

          <!-- 入库目标 -->
          <div class="space-y-1.5">
            <Label>入库目标监控目录</Label>
            <Select v-model="watchDirId" :disabled="submitting">
              <SelectTrigger class="w-full">
                <SelectValue placeholder="选择监控目录" />
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
            <p v-if="watchDirs.length === 0" class="text-xs text-muted-foreground">
              当前节点尚未配置监控目录，请先在节点管理中添加
            </p>
          </div>

          <!-- 文件选择 -->
          <div class="space-y-1.5">
            <Label>{{ fileMode === 'single' ? 'm3u 文件路径' : '文件夹路径' }}</Label>
            <div class="flex gap-2">
              <Input
                v-model="selectedPath"
                :placeholder="fileMode === 'single' ? '点击右侧按钮选择 m3u 文件' : '点击右侧按钮选择文件夹'"
                readonly
                class="font-mono text-xs"
              />
              <Button
                variant="outline"
                size="sm"
                :disabled="submitting || !node"
                @click="openBrowser"
              >
                选择{{ fileMode === 'single' ? '文件' : '文件夹' }}
              </Button>
            </div>
          </div>

          <!-- 复制 / 剪切 -->
          <div class="flex items-center gap-3">
            <Label class="cursor-pointer">
              <input
                type="radio"
                value="copy"
                v-model="copyMode"
                :disabled="submitting"
                class="mr-2"
              />
              复制（保留原文件）
            </Label>
            <Label class="cursor-pointer">
              <input
                type="radio"
                value="move"
                v-model="copyMode"
                :disabled="submitting"
                class="mr-2"
              />
              剪切（移动原文件）
            </Label>
          </div>

          <p class="text-xs text-muted-foreground">
            提示：导入后按 m3u 原始顺序创建播放列表。文件夹模式下保留 m3u 相对目录层级（自动创建同名文件夹），每个 m3u 创建一个独立播放列表。
          </p>
        </div>
      </div>

      <DialogFooter>
        <Button variant="outline" @click="onCancel" :disabled="submitting">取消</Button>
        <Button @click="onSubmit" :disabled="!canSubmit">
          <Loader2 v-if="submitting" class="h-4 w-4 mr-1 animate-spin" />
          {{ importMode === 'm3u' && isNodeGroup ? '提交导入任务' : '创建' }}
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>

  <!-- 文件/文件夹浏览器（嵌套 Dialog） -->
  <Dialog :open="browserOpen" @update:open="(v) => (browserOpen = v)">
    <DialogContent class="max-w-2xl">
      <DialogHeader>
        <DialogTitle>
          {{ fileMode === 'single' ? '选择 m3u 文件' : '选择文件夹' }}
        </DialogTitle>
        <DialogDescription>
          <template v-if="fileMode === 'single'">
            点击 m3u 文件直接选中；点击文件夹进入下级。
          </template>
          <template v-else>
            点击文件夹进入下级，到达目标目录后点「选择此文件夹」确认。
          </template>
        </DialogDescription>
      </DialogHeader>

      <!-- 当前路径 + 上一级 -->
      <div class="flex items-center gap-2">
        <Button
          variant="outline"
          size="sm"
          :disabled="browserLoading || (browserHistory.length === 0 && !browserCurrentPath)"
          @click="onBrowserGoUp"
        >
          <ChevronUp class="h-4 w-4" />
          上一级
        </Button>
        <div
          class="flex-1 px-3 py-1.5 rounded-md bg-muted text-sm font-mono truncate"
          :title="browserCurrentPath || '（盘符列表）'"
        >
          {{ browserCurrentPath || '（盘符列表）' }}
        </div>
      </div>

      <!-- 条目列表 -->
      <div class="border border-border rounded-md h-80 overflow-y-auto">
        <div v-if="browserLoading" class="flex items-center justify-center h-full">
          <Loader2 class="h-5 w-5 animate-spin text-primary" />
        </div>
        <ul v-else-if="browserEntries.length > 0" class="py-1">
          <li
            v-for="entry in browserEntries"
            :key="entry.path"
            v-memo="[entry.path]"
            class="flex items-center gap-2 px-3 py-2 cursor-pointer hover:bg-accent text-sm"
            @click="onClickEntry(entry)"
          >
            <FileText
              v-if="entry.is_file"
              class="h-4 w-4 text-amber-600 shrink-0"
            />
            <Folder v-else class="h-4 w-4 text-primary shrink-0" />
            <span class="truncate flex-1">{{ entry.name }}</span>
            <ArrowRight
              v-if="!entry.is_file"
              class="h-3.5 w-3.5 ml-auto text-muted-foreground shrink-0"
            />
          </li>
        </ul>
        <div
          v-else
          class="flex flex-col items-center justify-center h-full text-muted-foreground text-sm gap-2"
        >
          <HardDrive class="h-8 w-8 opacity-40" />
          <span>没有可访问的内容</span>
        </div>
      </div>

      <!-- 文件夹模式：可编辑路径 + 确认 -->
      <div v-if="fileMode === 'folder'" class="space-y-1">
        <label class="text-xs text-muted-foreground">已选路径（可手动编辑）</label>
        <Input v-model="browserDisplayPath" placeholder="如：D:/Playlists" class="font-mono" />
      </div>

      <DialogFooter>
        <Button variant="outline" @click="onBrowserCancel">取消</Button>
        <Button v-if="fileMode === 'folder'" @click="onBrowserConfirmFolder">
          选择此文件夹
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>
