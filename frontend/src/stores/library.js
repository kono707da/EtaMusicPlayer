import { defineStore } from 'pinia'
import { ref, watch } from 'vue'
import { useToast } from '@/components/ui/toast/use-toast'
import { useNodesStore } from './nodes'
import {
  getTracks,
  getPlaylists,
  getPlaylistDetail
} from '../api/node'

const toast = useToast()

/**
 * 聚合曲库
 * - 维护所有已登录节点的播放列表树
 * - 维护当前展示的曲目列表（某播放列表 / 全部音乐 / 搜索结果）
 * - 跨节点搜索：对所有"已登录"节点并发调 /api/tracks?q=，合并结果
 * - 监听 nodesStore.authVersion：节点登录/登出时自动刷新
 */
export const useLibraryStore = defineStore('library', () => {
  const nodesStore = useNodesStore()

  const keyword = ref('')
  const playlists = ref([]) // 所有已登录节点的播放列表（聚合，含 __nodeId/__nodeName）
  const tracks = ref([]) // 当前展示的曲目
  const tracksTotal = ref(0)
  const loading = ref(false)
  const searchResults = ref([]) // 跨节点搜索结果 [{track, nodeId, nodeName}]
  const searchLoading = ref(false)

  // 当前展示模式：'all' | 'playlist' | 'search' | 'empty'
  const mode = ref('empty')
  const currentPlaylistId = ref(null)
  const page = ref(1)
  const pageSize = ref(20)

  /**
   * 是否有任意已登录节点
   */
  function hasLoggedInNode() {
    return nodesStore.loggedInNodes.length > 0
  }

  /**
   * 刷新所有已登录节点的播放列表（聚合合并）
   * 每条播放列表附加 __nodeId / __nodeName 用于后续按节点操作
   */
  async function refreshPlaylists() {
    const loggedIn = nodesStore.loggedInNodes
    if (loggedIn.length === 0) {
      playlists.value = []
      return
    }
    try {
      const results = await Promise.allSettled(
        loggedIn.map(async (n) => {
          const data = await getPlaylists(n)
          const items = Array.isArray(data) ? data : data.items || []
          return items.map((p) => ({
            ...p,
            __nodeId: n.id,
            __nodeName: n.name
          }))
        })
      )
      const merged = []
      results.forEach((r) => {
        if (r.status === 'fulfilled') merged.push(...r.value)
      })
      playlists.value = merged
    } catch (e) {
      playlists.value = []
      toast.error('获取播放列表失败：' + (e.message || e))
    }
  }

  /**
   * 加载全部曲目（聚合所有已登录节点，一次性拉取，不分页）
   */
  async function loadAllTracks() {
    const loggedIn = nodesStore.loggedInNodes
    if (loggedIn.length === 0) {
      tracks.value = []
      tracksTotal.value = 0
      mode.value = 'empty'
      return
    }
    loading.value = true
    try {
      const results = await Promise.allSettled(
        loggedIn.map(async (n) => {
          const data = await getTracks(n, {
            page: 1,
            size: 100000,
            q: keyword.value || undefined
          })
          const items = data.items || data.tracks || []
          // 给每条曲目标记来源节点，供封面/播放等场景使用
          return items.map((t) => ({
            ...t,
            __nodeId: t.__nodeId ?? n.id,
            __nodeName: t.__nodeName ?? n.name
          }))
        })
      )
      const merged = []
      results.forEach((r) => {
        if (r.status === 'fulfilled') merged.push(...r.value)
      })
      tracks.value = merged
      tracksTotal.value = merged.length
      mode.value = 'all'
      currentPlaylistId.value = null
    } catch (e) {
      toast.error('获取曲目失败：' + (e.message || e))
      tracks.value = []
      tracksTotal.value = 0
    } finally {
      loading.value = false
    }
  }

  /**
   * 加载某播放列表的曲目
   * playlistId 形如 {id, nodeId}（聚合后必须知道目标节点）
   */
  async function loadPlaylistTracks(playlist) {
    const node = nodesStore.nodes.find((n) => n.id === playlist.nodeId)
    if (!node || !node.token) {
      tracks.value = []
      tracksTotal.value = 0
      mode.value = 'empty'
      return
    }
    loading.value = true
    try {
      // 后端 GET /api/playlists/{id} 返回 PlaylistDetail，含 items 数组（每项有 track 对象）
      const data = await getPlaylistDetail(node, playlist.id)
      const items = data.items || []
      tracks.value = items
        .map((it) => it.track || it)
        .filter(Boolean)
        .map((t) => ({
          ...t,
          __nodeId: t.__nodeId ?? node.id,
          __nodeName: t.__nodeName ?? node.name
        }))
      tracksTotal.value = tracks.value.length
      mode.value = 'playlist'
      currentPlaylistId.value = playlist
    } catch (e) {
      toast.error('获取播放列表曲目失败：' + (e.message || e))
      tracks.value = []
      tracksTotal.value = 0
    } finally {
      loading.value = false
    }
  }

  /**
   * 跨节点搜索
   * 对所有"已登录"节点并发调 /api/tracks?q=，合并结果
   */
  async function globalSearch(q) {
    if (!q) return
    const loggedIn = nodesStore.loggedInNodes
    if (loggedIn.length === 0) {
      toast.warning('尚未登录任何节点，请先在节点管理中登录')
      return
    }
    searchLoading.value = true
    try {
      const results = await Promise.allSettled(
        loggedIn.map(async (n) => {
          const data = await getTracks(n, { q, page: 1, page_size: 50 })
          const items = data.items || data.tracks || []
          return items.map((t) => ({ track: t, nodeId: n.id, nodeName: n.name }))
        })
      )
      const merged = []
      results.forEach((r) => {
        if (r.status === 'fulfilled') merged.push(...r.value)
      })
      searchResults.value = merged
      tracks.value = merged.map((m) => ({
        ...m.track,
        __nodeId: m.track.__nodeId ?? m.nodeId,
        __nodeName: m.track.__nodeName ?? m.nodeName
      }))
      tracksTotal.value = merged.length
      mode.value = 'search'
    } finally {
      searchLoading.value = false
    }
  }

  function setPage(p) {
    page.value = p
    if (mode.value === 'playlist' && currentPlaylistId.value) {
      loadPlaylistTracks(currentPlaylistId.value)
    } else if (mode.value === 'all') {
      loadAllTracks()
    }
  }

  function resetPaging() {
    page.value = 1
  }

  /**
   * 监听节点登录/登出/删除事件，自动刷新所有已登录节点的播放列表
   */
  watch(
    () => nodesStore.authVersion,
    () => {
      refreshPlaylists().then(() => {
        // 登录后自动加载全部音乐
        if (hasLoggedInNode() && mode.value === 'empty') {
          loadAllTracks()
        } else if (!hasLoggedInNode()) {
          tracks.value = []
          tracksTotal.value = 0
          mode.value = 'empty'
        }
      })
    }
  )

  return {
    keyword,
    playlists,
    tracks,
    tracksTotal,
    loading,
    searchResults,
    searchLoading,
    mode,
    currentPlaylistId,
    page,
    pageSize,
    refreshPlaylists,
    loadAllTracks,
    loadPlaylistTracks,
    globalSearch,
    setPage,
    resetPaging
  }
})
