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
 * - 维护当前激活节点的播放列表树
 * - 维护当前展示的曲目列表（某播放列表 / 全部音乐 / 搜索结果）
 * - 跨节点搜索：对所有"已登录"节点并发调 /api/tracks?q=，合并结果
 * - 监听 nodesStore.authVersion：节点登录/登出/切换时自动刷新
 */
export const useLibraryStore = defineStore('library', () => {
  const nodesStore = useNodesStore()

  const keyword = ref('')
  const playlists = ref([]) // 当前激活节点的播放列表
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
   * 当前激活节点是否已登录
   */
  function activeNodeLoggedIn() {
    const node = nodesStore.activeNode
    return !!(node && node.token)
  }

  /**
   * 刷新当前激活节点的播放列表（仅当已登录）
   */
  async function refreshPlaylists() {
    const node = nodesStore.activeNode
    if (!node || !node.token) {
      playlists.value = []
      return
    }
    try {
      const data = await getPlaylists(node)
      playlists.value = Array.isArray(data) ? data : data.items || []
    } catch (e) {
      playlists.value = []
      toast.error('获取播放列表失败：' + (e.message || e))
    }
  }

  /**
   * 加载全部曲目（分页）
   */
  async function loadAllTracks() {
    const node = nodesStore.activeNode
    if (!node || !node.token) {
      tracks.value = []
      tracksTotal.value = 0
      mode.value = 'empty'
      return
    }
    loading.value = true
    try {
      const data = await getTracks(node, {
        page: page.value,
        page_size: pageSize.value,
        q: keyword.value || undefined
      })
      tracks.value = data.items || data.tracks || []
      tracksTotal.value = data.total || tracks.value.length
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
   */
  async function loadPlaylistTracks(playlistId) {
    const node = nodesStore.activeNode
    if (!node || !node.token) {
      tracks.value = []
      tracksTotal.value = 0
      mode.value = 'empty'
      return
    }
    loading.value = true
    try {
      // 后端 GET /api/playlists/{id} 返回 PlaylistDetail，含 items 数组（每项有 track 对象）
      const data = await getPlaylistDetail(node, playlistId)
      const items = data.items || []
      tracks.value = items.map((it) => it.track || it).filter(Boolean)
      tracksTotal.value = tracks.value.length
      mode.value = 'playlist'
      currentPlaylistId.value = playlistId
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
      tracks.value = merged.map((m) => m.track)
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
   * 监听节点登录/登出/删除事件，自动刷新当前激活节点的播放列表
   */
  watch(
    () => nodesStore.authVersion,
    () => {
      refreshPlaylists().then(() => {
        // 登录后自动加载全部音乐
        if (activeNodeLoggedIn() && mode.value === 'empty') {
          loadAllTracks()
        } else if (!activeNodeLoggedIn()) {
          tracks.value = []
          tracksTotal.value = 0
          mode.value = 'empty'
        }
      })
    }
  )

  /**
   * 监听激活节点切换
   */
  watch(
    () => nodesStore.activeNodeId,
    () => {
      refreshPlaylists().then(() => {
        if (activeNodeLoggedIn()) {
          resetPaging()
          loadAllTracks()
        } else {
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
