<template>
  <div class="page">
    <van-nav-bar :title="detail?.title || '诉求详情'" left-arrow @click-left="router.back()" fixed />

    <div class="page-body" v-if="detail">
      <div
        class="status-banner"
        :style="{ background: statusBannerGradient('appeal', detail.status) }"
      >
        <div class="status-banner__text">{{ statusLabel('appeal', detail.status) }}</div>
        <div class="status-banner__sub">诉求编号：{{ detail.appealNo || '--' }}</div>
      </div>

      <div class="action-inline" v-if="canEvaluate">
        <van-button type="primary" round block @click="router.push(`/appeals/${detail.id}/evaluate`)">
          去评价
        </van-button>
      </div>

      <van-notice-bar
        v-if="detail.status === 'NEED_SUPPLEMENT'"
        left-icon="info-o"
        color="#ed6a0c"
        background="#fff7e8"
        :scrollable="false"
        wrapable
        style="margin-top:12px"
      >
        退回补充原因：{{ returnSupplementOpinion || '暂无说明' }}
      </van-notice-bar>

      <!-- 补充材料 -->
      <van-cell-group
        v-if="detail.status === 'NEED_SUPPLEMENT'"
        inset title="补充材料" style="margin-top:12px"
      >
        <van-field
          v-model="supplementContent"
          type="textarea"
          rows="3"
          maxlength="500"
          show-word-limit
          placeholder="请输入补充说明（必填）"
        />
        <div class="supplement-files">
          <div v-for="f in supplementFiles" :key="f.id" class="file-item">
            <van-icon name="description" color="#1989fa" size="18" />
            <span class="file-name">{{ f.originalName }}</span>
            <van-icon name="cross" @click="removeSupplementFile(f.id)" />
          </div>
          <van-uploader
            :after-read="handleSupplementUpload"
            accept=".jpg,.jpeg,.png,.pdf,.doc,.docx"
            :max-size="10 * 1024 * 1024"
            @oversize="showToast('单个文件不能超过10MB')"
            :disabled="supplementUploading"
          >
            <van-button icon="plus" size="small" plain type="primary" :loading="supplementUploading">
              上传附件（选填）
            </van-button>
          </van-uploader>
        </div>
        <div style="padding:12px 16px">
          <van-button
            type="primary" round block
            :loading="supplementSubmitting"
            @click="submitSupplement"
          >提交补充</van-button>
        </div>
      </van-cell-group>

      <van-cell-group inset title="诉求信息" class="content-block" style="margin-top:12px">
        <van-cell title="诉求标题" :value="detail.title" />
        <van-cell title="诉求类型" :value="detail.appealTypeName || '--'" />
        <van-cell title="紧急程度" :value="urgencyText(detail.urgencyLevel)" />
        <van-cell title="所属区划" :value="detail.regionName" />
        <van-cell title="联系人" :value="detail.contactName" />
        <van-cell title="联系电话" :value="detail.contactPhone" />
        <van-cell title="提交时间" :value="formatDate(detail.submittedAt)" />
        <van-cell title="受理时间" :value="formatDate(detail.acceptedAt)" />
        <van-cell v-if="detail.replyDeadline" title="答复截止" :value="formatDate(detail.replyDeadline)" />
      </van-cell-group>

      <!-- 诉求内容 -->
      <van-cell-group inset title="诉求内容" style="margin-top:12px">
        <div class="content-text">{{ detail.content }}</div>
      </van-cell-group>

      <!-- 办理回复（已回复时展示） -->
      <van-cell-group inset title="办理回复" style="margin-top:12px"
        v-if="replyRecord">
        <div class="content-text reply">{{ replyRecord.opinion }}</div>
        <van-cell title="回复时间" :value="formatDate(replyRecord.createdAt)" />
      </van-cell-group>

      <!-- 评价信息 -->
      <van-cell-group inset title="我的评价" style="margin-top:12px" v-if="detail.evaluation">
        <van-cell title="满意度" :value="satisfactionText(detail.evaluation.satisfaction)" />
        <van-cell title="星级评分">
          <template #value>
            <van-rate :model-value="detail.evaluation.score" readonly allow-half size="16" />
          </template>
        </van-cell>
        <van-cell title="是否解决" :value="detail.evaluation.resolvedFlag === 1 ? '已解决' : '未解决'" />
        <van-cell v-if="detail.evaluation.comment" title="评价意见" :value="detail.evaluation.comment" />
        <van-cell title="评价时间" :value="formatDate(detail.evaluation.evaluateTime)" />
      </van-cell-group>

      <!-- 办理时间线 -->
      <div class="section-title" v-if="detail.records.length">办理记录</div>
      <div class="timeline-wrap" v-if="detail.records.length">
        <div v-for="(rec, i) in detail.records" :key="rec.id" class="timeline-item">
          <div class="timeline-dot" :class="{ first: i === 0 }"></div>
          <div class="timeline-line" v-if="i < detail.records.length - 1"></div>
          <div class="timeline-content">
            <div class="tl-action">
              <span class="tl-name">{{ rec.actionName }}</span>
              <span class="tl-time">{{ formatDate(rec.createdAt) }}</span>
            </div>
            <div class="tl-operator">{{ rec.operatorName }}{{ rec.operatorDeptName ? ` · ${rec.operatorDeptName}` : '' }}</div>
            <div class="tl-opinion" v-if="rec.opinion">{{ rec.opinion }}</div>
          </div>
        </div>
      </div>
    </div>

    <div v-else-if="loading" class="page-body" style="padding-top:120px;text-align:center">
      <van-loading type="spinner" color="var(--esc-primary)" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onActivated } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showToast } from 'vant'
