<template>
  <div class="page">
    <van-nav-bar title="预约详情" left-arrow @click-left="router.back()" fixed />

    <div class="page-body page-body--action">
      <van-loading v-if="loading" size="32" vertical style="padding:60px 0;display:flex;justify-content:center">加载中...</van-loading>

      <template v-if="!loading && booking">
        <!-- 状态横幅 -->
        <div
          class="status-banner status-banner--center"
          :style="{ background: statusBannerGradient('booking', booking.status) }"
        >
          <div class="status-banner__text">{{ statusLabel('booking', booking.status) }}</div>
          <div class="status-banner__sub">{{ bookingStatusHint(booking.status) }}</div>
        </div>

        <!-- 审核未通过 / 退回补充提示 -->
        <van-notice-bar
          v-if="booking.status === 'REJECTED'"
          left-icon="warning-o"
          color="#ee0a24"
          background="#fff1f0"
          :scrollable="false"
          wrapable
          style="margin-top:12px"
        >
          <div class="audit-alert">
            <div class="audit-alert__title">审核未通过</div>
            <div class="audit-alert__text">审核驳回原因：{{ rejectOpinionText }}</div>
          </div>
        </van-notice-bar>

        <van-notice-bar
          v-if="booking.status === 'NEED_SUPPLEMENT'"
          left-icon="info-o"
          color="#ed6a0c"
          background="#fff7e8"
          :scrollable="false"
          wrapable
          style="margin-top:12px"
        >
          <div class="audit-alert">
            <div class="audit-alert__title">退回补充材料</div>
            <div class="audit-alert__text">退回补充说明：{{ supplementOpinionText }}</div>
          </div>
        </van-notice-bar>

        <!-- 预约信息 -->
        <van-cell-group inset style="margin-top:12px" title="预约信息">
          <van-cell title="预约编号" :value="booking.bookingNo || booking.booking_no" value-class="mono" />
          <van-cell title="会议室" :value="booking.roomName || booking.room_name" />
          <van-cell title="会议主题" :value="booking.meetingSubject || booking.meeting_subject" />
          <van-cell title="与会人数" :value="`${booking.participantCount || booking.participant_count} 人`" />
          <van-cell title="联系人" :value="booking.contactName || booking.contact_name" />
          <van-cell title="联系电话" :value="booking.contactPhone || booking.contact_phone" />
          <van-cell title="开始时间" :value="formatDt(booking.startTime || booking.start_time)" />
          <van-cell title="结束时间" :value="formatDt(booking.endTime || booking.end_time)" />
        </van-cell-group>

        <!-- 使用物品 -->
        <van-cell-group inset style="margin-top:12px" title="使用物品">
          <div v-if="supportItemList.length" style="padding:10px 16px;display:flex;flex-wrap:wrap;gap:6px">
            <van-tag v-for="item in supportItemList" :key="item" plain>{{ item }}</van-tag>
          </div>
          <div v-else style="padding:10px 16px;color:#999;font-size:13px">未选择</div>
        </van-cell-group>

        <!-- 附件 -->
        <van-cell-group
          v-if="booking.attachments && booking.attachments.length"
          inset style="margin-top:12px" title="上传材料"
        >
          <div
            v-for="att in booking.attachments"
            :key="att.id"
            class="att-item"
            @click="openAttachment(att.id)"
          >
            <van-icon name="description" color="#1989fa" size="18" />
            <span class="att-name">{{ att.originalName }}</span>
            <van-icon name="arrow" color="#ccc" size="14" />
          </div>
        </van-cell-group>

        <!-- 取消提醒 -->
        <van-notice-bar
          v-if="canCancel"
          left-icon="info-o"
          color="#ff976a"
          background="#fff7f0"
          :scrollable="false"
          wrapable
          style="margin:12px 0 0"
        >
          审核通过后取消需至少提前半天，并线下通知工作人员
        </van-notice-bar>

        <!-- 审核记录 -->
        <div v-if="auditRecords.length" style="margin-top:12px">
          <div class="section-title">审核记录</div>
          <van-steps direction="vertical" :active="auditRecords.length - 1" active-color="#07c160" style="padding:0 12px">
            <van-step v-for="rec in auditRecords" :key="rec.id">
              <div class="step-action">{{ rec.actionName || rec.action_name || rec.action }}</div>
              <div v-if="auditOpinionOf(rec)" class="step-opinion">{{ auditOpinionOf(rec) }}</div>
              <div class="step-meta">
                {{ rec.operatorName || rec.operator_name }}
                · {{ formatDt(rec.createdAt || rec.created_at) }}
              </div>
            </van-step>
          </van-steps>
        </div>

        <!-- 使用记录 -->
        <van-cell-group
          v-if="booking.actualStartTime || booking.actualEndTime"
          inset style="margin:12px 0" title="使用记录"
        >
          <van-cell v-if="booking.actualStartTime" title="实际开始" :value="formatDt(booking.actualStartTime)" />
          <van-cell v-if="booking.actualEndTime" title="实际结束" :value="formatDt(booking.actualEndTime)" />
          <van-cell v-if="booking.completedRemark" title="备注" :value="booking.completedRemark" />
        </van-cell-group>

        <!-- 操作按钮 -->
        <div v-if="canSupplement || canCancel" class="bottom-bar bottom-bar--multi">
          <van-button
            v-if="canSupplement"
            type="warning"
            round
            block
            @click="openSupplementPopup"
          >补充材料</van-button>
          <van-button
            v-if="canCancel"
            type="danger"
            round
            block
            plain
            @click="showCancelDialog = true"
          >取消预约</van-button>
        </div>
      </template>

      <van-empty v-if="!loading && !booking" description="预约记录不存在" />
    </div>

    <!-- 取消对话框 -->
    <van-dialog
      v-model:show="showCancelDialog"
      title="取消预约"
      show-cancel-button
      :before-close="handleCancelConfirm"
    >
      <div style="padding:12px 16px">
        <van-field
          v-model="cancelReason"
          type="textarea"
          placeholder="请输入取消原因"
          rows="3"
          maxlength="200"
          show-word-limit
          :rules="[{required:true,message:'请输入取消原因'}]"
        />
      </div>
    </van-dialog>

    <!-- 补充材料弹窗 -->
    <van-popup
      v-model:show="showSupplementPopup"
      position="bottom"
      round
      :style="{ height: '85%' }"
      @open="onSupplementPopupOpen"
    >
      <div class="supplement-popup">
        <div class="supplement-popup__title">补充材料</div>
        <div class="supplement-popup__hint">退回补充说明：{{ supplementOpinionText }}</div>

        <van-loading v-if="supplementRulesLoading" size="24" style="padding:24px;text-align:center" />
        <template v-else>
          <div
            v-for="rule in supplementRules"
            :key="matCode(rule)"
            class="material-block"
          >
            <div class="material-head">
              <span class="material-name">{{ matName(rule) }}</span>
              <van-tag v-if="matRequired(rule)" type="danger" size="medium">必传</van-tag>
            </div>
            <div v-if="rule.description" class="material-desc">{{ rule.description }}</div>
            <div
              v-for="f in supplementFiles[matCode(rule)] || []"
              :key="f.id"
              class="file-item"
            >
              <van-icon name="description" color="#1989fa" size="18" />
              <span class="file-name">{{ f.originalName }}</span>
              <van-icon name="cross" @click="removeSupplementFile(matCode(rule), f.id)" />
            </div>
            <van-uploader
              :after-read="(item) => handleSupplementUpload(matCode(rule), item)"
              accept=".jpg,.jpeg,.png,.pdf,.doc,.docx"
              :max-size="10 * 1024 * 1024"
              @oversize="showToast('单个文件不能超过10MB')"
              :disabled="supplementUploading"
            >
              <van-button icon="plus" size="small" plain type="primary" :loading="supplementUploading">
                上传{{ matName(rule) }}
              </van-button>
            </van-uploader>
          </div>
        </template>

        <van-field
          v-model="supplementRemark"
          type="textarea"
          rows="2"
          maxlength="200"
          placeholder="补充说明（选填）"
          style="margin-top:12px"
        />

        <div class="supplement-popup__actions">
          <van-button round block type="primary" :loading="supplementSubmitting" @click="submitSupplement">
            提交补充材料
          </van-button>
        </div>
      </div>
    </van-popup>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { showToast, showSuccessToast } from 'vant'
