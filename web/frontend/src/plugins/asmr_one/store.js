import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getAuthStatus, login as apiLogin, logout as apiLogout, register as apiRegister } from './api'

export const useAsmrAccountStore = defineStore('asmrAccount', () => {
  const loggedIn = ref(false)
  const user = ref(null)
  const regEnabled = ref(false)
  const loaded = ref(false)
  const loading = ref(false)

  const isLoggedIn = computed(() => loggedIn.value)

  async function load() {
    loading.value = true
    try {
      const data = await getAuthStatus()
      loggedIn.value = data.logged_in
      user.value = data.user
      regEnabled.value = data.reg_enabled
    } catch (e) {
      loggedIn.value = false
      user.value = null
    } finally {
      loaded.value = true
      loading.value = false
    }
  }

  async function login(name, password) {
    const data = await apiLogin(name, password)
    loggedIn.value = data.logged_in
    user.value = data.user
    return data
  }

  async function register(name, password, recommenderUuid = null) {
    const data = await apiRegister(name, password, recommenderUuid)
    if (data.token_saved) {
      loggedIn.value = true
      user.value = data.user
    }
    return data
  }

  async function logout() {
    await apiLogout()
    loggedIn.value = false
    user.value = null
  }

  return {
    loggedIn,
    user,
    regEnabled,
    loaded,
    loading,
    isLoggedIn,
    load,
    login,
    register,
    logout
  }
})
