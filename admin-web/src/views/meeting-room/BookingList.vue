<template>
  <div>
    <div class="page-header">
      <h2>预约管理</h2>
      <div class="header-actions">
        <el-button @click="handleQueryLedger">查询台账</el-button>
        <el-button @click="handleExport">导出</el-button>
      </div>
    </div>

    <!-- 查询区域 -->
    <el-card shadow="never" class="filter-card">
      <el-form :model="params" inline>
        <el-form-item label="会议室">
          <el-input v-model="roomNameFilter" placeholder="会议室名称" clearable style="width:140px" />
        </el-form-item>
        <el-form-item label="企业名称">
          <el-input v-model="params.enterpriseName" placeholder="请输入" clearable style="width:150px" />
        </el-form-item>
        <el-form-item label="信用代码">
          <el-input v-model="params.creditCode" placeholder="请输入" clearable style="width:170px" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="params.status" placeholder="全部" clearable style="width:130px">
            <el-option v-for="s in bookingStatusOptions" :key="s.value" :label="s.label" :value="s.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="区划">
          <el-select v-model="params.regionCode" placeholder="全部" clearable style="width:120px">
            <el-option v-for="r in regionOptions" :key="r.value" :label="r.label" :value="r.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="预约日期">
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

    <!-- 台账模式提示 -->
    <el-alert v-if="isLedgerMode" type="info" :closable="true" @close="exitLedgerMode" style="margin-top:12px">
      当前显示预约台账数据，点击右侧关闭返回普通查询。
    </el-alert>

    <!-- 表格 -->
    <el-card shadow="never" class="table-card" style="margin-top:12px">
      <el-table :data="list" v-loading="loading" stripe>
        <el-table-column prop="bookingNo" label="预约编号" width="150" show-overflow-tooltip />
        <el-table-column prop="roomName" label="会议室" width="130" show-overflow-tooltip />
        <el-table-column prop="enterpriseName" label="企业名称" min-width="140" show-overflow-tooltip />
        <el-table-column prop="meetingSubject" label="会议主题" min-width="160" show-overflow-tooltip />
        <el-table-column label="预约时间" width="290">
          <template #default="{ row }">
            {{ formatDate(row.startTime) }} ~ {{ formatDate(row.endTime) }}
          </template>
        </el-table-column>
        <el-table-column label="状态" width="110">
          <template #default="{ row }">
            <el-tag :type="bookingTagType(row.status)" size="small">{{ bookingStatusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="提交时间" width="155">
          <template #default="{ row }">{{ formatDate(row.submittedAt) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="260" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="goDetail(row)">查看详情</el-button>
            <el-button
              v-if="['PENDING_AUDIT','NEED_SUPPLEMENT'].includes(row.status)"
              link type="success" @click="handleApprove(row)">通过</el-button>
            <el-button
              v-if="['PENDING_AUDIT','NEED_SUPPLEMENT'].includes(row.status)"
              link type="danger" @click="openOpinionDialog('reject', row)">驳回</el-button>
            <el-button
              v-if="row.status === 'PENDING_AUDIT'"
              link type="warning" @click="openOpinionDialog('supplement', row)">退回补充</el-button>
            <el-button
              v-if="['APPROVED','WAIT_USE'].includes(row.status)"
              link type="primary" @click="openCompleteDialog(row)">完成</el-button>
            <el-button
              v-if="['APPROVED','WAIT_USE'].includes(row.status)"
              link type="danger" @click="handleNoShow(row)">爽约</el-button>
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

    <!-- ====== 审核意见弹窗（驳回/退回补充）====== -->
    <el-dialog v-model="opinionVisible" :title="opinionDialogTitle" width="440px" :close-on-click-modal="false">
      <el-form :model="opinionForm" :rules="opinionRules" ref="opinionRef" label-width="80px">
        <el-form-item label="审核意见" prop="auditOpinion">
          <el-input v-model="opinionForm.auditOpinion" type="textarea" :rows="4" placeholder="请输入审核意见" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="opinionVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleOpinionSubmit">确认</el-button>
      </template>
    </el-dialog>

    <!-- ====== 确认完成弹窗 ====== -->
    <el-dialog v-model="completeVisible" title="确认使用完成" width="480px" :close-on-click-modal="false">
      <el-form :model="completeForm" ref="completeRef" label-width="100px">
        <el-form-item label="实际开始">
          <el-date-picker v-model="completeForm.actualStartTime" type="datetime" value-format="YYYY-MM-DDTHH:mm:ss"
            placeholder="可留空（以预约时间为准）" style="width:100%" />
        </el-form-item>
        <el-form-item label="实际结束">
          <el-date-picker v-model="completeForm.actualEndTime" type="datetime" value-format="YYYY-MM-DDTHH:mm:ss"
            placeholder="可留空（以预约时间为准）" style="width:100%" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="completeForm.remark" type="textarea" :rows="2" placeholder="可选" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="completeVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleCompleteSubmit">确认完成</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import type { FormInstance } from 'element-plus'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import {
  getMeetingBookingList,
  approveMeetingBooking, rejectMeetingBooking, returnSupplementMeetingBooking,
  completeMeetingBooking, markMeetingBookingNoShow,
  getMeetingBookingLedger, exportMeetingBookingLedger,
} from '@/api/meetingRoom'
import type { MeetingBooking } from '@/api/meetingRoom'
import { getDictionary } from '@/api/common'
import { formatDate } from '@/utils/format'

const router = useRouter()

// ── 字典 ──────────────────────────────────────────────────────────────────────
const regionOptions = ref<{value:string;label:string}[]>([])

const BOOKING_STATUS_MAP: Record<string, string> = {
  PENDING_AUDIT: '待审核', NEED_SUPPLEMENT: '退回补充材料',
  REJECTED: '审核驳回', APPROVED: '审核通过', WAIT_USE: '待使用',
  CANCELED: '已取消', COMPLETED: '已完成', NO_SHOW: '爽约',
}
const bookingStatusOptions = ref(
  Object.entries(BOOKING_STATUS_MAP).map(([v, l]) => ({ value: v, label: l }))
)

function bookingStatusText(code: string) { return BOOKING_STATUS_MAP[code] ?? code }
function bookingTagType(code: string): 'success' | 'warning' | 'danger' | 'info' | '' {
  if (['APPROVED', 'WAIT_USE', 'COMPLETED'].includes(code)) return 'success'
  if (['PENDING_AUDIT', 'NEED_SUPPLEMENT'].includes(code)) return 'warning'
  if (['REJECTED', 'NO_SHOW'].includes(code)) return 'danger'
  if (['CANCELED'].includes(code)) return 'info'
  return ''
}

onMounted(async () => {
  const [regions, statuses] = await Promise.all([
    getDictionary('REGION'),
    getDictionary('MEETING_BOOKING_STATUS'),
  ])
  if (regions.length) regionOptions.value = regions.map(d => ({ value: d.dictCode, label: d.dictLabel }))
  if (statuses.length) {
    bookingStatusOptions.value = statuses.map(d => ({ value: d.dictCode, label: d.dictLabel }))
    for (const d of statuses) BOOKING_STATUS_MAP[d.dictCode] = d.dictLabel
  }
  fetchList()
})

// ── 列表 ──────────────────────────────────────────────────────────────────────
const loading = ref(false)
const list = ref<MeetingBooking[]>([])
const total = ref(0)
const dateRange = ref<[string,string] | null>(null)
const roomNameFilter = ref('')
const isLedgerMode = ref(false)

const params = ref({
  enterpriseName: '',
  creditCode: '',
  status: '',
  regionCode: '',
  startDate: '',
  endDate: '',
  pageNo: 1,
  pageSize: 10,
})

function buildQueryParams() {
  return {
    enterpriseName: params.value.enterpriseName || undefined,
    creditCode: params.value.creditCode || undefined,
    status: params.value.status || undefined,
    regionCode: params.value.regionCode || undefined,
    startDate: dateRange.value?.[0] || undefined,
    endDate: dateRange.value?.[1] || undefined,
    pageNo: params.value.pageNo,
    pageSize: params.value.pageSize,
  }
}

async function fetchList() {
  loading.value = true
  isLedgerMode.value = false
  try {
    const res = await getMeetingBookingList(buildQueryParams())
    list.value = res.records
    total.value = res.total
  } finally {
    loading.value = false
  }
}

function handleSearch() { params.value.pageNo = 1; fetchList() }
function handleReset() {
  params.value = { enterpriseName: '', creditCode: '', status: '', regionCode: '', startDate: '', endDate: '', pageNo: 1, pageSize: 10 }
  dateRange.value = null
  roomNameFilter.value = ''
  fetchList()
}
function exitLedgerMode() { fetchList() }

// ── 台账 & 导出 ───────────────────────────────────────────────────────────────
async function handleQueryLedger() {
  loading.value = true
  isLedgerMode.value = true
  try {
    const res = await getMeetingBookingLedger(buildQueryParams())
    list.value = res.records
    total.value = res.total
  } finally {
    loading.value = false
  }
}

async function handleExport() {
  try {
    const result = await exportMeetingBookingLedger(buildQueryParams())
    ElMessage.info(`导出接口已调用，当前返回 JSON 数据（共 ${(result as { total?: number })?.total ?? (result as unknown[])?.length ?? 0} 条），后续替换为 Excel 下载`)
  } catch {
    // handled by interceptor
  }
}

function goDetail(row: MeetingBooking) {
  router.push({ name: 'BookingDetail', params: { id: String(row.id) } })
}

// ── 审核通过 ──────────────────────────────────────────────────────────────────
const submitLoading = ref(false)

async function handleApprove(row: MeetingBooking) {
  try {
    await ElMessageBox.confirm(`确定审核通过「${row.meetingSubject}」的预约申请吗？`, '确认审核', { type: 'warning' })
  } catch { return }
  submitLoading.value = true
  try {
    await approveMeetingBooking(row.id, {})
    ElMessage.success('审核通过成功')
    fetchList()
  } catch (e: unknown) {
    const err = e as { message?: string }
    if (err?.message?.includes('40902') || err?.message?.includes('冲突') || err?.message?.includes('占用')) {
      ElMessage.error('该时段已被预约或占用')
    }
  } finally {
    submitLoading.value = false
  }
}

// ── 意见弹窗（驳回/退回补充）─────────────────────────────────────────────────
const opinionVisible = ref(false)
const opinionDialogTitle = ref('审核驳回')
const opinionAction = ref<'reject' | 'supplement'>('reject')
const currentBookingId = ref(0)
const opinionRef = ref<FormInstance>()
const opinionForm = reactive({ auditOpinion: '' })
const opinionRules = {
  auditOpinion: [{ required: true, message: '请输入审核意见', trigger: 'blur' }],
}

function openOpinionDialog(action: 'reject' | 'supplement', row: MeetingBooking) {
  opinionAction.value = action
  opinionDialogTitle.value = action === 'reject' ? '审核驳回' : '退回补充材料'
  currentBookingId.value = row.id
  opinionForm.auditOpinion = ''
  opinionRef.value?.clearValidate()
  opinionVisible.value = true
}

async function handleOpinionSubmit() {
  await opinionRef.value?.validate()
  submitLoading.value = true
  try {
    if (opinionAction.value === 'reject') {
      await rejectMeetingBooking(currentBookingId.value, { auditOpinion: opinionForm.auditOpinion })
      ElMessage.success('驳回成功')
    } else {
      await returnSupplementMeetingBooking(currentBookingId.value, { auditOpinion: opinionForm.auditOpinion })
      ElMessage.success('退回补充成功')
    }
    opinionVisible.value = false
    fetchList()
  } finally {
    submitLoading.value = false
  }
}

// ── 确认完成 ──────────────────────────────────────────────────────────────────
const completeVisible = ref(false)
const completeRef = ref<FormInstance>()
const completeForm = reactive({
  actualStartTime: '',
  actualEndTime: '',
  remark: '',
})

function openCompleteDialog(row: MeetingBooking) {
  currentBookingId.value = row.id
  Object.assign(completeForm, { actualStartTime: '', actualEndTime: '', remark: '' })
  completeVisible.value = true
}

async function handleCompleteSubmit() {
  submitLoading.value = true
  try {
    await completeMeetingBooking(currentBookingId.value, {
      actualStartTime: completeForm.actualStartTime || undefined,
      actualEndTime: completeForm.actualEndTime || undefined,
      remark: completeForm.remark || undefined,
    })
    ElMessage.success('已标记为使用完成')
    completeVisible.value = false
    fetchList()
  } finally {
    submitLoading.value = false
  }
}

// ── 标记爽约 ──────────────────────────────────────────────────────────────────
async function handleNoShow(row: MeetingBooking) {
  try {
    await ElMessageBox.confirm(
      `确定将此预约标记为爽约吗？\n企业累计爽约 2 次后将限制预约资格。`,
      '标记爽约',
      { type: 'warning', confirmButtonText: '确认爽约', confirmButtonClass: 'el-button--danger' }
    )
  } catch { return }
  submitLoading.value = true
  try {
    await markMeetingBookingNoShow(row.id, {})
    ElMessage.success('已标记为爽约')
    fetchList()
  } finally {
    submitLoading.value = false
  }
}
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  h2 { margin: 0; font-size: 18px; }
}
.header-actions { display: flex; gap: 8px; }
.filter-card { margin-bottom: 0; }
.pagination-wrap { display: flex; justify-content: flex-end; margin-top: 16px; }
.section-title { font-size: 14px; font-weight: 600; color: #333; margin-bottom: 12px; padding-bottom: 8px; border-bottom: 1px solid #eee; }
</style>