import type { UploaderFileListItem } from 'vant'
import {
  getMeetingBookingDetail, cancelMeetingBooking, supplementMeetingBooking,
  getMeetingRoomMaterialRules, matName, matRequired, matCode,
} from '@/api/meetingRoom'
import type { MeetingBooking, BookingAuditRecord, MaterialRule } from '@/api/meetingRoom'
import { uploadAttachment } from '@/api/common'
import { apiAssetUrl } from '@/utils/api'
import { validateFileSize } from '@/constants/upload'
import { statusLabel, statusBannerGradient, bookingStatusHint } from '@/utils/status'
import { formatDate, parseSupportItems, getField } from '@/utils/format'

const router = useRouter()
const route = useRoute()
const bookingId = Number(route.params.id)

const loading = ref(true)
const booking = ref<MeetingBooking | null>(null)
const showCancelDialog = ref(false)
const cancelReason = ref('')
const canceling = ref(false)

const CAN_CANCEL_STATUSES = ['PENDING_AUDIT', 'NEED_SUPPLEMENT', 'APPROVED', 'WAIT_USE']
const canCancel = computed(() => booking.value && CAN_CANCEL_STATUSES.includes(booking.value.status))
const canSupplement = computed(() => booking.value?.status === 'NEED_SUPPLEMENT')