import type { UploaderFileListItem } from 'vant'
import { getAppealDetail, supplementAppeal } from '@/api/appeal'
import type { AppealDetail as Detail, AppealRecord } from '@/api/appeal'
import { uploadAttachment } from '@/api/common'
import { validateFileSize } from '@/constants/upload'
import { formatDate } from '@/utils/format'
import { statusLabel, statusBannerGradient } from '@/utils/status'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const detail = ref<Detail | null>(null)

const EVALUABLE_STATUSES = ['REPLIED', 'PENDING_EVALUATION']
const canEvaluate = computed(() =>
  detail.value ? EVALUABLE_STATUSES.includes(detail.value.status) && !detail.value.evaluation : false
)

const replyRecord = computed<AppealRecord | undefined>(() =>
  detail.value?.records.find(r => ['CENTER_HANDLE', 'REVIEW_PASS'].includes(r.actionType))
)

const returnSupplementOpinion = computed(() => {
  const records = detail.value?.records || []
  for (let i = records.length - 1; i >= 0; i--) {
    if (records[i].actionType === 'RETURN_SUPPLEMENT') return records[i].opinion
  }
  return null
})

const supplementContent = ref('')
const supplementFiles = ref<{ id: number; originalName: string; fileSize: number }[]>([])
const supplementUploading = ref(false)
const supplementSubmitting = ref(false)

async function handleSupplementUpload(items: UploaderFileListItem | UploaderFileListItem[]) {
  const itemList = Array.isArray(items) ? items : [items]
  for (const item of itemList) {
    if (!item.file) continue
    const sizeErr = validateFileSize(item.file)
    if (sizeErr) { showToast(sizeErr); continue }
    supplementUploading.value = true
    try {
      const result = await uploadAttachment(item.file)
      supplementFiles.value = [
        ...supplementFiles.value,
        { id: result.id, originalName: result.originalName, fileSize: result.fileSize },
      ]
      showToast('上传成功')
    } catch (e: unknown) {
      const err = e as { message?: string }
      showToast(err?.message || '上传失败，请重试')
    } finally {
      supplementUploading.value = false
    }
  }
}

function removeSupplementFile(id: number) {
  supplementFiles.value = supplementFiles.value.filter(f => f.id !== id)
}

async function submitSupplement() {
  if (!supplementContent.value.trim()) {
    showToast('请输入补充说明')
    return
  }
  supplementSubmitting.value = true
  try {
    await supplementAppeal(Number(route.params.id), {
      content: supplementContent.value.trim(),
      attachmentIds: supplementFiles.value.map(f => f.id),
    })
    showToast({ type: 'success', message: '提交成功' })
    supplementContent.value = ''
    supplementFiles.value = []
    await loadDetail()
  } catch (e: unknown) {
    const err = e as { message?: string }
    showToast(err?.message || '提交失败，请重试')
  } finally {
    supplementSubmitting.value = false
  }
}

function urgencyText(code?: string | null) {
  const m: Record<string,string> = { NORMAL: '普通', URGENT: '紧急', VERY_URGENT: '非常紧急' }
  return code ? (m[code] ?? code) : '--'
}

function satisfactionText(code: string) {
  return statusLabel('satisfaction', code)
}

async function loadDetail() {
  loading.value = true
  try {
    detail.value = await getAppealDetail(Number(route.params.id))
  } finally {
    loading.value = false
  }
}

onMounted(loadDetail)
onActivated(loadDetail)
</script>

<style scoped>
.content-text.reply {
  background: var(--esc-bg);
  border-radius: var(--esc-radius-sm);
  margin: 8px;
}
.supplement-files {
  padding: 8px 16px;
}
.file-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 0;
  font-size: 13px;
}
.file-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
