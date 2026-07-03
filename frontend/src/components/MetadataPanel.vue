<script setup>
import { ref, computed, watch } from 'vue'
import {
  Pencil, Check, X, ChevronDown, AlertCircle, Layers, RefreshCw
} from 'lucide-vue-next'
import { updateMetadataField } from '../api/node'
import { useNodesStore } from '../stores/nodes'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter
} from '@/components/ui/dialog'
import { Alert, AlertTitle, AlertDescription } from '@/components/ui/alert'
import { useToast } from '@/components/ui/toast/use-toast'

const props = defineProps({
  // 选中的曲目
  tracks: { type: Array, default: () => [] },
  visible: { type: Boolean, default: false }
})

const emit = defineEmits(['update:visible', 'updated'])

const nodesStore = useNodesStore()
const toast = useToast()

// 批量编辑的字段值
const form = ref({
  field: 'artist',
  value: '',
  preview: true
})

// 可批量编辑的字段
const fields = [
  { label: '艺术家', value: 'artist' },
  { label: '专辑', value: 'album' },
  { label: '标题', value: 'title' },
  { label: '年份', value: 'year' },
  { label: '流派', value: 'genre' }
]

// 看板分区（按字段 key 归组）
const fieldGroups = [
  { title: '基本信息', desc: '曲目基础标识', keys: ['title', 'artist'] },
  { title: '专辑信息', desc: '专辑与分类归属', keys: ['album', 'year', 'genre'] }
]

// 看板预览：每首曲目 [field] 的旧值 → 新值
const preview = ref([])

watch(
  () => [props.visible, props.tracks, form.value.field, form.value.value],
  ([vis]) => {
    if (!vis) return
    preview.value = props.tracks.map((t) => ({
      id: t.id,
      title: t.title,
      artist: t.artist,
      old: t[form.value.field] || '',
      new: form.value.value || ''
    }))
  },
  { immediate: true, deep: true }
)

const hasSelection = computed(() => props.tracks.length > 0)

// 看板：每个字段的公共/差异状态与值分布
const fieldStates = computed(() => {
  return fields.map((f) => {
    const values = props.tracks.map((t) => String(t[f.value] ?? ''))
    const unique = [...new Set(values)]
    const common = unique.length === 1
    const distribution = unique
      .map((v) => ({ value: v, count: values.filter((x) => x === v).length }))
      .sort((a, b) => b.count - a.count)
    return {
      key: f.value,
      label: f.label,
      common,
      value: common ? unique[0] : '',
      distribution
    }
  })
})

function groupFields(keys) {
  return fieldStates.value.filter((s) => keys.includes(s.key))
}

// 内联编辑状态
const editingField = ref(null)
const expandedField = ref(null)
const applying = ref(false)

const currentFieldLabel = computed(
  () => fields.find((f) => f.value === form.value.field)?.label || ''
)

// 编辑时会变化的曲目数（基于 preview 旧/新值）
const changedCount = computed(
  () => preview.value.filter((p) => p.old !== (p.new || '')).length
)

function startEdit(key, currentValue) {
  form.value.field = key
  form.value.value = currentValue || ''
  editingField.value = key
  expandedField.value = null
}

function cancelEdit() {
  editingField.value = null
  form.value.value = ''
}

function toggleExpand(key) {
  expandedField.value = expandedField.value === key ? null : key
}

async function onApply() {
  if (!hasSelection.value) {
    toast.warning('请先选择曲目')
    return
  }
  if (!form.value.value) {
    toast.warning('请输入新值')
    return
  }
  const node = nodesStore.activeNode
  if (!node) return
  applying.value = true
  try {
    await updateMetadataField(
      node,
      props.tracks.map((t) => t.id),
      form.value.field,
      form.value.value
    )
    toast.success(`已更新 ${props.tracks.length} 首曲目`)
    emit('updated')
    emit('update:visible', false)
  } catch (e) {
    toast.error('更新失败', e.response?.data?.detail || e.message)
  } finally {
    applying.value = false
  }
}

function onOpenChange(v) {
  if (!v) cancelEdit()
  emit('update:visible', v)
}

function close() {
  emit('update:visible', false)
}
</script>

