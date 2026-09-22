<template>
  <div class="login-page">
    <div class="login-box">
      <h1 class="login-title">企业服务中心管理端</h1>

      <el-alert
        v-if="errorMsg"
        :title="errorMsg"
        type="error"
        show-icon
        :closable="false"
        style="margin-bottom: 16px; word-break: break-all"
      />

      <!-- 正式登录：统一身份认证（BSPPLUS）账号密码。角色/区划/数据权限一律不在
           这里选择——全部由本系统"管理员管理"预先分配，登录只做身份核验。 -->
      <el-form :model="form" label-width="80px" class="login-form" @submit.prevent="handleLogin">
        <el-form-item label="账号">
          <el-input v-model="form.username" autocomplete="username" placeholder="统一身份平台账号" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input
            v-model="form.password"
            type="password"
            show-password
            autocomplete="current-password"
            placeholder="统一身份平台密码"
            @keyup.enter="handleLogin"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" style="width: 100%" @click="handleLogin">
            登录
          </el-button>
        </el-form-item>
      </el-form>

      <!-- 开发调试登录：仅开发构建（import.meta.env.DEV）渲染，生产构建产物里
           不含这段代码；后端 /api/auth/admin/mock-login 在生产环境本身也会
           返回 404（见 app/api/auth/router.py），前后端双重把关。 -->
      <template v-if="isDev">
        <el-divider>开发调试登录（仅开发环境）</el-divider>
        <el-form :model="mockForm" label-width="100px" class="login-form">
          <el-form-item label="用户ID">
            <el-input v-model="mockForm.platformUserId" />
          </el-form-item>
          <el-form-item label="用户名">
            <el-input v-model="mockForm.username" />
          </el-form-item>
          <el-form-item label="真实姓名">
            <el-input v-model="mockForm.realName" />
          </el-form-item>
          <el-form-item label="部门ID">
            <el-input v-model="mockForm.departmentId" />
          </el-form-item>
          <el-form-item label="部门名称">
            <el-input v-model="mockForm.departmentName" />
          </el-form-item>
          <el-form-item label="区域代码">
            <el-input v-model="mockForm.regionCode" />
          </el-form-item>
          <el-form-item label="区域名称">
            <el-input v-model="mockForm.regionName" />
          </el-form-item>
          <el-form-item label="角色">
            <el-select v-model="mockForm.roleCodes" multiple style="width: 100%" placeholder="选择一个或多个角色">
              <el-option v-for="r in ROLE_OPTIONS" :key="r.value" :label="r.label" :value="r.value" />
            </el-select>
          </el-form-item>
          <el-form-item label="数据范围">
            <el-select v-model="mockForm.dataScope" style="width: 100%">
              <el-option label="全部（市级/平台）" value="ALL" />
              <el-option label="本区县/本企服中心" value="REGION" />
              <el-option label="本部门" value="DEPARTMENT" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button :loading="mockLoading" style="width: 100%" @click="handleMockLogin">
              模拟登录
            </el-button>
          </el-form-item>
        </el-form>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ADMIN_ROLE_OPTIONS } from '@/constants/permission'

const router = useRouter()
const authStore = useAuthStore()
const loading = ref(false)
const mockLoading = ref(false)
const errorMsg = ref('')
const isDev = import.meta.env.DEV

const form = ref({
  username: '',
  password: '',
})

function _describeError(err: unknown): string {
  const e = err as Error & { code?: string; response?: { status: number; data?: { message?: string } } }
  if (import.meta.env.DEV) console.error('[Login] failed:', e)
  if (e.code === 'ERR_NETWORK') {
    return '无法连接后端，请确认服务已启动且 Vite proxy 配置正确'
  }
  return e.message || '登录失败，请检查控制台'
}

async function handleLogin() {
  errorMsg.value = ''
  if (!form.value.username || !form.value.password) {
    errorMsg.value = '请输入账号和密码'
    return
  }
  loading.value = true
  try {
    await authStore.loginWithPassword({ username: form.value.username, password: form.value.password })
    router.push('/dashboard')
  } catch (err: unknown) {
    errorMsg.value = _describeError(err)
  } finally {
    // 密码只应活在这次请求的生命周期内：无论成功失败，提交后立即清空，
    // 不在表单/内存里继续保留明文密码。
    form.value.password = ''
    loading.value = false
  }
}

// ── 开发调试登录（仅 DEV 构建）──────────────────────────────────────────────────
const ROLE_OPTIONS = ADMIN_ROLE_OPTIONS

const mockForm = ref({
  platformUserId: 'u001',
  username: 'admin',
  realName: '管理员',
  departmentId: 'dept001',
  departmentName: '企业服务中心',
  regionCode: '371000',
  regionName: '威海市',
  dataScope: 'REGION',
  roleCodes: ['CENTER_ADMIN'] as string[],
})

async function handleMockLogin() {
  errorMsg.value = ''
  mockLoading.value = true
  try {
    await authStore.login({ ...mockForm.value })
    router.push('/dashboard')
  } catch (err: unknown) {
    errorMsg.value = _describeError(err)
  } finally {
    mockLoading.value = false
  }
}
</script>

<style scoped lang="scss">
.login-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
}

.login-box {
  background: #fff;
  border-radius: 8px;
  padding: 40px;
  width: 480px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);

  .login-title {
    text-align: center;
    font-size: 20px;
    font-weight: 700;
    color: #1a1a1a;
    margin-bottom: 32px;
  }

  .login-form {
    :deep(.el-form-item) {
      margin-bottom: 16px;
    }
  }
}
</style>
