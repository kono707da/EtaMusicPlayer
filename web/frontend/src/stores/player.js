import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import { Howl } from 'howler'
import { useToast } from '@/components/ui/toast/use-toast'
import { useNodesStore } from './nodes'
import { getStreamUrl, reportPlayEvent, getPlaybackSettings } from '../api/node'

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

// ============ 播放完成判定配置缓存（1.2.3 新增） ============
// 节点端 GET /api/settings/playback 返回的配置，按 nodeId 缓存
// 老节点（<1.2.3）无此 API，拉取失败时用默认值兜底

const DEFAULT_PLAYBACK_SETTINGS = {
  duration_threshold_seconds: 900,   // 15 分钟
  music_complete_percent: 90,
  broadcast_complete_percent: 70
}

// nodeId → settings（已成功拉取）
const _settingsCache = new Map()
// nodeId → Promise（进行中，防并发重复请求）
const _settingsPending = new Map()

/**
 * 获取节点播放完成配置（带缓存， Promise）
 * 节点不可用或拉取失败时返回默认值
 */
function _getPlaybackSettings(nodeId) {
  if (_settingsCache.has(nodeId)) return Promise.resolve(_settingsCache.get(nodeId))
  if (_settingsPending.has(nodeId)) return _settingsPending.get(nodeId)

  const nodesStore = useNodesStore()
  const node = nodesStore.getNode(nodeId)
  if (!node || !node.token) {
    // 节点不可用，直接用默认值（不缓存，下次节点恢复时重试）
    return Promise.resolve(DEFAULT_PLAYBACK_SETTINGS)
  }

  const promise = getPlaybackSettings(node)
    .then((s) => {
      const settings = {
        duration_threshold_seconds: s.duration_threshold_seconds ?? DEFAULT_PLAYBACK_SETTINGS.duration_threshold_seconds,
        music_complete_percent: s.music_complete_percent ?? DEFAULT_PLAYBACK_SETTINGS.music_complete_percent,
        broadcast_complete_percent: s.broadcast_complete_percent ?? DEFAULT_PLAYBACK_SETTINGS.broadcast_complete_percent
      }
      _settingsCache.set(nodeId, settings)
      _settingsPending.delete(nodeId)
      return settings
    })
    .catch(() => {
      // 老节点无此 API 或网络错误，用默认值兜底（不缓存，下次重试）
      _settingsPending.delete(nodeId)
      return DEFAULT_PLAYBACK_SETTINGS
    })
  _settingsPending.set(nodeId, promise)
  return promise
}

/**
 * 清除节点配置缓存（用户在 NodesView 修改配置后调用，让下次播放重新拉取）
 */
function _invalidatePlaybackSettings(nodeId) {
  _settingsCache.delete(nodeId)
  _settingsPending.delete(nodeId)
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
  // 1.2.3：播放完成判定状态（非响应式，store 内部使用）
  let completeReported = false      // 当前曲目是否已上报过 complete
  let completeThresholdSec = 0      // 当前曲目的完成阈值（秒），0 表示未计算

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
   * 根据当前曲目时长和节点配置计算完成阈值（秒）
   * 异步：先取节点配置，再按时长判断属于音乐还是广播剧
   * 异步期间若已切歌则放弃更新
   */
  async function _updateCompleteThreshold() {
    const cur = current.value
    if (!cur || !duration.value) {
      completeThresholdSec = 0
      return
    }
    const nodeId = cur.nodeId
    const dur = duration.value
    const settings = await _getPlaybackSettings(nodeId)
    // 异步期间可能已切歌，校验仍是同一首
    if (!current.value || current.value.nodeId !== nodeId || current.value.track.id !== cur.track.id) {
      return
    }
    const percent = dur >= settings.duration_threshold_seconds
      ? settings.broadcast_complete_percent
      : settings.music_complete_percent
    completeThresholdSec = dur * percent / 100
  }

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
    // 重置完成判定状态
    completeReported = false
    completeThresholdSec = 0
    loading.value = true
    howl = new Howl({
      src: [url],
      format: ['mp3', 'flac', 'wav', 'ogg', 'm4a'],
      html5: true,
      volume: volume.value,
      onload() {
        duration.value = howl.duration()
        loading.value = false
        // 加载完成后计算完成阈值（异步，不阻塞播放）
        _updateCompleteThreshold()
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
        // 自然结束：兜底上报 complete（如果还没上报过）
        if (!completeReported) {
          completeReported = true
          _reportPlay(current.value.nodeId, current.value.track.id, 'complete')
        }
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
    // 1.2.3：仅当未上报 complete 时才上报 skip
    // （已上报 complete 后用户切歌不算 skip，避免广播剧听到 70% 后切走被记 skip）
    if (current.value && isPlaying.value && !completeReported) {
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
    if (current.value && isPlaying.value && !completeReported) {
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
    // 跳转视为切歌：若当前未完成且正在播放，上报 skip
    if (current.value && isPlaying.value && !completeReported && index !== currentIndex.value) {
      _reportPlay(current.value.nodeId, current.value.track.id, 'skip')
    }
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
      // seek 后由 tick() 检测是否达到完成阈值（不在这里直接触发，避免拖动进度条时误触发）
    }
  }

  /**
   * 进度轮询：从 Howl 实例读取当前播放进度
   * 供播放器组件定时调用（html5 模式下没有逐帧回调）
   * 1.2.3：同时检查是否达到播放完成阈值，达到则上报 complete（仅记统计，不切歌）
   */
  function tick() {
    if (howl && isPlaying.value) {
      progress.value = howl.seek() || 0
      // 达到完成阈值且未上报过：上报 complete（仅一次）
      if (!completeReported && completeThresholdSec > 0 && progress.value >= completeThresholdSec) {
        completeReported = true
        _reportPlay(current.value.nodeId, current.value.track.id, 'complete')
      }
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
    completeReported = false
    completeThresholdSec = 0
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
      completeReported = false
      completeThresholdSec = 0
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

  /**
   * 1.2.3：清除节点播放配置缓存
   * 用户在 NodesView 修改了节点配置后调用，让下次播放重新拉取
   */
  function invalidatePlaybackSettings(nodeId) {
    _invalidatePlaybackSettings(nodeId)
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
    removeTrack,
    invalidatePlaybackSettings
  }
})
