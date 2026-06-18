<template>
  <div class="prototype-shell" :class="`prototype-shell--${activePage}`">
    <div class="sky sky--one"></div>
    <div class="sky sky--two"></div>
    <div class="wave wave--one"></div>
    <div class="wave wave--two"></div>

    <main class="phone-canvas">
      <nav class="preview-switch" aria-label="UI preview pages">
        <button
          v-for="item in previewPages"
          :key="item.key"
          class="preview-switch__item"
          :class="{ 'is-active': activePage === item.key }"
          type="button"
          @click="router.push(item.path)"
        >
          {{ item.label }}
        </button>
      </nav>

      <section v-if="activePage === 'home'" class="preview-page preview-page--home">
        <header class="home-hero home-hero--refined">
          <div class="hero-content">
            <div class="hero-meta">
              <span>威海 · 企业服务中心</span>
              <span class="hero-weather">晴 24℃</span>
            </div>
            <p class="eyebrow">上午好</p>
            <h1>测试企业有限公司</h1>
            <p class="hero-copy">为企业提供诉求办理、会议室预约、政企约见等一站式服务</p>
          </div>
          <button class="icon-bell" type="button" aria-label="消息">铃</button>
          <div class="hero-sea" aria-hidden="true">
            <span class="hero-cloud hero-cloud--one"></span>
            <span class="hero-cloud hero-cloud--two"></span>
            <span class="hero-wave hero-wave--one"></span>
            <span class="hero-wave hero-wave--two"></span>
          </div>
        </header>

        <section class="service-grid service-grid--refined" aria-label="业务办理入口">
          <article
            v-for="item in serviceCards"
            :key="item.title"
            class="service-card service-card--refined glass-card"
          >
            <div class="service-illustration" :class="`service-illustration--${item.kind}`">
              <span class="illu-main">{{ item.icon }}</span>
              <span class="illu-accent"></span>
            </div>
            <h2>{{ item.title }}</h2>
            <p>{{ item.desc }}</p>
          </article>
        </section>

        <section class="todo-summary glass-card" aria-label="我的待办统计">
          <div v-for="item in homeMetrics" :key="item.label" class="todo-summary__item">
            <strong>{{ item.value }}</strong>
            <span>{{ item.label }}</span>
          </div>
        </section>

        <footer class="home-logout">
          <button type="button">退出登录</button>
        </footer>
      </section>

      <section v-else-if="activePage === 'appeals'" class="preview-page">
        <header class="page-head">
          <span class="back-mark">‹</span>
          <div>
            <h1>企业诉求</h1>
            <p>倾听企业声音 · 快速响应诉求</p>
          </div>
        </header>

        <div class="search-card glass-card">搜索诉求编号 / 关键词</div>

        <div class="segment-row">
          <button
            v-for="tab in appealTabs"
            :key="tab"
            class="segment-pill"
            :class="{ 'is-active': tab === '办理中' }"
            type="button"
          >
            {{ tab }}
          </button>
        </div>

        <section class="summary-strip glass-card">
          <div>
            <strong>3</strong>
            <span>本月诉求</span>
          </div>
          <div>
            <strong>1.5天</strong>
            <span>平均响应</span>
          </div>
          <div>
            <strong>96%</strong>
            <span>满意度</span>
          </div>
        </section>

        <section class="appeal-list">
          <article
            v-for="item in appealCards"
            :key="item.no"
            class="appeal-card glass-card"
          >
            <div class="card-topline">
              <h2>{{ item.title }}</h2>
              <span class="status-chip" :class="item.statusClass">{{ item.status }}</span>
            </div>
            <p class="card-no">{{ item.no }} · {{ item.time }}</p>
            <p class="card-desc">{{ item.desc }}</p>
            <div class="progress-dots">
              <span class="is-done"></span>
              <span class="is-done"></span>
              <span :class="{ 'is-done': item.progress > 2 }"></span>
              <span :class="{ 'is-done': item.progress > 3 }"></span>
            </div>
            <button v-if="item.action" class="coral-link" type="button">{{ item.action }}</button>
          </article>
        </section>

        <button class="floating-action" type="button">＋ 提交诉求</button>
      </section>

      <section v-else class="preview-page">
        <header class="page-head">
          <span class="back-mark">‹</span>
          <div>
            <h1>共享会议室</h1>
            <p>海景会议空间 · 高效协作共享</p>
          </div>
          <button class="rule-link" type="button">规则</button>
        </header>

        <section class="room-feature glass-card">
          <div class="room-illus">
            <div class="room-illus__glass"></div>
            <div class="room-illus__sea"></div>
          </div>
          <div class="room-feature__body">
            <span class="status-chip success">今日可预约</span>
            <h2>威海市一号会议室</h2>
            <p>20人 · 投影仪 / 白板 / WiFi</p>
          </div>
        </section>

        <div class="filter-row">
          <button type="button">区域</button>
          <button type="button">容纳人数</button>
          <button type="button">设施</button>
          <button type="button">可预约</button>
        </div>

        <div class="date-strip glass-card">
          <span>今天</span>
          <span>明天</span>
          <span class="is-active">06/20</span>
          <span>06/21</span>
        </div>

        <section class="room-list">
          <article
            v-for="room in roomCards"
            :key="room.title"
            class="room-card glass-card"
          >
            <div class="room-thumb">
              <span></span>
            </div>
            <div class="room-card__content">
              <div class="card-topline">
                <h2>{{ room.title }}</h2>
                <span class="room-capacity">{{ room.capacity }}</span>
              </div>
              <p>{{ room.location }}</p>
              <div class="facility-row">
                <span v-for="tag in room.tags" :key="tag">{{ tag }}</span>
              </div>
              <div class="booking-row">
                <span>{{ room.next }}</span>
                <button type="button">立即预约</button>
              </div>
            </div>
          </article>
        </section>

        <section class="material-tip glass-card">
          <strong>预约材料提醒</strong>
          <p>需上传：会议室使用申请表、申请人身份证照片、会议方案</p>
        </section>
      </section>

      <footer v-if="activePage !== 'home'" class="prototype-tabbar glass-card">
        <span>首页</span>
        <span class="active">服务</span>
        <span>我的</span>
      </footer>
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

