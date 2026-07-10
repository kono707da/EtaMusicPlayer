<script setup>
import { ref, onMounted } from 'vue'
import { useToast } from '@/components/ui/toast/use-toast'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '@/components/ui/card'
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
import { Loader2, TrendingUp, Search, Replace, Inbox, Sparkles } from 'lucide-vue-next'
import { useNodesStore } from '../stores/nodes'
import {
  getPlaylists,
  detectQualityUpgrades,
  applyQualityReplace
} from '../api/node'

const nodesStore = useNodesStore()
const toast = useToast()

const playlists = ref([])
const selectedPlaylistId = ref(null)
// 升级候选列表：每项 {current_track_id, candidates: [Track...], best_candidate_id}
const upgrades = ref([])
const selectedUpgrade = ref(null)
// 用户在候选详情里选中的"要替换成"的新曲目 id
const selectedNewTrackId = ref(null)
const detecting = ref(false)
const replacing = ref(false)

async function loadPlaylists() {
  const node = nodesStore.activeNode
  if (!node) return
  try {
    const data = await getPlaylists(node)
    playlists.value = Array.isArray(data) ? data : data.items || []
  } catch (e) {
    toast.error('获取播放列表失败', e.message || String(e), e)
  }
}

async function onDetect() {
  if (!selectedPlaylistId.value) {
    toast.warning('请选择播放列表')
    return
  }
  const node = nodesStore.activeNode
  detecting.value = true
  selectedUpgrade.value = null
  selectedNewTrackId.value = null
  try {
    const data = await detectQualityUpgrades(node, selectedPlaylistId.value)
    upgrades.value = Array.isArray(data) ? data : data.items || []
    toast.success(`检测完成，共 ${upgrades.value.length} 个升级候选`)
  } catch (e) {
    toast.error('检测失败', e.response?.data?.detail || e.message, e)
  } finally {
    detecting.value = false
  }
}

async function onReplace() {
  if (!selectedUpgrade.value) {
    toast.warning('请选择一个候选组')
    return
  }
  const newId = selectedNewTrackId.value || selectedUpgrade.value.best_candidate_id
  if (!newId) {
    toast.warning('请选择要替换成的高音质版本')
    return
  }
  const node = nodesStore.activeNode
  replacing.value = true
  try {
    await applyQualityReplace(
      node,
      selectedPlaylistId.value,
      selectedUpgrade.value.current_track_id,
      newId
    )
    toast.success('已替换')
    selectedUpgrade.value = null
    selectedNewTrackId.value = null
    await onDetect()
  } catch (e) {
    toast.error('替换失败', e.response?.data?.detail || e.message, e)
  } finally {
    replacing.value = false
  }
}

// 选中某个升级候选组（左侧列表点击）
function selectUpgrade(row) {
  selectedUpgrade.value = row
  selectedNewTrackId.value = null
}

// 在右侧候选详情里选中某条候选曲目
function selectCandidate(row) {
  selectedNewTrackId.value = row?.id ?? null
}

onMounted(() => {
  loadPlaylists()
})
</script>

