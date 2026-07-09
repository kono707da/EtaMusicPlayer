<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { SkipBack, Play, Pause, SkipForward, ListMusic, Volume2, X } from 'lucide-vue-next'
import { Slider } from '@/components/ui/slider'
import { usePlayerStore } from '../stores/player'

const player = usePlayerStore()

// 进度条拖动状态
const seeking = ref(false)
const seekValue = ref(0)

const displayProgress = computed(() => {
  if (seeking.value) return (seekValue.value / 100) * player.duration
  return player.progress
})

const progressPercent = computed(() => {
  if (!player.duration) return 0
  return Math.min(100, (displayProgress.value / player.duration) * 100)
})

// Slider 用数组 modelValue
const progressModel = computed({
  get: () => [progressPercent.value],
  set: (v) => {
    const val = Array.isArray(v) ? v[0] : v
    if (seeking.value) {
      seekValue.value = val
    }
  }
})

const volumePercent = computed(() => Math.round(player.volume * 100))
const volumeModel = computed({
  get: () => [volumePercent.value],
  set: (v) => {
    const val = Array.isArray(v) ? v[0] : v
    player.setVolume(val / 100)
  }
})

const coverUrl = computed(() => {
  const t = player.currentTrack
  return t?.cover_url || t?.coverUrl || t?.album_cover || ''
})

function onSeekStart() {
  seeking.value = true
  seekValue.value = progressPercent.value
}
function onSeekEnd(v) {
  const val = Array.isArray(v) ? v[0] : v
  const target = (val / 100) * player.duration
  player.seek(target)
  seeking.value = false
}

function formatTime(sec) {
  if (!sec || isNaN(sec)) return '00:00'
  const m = Math.floor(sec / 60)
  const s = Math.floor(sec % 60)
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}

// 队列面板
const queueVisible = ref(false)
function toggleQueue() {
  queueVisible.value = !queueVisible.value
}
function onQueueItemClick(index) {
  player.jumpTo(index)
}

// 轮询进度
let timer = null
function startTimer() {
  stopTimer()
  timer = setInterval(() => {
    if (player.isPlaying && !seeking.value) {
      player.tick()
    }
  }, 500)
}
function stopTimer() {
  if (timer) {
    clearInterval(timer)
    timer = null
  }
}

onMounted(() => startTimer())
onBeforeUnmount(() => stopTimer())
</script>

