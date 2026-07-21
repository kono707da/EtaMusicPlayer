<template>
  <div class="flex h-full flex-col">
    <!-- 顶部标题 -->
    <div class="flex items-center gap-3 mb-4">
      <Music class="h-5 w-5 text-primary" />
      <h2 class="text-lg font-semibold">网易云账号</h2>
      <Button v-if="store.isLoggedIn" variant="ghost" size="sm" @click="refreshing = true; store.refresh().finally(() => refreshing = false)">
        <RefreshCw v-if="refreshing" class="h-4 w-4 animate-spin" />
        <RefreshCw v-else class="h-4 w-4" />
        刷新
      </Button>
    </div>

    <div class="flex-1 min-h-0 overflow-auto">
      <!-- 已登录视图 -->
      <div v-if="store.isLoggedIn" class="flex flex-col gap-4 max-w-2xl">
        <!-- 当前账号卡片 -->
        <div class="rounded-lg border border-border bg-card/40 p-4 flex items-center gap-4">
          <img
            v-if="store.currentAccount?.avatar_url"
            :src="store.currentAccount.avatar_url"
            class="h-14 w-14 rounded-full border border-border"
            referrerpolicy="no-referrer"
          />
          <div v-else class="h-14 w-14 rounded-full bg-primary/20 flex items-center justify-center">
            <User class="h-7 w-7 text-primary" />
          </div>
          <div class="flex-1 min-w-0">
            <div class="font-medium truncate">{{ store.currentAccount?.nickname || '未知' }}</div>
            <div class="text-sm text-muted-foreground">
              UID: {{ store.currentAccount?.ncm_uid }}
              <Badge v-if="store.currentAccount?.vip_type > 0" variant="gold" class="ml-2">VIP</Badge>
            </div>
          </div>
          <Button variant="outline" size="sm" @click="openAddDialog">
            <QrCode class="h-4 w-4" />
            添加账号
          </Button>
        </div>

        <!-- 多账号列表 -->
        <div v-if="store.accounts.length > 1" class="rounded-lg border border-border bg-card/40">
          <div class="px-4 py-2 text-sm text-muted-foreground border-b border-border">所有账号（点击切换）</div>
          <div
            v-for="acc in store.accounts"
            :key="acc.ncm_uid"
            class="px-4 py-3 flex items-center gap-3 cursor-pointer hover:bg-accent/50 transition-colors border-b border-border last:border-b-0"
            :class="{ 'bg-primary/10': acc.ncm_uid === store.currentUid }"
            @click="switchTo(acc.ncm_uid)"
          >
            <img
              v-if="acc.avatar_url"
              :src="acc.avatar_url"
              class="h-10 w-10 rounded-full"
              referrerpolicy="no-referrer"
            />
            <div v-else class="h-10 w-10 rounded-full bg-muted flex items-center justify-center">
              <User class="h-5 w-5 text-muted-foreground" />
            </div>
            <div class="flex-1 min-w-0">
              <div class="font-medium truncate">{{ acc.nickname || '未知' }}</div>
              <div class="text-xs text-muted-foreground">UID: {{ acc.ncm_uid }}</div>
            </div>
            <Badge v-if="acc.ncm_uid === store.currentUid" variant="gold">当前</Badge>
            <Button
              variant="ghost"
              size="sm"
              class="text-destructive hover:text-destructive"
              @click.stop="confirmDelete(acc)"
            >
              <Trash2 class="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>

      <!-- 未登录视图：扫码登录 -->
      <div v-else class="flex items-start justify-center pt-4">
        <div class="w-full max-w-md rounded-lg border border-border bg-card/40 p-6 flex flex-col gap-5 shadow-sm">
          <div class="text-center">
            <Music class="h-10 w-10 text-primary mx-auto mb-2" />
            <h3 class="text-lg font-semibold">扫码登录网易云音乐</h3>
            <p class="text-sm text-muted-foreground mt-1">使用网易云 App 扫描下方二维码</p>
          </div>

          <!-- 二维码区域 -->
          <div class="flex flex-col items-center gap-3">
            <div class="relative w-64 h-64 border border-border rounded-lg overflow-hidden bg-white flex items-center justify-center">
              <img
                v-if="qrcodeImageUrl"
                :src="qrcodeImageUrl"
                class="w-full h-full object-contain"
                alt="登录二维码"
              />
              <Loader2 v-else class="h-8 w-8 animate-spin text-muted-foreground" />

              <!-- 遮罩：已过期 -->
              <div v-if="qrcodeStatus === 800" class="absolute inset-0 bg-black/60 flex flex-col items-center justify-center gap-2 text-white">
                <p class="text-sm">二维码已过期</p>
                <Button variant="gold" size="sm" @click="startQrcodeLogin">重新生成</Button>
              </div>

              <!-- 遮罩：已扫码 -->
              <div v-if="qrcodeStatus === 802" class="absolute inset-0 bg-black/60 flex flex-col items-center justify-center gap-2 text-white">
                <CheckCircle2 class="h-8 w-8" />
                <p class="text-sm">已扫码，请在手机上确认</p>
              </div>
            </div>

            <!-- 状态提示 -->
            <div class="text-sm text-center min-h-[20px]">
              <span v-if="qrcodeStatus === 801" class="text-muted-foreground">等待扫码...</span>
              <span v-else-if="qrcodeStatus === 802" class="text-primary">已扫码，等待确认</span>
              <span v-else-if="qrcodeStatus === 803" class="text-primary">登录成功！</span>
              <span v-else-if="qrcodeStatus === 800" class="text-destructive">二维码已过期</span>
              <span v-else-if="qrcodeStatus === 8821" class="text-destructive">风控拒绝，请稍后重试</span>
            </div>
          </div>

          <Button variant="ghost" size="sm" @click="startQrcodeLogin" :disabled="qrLoading">
            <RefreshCw v-if="qrLoading" class="h-4 w-4 animate-spin" />
            <RefreshCw v-else class="h-4 w-4" />
            刷新二维码
          </Button>
        </div>
      </div>

      <!-- 添加账号的弹窗（已登录时点"添加账号"） -->
      <Dialog v-model:open="showAddDialog">
        <DialogContent class="max-w-md">
          <DialogHeader>
            <DialogTitle>添加网易云账号</DialogTitle>
            <DialogDescription>扫描二维码登录新账号，登录后可免扫码切换</DialogDescription>
          </DialogHeader>

          <div class="flex flex-col items-center gap-3 py-2">
            <div class="relative w-64 h-64 border border-border rounded-lg overflow-hidden bg-white flex items-center justify-center">
              <img
                v-if="qrcodeImageUrl"
                :src="qrcodeImageUrl"
                class="w-full h-full object-contain"
                alt="登录二维码"
              />
              <Loader2 v-else class="h-8 w-8 animate-spin text-muted-foreground" />

              <div v-if="qrcodeStatus === 800" class="absolute inset-0 bg-black/60 flex flex-col items-center justify-center gap-2 text-white">
                <p class="text-sm">二维码已过期</p>
                <Button variant="gold" size="sm" @click="startQrcodeLogin">重新生成</Button>
              </div>
              <div v-if="qrcodeStatus === 802" class="absolute inset-0 bg-black/60 flex flex-col items-center justify-center gap-2 text-white">
                <CheckCircle2 class="h-8 w-8" />
                <p class="text-sm">已扫码，请在手机上确认</p>
              </div>
            </div>

            <div class="text-sm text-center min-h-[20px]">
              <span v-if="qrcodeStatus === 801" class="text-muted-foreground">等待扫码...</span>
              <span v-else-if="qrcodeStatus === 802" class="text-primary">已扫码，等待确认</span>
              <span v-else-if="qrcodeStatus === 803" class="text-primary">登录成功！</span>
              <span v-else-if="qrcodeStatus === 800" class="text-destructive">二维码已过期</span>
              <span v-else-if="qrcodeStatus === 8821" class="text-destructive">风控拒绝，请稍后重试</span>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  </div>
