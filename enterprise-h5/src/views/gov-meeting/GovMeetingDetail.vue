<template>
  <div class="page">
    <van-nav-bar
      :title="detail ? String(getTitle(detail) || '约见详情') : '约见详情'"
      left-arrow
      @click-left="router.back()"
      fixed
    />

    <div class="page-body page-body--action" v-if="detail">
      <!-- 状态横幅 -->
      <div
        class="status-banner"
        :style="{ background: statusBannerGradient('govMeeting', detail.status) }"
      >
        <div class="status-banner__text">{{ statusLabel('govMeeting', detail.status) }}</div>
        <div class="status-banner__sub">申请编号：{{ getApplyNo(detail) || '--' }}</div>
      </div>

      <!-- 操作按钮 -->
      <div class="action-bar">
        <van-button
          v-if="detail.status === 'NEED_SUPPLEMENT'"
          type="warning" round size="small" block
          @click="showSupplementPopup = true"
        >
          补充材料
        </van-button>
        <van-button
          v-if="canEvaluate"
          type="primary" round size="small" block
          @click="router.push(`/gov-meetings/${detail.id}/evaluate`)"
        >
          去评价
        </van-button>
      </div>

      <!-- 约见基本信息 -->
      <van-cell-group inset title="约见申请信息" style="margin-top:12px">
        <van-cell title="约见标题" :value="getTitle(detail)" />
        <van-cell title="约见主题" :value="getTopicName(detail)" />
        <van-cell title="紧急程度" :value="urgencyText(getField(detail, 'urgencyLevel', 'urgency_level'))" />
        <van-cell title="期望约见层级" :value="getExpectedLevel(detail) || '--'" />
        <van-cell v-if="getFinalLevel(detail)" title="后台研判层级">
          <template #value>
            <span style="color:#07c160; font-weight:500">{{ getFinalLevel(detail) }}</span>
          </template>
        </van-cell>
        <van-cell title="联系人" :value="getField(detail, 'contactName', 'contact_name') || '--'" />
        <van-cell title="联系电话" :value="getField(detail, 'contactPhone', 'contact_phone') || '--'" />
        <van-cell title="所属区划" :value="getField(detail, 'regionName', 'region_name') || '--'" />
        <van-cell title="提交时间" :value="formatDt(getField(detail, 'submittedAt', 'submitted_at'))" />
        <van-cell v-if="getField(detail, 'acceptedAt', 'accepted_at')" title="受理时间" :value="formatDt(getField(detail, 'acceptedAt', 'accepted_at'))" />
      </van-cell-group>

      <!-- 约见内容 -->
      <div class="content-section" v-if="getContent(detail)">
        <div class="section-label">约见内容</div>
        <div class="content-body">{{ getContent(detail) }}</div>
      </div>

      <!-- 洽谈事项 -->
      <div class="content-section" v-if="getField(detail, 'discussionItem', 'discussion_item')">
        <div class="section-label">洽谈事项</div>
        <div class="content-body">{{ getField(detail, 'discussionItem', 'discussion_item') }}</div>
      </div>

      <!-- 不予受理原因 -->
      <van-cell-group v-if="detail.status === 'REJECTED'" inset title="不予受理信息" style="margin-top:12px">
        <van-cell
          title="不予受理原因"
          :value="getField(detail, 'rejectReasonName', 'reject_reason_name') || '--'"
        />
        <van-cell
          v-if="getField(detail, 'rejectOpinion', 'reject_opinion')"
          title="审核意见"
          :value="getField(detail, 'rejectOpinion', 'reject_opinion')"
          :value-class="'reject-text'"
        />
      </van-cell-group>

      <!-- 审核记录 -->
      <div class="section-title" v-if="auditTrail.length">审核记录</div>
      <div class="timeline-wrap" v-if="auditTrail.length">
        <div v-for="(item, i) in auditTrail" :key="item.id" class="timeline-item">
          <div class="timeline-dot" :class="{ first: i === 0 }"></div>
          <div class="timeline-line" v-if="i < auditTrail.length - 1"></div>
          <div class="timeline-content">
            <div class="tl-action">
              <span class="tl-name">{{ getField(item, 'actionName', 'action_name') }}</span>
              <span class="tl-time">{{ formatDt(getField(item, 'createdAt', 'created_at')) }}</span>
            </div>
            <div class="tl-operator">
              {{ getField(item, 'operatorName', 'operator_name') }}
              {{ getField(item, 'operatorDeptName', 'operator_dept_name') ? `· ${getField(item, 'operatorDeptName', 'operator_dept_name')}` : '' }}
            </div>
            <div class="tl-opinion" v-if="item.opinion">{{ item.opinion }}</div>
          </div>
        </div>
      </div>

      <!-- 约见安排 -->
      <template v-if="arrangement">
        <van-cell-group inset title="约见安排" style="margin-top:12px">
          <van-cell title="约见日期" :value="formatDateOnly(arrMeetingDate)" />
          <van-cell v-if="arrStartTime" title="开始时间" :value="formatDt(arrStartTime)" />
          <van-cell v-if="arrEndTime" title="结束时间" :value="formatDt(arrEndTime)" />
          <van-cell title="约见方式" :value="meetingMethodText(arrMethod)" />
          <van-cell title="约见地点" :value="arrPlace || '--'" />
          <van-cell v-if="arrHostDept" title="主办单位" :value="arrHostDept" />
          <van-cell v-if="arrNotes" title="备注说明" :value="arrNotes" />
        </van-cell-group>

        <!-- 参会人员 -->
        <div class="section-title" v-if="participants.length">参会人员</div>
        <div class="participant-list" v-if="participants.length">
          <div v-for="p in participants" :key="p.id" class="participant-item">
            <div class="participant-header">
              <van-tag :type="pType(p) === 'GOV' ? 'primary' : 'success'" size="medium">
                {{ pType(p) === 'GOV' ? '政府' : '企业' }}
              </van-tag>
              <span class="p-name">{{ pName(p) }}</span>
              <span class="p-title" v-if="pTitle(p)">{{ pTitle(p) }}</span>
            </div>
            <div class="participant-info" v-if="pDept(p) || pPhone(p) || pRole(p)">
              <span v-if="pDept(p)">{{ pDept(p) }}</span>
              <span v-if="pRole(p)" class="p-role">{{ pRole(p) }}</span>
              <span v-if="pPhone(p)" class="p-phone">{{ pPhone(p) }}</span>
            </div>
          </div>
        </div>
      </template>

      <!-- 约见纪要 -->
      <template v-if="records.length">
        <div class="section-title">约见记录</div>
        <div v-for="rec in records" :key="rec.id" class="record-item">
          <div class="record-meta">
            记录时间：{{ formatDt(getField(rec, 'recordTime', 'record_time')) }}
            <span v-if="getField(rec, 'recorderName', 'recorder_name')">
              &nbsp;|&nbsp; 记录人：{{ getField(rec, 'recorderName', 'recorder_name') }}
            </span>
          </div>
          <div class="content-body" style="margin-top:8px">{{ rec.content }}</div>
          <template v-if="rec.conclusions">
            <div class="section-label" style="margin-top:10px; font-size:12px">沟通结论</div>
            <div class="content-body">{{ rec.conclusions }}</div>
          </template>
          <template v-if="getField(rec, 'followUpItems', 'follow_up_items')">
            <div class="section-label" style="margin-top:10px; font-size:12px">后续跟进</div>
            <div class="content-body">{{ getField(rec, 'followUpItems', 'follow_up_items') }}</div>
          </template>
        </div>
      </template>

      <!-- 评价信息 -->
      <van-cell-group v-if="detail.evaluation" inset title="我的评价" style="margin-top:12px">
        <van-cell title="满意度" :value="satisfactionText(detail.evaluation.satisfaction)" />
        <van-cell title="星级评分">
          <template #value>
            <van-rate :model-value="detail.evaluation.score" readonly allow-half size="16" />
          </template>
        </van-cell>
        <van-cell title="是否解决诉求">
          <template #value>
            {{ (detail.evaluation.resolvedFlag ?? detail.evaluation.resolved_flag) === 1 ? '已解决' : '未解决' }}
          </template>
        </van-cell>
        <van-cell v-if="detail.evaluation.comment" title="评价意见" :value="detail.evaluation.comment" />
        <van-cell title="评价时间" :value="formatDt(getField(detail.evaluation, 'createdAt', 'created_at'))" />
      </van-cell-group>

      <div v-else-if="canEvaluate || detail.status === 'PENDING_EVALUATION'" class="eval-tip">
        <van-icon name="star-o" color="#ff976a" size="16" />
        约见完成后可对本次约见服务进行评价
        <van-button
          type="warning" round size="mini"
          style="margin-left:8px"
          @click="router.push(`/gov-meetings/${detail.id}/evaluate`)"
        >去评价</van-button>
      </div>
    </div>

    <div v-else-if="loading" style="padding-top:120px; text-align:center">
      <van-loading type="spinner" />
    </div>

    <!-- 补充材料弹窗 -->
    <van-popup v-model:show="showSupplementPopup" position="bottom" round style="padding:20px 16px 30px">
      <div class="popup-title">补充材料</div>
      <van-field
        v-model="supplementContent"
        type="textarea"
        rows="4"
        placeholder="请填写补充说明内容"
        maxlength="500"
        show-word-limit
      />
      <div style="margin-top:16px">
        <van-button round block type="primary" :loading="supLoading" @click="handleSupplement">
          提交补充
        </van-button>
      </div>
    </van-popup>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onActivated } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showToast, showSuccessToast } from 'vant'