<template>
  <div class="flex h-full items-center gap-5 px-6">
    <!-- 左：曲目信息 -->
    <div class="flex w-64 shrink-0 items-center gap-3 overflow-hidden">
      <div class="flex h-14 w-14 shrink-0 items-center justify-center overflow-hidden rounded-lg border border-border bg-secondary">
        <img v-if="coverUrl" :src="coverUrl" alt="cover" class="h-full w-full object-cover" />
        <ListMusic v-else class="h-5 w-5 text-muted-foreground" />
      </div>
      <div class="min-w-0 overflow-hidden">
        <div class="truncate text-sm font-semibold text-foreground" :title="player.currentTrack?.title || '未在播放'">
          {{ player.currentTrack?.title || '未在播放' }}
        </div>
        <div class="mt-0.5 flex items-center gap-2 overflow-hidden">
          <span class="truncate text-xs text-muted-foreground">{{ player.currentTrack?.artist || '—' }}</span>
          <span
            v-if="player.currentNodeName"
            class="shrink-0 rounded-full bg-primary/10 px-2 py-0.5 text-[10px] font-medium text-primary"
          >
            {{ player.currentNodeName }}
          </span>
        </div>
      </div>
    </div>

    <!-- 中：控制 + 进度 -->
    <div class="mx-auto flex max-w-2xl flex-1 flex-col items-center gap-1.5">
      <!-- 控制按钮 -->
      <div class="flex items-center gap-3">
        <button
          class="flex h-8 w-8 items-center justify-center rounded-full text-muted-foreground transition-colors hover:bg-accent hover:text-foreground disabled:opacity-30 disabled:hover:bg-transparent"
          :disabled="player.currentIndex <= 0"
          @click="player.prev()"
          title="上一首"
        >
          <SkipBack class="h-4 w-4" />
        </button>
        <button
          class="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-gold-400 to-gold-600 text-black shadow-gold-glow transition-transform hover:scale-105"
          @click="player.toggle()"
          :title="player.isPlaying ? '暂停' : '播放'"
        >
          <Pause v-if="player.isPlaying" class="h-5 w-5" />
          <Play v-else class="ml-0.5 h-5 w-5" />
        </button>
        <button
          class="flex h-8 w-8 items-center justify-center rounded-full text-muted-foreground transition-colors hover:bg-accent hover:text-foreground disabled:opacity-30 disabled:hover:bg-transparent"
          :disabled="player.currentIndex >= player.queue.length - 1"
          @click="player.next()"
          title="下一首"
        >
          <SkipForward class="h-4 w-4" />
        </button>
      </div>
      <!-- 进度条 -->
      <div class="flex w-full items-center gap-2.5">
        <span class="w-9 shrink-0 text-right text-[11px] tabular-nums text-muted-foreground">
          {{ formatTime(displayProgress) }}
        </span>
        <Slider
          v-model="progressModel"
          :max="100"
          :step="0.1"
          class="flex-1"
          @pointerdown="onSeekStart"
          @value-commit="onSeekEnd"
        />
        <span class="w-9 shrink-0 text-[11px] tabular-nums text-muted-foreground">
          {{ formatTime(player.duration) }}
        </span>
      </div>
    </div>

    <!-- 右：队列 + 音量 -->
    <div class="flex w-44 shrink-0 items-center justify-end gap-2.5">
      <button
        class="flex h-8 w-8 items-center justify-center rounded-full text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
        :class="{ 'text-primary': queueVisible }"
        @click="toggleQueue"
        title="播放队列"
      >
        <ListMusic class="h-4 w-4" />
      </button>
      <Volume2 class="h-4 w-4 text-muted-foreground" />
      <Slider v-model="volumeModel" :max="100" class="w-20" />
    </div>

    <!-- 播放队列面板（右侧滑出） -->
    <Transition name="slide-fade">
      <div
        v-if="queueVisible"
        class="fixed bottom-[88px] right-0 top-16 z-40 w-80 border-l border-border bg-popover/95 shadow-glass backdrop-blur-xl"
      >
        <div class="flex items-center justify-between border-b border-border px-4 py-3">
          <span class="text-sm font-semibold text-foreground">播放队列</span>
          <button class="text-muted-foreground transition-colors hover:text-foreground" @click="queueVisible = false">
            <X class="h-4 w-4" />
          </button>
        </div>
        <div class="h-[calc(100%-49px)] overflow-auto">
          <div
            v-for="(item, idx) in player.queue"
            :key="idx"
            class="flex cursor-pointer items-center gap-3 border-b border-border/50 px-4 py-2.5 transition-colors hover:bg-accent"
            :class="{ 'bg-primary/10': idx === player.currentIndex }"
            @click="onQueueItemClick(idx)"
          >
            <span class="w-5 shrink-0 text-xs tabular-nums" :class="idx === player.currentIndex ? 'text-primary' : 'text-muted-foreground'">
              {{ idx + 1 }}
            </span>
            <div class="min-w-0 flex-1">
              <div class="truncate text-xs font-medium" :class="idx === player.currentIndex ? 'text-primary' : 'text-foreground'">
                {{ item.track?.title || '—' }}
              </div>
              <div class="truncate text-[11px] text-muted-foreground">
                {{ item.track?.artist || '—' }}
              </div>
            </div>
            <span class="shrink-0 rounded-full bg-secondary px-1.5 py-0.5 text-[9px] text-muted-foreground">
              {{ item.nodeName }}
            </span>
          </div>
          <div v-if="player.queue.length === 0" class="py-12 text-center text-xs text-muted-foreground">
            队列为空
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
/* 队列滑出动画 */
.slide-fade-enter-active,
.slide-fade-leave-active {
  transition: all 0.25s ease;
}
.slide-fade-enter-from,
.slide-fade-leave-to {
  transform: translateX(100%);
  opacity: 0;
}

/* 进度条/音量条：更细的金色轨道 */
:deep([data-radix-slider-root]) {
  height: 6px;
}
:deep(.reka-slider__track),
:deep([data-radix-slider-track]) {
  height: 4px;
  background: hsl(0 0% 18%);
  border-radius: 999px;
}
:deep(.reka-slider__range),
:deep([data-radix-slider-range]) {
  background: hsl(46 74% 52%);
  border-radius: 999px;
}
:deep(.reka-slider__thumb),
:deep([data-radix-slider-thumb]) {
  width: 12px;
  height: 12px;
  border: 2px solid hsl(46 74% 52%);
  background: hsl(46 74% 52%);
  box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.3);
}
</style>
