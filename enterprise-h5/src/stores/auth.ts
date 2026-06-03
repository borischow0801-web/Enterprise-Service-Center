import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getEnterpriseMe, type EnterpriseUser } from '@/api/auth'
import { setToken, setUser, clearAuth, getToken, getUser } from '@/utils/token'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string>(getToken())
  const user = ref<EnterpriseUser | null>(getUser() as EnterpriseUser | null)

  function applyToken(accessToken: string) {
    token.value = accessToken
    setToken(accessToken)
  }

  function applyUser(enterprise: EnterpriseUser) {
    user.value = enterprise
    setUser(enterprise)
  }

  async function fetchEnterpriseMe() {
    const me = await getEnterpriseMe()
    applyUser(me)
    return me
  }

  function logout() {
    token.value = ''
    user.value = null
    clearAuth()
  }

  function isLoggedIn() {
    return !!token.value
  }

  return { token, user, applyToken, applyUser, fetchEnterpriseMe, logout, isLoggedIn }
})
