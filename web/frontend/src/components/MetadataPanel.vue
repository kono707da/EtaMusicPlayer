<script setup>
import { ref, computed, watch, reactive } from 'vue'
import { X, Save, AlertCircle, RotateCcw, Music, FileText, Tags, AlignLeft, Image, Upload, Trash2, Loader2 } from 'lucide-vue-next'
import {
  previewMetadata,
  batchUpdateMetadata,
  batchWriteLyrics,
  batchUploadCover,
  batchRemoveCover,
  getCoverUrl,
  getLyrics
} from '../api/node'
import { useAuthStore } from '../stores/auth'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter
} from '@/components/ui/dialog'
import { useToast } from '@/components/ui/toast/use-toast'

const props = defineProps({
  tracks: { type: Array, default: () => [] },
  visible: { type: Boolean, default: false },
  // 只读模式：用于离线节点曲目，仅展示元数据，不允许编辑/保存
  readonly: { type: Boolean, default: false }
})

const emit = defineEmits(['update:visible', 'updated'])

const authStore = useAuthStore()
const toast = useToast()

// ==================== Tab 定义 ====================

const TABS = [
  { key: 'file', label: '文件', icon: FileText },
  { key: 'metadata', label: '元数据', icon: Tags },
  { key: 'lyrics', label: '歌词', icon: AlignLeft },
  { key: 'cover', label: '封面', icon: Image }
]
const activeTab = ref('file')

// ==================== 字段定义 ====================

// 文件信息字段（只读，用 disabled input 展示）
const FILE_FIELDS = [
  { key: 'id', label: '数据库 ID', group: '基础' },
  { key: 'filename', label: '文件名', group: '基础' },
  { key: 'rel_path', label: '相对路径', group: '基础' },
  { key: 'ext', label: '扩展名', group: '基础' },
  { key: 'file_size', label: '文件大小', group: '基础' },
  { key: 'duration', label: '时长', group: '基础' },
  { key: 'watch_dir_id', label: '监控目录 ID', group: '基础' },
  { key: 'format_priority', label: '格式优先级', group: '质量' },
  { key: 'quality_score', label: '质量评分', group: '质量' },
  { key: 'bitrate', label: '比特率', group: '质量' },
  { key: 'sample_rate', label: '采样率', group: '质量' },
  { key: 'channels', label: '声道', group: '质量' },
  { key: 'cover_embedded', label: '内嵌封面', group: '状态' },
  { key: 'lyrics_embedded', label: '内嵌歌词', group: '状态' },
  { key: 'created_at', label: '创建时间', group: '状态' },
  { key: 'updated_at', label: '更新时间', group: '状态' }
]

const FILE_GROUPS = ['基础', '质量', '状态']