type PreviewPage = 'home' | 'appeals' | 'meeting-rooms'

const previewPages: Array<{ key: PreviewPage; label: string; path: string }> = [
  { key: 'home', label: '首页', path: '/ui-preview/home' },
  { key: 'appeals', label: '诉求', path: '/ui-preview/appeals' },
  { key: 'meeting-rooms', label: '会议室', path: '/ui-preview/meeting-rooms' },
]

const activePage = computed<PreviewPage>(() => {
  const page = route.params.page
  if (page === 'appeals' || page === 'meeting-rooms') return page
  return 'home'
})

const serviceCards = [
  { kind: 'appeal', icon: '信', title: '企业诉求', desc: '诉求提交 · 进度查询' },
  { kind: 'room', icon: '会', title: '共享会议室', desc: '会议室查看 · 预约申请' },
  { kind: 'meeting', icon: '约', title: '政企约见', desc: '约见申请 · 安排查看' },
]

const homeMetrics = [
  { label: '待处理', value: '2' },
  { label: '待评价', value: '1' },
  { label: '我的预约', value: '3' },
]

const appealTabs = ['全部', '待受理', '办理中', '待评价', '已办结']

const appealCards = [
  {
    title: '厂房租金减免申请',
    no: 'SQ20260618001',
    time: '今天 09:30',
    status: '待受理',
    statusClass: 'warning',
    desc: '已提交至环翠区企业服务中心，等待工作人员受理。',
    progress: 1,
  },
  {
    title: '政策兑现咨询',
    no: 'SQ20260612008',
    time: '06/12 14:20',
    status: '办理中',
    statusClass: 'primary',
    desc: '责任部门正在核对补贴材料，预计 1 个工作日内反馈。',
    progress: 3,
  },
  {
    title: '用工补贴材料咨询',
    no: 'SQ20260606003',
    time: '06/06 10:10',
    status: '待评价',
    statusClass: 'coral',
    desc: '事项已回复，请对本次服务进行评价。',
    progress: 4,
    action: '去评价',
  },
]

