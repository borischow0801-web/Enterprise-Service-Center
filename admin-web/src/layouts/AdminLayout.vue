<template>
  <el-container class="layout-container">
    <!-- Sidebar -->
    <el-aside width="220px" class="layout-aside">
      <div class="logo">
        <span class="logo-text">企业服务中心</span>
      </div>
      <el-menu
        :default-active="activeMenu"
        router
        background-color="#001529"
        text-color="rgba(255,255,255,0.65)"
        active-text-color="#fff"
        class="side-menu"
      >
        <el-menu-item v-permission="Permission.DASHBOARD_VIEW" index="/dashboard">
          <el-icon><Odometer /></el-icon>
          <span>工作台</span>
        </el-menu-item>

        <el-menu-item v-permission="Permission.APPEAL_VIEW" index="/appeals">
          <el-icon><ChatDotRound /></el-icon>
          <span>诉求管理</span>
        </el-menu-item>

        <el-sub-menu v-if="hasPermission(Permission.MEETING_ROOM_VIEW)" index="meeting">
          <template #title>
            <el-icon><OfficeBuilding /></el-icon>
            <span>会议室管理</span>
          </template>
          <el-menu-item index="/meeting-rooms">会议室列表</el-menu-item>
          <el-menu-item index="/meeting-bookings">预约管理</el-menu-item>
        </el-sub-menu>

        <el-menu-item v-permission="Permission.GOV_MEETING_VIEW" index="/gov-meetings">
          <el-icon><UserFilled /></el-icon>
          <span>政企约见</span>
        </el-menu-item>

        <el-sub-menu v-if="hasPermission(Permission.DICT_MANAGE, Permission.OPERATION_LOG_VIEW)" index="system">
          <template #title>
            <el-icon><Setting /></el-icon>
            <span>系统管理</span>
          </template>
          <el-menu-item v-permission="Permission.DICT_MANAGE" index="/system/dictionaries">字典管理</el-menu-item>
          <el-menu-item v-permission="Permission.OPERATION_LOG_VIEW" index="/system/operation-logs">操作日志</el-menu-item>
        </el-sub-menu>
      </el-menu>
    </el-aside>

    <el-container class="layout-main">
      <!-- Header -->
      <el-header class="layout-header">
        <div class="header-left">
          <span class="breadcrumb">{{ currentTitle }}</span>
        </div>
        <div class="header-right">
          <span class="username">{{ authStore.user?.realName || authStore.user?.username }}</span>
          <el-divider direction="vertical" />
          <el-button link @click="handleLogout">退出登录</el-button>
        </div>
      </el-header>

      <!-- Content -->
      <el-main class="layout-content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { hasPermission } from '@/utils/permission'
import { Permission } from '@/constants/permission'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const activeMenu = computed(() => route.path)
const currentTitle = computed(() => String(route.meta.title || ''))

function handleLogout() {
  authStore.logout()
  router.push('/login')
}
</script>

<style scoped lang="scss">
.layout-container {
  height: 100vh;
}

.layout-aside {
  background-color: #001529;
  overflow: hidden;

  .logo {
    height: 60px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-bottom: 1px solid rgba(255,255,255,0.1);

    .logo-text {
      color: #fff;
      font-size: 16px;
      font-weight: 700;
      letter-spacing: 1px;
    }
  }

  .side-menu {
    border-right: none;
    height: calc(100vh - 60px);
    overflow-y: auto;
  }
}

.layout-header {
  height: 60px;
  background: #fff;
  border-bottom: 1px solid #e8e8e8;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;

  .header-left {
    .breadcrumb {
      font-size: 16px;
      font-weight: 500;
      color: #1a1a1a;
    }
  }

  .header-right {
    display: flex;
    align-items: center;
    gap: 8px;

    .username {
      font-size: 14px;
      color: #333;
    }
  }
}

.layout-content {
  background-color: #f0f2f5;
  padding: 24px;
  overflow-y: auto;
}
</style>