import { getGovMeetingDetail, supplementGovMeeting } from '@/api/govMeeting'
import type { GovMeetingDetail, GovMeetingArrangement, GovMeetingParticipant, GovMeetingAudit, GovMeetingRecord } from '@/api/govMeeting'
import {
  arrMeetingDate as _arrDate, arrStartTime as _arrStart, arrEndTime as _arrEnd,
  arrPlace as _arrPlace, arrMethod as _arrMethod, arrHostDept as _arrHost, arrNotes as _arrNotes,
  pType, pName, pTitle, pDept, pPhone, pRole,
  detailAuditTrail, detailRecords,
} from '@/api/govMeeting'
import { statusLabel, statusBannerGradient } from '@/utils/status'
import { getField, formatDate } from '@/utils/format'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const supLoading = ref(false)
const detail = ref<GovMeetingDetail | null>(null)
const showSupplementPopup = ref(false)
const supplementContent = ref('')

const MEETING_METHOD: Record<string, string> = { ON_SITE: '现场会议', VIDEO: '视频会议', PHONE: '电话沟通' }

function meetingMethodText(m?: string) { return m ? (MEETING_METHOD[m] || m) : '--' }
function urgencyText(code?: string) {
  const m: Record<string,string> = { NORMAL: '普通', URGENT: '紧急', VERY_URGENT: '非常紧急' }
  return code ? (m[code] ?? code) : '--'
}
function satisfactionText(code: string) {
  return statusLabel('satisfaction', code)
}