const roomCards = [
  {
    title: '一号会议室',
    capacity: '20人',
    location: '企业综合服务中心 3F',
    tags: ['投影', '白板', 'WiFi'],
    next: '06/20 09:00 可约',
  },
  {
    title: '多功能厅',
    capacity: '80人',
    location: '企业综合服务中心 2F',
    tags: ['音响', '视频会议', '饮水'],
    next: '需提前 2 天预约',
  },
]
</script>

<style scoped>
.prototype-shell {
  position: relative;
  min-height: 100vh;
  overflow-x: hidden;
  background:
    radial-gradient(circle at 18% 7%, rgba(255, 255, 255, 0.95) 0 9%, transparent 16%),
    linear-gradient(180deg, #bfeeff 0%, #ecfaff 42%, #f7fbff 100%);
  color: #123047;
}

.prototype-shell::before {
  position: fixed;
  inset: 0;
  pointer-events: none;
  content: '';
  background:
    linear-gradient(120deg, rgba(255, 255, 255, 0.42), transparent 38%),
    radial-gradient(circle at 76% 18%, rgba(40, 182, 246, 0.22), transparent 24%);
}

.sky,
.wave {
  position: fixed;
  pointer-events: none;
}

.sky {
  width: clamp(130px, 42vw, 220px);
  height: clamp(46px, 13vw, 72px);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.58);
  filter: blur(1px);
  animation: cloudDrift 14s ease-in-out infinite;
}

.sky--one { top: 7%; left: -28px; }
.sky--two { top: 17%; right: -62px; animation-delay: -5s; }

.wave {
  left: -8%;
  right: -8%;
  height: 120px;
  border-radius: 50%;
  border-top: 1px solid rgba(22, 119, 255, 0.16);
}

.wave--one { top: 42%; }
.wave--two { top: 52%; border-color: rgba(40, 182, 246, 0.13); }

.phone-canvas {
  position: relative;
  width: min(100%, 480px);
  min-height: 100vh;
  margin: 0 auto;
  padding: calc(12px + env(safe-area-inset-top)) clamp(14px, 4vw, 20px) calc(90px + env(safe-area-inset-bottom));
}

.preview-switch {
  position: sticky;
  top: max(10px, env(safe-area-inset-top));
  z-index: 20;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 6px;
  padding: 6px;
  margin-bottom: 14px;
  border: 1px solid rgba(255, 255, 255, 0.64);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.62);
  box-shadow: 0 10px 28px rgba(50, 133, 198, 0.13);
  backdrop-filter: blur(18px);
}

.preview-switch__item {
  min-height: 34px;
  border: 0;
  border-radius: 999px;
  background: transparent;
  color: #5f7488;
  font-size: 13px;
  font-weight: 600;
}

.preview-switch__item.is-active {
  color: #fff;
  background: linear-gradient(135deg, #1677ff, #28b6f6);
  box-shadow: 0 8px 16px rgba(22, 119, 255, 0.24);
}

.preview-page { position: relative; z-index: 1; }


.glass-card {
  border: 1px solid rgba(255, 255, 255, 0.66);
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.84), rgba(255, 255, 255, 0.58));
  box-shadow: 0 18px 40px rgba(54, 133, 190, 0.14);
  backdrop-filter: blur(22px);
}

.home-hero {
  position: relative;
  min-height: 190px;
  padding: clamp(20px, 6vw, 28px);
  overflow: hidden;
  border-radius: 30px;
}