<template>
  <Dialog :open="visible" @update:open="onOpenChange">
    <DialogContent class="max-w-3xl max-h-[88vh] overflow-y-auto">
      <DialogHeader>
        <DialogTitle class="flex items-center gap-2">
          <Layers class="h-5 w-5 text-primary" />
          元数据批量编辑
        </DialogTitle>
        <DialogDescription>
          查看选中曲目的公共 / 差异字段，点击编辑按钮逐字段批量回写。
        </DialogDescription>
      </DialogHeader>

      <!-- 未选择曲目 -->
      <Alert v-if="!hasSelection">
        <AlertCircle class="h-4 w-4 text-primary" />
        <AlertTitle>未选择曲目</AlertTitle>
        <AlertDescription>请先在曲目表格中选择要编辑的曲目。</AlertDescription>
      </Alert>

      <template v-else>
        <!-- 选中概要 -->
        <div class="flex items-center gap-2 text-sm text-muted-foreground">
          <Badge variant="default">{{ tracks.length }} 首选中</Badge>
          <span>·</span>
          <span>共 {{ fields.length }} 个可编辑字段，公共字段可直接回写，差异字段可展开查看分布</span>
        </div>

        <!-- 看板：按区分组 -->
        <div class="space-y-4">
          <Card v-for="group in fieldGroups" :key="group.title">
            <CardHeader class="pb-3">
              <div class="flex items-baseline justify-between">
                <CardTitle class="text-base">{{ group.title }}</CardTitle>
                <span class="text-xs text-muted-foreground">{{ group.desc }}</span>
              </div>
            </CardHeader>
            <CardContent class="space-y-0.5">
              <div
                v-for="state in groupFields(group.keys)"
                :key="state.key"
                class="flex items-center gap-3 rounded-md px-3 py-2.5 transition-colors hover:bg-accent/30"
                :class="{
                  'bg-primary/5 ring-1 ring-primary': editingField === state.key
                }"
              >
                <!-- 字段名 -->
                <Label class="w-16 shrink-0 text-muted-foreground">{{ state.label }}</Label>

                <!-- 值 / 编辑器 -->
                <div class="min-w-0 flex-1">
                  <template v-if="editingField === state.key">
                    <Input
                      v-model="form.value"
                      placeholder="留空则清空"
                      :disabled="applying"
                    />
                  </template>
                  <template v-else>
                    <!-- 公共值 -->
                    <div
                      v-if="state.common"
                      class="truncate text-foreground"
                      :title="state.value"
                    >
                      {{ state.value || '(空)' }}
                    </div>
                    <!-- 差异：多个值 -->
                    <div v-else>
                      <button
                        type="button"
                        class="inline-flex items-center gap-1 text-muted-foreground transition-colors hover:text-primary"
                        @click="toggleExpand(state.key)"
                      >
                        <span>&lt;多个值&gt;</span>
                        <ChevronDown
                          class="h-3 w-3 transition-transform"
                          :class="{ 'rotate-180': expandedField === state.key }"
                        />
                      </button>
                      <!-- 值分布 -->
                      <div v-if="expandedField === state.key" class="mt-2 space-y-1">
                        <div
                          v-for="d in state.distribution"
                          :key="d.value"
                          class="flex items-center justify-between gap-2 rounded bg-secondary/40 px-2 py-1 text-xs"
                        >
                          <span class="truncate text-foreground" :title="d.value">
                            {{ d.value || '(空)' }}
                          </span>
                          <Badge variant="secondary" class="shrink-0">{{ d.count }} 首</Badge>
                        </div>
                      </div>
                    </div>
                  </template>
                </div>

                <!-- 状态标记 -->
                <Badge
                  v-if="editingField !== state.key"
                  :variant="state.common ? 'default' : 'secondary'"
                  class="shrink-0"
                >
                  {{ state.common ? '公共' : '差异' }}
                </Badge>
                <Badge v-else variant="outline" class="shrink-0 border-primary text-primary">
                  编辑中
                </Badge>

                <!-- 行内操作 -->
                <div class="flex shrink-0 items-center gap-1">
                  <template v-if="editingField === state.key">
                    <Button
                      size="sm"
                      :disabled="applying"
                      @click="onApply"
                    >
                      <Check class="h-3.5 w-3.5" />
                      保存
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      :disabled="applying"
                      @click="cancelEdit"
                    >
                      <X class="h-3.5 w-3.5" />
                    </Button>
                  </template>
                  <template v-else>
                    <Button
                      size="sm"
                      variant="ghost"
                      @click="startEdit(state.key, state.value)"
                    >
                      <Pencil class="h-3.5 w-3.5" />
                    </Button>
                  </template>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        <!-- 编辑预览提示 -->
        <div
          v-if="editingField"
          class="flex items-center gap-2 rounded-md border border-primary/30 bg-primary/5 px-3 py-2 text-xs text-muted-foreground"
        >
          <RefreshCw class="h-3.5 w-3.5 text-primary" />
          <span>
            将更新 <span class="font-semibold text-primary">{{ tracks.length }}</span> 首曲目的
            「{{ currentFieldLabel }}」字段
            <template v-if="form.value">
              ，其中
              <span class="font-semibold text-foreground">{{ changedCount }}</span> 首值会变化
            </template>
          </span>
        </div>
      </template>

      <DialogFooter>
        <Button variant="ghost" @click="close">关闭</Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>
