<template>
  <div class="booking-detail">
    <div class="detail-header">
      <el-button @click="router.back()"><el-icon><ArrowLeft /></el-icon> 返回</el-button>
      <div class="header-title" v-if="detail">
        <span class="booking-no">{{ detail.bookingNo }}</span>
        <el-tag :type="bookingTagType(detail.status)" style="margin-left:10px">
          {{ bookingStatusText(detail.status) }}
        </el-tag>
        <span class="meeting-subject">{{ detail.meetingSubject }}</span>
      </div>
      <div class="header-actions" v-if="detail && showAuditActions">
        <template v-if="['PENDING_AUDIT', 'NEED_SUPPLEMENT'].includes(detail.status)">
          <el-button type="success" :loading="submitLoading" @click="handleApprove">审核通过</el-button>
          <el-button type="danger" @click="openOpinionDialog('reject')">审核驳回</el-button>
          <el-button
            v-if="detail.status === 'PENDING_AUDIT'"
            type="warning"
            @click="openOpinionDialog('supplement')"
          >退回补充材料</el-button>
        </template>
        <template v-if="['APPROVED', 'WAIT_USE'].includes(detail.status)">
          <el-button type="primary" @click="openCompleteDialog">确认使用完成</el-button>
          <el-button type="danger" plain @click="handleNoShow">标记爽约</el-button>
        </template>
      </div>
    </div>

    <div v-if="loading" v-loading="loading" style="height:300px" />

    <template v-else-if="detail">
      <el-card class="detail-card" header="预约信息">
        <el-descriptions :column="3" border>
          <el-descriptions-item label="会议室">{{ detail.roomName }}</el-descriptions-item>
          <el-descriptions-item label="预约时间" :span="2">
            {{ formatDate(detail.startTime) }} ~ {{ formatDate(detail.endTime) }}
          </el-descriptions-item>
          <el-descriptions-item label="使用人数">{{ detail.participantCount }} 人</el-descriptions-item>
          <el-descriptions-item label="会议主题" :span="2">{{ detail.meetingSubject }}</el-descriptions-item>
          <el-descriptions-item label="使用物品" :span="3">
            <template v-if="supportItems.length">
              <el-tag v-for="item in supportItems" :key="item" size="small" style="margin-right:6px">{{ item }}</el-tag>
            </template>
            <span v-else>未选择</span>
          </el-descriptions-item>
          <el-descriptions-item label="申请主体类型">
            {{ detail.enterpriseTypeName || detail.enterpriseType || '—' }}
          </el-descriptions-item>
          <el-descriptions-item label="联系人">{{ detail.contactName }}</el-descriptions-item>
          <el-descriptions-item label="联系电话" :span="2">{{ detail.contactPhone }}</el-descriptions-item>
          <el-descriptions-item label="提交时间">{{ formatDate(detail.submittedAt) }}</el-descriptions-item>
          <el-descriptions-item label="审核时间">{{ formatDate(detail.approvedAt) }}</el-descriptions-item>
          <el-descriptions-item label="完成时间">{{ formatDate(detail.completedAt) }}</el-descriptions-item>
          <el-descriptions-item v-if="detail.cancelReason" label="取消原因" :span="3">
            {{ detail.cancelReason }}
          </el-descriptions-item>
          <el-descriptions-item v-if="detail.canceledAt" label="取消时间" :span="3">
            {{ formatDate(detail.canceledAt) }}
          </el-descriptions-item>
        </el-descriptions>
      </el-card>

      <el-card class="detail-card" header="企业信息">
        <el-descriptions :column="3" border>
          <el-descriptions-item label="企业名称">{{ enterpriseName }}</el-descriptions-item>
          <el-descriptions-item label="统一社会信用代码">{{ creditCode }}</el-descriptions-item>
          <el-descriptions-item label="所属区划">{{ regionName }}</el-descriptions-item>
          <el-descriptions-item
            v-if="detail.enterpriseInfo?.meetingNoShowCount != null"
            label="累计爽约次数"
          >{{ detail.enterpriseInfo.meetingNoShowCount }} 次</el-descriptions-item>
        </el-descriptions>
      </el-card>

      <el-card v-if="roomInfo" class="detail-card" header="会议室信息">
        <el-descriptions :column="3" border>
          <el-descriptions-item label="会议室">{{ roomInfo.roomName || detail.roomName }}</el-descriptions-item>
          <el-descriptions-item label="地址" :span="2">{{ roomInfo.address || '—' }}</el-descriptions-item>
          <el-descriptions-item label="容量">{{ roomInfo.capacity ?? '—' }} 人</el-descriptions-item>
          <el-descriptions-item label="所属企服中心" :span="2">{{ roomInfo.serviceCenterName || '—' }}</el-descriptions-item>
          <el-descriptions-item label="设施" :span="3">
            <template v-if="roomFacilities.length">
              <el-tag v-for="f in roomFacilities" :key="f" size="small" style="margin-right:6px">{{ f }}</el-tag>
            </template>
            <span v-else>—</span>
          </el-descriptions-item>
        </el-descriptions>
      </el-card>

      <el-card class="detail-card" header="申请材料">
        <div v-if="materialGroups.length" class="material-groups">
          <div v-for="(mat, idx) in materialGroups" :key="mat.materialCode" class="material-group-item">
            <div class="mat-title">
              <span class="mat-index">{{ idx + 1 }}.</span>
              <span class="mat-name">{{ mat.materialName }}</span>
              <el-tag v-if="mat.requiredFlag === 1" type="danger" size="small">必传</el-tag>
            </div>
            <p v-if="mat.description" class="mat-desc">{{ mat.description }}</p>
            <template v-if="mat.attachments?.length">
              <div v-for="att in mat.attachments" :key="att.id" class="mat-file-row">
                <span class="mat-file-name">{{ att.originalName }}</span>
                <span class="mat-file-size">{{ formatFileSize(att.fileSize) }}</span>
                <el-button link type="primary" size="small" @click="downloadAttachment(att)">下载</el-button>
                <el-button v-if="isImageFile(att)" link type="primary" size="small" @click="openImagePreview(att)">预览</el-button>
              </div>
            </template>
            <div v-else class="mat-missing">未上传</div>
          </div>
        </div>
        <el-empty v-else description="暂无申请材料" :image-size="80" />
        <el-dialog v-model="imagePreviewVisible" title="图片预览" width="720px" append-to-body>
          <el-image v-if="imagePreviewUrl" :src="imagePreviewUrl" fit="contain" style="width:100%;max-height:70vh" />
        </el-dialog>
      </el-card>

      <el-card v-if="auditRecords.length" class="detail-card" header="审核记录">
        <el-timeline>
          <el-timeline-item
            v-for="rec in auditRecords"
            :key="rec.id"
            :timestamp="formatDate(rec.createdAt)"
            placement="top"
          >
            <div class="timeline-row">
              <el-tag size="small">{{ auditActionName(rec) }}</el-tag>
              <span class="tl-operator">{{ rec.operatorName }}</span>
              <span v-if="rec.operatorDeptName" class="tl-dept">（{{ rec.operatorDeptName }}）</span>
            </div>
            <div v-if="rec.beforeStatus || rec.afterStatus" class="tl-status">
              <span v-if="rec.beforeStatus">{{ bookingStatusText(rec.beforeStatus) }}</span>
              <span v-if="rec.beforeStatus && rec.afterStatus"> → </span>
              <span v-if="rec.afterStatus">{{ bookingStatusText(rec.afterStatus) }}</span>
            </div>
            <div v-if="auditOpinion(rec)" class="tl-opinion">意见：{{ auditOpinion(rec) }}</div>
          </el-timeline-item>
        </el-timeline>
      </el-card>

      <el-card v-if="usageRecord" class="detail-card" header="使用记录">
        <el-descriptions :column="3" border>
          <el-descriptions-item label="使用状态">{{ usageRecord.usageStatus || '—' }}</el-descriptions-item>
          <el-descriptions-item label="实际开始">{{ formatDate(usageRecord.actualStartTime) }}</el-descriptions-item>
          <el-descriptions-item label="实际结束">{{ formatDate(usageRecord.actualEndTime) }}</el-descriptions-item>
          <el-descriptions-item label="确认人">{{ usageRecord.confirmUserName || '—' }}</el-descriptions-item>
          <el-descriptions-item label="确认时间" :span="2">{{ formatDate(usageRecord.confirmTime) }}</el-descriptions-item>
          <el-descriptions-item v-if="usageRecord.remark" label="备注" :span="3">{{ usageRecord.remark }}</el-descriptions-item>
        </el-descriptions>
      </el-card>
    </template>

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

    <el-dialog v-model="noShowVisible" title="标记爽约" width="440px" :close-on-click-modal="false">
      <el-alert type="warning" :closable="false" show-icon style="margin-bottom:12px">
        企业累计爽约 2 次后将被限制会议室预约资格。
      </el-alert>
      <el-form label-width="80px">
        <el-form-item label="爽约原因">
          <el-input v-model="noShowForm.reason" type="textarea" :rows="3" placeholder="可选" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="noShowVisible = false">取消</el-button>
        <el-button type="danger" :loading="submitLoading" @click="handleNoShowSubmit">确认爽约</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="completeVisible" title="确认使用完成" width="480px" :close-on-click-modal="false">
      <el-form :model="completeForm" ref="completeRef" label-width="100px">
        <el-form-item label="实际开始">
          <el-date-picker
            v-model="completeForm.actualStartTime"
            type="datetime"
            value-format="YYYY-MM-DDTHH:mm:ss"
            placeholder="可留空（以预约时间为准）"
            style="width:100%"
          />
        </el-form-item>
        <el-form-item label="实际结束">
          <el-date-picker
            v-model="completeForm.actualEndTime"
            type="datetime"
            value-format="YYYY-MM-DDTHH:mm:ss"
            placeholder="可留空（以预约时间为准）"
            style="width:100%"
          />
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
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import type { FormInstance } from 'element-plus'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft } from '@element-plus/icons-vue'
import {
  getMeetingBookingDetail,
  approveMeetingBooking,
  rejectMeetingBooking,
  returnSupplementMeetingBooking,
  completeMeetingBooking,
  markMeetingBookingNoShow,
} from '@/api/meetingRoom'
import type {
  MeetingBooking, BookingAttachment, BookingAuditRecord, BookingMaterialGroup,
} from '@/api/meetingRoom'
import { getDictionary } from '@/api/common'
import { formatDate } from '@/utils/format'

