<template>
  <div>
    <div class="page-header">
      <h2>企业诉求管理</h2>
    </div>

    <el-card shadow="never" class="filter-card">
      <el-form :model="params" inline>
        <el-form-item label="企业名称">
          <el-input v-model="params.enterpriseName" placeholder="请输入" clearable style="width:150px" />
        </el-form-item>
        <el-form-item label="信用代码">
          <el-input v-model="params.creditCode" placeholder="请输入" clearable style="width:170px" />
        </el-form-item>
        <el-form-item label="诉求状态">
          <el-select v-model="params.status" placeholder="全部" clearable style="width:140px">
            <el-option v-for="s in statusOptions" :key="s.value" :label="s.label" :value="s.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="诉求类型">
          <el-select v-model="params.appealTypeCode" placeholder="全部" clearable style="width:130px">
            <el-option v-for="t in typeOptions" :key="t.value" :label="t.label" :value="t.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="区划">
          <el-select v-model="params.regionCode" placeholder="全部" clearable style="width:120px">
            <el-option v-for="r in regionOptions" :key="r.value" :label="r.label" :value="r.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="责任单位ID">
          <el-input v-model="params.responsibleDeptId" placeholder="部门ID" clearable style="width:140px" />
        </el-form-item>
        <el-form-item label="提交时间">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始"
            end-placeholder="结束"
            value-format="YYYY-MM-DD"
            style="width:240px"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch"><el-icon><Search /></el-icon> 查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card shadow="never" class="table-card" style="margin-top:12px">
      <el-table :data="list" v-loading="loading" stripe row-key="id">
        <el-table-column prop="appealNo" label="诉求编号" width="150" show-overflow-tooltip />
        <el-table-column prop="enterpriseName" label="企业名称" min-width="150" show-overflow-tooltip />
        <el-table-column prop="title" label="诉求标题" min-width="200" show-overflow-tooltip />
        <el-table-column prop="appealTypeName" label="诉求类型" width="110">
          <template #default="{ row }">{{ row.appealTypeName || typeMap[row.appealTypeCode] || '--' }}</template>
        </el-table-column>
        <el-table-column prop="urgencyLevel" label="紧急" width="70">
          <template #default="{ row }">
            <el-tag v-if="row.urgencyLevel && row.urgencyLevel !== 'NORMAL'" type="warning" size="small">急</el-tag>
            <span v-else>--</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="130">
          <template #default="{ row }">
            <el-tag :type="appealTagType(row.status)" size="small">{{ statusMap[row.status] || row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="regionName" label="区划" width="90" />
        <el-table-column prop="responsibleDeptName" label="责任单位" width="130" show-overflow-tooltip>
          <template #default="{ row }">{{ row.responsibleDeptName || '--' }}</template>
        </el-table-column>
        <el-table-column prop="submittedAt" label="提交时间" width="155">
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
          layout="total, sizes, prev, pager, next, jumper"
          @change="fetchList"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getAppealList } from '@/api/appeal'
import type { AppealItem } from '@/api/appeal'
import { formatDate } from '@/utils/format'
import { getDictionary, dictToMap } from '@/api/common'
import { appealTagType, APPEAL_STATUS_MAP, APPEAL_TYPE_MAP } from '@/utils/appealConsts'

const router = useRouter()
const loading = ref(false)
const list = ref<AppealItem[]>([])
const total = ref(0)
const dateRange = ref<[string, string] | null>(null)

// 字典选项（优先后端，回退本地枚举）
const statusOptions = ref<{value:string,label:string}[]>([])
const typeOptions = ref<{value:string,label:string}[]>([])
const regionOptions = ref<{value:string,label:string}[]>([])
const statusMap = ref<Record<string,string>>(APPEAL_STATUS_MAP)
const typeMap = ref<Record<string,string>>(APPEAL_TYPE_MAP)

onMounted(async () => {
  const [statuses, types, regions] = await Promise.all([
    getDictionary('APPEAL_STATUS'),
    getDictionary('APPEAL_TYPE'),
    getDictionary('REGION'),
  ])
  if (statuses.length) {
    statusOptions.value = statuses.map(d => ({ value: d.dictCode, label: d.dictLabel }))
    statusMap.value = dictToMap(statuses)
  } else {
    statusOptions.value = Object.entries(APPEAL_STATUS_MAP).map(([v,l]) => ({ value:v, label:l }))
  }
  if (types.length) {
    typeOptions.value = types.map(d => ({ value: d.dictCode, label: d.dictLabel }))
    typeMap.value = dictToMap(types)
  } else {
    typeOptions.value = Object.entries(APPEAL_TYPE_MAP).map(([v,l]) => ({ value:v, label:l }))
  }
  regionOptions.value = regions.map(d => ({ value: d.dictCode, label: d.dictLabel }))
  fetchList()
})

const params = ref({
  enterpriseName: '', creditCode: '', status: '', appealTypeCode: '',
  regionCode: '', responsibleDeptId: '', startDate: '', endDate: '',
  pageNo: 1, pageSize: 10
})

async function fetchList() {
  loading.value = true
  try {
    if (dateRange.value) {
      params.value.startDate = dateRange.value[0]
      params.value.endDate = dateRange.value[1]
    } else {
      params.value.startDate = ''
      params.value.endDate = ''
    }
    const q: Record<string,unknown> = { pageNo: params.value.pageNo, pageSize: params.value.pageSize }
    if (params.value.enterpriseName) q.enterpriseName = params.value.enterpriseName
    if (params.value.creditCode) q.creditCode = params.value.creditCode
    if (params.value.status) q.status = params.value.status
    if (params.value.appealTypeCode) q.appealTypeCode = params.value.appealTypeCode
    if (params.value.regionCode) q.regionCode = params.value.regionCode
    if (params.value.responsibleDeptId) q.responsibleDeptId = params.value.responsibleDeptId
    if (params.value.startDate) q.startDate = params.value.startDate
    if (params.value.endDate) q.endDate = params.value.endDate
    const res = await getAppealList(q)
    list.value = res.records
    total.value = res.total
  } finally {
    loading.value = false
  }
}

function handleSearch() { params.value.pageNo = 1; fetchList() }
function handleReset() {
  params.value = { enterpriseName:'', creditCode:'', status:'', appealTypeCode:'',
    regionCode:'', responsibleDeptId:'', startDate:'', endDate:'', pageNo:1, pageSize:10 }
  dateRange.value = null
  fetchList()
}
function goDetail(id: number) { router.push(`/appeals/${id}`) }
</script>

<style scoped lang="scss">
.filter-card { :deep(.el-card__body) { padding: 16px 16px 0; } }
.pagination-wrap { display:flex; justify-content:flex-end; margin-top:16px; }
</style>
