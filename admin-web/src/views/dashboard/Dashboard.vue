<template>
  <div>
    <div class="page-header">
      <h2>工作台</h2>
    </div>

    <el-alert v-if="loadError" type="warning" :title="loadError" show-icon :closable="false" style="margin-bottom:12px" />

    <el-row :gutter="16" class="stats-row" v-loading="loading">
      <el-col :span="6" v-for="card in statCards" :key="card.key">
        <el-card class="stat-card" shadow="never">
          <div class="stat-content">
            <div class="stat-icon" :style="{ background: card.color }">
              <el-icon size="24"><component :is="card.icon" /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ summary[card.key] ?? 0 }}</div>
              <div class="stat-label">{{ card.label }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" style="margin-top:16px">
      <el-col :span="12">
        <el-card shadow="never">
          <template #header><span>企业诉求</span></template>
          <el-descriptions :column="2" border size="small">
            <el-descriptions-item label="总数">{{ summary.appealTotal }}</el-descriptions-item>
            <el-descriptions-item label="待受理">{{ summary.appealPending }}</el-descriptions-item>
            <el-descriptions-item label="办理中">{{ summary.appealProcessing }}</el-descriptions-item>
            <el-descriptions-item label="已完成">{{ summary.appealCompleted }}</el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="never">
          <template #header><span>会议室预约</span></template>
          <el-descriptions :column="2" border size="small">
            <el-descriptions-item label="会议室数">{{ summary.meetingRoomTotal }}</el-descriptions-item>
            <el-descriptions-item label="预约总数">{{ summary.meetingBookingTotal }}</el-descriptions-item>
            <el-descriptions-item label="待审核">{{ summary.meetingBookingPending }}</el-descriptions-item>
            <el-descriptions-item label="已通过">{{ summary.meetingBookingApproved }}</el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" style="margin-top:16px">
      <el-col :span="12">
        <el-card shadow="never">
          <template #header><span>政企约见</span></template>
          <el-descriptions :column="2" border size="small">
            <el-descriptions-item label="总数">{{ summary.govMeetingTotal }}</el-descriptions-item>
            <el-descriptions-item label="待审核">{{ summary.govMeetingPending }}</el-descriptions-item>
            <el-descriptions-item label="已安排/待约见">{{ summary.govMeetingArranged }}</el-descriptions-item>
            <el-descriptions-item label="待评价">{{ summary.govMeetingPendingEvaluation }}</el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="never">
          <template #header><span>满意度</span></template>
          <el-descriptions :column="2" border size="small">
            <el-descriptions-item label="评价总数">{{ summary.evaluationTotal }}</el-descriptions-item>
            <el-descriptions-item label="满意">{{ summary.satisfiedCount }}</el-descriptions-item>
            <el-descriptions-item label="不满意">{{ summary.unsatisfiedCount }}</el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { getDashboardSummary, type DashboardSummary } from '@/api/dashboard'

const loading = ref(false)
const loadError = ref('')

const summary = reactive<DashboardSummary>({
  appealTotal: 0,
  appealPending: 0,
  appealProcessing: 0,
  appealCompleted: 0,
  meetingRoomTotal: 0,
  meetingBookingTotal: 0,
  meetingBookingPending: 0,
  meetingBookingApproved: 0,
  govMeetingTotal: 0,
  govMeetingPending: 0,
  govMeetingArranged: 0,
  govMeetingPendingEvaluation: 0,
  evaluationTotal: 0,
  satisfiedCount: 0,
  unsatisfiedCount: 0,
})

const statCards = [
  { key: 'appealPending' as const, label: '待受理诉求', icon: 'ChatDotRound', color: '#1677ff' },
  { key: 'meetingBookingPending' as const, label: '待审核预约', icon: 'OfficeBuilding', color: '#52c41a' },
  { key: 'govMeetingPending' as const, label: '待审核约见', icon: 'UserFilled', color: '#fa8c16' },
  { key: 'appealCompleted' as const, label: '已完成诉求', icon: 'CircleCheck', color: '#722ed1' },
]

async function loadSummary() {
  loading.value = true
  loadError.value = ''
  try {
    const data = await getDashboardSummary()
    Object.assign(summary, data)
  } catch {
    loadError.value = '统计数据加载失败，已显示为 0'
  } finally {
    loading.value = false
  }
}

onMounted(loadSummary)
</script>

<style scoped lang="scss">
.stats-row {
  .stat-card {
    :deep(.el-card__body) {
      padding: 20px;
    }
    .stat-content {
      display: flex;
      align-items: center;
      gap: 16px;
    }
    .stat-icon {
      width: 52px;
      height: 52px;
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      color: #fff;
    }
    .stat-value {
      font-size: 28px;
      font-weight: 700;
      color: #1a1a1a;
      line-height: 1;
    }
    .stat-label {
      font-size: 13px;
      color: #888;
      margin-top: 6px;
    }
  }
}
</style>
