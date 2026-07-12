import { defineStore } from 'pinia'
import { ref, watch } from 'vue'
import { useToast } from '@/components/ui/toast/use-toast'
import { useNodesStore } from './nodes'
import {
  getTracks,
  getPlaylists,
  getPlaylistDetail
} from '../api/node'
import {
  listClientPlaylists,
  listClientPlaylistItems
} from '../api/client_playlist'

const toast = useToast()

/**
 * 聚合曲库（多节点架构）
 *
 * 不依赖 activeNode。聚合所有已登录节点的内容：
 * - nodePlaylists: 每个节点的播放列表（含该节点的系统"收集箱"）
 * - clientPlaylists: 客户端播放列表（存在 eta_web 后端，可跨节点）
 *
 * 视图模式：
 * - 'all'              客户端"全部音乐"（聚合所有节点曲目）
 * - 'node-all'         某节点的"全部音乐"
 * - 'node-playlist'    某节点的播放列表（含节点"收集箱"）
 * - 'client-playlist'  客户端播放列表
 * - 'search'           跨节点搜索结果
 * - 'empty'            无内容
 *
 * 每条曲目都带 __nodeId / __nodeName，供播放器从正确节点取流。
 */
export const useLibraryStore = defineStore('library', () => {
  const nodesStore = useNodesStore()

  const keyword = ref('')
  // 各节点的播放列表：{ [nodeId]: playlists[] }
  const nodePlaylists = ref({})
  // 客户端播放列表（eta_web 后端）
  const clientPlaylists = ref([])

  const tracks = ref([]) // 当前展示的曲目
  const tracksTotal = ref(0)
  const loading = ref(false)
  const searchResults = ref([]) // 跨节点搜索结果 [{track, nodeId, nodeName}]
  const searchLoading = ref(false)

  // 当前展示模式
  const mode = ref('empty')
  const currentNodeId = ref(null) // node-* 模式下的节点 id
  const currentPlaylistId = ref(null) // playlist 模式下的播放列表 id
  const currentPlaylistType = ref(null) // 'node' | 'client'
  const page = ref(1)
  const pageSize = ref(20)

  /**
   * 刷新所有已登录节点的播放列表 + 客户端播放列表
   */
  async function refreshAllPlaylists() {
    const loggedIn = nodesStore.loggedInNodes
    // 并发拉取每个节点的播放列表
    const nodeResults = await Promise.allSettled(
      loggedIn.map(async (n) => {
        const data = await getPlaylists(n)
        const items = Array.isArray(data) ? data : data.items || []
        return { nodeId: n.id, playlists: items }
      })
    )
    const map = {}
    nodeResults.forEach((r) => {
      if (r.status === 'fulfilled') {
        map[r.value.nodeId] = r.value.playlists
      }
    })
    nodePlaylists.value = map

    // 拉取客户端播放列表
    try {
      clientPlaylists.value = await listClientPlaylists()
    } catch (e) {
      toast.error('获取客户端播放列表失败', e)
      clientPlaylists.value = []
    }
  }

  /**
   * 加载客户端"全部音乐"：聚合所有已登录节点的全部曲目
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
      const q = keyword.value || undefined
      const results = await Promise.allSettled(
        loggedIn.map(async (n) => {
          const data = await getTracks(n, { page: 1, size: 100000, q })
          const items = data.items || data.tracks || []
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
      currentNodeId.value = null
      currentPlaylistId.value = null
      currentPlaylistType.value = null
    } catch (e) {
      toast.error('获取曲目失败', e)
      tracks.value = []
      tracksTotal.value = 0
    } finally {
      loading.value = false
    }
  }

  /**
   * 加载某节点的"全部音乐"
   */
  async function loadNodeAllTracks(nodeId) {
    const node = nodesStore.getNode(nodeId)
    if (!node || !node.token) {
      tracks.value = []
      tracksTotal.value = 0
      mode.value = 'empty'
      return
    }
    loading.value = true
    try {
      const data = await getTracks(node, {
        page: 1,
        size: 100000,
        q: keyword.value || undefined
      })
      const items = data.items || data.tracks || []
      tracks.value = items.map((t) => ({
        ...t,
        __nodeId: t.__nodeId ?? node.id,
        __nodeName: t.__nodeName ?? node.name
      }))
      tracksTotal.value = data.total || tracks.value.length
      mode.value = 'node-all'
      currentNodeId.value = nodeId
      currentPlaylistId.value = null
      currentPlaylistType.value = null
    } catch (e) {
      toast.error('获取节点曲目失败', e)
      tracks.value = []
      tracksTotal.value = 0
    } finally {
      loading.value = false
    }
  }

  /**
   * 加载某节点的播放列表曲目（含节点"收集箱"）
   */
  async function loadNodePlaylistTracks(nodeId, playlistId) {
    const node = nodesStore.getNode(nodeId)
    if (!node || !node.token) {
      tracks.value = []
      tracksTotal.value = 0
      mode.value = 'empty'
      return
    }
    loading.value = true
    try {
      const data = await getPlaylistDetail(node, playlistId)
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
      mode.value = 'node-playlist'
      currentNodeId.value = nodeId
      currentPlaylistId.value = playlistId
      currentPlaylistType.value = 'node'
    } catch (e) {
      toast.error('获取播放列表曲目失败', e)
      tracks.value = []
      tracksTotal.value = 0
    } finally {
      loading.value = false
    }
  }

  /**
   * 加载客户端播放列表曲目（跨节点）
   * 曲目元数据已缓存在 eta_web 后端，但流地址仍需从来源节点获取。
   */
  async function loadClientPlaylistTracks(playlistId) {
    loading.value = true
    try {
      const items = await listClientPlaylistItems(playlistId)
      // 给每条曲目标注来源节点（节点失效则 __nodeOffline = true）
      tracks.value = items.map((it) => {
        const node = nodesStore.getNode(Number(it.node_id))
        const online = !!(node && node.token)
        return {
          id: it.track_id,
          title: it.title,
          artist: it.artist,
          album: it.album,
          duration: it.duration,
          __nodeId: Number(it.node_id),
          __nodeName: node?.name || `节点 ${it.node_id}`,
          __nodeOffline: !online,
          __clientItemId: it.id,
          __position: it.position
        }
      })
      tracksTotal.value = tracks.value.length
      mode.value = 'client-playlist'
      currentNodeId.value = null
      currentPlaylistId.value = playlistId
      currentPlaylistType.value = 'client'
    } catch (e) {
      toast.error('获取客户端播放列表曲目失败', e)
      tracks.value = []
      tracksTotal.value = 0
    } finally {
      loading.value = false
    }
  }

  /**
   * 跨节点搜索
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
  }

  function resetPaging() {
    page.value = 1
  }

  /**
   * 监听节点登录/登出/删除事件，自动刷新所有播放列表
   */
  watch(
    () => nodesStore.authVersion,
    () => {
      refreshAllPlaylists().then(() => {
        // 登录后若当前为空视图，自动加载客户端"全部音乐"
        if (mode.value === 'empty' && nodesStore.loggedInNodes.length > 0) {
          loadAllTracks()
        } else if (nodesStore.loggedInNodes.length === 0) {
          tracks.value = []
          tracksTotal.value = 0
          mode.value = 'empty'
        }
      })
    }
  )

  return {
    keyword,
    nodePlaylists,
    clientPlaylists,
    tracks,
    tracksTotal,
    loading,
    searchResults,
    searchLoading,
    mode,
    currentNodeId,
    currentPlaylistId,
    currentPlaylistType,
    page,
    pageSize,
    refreshAllPlaylists,
    loadAllTracks,
    loadNodeAllTracks,
    loadNodePlaylistTracks,
    loadClientPlaylistTracks,
    globalSearch,
    setPage,
    resetPaging
  }
})
