<template>
  <div class="appeal-detail">
    <!-- 顶部 -->
    <div class="detail-topbar">
      <el-button @click="router.back()"><el-icon><ArrowLeft /></el-icon> 返回</el-button>
      <div class="detail-title" v-if="detail">
        <span class="title-text">{{ detail.title }}</span>
        <el-tag :type="appealTagType(detail.status)" style="margin-left:12px">
          {{ appealStatusText(detail.status) }}
        </el-tag>
        <el-tag v-if="detail.urgencyLevel" :type="urgencyTagType(detail.urgencyLevel)" style="margin-left:8px">
          {{ urgencyText(detail.urgencyLevel) }}
        </el-tag>
      </div>
    </div>

    <div v-loading="loading" style="min-height:200px">
      <template v-if="detail">

        <!-- 操作按钮区 -->
        <el-card shadow="never" class="section-card" v-if="actions.length">
          <template #header><span class="section-title">办理操作</span></template>
          <div class="action-buttons">
            <el-button
              v-if="actions.includes('accept')" v-permission="Permission.APPEAL_HANDLE"
              type="primary" @click="openDialog('accept')">受理</el-button>
            <el-button
              v-if="actions.includes('returnSupplement')" v-permission="Permission.APPEAL_HANDLE"
              type="warning" @click="openDialog('returnSupplement')">退回补充</el-button>
            <el-button
              v-if="actions.includes('reject')" v-permission="Permission.APPEAL_HANDLE"
              type="danger" @click="openDialog('reject')">不予受理</el-button>
            <el-button
              v-if="actions.includes('centerHandle')" v-permission="Permission.APPEAL_HANDLE"
              type="success" @click="openDialog('centerHandle')">企服中心自行办理</el-button>
            <el-button
              v-if="actions.includes('assign')" v-permission="Permission.APPEAL_HANDLE"
              type="primary" plain @click="openDialog('assign')">分派责任部门</el-button>
            <el-button
              v-if="actions.includes('deptReply')" v-permission="[Permission.APPEAL_HANDLE, Permission.APPEAL_DEPT_REPLY]"
              type="success" plain @click="openDialog('deptReply')">部门反馈</el-button>
            <el-button
              v-if="actions.includes('reviewReply')" v-permission="Permission.APPEAL_HANDLE"
              type="primary" @click="openDialog('reviewReply')">审核部门反馈</el-button>
            <el-button
              v-if="actions.includes('followup')" v-permission="Permission.APPEAL_HANDLE"
              type="info" @click="openDialog('followup')">记录回访</el-button>
            <el-button
              v-if="actions.includes('complete')" v-permission="Permission.APPEAL_HANDLE"
              type="success" @click="openDialog('complete')">办结</el-button>
          </div>
        </el-card>

        <!-- 企业信息 -->
        <el-card shadow="never" class="section-card">
          <template #header><span class="section-title">企业信息</span></template>
          <el-descriptions :column="3" border size="small">
            <el-descriptions-item label="企业名称">{{ detail.enterpriseName }}</el-descriptions-item>
            <el-descriptions-item label="统一社会信用代码">{{ detail.creditCode }}</el-descriptions-item>
            <el-descriptions-item label="联系人">{{ detail.contactName }}</el-descriptions-item>
            <el-descriptions-item label="联系电话">{{ detail.contactPhone }}</el-descriptions-item>
            <el-descriptions-item label="所属行业">{{ detail.industryName || '--' }}</el-descriptions-item>
            <el-descriptions-item label="所属区划">{{ detail.regionName }}（{{ detail.regionCode }}）</el-descriptions-item>
          </el-descriptions>
        </el-card>

        <!-- 诉求信息 -->
        <el-card shadow="never" class="section-card">
          <template #header><span class="section-title">诉求信息</span></template>
          <el-descriptions :column="3" border size="small">
            <el-descriptions-item label="诉求编号">{{ detail.appealNo }}</el-descriptions-item>
            <el-descriptions-item label="诉求类型">{{ detail.appealTypeName || '--' }}</el-descriptions-item>
            <el-descriptions-item label="紧急程度">
              <el-tag v-if="detail.urgencyLevel" :type="urgencyTagType(detail.urgencyLevel)" size="small">
                {{ urgencyText(detail.urgencyLevel) }}
              </el-tag>
              <span v-else>--</span>
            </el-descriptions-item>
            <el-descriptions-item label="当前状态">
              <el-tag :type="appealTagType(detail.status)" size="small">{{ appealStatusText(detail.status) }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="办理方式">{{ handleModeText(detail.handleMode) }}</el-descriptions-item>
            <el-descriptions-item label="责任单位">{{ detail.responsibleDeptName || '--' }}</el-descriptions-item>
            <el-descriptions-item label="提交时间">{{ formatDate(detail.submittedAt) }}</el-descriptions-item>
            <el-descriptions-item label="受理时间">{{ formatDate(detail.acceptedAt) }}</el-descriptions-item>
            <el-descriptions-item label="答复截止时间">{{ formatDate(detail.replyDeadline) }}</el-descriptions-item>
            <el-descriptions-item label="回复时间">{{ formatDate(detail.repliedAt) }}</el-descriptions-item>
            <el-descriptions-item label="评价时间">{{ formatDate(detail.evaluatedAt) }}</el-descriptions-item>
            <el-descriptions-item label="办结时间">{{ formatDate(detail.completedAt) }}</el-descriptions-item>
            <el-descriptions-item label="诉求内容" :span="3">
              <div class="content-text">{{ detail.content }}</div>
            </el-descriptions-item>
          </el-descriptions>
        </el-card>

        <!-- 附件列表 -->
        <el-card shadow="never" class="section-card" v-if="detail.attachments.length">
          <template #header><span class="section-title">附件列表</span></template>
          <el-table :data="detail.attachments" size="small">
            <el-table-column prop="originalName" label="文件名" min-width="200" />
            <el-table-column prop="fileExt" label="类型" width="80" />
            <el-table-column prop="fileSize" label="大小" width="100">
              <template #default="{ row }">{{ formatFileSize(row.fileSize) }}</template>
            </el-table-column>
            <el-table-column label="操作" width="80">
              <template #default="{ row }">
                <el-button link type="primary" @click="downloadAttachment(row.id)">下载</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>

        <!-- 办理记录时间线 -->
        <el-card shadow="never" class="section-card" v-if="detail.records.length">
          <template #header><span class="section-title">办理记录</span></template>
          <el-timeline>
            <el-timeline-item
              v-for="rec in detail.records"
              :key="rec.id"
              :timestamp="formatDate(rec.createdAt)"
              placement="top"
            >
              <div class="record-item">
                <div class="record-header">
                  <el-tag size="small" type="primary">{{ rec.actionName }}</el-tag>
                  <span class="record-operator">{{ rec.operatorName }}</span>
                  <span class="record-dept" v-if="rec.operatorDeptName">{{ rec.operatorDeptName }}</span>
                  <span class="record-status" v-if="rec.afterStatus">
                    → <el-tag size="small" :type="appealTagType(rec.afterStatus)">{{ appealStatusText(rec.afterStatus) }}</el-tag>
                  </span>
                </div>
                <div class="record-opinion" v-if="rec.opinion">{{ rec.opinion }}</div>
              </div>
            </el-timeline-item>
          </el-timeline>
        </el-card>

        <!-- 分派记录 -->
        <el-card shadow="never" class="section-card" v-if="detail.assignments.length">
          <template #header><span class="section-title">分派记录</span></template>
          <el-table :data="detail.assignments" size="small" border>
            <el-table-column prop="assignedDeptName" label="责任部门" width="150" />
            <el-table-column prop="assignedAt" label="分派时间" width="155">
              <template #default="{ row }">{{ formatDate(row.assignedAt) }}</template>
            </el-table-column>
            <el-table-column prop="deadline" label="办理期限" width="155">
              <template #default="{ row }">{{ formatDate(row.deadline) }}</template>
            </el-table-column>
            <el-table-column prop="assignOpinion" label="分派意见" min-width="150" show-overflow-tooltip />
            <el-table-column prop="replyContent" label="部门反馈" min-width="180" show-overflow-tooltip>
              <template #default="{ row }">{{ row.replyContent || '--' }}</template>
            </el-table-column>
            <el-table-column prop="repliedAt" label="反馈时间" width="155">
              <template #default="{ row }">{{ formatDate(row.repliedAt) }}</template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="90">
              <template #default="{ row }">{{ ASSIGNMENT_STATUS_MAP[row.status] ?? row.status }}</template>
            </el-table-column>
          </el-table>
        </el-card>

        <!-- 评价信息 -->
        <el-card shadow="never" class="section-card" v-if="detail.evaluation">
          <template #header><span class="section-title">企业评价</span></template>
          <el-descriptions :column="3" border size="small">
            <el-descriptions-item label="满意度">
              <el-tag :type="satisfactionTag(detail.evaluation.satisfaction)">
                {{ formatSatisfaction(detail.evaluation.satisfaction) }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="星级评分">
              <el-rate :model-value="detail.evaluation.score" disabled />
            </el-descriptions-item>
            <el-descriptions-item label="主要诉求是否解决">
              {{ formatResolvedFlag(detail.evaluation.resolvedFlag) }}
            </el-descriptions-item>
            <el-descriptions-item label="评价时间">{{ formatDate(detail.evaluation.evaluateTime) }}</el-descriptions-item>
            <el-descriptions-item label="评价意见" :span="2">{{ detail.evaluation.comment || '--' }}</el-descriptions-item>
          </el-descriptions>
        </el-card>

        <!-- 回访记录 -->
        <el-card shadow="never" class="section-card" v-if="detail.followups.length">
          <template #header><span class="section-title">回访记录</span></template>
          <el-table :data="detail.followups" size="small" border>
            <el-table-column prop="followupStatus" label="回访状态" width="90">
              <template #default="{ row }">{{ FOLLOWUP_STATUS_MAP[row.followupStatus] ?? row.followupStatus }}</template>
            </el-table-column>
            <el-table-column prop="followupMethod" label="回访方式" width="100">
              <template #default="{ row }">{{ followupMethodText(row.followupMethod) }}</template>
            </el-table-column>
            <el-table-column prop="followupContent" label="回访内容" min-width="150" show-overflow-tooltip />
            <el-table-column prop="followupResult" label="回访结果" min-width="150" show-overflow-tooltip />
            <el-table-column prop="followupUserName" label="回访人" width="100" />
            <el-table-column prop="followupTime" label="回访时间" width="155">
              <template #default="{ row }">{{ formatDate(row.followupTime) }}</template>
            </el-table-column>
          </el-table>
        </el-card>

      </template>
    </div>

    <!-- ===== 操作弹窗：受理 ===== -->
    <el-dialog v-model="dialogs.accept" title="受理诉求" width="500px" :close-on-click-modal="false">
      <el-form :model="acceptForm" :rules="acceptRules" ref="acceptRef" label-width="110px">
        <el-form-item label="诉求类型" prop="appealTypeCode">
          <el-select v-model="acceptForm.appealTypeCode" placeholder="请选择" style="width:100%"
            @change="onAppealTypeChange">
            <el-option v-for="t in appealTypeOptions" :key="t.value" :label="t.label" :value="t.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="答复截止时间" prop="replyDeadline">
          <el-date-picker v-model="acceptForm.replyDeadline" type="datetime"
            placeholder="请选择" value-format="YYYY-MM-DDTHH:mm:ss" style="width:100%" />
        </el-form-item>
        <el-form-item label="受理意见" prop="opinion">
          <el-input v-model="acceptForm.opinion" type="textarea" :rows="3" placeholder="请输入受理意见" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogs.accept = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitAccept">确认受理</el-button>
      </template>
    </el-dialog>

    <!-- ===== 退回补充 ===== -->
    <el-dialog v-model="dialogs.returnSupplement" title="退回补充" width="480px" :close-on-click-modal="false">
      <el-form :model="returnForm" :rules="returnRules" ref="returnRef" label-width="90px">
        <el-form-item label="退回意见" prop="opinion">
          <el-input v-model="returnForm.opinion" type="textarea" :rows="4" placeholder="请说明退回原因和需补充内容" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogs.returnSupplement = false">取消</el-button>
        <el-button type="warning" :loading="submitting" @click="submitReturn">确认退回</el-button>
      </template>
    </el-dialog>

    <!-- ===== 不予受理 ===== -->
    <el-dialog v-model="dialogs.reject" title="不予受理" width="480px" :close-on-click-modal="false">
      <el-form :model="rejectForm" :rules="rejectRules" ref="rejectRef" label-width="100px">
        <el-form-item label="不予受理原因" prop="reasonCode">
          <el-select v-model="rejectForm.reasonCode" placeholder="请选择" style="width:100%"
            @change="onRejectReasonChange">
            <el-option v-for="r in rejectReasonOptions" :key="r.value" :label="r.label" :value="r.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="处理意见" prop="opinion">
          <el-input v-model="rejectForm.opinion" type="textarea" :rows="3" placeholder="请输入处理意见" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogs.reject = false">取消</el-button>
        <el-button type="danger" :loading="submitting" @click="submitReject">确认不予受理</el-button>
      </template>
    </el-dialog>

    <!-- ===== 企服中心自行办理 ===== -->
    <el-dialog v-model="dialogs.centerHandle" title="企服中心自行办理" width="520px" :close-on-click-modal="false">
      <el-form :model="centerHandleForm" :rules="centerHandleRules" ref="centerHandleRef" label-width="90px">
        <el-form-item label="办理回复" prop="replyContent">
          <el-input v-model="centerHandleForm.replyContent" type="textarea" :rows="5" placeholder="请输入办理回复内容" />
        </el-form-item>
        <el-form-item label="附件">
          <div class="attachment-uploader">
            <div v-for="f in centerHandleAttachments" :key="f.id" class="attachment-uploader__item">
              <span>{{ f.originalName }}</span>
              <el-icon @click="centerHandleAttachments = centerHandleAttachments.filter(x => x.id !== f.id)"><Close /></el-icon>
            </div>
            <el-upload
              :show-file-list="false"
              :before-upload="(f: File) => handleDialogUpload(f, 'centerHandle')"
              accept=".doc,.docx,.pdf,.jpg,.jpeg,.png"
              :disabled="centerHandleUploading"
            >
              <el-button size="small" :loading="centerHandleUploading">上传附件（选填）</el-button>
            </el-upload>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogs.centerHandle = false">取消</el-button>
        <el-button type="success" :loading="submitting" @click="submitCenterHandle">提交办理</el-button>
      </template>
    </el-dialog>

    <!-- ===== 分派责任部门 ===== -->
    <el-dialog v-model="dialogs.assign" title="分派责任部门" width="520px" :close-on-click-modal="false">
      <el-form :model="assignForm" :rules="assignRules" ref="assignRef" label-width="110px">
        <el-form-item label="责任部门ID" prop="assignedDeptId">
          <el-input v-model="assignForm.assignedDeptId" placeholder="如 dept_econ_001" />
        </el-form-item>
        <el-form-item label="责任部门名称" prop="assignedDeptName">
          <el-input v-model="assignForm.assignedDeptName" placeholder="如 经济发展局" />
        </el-form-item>
        <el-form-item label="办理截止时间" prop="deadline">
          <el-date-picker v-model="assignForm.deadline" type="datetime"
            placeholder="请选择" value-format="YYYY-MM-DDTHH:mm:ss" style="width:100%" />
        </el-form-item>
        <el-form-item label="分派意见">
          <el-input v-model="assignForm.assignOpinion" type="textarea" :rows="3" placeholder="请输入分派说明" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogs.assign = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitAssign">确认分派</el-button>
      </template>
    </el-dialog>

    <!-- ===== 部门反馈 ===== -->
    <el-dialog v-model="dialogs.deptReply" title="部门反馈" width="520px" :close-on-click-modal="false">
      <el-form :model="deptReplyForm" :rules="deptReplyRules" ref="deptReplyRef" label-width="90px">
        <el-form-item label="办理意见" prop="replyContent">
          <el-input v-model="deptReplyForm.replyContent" type="textarea" :rows="5" placeholder="请输入部门办理意见" />
        </el-form-item>
        <el-form-item label="附件">
          <div class="attachment-uploader">
            <div v-for="f in deptReplyAttachments" :key="f.id" class="attachment-uploader__item">
              <span>{{ f.originalName }}</span>
              <el-icon @click="deptReplyAttachments = deptReplyAttachments.filter(x => x.id !== f.id)"><Close /></el-icon>
            </div>
            <el-upload
              :show-file-list="false"
              :before-upload="(f: File) => handleDialogUpload(f, 'deptReply')"
              accept=".doc,.docx,.pdf,.jpg,.jpeg,.png"
              :disabled="deptReplyUploading"
            >
              <el-button size="small" :loading="deptReplyUploading">上传附件（选填）</el-button>
            </el-upload>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogs.deptReply = false">取消</el-button>
        <el-button type="success" :loading="submitting" @click="submitDeptReply">提交反馈</el-button>
      </template>
    </el-dialog>

    <!-- ===== 审核部门反馈 ===== -->
    <el-dialog v-model="dialogs.reviewReply" title="审核部门反馈" width="480px" :close-on-click-modal="false">
      <el-form :model="reviewForm" :rules="reviewRules" ref="reviewRef" label-width="90px">
        <el-form-item label="审核结果" prop="pass">
          <el-radio-group v-model="reviewForm.pass">
            <el-radio :value="true">审核通过</el-radio>
            <el-radio :value="false">审核退回</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="审核意见" prop="opinion">
          <el-input v-model="reviewForm.opinion" type="textarea" :rows="3" placeholder="请输入审核意见" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogs.reviewReply = false">取消</el-button>
        <el-button :type="reviewForm.pass ? 'success' : 'warning'" :loading="submitting" @click="submitReview">
          {{ reviewForm.pass ? '通过' : '退回' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- ===== 记录回访 ===== -->
    <el-dialog v-model="dialogs.followup" title="记录回访" width="520px" :close-on-click-modal="false">
      <el-form :model="followupForm" :rules="followupRules" ref="followupRef" label-width="100px">
        <el-form-item label="责任单位ID">
          <el-input v-model="followupForm.responsibleDeptId" placeholder="可选" />
        </el-form-item>
        <el-form-item label="责任单位名称">
          <el-input v-model="followupForm.responsibleDeptName" placeholder="可选" />
        </el-form-item>
        <el-form-item label="回访方式" prop="followupMethod">
          <el-select v-model="followupForm.followupMethod" placeholder="请选择" style="width:100%">
            <el-option v-for="m in followupMethodOptions" :key="m.value" :label="m.label" :value="m.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="回访内容" prop="followupContent">
          <el-input v-model="followupForm.followupContent" type="textarea" :rows="3" placeholder="请输入回访内容" />
        </el-form-item>
        <el-form-item label="回访结果" prop="followupResult">
          <el-input v-model="followupForm.followupResult" type="textarea" :rows="2" placeholder="请输入回访结果" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogs.followup = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitFollowup">提交记录</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="dialogs.complete" title="办结" width="480px" :close-on-click-modal="false">
      <el-form label-width="80px">
        <el-form-item label="备注">
          <el-input v-model="completeForm.remark" type="textarea" :rows="3" placeholder="可选" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogs.complete = false">取消</el-button>
        <el-button type="success" :loading="submitting" @click="submitComplete">确认办结</el-button>
      </template>
    </el-dialog>

  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import type { FormInstance } from 'element-plus'
import {
  getAppealDetail, acceptAppeal, returnSupplementAppeal, rejectAppeal,
  centerHandleAppeal, assignAppeal, departmentReplyAppeal, reviewReplyAppeal, addAppealFollowup,
  completeAppeal,
} from '@/api/appeal'
import type { AppealDetail } from '@/api/appeal'
import { formatDate } from '@/utils/format'
import {
  APPEAL_TYPE_OPTIONS, REJECT_REASON_OPTIONS, FOLLOWUP_METHOD_OPTIONS,
  ASSIGNMENT_STATUS_MAP, SATISFACTION_MAP, FOLLOWUP_STATUS_MAP,
  appealStatusText, appealTagType, urgencyText, urgencyTagType, availableActions,
  formatSatisfaction, formatResolvedFlag,
} from '@/utils/appealConsts'
import { getDictionary, dictToMap, uploadAttachment } from '@/api/common'
import { Close } from '@element-plus/icons-vue'
import { Permission } from '@/constants/permission'
import { openSecureAttachment } from '@/utils/attachment'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const submitting = ref(false)
const detail = ref<AppealDetail | null>(null)

const appealId = computed(() => Number(route.params.id))
const actions = computed(() => detail.value ? availableActions(detail.value.status) : [])

// ── 弹窗状态 ──────────────────────────────────────────────────────────────────
type DialogKey = 'accept' | 'returnSupplement' | 'reject' | 'centerHandle' | 'assign' | 'deptReply' | 'reviewReply' | 'followup' | 'complete'
const dialogs = ref<Record<DialogKey, boolean>>({
  accept: false, returnSupplement: false, reject: false,
  centerHandle: false, assign: false, deptReply: false,
  reviewReply: false, followup: false, complete: false
})

// ── 表单数据 ──────────────────────────────────────────────────────────────────
const acceptForm = ref({ appealTypeCode: '', appealTypeName: '', replyDeadline: '', opinion: '' })
const returnForm = ref({ opinion: '' })
const rejectForm = ref({ reasonCode: '', reasonName: '', opinion: '' })
const centerHandleForm = ref({ replyContent: '' })
const assignForm = ref({ assignedDeptId: '', assignedDeptName: '', deadline: '', assignOpinion: '' })
const deptReplyForm = ref({ replyContent: '' })
const reviewForm = ref({ pass: true, opinion: '' })
const followupForm = ref({ responsibleDeptId: '', responsibleDeptName: '', followupMethod: '', followupContent: '', followupResult: '' })
const completeForm = ref({ remark: '' })

// ── 附件上传（企服中心办理 / 部门反馈） ──────────────────────────────────────────
interface UploadedAttachment { id: number; originalName: string }
const centerHandleAttachments = ref<UploadedAttachment[]>([])
const deptReplyAttachments = ref<UploadedAttachment[]>([])
const centerHandleUploading = ref(false)
const deptReplyUploading = ref(false)

async function handleDialogUpload(file: File, target: 'centerHandle' | 'deptReply'): Promise<false> {
  const uploadingRef = target === 'centerHandle' ? centerHandleUploading : deptReplyUploading
  const listRef = target === 'centerHandle' ? centerHandleAttachments : deptReplyAttachments
  uploadingRef.value = true
  try {
    const result = await uploadAttachment(file)
    listRef.value = [...listRef.value, { id: result.id, originalName: result.originalName }]
  } catch {
    // 错误提示已由 uploadAttachment/request 拦截器统一处理
  } finally {
    uploadingRef.value = false
  }
  return false
}

// ── 表单 ref ──────────────────────────────────────────────────────────────────
const acceptRef = ref<FormInstance>()
const returnRef = ref<FormInstance>()
const rejectRef = ref<FormInstance>()
const centerHandleRef = ref<FormInstance>()
const assignRef = ref<FormInstance>()
const deptReplyRef = ref<FormInstance>()
const reviewRef = ref<FormInstance>()
const followupRef = ref<FormInstance>()

// ── 表单校验规则 ──────────────────────────────────────────────────────────────
const acceptRules = {
  appealTypeCode: [{ required: true, message: '请选择诉求类型', trigger: 'change' }],
  opinion: [{ required: true, message: '请输入受理意见', trigger: 'blur' }],
}
const returnRules = { opinion: [{ required: true, message: '请输入退回意见', trigger: 'blur' }] }
const rejectRules = {
  reasonCode: [{ required: true, message: '请选择不予受理原因', trigger: 'change' }],
  opinion: [{ required: true, message: '请输入处理意见', trigger: 'blur' }],
}
const centerHandleRules = { replyContent: [{ required: true, message: '请输入办理回复', trigger: 'blur' }] }
const assignRules = {
  assignedDeptId: [{ required: true, message: '请输入责任部门ID', trigger: 'blur' }],
  assignedDeptName: [{ required: true, message: '请输入责任部门名称', trigger: 'blur' }],
}
const deptReplyRules = { replyContent: [{ required: true, message: '请输入办理意见', trigger: 'blur' }] }
const reviewRules = { opinion: [{ required: true, message: '请输入审核意见', trigger: 'blur' }] }
const followupRules = {
  followupMethod: [{ required: true, message: '请选择回访方式', trigger: 'change' }],
  followupContent: [{ required: true, message: '请输入回访内容', trigger: 'blur' }],
  followupResult: [{ required: true, message: '请输入回访结果', trigger: 'blur' }],
}

// ── 动态字典（优先后端，回退本地枚举）────────────────────────────────────────
const appealTypeOptions = ref(APPEAL_TYPE_OPTIONS)
const rejectReasonOptions = ref(REJECT_REASON_OPTIONS)
const followupMethodOptions = ref(FOLLOWUP_METHOD_OPTIONS)
const appealTypeMap = ref<Record<string,string>>(Object.fromEntries(APPEAL_TYPE_OPTIONS.map(o=>[o.value,o.label])))
const rejectReasonMap = ref<Record<string,string>>(Object.fromEntries(REJECT_REASON_OPTIONS.map(o=>[o.value,o.label])))

// ── 数据加载 ──────────────────────────────────────────────────────────────────
async function loadDetail() {
  loading.value = true
  try {
    detail.value = await getAppealDetail(appealId.value)
  } finally {
    loading.value = false
  }
}

// ── 弹窗开关 ──────────────────────────────────────────────────────────────────
function openDialog(key: DialogKey) {
  dialogs.value[key] = true
}

async function downloadAttachment(id: number) {
  try {
    await openSecureAttachment(`/api/common/attachments/${id}/download`)
  } catch (e: unknown) {
    ElMessage.error((e as Error)?.message || '附件下载失败')
  }
}

// ── 字典联动 ──────────────────────────────────────────────────────────────────
function onAppealTypeChange(val: string) {
  acceptForm.value.appealTypeName = appealTypeMap.value[val] || val
}

function onRejectReasonChange(val: string) {
  rejectForm.value.reasonName = rejectReasonMap.value[val] || val
}

// ── 工具函数 ──────────────────────────────────────────────────────────────────
function handleModeText(mode?: string | null) {
  const map: Record<string, string> = { CENTER: '企服中心自行办理', DEPARTMENT: '分派部门办理' }
  return mode ? (map[mode] ?? mode) : '--'
}

function formatFileSize(bytes?: number) {
  if (!bytes) return '--'
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

function satisfactionTag(sat: string): 'success' | 'warning' | 'danger' | '' {
  if (sat === 'SATISFIED') return 'success'
  if (sat === 'UNSATISFIED') return 'danger'
  return 'warning'
}

function followupMethodText(method: string | null) {
  const map: Record<string, string> = { PHONE: '电话', VISIT: '上门', ONLINE: '线上', OTHER: '其他' }
  return method ? (map[method] ?? method) : '--'
}

// ── 提交操作 ──────────────────────────────────────────────────────────────────
async function withSubmit(fn: () => Promise<void>) {
  submitting.value = true
  try {
    await fn()
    await loadDetail()
  } finally {
    submitting.value = false
  }
}

async function submitAccept() {
  await acceptRef.value?.validate()
  await withSubmit(async () => {
    await acceptAppeal(appealId.value, {
      appealTypeCode: acceptForm.value.appealTypeCode,
      appealTypeName: acceptForm.value.appealTypeName,
      replyDeadline: acceptForm.value.replyDeadline || undefined,
      opinion: acceptForm.value.opinion,
    })
    dialogs.value.accept = false
    acceptForm.value = { appealTypeCode: '', appealTypeName: '', replyDeadline: '', opinion: '' }
    ElMessage.success('受理成功')
  })
}

async function submitReturn() {
  await returnRef.value?.validate()
  await withSubmit(async () => {
    await returnSupplementAppeal(appealId.value, { opinion: returnForm.value.opinion })
    dialogs.value.returnSupplement = false
    returnForm.value = { opinion: '' }
    ElMessage.success('已退回补充')
  })
}

async function submitReject() {
  await rejectRef.value?.validate()
  await withSubmit(async () => {
    await rejectAppeal(appealId.value, {
      reasonCode: rejectForm.value.reasonCode,
      reasonName: rejectForm.value.reasonName,
      opinion: rejectForm.value.opinion,
    })
    dialogs.value.reject = false
    rejectForm.value = { reasonCode: '', reasonName: '', opinion: '' }
    ElMessage.success('不予受理操作成功')
  })
}

async function submitCenterHandle() {
  await centerHandleRef.value?.validate()
  await withSubmit(async () => {
    await centerHandleAppeal(appealId.value, {
      replyContent: centerHandleForm.value.replyContent,
      attachmentIds: centerHandleAttachments.value.map(f => f.id),
    })
    dialogs.value.centerHandle = false
    centerHandleForm.value = { replyContent: '' }
    centerHandleAttachments.value = []
    ElMessage.success('办理成功')
  })
}

async function submitAssign() {
  await assignRef.value?.validate()
  await withSubmit(async () => {
    await assignAppeal(appealId.value, {
      assignedDeptId: assignForm.value.assignedDeptId,
      assignedDeptName: assignForm.value.assignedDeptName,
      deadline: assignForm.value.deadline || undefined,
      assignOpinion: assignForm.value.assignOpinion || undefined,
    })
    dialogs.value.assign = false
    assignForm.value = { assignedDeptId: '', assignedDeptName: '', deadline: '', assignOpinion: '' }
    ElMessage.success('分派成功')
  })
}

async function submitDeptReply() {
  await deptReplyRef.value?.validate()
  await withSubmit(async () => {
    await departmentReplyAppeal(appealId.value, {
      replyContent: deptReplyForm.value.replyContent,
      attachmentIds: deptReplyAttachments.value.map(f => f.id),
    })
    dialogs.value.deptReply = false
    deptReplyForm.value = { replyContent: '' }
    deptReplyAttachments.value = []
    ElMessage.success('反馈提交成功')
  })
}

async function submitReview() {
  await reviewRef.value?.validate()
  await withSubmit(async () => {
    const passed = reviewForm.value.pass
    await reviewReplyAppeal(appealId.value, { pass: passed, opinion: reviewForm.value.opinion })
    dialogs.value.reviewReply = false
    reviewForm.value = { pass: true, opinion: '' }
    ElMessage.success(passed ? '审核通过' : '已退回')
  })
}

async function submitFollowup() {
  await followupRef.value?.validate()
  await withSubmit(async () => {
    await addAppealFollowup(appealId.value, {
      responsibleDeptId: followupForm.value.responsibleDeptId || undefined,
      responsibleDeptName: followupForm.value.responsibleDeptName || undefined,
      followupMethod: followupForm.value.followupMethod,
      followupContent: followupForm.value.followupContent,
      followupResult: followupForm.value.followupResult,
    })
    dialogs.value.followup = false
    followupForm.value = { responsibleDeptId: '', responsibleDeptName: '', followupMethod: '', followupContent: '', followupResult: '' }
    ElMessage.success('回访记录已保存')
  })
}

async function submitComplete() {
  await withSubmit(async () => {
    await completeAppeal(appealId.value, { remark: completeForm.value.remark || undefined })
    dialogs.value.complete = false
    completeForm.value = { remark: '' }
    ElMessage.success('已办结')
  })
}

onMounted(async () => {
  // 并行加载字典 + 详情
  const [types, reasons, methods] = await Promise.all([
    getDictionary('APPEAL_TYPE'),
    getDictionary('APPEAL_REJECT_REASON'),
    getDictionary('FOLLOWUP_METHOD'),
    loadDetail(),
  ])
  if (types.length) {
    appealTypeOptions.value = types.map(d => ({ value: d.dictCode, label: d.dictLabel }))
    appealTypeMap.value = dictToMap(types)
  }
  if (reasons.length) {
    rejectReasonOptions.value = reasons.map(d => ({ value: d.dictCode, label: d.dictLabel }))
    rejectReasonMap.value = dictToMap(reasons)
  }
  if (methods.length) {
    followupMethodOptions.value = methods.map(d => ({ value: d.dictCode, label: d.dictLabel }))
  }
})
</script>

<style scoped lang="scss">
.appeal-detail {
  padding-bottom: 40px;
}

.detail-topbar {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;

  .detail-title {
    display: flex;
    align-items: center;
    flex: 1;

    .title-text {
      font-size: 18px;
      font-weight: 600;
      color: #1a1a1a;
    }
  }
}

.section-card {
  margin-bottom: 12px;

  :deep(.el-card__header) {
    padding: 10px 16px;
    background: #fafafa;
  }
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: #333;
}

.action-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.content-text {
  white-space: pre-wrap;
  line-height: 1.8;
  color: #444;
}

.record-item {
  padding: 2px 0;

  .record-header {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 8px;

    .record-operator {
      font-weight: 500;
      color: #333;
    }

    .record-dept {
      color: #888;
      font-size: 12px;
    }

    .record-status {
      display: flex;
      align-items: center;
      gap: 4px;
      color: #888;
    }
  }

  .record-opinion {
    margin-top: 6px;
    color: #555;
    font-size: 13px;
    background: #f9f9f9;
    padding: 6px 10px;
    border-radius: 4px;
    border-left: 3px solid #e0e0e0;
  }
}

.attachment-uploader__item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #606266;
  margin-bottom: 6px;
}
.attachment-uploader__item .el-icon {
  cursor: pointer;
  color: #f56c6c;
}
</style>