const route = useRoute()
const router = useRouter()
const bookingId = computed(() => Number(route.params.id))

const loading = ref(false)
const submitLoading = ref(false)
const detail = ref<MeetingBooking | null>(null)

const BOOKING_STATUS_MAP: Record<string, string> = {
  PENDING_AUDIT: '待审核', NEED_SUPPLEMENT: '退回补充材料',
  REJECTED: '审核驳回', APPROVED: '审核通过', WAIT_USE: '待使用',
  CANCELED: '已取消', COMPLETED: '已完成', NO_SHOW: '爽约',
}

function bookingStatusText(code: string) { return BOOKING_STATUS_MAP[code] ?? code }
function bookingTagType(code: string): 'success' | 'warning' | 'danger' | 'info' | '' {
  if (['APPROVED', 'WAIT_USE', 'COMPLETED'].includes(code)) return 'success'
  if (['PENDING_AUDIT', 'NEED_SUPPLEMENT'].includes(code)) return 'warning'
  if (['REJECTED', 'NO_SHOW'].includes(code)) return 'danger'
  if (['CANCELED'].includes(code)) return 'info'
  return ''
}

const showAuditActions = computed(() => {
  const s = detail.value?.status
  return s && !['CANCELED', 'REJECTED', 'COMPLETED', 'NO_SHOW'].includes(s)
})