const showSupplementPopup = ref(false)
const supplementRules = ref<MaterialRule[]>([])
const supplementRulesLoading = ref(false)
const supplementFiles = ref<Record<string, { id: number; originalName: string; fileSize?: number }[]>>({})
const supplementUploading = ref(false)
const supplementSubmitting = ref(false)
const supplementRemark = ref('')

const auditRecords = computed<BookingAuditRecord[]>(() => booking.value?.auditRecords || [])

const supportItemList = computed(() =>
  parseSupportItems(
    (booking.value?.supportItems ?? booking.value?.support_items) as string[] | string | undefined
  )
)

function auditOpinionOf(rec: BookingAuditRecord): string {
  return getField<string>(rec, 'auditOpinion', 'audit_opinion', 'opinion') || ''
}

function sortRecordsDesc(records: BookingAuditRecord[]): BookingAuditRecord[] {
  return [...records].sort((a, b) => {
    const ta = new Date(a.createdAt || a.created_at || 0).getTime()
    const tb = new Date(b.createdAt || b.created_at || 0).getTime()
    return tb - ta
  })
}

function findLatestOpinion(
  records: BookingAuditRecord[],
  match: (rec: BookingAuditRecord) => boolean
): string {
  for (const rec of sortRecordsDesc(records)) {
    if (match(rec)) {
      const text = auditOpinionOf(rec)
      if (text) return text
    }
  }
  return ''
}

const rejectOpinionText = computed(() => {
  if (booking.value?.status !== 'REJECTED') return ''
  const text = findLatestOpinion(auditRecords.value, rec => {
    const action = getField<string>(rec, 'actionType', 'action_type', 'action') || ''
    const after = getField<string>(rec, 'afterStatus', 'after_status') || ''
    return action === 'REJECT' || after === 'REJECTED'
  })
  return text || '暂无审核意见'
})

const supplementOpinionText = computed(() => {
  if (booking.value?.status !== 'NEED_SUPPLEMENT') return ''
  const text = findLatestOpinion(auditRecords.value, rec => {
    const action = getField<string>(rec, 'actionType', 'action_type', 'action') || ''
    const after = getField<string>(rec, 'afterStatus', 'after_status') || ''
    return action === 'RETURN_SUPPLEMENT' || after === 'NEED_SUPPLEMENT'
  })
  return text || '暂无审核意见'
})

const formatDt = formatDate

function openAttachment(id: number) {
  window.open(apiAssetUrl(`/api/common/attachments/${id}/download`), '_blank')
}

async function fetchBooking() {
  loading.value = true
  try {
    booking.value = await getMeetingBookingDetail(bookingId)
  } catch {
    booking.value = null
  } finally {
    loading.value = false
  }
}

async function handleCancelConfirm(action: string) {
  if (action !== 'confirm') return true
  if (!cancelReason.value.trim()) {
    showToast('请输入取消原因')
    return false
  }
  canceling.value = true
  try {
    await cancelMeetingBooking(bookingId, { cancelReason: cancelReason.value })
    showToast('预约已取消')
    showCancelDialog.value = false
    cancelReason.value = ''
    await fetchBooking()
  } catch {
    // error handled by interceptor
  } finally {
    canceling.value = false
  }
  return true
}

function openSupplementPopup() {
  showSupplementPopup.value = true
}

function seedSupplementFilesFromBooking() {
  const next: Record<string, { id: number; originalName: string; fileSize?: number }[]> = {}
  for (const m of booking.value?.materials || []) {
    const code = m.materialCode || m.material_code
    if (!code) continue
    for (const att of m.attachments || []) {
      if (!att?.id) continue
      next[code] = next[code] || []
      if (!next[code].some(f => f.id === att.id)) {
        next[code].push({
          id: att.id,
          originalName: att.originalName || '附件',
          fileSize: att.fileSize,
        })
      }
    }
  }
  supplementFiles.value = next
}

async function onSupplementPopupOpen() {
  const b = booking.value
  if (!b) return
  const roomId = b.roomId || b.room_id
  const enterpriseType = b.enterpriseType || b.enterprise_type
  if (!roomId || !enterpriseType) {
    showToast('缺少会议室或主体类型信息')
    return
  }
  supplementRulesLoading.value = true
  seedSupplementFilesFromBooking()
  try {
    supplementRules.value = await getMeetingRoomMaterialRules(roomId, { enterpriseType })
    const merged: Record<string, { id: number; originalName: string; fileSize?: number }[]> = {
      ...supplementFiles.value,
    }
    for (const r of supplementRules.value) {
      const code = matCode(r)
      if (code && !merged[code]) merged[code] = []
    }
    supplementFiles.value = merged
  } catch {
    supplementRules.value = []
    showToast('加载材料清单失败')
  } finally {
    supplementRulesLoading.value = false
  }
}

