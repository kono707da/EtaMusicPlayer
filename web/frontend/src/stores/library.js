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
import {
  refreshLibrary as apiRefreshLibrary,
  getCachedTracks,
  getCachedPlaylists
} from '../api/node_cache'

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
   * 触发后台增量同步（在线节点），不阻塞 UI
   * 进入工作台或登录状态变化时调用
   */
  async function triggerBackgroundSync() {
    try {
      await apiRefreshLibrary()
    } catch (e) {
      // 同步失败不阻塞 UI，离线节点照常读缓存展示
      console.warn('[library] 后台同步失败:', e)
    }
  }

  /**
   * 刷新所有节点的播放列表 + 客户端播放列表
   * - 在线节点：直调节点 API
   * - 离线节点：读访问端缓存（置灰展示）
   */
  async function refreshAllPlaylists() {
    const allNodes = nodesStore.nodes
    const onlineNodes = allNodes.filter((n) => !!n.token)
    const offlineNodes = allNodes.filter((n) => !n.token)

    // 在线节点：直调节点 API
    const onlineResults = await Promise.allSettled(
      onlineNodes.map(async (n) => {
        const data = await getPlaylists(n)
        const items = Array.isArray(data) ? data : data.items || []
        return { nodeId: n.id, playlists: items }
      })
    )
    const map = {}
    onlineResults.forEach((r) => {
      if (r.status === 'fulfilled') {
        map[r.value.nodeId] = r.value.playlists
      }
    })

    // 离线节点：读缓存（如有）
    if (offlineNodes.length > 0) {
      try {
        const cached = await getCachedPlaylists()
        const byNode = new Map()
        for (const p of cached) {
          if (!byNode.has(p.node_id)) byNode.set(p.node_id, [])
          byNode.get(p.node_id).push({
            id: p.playlist_id,
            name: p.name,
            owner_id: p.owner_id,
            is_system: p.is_system,
            description: p.description,
            items: p.items || [],
            __offline: true
          })
        }
        for (const n of offlineNodes) {
          if (byNode.has(n.id)) {
            map[n.id] = byNode.get(n.id)
          }
        }
      } catch (e) {
        // 缓存读取失败不阻塞 UI
        console.warn('[library] 读取离线节点播放列表缓存失败:', e)
      }
    }

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
   * 加载客户端"全部音乐"：聚合所有节点
   * - 在线节点：直调节点 API
   * - 离线节点：读访问端缓存（置灰展示，__nodeOffline=true）
   */
  async function loadAllTracks() {
    const allNodes = nodesStore.nodes
    if (allNodes.length === 0) {
      tracks.value = []
      tracksTotal.value = 0
      mode.value = 'empty'
      return
    }
    loading.value = true
    try {
      const q = keyword.value || undefined
      const onlineNodes = allNodes.filter((n) => !!n.token)
      const offlineNodes = allNodes.filter((n) => !n.token)

      // 在线节点直调
      const onlineResults = await Promise.allSettled(
        onlineNodes.map(async (n) => {
          const data = await getTracks(n, { page: 1, size: 100000, q })
          const items = data.items || data.tracks || []
          return items.map((t) => ({
            ...t,
            __nodeId: t.__nodeId ?? n.id,
            __nodeName: t.__nodeName ?? n.name,
            __nodeOffline: false
          }))
        })
      )

      // 离线节点读缓存
      let offlineTracks = []
      if (offlineNodes.length > 0) {
        try {
          const cached = await getCachedTracks({ q })
          const offlineIds = new Set(offlineNodes.map((n) => n.id))
          const nodeNameById = new Map(offlineNodes.map((n) => [n.id, n.name]))
          offlineTracks = cached
            .filter((c) => offlineIds.has(c.node_id))
            .map((c) => ({
              id: c.track_id,
              title: c.title,
              artist: c.artist,
              album: c.album,
              album_artist: c.album_artist,
              track_no: c.track_no,
              year: c.year,
              genre: c.genre,
              duration: c.duration,
              bitrate: c.bitrate,
              sample_rate: c.sample_rate,
              channels: c.channels,
              file_size: c.file_size,
              cover_embedded: c.cover_embedded,
              lyrics_embedded: c.lyrics_embedded,
              format_priority: c.format_priority,
              quality_score: c.quality_score,
              __nodeId: c.node_id,
              __nodeName: nodeNameById.get(c.node_id) || `节点 ${c.node_id}`,
              __nodeOffline: true
            }))
        } catch (e) {
          console.warn('[library] 读取离线节点曲库缓存失败:', e)
        }
      }

      const merged = []
      onlineResults.forEach((r) => {
        if (r.status === 'fulfilled') merged.push(...r.value)
      })
      merged.push(...offlineTracks)
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
   * - 在线：直调节点 API
   * - 离线：读访问端缓存
   */
  async function loadNodeAllTracks(nodeId) {
    const node = nodesStore.getNode(nodeId)
    if (!node) {
      tracks.value = []
      tracksTotal.value = 0
      mode.value = 'empty'
      return
    }

    // 离线节点：读缓存
    if (!node.token) {
      loading.value = true
      try {
        const cached = await getCachedTracks({ node_id: nodeId, q: keyword.value || undefined })
        tracks.value = cached.map((c) => ({
          id: c.track_id,
          title: c.title,
          artist: c.artist,
          album: c.album,
          album_artist: c.album_artist,
          track_no: c.track_no,
          year: c.year,
          genre: c.genre,
          duration: c.duration,
          bitrate: c.bitrate,
          sample_rate: c.sample_rate,
          channels: c.channels,
          file_size: c.file_size,
          cover_embedded: c.cover_embedded,
          lyrics_embedded: c.lyrics_embedded,
          format_priority: c.format_priority,
          quality_score: c.quality_score,
          __nodeId: node.id,
          __nodeName: node.name,
          __nodeOffline: true
        }))
        tracksTotal.value = tracks.value.length
        mode.value = 'node-all'
        currentNodeId.value = nodeId
        currentPlaylistId.value = null
        currentPlaylistType.value = null
      } catch (e) {
        toast.error('节点离线读取缓存失败', e)
        tracks.value = []
        tracksTotal.value = 0
      } finally {
        loading.value = false
      }
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
        __nodeName: t.__nodeName ?? node.name,
        __nodeOffline: false
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
   * - 在线：直调节点 API
   * - 离线：读访问端缓存的播放列表 items
   */
  async function loadNodePlaylistTracks(nodeId, playlistId) {
    const node = nodesStore.getNode(nodeId)
    if (!node) {
      tracks.value = []
      tracksTotal.value = 0
      mode.value = 'empty'
      return
    }

    // 离线节点：读缓存
    if (!node.token) {
      loading.value = true
      try {
        const cached = await getCachedPlaylists({ node_id: nodeId })
        const pl = cached.find((p) => p.playlist_id === playlistId)
        if (!pl) {
          toast.warning('节点离线，缓存中无此播放列表')
          tracks.value = []
          tracksTotal.value = 0
          mode.value = 'empty'
          return
        }
        const items = pl.items || []
        tracks.value = items
          .map((it) => it.track || it)
          .filter(Boolean)
          .map((t) => ({
            ...t,
            __nodeId: node.id,
            __nodeName: node.name,
            __nodeOffline: true
          }))
        tracksTotal.value = tracks.value.length
        mode.value = 'node-playlist'
        currentNodeId.value = nodeId
        currentPlaylistId.value = playlistId
        currentPlaylistType.value = 'node'
      } catch (e) {
        toast.error('节点离线读取缓存失败', e)
        tracks.value = []
        tracksTotal.value = 0
      } finally {
        loading.value = false
      }
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
          __nodeName: t.__nodeName ?? node.name,
          __nodeOffline: false
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
   * - 在线节点：直调节点 API
   * - 离线节点：读访问端缓存（置灰展示）
   */
  async function globalSearch(q) {
    if (!q) return
    const allNodes = nodesStore.nodes
    if (allNodes.length === 0) {
      toast.warning('尚未配置任何节点，请先在节点管理中添加')
      return
    }
    searchLoading.value = true
    try {
      const onlineNodes = allNodes.filter((n) => !!n.token)
      const offlineNodes = allNodes.filter((n) => !n.token)

      // 在线节点搜索
      const onlineResults = await Promise.allSettled(
        onlineNodes.map(async (n) => {
          const data = await getTracks(n, { q, page: 1, page_size: 50 })
          const items = data.items || data.tracks || []
          return items.map((t) => ({
            track: { ...t, __nodeOffline: false },
            nodeId: n.id,
            nodeName: n.name
          }))
        })
      )

      // 离线节点缓存搜索
      let offlineMatches = []
      if (offlineNodes.length > 0) {
        try {
          const cached = await getCachedTracks({ q })
          const offlineIds = new Set(offlineNodes.map((n) => n.id))
          const nodeNameById = new Map(offlineNodes.map((n) => [n.id, n.name]))
          offlineMatches = cached
            .filter((c) => offlineIds.has(c.node_id))
            .map((c) => ({
              track: {
                id: c.track_id,
                title: c.title,
                artist: c.artist,
                album: c.album,
                album_artist: c.album_artist,
                track_no: c.track_no,
                year: c.year,
                genre: c.genre,
                duration: c.duration,
                bitrate: c.bitrate,
                sample_rate: c.sample_rate,
                channels: c.channels,
                file_size: c.file_size,
                cover_embedded: c.cover_embedded,
                lyrics_embedded: c.lyrics_embedded,
                format_priority: c.format_priority,
                quality_score: c.quality_score,
                __nodeOffline: true
              },
              nodeId: c.node_id,
              nodeName: nodeNameById.get(c.node_id) || `节点 ${c.node_id}`
            }))
        } catch (e) {
          console.warn('[library] 离线节点缓存搜索失败:', e)
        }
      }

      const merged = []
      onlineResults.forEach((r) => {
        if (r.status === 'fulfilled') merged.push(...r.value)
      })
      merged.push(...offlineMatches)
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
   * 1.2.1：按当前 mode 重新加载视图（删除曲目后调用）
   * - 'all': loadAllTracks
   * - 'node-all': loadNodeAllTracks(currentNodeId)
   * - 'node-playlist': loadNodePlaylistTracks(currentNodeId, currentPlaylistId)
   * - 'client-playlist': loadClientPlaylistTracks(currentPlaylistId)
   * - 'search': 用 keyword 重新搜索
   * - 'empty': no-op
   * 删除失败时不调用，避免无谓刷新。
   */
  async function reloadCurrentView() {
    switch (mode.value) {
      case 'all':
        await loadAllTracks()
        break
      case 'node-all':
        if (currentNodeId.value != null) {
          await loadNodeAllTracks(currentNodeId.value)
        }
        break
      case 'node-playlist':
        if (currentNodeId.value != null && currentPlaylistId.value != null) {
          await loadNodePlaylistTracks(currentNodeId.value, currentPlaylistId.value)
        }
        break
      case 'client-playlist':
        if (currentPlaylistId.value != null) {
          await loadClientPlaylistTracks(currentPlaylistId.value)
        }
        break
      case 'search':
        if (keyword.value) {
          await globalSearch(keyword.value)
        }
        break
      case 'empty':
      default:
        break
    }
  }

  /**
   * 监听节点登录/登出/删除事件
   * 1. 触发后台增量同步（在线节点缓存刷新）
   * 2. 刷新所有节点播放列表（在线直调+离线读缓存）
   * 3. 自动加载"全部音乐"（若当前为空视图）
   */
  watch(
    () => nodesStore.authVersion,
    () => {
      // 后台同步不阻塞 UI
      triggerBackgroundSync()
      refreshAllPlaylists().then(() => {
        // 登录/状态变化后若当前为空视图，自动加载聚合"全部音乐"
        if (mode.value === 'empty' && nodesStore.nodes.length > 0) {
          loadAllTracks()
        } else if (nodesStore.nodes.length === 0) {
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
    triggerBackgroundSync,
    loadAllTracks,
    loadNodeAllTracks,
    loadNodePlaylistTracks,
    loadClientPlaylistTracks,
    globalSearch,
    setPage,
    resetPaging,
    reloadCurrentView
  }
})