const materialGroups = computed((): BookingMaterialGroup[] => {
  if (detail.value?.materials?.length) return detail.value.materials
  const atts = detail.value?.attachments ?? []
  const map = new Map<string, BookingMaterialGroup>()
  for (const a of atts) {
    const code = a.fileCategory || 'OTHER'
    if (!map.has(code)) {
      map.set(code, { materialCode: code, materialName: code, requiredFlag: 0, attachments: [] })
    }
    map.get(code)!.attachments!.push(a)
  }
  return Array.from(map.values())
})
const auditRecords = computed(() => detail.value?.auditRecords ?? [])
const usageRecord = computed(() => detail.value?.usageRecord ?? null)
const roomInfo = computed(() => detail.value?.roomInfo ?? null)

const enterpriseName = computed(() =>
  detail.value?.enterpriseInfo?.enterpriseName || detail.value?.enterpriseName || '—')
const creditCode = computed(() =>
  detail.value?.enterpriseInfo?.creditCode || detail.value?.creditCode || '—')
const regionName = computed(() =>
  detail.value?.enterpriseInfo?.regionName || detail.value?.regionName || '—')

const supportItems = computed((): string[] => {
  const raw = detail.value?.supportItems as string[] | string | undefined
  if (!raw) return []
  const parts: string[] = []
  const add = (s: string) => {
    const t = s.trim()
    if (t && !parts.includes(t)) parts.push(t)
  }
  const splitOne = (s: string) => s.split(/[,，、;；\n\r]+/).forEach(add)
  if (Array.isArray(raw)) {
    for (const item of raw) {
      if (typeof item === 'string') splitOne(item)
    }
    return parts
  }
  if (typeof raw === 'string') splitOne(raw)
  return parts
})

