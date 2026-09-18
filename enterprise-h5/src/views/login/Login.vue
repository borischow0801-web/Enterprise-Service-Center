<template>
  <div class="login-page">
    <div class="login-header">
      <img src="/favicon.svg" alt="logo" class="logo" />
      <h1>企业服务中心</h1>
      <p>企业登录</p>
    </div>

    <div class="login-form">
      <van-cell-group inset>
        <van-field
          v-model="form.creditCode"
          label="信用代码"
          placeholder="请输入统一社会信用代码"
          maxlength="18"
        />
        <van-field
          v-model="form.password"
          type="password"
          label="密码"
          placeholder="请输入密码"
        />
      </van-cell-group>

      <div class="login-btn-wrap">
        <van-button type="primary" block :loading="loading" @click="handleLogin">
          登录
        </van-button>
      </div>
      <p v-if="errorMsg" class="error-msg">{{ errorMsg }}</p>

      <div class="login-links">
        <span class="link" @click="goRegister">还没有账号？立即注册</span>
      </div>

      <div class="sso-wrap">
        <van-button plain block disabled>
          省统一身份认证登录
        </van-button>
        <p class="sso-hint">该功能暂未开放，敬请期待</p>
      </div>

      <div v-if="isDev" class="dev-links">
        <span class="link" @click="goDevLogin">开发调试登录</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { showToast } from 'vant'
import { loginEnterprise } from '@/api/auth'
import { getEnterpriseMe } from '@/api/auth'
import { useAuthStore } from '@/stores/auth'
import { resolveRedirectPath } from '@/utils/redirect'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const isDev = import.meta.env.DEV
const loading = ref(false)
const errorMsg = ref('')
const form = ref({
  creditCode: '',
  password: '',
})

function navigateAfterLogin() {
  const redirect = route.query.redirect as string | undefined
  router.replace(resolveRedirectPath(redirect))
}

function goRegister() {
  const redirect = route.query.redirect as string | undefined
  router.push({ path: '/register', query: redirect ? { redirect } : {} })
}

function goDevLogin() {
  router.push('/dev-login')
}

async function handleLogin() {
  errorMsg.value = ''
  if (!form.value.creditCode || !form.value.password) {
    errorMsg.value = '请输入统一社会信用代码和密码'
    return
  }

  loading.value = true
  try {
    const data = await loginEnterprise({
      creditCode: form.value.creditCode.trim(),
      password: form.value.password,
    })
    authStore.applyToken(data.accessToken)
    try {
      const me = await getEnterpriseMe()
      authStore.applyUser(me)
    } catch {
      // /me 失败不阻断登录，业务页面会按未登录态自然重新校验
    }
    showToast({ type: 'success', message: '登录成功' })
    navigateAfterLogin()
  } catch (err: unknown) {
    const e = err as { message?: string }
    errorMsg.value = e.message || '登录失败，请稍后重试'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  background: linear-gradient(160deg, var(--esc-primary) 0%, var(--esc-primary-dark) 100%);
  padding: 0 0 40px;
  position: relative;
  z-index: 0;
}
.login-header {
  padding: 60px 20px 24px;
  text-align: center;
  color: #fff;
  pointer-events: none;
}
.login-header .logo {
  width: 60px;
  height: 60px;
  margin-bottom: 16px;
  filter: brightness(10);
}
.login-header h1 {
  font-size: 22px;
  font-weight: 700;
  margin-bottom: 8px;
}
.login-header p {
  font-size: 14px;
  opacity: 0.8;
}
.login-form {
  position: relative;
  z-index: 1;
  pointer-events: auto;
}
.login-form :deep(.van-cell-group) {
  border-radius: 12px;
}
.login-btn-wrap {
  margin: 24px 16px 0;
}
.error-msg {
  text-align: center;
  color: #ee0a24;
  font-size: 13px;
  margin-top: 12px;
  padding: 0 16px;
}
.login-links {
  text-align: center;
  margin-top: 16px;
}
.link {
  color: #fff;
  font-size: 14px;
  text-decoration: underline;
}
.sso-wrap {
  margin: 32px 16px 0;
}
.sso-hint {
  text-align: center;
  color: rgba(255, 255, 255, 0.7);
  font-size: 12px;
  margin-top: 8px;
}
.dev-links {
  text-align: center;
  margin-top: 24px;
}
.dev-links .link {
  color: rgba(255, 255, 255, 0.5);
  font-size: 12px;
}
</style>
