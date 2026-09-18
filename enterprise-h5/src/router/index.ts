import { createRouter, createWebHistory } from 'vue-router'
import { getToken } from '@/utils/token'
import { buildLoginRedirect, resolveRedirectPath } from '@/utils/redirect'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('@/views/login/Login.vue'),
      meta: { requiresAuth: false },
    },
    {
      path: '/register',
      name: 'Register',
      component: () => import('@/views/login/Register.vue'),
      meta: { requiresAuth: false },
    },
    // 开发调试登录页：仅在开发构建中注册该路由，生产构建会被 Vite 静态裁剪掉，
    // 对应的后端 mock-login 接口在 APP_ENV=production 下也会直接返回 40401。
    ...(import.meta.env.DEV
      ? [
          {
            path: '/dev-login',
            name: 'DevMockLogin',
            component: () => import('@/views/login/DevMockLogin.vue'),
            meta: { requiresAuth: false },
          },
        ]
      : []),
    { path: '/', redirect: '/home' },
    {
      path: '/home',
      name: 'Home',
      component: () => import('@/views/home/Home.vue'),
      meta: { requiresAuth: true, title: '企业服务中心' },
    },
    {
      path: '/appeals',
      name: 'AppealList',
      component: () => import('@/views/appeal/AppealList.vue'),
      meta: { requiresAuth: true, title: '企业诉求' },
    },
    {
      path: '/appeals/create',
      name: 'AppealCreate',
      component: () => import('@/views/appeal/AppealCreate.vue'),
      meta: { requiresAuth: true, title: '提交诉求' },
    },
    {
      path: '/appeals/:id',
      name: 'AppealDetail',
      component: () => import('@/views/appeal/AppealDetail.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/appeals/:id/evaluate',
      name: 'AppealEvaluate',
      component: () => import('@/views/appeal/AppealEvaluate.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/mine',
      name: 'Mine',
      component: () => import('@/views/mine/Mine.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/meeting-rooms',
      name: 'MeetingRoomList',
      component: () => import('@/views/meeting-room/MeetingRoomList.vue'),
      meta: { requiresAuth: true, title: '共享会议室' },
    },
    {
      path: '/meeting-rooms/rules',
      name: 'MeetingRoomRules',
      component: () => import('@/views/meeting-room/MeetingRoomRules.vue'),
      meta: { requiresAuth: true, title: '共享会议室预约使用管理制度' },
    },
    {
      path: '/meeting-rooms/:id',
      name: 'MeetingRoomDetail',
      component: () => import('@/views/meeting-room/MeetingRoomDetail.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/meeting-rooms/:id/book',
      name: 'MeetingRoomBook',
      component: () => import('@/views/meeting-room/MeetingRoomBook.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/meeting-bookings',
      name: 'MeetingBookingList',
      component: () => import('@/views/meeting-room/MeetingBookingList.vue'),
      meta: { requiresAuth: true, title: '我的预约' },
    },
    {
      path: '/meeting-bookings/:id',
      name: 'MeetingBookingDetail',
      component: () => import('@/views/meeting-room/MeetingBookingDetail.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/gov-meetings/notice',
      name: 'GovMeetingNotice',
      component: () => import('@/views/gov-meeting/GovMeetingNotice.vue'),
      meta: { requiresAuth: true, title: '政企约见' },
    },
    {
      path: '/gov-meetings/create',
      name: 'GovMeetingCreate',
      component: () => import('@/views/gov-meeting/GovMeetingCreate.vue'),
      meta: { requiresAuth: true, title: '发起约见' },
    },
    {
      path: '/gov-meetings',
      name: 'GovMeetingList',
      component: () => import('@/views/gov-meeting/GovMeetingList.vue'),
      meta: { requiresAuth: true, title: '我的约见' },
    },
    {
      path: '/gov-meetings/:id/evaluate',
      name: 'GovMeetingEvaluate',
      component: () => import('@/views/gov-meeting/GovMeetingEvaluate.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/gov-meetings/:id',
      name: 'GovMeetingDetail',
      component: () => import('@/views/gov-meeting/GovMeetingDetail.vue'),
      meta: { requiresAuth: true },
    },
  ],
})

/**
 * 路由守卫（微信公众号菜单直链场景）：
 * 1. 未登录访问需鉴权页 → /login?redirect=<原始 fullPath>
 * 2. 已登录访问 /login → 跳 redirect 或 /home
 *
 * 正式环境省级统一身份认证：
 * - 菜单访问 /appeals 等 → 记录 redirect → 跳转省认证
 * - 回调 /auth/callback 换 token → resolveRedirectPath(redirect) 回到菜单页
 * - 不应强制回到 /home
 */
router.beforeEach((to) => {
  const token = getToken()
  const redirectQuery = typeof to.query.redirect === 'string' ? to.query.redirect : undefined

  if (to.path === '/login' || to.path === '/register' || to.path === '/dev-login') {
    if (token) return resolveRedirectPath(redirectQuery)
    return true
  }

  if (to.meta.requiresAuth && !token) {
    return buildLoginRedirect(to.fullPath)
  }

  return true
})

export default router