// 可编辑元数据字段（涵盖所有 ID3 文本 frame + URL frame + COMM）
const EDIT_FIELDS = [
  // 基础
  { key: 'title', label: '标题', group: '基础', type: 'text' },
  { key: 'artist', label: '艺术家', group: '基础', type: 'text' },
  { key: 'subtitle', label: '副标题', group: '基础', type: 'text' },
  { key: 'content_group', label: '内容分组', group: '基础', type: 'text' },
  { key: 'mood', label: '情绪', group: '基础', type: 'text' },
  { key: 'set_subtitle', label: '套装副标题', group: '基础', type: 'text' },
  // 专辑
  { key: 'album', label: '专辑', group: '专辑', type: 'text' },
  { key: 'album_artist', label: '专辑艺术家', group: '专辑', type: 'text' },
  { key: 'track_no', label: '音轨号', group: '专辑', type: 'number' },
  { key: 'disc_no', label: '碟号', group: '专辑', type: 'number' },
  { key: 'year', label: '年份', group: '专辑', type: 'number' },
  { key: 'genre', label: '流派', group: '专辑', type: 'text' },
  { key: 'original_album', label: '原专辑', group: '专辑', type: 'text' },
  { key: 'original_artist', label: '原唱', group: '专辑', type: 'text' },
  // 人员
  { key: 'composer', label: '作曲', group: '人员', type: 'text' },
  { key: 'conductor', label: '指挥', group: '人员', type: 'text' },
  { key: 'remixer', label: '混音师', group: '人员', type: 'text' },
  { key: 'lyricist', label: '词作者', group: '人员', type: 'text' },
  { key: 'original_lyricist', label: '原词作者', group: '人员', type: 'text' },
  { key: 'involved_people', label: '参与人员', group: '人员', type: 'text' },
  { key: 'musician_credits', label: '演奏者名单', group: '人员', type: 'text' },
  { key: 'file_owner', label: '文件所有者', group: '人员', type: 'text' },
  // 技术
  { key: 'bpm', label: 'BPM', group: '技术', type: 'number' },
  { key: 'key', label: '调式', group: '技术', type: 'text' },
  { key: 'isrc', label: 'ISRC', group: '技术', type: 'text' },
  { key: 'language', label: '语言', group: '技术', type: 'text' },
  { key: 'length', label: '长度(ms)', group: '技术', type: 'number' },
  { key: 'media_type', label: '媒体类型', group: '技术', type: 'text' },
  { key: 'file_type', label: '文件类型', group: '技术', type: 'text' },
  { key: 'encoder_settings', label: '编码器设置', group: '技术', type: 'text' },
  { key: 'encoded_by', label: '编码者', group: '技术', type: 'text' },
  { key: 'playlist_delay', label: '播放列表延迟', group: '技术', type: 'number' },
  // 时间
  { key: 'release_time', label: '发行时间', group: '时间', type: 'text' },
  { key: 'original_release_time', label: '原发行时间', group: '时间', type: 'text' },
  { key: 'encoding_time', label: '编码时间', group: '时间', type: 'text' },
  { key: 'tagging_time', label: '打标签时间', group: '时间', type: 'text' },
  // 排序
  { key: 'album_sort', label: '专辑排序', group: '排序', type: 'text' },
  { key: 'performer_sort', label: '艺术家排序', group: '排序', type: 'text' },
  { key: 'title_sort', label: '标题排序', group: '排序', type: 'text' },
  // 版权
  { key: 'copyright', label: '版权', group: '版权', type: 'text' },
  { key: 'publisher', label: '发行方', group: '版权', type: 'text' },
  { key: 'copyright_url', label: '版权 URL', group: '版权', type: 'text' },
  { key: 'publisher_url', label: '发行方 URL', group: '版权', type: 'text' },
  { key: 'commercial_info_url', label: '商业信息 URL', group: '版权', type: 'text' },
  { key: 'payment_url', label: '支付 URL', group: '版权', type: 'text' },
  // 网络资源
  { key: 'official_audio_file_url', label: '音频文件官方 URL', group: '网络', type: 'text' },
  { key: 'official_artist_url', label: '艺术家官方 URL', group: '网络', type: 'text' },
  { key: 'official_audio_source_url', label: '音频来源官方 URL', group: '网络', type: 'text' },
  { key: 'internet_radio_station_homepage', label: '网络电台主页', group: '网络', type: 'text' },
  // 电台
  { key: 'internet_radio_station_name', label: '网络电台名称', group: '电台', type: 'text' },
  { key: 'internet_radio_station_owner', label: '网络电台所有者', group: '电台', type: 'text' },
  // 其他
  { key: 'comment', label: '注释', group: '其他', type: 'text' },
  { key: 'original_filename', label: '原始文件名', group: '其他', type: 'text' }
]
const EDIT_GROUPS = ['基础', '专辑', '人员', '技术', '时间', '排序', '版权', '网络', '电台', '其他']

// ==================== 元数据字段状态 ====================

const fieldStates = reactive({})
const fieldsLoading = ref(false)
let cachedTracks = []
// 用于取消过时的异步 init（用户快速切换曲目时）
let initToken = 0

const hasDirty = computed(() =>
  Object.values(fieldStates).some((s) => s.isDirty)
)
const dirtyCount = computed(() =>
  Object.values(fieldStates).filter((s) => s.isDirty).length
)

async function initFieldStates() {
  Object.keys(fieldStates).forEach((k) => delete fieldStates[k])
  if (props.tracks.length === 0) return

  const token = ++initToken

  // 1. 先用 tracks 数据库字段快速初始化（DB 字段从 props.tracks 读）
  for (const f of EDIT_FIELDS) {
    const values = props.tracks.map((t) => {
      const v = t[f.key]
      return v == null ? '' : String(v)
    })
    const unique = [...new Set(values)]
    const isMixed = unique.length > 1
    const commonValue = isMixed ? '' : (unique[0] || '')
    fieldStates[f.key] = {
      value: commonValue,
      originalValue: commonValue,
      isMixed,
      isDirty: false
    }
  }

  // 2. 调用 batch_preview API 获取所有字段的真实值（含非 DB 字段）
  // 离线只读模式下跳过远程预览（节点不可达，且曲目不属于本地节点）
  const node = authStore.localNode
  if (!node || props.readonly) return

  fieldsLoading.value = true
  try {
    const data = await previewMetadata(node, props.tracks.map((t) => t.id))
    // 如果已经有新的 init 在跑，放弃这次结果
    if (token !== initToken) return

    for (const f of EDIT_FIELDS) {
      const fieldData = data.fields[f.key]
      if (!fieldData) continue
      const isMixed = !fieldData.is_uniform
      const val = fieldData.value || ''
      fieldStates[f.key] = {
        value: isMixed ? '' : val,
        originalValue: isMixed ? '' : val,
        isMixed,
        isDirty: false
      }
    }
  } catch (e) {
    // 失败时保留 DB 字段的值（已初始化）
  } finally {
    if (token === initToken) {
      fieldsLoading.value = false
    }
  }
}

