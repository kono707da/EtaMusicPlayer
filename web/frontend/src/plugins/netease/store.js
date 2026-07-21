import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  listAccounts,
  switchAccount,
  deleteAccount,
  getLoginStatus,
  refreshLogin
} from './api'

export const useNeteaseStore = defineStore('netease', () => {
  // 账号列表
  const accounts = ref([])
  // 当前账号 ncm_uid
  const currentUid = ref(null)
  // 当前账号详情（含 nickname/avatar_url/vip_type）
  const currentAccount = ref(null)
  const loaded = ref(false)
  const loading = ref(false)

  const isLoggedIn = computed(() => !!currentUid.value)

  /**
   * 加载账号列表和当前登录状态
   */
  async function load() {
    loading.value = true
    try {
      const data = await listAccounts()
      accounts.value = data.accounts || []
      currentUid.value = data.current || null
      const cur = accounts.value.find((a) => a.ncm_uid === currentUid.value)
      currentAccount.value = cur || null
    } catch (e) {
      accounts.value = []
      currentUid.value = null
      currentAccount.value = null
    } finally {
      loaded.value = true
      loading.value = false
    }
  }

  /**
   * 切换账号
   */
  async function switchTo(ncmUid) {
    const data = await switchAccount(ncmUid)
    currentUid.value = data.account?.ncm_uid || ncmUid
    // 更新本地列表中的当前标记
    accounts.value = accounts.value.map((a) => ({
      ...a,
      is_current: a.ncm_uid === currentUid.value
    }))
    const cur = accounts.value.find((a) => a.ncm_uid === currentUid.value)
    currentAccount.value = cur || data.account || null
    return data
  }

  /**
   * 删除账号（退出登录）
   */
  async function remove(ncmUid) {
    await deleteAccount(ncmUid)
    accounts.value = accounts.value.filter((a) => a.ncm_uid !== ncmUid)
    if (currentUid.value === ncmUid) {
      currentUid.value = accounts.value[0]?.ncm_uid || null
      currentAccount.value = accounts.value[0] || null
    }
  }

  /**
   * 刷新登录状态（cookie 续期）
   */
  async function refresh() {
    await refreshLogin()
    await load()
  }

  /**
   * 登录成功后调用，刷新账号列表
   */
  async function onLoginSuccess() {
    await load()
  }

  return {
    accounts,
    currentUid,
    currentAccount,
    loaded,
    loading,
    isLoggedIn,
    load,
    switchTo,
    remove,
    refresh,
    onLoginSuccess
  }
})
