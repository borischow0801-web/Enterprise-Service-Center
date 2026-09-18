<template>
  <div class="register-page">
    <div class="register-header">
      <h1>企业注册</h1>
      <p>使用统一社会信用代码创建企业账号</p>
    </div>

    <div class="register-form">
      <van-cell-group inset>
        <van-field
          v-model="form.enterpriseName"
          label="企业名称"
          placeholder="请输入企业名称"
          required
        />
        <van-field
          v-model="form.creditCode"
          label="信用代码"
          placeholder="请输入统一社会信用代码"
          maxlength="18"
          required
        />
        <van-field
          v-model="form.contactName"
          label="联系人"
          placeholder="请输入联系人姓名"
          required
        />
        <van-field
          v-model="form.contactMobile"
          label="手机号"
          type="tel"
          placeholder="请输入联系手机号"
          maxlength="11"
          required
        />
        <van-field
          v-model="form.password"
          type="password"
          label="密码"
          placeholder="至少8位，需同时包含字母和数字"
          required
        />
        <van-field
          v-model="form.confirmPassword"
          type="password"
          label="确认密码"
          placeholder="请再次输入密码"
          required
        />
      </van-cell-group>

      <div class="agreement-wrap">
        <van-checkbox v-model="agreed" shape="square" icon-size="16px">
          我已阅读并同意相关服务条款
        </van-checkbox>
      </div>

      <div class="submit-btn-wrap">
        <van-button type="primary" block :loading="loading" @click="handleRegister">
          注册
        </van-button>
      </div>
      <p v-if="errorMsg" class="error-msg">{{ errorMsg }}</p>

      <div class="login-links">
        <span class="link" @click="goLogin">已有账号？返回登录</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { showToast } from 'vant'
import { registerEnterprise, getEnterpriseMe } from '@/api/auth'
import { useAuthStore } from '@/stores/auth'
import { resolveRedirectPath } from '@/utils/redirect'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const loading = ref(false)
const agreed = ref(false)
const errorMsg = ref('')
const form = ref({
  enterpriseName: '',
  creditCode: '',
  contactName: '',
  contactMobile: '',
  password: '',
  confirmPassword: '',
})

const CREDIT_CODE_RE = /^[0-9A-Za-z]{18}$/
const MOBILE_RE = /^1[3-9]\d{9}$/

function goLogin() {
  const redirect = route.query.redirect as string | undefined
  router.push({ path: '/login', query: redirect ? { redirect } : {} })
}

function validate(): string | null {
  const f = form.value
  if (!f.enterpriseName.trim()) return '请输入企业名称'
  if (!CREDIT_CODE_RE.test(f.creditCode.trim())) return '统一社会信用代码格式不正确，应为18位数字/字母'
  if (!f.contactName.trim()) return '请输入联系人姓名'
  if (!MOBILE_RE.test(f.contactMobile.trim())) return '手机号格式不正确'
  if (f.password.length < 8) return '密码长度不能少于8位'
  if (!/[A-Za-z]/.test(f.password) || !/\d/.test(f.password)) return '密码必须同时包含字母和数字'
  if (f.password !== f.confirmPassword) return '两次输入的密码不一致'
  if (!agreed.value) return '请先阅读并同意相关服务条款'
  return null
}

async function handleRegister() {
  errorMsg.value = ''
  const err = validate()
  if (err) {
    errorMsg.value = err
    return
  }

  loading.value = true
  try {
    const data = await registerEnterprise({
      enterpriseName: form.value.enterpriseName.trim(),
      creditCode: form.value.creditCode.trim().toUpperCase(),
      contactName: form.value.contactName.trim(),
      contactMobile: form.value.contactMobile.trim(),
      password: form.value.password,
      confirmPassword: form.value.confirmPassword,
    })

    // 注册成功后自动完成登录：后端已返回可用 token，无需用户再手动登录一次。
    authStore.applyToken(data.accessToken)
    try {
      const me = await getEnterpriseMe()
      authStore.applyUser(me)
    } catch {
      // 不阻断注册流程
    }
    showToast({ type: 'success', message: '注册成功' })
    const redirect = route.query.redirect as string | undefined
    router.replace(resolveRedirectPath(redirect))
  } catch (e: unknown) {
    const ax = e as { message?: string }
    errorMsg.value = ax.message || '注册失败，请稍后重试'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.register-page {
  min-height: 100vh;
  background: linear-gradient(160deg, var(--esc-primary) 0%, var(--esc-primary-dark) 100%);
  padding: 0 0 40px;
}
.register-header {
  padding: 40px 20px 20px;
  text-align: center;
  color: #fff;
}
.register-header h1 {
  font-size: 20px;
  font-weight: 700;
  margin-bottom: 8px;
}
.register-header p {
  font-size: 13px;
  opacity: 0.8;
}
.register-form :deep(.van-cell-group) {
  border-radius: 12px;
}
.agreement-wrap {
  margin: 16px 20px 0;
  color: #fff;
  font-size: 13px;
}
.agreement-wrap :deep(.van-checkbox__label) {
  color: #fff;
}
.submit-btn-wrap {
  margin: 20px 16px 0;
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
</style>