function onFieldInput(fieldKey) {
  const s = fieldStates[fieldKey]
  if (!s) return
  const changed = s.isMixed
    ? s.value !== ''
    : s.value !== s.originalValue
  s.isDirty = changed
}

async function saveMetadata() {
  const dirtyFields = EDIT_FIELDS.filter((f) => fieldStates[f.key]?.isDirty)
  if (dirtyFields.length === 0) {
    toast.info('没有需要保存的修改')
    return
  }
  const node = authStore.localNode
  if (!node) {
    toast.error('保存失败', '未连接节点')
    return
  }
  const tracksToSave = props.tracks
  const trackIds = tracksToSave.map((t) => t.id)
  const updates = {}
  for (const f of dirtyFields) {
    updates[f.key] = fieldStates[f.key].value
  }
  try {
    const result = await batchUpdateMetadata(node, trackIds, updates)
    for (const f of dirtyFields) {
      const s = fieldStates[f.key]
      s.originalValue = s.value
      s.isDirty = false
      s.isMixed = false
    }
    const skippedMsg = result.skipped?.length
      ? `（${result.skipped.length} 项跳过：${result.skipped.map(s => s.field).join(', ')}）`
      : ''
    toast.success(
      `已更新 ${result.updated} 首曲目的 ${result.fields.length} 个字段${skippedMsg}`
    )
    emit('updated')
  } catch (e) {
    const detail = e?.response?.data?.detail || e?.message || '未知错误'
    toast.error('保存失败', detail, e)
  }
}

function resetField(fieldKey) {
  const s = fieldStates[fieldKey]
  if (!s) return
  s.value = s.originalValue
  s.isDirty = false
}

function resetAllMetadata() {
  for (const k of Object.keys(fieldStates)) {
    fieldStates[k].value = fieldStates[k].originalValue
    fieldStates[k].isDirty = false
  }
}

// ==================== 歌词 ====================

const lyricsText = ref('')
const lyricsOriginal = ref('')
const lyricsLoading = ref(false)
const lyricsSaving = ref(false)
const lyricsMixed = ref(false)  // 多曲目时歌词可能不一致

async function loadLyrics() {
  lyricsText.value = ''
  lyricsOriginal.value = ''
  lyricsMixed.value = false
  if (props.tracks.length === 0) return
  const node = authStore.localNode
  if (!node || props.readonly) return

  // 单首直接拉取
  if (props.tracks.length === 1) {
    const t = props.tracks[0]
    if (!t.lyrics_embedded) {
      lyricsText.value = ''
      return
    }
    lyricsLoading.value = true
    try {
      const data = await getLyrics(node, t.id)
      lyricsText.value = data.lyrics || ''
      lyricsOriginal.value = lyricsText.value
    } catch (e) {
      // 404 等情况
      lyricsText.value = ''
    } finally {
      lyricsLoading.value = false
    }
    return
  }

  // 多首：先看是否所有曲目 lyrics_embedded 一致
  // 不拉取每首歌词对比（开销太大），直接显示「混合」提示让用户决定是否覆盖
  const allHaveLyrics = props.tracks.every((t) => t.lyrics_embedded)
  const noneHaveLyrics = props.tracks.every((t) => !t.lyrics_embedded)
  if (allHaveLyrics || noneHaveLyrics) {
    // 状态一致：多首仍可能有不同歌词，不预填，让用户主动输入覆盖
    lyricsMixed.value = true
  } else {
    lyricsMixed.value = true
  }
}

const lyricsDirty = computed(() => lyricsText.value !== lyricsOriginal.value)

async function saveLyrics() {
  if (!lyricsDirty.value) {
    toast.info('歌词未修改')
    return
  }
  const node = authStore.localNode
  if (!node) {
    toast.error('保存失败', '未连接节点')
    return
  }
  const trackIds = props.tracks.map((t) => t.id)
  lyricsSaving.value = true
  try {
    const result = await batchWriteLyrics(node, trackIds, lyricsText.value)
    lyricsOriginal.value = lyricsText.value
    lyricsMixed.value = false
    // 更新本地 lyrics_embedded 标志
    for (const t of props.tracks) {
      t.lyrics_embedded = true
    }
    const failMsg = result.failed?.length ? `（${result.failed.length} 首失败）` : ''
    toast.success(`已写入歌词到 ${result.updated} 首曲目${failMsg}`)
    emit('updated')
  } catch (e) {
    const detail = e?.response?.data?.detail || e?.message || '未知错误'
    toast.error('保存失败', detail, e)
  } finally {
    lyricsSaving.value = false
  }
}

function resetLyrics() {
  lyricsText.value = lyricsOriginal.value
}

// ==================== 封面 ====================

const coverUploading = ref(false)
const coverRemoving = ref(false)
const coverRefreshKey = ref(0)  // 用于强制刷新封面 img
const hiddenCovers = ref(new Set())  // 加载失败的 track_id 集合

