import { createRouter, createWebHistory } from 'vue-router'
import { getToken } from '@/utils/token'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('@/views/login/Login.vue'),
      meta: { public: true }
    },
    {
      path: '/',
      component: () => import('@/layouts/AdminLayout.vue'),
      redirect: '/dashboard',
      children: [
        {
          path: 'dashboard',
          name: 'Dashboard',
          component: () => import('@/views/dashboard/Dashboard.vue'),
          meta: { title: '工作台' }
        },
        {
          path: 'appeals',
          name: 'AppealList',
          component: () => import('@/views/appeal/AppealList.vue'),
          meta: { title: '诉求管理' }
        },
        {
          path: 'appeals/:id',
          name: 'AppealDetail',
          component: () => import('@/views/appeal/AppealDetail.vue'),
          meta: { title: '诉求详情' }
        },
        {
          path: 'meeting-rooms',
          name: 'RoomList',
          component: () => import('@/views/meeting-room/RoomList.vue'),
          meta: { title: '会议室管理' }
        },
        {
          path: 'meeting-bookings',
          name: 'BookingList',
          component: () => import('@/views/meeting-room/BookingList.vue'),
          meta: { title: '预约管理' }
        },
        {
          path: 'meeting-bookings/:id',
          name: 'BookingDetail',
          component: () => import('@/views/meeting-room/BookingDetail.vue'),
          meta: { title: '预约详情' }
        },
        {
          path: 'gov-meetings',
          name: 'GovMeetingList',
          component: () => import('@/views/gov-meeting/GovMeetingList.vue'),
          meta: { title: '政企约见' }
        },
        {
          path: 'gov-meetings/:id',
          name: 'GovMeetingDetail',
          component: () => import('@/views/gov-meeting/GovMeetingDetail.vue'),
          meta: { title: '约见详情' }
        },
        {
          path: 'system/dictionaries',
          name: 'DictionaryList',
          component: () => import('@/views/system/DictionaryList.vue'),
          meta: { title: '字典管理' }
        },
        {
          path: 'system/operation-logs',
          name: 'OperationLog',
          component: () => import('@/views/system/OperationLog.vue'),
          meta: { title: '操作日志' }
        }
      ]
    },
    {
      path: '/404',
      name: 'NotFound',
      component: () => import('@/views/error/NotFound.vue'),
      meta: { public: true }
    },
    {
      path: '/:pathMatch(.*)*',
      redirect: '/404'
    }
  ]
})

router.beforeEach((to) => {
  const token = getToken()
  if (!to.meta.public && !token) {
    return '/login'
  }
  if (to.path === '/login' && token) {
    return '/dashboard'
  }
})

export default router