</template>

<script setup>
/**
 * 网易云账号视图
 *
 * 依赖通过 window.__etamusic 取用（vue/pinia/ui/icons），
 * store 和 api 通过相对路径 import（同一插件包内）。
 */
const { ref, onMounted, onUnmounted } = window.__etamusic.vue
const { Music, User, QrCode, RefreshCw, Loader2, CheckCircle2, Trash2 } = window.__etamusic.icons
const {
  Button, Badge,
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription,
  useToast
} = window.__etamusic.ui

import { useNeteaseStore } from '../store'
import { getQrcodeKey, getQrcodeImage, pollQrcodeStatus } from '../api'

const toast = useToast()
const store = useNeteaseStore()

const refreshing = ref(false)
const showAddDialog = ref(false)

// 二维码登录状态
const qrcodeImageUrl = ref('')
const qrcodeUnikey = ref('')
const qrcodeStatus = ref(0) // 0=未开始, 801=等待扫码, 802=已扫码, 803=成功, 800=过期, 8821=风控
const qrLoading = ref(false)
let pollTimer = null

/**
 * 打开添加账号弹窗并启动二维码登录
 */
function openAddDialog() {
  showAddDialog.value = true
  startQrcodeLogin()
}

/**
 * 启动二维码登录流程
 */
