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

      <el-form :model="form" label-width="100px" class="login-form">
        <el-form-item label="用户ID">
          <el-input v-model="form.platformUserId" />
        </el-form-item>
        <el-form-item label="用户名">
          <el-input v-model="form.username" />
        </el-form-item>
        <el-form-item label="真实姓名">
          <el-input v-model="form.realName" />
        </el-form-item>
        <el-form-item label="部门ID">
          <el-input v-model="form.departmentId" />
        </el-form-item>
        <el-form-item label="部门名称">
          <el-input v-model="form.departmentName" />
        </el-form-item>
        <el-form-item label="区域代码">
          <el-input v-model="form.regionCode" />
        </el-form-item>
        <el-form-item label="区域名称">
          <el-input v-model="form.regionName" />
        </el-form-item>
        <el-form-item label="角色">
          <el-input v-model="roleCodesStr" placeholder="多个用逗号分隔" />
        </el-form-item>
        <el-form-item label="数据范围">
          <el-select v-model="form.dataScope" style="width: 100%">
            <el-option label="全国" value="NATIONAL" />
            <el-option label="省级" value="PROVINCE" />
            <el-option label="市级" value="REGION" />
            <el-option label="区县" value="DISTRICT" />
            <el-option label="服务中心" value="CENTER" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" style="width: 100%" @click="handleLogin">
            模拟登录
          </el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()
const loading = ref(false)
const errorMsg = ref('')

const form = ref({
  platformUserId: 'u001',
  username: 'admin',
  realName: '管理员',
  departmentId: 'dept001',
  departmentName: '企业服务中心',
  regionCode: '371000',
  regionName: '威海市',
  dataScope: 'REGION'
})

const roleCodesStr = ref('CENTER_ADMIN')

async function handleLogin() {
  errorMsg.value = ''
  loading.value = true
  try {
    await authStore.login({
      ...form.value,
      roleCodes: roleCodesStr.value.split(',').map(s => s.trim()).filter(Boolean)
    })
    router.push('/dashboard')
  } catch (err: unknown) {
    const e = err as Error & { code?: string; response?: { status: number; data?: { message?: string } } }
    console.error('[Login] failed:', e)
    if (e.code === 'ERR_NETWORK') {
      errorMsg.value = '无法连接后端，请确认服务已启动且 Vite proxy 配置正确'
    } else {
      errorMsg.value = e.message || '登录失败，请检查控制台'
    }
  } finally {
    loading.value = false
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
