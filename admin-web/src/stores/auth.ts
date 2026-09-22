import { defineStore } from 'pinia'
import { ref } from 'vue'
import {
  adminLogin,
  adminMockLogin,
  getAdminMe,
  type AdminLoginParams,
  type AdminPasswordLoginParams,
  type AdminUser,
} from '@/api/auth'
import { setToken, setUser, clearAuth, getToken, getUser } from '@/utils/token'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string>(getToken())
  const user = ref<AdminUser | null>(getUser() as AdminUser | null)

  async function _afterLogin(result: { accessToken: string }) {
    token.value = result.accessToken
    setToken(result.accessToken)
    const me = await getAdminMe()
    user.value = me
    setUser(me)
  }

  /** 正式登录：统一身份认证（BSPPLUS）账号密码。 */
  async function loginWithPassword(params: AdminPasswordLoginParams) {
    const result = await adminLogin(params)
    await _afterLogin(result)
  }

  /** 模拟登录：仅开发/测试环境可用，生产环境后端会直接拒绝（404）。 */
  async function login(params: AdminLoginParams) {
    const result = await adminMockLogin(params)
    await _afterLogin(result)
  }

  function logout() {
    token.value = ''
    user.value = null
    clearAuth()
  }

  function isLoggedIn() {
    return !!token.value
  }

  return { token, user, login, loginWithPassword, logout, isLoggedIn }
})