async function startQrcodeLogin() {
  // 清理旧状态
  stopPolling()
  qrcodeImageUrl.value = ''
  qrcodeStatus.value = 0
  qrLoading.value = true

  try {
    const data = await getQrcodeKey()
    if (!data.unikey) {
      toast.error('获取二维码 key 失败', '后端未返回 unikey')
      return
    }
    qrcodeUnikey.value = data.unikey
    qrcodeImageUrl.value = getQrcodeImage(data.unikey)
    qrcodeStatus.value = 801
    startPolling()
  } catch (e) {
    toast.error('二维码登录启动失败', e.message || String(e))
    qrcodeStatus.value = 0
  } finally {
    qrLoading.value = false
  }
}

/**
 * 开始轮询扫码状态
 */
function startPolling() {
  stopPolling()
  pollTimer = setInterval(async () => {
    if (!qrcodeUnikey.value) {
      stopPolling()
      return
    }
    try {
      const data = await pollQrcodeStatus(qrcodeUnikey.value)
      qrcodeStatus.value = data.code || 0

      if (data.code === 803) {
        // 登录成功
        stopPolling()
        toast.success('网易云登录成功')
        await store.onLoginSuccess()
        showAddDialog.value = false
        qrcodeImageUrl.value = ''
        qrcodeUnikey.value = ''
      } else if (data.code === 800 || data.code === 8821) {
        // 过期或风控，停止轮询
        stopPolling()
      }
    } catch (e) {
      // 网络错误，继续轮询
      console.error('轮询扫码状态失败:', e)
    }
  }, 2000)
}

/**
 * 停止轮询
 */
function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

/**
 * 切换账号
 */
async function switchTo(ncmUid) {
  if (ncmUid === store.currentUid) return
  try {
    await store.switchTo(ncmUid)
    toast.success('已切换账号')
  } catch (e) {
    toast.error('切换账号失败', e.message || String(e))
  }
}

/**
 * 确认删除账号
 */
async function confirmDelete(acc) {
  if (!confirm(`确定要删除账号「${acc.nickname}」吗？\n删除后需要重新扫码登录。`)) return
  try {
    await store.remove(acc.ncm_uid)
    toast.success('已删除账号')
  } catch (e) {
    toast.error('删除账号失败', e.message || String(e))
  }
}

onMounted(() => {
  if (!store.loaded) {
    store.load()
  }
})

onUnmounted(() => {
  stopPolling()
})
</script>