<template>
  <div class="space-y-6">
    <div>
      <h2 class="text-2xl font-bold tracking-tight">音质升级检测</h2>
    </div>

    <!-- 顶部：选择播放列表 + 检测 -->
    <Card>
      <CardContent class="pt-6">
        <div class="flex flex-wrap items-end gap-4">
          <div class="flex flex-col gap-1.5">
            <Label>播放列表</Label>
            <Select v-model="selectedPlaylistId">
              <SelectTrigger class="w-72">
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
          <Button :disabled="detecting" @click="onDetect">
            <Loader2 v-if="detecting" class="h-4 w-4 animate-spin" />
            <Search v-else class="h-4 w-4" />
            检测升级候选
          </Button>
        </div>
      </CardContent>
    </Card>

    <!-- 检测结果：左右两栏 -->
    <div class="grid grid-cols-12 gap-4">
      <!-- 左：升级候选列表 -->
      <Card class="col-span-12 lg:col-span-5">
        <CardHeader>
          <CardTitle class="flex items-center gap-2">
            <TrendingUp class="h-4 w-4 text-primary" />
            升级候选（{{ upgrades.length }}）
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Empty
            v-if="upgrades.length === 0"
            :icon="Inbox"
            title="尚未检测"
            description="选择播放列表后点击「检测升级候选」"
          />
          <Table v-else>
            <TableHeader>
              <TableRow class="hover:bg-transparent">
                <TableHead class="w-32">当前曲目ID</TableHead>
                <TableHead class="w-32 text-right">高音质候选数</TableHead>
                <TableHead class="w-32">最佳候选ID</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              <TableRow
                v-for="(u, i) in upgrades"
                :key="i"
                class="cursor-pointer"
                :class="{
                  'bg-accent/60':
                    selectedUpgrade &&
                    selectedUpgrade.current_track_id === u.current_track_id
                }"
                @click="selectUpgrade(u)"
              >
                <TableCell class="font-medium text-foreground">
                  {{ u.current_track_id }}
                </TableCell>
                <TableCell class="text-right text-foreground">
                  {{ u.candidates?.length || 0 }}
                </TableCell>
                <TableCell class="text-muted-foreground">
                  {{ u.best_candidate_id || '—' }}
                </TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <!-- 右：候选详情 -->
      <Card class="col-span-12 lg:col-span-7">
        <CardHeader>
          <div class="flex items-center justify-between">
            <CardTitle>候选详情</CardTitle>
            <Button
              size="sm"
              :disabled="!selectedUpgrade || !selectedNewTrackId || replacing"
              @click="onReplace"
            >
              <Loader2 v-if="replacing" class="h-4 w-4 animate-spin" />
              <Replace v-else class="h-4 w-4" />
              替换为选中版本
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <Empty
            v-if="!selectedUpgrade"
            :icon="Inbox"
            title="请选择左侧候选"
            description="点击任一升级候选查看高音质版本"
          />
          <template v-else>
            <Table>
              <TableHeader>
                <TableRow class="hover:bg-transparent">
                  <TableHead class="w-12">选择</TableHead>
                  <TableHead class="min-w-[140px]">标题</TableHead>
                  <TableHead class="min-w-[100px]">艺术家</TableHead>
                  <TableHead class="w-24">码率</TableHead>
                  <TableHead class="w-20">格式</TableHead>
                  <TableHead class="w-24">音质分</TableHead>
                  <TableHead class="min-w-[180px]">路径</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                <TableRow
                  v-for="(track, i) in selectedUpgrade.candidates || []"
                  :key="i"
                  class="cursor-pointer"
                  :class="{
                    'bg-accent/60': selectedNewTrackId === track.id
                  }"
                  @click="selectCandidate(track)"
                >
                  <TableCell>
                    <button
                      type="button"
                      class="flex h-4 w-4 items-center justify-center rounded-full border-2 transition-colors"
                      :class="
                        selectedNewTrackId === track.id
                          ? 'border-primary bg-primary'
                          : 'border-border'
                      "
                      @click.stop="selectCandidate(track)"
                    >
                      <span
                        v-if="selectedNewTrackId === track.id"
                        class="h-1.5 w-1.5 rounded-full bg-primary-foreground"
                      ></span>
                    </button>
                  </TableCell>
                  <TableCell class="font-medium text-foreground">{{ track.title }}</TableCell>
                  <TableCell class="text-foreground">{{ track.artist }}</TableCell>
                  <TableCell class="text-muted-foreground">{{ track.bitrate }}</TableCell>
                  <TableCell class="text-muted-foreground">{{ track.ext }}</TableCell>
                  <TableCell>
                    <span
                      class="inline-flex items-center gap-1 text-foreground"
                      :class="{
                        'text-primary font-semibold':
                          track.id === selectedUpgrade.best_candidate_id
                      }"
                    >
                      <Sparkles
                        v-if="track.id === selectedUpgrade.best_candidate_id"
                        class="h-3 w-3"
                      />
                      {{ track.quality_score }}
                    </span>
                  </TableCell>
                  <TableCell
                    class="text-muted-foreground truncate max-w-[200px]"
                    :title="track.abs_path"
                  >
                    {{ track.abs_path }}
                  </TableCell>
                </TableRow>
                <TableRow
                  v-if="(selectedUpgrade.candidates || []).length === 0"
                  class="hover:bg-transparent"
                >
                  <TableCell colspan="7" class="text-center text-muted-foreground py-6">
                    无候选曲目
                  </TableCell>
                </TableRow>
              </TableBody>
            </Table>
            <div
              v-if="selectedUpgrade?.best_candidate_id"
              class="mt-3 flex items-center gap-1.5 text-xs text-muted-foreground"
            >
              <Sparkles class="h-3 w-3 text-primary" />
              系统推荐：{{ selectedUpgrade.best_candidate_id }}
            </div>
          </template>
        </CardContent>
        <CardFooter v-if="selectedUpgrade && !selectedNewTrackId" class="pt-0">
          <p class="text-xs text-muted-foreground">
            提示：从上方候选中点选一首作为替换目标，未选时将使用系统推荐。
          </p>
        </CardFooter>
      </Card>
    </div>
  </div>
</template>
