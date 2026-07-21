/**
 * 网易云账号状态 Pinia store
 *
 * 不打包 pinia，运行时从 window.__etamusic.pinia 取用。
 */
const { defineStore } = window.__etamusic.pinia
const { ref, computed } = window.__etamusic.vue

import { listAccounts, switchAccount, deleteAccount, refreshLogin } from './api'

export const useNeteaseStore = defineStore('netease', () => {
  const accounts = ref([])
  const currentUid = ref(null)

  const currentAccount = computed(() =>
    accounts.value.find((a) => String(a.ncm_uid) === String(currentUid.value)) || null
  )

  const isLoggedIn = computed(() => !!currentAccount.value)

  async function load() {
    try {
      const data = await listAccounts()
      accounts.value = data.accounts || []
      currentUid.value = data.current || (accounts.value[0]?.ncm_uid ?? null)
    } catch (e) {
      accounts.value = []
      currentUid.value = null
    }
  }

  async function switchTo(ncmUid) {
    const r = await switchAccount(ncmUid)
    currentUid.value = String(ncmUid)
    // 更新本地账号列表中对应账号的信息
    const idx = accounts.value.findIndex((a) => String(a.ncm_uid) === String(ncmUid))
    if (idx >= 0 && r.account) {
      accounts.value[idx] = { ...accounts.value[idx], ...r.account }
    }
  }

  async function remove(ncmUid) {
    await deleteAccount(ncmUid)
    accounts.value = accounts.value.filter((a) => String(a.ncm_uid) !== String(ncmUid))
    if (String(currentUid.value) === String(ncmUid)) {
      currentUid.value = accounts.value[0]?.ncm_uid ?? null
    }
  }

  async function refresh() {
    try {
      await refreshLogin()
    } catch (e) {
      // 静默失败
    }
  }

  /**
   * 扫码登录成功后调用
   * @param {object} account 登录返回的账号信息
   */
  function onLoginSuccess(account) {
    if (!account || !account.ncm_uid) return
    const idx = accounts.value.findIndex((a) => String(a.ncm_uid) === String(account.ncm_uid))
    if (idx >= 0) {
      accounts.value[idx] = { ...accounts.value[idx], ...account }
    } else {
      accounts.value.push(account)
    }
    currentUid.value = String(account.ncm_uid)
  }

  return {
    accounts,
    currentUid,
    currentAccount,
    isLoggedIn,
    load,
    switchTo,
    remove,
    refresh,
    onLoginSuccess
  }
})