function getTrackCoverUrl(track) {
  const node = authStore.localNode
  if (!node) return ''
  return getCoverUrl(node, track.id) + `&_=${coverRefreshKey.value}`
}

function onCoverImgError(trackId, e) {
  hiddenCovers.value.add(trackId)
  if (e?.target) e.target.style.display = 'none'
}

const coverFileInput = ref(null)
function triggerCoverUpload() {
  if (props.tracks.length === 0) return
  coverFileInput.value?.click()
}

async function onCoverFileChange(e) {
  const file = e.target.files?.[0]
  if (!file) return
  e.target.value = ''  // 重置允许重复选择同一文件

  const node = authStore.localNode
  if (!node) {
    toast.error('上传失败', '未连接节点')
    return
  }
  const trackIds = props.tracks.map((t) => t.id)
  coverUploading.value = true
  try {
    const result = await batchUploadCover(node, trackIds, file)
    // 更新本地 cover_embedded
    for (const t of props.tracks) {
      t.cover_embedded = true
    }
    hiddenCovers.value.clear()
    coverRefreshKey.value++
    const failMsg = result.failed?.length ? `（${result.failed.length} 首失败）` : ''
    toast.success(`已上传封面到 ${result.updated} 首曲目${failMsg}`)
    emit('updated')
  } catch (err) {
    const detail = err?.response?.data?.detail || err?.message || '未知错误'
    toast.error('上传失败', detail, err)
  } finally {
    coverUploading.value = false
  }
}

async function removeCover() {
  if (props.tracks.length === 0) return
  const ok = await confirm(
    `删除 ${props.tracks.length} 首曲目文件内嵌的封面？`,
    { title: '提示', type: 'warning' }
  )
  if (!ok) return

  const node = authStore.localNode
  if (!node) {
    toast.error('删除失败', '未连接节点')
    return
  }
  const trackIds = props.tracks.map((t) => t.id)
  coverRemoving.value = true
  try {
    const result = await batchRemoveCover(node, trackIds)
    for (const t of props.tracks) {
      t.cover_embedded = false
    }
    coverRefreshKey.value++
    const failMsg = result.failed?.length ? `（${result.failed.length} 首失败）` : ''
    toast.success(`已删除 ${result.updated} 首曲目的封面${failMsg}`)
    emit('updated')
  } catch (e) {
    const detail = e?.response?.data?.detail || e?.message || '未知错误'
    toast.error('删除失败', detail, e)
  } finally {
    coverRemoving.value = false
  }
}

// 简易确认（不依赖 useConfirm）
function confirm(message, opts = {}) {
  return new Promise((resolve) => {
    _confirmState.value = {
      visible: true,
      message,
      title: opts.title || '提示',
      type: opts.type || 'info',
      resolve
    }
  })
}
const _confirmState = ref({ visible: false, message: '', title: '', type: 'info', resolve: null })
function _onConfirm() {
  _confirmState.value.resolve?.(true)
  _confirmState.value.visible = false
}
function _onConfirmCancel() {
  _confirmState.value.resolve?.(false)
  _confirmState.value.visible = false
}

// ==================== 抽屉打开/关闭 + 未保存提示 ====================

const saving = ref(false)
const unsavedDialog = ref({ visible: false, pendingAction: null, pendingSaveTracks: null })

// 弹窗打开/关闭 watch
watch(
  () => props.visible,
  (v) => {
    if (v) {
      cachedTracks = props.tracks.slice()
      initFieldStates()
      activeTab.value = 'file'
      // 切到歌词/封面 tab 时再加载
      loadLyrics()
    } else {
      cachedTracks = []
    }
  }
)

// tracks 改变时
watch(
  () => props.tracks,
  (newTracks, oldTracks) => {
    if (!props.visible) return
    if (newTracks === oldTracks) return
    const newIds = newTracks.map((t) => t.id).sort().join(',')
    const oldIds = (cachedTracks || []).map((t) => t.id).sort().join(',')
    if (newIds === oldIds) return

    // 检查所有 tab 的未保存状态
    if (hasDirty.value || lyricsDirty.value) {
      unsavedDialog.value = {
        visible: true,
        pendingAction: 'switch',
        pendingSaveTracks: cachedTracks.slice()
      }
      return
    }

    cachedTracks = newTracks.slice()
    initFieldStates()
    loadLyrics()
    hiddenCovers.value.clear()
  },
  { deep: true, immediate: false }
)

// 全局 dirty（所有 tab）
const globalDirty = computed(() => hasDirty.value || lyricsDirty.value)

function requestClose() {
  if (globalDirty.value) {
    unsavedDialog.value = {
      visible: true,
      pendingAction: 'close',
      pendingSaveTracks: null
    }
    return
  }
  emit('update:visible', false)
}

