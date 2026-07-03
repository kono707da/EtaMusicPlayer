<script setup>
import { ref, watch, computed } from 'vue'
import { useToast } from '@/components/ui/toast/use-toast'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription
} from '@/components/ui/dialog'
import { Loader2, Folder, ChevronUp, ArrowRight, HardDrive } from 'lucide-vue-next'
import { browseDirectories } from '@/api/node'

const props = defineProps({
  open: { type: Boolean, default: false },
  node: { type: Object, default: null },
  title: { type: String, default: '选择目录' }
})
const emit = defineEmits(['update:open', 'select'])

const toast = useToast()
const currentPath = ref('')         // 当前正在浏览的目录（'' 表示盘符列表）
const displayPath = ref('')          // 用户选中的目录路径（可手动编辑）
const entries = ref([])
const loading = ref(false)
const history = ref([])              // 浏览历史栈，用于"上一级"返回多次

const isRoot = computed(() => currentPath.value === '')

async function loadDir(path) {
  if (!props.node) return
  loading.value = true
  try {
    const data = await browseDirectories(props.node, path)
    currentPath.value = data.path || ''
    entries.value = data.entries || []
    displayPath.value = data.path || ''
  } catch (e) {
    toast.error('读取目录失败', e.response?.data?.detail || e.message)
    entries.value = []
  } finally {
    loading.value = false
  }
}

// 打开对话框时加载根目录
watch(
  () => props.open,
  (v) => {
    if (v) {
      history.value = []
      loadDir('')
    }
  }
)

function onClickEntry(entry) {
  // 进入子目录前，把当前路径推入历史
  if (currentPath.value) history.value.push(currentPath.value)
  loadDir(entry.path)
}

function onGoUp() {
  // 优先用后端给出的 parent；若历史栈非空则用历史栈（更精确）
  if (history.value.length > 0) {
    const prev = history.value.pop()
    loadDir(prev)
    return
  }
  // 没有历史时，回退到根（盘符列表）
  loadDir('')
}

function onConfirm() {
  const p = displayPath.value.trim()
  if (!p) {
    toast.warning('请选择或输入一个目录路径')
    return
  }
  emit('select', p)
  emit('update:open', false)
}

function onCancel() {
  emit('update:open', false)
}
</script>

<template>
  <Dialog :open="open" @update:open="(v) => emit('update:open', v)">
    <DialogContent class="max-w-2xl">
      <DialogHeader>
        <DialogTitle>{{ title }}</DialogTitle>
        <DialogDescription>
          点击目录进入下级，使用"上一级"返回。也可在下方直接编辑路径。
        </DialogDescription>
      </DialogHeader>

      <!-- 当前路径 + 上一级 -->
      <div class="flex items-center gap-2">
        <Button
          variant="outline"
          size="sm"
          :disabled="loading || history.length === 0 && isRoot"
          @click="onGoUp"
        >
          <ChevronUp class="h-4 w-4" />
          上一级
        </Button>
        <div
          class="flex-1 px-3 py-1.5 rounded-md bg-muted text-sm font-mono truncate"
          :title="currentPath || '（盘符列表）'"
        >
          {{ currentPath || '（盘符列表）' }}
        </div>
      </div>

      <!-- 目录列表 -->
      <div class="border border-border rounded-md h-80 overflow-y-auto contain-content">
        <div v-if="loading" class="flex items-center justify-center h-full">
          <Loader2 class="h-5 w-5 animate-spin text-primary" />
        </div>
        <ul v-else-if="entries.length > 0" class="py-1">
          <li
            v-for="entry in entries"
            :key="entry.path"
            v-memo="[entry.path]"
            class="flex items-center gap-2 px-3 py-2 cursor-pointer hover:bg-accent text-sm"
            @click="onClickEntry(entry)"
          >
            <Folder class="h-4 w-4 text-primary shrink-0" />
            <span class="truncate">{{ entry.name }}</span>
            <ArrowRight class="h-3.5 w-3.5 ml-auto text-muted-foreground shrink-0" />
          </li>
        </ul>
        <div
          v-else
          class="flex flex-col items-center justify-center h-full text-muted-foreground text-sm gap-2"
        >
          <HardDrive class="h-8 w-8 opacity-40" />
          <span>没有可访问的子目录</span>
        </div>
      </div>

      <!-- 可编辑路径 -->
      <div class="space-y-1">
        <label class="text-xs text-muted-foreground">已选路径（可手动编辑）</label>
        <Input v-model="displayPath" placeholder="如：D:/Music" class="font-mono" />
      </div>

      <DialogFooter>
        <Button variant="outline" @click="onCancel">取消</Button>
        <Button @click="onConfirm">确定</Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>
