<template>
  <div>
    <div class="page-header">
      <h2>政企约见管理</h2>
    </div>

    <!-- 查询区域 -->
    <el-card shadow="never" class="filter-card">
      <el-form :model="params" inline>
        <el-form-item label="企业名称">
          <el-input v-model="params.enterpriseName" placeholder="请输入" clearable style="width:150px" />
        </el-form-item>
        <el-form-item label="信用代码">
          <el-input v-model="params.creditCode" placeholder="请输入" clearable style="width:180px" />
        </el-form-item>
        <el-form-item label="约见状态">
          <el-select v-model="params.status" placeholder="全部" clearable style="width:140px">
            <el-option v-for="s in statusOptions" :key="s.value" :label="s.label" :value="s.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="区划">
          <el-select v-model="params.regionCode" placeholder="全部" clearable style="width:130px">
            <el-option v-for="r in regionOptions" :key="r.value" :label="r.label" :value="r.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="提交时间">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始"
            end-placeholder="结束"
            value-format="YYYY-MM-DD"
            style="width:230px"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch"><el-icon><Search /></el-icon> 查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 表格 -->
    <el-card shadow="never" class="table-card" style="margin-top:12px">
      <el-table :data="list" v-loading="loading" stripe>
        <el-table-column prop="applyNo" label="申请编号" width="150" show-overflow-tooltip />
        <el-table-column prop="enterpriseName" label="企业名称" min-width="150" show-overflow-tooltip />
        <el-table-column prop="topicName" label="约见主题" width="110" show-overflow-tooltip>
          <template #default="{ row }">{{ row.topicName || '--' }}</template>
        </el-table-column>
        <el-table-column label="期望层级" width="110" show-overflow-tooltip>
          <template #default="{ row }">{{ row.expectedLevelName || row.meetingLevel || '--' }}</template>
        </el-table-column>
        <el-table-column label="研判层级" width="110" show-overflow-tooltip>
          <template #default="{ row }">{{ row.finalLevelName || '--' }}</template>
        </el-table-column>
        <el-table-column label="状态" width="110">
          <template #default="{ row }">
            <el-tag :type="statusTagType('govMeeting', row.status)" size="small">
              {{ statusText('govMeeting', row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="regionName" label="区划" width="90" />
        <el-table-column label="提交时间" width="155">
          <template #default="{ row }">{{ formatDate(row.submittedAt) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="80" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="goDetail(row.id)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrap">
        <el-pagination
          v-model:current-page="params.pageNo"
          v-model:page-size="params.pageSize"
          :total="total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @change="fetchList"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Search } from '@element-plus/icons-vue'
import { getGovMeetingList } from '@/api/govMeeting'
import type { GovMeetingApply } from '@/api/govMeeting'
import { statusText, statusTagType, formatDate } from '@/utils/format'
import { getDictionary } from '@/api/common'

const router = useRouter()
const loading = ref(false)
const list = ref<GovMeetingApply[]>([])
const total = ref(0)
const dateRange = ref<[string, string] | null>(null)

const regionOptions = ref<{ value: string; label: string }[]>([])
const statusOptions = [
  { value: 'PENDING_AUDIT',      label: '待审核' },
  { value: 'NEED_SUPPLEMENT',    label: '退回补正' },
  { value: 'REJECTED',           label: '不予受理' },
  { value: 'ACCEPTED',           label: '受理通过' },
  { value: 'PENDING_ARRANGE',    label: '待安排' },
  { value: 'ARRANGED',           label: '已安排' },
  { value: 'WAIT_MEETING',       label: '待约见' },
  { value: 'MEETING_COMPLETED',  label: '约见完成' },
  { value: 'PENDING_EVALUATION', label: '待评价' },
  { value: 'EVALUATED',          label: '已评价' },
  { value: 'COMPLETED',          label: '已办结' },
]

const params = ref({
  enterpriseName: '',
  creditCode: '',
  status: '',
  regionCode: '',
  pageNo: 1,
  pageSize: 10,
})

onMounted(async () => {
  const regions = await getDictionary('REGION')
  if (regions.length) regionOptions.value = regions.map(d => ({ value: d.dictCode, label: d.dictLabel }))
  fetchList()
})

async function fetchList() {
  loading.value = true
  try {
    const res = await getGovMeetingList({
      enterpriseName: params.value.enterpriseName || undefined,
      creditCode: params.value.creditCode || undefined,
      status: params.value.status || undefined,
      regionCode: params.value.regionCode || undefined,
      startDate: dateRange.value?.[0] || undefined,
      endDate: dateRange.value?.[1] || undefined,
      pageNo: params.value.pageNo,
      pageSize: params.value.pageSize,
    })
    list.value = res.records
    total.value = res.total
  } finally {
    loading.value = false
  }
}

function handleSearch() { params.value.pageNo = 1; fetchList() }
function handleReset() {
  params.value = { enterpriseName: '', creditCode: '', status: '', regionCode: '', pageNo: 1, pageSize: 10 }
  dateRange.value = null
  fetchList()
}

function goDetail(id: number) { router.push(`/gov-meetings/${id}`) }
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; h2 { margin: 0; font-size: 18px; } }
.filter-card { margin-bottom: 0; }
.pagination-wrap { display: flex; justify-content: flex-end; margin-top: 16px; }
</style>