.hero-meta,
.hero-title-row,
.card-topline,
.booking-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.hero-meta { color: #5f7488; font-size: 12px; }

.hero-weather,
.rule-link {
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(22, 119, 255, 0.1);
  color: #1677ff;
}

.hero-title-row { position: relative; z-index: 1; margin-top: 24px; }

.eyebrow {
  margin-bottom: 6px;
  color: #28a2df;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
}

h1,
h2,
p { margin: 0; }

h1 { font-size: clamp(24px, 7vw, 30px); line-height: 1.18; }
h2 { font-size: 16px; line-height: 1.35; }

.hero-copy {
  position: relative;
  z-index: 1;
  margin-top: 14px;
  color: #5f7488;
  font-size: 14px;
}

.icon-bell {
  width: 44px;
  height: 44px;
  border: 0;
  border-radius: 16px;
  background: #fff;
  color: #1677ff;
  box-shadow: 0 10px 20px rgba(22, 119, 255, 0.14);
}

.hero-cloud {
  position: absolute;
  right: -12px;
  bottom: -8px;
  width: 150px;
  height: 88px;
  opacity: 0.78;
}

.cloud-dot {
  position: absolute;
  display: block;
  border-radius: 999px;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.9), rgba(40, 182, 246, 0.2));
}

.cloud-dot--one { right: 26px; bottom: 16px; width: 116px; height: 38px; }
.cloud-dot--two { right: 60px; bottom: 35px; width: 56px; height: 56px; }
.cloud-dot--three { right: 16px; bottom: 32px; width: 44px; height: 44px; }

.service-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
  margin-top: 14px;
}

.service-card { min-height: 132px; padding: 14px 10px; border-radius: 22px; }

