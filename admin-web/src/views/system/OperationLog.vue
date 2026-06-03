<template>
  <div>
    <div class="page-header">
      <h2>操作日志</h2>
    </div>

    <el-card shadow="never" class="filter-card">
      <el-form :model="params" inline>
        <el-form-item label="操作人类型">
          <el-select v-model="params.operatorType" placeholder="全部" clearable style="width:120px">
            <el-option label="用户" value="USER" />
            <el-option label="企业" value="ENTERPRISE" />
          </el-select>
        </el-form-item>
        <el-form-item label="操作人名称">
          <el-input v-model="params.operatorName" clearable style="width:140px" />
        </el-form-item>
        <el-form-item label="业务类型">
          <el-input v-model="params.businessType" clearable style="width:120px" placeholder="如 APPEAL" />
        </el-form-item>
        <el-form-item label="操作类型">
          <el-input v-model="params.operationType" clearable style="width:140px" />
        </el-form-item>
        <el-form-item label="操作时间">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            value-format="YYYY-MM-DD"
            range-separator="至"
            start-placeholder="开始"
            end-placeholder="结束"
            style="width:240px"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card shadow="never" class="table-card" style="margin-top:12px">
      <el-table :data="list" v-loading="loading" stripe>
        <el-table-column prop="operatorType" label="操作人类型" width="100" />
        <el-table-column prop="operatorName" label="操作人名称" width="120" />
        <el-table-column prop="businessType" label="业务类型" width="100" />
        <el-table-column prop="businessId" label="业务ID" width="90" />
        <el-table-column prop="operationType" label="操作类型" width="140" show-overflow-tooltip />
        <el-table-column label="操作内容" min-width="200">
          <template #default="{ row }">
            <span class="content-ellipsis">{{ row.operationContent || '--' }}</span>
            <el-button
              v-if="row.operationContent && row.operationContent.length > 40"
              link type="primary"
              size="small"
              @click="showContent(row.operationContent!)"
            >详情</el-button>
          </template>
        </el-table-column>
        <el-table-column prop="beforeStatus" label="操作前状态" width="110" />
        <el-table-column prop="afterStatus" label="操作后状态" width="110" />
        <el-table-column prop="ipAddress" label="IP" width="120" />
        <el-table-column prop="createdAt" label="操作时间" width="165">
          <template #default="{ row }">{{ formatDate(row.createdAt) }}</template>
        </el-table-column>
      </el-table>
      <div class="pagination-wrap">
        <el-pagination
          v-model:current-page="params.pageNo"
          v-model:page-size="params.pageSize"
          :total="total"
          layout="total, sizes, prev, pager, next"
          @change="fetchList"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessageBox } from 'element-plus'
import { listOperationLogs, type OperationLogItem } from '@/api/operationLog'
import { formatDate } from '@/utils/format'

const loading = ref(false)
const list = ref<OperationLogItem[]>([])
const total = ref(0)
const dateRange = ref<string[]>([])

const params = reactive({
  operatorType: '',
  operatorName: '',
  businessType: '',
  operationType: '',
  pageNo: 1,
  pageSize: 20,
})

async function fetchList() {
  loading.value = true
  try {
    const res = await listOperationLogs({
      operatorType: params.operatorType || undefined,
      operatorName: params.operatorName || undefined,
      businessType: params.businessType || undefined,
      operationType: params.operationType || undefined,
      startDate: dateRange.value?.[0],
      endDate: dateRange.value?.[1],
      pageNo: params.pageNo,
      pageSize: params.pageSize,
    })
    list.value = res.records || []
    total.value = res.total || 0
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  params.pageNo = 1
  fetchList()
}

function handleReset() {
  params.operatorType = ''
  params.operatorName = ''
  params.businessType = ''
  params.operationType = ''
  dateRange.value = []
  params.pageNo = 1
  fetchList()
}

function showContent(text: string) {
  ElMessageBox.alert(text, '操作内容', { confirmButtonText: '关闭' })
}

onMounted(fetchList)
</script>

<style scoped>
.content-ellipsis {
  display: inline-block;
  max-width: 280px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  vertical-align: middle;
}
</style>
