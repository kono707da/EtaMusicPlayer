<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useToast } from '@/components/ui/toast/use-toast'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Switch } from '@/components/ui/switch'
import { Empty } from '@/components/ui/empty'
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
  Save,
  Search,
  Check,
  Square,
  Inbox
} from 'lucide-vue-next'
import { useNodesStore } from '../stores/nodes'
import {
  getDedupConfig,
  updateDedupConfig,
  detectDuplicates
} from '../api/node'

const nodesStore = useNodesStore()
const toast = useToast()

// 去重可用字段（与后端 DEDUP_FIELDS_AVAILABLE 对齐）
const fieldOptions = [
  { label: '标题', value: 'title' },
  { label: '专辑', value: 'album' },
  { label: '艺术家', value: 'artist' },
  { label: '时长', value: 'duration' },
  { label: '文件大小', value: 'file_size' },
  { label: '文件指纹 (hash)', value: 'file_hash' }
]

const form = reactive({
  fields: ['title', 'album', 'artist', 'duration', 'file_size'],
  duration_tolerance: 1.0,
  enabled: true
})

const configLoading = ref(false)
const savingConfig = ref(false)
const detecting = ref(false)
const groups = ref([]) // 重复组
const selectedGroup = ref(null)

function toggleField(v) {
  const idx = form.fields.indexOf(v)
  if (idx > -1) form.fields.splice(idx, 1)
  else form.fields.push(v)
}

async function loadConfig() {
  const node = nodesStore.activeNode
  if (!node) return
  configLoading.value = true
  try {
    const data = await getDedupConfig(node)
    form.fields = data.fields || form.fields
    form.duration_tolerance = data.duration_tolerance ?? 1.0
    form.enabled = data.enabled ?? true
  } catch (e) {
    /* 静默，使用默认值 */
  } finally {
    configLoading.value = false
  }
}

async function onSaveConfig() {
  const node = nodesStore.activeNode
  savingConfig.value = true
  try {
    await updateDedupConfig(node, {
      fields: form.fields,
      duration_tolerance: Number(form.duration_tolerance),
      enabled: form.enabled
    })
    toast.success('配置已保存')
  } catch (e) {
    toast.error('保存失败', e.response?.data?.detail || e.message, e)
  } finally {
    savingConfig.value = false
  }
}

async function onDetect() {
  if (form.fields.length === 0) {
    toast.warning('请至少选择一个比对字段')
    return
  }
  const node = nodesStore.activeNode
  detecting.value = true
  try {
    // 后端 POST /api/dedup/detect 无 body，使用当前已保存的配置
    const data = await detectDuplicates(node)
    groups.value = Array.isArray(data) ? data : data.items || []
    toast.success(`检测完成，共 ${groups.value.length} 组重复`)
  } catch (e) {
    toast.error('检测失败', e.response?.data?.detail || e.message, e)
  } finally {
    detecting.value = false
  }
}

function viewGroup(g) {
  selectedGroup.value = g
}

function keepTrack(track) {
  toast.info('保留', `${track.title}（实际删除需在文件管理中操作）`)
}

onMounted(() => {
  loadConfig()
})
</script>