async function confirmUnsaved(action) {
  const pendingAction = unsavedDialog.value.pendingAction
  const saveTracks = unsavedDialog.value.pendingSaveTracks
  unsavedDialog.value = { visible: false, pendingAction: null, pendingSaveTracks: null }

  if (action === 'cancel') return

  if (action === 'save') {
    try {
      // 保存元数据
      if (hasDirty.value) {
        const node = authStore.localNode
        const tracksToSave = saveTracks || props.tracks
        if (node && tracksToSave.length > 0) {
          const dirtyFields = EDIT_FIELDS.filter((f) => fieldStates[f.key]?.isDirty)
          const updates = {}
          for (const f of dirtyFields) {
            updates[f.key] = fieldStates[f.key].value
          }
          await batchUpdateMetadata(node, tracksToSave.map((t) => t.id), updates)
        }
      }
      // 保存歌词（用 saveTracks 处理切换场景）
      if (lyricsDirty.value) {
        const node = authStore.localNode
        const tracksToSave = saveTracks || props.tracks
        if (node && tracksToSave.length > 0) {
          await batchWriteLyrics(node, tracksToSave.map((t) => t.id), lyricsText.value)
        }
      }
      emit('updated')
    } catch (e) {
      toast.error('保存失败', e?.message || '未知错误', e)
      return
    }
  } else {
    // discard
    resetAllMetadata()
    resetLyrics()
  }

  if (pendingAction === 'switch') {
    cachedTracks = props.tracks.slice()
    initFieldStates()
    loadLyrics()
    hiddenCovers.value.clear()
  } else {
    emit('update:visible', false)
  }
}

function onKeydown(e) {
  if (e.key === 'Escape' && props.visible) {
    e.preventDefault()
    e.stopPropagation()
    requestClose()
  }
}
if (typeof window !== 'undefined') {
  window.addEventListener('keydown', onKeydown)
}

// ==================== 概要 ====================

const selectedCount = computed(() => props.tracks.length)

// ==================== 文件信息格式化 ====================

