<template>
  <div class="login-page">
    <div class="login-header">
      <img src="/favicon.svg" alt="logo" class="logo" />
      <h1>企业服务中心</h1>
      <p>开发调试登录</p>
    </div>

    <van-notice-bar
      wrapable
      :scrollable="false"
      text="仅开发/测试环境可用；生产环境该接口会被后端拒绝。正式登录请使用登录页的账号密码登录或注册。"
      background="#fff7e6"
      color="#ed6a0c"
      class="login-notice"
    />

    <div class="login-form">
      <van-cell-group inset>
        <van-field v-model="form.enterpriseName" label="企业名称" placeholder="请输入企业名称" />
        <van-field v-model="form.creditCode" label="信用代码" placeholder="统一社会信用代码" />
        <van-field v-model="form.legalPersonName" label="法人姓名" placeholder="请输入法人姓名" />
        <van-field v-model="form.legalPersonIdNo" label="法人身份证" placeholder="身份证号" />
        <van-field v-model="form.legalPersonMobile" label="法人手机" placeholder="手机号" type="tel" />
      </van-cell-group>

      <div class="login-btn-wrap">
        <van-button type="primary" block @click="handleLogin">
          调试登录
        </van-button>
      </div>
      <p v-if="errorMsg" class="error-msg">{{ errorMsg }}</p>

      <div class="login-links">
        <span class="link" @click="router.push('/login')">返回正式登录页</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { showToast } from 'vant'
import { enterpriseMockLogin, getEnterpriseMe } from '@/api/auth'
import { useAuthStore } from '@/stores/auth'
import { resolveRedirectPath } from '@/utils/redirect'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

function navigateAfterLogin() {
  const redirect = route.query.redirect as string | undefined
  router.replace(resolveRedirectPath(redirect))
}
const errorMsg = ref('')

const form = ref({
  enterpriseName: '测试企业有限公司',
  creditCode: '91371000XXXXXXXXXX',
  legalPersonName: '张三',
  legalPersonIdNo: '370000000000000000',
  legalPersonMobile: '13800000000',
})

/** 从登录返回值中兼容解析 token */
function parseToken(res: unknown): string {
  if (!res || typeof res !== 'object') return ''
  const r = res as Record<string, unknown>
  const data = r.data && typeof r.data === 'object' ? (r.data as Record<string, unknown>) : null

  const candidates = [r.token, r.accessToken, r.access_token, data?.token, data?.accessToken, data?.access_token]
  for (const c of candidates) {
    if (typeof c === 'string' && c) return c
  }
  return ''
}

async function handleLogin() {
  errorMsg.value = ''

  try {
    const res = await enterpriseMockLogin(form.value)
    const token = parseToken(res)
    if (!token) {
      showToast('登录接口未返回 token')
      errorMsg.value = '登录接口未返回 token'
      return
    }

    authStore.applyToken(token)

    try {
      const me = await getEnterpriseMe()
      authStore.applyUser(me)
      showToast({ type: 'success', message: '登录成功' })
      navigateAfterLogin()
    } catch (meErr: unknown) {
      const ax = meErr as { message?: string }
      errorMsg.value = `Token 已保存，获取企业信息失败：${ax.message || '未知错误'}`
      navigateAfterLogin()
    }
  } catch (err: unknown) {
    const ax = err as { message?: string }
    errorMsg.value = ax.message || '登录失败'
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
.login-notice {
  margin: 0 16px 16px;
  position: relative;
  z-index: 1;
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
  position: relative;
  z-index: 2;
}
.login-btn-wrap :deep(.van-button) {
  pointer-events: auto;
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
  font-size: 13px;
  text-decoration: underline;
}
</style>
