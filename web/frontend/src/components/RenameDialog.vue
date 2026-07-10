<script setup>
import { ref, watch } from 'vue'
import {
  Wand2, RefreshCw, Eye, FileText, Info, ArrowRight
} from 'lucide-vue-next'
import { previewRename, executeRename } from '../api/node'
import { useNodesStore } from '../stores/nodes'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import {
  Table, TableHeader, TableBody, TableRow, TableHead, TableCell
} from '@/components/ui/table'
import { Empty } from '@/components/ui/empty'
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter
} from '@/components/ui/dialog'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { useToast } from '@/components/ui/toast/use-toast'

const props = defineProps({
  // 选中的曲目
  tracks: { type: Array, default: () => [] },
  visible: { type: Boolean, default: false }
})

const emit = defineEmits(['update:visible', 'applied'])

const nodesStore = useNodesStore()
const toast = useToast()

// 重命名模板：可用占位符 {artist} {title} {album} {year}
const template = ref('{artist} - {title}')
const previewing = ref(false)
const applying = ref(false)
const preview = ref([]) // [{id, oldName, newName}]

const placeholders = ['{artist}', '{title}', '{album}', '{year}']

watch(
  () => props.visible,
  (v) => {
    if (v) {
      preview.value = []
    }
  }
)

async function onPreview() {
  if (props.tracks.length === 0) {
    toast.warning('请先选择曲目')
    return
  }
  const node = nodesStore.activeNode
  if (!node) return
  previewing.value = true
  try {
    const data = await previewRename(
      node,
      props.tracks.map((t) => t.id),
      template.value
    )
    // 后端返回 {items: [{track_id, old_path, new_path}]}
    preview.value = data.items || []
    if (preview.value.length === 0) {
      toast.info('预览完成', '没有需要重命名的文件')
    }
  } catch (e) {
    toast.error('预览失败', e.response?.data?.detail || e.message, e)
  } finally {
    previewing.value = false
  }
}

async function onApply() {
  if (preview.value.length === 0) {
    toast.warning('请先预览')
    return
  }
  const node = nodesStore.activeNode
  if (!node) return
  applying.value = true
  try {
    await executeRename(
      node,
      props.tracks.map((t) => t.id),
      template.value
    )
    toast.success(`已重命名 ${props.tracks.length} 个文件`)
    emit('applied')
    emit('update:visible', false)
  } catch (e) {
    toast.error('重命名失败', e.response?.data?.detail || e.message, e)
  } finally {
    applying.value = false
  }
}

function onOpenChange(v) {
  emit('update:visible', v)
}

function close() {
  emit('update:visible', false)
}

function appendPlaceholder(p) {
  template.value = template.value + p
}
</script>

<template>
  <Dialog :open="visible" @update:open="onOpenChange">
    <DialogContent class="max-w-3xl max-h-[88vh] overflow-y-auto">
      <DialogHeader>
        <DialogTitle class="flex items-center gap-2">
          <Wand2 class="h-5 w-5 text-primary" />
          重命名预览 / 执行
        </DialogTitle>
        <DialogDescription>
          使用占位符模板批量重命名选中曲目文件，预览无误后再执行。
        </DialogDescription>
      </DialogHeader>

      <!-- 占位符提示 -->
      <Alert>
        <Info class="h-4 w-4 text-primary" />
        <AlertDescription class="flex flex-wrap items-center gap-1.5">
          <span>可用占位符：</span>
          <button
            v-for="p in placeholders"
            :key="p"
            type="button"
            class="rounded bg-primary/10 px-1.5 py-0.5 font-mono text-xs text-primary transition-colors hover:bg-primary/20"
            @click="appendPlaceholder(p)"
          >
            {{ p }}
          </button>
          <span class="text-xs text-muted-foreground">（点击插入到模板末尾）</span>
        </AlertDescription>
      </Alert>

      <!-- 模板输入 + 预览按钮 -->
      <div class="flex items-end gap-3">
        <div class="flex-1 space-y-1.5">
          <Label>命名模板</Label>
          <Input
            v-model="template"
            placeholder="{artist} - {title}"
            class="font-mono"
            @keyup.enter="onPreview"
          />
        </div>
        <Button
          variant="outline"
          :disabled="previewing || tracks.length === 0"
          class="border-primary text-primary hover:bg-primary/10"
          @click="onPreview"
        >
          <RefreshCw v-if="previewing" class="h-4 w-4 animate-spin" />
          <Eye v-else class="h-4 w-4" />
          预览
        </Button>
      </div>

      <!-- 预览结果 -->
      <div v-if="preview.length === 0" class="rounded-lg border border-dashed border-border">
        <Empty
          :icon="FileText"
          title="暂无预览结果"
          description="点击上方「预览」按钮查看重命名前后对比"
        />
      </div>
      <div v-else class="space-y-2">
        <div class="flex items-center gap-2 text-xs text-muted-foreground">
          <Badge variant="default">{{ preview.length }} 个文件</Badge>
          <span>将按以下规则重命名</span>
        </div>
        <div class="rounded-md border border-border">
          <Table>
            <TableHeader>
              <TableRow class="bg-secondary/40 hover:bg-secondary/40">
                <TableHead class="w-10 text-center">#</TableHead>
                <TableHead>原路径</TableHead>
                <TableHead class="w-6 text-center"></TableHead>
                <TableHead>新路径</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              <TableRow v-for="(row, i) in preview" :key="row.track_id ?? i">
                <TableCell class="text-center text-muted-foreground">{{ i + 1 }}</TableCell>
                <TableCell
                  class="max-w-[260px] truncate text-muted-foreground"
                  :title="row.old_path"
                >
                  {{ row.old_path }}
                </TableCell>
                <TableCell class="text-center text-muted-foreground">
                  <ArrowRight class="mx-auto h-3.5 w-3.5" />
                </TableCell>
                <TableCell
                  class="max-w-[260px] truncate text-primary"
                  :title="row.new_path"
                >
                  {{ row.new_path }}
                </TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </div>
      </div>

      <DialogFooter>
        <Button variant="ghost" @click="close">取消</Button>
        <Button
          variant="gold"
          :disabled="preview.length === 0 || applying"
          @click="onApply"
        >
          <RefreshCw v-if="applying" class="h-4 w-4 animate-spin" />
          <Wand2 v-else class="h-4 w-4" />
          执行重命名 ({{ tracks.length }})
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>