.service-card__icon {
  display: grid;
  width: 46px;
  height: 46px;
  margin-bottom: 10px;
  place-items: center;
  border-radius: 18px;
  background: linear-gradient(135deg, #eaf7ff, #ffffff);
  color: #1677ff;
  font-weight: 800;
}

.service-card p,
.metric-card p,
.journey-card p,
.page-head p,
.room-feature p,
.room-card p,
.material-tip p,
.card-desc,
.card-no {
  color: #5f7488;
  font-size: 12px;
  line-height: 1.55;
}

.service-card h2 { margin-bottom: 6px; font-size: 15px; }

.bento-grid {
  display: grid;
  grid-template-columns: 1.2fr 0.8fr;
  gap: 10px;
  margin-top: 14px;
}

.metric-card { min-height: 92px; padding: 14px; border-radius: 22px; }
.metric-card--wide { grid-row: span 2; }
.metric-card span { color: #5f7488; font-size: 12px; }
.metric-card strong { display: block; margin-top: 8px; color: #1677ff; font-size: 30px; }

.journey-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 14px;
  padding: 18px;
  border-radius: 24px;
}

.primary-pill,
.floating-action,
.booking-row button {
  border: 0;
  border-radius: 999px;
  color: #fff;
  background: linear-gradient(135deg, #1677ff, #28b6f6);
  box-shadow: 0 12px 24px rgba(22, 119, 255, 0.24);
}

.primary-pill {
  flex: 0 0 auto;
  min-height: 40px;
  padding: 0 16px;
  font-size: 13px;
  font-weight: 700;
}

.page-head {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 6px 0 12px;
}

.page-head h1 { font-size: 25px; }

.back-mark {
  display: grid;
  width: 36px;
  height: 36px;
  place-items: center;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.7);
  color: #1677ff;
  font-size: 28px;
}

.rule-link { margin-left: auto; border: 0; font-weight: 700; }

.search-card {
  padding: 13px 16px;
  border-radius: 999px;
  color: #8aa0b2;
  font-size: 14px;
}

.segment-row,
.filter-row {
  display: flex;
  gap: 8px;
  padding: 12px 0 4px;
  overflow-x: auto;
  scrollbar-width: none;
}

.segment-row::-webkit-scrollbar,
.filter-row::-webkit-scrollbar { display: none; }

.segment-pill,
.filter-row button {
  flex: 0 0 auto;
  min-height: 34px;
  padding: 0 13px;
  border: 1px solid rgba(255, 255, 255, 0.7);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.65);
  color: #5f7488;
  font-weight: 600;
}

.segment-pill.is-active { color: #fff; background: linear-gradient(135deg, #1677ff, #28b6f6); }

.summary-strip {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  margin-top: 10px;
  padding: 16px 10px;
  border-radius: 24px;
  text-align: center;
}

.summary-strip strong { display: block; color: #1677ff; font-size: 19px; }
.summary-strip span { color: #5f7488; font-size: 12px; }

.appeal-list,
.room-list { display: grid; gap: 12px; margin-top: 12px; }

.appeal-card,
.room-card,
.material-tip { position: relative; border-radius: 24px; padding: 16px; }

.card-topline h2 { min-width: 0; }

.status-chip {
  flex: 0 0 auto;
  padding: 5px 9px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
  color: #1677ff;
  background: rgba(22, 119, 255, 0.1);
}

.status-chip.warning { color: #b97700; background: rgba(245, 166, 35, 0.16); }
.status-chip.primary { color: #1677ff; background: rgba(22, 119, 255, 0.12); }
.status-chip.coral { color: #d75d43; background: rgba(255, 138, 106, 0.16); }
.status-chip.success { color: #16875e; background: rgba(37, 185, 127, 0.16); }

.card-no { margin-top: 8px; }
.card-desc { margin-top: 6px; }

.progress-dots {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 6px;
  margin-top: 13px;
}

.progress-dots span { height: 4px; border-radius: 999px; background: rgba(22, 119, 255, 0.12); }
.progress-dots .is-done { background: linear-gradient(90deg, #1677ff, #28b6f6); }

.coral-link {
  position: absolute;
  right: 16px;
  bottom: 14px;
  border: 0;
  background: transparent;
  color: #ff795b;
  font-weight: 800;
}

.floating-action {
  position: fixed;
  right: max(18px, calc((100vw - 480px) / 2 + 18px));
  bottom: calc(82px + env(safe-area-inset-bottom));
  z-index: 25;
  min-height: 46px;
  padding: 0 18px;
  font-weight: 800;
  animation: pulseRing 2.4s ease-in-out infinite;
}

.room-feature { overflow: hidden; border-radius: 28px; }

.room-illus {
  position: relative;
  height: clamp(130px, 42vw, 190px);
  overflow: hidden;
  background: linear-gradient(180deg, #91dcff, #eefbff);
}

.room-illus__glass {
  position: absolute;
  left: 14%;
  right: 14%;
  bottom: 30px;
  height: 62px;
  border: 2px solid rgba(255, 255, 255, 0.9);
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.34);
  box-shadow: inset 0 0 24px rgba(255, 255, 255, 0.5);
}

.room-illus__sea {
  position: absolute;
  left: -10%;
  right: -10%;
  bottom: -18px;
  height: 64px;
  border-radius: 50% 50% 0 0;
  background: linear-gradient(90deg, rgba(22, 119, 255, 0.32), rgba(40, 182, 246, 0.4));
}

.room-feature__body { padding: 16px; }
.room-feature__body h2 { margin: 10px 0 4px; font-size: 18px; }

.date-strip {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
  margin-top: 10px;
  padding: 8px;
  border-radius: 999px;
  text-align: center;
}

.date-strip span {
  padding: 9px 0;
  border-radius: 999px;
  color: #5f7488;
  font-size: 12px;
  font-weight: 700;
}

.date-strip .is-active { color: #fff; background: linear-gradient(135deg, #1677ff, #28b6f6); }

.room-card {
  display: grid;
  grid-template-columns: 88px minmax(0, 1fr);
  gap: 12px;
}

.room-thumb {
  position: relative;
  min-height: 112px;
  overflow: hidden;
  border-radius: 20px;
  background: linear-gradient(160deg, #88d9ff, #ffffff 58%, #8fdff1);
}

.room-thumb span {
  position: absolute;
  left: 14px;
  right: 14px;
  bottom: 26px;
  height: 38px;
  border-radius: 12px;
  border: 2px solid rgba(255, 255, 255, 0.88);
  background: rgba(255, 255, 255, 0.32);
}

.room-capacity { color: #1677ff; font-weight: 800; }

.facility-row {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 8px;
}

.facility-row span {
  padding: 4px 7px;
  border-radius: 999px;
  background: rgba(22, 119, 255, 0.1);
  color: #1677ff;
  font-size: 11px;
}

.booking-row { margin-top: 10px; }
.booking-row span { color: #25a878; font-size: 12px; font-weight: 700; }

.booking-row button {
  min-height: 32px;
  padding: 0 12px;
  font-size: 12px;
  font-weight: 800;
}

.material-tip { margin-top: 12px; }
.material-tip strong { display: block; margin-bottom: 5px; }

.prototype-tabbar {
  position: fixed;
  right: max(14px, calc((100vw - 480px) / 2 + 14px));
  bottom: calc(12px + env(safe-area-inset-bottom));
  left: max(14px, calc((100vw - 480px) / 2 + 14px));
  z-index: 18;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  padding: 12px 8px;
  border-radius: 24px;
  text-align: center;
  color: #7890a3;
  font-size: 12px;
  font-weight: 700;
}

.prototype-tabbar .active { color: #1677ff; }


/* Refined Home prototype based on the agreed information architecture. */
.preview-page--home {
  display: grid;
  gap: 14px;
}

.home-hero--refined {
  position: relative;
  min-height: clamp(176px, 50vw, 208px);
  padding: clamp(18px, 5vw, 24px);
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.72);
  background:
    radial-gradient(circle at 82% 18%, rgba(255, 255, 255, 0.92) 0 9%, transparent 18%),
    linear-gradient(145deg, rgba(42, 178, 246, 0.92), rgba(22, 119, 255, 0.82) 52%, rgba(116, 217, 255, 0.7));
  box-shadow: 0 22px 46px rgba(36, 128, 204, 0.22);
}

.home-hero--refined::before {
  position: absolute;
  inset: 0;
  content: '';
  background:
    linear-gradient(115deg, rgba(255, 255, 255, 0.24), transparent 42%),
    radial-gradient(circle at 12% 24%, rgba(255, 255, 255, 0.24), transparent 24%);
}

.hero-content {
  position: relative;
  z-index: 2;
  max-width: 78%;
  color: #fff;
}

.home-hero--refined .hero-meta {
  margin-bottom: 18px;
  color: rgba(255, 255, 255, 0.9);
}

.home-hero--refined .hero-weather {
  color: #0f6bff;
  background: rgba(255, 255, 255, 0.78);
}

.home-hero--refined .eyebrow {
  color: rgba(255, 255, 255, 0.86);
}

.home-hero--refined h1 {
  max-width: 300px;
  color: #fff;
  font-size: clamp(24px, 6.8vw, 31px);
  letter-spacing: -0.03em;
  text-shadow: 0 10px 24px rgba(17, 85, 156, 0.22);
}

.home-hero--refined .hero-copy {
  max-width: 280px;
  margin-top: 10px;
  color: rgba(255, 255, 255, 0.9);
  font-size: 13px;
}

.home-hero--refined .icon-bell {
  position: absolute;
  top: 20px;
  right: 18px;
  z-index: 3;
  background: rgba(255, 255, 255, 0.88);
}

.hero-sea {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.hero-cloud,
.hero-wave {
  position: absolute;
  display: block;
}

.hero-cloud {
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.58);
  animation: cloudDrift 12s ease-in-out infinite;
}

.hero-cloud--one {
  right: 28px;
  bottom: 68px;
  width: 96px;
  height: 32px;
}

.hero-cloud--two {
  right: 82px;
  bottom: 88px;
  width: 48px;
  height: 48px;
  animation-delay: -4s;
}

.hero-wave {
  left: -8%;
  right: -8%;
  height: 80px;
  border-radius: 50% 50% 0 0;
  border-top: 1px solid rgba(255, 255, 255, 0.52);
}

.hero-wave--one {
  bottom: -34px;
  background: linear-gradient(90deg, rgba(255, 255, 255, 0.18), rgba(255, 255, 255, 0.05));
}

.hero-wave--two {
  bottom: -50px;
  opacity: 0.72;
}

.service-grid--refined {
  gap: 9px;
  margin-top: 0;
}

.service-card--refined {
  min-height: 136px;
  padding: 13px 9px 12px;
  border-radius: 22px;
  text-align: center;
  transition: transform 0.18s ease, box-shadow 0.18s ease;
}

.service-card--refined:active {
  transform: scale(0.97);
}

.service-card--refined h2 {
  margin-top: 9px;
  margin-bottom: 4px;
  font-size: clamp(13px, 3.8vw, 15px);
}

.service-card--refined p {
  min-height: 32px;
  font-size: 11px;
}

.service-illustration {
  position: relative;
  display: grid;
  width: clamp(48px, 14vw, 58px);
  height: clamp(48px, 14vw, 58px);
  margin: 0 auto;
  place-items: center;
  border-radius: 22px;
  overflow: hidden;
  background: linear-gradient(145deg, #e8f6ff, #ffffff);
  box-shadow: inset 0 0 18px rgba(255, 255, 255, 0.8), 0 10px 20px rgba(22, 119, 255, 0.12);
}

.illu-main {
  position: relative;
  z-index: 2;
  display: grid;
  width: 34px;
  height: 34px;
  place-items: center;
  border-radius: 15px;
  color: #fff;
  background: linear-gradient(135deg, #1677ff, #28b6f6);
  font-size: 15px;
  font-weight: 800;
}

.illu-accent {
  position: absolute;
  right: 6px;
  bottom: 8px;
  width: 22px;
  height: 8px;
  border-radius: 999px;
  border-top: 2px solid rgba(255, 138, 106, 0.76);
  transform: rotate(-12deg);
}

.service-illustration--room .illu-main {
  background: linear-gradient(135deg, #19a9e6, #67d9ff);
}

.service-illustration--meeting .illu-main {
  background: linear-gradient(135deg, #0f6bff, #6b8cff);
}

.service-illustration--meeting .illu-accent {
  border-color: rgba(255, 207, 98, 0.82);
}

.todo-summary {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  padding: 14px 10px;
  border-radius: 24px;
}

.todo-summary__item {
  position: relative;
  display: grid;
  gap: 4px;
  text-align: center;
}

.todo-summary__item + .todo-summary__item::before {
  position: absolute;
  top: 8px;
  bottom: 8px;
  left: 0;
  width: 1px;
  content: '';
  background: rgba(22, 119, 255, 0.12);
}

.todo-summary__item strong {
  color: #1677ff;
  font-size: clamp(23px, 7vw, 30px);
  line-height: 1;
}

.todo-summary__item span {
  color: #5f7488;
  font-size: 12px;
  font-weight: 700;
}

.home-logout {
  padding: 2px 0 0;
}

.home-logout button {
  width: 100%;
  min-height: 46px;
  border: 1px solid rgba(22, 119, 255, 0.16);
  border-radius: 999px;
  color: #1677ff;
  background: rgba(255, 255, 255, 0.78);
  box-shadow: 0 14px 28px rgba(54, 133, 190, 0.13);
  backdrop-filter: blur(18px);
  font-size: 15px;
  font-weight: 800;
}

@keyframes cloudDrift {
  0%, 100% { transform: translateX(0); }
  50% { transform: translateX(18px); }
}

@keyframes pulseRing {
  0%, 100% { box-shadow: 0 12px 24px rgba(22, 119, 255, 0.24), 0 0 0 0 rgba(22, 119, 255, 0.22); }
  50% { box-shadow: 0 12px 24px rgba(22, 119, 255, 0.24), 0 0 0 10px rgba(22, 119, 255, 0); }
}

@media (max-width: 374px) {
  .service-grid { grid-template-columns: 1fr; }

  .service-card {
    display: grid;
    grid-template-columns: auto 1fr;
    column-gap: 12px;
    min-height: auto;
    text-align: left;
  }

  .service-card__icon { grid-row: span 2; margin-bottom: 0; }

  .room-card { grid-template-columns: 1fr; }
  .room-thumb { min-height: 132px; }

  .journey-card {
    align-items: flex-start;
    flex-direction: column;
  }
}

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.001ms !important;
    animation-iteration-count: 1 !important;
    scroll-behavior: auto !important;
  }
}
</style>