function formatFileSize(bytes) {
  if (!bytes) return '--'
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`
}

function formatDuration(sec) {
  if (sec == null) return '--'
  const m = Math.floor(sec / 60)
  const s = Math.floor(sec % 60)
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}

function formatBitrate(bps) {
  if (!bps) return '--'
  return `${Math.round(bps / 1000)} kbps`
}

function formatSampleRate(hz) {
  if (!hz) return '--'
  if (hz >= 1000) return `${(hz / 1000).toFixed(1)} kHz`
  return `${hz} Hz`
}

function formatChannels(ch) {
  if (ch == null) return '--'
  if (ch === 1) return '单声道'
  if (ch === 2) return '立体声'
  return `${ch} 声道`
}

function formatBool(v) {
  return v ? '是' : '否'
}

function formatDateTime(dt) {
  if (!dt) return '--'
  try {
    const d = new Date(dt)
    return d.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch {
    return String(dt)
  }
}

function formatFileField(field, track) {
  const v = track[field]
  switch (field) {
    case 'file_size': return formatFileSize(v)
    case 'duration': return formatDuration(v)
    case 'bitrate': return formatBitrate(v)
    case 'sample_rate': return formatSampleRate(v)
    case 'channels': return formatChannels(v)
    case 'cover_embedded':
    case 'lyrics_embedded':
      return formatBool(v)
    case 'created_at':
    case 'updated_at':
      return formatDateTime(v)
    case 'ext':
      return v ? String(v).toUpperCase() : '--'
    default:
      return v ?? '--'
  }
}

// 文件字段值是否在多曲目间一致
function isFileFieldMixed(field) {
  if (props.tracks.length <= 1) return false
  const vals = props.tracks.map((t) => String(t[field] ?? ''))
  return new Set(vals).size > 1
}

function getFileFieldValue(field) {
  if (props.tracks.length === 0) return ''
  if (isFileFieldMixed(field)) return ''  // 混合时显示空
  return formatFileField(field, props.tracks[0])
}
</script>

<template>
  <Teleport to="body">
    <Transition name="drawer-slide">
      <div
        v-if="visible"
        class="fixed inset-0 z-[70] flex justify-end bg-black/40 backdrop-blur-sm"
        @click.self="requestClose"
      >
        <div class="relative flex h-full w-[min(560px,94vw)] flex-col overflow-hidden border-l border-border bg-popover shadow-2xl">
          <!-- 头部 -->
          <div class="flex items-center justify-between border-b border-border px-5 py-4">
            <div class="min-w-0">
              <div class="flex items-center gap-2">
                <Music class="h-4 w-4 shrink-0 text-primary" />
                <h3 class="truncate text-base font-semibold text-foreground">元数据编辑</h3>
              </div>
              <p class="mt-0.5 text-xs text-muted-foreground">
                {{ selectedCount }} 首曲目
                <template v-if="props.readonly">
                  · <span class="font-medium text-amber-500">节点离线·只读</span>
                </template>
                <template v-else-if="globalDirty">
                  · <span class="font-medium text-red-500">有未保存修改</span>
                </template>
              </p>
            </div>
            <button
              class="flex h-8 w-8 items-center justify-center rounded-full text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
              @click="requestClose"
              title="关闭 (Esc)"
            >
              <X class="h-4 w-4" />
            </button>
          </div>

          <!-- Tab 导航 -->
          <div class="relative flex border-b border-border bg-card/30">
            <button
              v-for="tab in TABS"
              :key="tab.key"
              class="relative flex flex-1 items-center justify-center gap-1.5 px-3 py-3 text-sm font-medium"
              :class="activeTab === tab.key
                ? 'text-primary'
                : 'text-muted-foreground hover:text-foreground'"
              @click="activeTab = tab.key"
            >
              <component :is="tab.icon" class="h-4 w-4" />
              {{ tab.label }}
              <span
                v-if="tab.key === 'metadata' && dirtyCount > 0"
                class="ml-0.5 inline-flex h-4 min-w-4 items-center justify-center rounded-full bg-red-500 px-1 text-[10px] font-semibold text-white"
              >{{ dirtyCount }}</span>
              <span
                v-if="tab.key === 'lyrics' && lyricsDirty"
                class="ml-0.5 inline-flex h-4 min-w-4 items-center justify-center rounded-full bg-red-500 px-1 text-[10px] font-semibold text-white"
              >•</span>
            </button>
            <!-- 滑动指示条 -->
            <div
              class="pointer-events-none absolute bottom-0 h-0.5 rounded-full bg-primary transition-all duration-200 ease-out"
              :style="{
                left: `calc(${TABS.findIndex(t => t.key === activeTab) * (100 / TABS.length)}% + 8px)`,
                width: `calc(${100 / TABS.length}% - 16px)`
              }"
            />
          </div>

          <!-- 内容区：所有 tab 内容绝对定位叠加，通过 opacity 切换，不触发重排 -->
          <div class="relative flex-1 min-h-0">
            <!-- 文件信息 -->
            <div
              class="absolute inset-0 overflow-auto px-5 py-4"
              :class="activeTab === 'file' ? 'opacity-100 z-10' : 'opacity-0 pointer-events-none'"
            >
              <div v-if="selectedCount === 0" class="py-16 text-center text-sm text-muted-foreground">
                未选择任何曲目
              </div>
              <template v-else>
                <div v-for="group in FILE_GROUPS" :key="group" class="mb-5">
                  <div class="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    {{ group }}
                  </div>
                  <div class="space-y-2">
                    <div
                      v-for="f in FILE_FIELDS.filter((x) => x.group === group)"
                      :key="f.key"
                      class="rounded-md p-2"
                    >
                      <div class="mb-1 flex items-center justify-between">
                        <Label class="text-xs text-muted-foreground">{{ f.label }}</Label>
                        <Badge
                          v-if="isFileFieldMixed(f.key)"
                          variant="secondary"
                          class="text-[10px]"
                        >混合</Badge>
                      </div>
                      <Input
                        :value="getFileFieldValue(f.key)"
                        disabled
                        class="h-8 bg-muted/40 text-muted-foreground select-text cursor-not-allowed"
                      />
                    </div>
                  </div>
                </div>
              </template>
            </div>

            <!-- 元数据 -->
            <div
              class="absolute inset-0 overflow-auto px-5 py-4"
              :class="activeTab === 'metadata' ? 'opacity-100 z-10' : 'opacity-0 pointer-events-none'"
            >
              <div v-if="selectedCount === 0" class="py-16 text-center text-sm text-muted-foreground">
                未选择任何曲目
              </div>
              <template v-else>
                <div v-for="group in EDIT_GROUPS" :key="group" class="mb-5">
                  <div class="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    {{ group }}
                  </div>
                  <div class="space-y-2">
                    <div
                      v-for="f in EDIT_FIELDS.filter((x) => x.group === group)"
                      :key="f.key"
                      class="rounded-md p-2 transition-colors"
                      :class="fieldStates[f.key]?.isDirty ? 'bg-red-500/5 ring-1 ring-red-500/30' : ''"
                    >
                      <div class="mb-1 flex items-center justify-between">
                        <Label class="text-xs text-muted-foreground">{{ f.label }}</Label>
                        <div class="flex items-center gap-1.5">
                          <Badge
                            v-if="fieldStates[f.key]?.isMixed"
                            variant="secondary"
                            class="text-[10px]"
                          >混合</Badge>
                          <Badge
                            v-if="fieldStates[f.key]?.isDirty"
                            variant="outline"
                            class="border-red-500 text-[10px] text-red-500"
                          >已修改</Badge>
                          <button
                            v-if="fieldStates[f.key]?.isDirty"
                            class="flex h-5 w-5 items-center justify-center rounded text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
                            title="撤销此字段修改"
                            @click="resetField(f.key)"
                          >
                            <RotateCcw class="h-3 w-3" />
                          </button>
                        </div>
                      </div>
                      <Input
                        v-model="fieldStates[f.key].value"
                        :type="f.type"
                        :placeholder="fieldStates[f.key]?.isMixed ? '混合值 - 输入新值覆盖全部' : '留空则清空'"
                        class="h-8 bg-background select-text"
                        :class="fieldStates[f.key]?.isDirty
                          ? 'border-red-500/50 focus-visible:ring-red-500/30'
                          : ''"
                        :disabled="saving || props.readonly"
                        @input="onFieldInput(f.key)"
                      />
                    </div>
                  </div>
                </div>
              </template>

              <!-- 元数据加载中提示 -->
              <div v-if="fieldsLoading" class="mt-3 flex items-center justify-center py-4">
                <Loader2 class="h-4 w-4 animate-spin text-primary" />
                <span class="ml-2 text-xs text-muted-foreground">读取文件标签...</span>
              </div>
            </div>

            <!-- 歌词 -->
            <div
              class="absolute inset-0 overflow-auto px-5 py-4"
              :class="activeTab === 'lyrics' ? 'opacity-100 z-10' : 'opacity-0 pointer-events-none'"
            >
              <div v-if="selectedCount === 0" class="py-16 text-center text-sm text-muted-foreground">
                未选择任何曲目
              </div>
              <template v-else>
                <div class="mb-3 flex items-center justify-between">
                  <div class="text-xs text-muted-foreground">
                    <template v-if="selectedCount === 1">
                      当前曲目: <span class="font-medium text-foreground">{{ tracks[0]?.title || '--' }}</span>
                    </template>
                    <template v-else>
                      将写入到 <span class="font-medium text-foreground">{{ selectedCount }}</span> 首曲目
                    </template>
                  </div>
                  <Badge
                    v-if="lyricsMixed"
                    variant="secondary"
                    class="text-[10px]"
                  >混合</Badge>
                </div>
                <div v-if="lyricsLoading" class="flex items-center justify-center py-12">
                  <Loader2 class="h-5 w-5 animate-spin text-primary" />
                  <span class="ml-2 text-sm text-muted-foreground">加载歌词...</span>
                </div>
                <textarea
                  v-else
                  v-model="lyricsText"
                  class="h-full min-h-[400px] w-full flex-1 resize-none rounded-md border border-border bg-background p-3 font-mono text-sm leading-relaxed text-foreground focus:outline-none focus:ring-2 focus:ring-primary/30 select-text"
                  :placeholder="lyricsMixed ? '多首曲目歌词不一致，输入新内容将覆盖全部' : '输入歌词（支持 LRC 时间戳格式）'"
                  :disabled="lyricsSaving || props.readonly"
                ></textarea>
                <div class="mt-3 flex items-center justify-between">
                  <Button
                    variant="ghost"
                    size="sm"
                    :disabled="!lyricsDirty || lyricsSaving || props.readonly"
                    @click="resetLyrics"
                  >
                    <RotateCcw class="h-3.5 w-3.5" />
                    撤销
                  </Button>
                  <Button
                    variant="gold"
                    size="sm"
                    :disabled="!lyricsDirty || lyricsSaving || props.readonly"
                    @click="saveLyrics"
                  >
                    <Save class="h-3.5 w-3.5" />
                    {{ lyricsSaving ? '保存中...' : '保存歌词' }}
                  </Button>
                </div>
              </template>
            </div>

            <!-- 封面 -->
            <div
              class="absolute inset-0 overflow-auto px-5 py-4"
              :class="activeTab === 'cover' ? 'opacity-100 z-10' : 'opacity-0 pointer-events-none'"
            >
              <div v-if="selectedCount === 0" class="py-16 text-center text-sm text-muted-foreground">
                未选择任何曲目
              </div>
              <template v-else>
                <div class="mb-3 flex items-center justify-between">
                  <div class="text-xs text-muted-foreground">
                    <template v-if="selectedCount === 1">
                      当前曲目封面
                    </template>
                    <template v-else>
                      {{ selectedCount }} 首曲目当前封面
                    </template>
                  </div>
                  <div class="flex gap-2">
                    <Button
                      variant="gold"
                      size="sm"
                      :disabled="coverUploading || selectedCount === 0 || props.readonly"
                      @click="triggerCoverUpload"
                    >
                      <Upload class="h-3.5 w-3.5" />
                      {{ coverUploading ? '上传中...' : (selectedCount > 1 ? '批量上传' : '上传封面') }}
                    </Button>
                    <Button
                      variant="destructive"
                      size="sm"
                      :disabled="coverRemoving || selectedCount === 0 || props.readonly"
                      @click="removeCover"
                    >
                      <Trash2 class="h-3.5 w-3.5" />
                      {{ coverRemoving ? '删除中...' : '删除封面' }}
                    </Button>
                  </div>
                </div>
                <input
                  ref="coverFileInput"
                  type="file"
                  accept="image/png,image/jpeg,image/webp"
                  class="hidden"
                  @change="onCoverFileChange"
                />
                <div class="grid grid-cols-2 gap-3 sm:grid-cols-3">
                  <div
                    v-for="t in tracks"
                    :key="t.id"
                    class="group relative overflow-hidden rounded-md border border-border bg-muted/30"
                  >
                    <div class="aspect-square w-full overflow-hidden">
                      <img
                        v-if="!hiddenCovers.has(t.id)"
                        :src="getTrackCoverUrl(t)"
                        :alt="t.title || ''"
                        class="h-full w-full object-cover"
                        @error="onCoverImgError(t.id, $event)"
                      />
                      <div v-else class="flex h-full w-full items-center justify-center">
                        <Image class="h-8 w-8 text-muted-foreground/30" />
                      </div>
                    </div>
                    <div class="truncate p-1.5 text-[11px] text-muted-foreground" :title="t.title">
                      {{ t.title || '--' }}
                    </div>
                  </div>
                </div>
                <p class="mt-4 text-xs text-muted-foreground">
                  提示：上传封面将覆盖所有选中曲目已嵌入的封面。支持 PNG / JPEG / WEBP。
                </p>
              </template>
            </div>
          </div>

          <!-- 底部操作栏（仅元数据 tab 显示保存按钮） -->
          <div
            v-show="activeTab === 'metadata' && selectedCount > 0"
            class="border-t border-border px-5 py-3"
          >
            <div class="flex items-center justify-between gap-2">
              <Button
                variant="ghost"
                size="sm"
                :disabled="!hasDirty || saving || props.readonly"
                @click="resetAllMetadata"
              >
                <RotateCcw class="h-3.5 w-3.5" />
                全部撤销
              </Button>
              <Button
                variant="gold"
                size="sm"
                :disabled="!hasDirty || saving || props.readonly"
                @click="saveMetadata"
              >
                <Save class="h-3.5 w-3.5" />
                {{ saving ? '保存中...' : `保存${dirtyCount > 0 ? ` (${dirtyCount})` : ''}` }}
              </Button>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>

  <!-- 未保存确认弹窗 -->
  <Dialog
    :open="unsavedDialog.visible"
    @update:open="(v) => (unsavedDialog.visible = v)"
  >
    <DialogContent class="max-w-md">
      <DialogHeader>
        <DialogTitle>
          {{ unsavedDialog.pendingAction === 'switch' ? '切换曲目' : '关闭' }}前有未保存的修改
        </DialogTitle>
        <DialogDescription>
          当前有
          <template v-if="dirtyCount > 0">{{ dirtyCount }} 个元数据字段</template>
          <template v-if="dirtyCount > 0 && lyricsDirty"> 和 </template>
          <template v-if="lyricsDirty">歌词</template>
          已修改但未保存。
          <template v-if="unsavedDialog.pendingAction === 'switch'">
            切换到其他曲目将丢失这些修改，是否先保存？
          </template>
          <template v-else>
            是否保存后再关闭？
          </template>
        </DialogDescription>
      </DialogHeader>
      <DialogFooter class="gap-2">
        <Button variant="ghost" @click="confirmUnsaved('cancel')">取消</Button>
        <Button variant="destructive" @click="confirmUnsaved('discard')">
          {{ unsavedDialog.pendingAction === 'switch' ? '不保存切换' : '不保存关闭' }}
        </Button>
        <Button variant="gold" @click="confirmUnsaved('save')">
          {{ unsavedDialog.pendingAction === 'switch' ? '保存并切换' : '保存并关闭' }}
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>

  <!-- 简易确认弹窗 -->
  <Dialog :open="_confirmState.visible" @update:open="(v) => (_confirmState.visible = v)">
    <DialogContent class="max-w-md">
      <DialogHeader>
        <DialogTitle>{{ _confirmState.title }}</DialogTitle>
        <DialogDescription>{{ _confirmState.message }}</DialogDescription>
      </DialogHeader>
      <DialogFooter class="gap-2">
        <Button variant="ghost" @click="_onConfirmCancel">取消</Button>
        <Button
          :variant="_confirmState.type === 'warning' ? 'destructive' : 'gold'"
          @click="_onConfirm"
        >确定</Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>

<style scoped>
.drawer-slide-enter-active,
.drawer-slide-leave-active {
  transition: opacity 0.2s ease;
}
.drawer-slide-enter-active > div,
.drawer-slide-leave-active > div {
  transition: transform 0.25s ease;
}
.drawer-slide-enter-from,
.drawer-slide-leave-to {
  opacity: 0;
}
.drawer-slide-enter-from > div,
.drawer-slide-leave-to > div {
  transform: translateX(100%);
}
</style>