const roomFacilities = computed((): string[] => {
  const f = roomInfo.value?.facilities as string[] | string | undefined
  if (Array.isArray(f)) return f
  if (typeof f === 'string' && f) return f.split(',').map(s => s.trim()).filter(Boolean)
  return []
})

function auditActionName(rec: BookingAuditRecord) {
  return rec.actionName || rec.actionType || rec.action || '操作'
}
function auditOpinion(rec: BookingAuditRecord) {
  return rec.auditOpinion || rec.opinion || ''
}

function formatFileSize(bytes?: number): string {
  if (!bytes) return '—'
  if (bytes < 1024) return `${bytes}B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)}KB`
  return `${(bytes / 1024 / 1024).toFixed(1)}MB`
}

const apiBase = import.meta.env.VITE_API_BASE_URL ?? ''

function resolveDownloadUrl(att: BookingAttachment): string {
  const url = att.downloadUrl || `/api/common/attachments/${att.id}/download`
  if (url.startsWith('http')) return url
  return `${apiBase}${url}`
}

const IMAGE_EXTS = new Set(['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp'])
function isImageFile(att: BookingAttachment): boolean {
  const ext = (att.fileExt || att.originalName?.split('.').pop() || '').toLowerCase()
  return IMAGE_EXTS.has(ext)
}

const imagePreviewVisible = ref(false)
const imagePreviewUrl = ref('')

function openImagePreview(att: BookingAttachment) {
  imagePreviewUrl.value = resolveDownloadUrl(att)
  imagePreviewVisible.value = true
}

function downloadAttachment(att: BookingAttachment) {
  const url = resolveDownloadUrl(att)
  const win = window.open(url, '_blank')
  if (!win) {
    ElMessage.error('附件下载失败，请检查文件是否存在或服务器上传目录权限')
  }
}

async function loadDetail() {
  loading.value = true
  try {
    detail.value = await getMeetingBookingDetail(bookingId.value)
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  const statuses = await getDictionary('MEETING_BOOKING_STATUS')
  for (const d of statuses) BOOKING_STATUS_MAP[d.dictCode] = d.dictLabel
  if (!bookingId.value || Number.isNaN(bookingId.value)) {
    ElMessage.error('无效的预约 ID')
    router.back()
    return
  }
  await loadDetail()
})

async function handleApprove() {
  if (!detail.value) return
  try {
    await ElMessageBox.confirm(
      `确定审核通过「${detail.value.meetingSubject}」的预约申请吗？`,
      '确认审核',
      { type: 'warning' },
    )
  } catch { return }
  submitLoading.value = true
  try {
    await approveMeetingBooking(bookingId.value, {})
    ElMessage.success('审核通过成功')
    await loadDetail()
  } catch (e: unknown) {
    const msg = (e as Error)?.message || ''
    if (msg.includes('40902') || msg.includes('冲突') || msg.includes('占用')) {
      ElMessage.error('该时段已被预约或占用')
    }
  } finally {
    submitLoading.value = false
  }
}