function getApplyNo(a: GovMeetingDetail): string {
  return getField<string>(a, 'applyNo', 'apply_no') || ''
}
function getTitle(a: GovMeetingDetail): string {
  return getField<string>(a, 'title') || getField<string>(a, 'topicName', 'topic_name') || ''
}
function getTopicName(a: GovMeetingDetail): string {
  return getField<string>(a, 'topicName', 'topic_name') || '--'
}
function getExpectedLevel(a: GovMeetingDetail): string {
  return getField<string>(a, 'expectedLevelName', 'expected_level_name')
    || getField<string>(a, 'meetingLevel', 'meeting_level') || ''
}
function getFinalLevel(a: GovMeetingDetail): string {
  return getField<string>(a, 'finalLevelName', 'final_level_name') || ''
}
function getContent(a: GovMeetingDetail): string {
  return getField<string>(a, 'content', 'meeting_content') || getField<string>(a, 'description') || ''
}

const formatDt = formatDate
function formatDateOnly(dt?: string): string {
  if (!dt) return '--'
  const s = formatDate(dt)
  return s.length >= 10 ? s.slice(0, 10) : s
}

const canEvaluate = computed(() =>
  detail.value &&
  ['PENDING_EVALUATION', 'MEETING_COMPLETED'].includes(detail.value.status) &&
  !detail.value.evaluation
)

const arrangement = computed<GovMeetingArrangement | null>(() => detail.value?.arrangement || null)
const auditTrail = computed<GovMeetingAudit[]>(() => detail.value ? detailAuditTrail(detail.value) : [])
const records = computed<GovMeetingRecord[]>(() => detail.value ? detailRecords(detail.value) : [])
const participants = computed<GovMeetingParticipant[]>(() => arrangement.value?.participants || [])

