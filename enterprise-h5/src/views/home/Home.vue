<template>
  <div class="page home-page">
    <div class="home-hero">
      <div class="home-hero__badge">企业服务</div>
      <h1 class="home-hero__title">威海市（环翠区）企业综合服务中心</h1>
      <p class="home-hero__ent">{{ user?.enterpriseName || '未获取企业信息' }}</p>
      <p class="home-hero__credit">统一社会信用代码：{{ user?.creditCode || '--' }}</p>
      <p class="home-hero__desc">
        为企业提供诉求办理、共享会议室预约、政企约见等一站式服务
      </p>
    </div>

    <div class="home-section">
      <div class="home-section__label">业务办理</div>
      <div class="feature-grid">
        <div class="feature-card" @click="router.push('/appeals')">
          <van-icon name="comment-o" size="28" color="var(--esc-primary)" />
          <span class="feature-card__name">企业诉求</span>
          <span class="feature-card__hint">提交与查询诉求</span>
        </div>
        <div class="feature-card" @click="router.push('/meeting-rooms')">
          <van-icon name="home-o" size="28" color="var(--esc-primary)" />
          <span class="feature-card__name">共享会议室</span>
          <span class="feature-card__hint">预约共享会议室</span>
        </div>
        <div class="feature-card" @click="router.push('/gov-meetings/notice')">
          <van-icon name="friends-o" size="28" color="var(--esc-primary)" />
          <span class="feature-card__name">政企约见</span>
          <span class="feature-card__hint">发起约见申请</span>
        </div>
      </div>
    </div>

    <div class="home-section">
      <div class="home-section__label">我的事项</div>
      <div class="content-block mine-links">
        <van-cell title="我的诉求" is-link icon="orders-o" @click="router.push('/appeals')" />
        <van-cell title="我的会议室预约" is-link icon="calendar-o" @click="router.push('/meeting-bookings')" />
        <van-cell title="我的政企约见" is-link icon="records" @click="router.push('/gov-meetings')" />
        <van-cell title="企业信息" is-link icon="contact" @click="router.push('/mine')" />
      </div>
    </div>

    <div class="home-footer-tip">
      <van-icon name="info-o" size="14" />
      <span>当前为企业端服务页面；正式环境将通过省级统一身份认证进入。</span>
    </div>

    <div class="home-logout">
      <van-button round block plain type="danger" size="small" @click="handleLogout">退出登录</van-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showConfirmDialog } from 'vant'
import { useAuthStore } from '@/stores/auth'
import { getToken } from '@/utils/token'

const router = useRouter()
const authStore = useAuthStore()
const user = computed(() => authStore.user)

onMounted(async () => {
  if (!getToken()) return
  try {
    await authStore.fetchEnterpriseMe()
  } catch (e) {
    console.warn('[Home] 刷新企业信息失败', e)
  }
})

async function handleLogout() {
  try {
    await showConfirmDialog({ title: '确认退出', message: '确定要退出登录吗？' })
    authStore.logout()
    router.push('/login')
  } catch {
    /* 取消 */
  }
}
</script>

<style scoped>
.home-page {
  padding-bottom: 24px;
}

.home-hero {
  background: linear-gradient(160deg, var(--esc-primary) 0%, var(--esc-primary-dark) 100%);
  padding: 28px 20px 32px;
  color: #fff;
}

.home-hero__badge {
  display: inline-block;
  font-size: 11px;
  padding: 2px 10px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.2);
  margin-bottom: 12px;
}

.home-hero__title {
  font-size: 22px;
  font-weight: 700;
  margin-bottom: 10px;
}

.home-hero__ent {
  font-size: 15px;
  font-weight: 500;
  margin-bottom: 6px;
  word-break: break-all;
}

.home-hero__credit {
  font-size: 12px;
  opacity: 0.88;
  margin-bottom: 12px;
  word-break: break-all;
}

.home-hero__desc {
  font-size: 13px;
  line-height: 1.6;
  opacity: 0.92;
}

.home-section {
  padding: 16px 12px 0;
}

.home-section__label {
  font-size: 14px;
  font-weight: 600;
  color: var(--esc-text);
  margin-bottom: 10px;
  padding-left: 4px;
}

.feature-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
}

.feature-card {
  background: var(--esc-card);
  border-radius: var(--esc-radius);
  padding: 16px 8px;
  text-align: center;
  box-shadow: var(--esc-shadow);
  border: 1px solid var(--esc-border);
}

.feature-card:active {
  opacity: 0.85;
}

.feature-card__name {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: var(--esc-text);
  margin-top: 8px;
}

.feature-card__hint {
  display: block;
  font-size: 11px;
  color: var(--esc-text-muted);
  margin-top: 4px;
}

.mine-links {
  margin: 0;
}

.home-footer-tip {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  margin: 16px 12px 0;
  padding: 12px;
  font-size: 12px;
  color: var(--esc-text-secondary);
  line-height: 1.5;
  background: var(--esc-primary-light);
  border-radius: var(--esc-radius-sm);
}

.home-logout {
  margin: 20px 16px 0;
}
</style>