const opinionVisible = ref(false)
const opinionDialogTitle = ref('审核驳回')
const opinionAction = ref<'reject' | 'supplement'>('reject')
const opinionRef = ref<FormInstance>()
const opinionForm = reactive({ auditOpinion: '' })
const opinionRules = {
  auditOpinion: [{ required: true, message: '请输入审核意见', trigger: 'blur' }],
}

function openOpinionDialog(action: 'reject' | 'supplement') {
  opinionAction.value = action
  opinionDialogTitle.value = action === 'reject' ? '审核驳回' : '退回补充材料'
  opinionForm.auditOpinion = ''
  opinionRef.value?.clearValidate()
  opinionVisible.value = true
}

async function handleOpinionSubmit() {
  await opinionRef.value?.validate()
  submitLoading.value = true
  try {
    if (opinionAction.value === 'reject') {
      await rejectMeetingBooking(bookingId.value, { auditOpinion: opinionForm.auditOpinion })
      ElMessage.success('驳回成功')
    } else {
      await returnSupplementMeetingBooking(bookingId.value, { auditOpinion: opinionForm.auditOpinion })
      ElMessage.success('退回补充成功')
    }
    opinionVisible.value = false
    await loadDetail()
  } finally {
    submitLoading.value = false
  }
}

const completeVisible = ref(false)
const completeRef = ref<FormInstance>()
const completeForm = reactive({
  actualStartTime: '',
  actualEndTime: '',
  remark: '',
})

function openCompleteDialog() {
  Object.assign(completeForm, { actualStartTime: '', actualEndTime: '', remark: '' })
  completeVisible.value = true
}

async function handleCompleteSubmit() {
  submitLoading.value = true
  try {
    await completeMeetingBooking(bookingId.value, {
      actualStartTime: completeForm.actualStartTime || undefined,
      actualEndTime: completeForm.actualEndTime || undefined,
      remark: completeForm.remark || undefined,
    })
    ElMessage.success('已标记为使用完成')
    completeVisible.value = false
    await loadDetail()
  } finally {
    submitLoading.value = false
  }
}

const noShowVisible = ref(false)
const noShowForm = reactive({ reason: '' })

function handleNoShow() {
  noShowForm.reason = ''
  noShowVisible.value = true
}

async function handleNoShowSubmit() {
  submitLoading.value = true
  try {
    await markMeetingBookingNoShow(bookingId.value, { reason: noShowForm.reason || undefined })
    ElMessage.success('已标记为爽约')
    noShowVisible.value = false
    await loadDetail()
  } finally {
    submitLoading.value = false
  }
}
</script>

<style scoped>
.booking-detail { padding: 0 4px 24px; }
.detail-header {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 16px;
}
.header-title {
  flex: 1;
  min-width: 200px;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}
.booking-no { font-weight: 600; font-size: 16px; }
.meeting-subject { color: #666; font-size: 14px; }
.header-actions { display: flex; flex-wrap: wrap; gap: 8px; }
.detail-card { margin-bottom: 12px; }
.timeline-row { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.tl-operator { font-weight: 500; }
.tl-dept { color: #888; font-size: 13px; }
.tl-status { color: #666; font-size: 13px; margin-top: 4px; }
.tl-opinion { color: #555; margin-top: 6px; font-size: 13px; }
.material-groups { display: flex; flex-direction: column; gap: 16px; }
.material-group-item { padding: 12px; background: #fafafa; border-radius: 4px; border: 1px solid #eee; }
.mat-title { display: flex; align-items: center; gap: 8px; font-weight: 600; }
.mat-index { color: #909399; }
.mat-desc { margin: 6px 0 8px; font-size: 13px; color: #666; }
.mat-file-row { display: flex; align-items: center; gap: 12px; padding: 4px 0; font-size: 13px; }
.mat-file-name { flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.mat-file-size { color: #909399; font-size: 12px; }
.mat-missing { color: #f56c6c; font-size: 13px; }
</style>
