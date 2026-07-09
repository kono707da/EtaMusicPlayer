import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { Howl } from 'howler'
import { useToast } from '@/components/ui/toast/use-toast'
import { useNodesStore } from './nodes'
import { getStreamUrl } from '../api/node'

const toast = useToast()

/**
 * 播放器状态
 * - 当前播放队列
 * - 当前曲目索引
 * - 播放/暂停状态
 * - 进度、音量
 * - 当前播放来源节点名称（标注来源）
 */
export const usePlayerStore = defineStore('player', () => {
  const queue = ref([]) // [{track, nodeId, nodeName}]
  const currentIndex = ref(-1)
  const isPlaying = ref(false)
  const progress = ref(0) // 秒
  const duration = ref(0) // 秒
  const volume = ref(0.8) // 0~1
  const loading = ref(false)

  let howl = null

  const current = computed(() =>
    currentIndex.value >= 0 ? queue.value[currentIndex.value] : null
  )

  const currentTrack = computed(() => current.value?.track || null)
  const currentNodeName = computed(() => current.value?.nodeName || '')

  /**
   * 加载并播放当前曲目
   */
  function loadCurrent() {
    if (!current.value) return
    const nodesStore = useNodesStore()
    const node = nodesStore.nodes.find((n) => n.id === current.value.nodeId)
    if (!node) {
      toast.error('找不到来源节点')
      return
    }
    const url = getStreamUrl(node, current.value.track.id)
    if (howl) {
      howl.unload()
      howl = null
    }
    loading.value = true
    howl = new Howl({
      src: [url],
      format: ['mp3', 'flac', 'wav', 'ogg', 'm4a'],
      html5: true,
      volume: volume.value,
      onload() {
        duration.value = howl.duration()
        loading.value = false
      },
      onplay() {
        isPlaying.value = true
      },
      onpause() {
        isPlaying.value = false
      },
      onend() {
        next()
      },
      onloaderror() {
        loading.value = false
        toast.error('音频加载失败')
      },
      onplayerror() {
        loading.value = false
        toast.error('播放失败')
      }
    })
    howl.play()
  }

  /**
   * 将一组曲目加入播放队列（替换队列）并播放
   * @param {Array} tracks 曲目数组
   * @param {Number} nodeId 来源节点 id
   * @param {String} nodeName 来源节点名称
   * @param {Number} startIndex 从第几首开始播放
   */
  function playTracks(tracks, nodeId, nodeName, startIndex = 0) {
    if (!tracks || tracks.length === 0) return
    queue.value = tracks.map((t) => ({ track: t, nodeId, nodeName }))
    currentIndex.value = startIndex
    loadCurrent()
  }

  /**
   * 追加到队列末尾（不切换播放）
   */
  function appendTracks(tracks, nodeId, nodeName) {
    const items = tracks.map((t) => ({ track: t, nodeId, nodeName }))
    queue.value.push(...items)
    if (currentIndex.value < 0 && queue.value.length > 0) {
      currentIndex.value = 0
      loadCurrent()
    }
  }

  function play() {
    if (howl) howl.play()
  }

  function pause() {
    if (howl) howl.pause()
  }

  function toggle() {
    if (isPlaying.value) pause()
    else play()
  }

  function next() {
    if (currentIndex.value < queue.value.length - 1) {
      currentIndex.value++
      loadCurrent()
    } else {
      // 队列末尾
      isPlaying.value = false
    }
  }

  function prev() {
    if (currentIndex.value > 0) {
      currentIndex.value--
      loadCurrent()
    }
  }

  /**
   * 跳转播放队列指定索引
   */
  function jumpTo(index) {
    if (index < 0 || index >= queue.value.length) return
    currentIndex.value = index
    loadCurrent()
  }

  /**
   * seek
   * @param {Number} seconds 目标秒数
   */
  function seek(seconds) {
    if (howl) {
      howl.seek(seconds)
      progress.value = seconds
    }
  }

  /**
   * 进度轮询：从 Howl 实例读取当前播放进度
   * 供播放器组件定时调用（html5 模式下没有逐帧回调）
   */
  function tick() {
    if (howl && isPlaying.value) {
      progress.value = howl.seek() || 0
    }
  }

  function setVolume(v) {
    volume.value = v
    if (howl) howl.volume(v)
  }

  /**
   * 清空队列
   */
  function clearQueue() {
    if (howl) {
      howl.unload()
      howl = null
    }
    queue.value = []
    currentIndex.value = -1
    isPlaying.value = false
    progress.value = 0
    duration.value = 0
  }

  return {
    queue,
    currentIndex,
    isPlaying,
    progress,
    duration,
    volume,
    loading,
    current,
    currentTrack,
    currentNodeName,
    playTracks,
    appendTracks,
    play,
    pause,
    toggle,
    next,
    prev,
    jumpTo,
    seek,
    tick,
    setVolume,
    clearQueue
  }
})
