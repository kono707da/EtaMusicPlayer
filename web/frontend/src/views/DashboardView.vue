<script setup>
import { ref, onMounted, computed } from 'vue'
import { useToast } from '@/components/ui/toast/use-toast'
import { Button } from '@/components/ui/button'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import {
  Table, TableHeader, TableBody, TableRow, TableHead, TableCell
} from '@/components/ui/table'
import {
  RefreshCw, Loader2, Music, Play, SkipForward, CheckCircle,
  TrendingUp, Calendar, Users, Clock
} from 'lucide-vue-next'
import { useNodesStore } from '../stores/nodes'
import { getDashboard } from '../api/node'

const nodesStore = useNodesStore()
const toast = useToast()

const dashboard = ref(null)
const loading = ref(false)

async function loadDashboard() {
  const node = nodesStore.activeNode
  if (!node || !node.token) return
  loading.value = true
  try {
    dashboard.value = await getDashboard(node)
  } catch (e) {
    toast.error('加载看板数据失败', e.message || String(e), e)
  } finally {
    loading.value = false
  }
}

function formatTime(iso) {
  if (!iso) return '—'
  const d = new Date(iso)
  return d.toLocaleString('zh-CN', { hour12: false })
}

onMounted(() => loadDashboard())
</script>

<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <h2 class="text-xl font-bold text-foreground">数据看板</h2>
      <Button variant="outline" size="sm" :disabled="loading" @click="loadDashboard">
        <RefreshCw v-if="!loading" class="mr-2 h-4 w-4" />
        <Loader2 v-else class="mr-2 h-4 w-4 animate-spin" />
        刷新
      </Button>
    </div>

    <div v-if="!dashboard && loading" class="py-20 text-center text-muted-foreground">
      <Loader2 class="mx-auto mb-3 h-8 w-8 animate-spin" />
      加载中...
    </div>

    <template v-if="dashboard">
      <!-- 统计卡片 -->
      <div class="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <Card class="border-border bg-card/60">
          <CardContent class="pt-5">
            <div class="flex items-center gap-3">
              <div class="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                <Music class="h-5 w-5 text-primary" />
              </div>
              <div>
                <div class="text-2xl font-bold text-foreground">{{ dashboard.total_tracks }}</div>
                <div class="text-xs text-muted-foreground">总曲目数</div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card class="border-border bg-card/60">
          <CardContent class="pt-5">
            <div class="flex items-center gap-3">
              <div class="flex h-10 w-10 items-center justify-center rounded-lg bg-green-500/10">
                <Play class="h-5 w-5 text-green-400" />
              </div>
              <div>
                <div class="text-2xl font-bold text-foreground">{{ dashboard.total_play_count }}</div>
                <div class="text-xs text-muted-foreground">总播放次数</div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card class="border-border bg-card/60">
          <CardContent class="pt-5">
            <div class="flex items-center gap-3">
              <div class="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-500/10">
                <CheckCircle class="h-5 w-5 text-blue-400" />
              </div>
              <div>
                <div class="text-2xl font-bold text-foreground">{{ dashboard.total_complete_count }}</div>
                <div class="text-xs text-muted-foreground">总完成次数</div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card class="border-border bg-card/60">
          <CardContent class="pt-5">
            <div class="flex items-center gap-3">
              <div class="flex h-10 w-10 items-center justify-center rounded-lg bg-yellow-500/10">
                <SkipForward class="h-5 w-5 text-yellow-400" />
              </div>
              <div>
                <div class="text-2xl font-bold text-foreground">{{ dashboard.total_skip_count }}</div>
                <div class="text-xs text-muted-foreground">总跳过次数</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <!-- 入库统计 -->
      <div class="grid grid-cols-2 gap-4">
        <Card class="border-border bg-card/60">
          <CardContent class="pt-5">
            <div class="flex items-center gap-3">
              <div class="flex h-10 w-10 items-center justify-center rounded-lg bg-purple-500/10">
                <Calendar class="h-5 w-5 text-purple-400" />
              </div>
              <div>
                <div class="text-2xl font-bold text-foreground">{{ dashboard.tracks_imported_today }}</div>
                <div class="text-xs text-muted-foreground">今日入库</div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card class="border-border bg-card/60">
          <CardContent class="pt-5">
            <div class="flex items-center gap-3">
              <div class="flex h-10 w-10 items-center justify-center rounded-lg bg-cyan-500/10">
                <TrendingUp class="h-5 w-5 text-cyan-400" />
              </div>
              <div>
                <div class="text-2xl font-bold text-foreground">{{ dashboard.tracks_imported_this_week }}</div>
                <div class="text-xs text-muted-foreground">本周入库</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <!-- 热门曲目 + 活跃用户 -->
      <div class="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <!-- 热门曲目 -->
        <Card class="border-border bg-card/60">
          <CardHeader>
            <CardTitle class="flex items-center gap-2 text-base">
              <TrendingUp class="h-4 w-4 text-primary" />
              热门曲目 Top 10
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead class="w-10">#</TableHead>
                  <TableHead>曲目</TableHead>
                  <TableHead class="w-20 text-right">播放</TableHead>
                  <TableHead class="w-20 text-right">完成</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                <TableRow v-for="(track, idx) in dashboard.top_played_tracks" :key="track.track_id">
                  <TableCell class="text-xs text-muted-foreground">{{ idx + 1 }}</TableCell>
                  <TableCell>
                    <div class="truncate text-sm font-medium">{{ track.title || '—' }}</div>
                    <div class="truncate text-xs text-muted-foreground">{{ track.artist || '—' }}</div>
                  </TableCell>
                  <TableCell class="text-right text-sm">{{ track.play_count }}</TableCell>
                  <TableCell class="text-right text-sm text-muted-foreground">{{ track.complete_count }}</TableCell>
                </TableRow>
                <TableRow v-if="!dashboard.top_played_tracks?.length">
                  <TableCell :colspan="4" class="py-8 text-center text-sm text-muted-foreground">暂无播放记录</TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </CardContent>
        </Card>

        <!-- 活跃用户 -->
        <Card class="border-border bg-card/60">
          <CardHeader>
            <CardTitle class="flex items-center gap-2 text-base">
              <Users class="h-4 w-4 text-primary" />
              活跃用户 Top 5
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead class="w-10">#</TableHead>
                  <TableHead>用户</TableHead>
                  <TableHead class="w-20 text-right">播放</TableHead>
                  <TableHead class="w-20 text-right">完成</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                <TableRow v-for="(user, idx) in dashboard.active_users" :key="idx">
                  <TableCell class="text-xs text-muted-foreground">{{ idx + 1 }}</TableCell>
                  <TableCell class="text-sm font-medium">{{ user.username || '—' }}</TableCell>
                  <TableCell class="text-right text-sm">{{ user.play_count }}</TableCell>
                  <TableCell class="text-right text-sm text-muted-foreground">{{ user.complete_count }}</TableCell>
                </TableRow>
                <TableRow v-if="!dashboard.active_users?.length">
                  <TableCell :colspan="4" class="py-8 text-center text-sm text-muted-foreground">暂无活跃用户</TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>

      <!-- 最近播放 -->
      <Card class="border-border bg-card/60">
        <CardHeader>
          <CardTitle class="flex items-center gap-2 text-base">
            <Clock class="h-4 w-4 text-primary" />
            最近播放
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead class="w-40">时间</TableHead>
                <TableHead>曲目</TableHead>
                <TableHead>用户</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              <TableRow v-for="(play, idx) in dashboard.recent_plays" :key="idx">
                <TableCell class="text-xs text-muted-foreground">{{ formatTime(play.played_at) }}</TableCell>
                <TableCell class="text-sm">{{ play.title || '—' }}</TableCell>
                <TableCell class="text-sm text-muted-foreground">{{ play.username || '—' }}</TableCell>
              </TableRow>
              <TableRow v-if="!dashboard.recent_plays?.length">
                <TableCell :colspan="3" class="py-8 text-center text-sm text-muted-foreground">暂无播放记录</TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </template>
  </div>
</template>
