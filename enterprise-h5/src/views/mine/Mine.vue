<template>
  <div class="page">
    <van-nav-bar title="我的" left-arrow @click-left="router.push('/home')" fixed />

    <div class="page-body">
      <div class="mine-header">
        <van-icon name="shop-o" size="48" color="#fff" />
        <div class="mine-name">{{ user?.enterpriseName }}</div>
      </div>

      <van-cell-group inset style="margin-top:16px" title="企业基本信息">
        <van-cell title="企业名称" :value="user?.enterpriseName" />
        <van-cell title="统一社会信用代码" :value="user?.creditCode" />
        <van-cell title="法人姓名" :value="user?.legalPersonName || '--'" />
        <van-cell title="法人手机" :value="maskedMobile" />
      </van-cell-group>

      <van-cell-group inset style="margin-top:12px" title="我的业务">
        <van-cell title="我的诉求" is-link @click="router.push('/appeals')" />
        <van-cell title="我的会议室预约" is-link @click="router.push('/meeting-bookings')" />
        <van-cell title="我的政企约见" is-link @click="router.push('/gov-meetings')" />
      </van-cell-group>

      <div style="margin:24px 16px">
        <van-button round block plain type="danger" @click="handleLogout">退出登录</van-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { showConfirmDialog } from 'vant'
import { useAuthStore } from '@/stores/auth'
import { maskMobile } from '@/utils/format'

const router = useRouter()
const authStore = useAuthStore()
const user = computed(() => authStore.user)
const maskedMobile = computed(() => maskMobile(user.value?.legalPersonMobile))

async function handleLogout() {
  try {
    await showConfirmDialog({ title: '确认退出', message: '确定要退出登录吗？' })
    authStore.logout()
    router.push('/login')
  } catch {
    /* 用户取消 */
  }
}
</script>

<style scoped>
.mine-header {
  background: linear-gradient(160deg, var(--esc-primary) 0%, var(--esc-primary-dark) 100%);
  padding: 32px 20px 24px;
  text-align: center;
  color: #fff;
  .mine-name { font-size: 16px; font-weight: 600; margin-top: 10px; }
}
</style>
