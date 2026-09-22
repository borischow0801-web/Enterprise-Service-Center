import { createRouter, createWebHistory } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getToken } from '@/utils/token'
import { hasPermission } from '@/utils/permission'
import { Permission } from '@/constants/permission'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
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
          meta: { title: '工作台', permission: Permission.DASHBOARD_VIEW }
        },
        {
          path: 'appeals',
          name: 'AppealList',
          component: () => import('@/views/appeal/AppealList.vue'),
          meta: { title: '诉求管理', permission: Permission.APPEAL_VIEW }
        },
        {
          path: 'appeals/:id',
          name: 'AppealDetail',
          component: () => import('@/views/appeal/AppealDetail.vue'),
          meta: { title: '诉求详情', permission: Permission.APPEAL_VIEW }
        },
        {
          path: 'meeting-rooms',
          name: 'RoomList',
          component: () => import('@/views/meeting-room/RoomList.vue'),
          meta: { title: '会议室管理', permission: Permission.MEETING_ROOM_VIEW }
        },
        {
          path: 'meeting-bookings',
          name: 'BookingList',
          component: () => import('@/views/meeting-room/BookingList.vue'),
          meta: { title: '预约管理', permission: Permission.MEETING_ROOM_VIEW }
        },
        {
          path: 'meeting-bookings/:id',
          name: 'BookingDetail',
          component: () => import('@/views/meeting-room/BookingDetail.vue'),
          meta: { title: '预约详情', permission: Permission.MEETING_ROOM_VIEW }
        },
        {
          path: 'gov-meetings',
          name: 'GovMeetingList',
          component: () => import('@/views/gov-meeting/GovMeetingList.vue'),
          meta: { title: '政企约见', permission: Permission.GOV_MEETING_VIEW }
        },
        {
          path: 'gov-meetings/:id',
          name: 'GovMeetingDetail',
          component: () => import('@/views/gov-meeting/GovMeetingDetail.vue'),
          meta: { title: '约见详情', permission: Permission.GOV_MEETING_VIEW }
        },
        {
          path: 'system/dictionaries',
          name: 'DictionaryList',
          component: () => import('@/views/system/DictionaryList.vue'),
          meta: { title: '字典管理', permission: Permission.DICT_MANAGE }
        },
        {
          path: 'system/operation-logs',
          name: 'OperationLog',
          component: () => import('@/views/system/OperationLog.vue'),
          meta: { title: '操作日志', permission: Permission.OPERATION_LOG_VIEW }
        },
        {
          path: 'system/admin-users',
          name: 'AdminUserList',
          component: () => import('@/views/system/AdminUserList.vue'),
          meta: { title: '管理员管理', permission: Permission.ADMIN_USER_MANAGE }
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
  const required = to.meta.permission as string | string[] | undefined
  if (required && token) {
    const codes = Array.isArray(required) ? required : [required]
    if (!hasPermission(...(codes as (typeof Permission)[keyof typeof Permission][]))) {
      ElMessage.warning('当前角色无权访问该页面')
      return to.path === '/dashboard' ? false : '/dashboard'
    }
  }
})

export default router