async function handleSupplementUpload(
  materialCode: string,
  items: UploaderFileListItem | UploaderFileListItem[],
) {
  const itemList = Array.isArray(items) ? items : [items]
  for (const item of itemList) {
    if (!item.file) continue
    const sizeErr = validateFileSize(item.file)
    if (sizeErr) { showToast(sizeErr); continue }
    supplementUploading.value = true
    try {
      const result = await uploadAttachment(item.file)
      const prev = supplementFiles.value[materialCode] || []
      supplementFiles.value = {
        ...supplementFiles.value,
        [materialCode]: [
          ...prev,
          { id: result.id, originalName: result.originalName, fileSize: result.fileSize },
        ],
      }
      showToast('上传成功')
    } catch (e: unknown) {
      const err = e as { message?: string }
      showToast(err?.message || '上传失败，请重试')
    } finally {
      supplementUploading.value = false
    }
  }
}

function removeSupplementFile(materialCode: string, id: number) {
  supplementFiles.value = {
    ...supplementFiles.value,
    [materialCode]: (supplementFiles.value[materialCode] || []).filter(f => f.id !== id),
  }
}

async function submitSupplement() {
  if (!supplementRules.value.length) {
    showToast('材料清单加载中，请稍后')
    return
  }
  const missing: string[] = []
  for (const rule of supplementRules.value) {
    const code = matCode(rule)
    if (matRequired(rule) && code && !(supplementFiles.value[code]?.length)) {
      missing.push(matName(rule))
    }
  }
  if (missing.length) {
    showToast(`请上传必传材料：${missing.join('、')}`)
    return
  }

  const materials = supplementRules.value
    .map(rule => {
      const code = matCode(rule)
      const ids = (supplementFiles.value[code] || []).map(f => f.id)
      return {
        materialCode: code,
        materialName: matName(rule),
        attachmentIds: ids,
      }
    })
    .filter(m => m.materialCode && m.attachmentIds.length > 0)

  const allIds = materials.flatMap(m => m.attachmentIds)
  supplementSubmitting.value = true
  try {
    booking.value = await supplementMeetingBooking(bookingId, {
      materials,
      attachmentIds: allIds.length ? allIds : undefined,
      remark: supplementRemark.value.trim() || undefined,
    })
    showSuccessToast('材料已补充，等待后台重新审核')
    showSupplementPopup.value = false
    supplementRemark.value = ''
  } catch {
    // interceptor handles error
  } finally {
    supplementSubmitting.value = false
  }
}

onMounted(fetchBooking)
</script>

<style scoped>
.status-banner--center {
  text-align: center;
  padding: 24px 16px 20px;
}
.audit-alert__title {
  font-weight: 600;
  margin-bottom: 4px;
}
.audit-alert__text {
  font-size: 13px;
  line-height: 1.6;
}
.section-title {
  font-size: 14px;
  font-weight: 600;
  color: #333;
  padding: 8px 16px 4px;
}
.mono { font-family: monospace; font-size: 12px; color: #999; }
.att-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  border-bottom: 1px solid #f5f5f5;
  cursor: pointer;
  &:last-child { border-bottom: none; }
  &:active { background: #f9f9f9; }
}
.att-name { flex: 1; font-size: 13px; color: #333; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.step-action { font-size: 14px; font-weight: 500; color: #333; }
.step-opinion { font-size: 13px; color: #666; margin-top: 4px; }
.step-meta { font-size: 12px; color: #999; margin-top: 4px; }
.bottom-bar--multi {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.supplement-popup {
  padding: 16px 16px 24px;
  height: 100%;
  overflow-y: auto;
  scrollbar-width: none;
  -ms-overflow-style: none;
  -webkit-overflow-scrolling: touch;
  box-sizing: border-box;
}
.supplement-popup::-webkit-scrollbar {
  width: 0;
  height: 0;
  display: none;
}
.supplement-popup__title {
  font-size: 17px;
  font-weight: 600;
  text-align: center;
  margin-bottom: 8px;
}
.supplement-popup__hint {
  font-size: 13px;
  color: #ed6a0c;
  line-height: 1.6;
  margin-bottom: 12px;
  padding: 8px 10px;
  background: #fff7e8;
  border-radius: 6px;
}
.supplement-popup__actions {
  margin-top: 16px;
  padding-bottom: env(safe-area-inset-bottom);
}
.material-block {
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f5f5f5;
}
.material-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}
.material-name { font-size: 14px; font-weight: 500; color: #333; }
.material-desc { font-size: 12px; color: #999; margin-bottom: 8px; }
.file-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 0;
  font-size: 13px;
}
.file-name { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
</style>