const arrMeetingDate = computed(() => arrangement.value ? _arrDate(arrangement.value) : '')
const arrStartTime = computed(() => arrangement.value ? _arrStart(arrangement.value) : '')
const arrEndTime = computed(() => arrangement.value ? _arrEnd(arrangement.value) : '')
const arrPlace = computed(() => arrangement.value ? _arrPlace(arrangement.value) : '')
const arrMethod = computed(() => arrangement.value ? _arrMethod(arrangement.value) : '')
const arrHostDept = computed(() => arrangement.value ? _arrHost(arrangement.value) : '')
const arrNotes = computed(() => arrangement.value ? _arrNotes(arrangement.value) : '')

async function fetchDetail() {
  loading.value = true
  try {
    detail.value = await getGovMeetingDetail(Number(route.params.id))
  } catch {
    detail.value = null
  } finally {
    loading.value = false
  }
}

onMounted(fetchDetail)
onActivated(fetchDetail)

async function handleSupplement() {
  if (!supplementContent.value.trim()) { showToast('请填写补充说明'); return }
  supLoading.value = true
  try {
    await supplementGovMeeting(Number(route.params.id), { content: supplementContent.value })
    showSuccessToast('补充材料已提交')
    showSupplementPopup.value = false
    supplementContent.value = ''
    fetchDetail()
  } finally {
    supLoading.value = false
  }
}
</script>

<style scoped>
.status-banner {
  padding: 16px 20px;
  color: #fff;
  .status-text { font-size: 18px; font-weight: 700; margin-bottom: 4px; }
  .status-sub { font-size: 12px; opacity: 0.85; }
}
.action-bar { padding: 10px 12px 0; display: flex; flex-direction: column; gap: 8px; }
.content-section {
  background: #fff;
  margin: 12px;
  border-radius: 10px;
  padding: 14px;
  box-shadow: 0 1px 6px rgba(0,0,0,0.06);
}
.section-label { font-size: 13px; font-weight: 600; color: #666; margin-bottom: 8px; }
.content-body {
  font-size: 13px;
  color: #555;
  line-height: 1.8;
  white-space: pre-wrap;
  background: #f7f8fa;
  border-radius: 6px;
  padding: 10px 12px;
}
.section-title {
  padding: 14px 16px 8px;
  font-size: 14px;
  font-weight: 600;
  color: #666;
}
.timeline-wrap {
  margin: 0 12px 12px;
  background: #fff;
  border-radius: 10px;
  padding: 16px;
  box-shadow: 0 1px 6px rgba(0,0,0,0.06);
}
.timeline-item {
  display: flex;
  gap: 12px;
  position: relative;
  padding-bottom: 16px;
  &:last-child { padding-bottom: 0; }
}
.timeline-dot {
  width: 10px; height: 10px;
  border-radius: 50%; background: #ccc;
  flex-shrink: 0; margin-top: 4px;
  &.first { background: #1989fa; }
}
.timeline-line {
  position: absolute; left: 4px; top: 14px;
  width: 2px; height: calc(100% - 10px); background: #eee;
}
.timeline-content { flex: 1; }
.tl-action { display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; }
.tl-name { font-size: 14px; font-weight: 500; color: #333; }
.tl-time { font-size: 11px; color: #aaa; }
.tl-operator { font-size: 12px; color: #888; margin-bottom: 4px; }
.tl-opinion { font-size: 13px; color: #555; background: #f5f5f5; border-radius: 4px; padding: 6px 8px; }
.participant-list { margin: 0 12px 12px; display: flex; flex-direction: column; gap: 8px; }
.participant-item {
  background: #fff;
  border-radius: 8px;
  padding: 12px 14px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
.participant-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}
.p-name { font-size: 14px; font-weight: 500; color: #333; }
.p-title { font-size: 12px; color: #888; }
.participant-info {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  font-size: 12px;
  color: #777;
}
.p-role { color: #1989fa; }
.p-phone { color: #07c160; }
.record-item {
  background: #fff; margin: 0 12px 8px; border-radius: 10px;
  padding: 14px; box-shadow: 0 1px 6px rgba(0,0,0,0.06);
}
.record-meta { font-size: 12px; color: #999; margin-bottom: 8px; }
.eval-tip {
  display: flex;
  align-items: center;
  gap: 6px;
  background: #fff7e6;
  margin: 12px;
  border-radius: 8px;
  padding: 12px 14px;
  font-size: 13px;
  color: #c77b2a;
}
.popup-title {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin-bottom: 16px;
}
:deep(.reject-text) { color: #ee0a24; }
</style>
