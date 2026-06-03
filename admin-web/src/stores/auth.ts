import { defineStore } from 'pinia'
import { ref } from 'vue'
import { adminMockLogin, getAdminMe, type AdminLoginParams, type AdminUser } from '@/api/auth'
import { setToken, setUser, clearAuth, getToken, getUser } from '@/utils/token'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string>(getToken())
  const user = ref<AdminUser | null>(getUser() as AdminUser | null)

  async function login(params: AdminLoginParams) {
    const result = await adminMockLogin(params)
    token.value = result.accessToken
    setToken(result.accessToken)
    const me = await getAdminMe()
    user.value = me
    setUser(me)
  }

  function logout() {
    token.value = ''
    user.value = null
    clearAuth()
  }

  function isLoggedIn() {
    return !!token.value
  }

  return { token, user, login, logout, isLoggedIn }
})