<template>
  <div class="space-y-6">
    <div>
      <h2 class="text-2xl font-bold tracking-tight">去重检测</h2>
    </div>

    <!-- 去重配置 -->
    <Card>
      <CardHeader>
        <CardTitle>去重配置</CardTitle>
      </CardHeader>
      <CardContent class="space-y-5">
        <div
          v-if="configLoading"
          class="flex items-center gap-2 text-sm text-muted-foreground"
        >
          <Loader2 class="h-4 w-4 animate-spin" />
          加载配置中...
        </div>
        <template v-else>
          <!-- 比对字段：手写复选框列表 -->
          <div class="space-y-2">
            <Label>比对字段</Label>
            <div class="grid grid-cols-2 sm:grid-cols-3 gap-2">
              <button
                v-for="f in fieldOptions"
                :key="f.value"
                type="button"
                class="flex items-center gap-2 rounded-md border px-3 py-2 text-sm transition-colors"
                :class="
                  form.fields.includes(f.value)
                    ? 'border-primary bg-primary/10 text-primary'
                    : 'border-border bg-background text-foreground hover:bg-accent/50'
                "
                @click="toggleField(f.value)"
              >
                <component
                  :is="form.fields.includes(f.value) ? Check : Square"
                  class="h-4 w-4"
                />
                <span>{{ f.label }}</span>
              </button>
            </div>
          </div>

          <!-- 时长容差 + 启用 -->
          <div class="flex flex-wrap items-end gap-6">
            <div class="flex flex-col gap-1.5">
              <Label>时长容差(秒)</Label>
              <input
                v-model.number="form.duration_tolerance"
                type="number"
                min="0"
                step="0.5"
                class="flex h-10 w-32 rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
              />
            </div>
            <div class="flex items-center gap-2 pb-2">
              <Switch v-model:checked="form.enabled" id="dedup-enabled" />
              <Label for="dedup-enabled" class="cursor-pointer">启用去重</Label>
            </div>
          </div>

          <!-- 操作 -->
          <div class="flex gap-2">
            <Button variant="secondary" :disabled="savingConfig" @click="onSaveConfig">
              <Loader2 v-if="savingConfig" class="h-4 w-4 animate-spin" />
              <Save v-else class="h-4 w-4" />
              保存配置
            </Button>
            <Button :disabled="detecting" @click="onDetect">
              <Loader2 v-if="detecting" class="h-4 w-4 animate-spin" />
              <Search v-else class="h-4 w-4" />
              开始检测
            </Button>
          </div>
        </template>
      </CardContent>
    </Card>

    <!-- 检测结果：左右两栏 -->
    <div class="grid grid-cols-12 gap-4">
      <!-- 左：重复组列表 -->
      <Card class="col-span-12 lg:col-span-5">
        <CardHeader>
          <CardTitle>重复组（{{ groups.length }}）</CardTitle>
        </CardHeader>
        <CardContent>
          <Empty
            v-if="groups.length === 0"
            :icon="Inbox"
            title="尚未检测"
            description="点击「开始检测」查找重复曲目"
          />
          <Table v-else>
            <TableHeader>
              <TableRow class="hover:bg-transparent">
                <TableHead class="w-12">#</TableHead>
                <TableHead class="min-w-[200px]">匹配键</TableHead>
                <TableHead class="w-20 text-right">数量</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              <TableRow
                v-for="(g, i) in groups"
                :key="i"
                class="cursor-pointer"
                :class="{
                  'bg-accent/60':
                    selectedGroup && selectedGroup.group_key === g.group_key
                }"
                @click="viewGroup(g)"
              >
                <TableCell class="text-muted-foreground">{{ i + 1 }}</TableCell>
                <TableCell class="font-medium text-foreground truncate max-w-[220px]">
                  {{ g.group_key }}
                </TableCell>
                <TableCell class="text-right text-foreground">
                  {{ g.tracks?.length || g.track_ids?.length || 0 }}
                </TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <!-- 右：组内曲目 -->
      <Card class="col-span-12 lg:col-span-7">
        <CardHeader>
          <CardTitle>组内曲目</CardTitle>
        </CardHeader>
        <CardContent>
          <Empty
            v-if="!selectedGroup"
            :icon="Inbox"
            title="请选择左侧重复组"
            description="点击任一重复组查看组内曲目"
          />
          <Table v-else>
            <TableHeader>
              <TableRow class="hover:bg-transparent">
                <TableHead class="min-w-[160px]">标题</TableHead>
                <TableHead class="min-w-[120px]">艺术家</TableHead>
                <TableHead class="w-24">码率</TableHead>
                <TableHead class="w-20">格式</TableHead>
                <TableHead class="min-w-[200px]">路径</TableHead>
                <TableHead class="w-20 text-right">操作</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              <TableRow
                v-for="(track, i) in selectedGroup.tracks || []"
                :key="i"
              >
                <TableCell class="font-medium text-foreground">{{ track.title }}</TableCell>
                <TableCell class="text-foreground">{{ track.artist }}</TableCell>
                <TableCell class="text-muted-foreground">{{ track.bitrate }}</TableCell>
                <TableCell class="text-muted-foreground">{{ track.ext }}</TableCell>
                <TableCell class="text-muted-foreground truncate max-w-[220px]" :title="track.abs_path">
                  {{ track.abs_path }}
                </TableCell>
                <TableCell class="text-right">
                  <Button variant="ghost" size="sm" @click="keepTrack(track)">
                    <Check class="h-3.5 w-3.5" />
                    保留
                  </Button>
                </TableCell>
              </TableRow>
              <TableRow v-if="(selectedGroup.tracks || []).length === 0" class="hover:bg-transparent">
                <TableCell colspan="6" class="text-center text-muted-foreground py-6">
                  该组无曲目数据
                </TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  </div>
</template>
