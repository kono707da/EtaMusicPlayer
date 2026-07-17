import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import { Howl } from 'howler'
import { useToast } from '@/components/ui/toast/use-toast'
import { useNodesStore } from './nodes'
import { getStreamUrl, reportPlayEvent } from '../api/node'

const toast = useToast()

/**
 * 上报播放事件到节点（静默失败，不阻塞播放）
 */
function _reportPlay(nodeId, trackId, eventType) {
  const nodesStore = useNodesStore()
  const node = nodesStore.nodes.find((n) => n.id === nodeId)
  if (!node || !node.token) return
  reportPlayEvent(node, { track_id: trackId, event_type: eventType })
    .catch(() => { /* 静默失败 */ })
}

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
  const volume = ref((() => {
    const v = parseFloat(localStorage.getItem('etamusic_volume'))
    return isNaN(v) ? 0.8 : Math.min(1, Math.max(0, v))
  })()) // 0~1，从 localStorage 恢复
  const loading = ref(false)

  let howl = null

  // 音量变化时持久化到 localStorage
  watch(volume, (v) => {
    localStorage.setItem('etamusic_volume', String(v))
  })

  const current = computed(() =>
    currentIndex.value >= 0 ? queue.value[currentIndex.value] : null
  )

  const currentTrack = computed(() => current.value?.track || null)
  const currentNodeName = computed(() => current.value?.nodeName || '')

  /**
   * 加载并播放当前曲目
   * 支持跨节点：每条曲目自带 __nodeId / __nodeName
   */
  function loadCurrent() {
    if (!current.value) return
    const nodesStore = useNodesStore()
    const nodeId = current.value.nodeId
    const node = nodesStore.getNode(nodeId)
    if (!node || !node.token) {
      // 节点不可用：标记停止，由用户手动跳过（避免自动跳过递归）
      toast.error(`节点「${node?.name || nodeId}」不可用，无法播放`)
      isPlaying.value = false
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
        // 上报 play 事件
        _reportPlay(current.value.nodeId, current.value.track.id, 'play')
      },
      onpause() {
        isPlaying.value = false
      },
      onend() {
        // 上报 complete 事件
        _reportPlay(current.value.nodeId, current.value.track.id, 'complete')
        // 自动播放下一首
        if (currentIndex.value < queue.value.length - 1) {
          currentIndex.value++
          loadCurrent()
        } else {
          isPlaying.value = false
        }
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
   * 跨节点：每条曲目自带 __nodeId / __nodeName
   * @param {Array} tracks 曲目数组
   * @param {Number} startIndex 从第几首开始播放
   */
  function playTracks(tracks, startIndex = 0) {
    if (!tracks || tracks.length === 0) return
    queue.value = tracks.map((t) => ({
      track: t,
      nodeId: t.__nodeId,
      nodeName: t.__nodeName || ''
    }))
    currentIndex.value = startIndex
    loadCurrent()
  }

  /**
   * 追加到队列末尾（不切换播放）
   * 跨节点：每条曲目自带 __nodeId / __nodeName
   */
  function appendTracks(tracks) {
    const items = tracks.map((t) => ({
      track: t,
      nodeId: t.__nodeId,
      nodeName: t.__nodeName || ''
    }))
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
    // 如果当前曲目正在播放（非自然结束），上报 skip 事件
    if (current.value && isPlaying.value) {
      _reportPlay(current.value.nodeId, current.value.track.id, 'skip')
    }
    if (currentIndex.value < queue.value.length - 1) {
      currentIndex.value++
      loadCurrent()
    } else {
      // 队列末尾
      isPlaying.value = false
    }
  }

  function prev() {
    if (current.value && isPlaying.value) {
      _reportPlay(current.value.nodeId, current.value.track.id, 'skip')
    }
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

  /**
   * 1.2.1：从播放队列移除指定曲目（删除文件后调用）
   * - 队列内匹配 (nodeId, trackId) 的条目全部移除（理论上唯一，但保险起见全部清理）
   * - 若移除的是当前播放曲目：自动切换到下一首；若已是最后一首则停止
   * - 若移除的在当前之前：currentIndex 前移
   * - 若移除的在当前之后：currentIndex 不变
   * @param {Number} nodeId 节点 ID（数字）
   * @param {Number} trackId 曲目 ID
   */
  function removeTrack(nodeId, trackId) {
    if (!queue.value.length) return
    const oldIndex = currentIndex.value
    // 收集所有要删除的索引
    const removeIndices = new Set()
    queue.value.forEach((item, idx) => {
      if (item.nodeId === nodeId && item.track?.id === trackId) {
        removeIndices.add(idx)
      }
    })
    if (removeIndices.size === 0) return

    // 计算新队列
    const newQueue = queue.value.filter((_, idx) => !removeIndices.has(idx))
    const removedBeforeCurrent = Array.from(removeIndices).filter(
      (i) => i < oldIndex
    ).length
    const currentRemoved = removeIndices.has(oldIndex)
    const newLen = newQueue.length

    queue.value = newQueue

    if (newLen === 0) {
      // 队列清空
      if (howl) {
        howl.unload()
        howl = null
      }
      currentIndex.value = -1
      isPlaying.value = false
      progress.value = 0
      duration.value = 0
      return
    }

    if (currentRemoved) {
      // 当前播放曲目被删除：切到原 currentIndex 在新队列中的位置
      // 若原 currentIndex 已超出新队列范围，取最后一首
      const newIndex = Math.min(oldIndex - removedBeforeCurrent, newLen - 1)
      currentIndex.value = Math.max(0, newIndex)
      // 重新加载播放（不再上报 skip 事件，因为是删除触发的）
      loadCurrent()
    } else if (removedBeforeCurrent > 0) {
      // 当前未删除，但前面被删了一些，需要前移
      currentIndex.value = oldIndex - removedBeforeCurrent
    }
    // 若删除在当前之后：currentIndex 不变
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
    clearQueue,
    removeTrack
  }
})
