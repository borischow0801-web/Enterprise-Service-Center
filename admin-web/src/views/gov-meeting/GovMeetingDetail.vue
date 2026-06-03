<template>
  <div class="detail-page">
    <!-- 顶部操作栏 -->
    <div class="detail-header">
      <el-button @click="router.back()"><el-icon><ArrowLeft /></el-icon> 返回列表</el-button>
      <div class="header-title">
        <span class="apply-no">{{ detail?.applyNo }}</span>
        <el-tag v-if="detail" :type="statusTagType('govMeeting', detail.status)" style="margin-left:10px">
          {{ statusText('govMeeting', detail.status) }}
        </el-tag>
      </div>
      <!-- 操作按钮区 -->
      <div class="header-actions" v-if="detail">
        <template v-if="detail.status === 'PENDING_AUDIT'">
          <el-button type="success" @click="openAcceptDialog">受理通过</el-button>
          <el-button type="warning" @click="openReturnDialog">退回补正</el-button>
          <el-button type="danger" @click="openRejectDialog">不予受理</el-button>
        </template>
        <template v-if="detail.status === 'PENDING_ARRANGE'">
          <el-button type="primary" @click="openArrangeDialog(false)">安排约见</el-button>
        </template>
        <template v-if="detail.status === 'ARRANGED'">
          <el-button type="primary" @click="openArrangeDialog(true)">变更安排</el-button>
          <el-button type="success" @click="openConfirmDialog">确认并通知企业</el-button>
        </template>
        <template v-if="detail.status === 'WAIT_MEETING'">
          <el-button type="primary" @click="openArrangeDialog(true)">变更安排</el-button>
          <el-button type="success" @click="openCompleteDialog">标记约见完成</el-button>
        </template>
        <template v-if="detail.status === 'MEETING_COMPLETED'">
          <el-button type="primary" @click="openRecordDialog">填写约见纪要</el-button>
          <el-button type="success" @click="openFinishDialog">发送评价/办结</el-button>
        </template>
      </div>
    </div>

    <div v-if="loading" v-loading="loading" style="height:300px" />

    <template v-else-if="detail">
      <!-- 第一块：企业信息 -->
      <el-card class="detail-card" header="企业信息">
        <el-descriptions :column="3" border>
          <el-descriptions-item label="企业名称">{{ detail.enterpriseName }}</el-descriptions-item>
          <el-descriptions-item label="统一社会信用代码">{{ detail.creditCode }}</el-descriptions-item>
          <el-descriptions-item label="联系人">{{ detail.contactName }}</el-descriptions-item>
          <el-descriptions-item label="联系电话">{{ detail.contactPhone }}</el-descriptions-item>
          <el-descriptions-item label="所属区划">{{ detail.regionName }}</el-descriptions-item>
          <el-descriptions-item label="所属企服中心">{{ detail.serviceCenterName || '--' }}</el-descriptions-item>
        </el-descriptions>
      </el-card>

      <!-- 第二块：约见申请信息 -->
      <el-card class="detail-card" header="约见申请信息">
        <el-descriptions :column="3" border>
          <el-descriptions-item label="申请编号">{{ detail.applyNo }}</el-descriptions-item>
          <el-descriptions-item label="当前状态">
            <el-tag :type="statusTagType('govMeeting', detail.status)">{{ statusText('govMeeting', detail.status) }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="约见主题">{{ detail.topicName || '--' }}</el-descriptions-item>
          <el-descriptions-item label="企业期望层级">{{ detail.expectedLevelName || detail.meetingLevel || '--' }}</el-descriptions-item>
          <el-descriptions-item label="后台研判层级">{{ detail.finalLevelName || '--' }}</el-descriptions-item>
          <el-descriptions-item label="承诺书">{{ detail.commitmentChecked ? '已确认' : '--' }}</el-descriptions-item>
          <el-descriptions-item label="提交时间">{{ formatDate(detail.submittedAt) }}</el-descriptions-item>
          <el-descriptions-item label="受理时间">{{ formatDate(detail.acceptedAt) }}</el-descriptions-item>
          <el-descriptions-item label="安排时间">{{ formatDate(detail.arrangedAt) }}</el-descriptions-item>
          <el-descriptions-item label="约见完成时间">{{ formatDate(detail.completedAt) }}</el-descriptions-item>
          <el-descriptions-item label="评价时间">{{ formatDate(detail.evaluatedAt) }}</el-descriptions-item>
          <el-descriptions-item label="办结时间">{{ formatDate(detail.finishedAt) }}</el-descriptions-item>
        </el-descriptions>
        <div style="margin-top:14px">
          <div class="field-label">约见内容 / 诉求描述</div>
          <div class="content-body">{{ detail.description }}</div>
        </div>
        <div v-if="detail.rejectReasonName || detail.rejectOpinion" style="margin-top:14px">
          <div class="field-label" style="color:#ee0a24">不予受理原因</div>
          <div style="color:#ee0a24">{{ detail.rejectReasonName }}{{ detail.rejectOpinion ? '：' + detail.rejectOpinion : '' }}</div>
        </div>
      </el-card>

      <!-- 第三块：附件列表 -->
      <el-card v-if="detail.attachments?.length" class="detail-card" header="申请附件">
        <el-table :data="detail.attachments" border size="small">
          <el-table-column prop="originalName" label="文件名" min-width="200" show-overflow-tooltip />
          <el-table-column label="大小" width="100">
            <template #default="{ row }">{{ formatSize(row.fileSize) }}</template>
          </el-table-column>
          <el-table-column label="操作" width="100">
            <template #default="{ row }">
              <el-button link type="primary" @click="downloadAtt(row.id)">下载</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <!-- 第四块：审核记录时间线 -->
      <el-card v-if="detail.auditTrail?.length" class="detail-card" header="审核记录">
        <el-timeline>
          <el-timeline-item
            v-for="item in detail.auditTrail"
            :key="item.id"
            :timestamp="formatDate(item.createdAt)"
            placement="top"
          >
            <el-card shadow="never" class="timeline-card">
              <div class="timeline-row">
                <el-tag size="small" type="primary">{{ item.actionName || item.actionType }}</el-tag>
                <span class="tl-operator">{{ item.operatorName }}</span>
                <span v-if="item.operatorDeptName" class="tl-dept">（{{ item.operatorDeptName }}）</span>
              </div>
              <div v-if="item.beforeStatus || item.afterStatus" class="tl-status">
                <span v-if="item.beforeStatus">{{ statusText('govMeeting', item.beforeStatus) }}</span>
                <span v-if="item.beforeStatus && item.afterStatus"> → </span>
                <span v-if="item.afterStatus">{{ statusText('govMeeting', item.afterStatus) }}</span>
              </div>
              <div v-if="item.opinion" class="tl-opinion">意见：{{ item.opinion }}</div>
            </el-card>
          </el-timeline-item>
        </el-timeline>
      </el-card>

      <!-- 第五块：约见安排 -->
      <el-card v-if="detail.arrangement" class="detail-card" header="约见安排">
        <el-descriptions :column="3" border>
          <el-descriptions-item label="约见日期">{{ formatDateOnly(detail.arrangement.meetingDate) }}</el-descriptions-item>
          <el-descriptions-item label="开始时间">{{ formatDate(detail.arrangement.startTime) || '--' }}</el-descriptions-item>
          <el-descriptions-item label="结束时间">{{ formatDate(detail.arrangement.endTime) || '--' }}</el-descriptions-item>
          <el-descriptions-item label="约见方式">{{ MEETING_METHOD_MAP[detail.arrangement.meetingMethod || ''] || detail.arrangement.meetingMethod || '--' }}</el-descriptions-item>
          <el-descriptions-item label="约见地点">{{ detail.arrangement.meetingPlace || '--' }}</el-descriptions-item>
          <el-descriptions-item label="主持部门">{{ detail.arrangement.hostDeptName || '--' }}</el-descriptions-item>
          <el-descriptions-item label="政府联系人">{{ detail.arrangement.govContactName || '--' }}</el-descriptions-item>
          <el-descriptions-item label="联系电话">{{ detail.arrangement.govContactPhone || '--' }}</el-descriptions-item>
          <el-descriptions-item label="已通知企业">{{ detail.arrangement.confirmedFlag ? '是' : '否' }}</el-descriptions-item>
          <el-descriptions-item v-if="detail.arrangement.notes" label="备注说明" :span="3">{{ detail.arrangement.notes }}</el-descriptions-item>
          <el-descriptions-item v-if="detail.arrangement.remark" label="注意事项" :span="3">{{ detail.arrangement.remark }}</el-descriptions-item>
        </el-descriptions>

        <!-- 第六块：参会人员 -->
        <div v-if="detail.arrangement.participants?.length" style="margin-top:16px">
          <div class="field-label">参会人员</div>
          <el-table :data="detail.arrangement.participants" border size="small" style="margin-top:8px">
            <el-table-column label="类型" width="90">
              <template #default="{ row }">{{ PARTICIPANT_TYPE_MAP[row.participantType] || row.participantType }}</template>
            </el-table-column>
            <el-table-column prop="participantName" label="姓名" width="110" />
            <el-table-column prop="participantTitle" label="职务" width="120" show-overflow-tooltip />
            <el-table-column prop="roleName" label="参会角色" width="110" show-overflow-tooltip>
              <template #default="{ row }">{{ row.roleName || '--' }}</template>
            </el-table-column>
            <el-table-column prop="participantDeptName" label="所在部门" min-width="130" show-overflow-tooltip>
              <template #default="{ row }">{{ row.participantDeptName || '--' }}</template>
            </el-table-column>
            <el-table-column prop="contactPhone" label="联系电话" width="130">
              <template #default="{ row }">{{ row.contactPhone || '--' }}</template>
            </el-table-column>
          </el-table>
        </div>
      </el-card>

      <!-- 第七块：约见纪要 -->
      <el-card v-if="detail.records?.length" class="detail-card" header="约见纪要">
        <div v-for="rec in detail.records" :key="rec.id" class="record-item">
          <div class="record-meta">
            记录人：{{ rec.recorderName }} &nbsp;|&nbsp; 记录时间：{{ formatDate(rec.recordTime) }}
          </div>
          <div class="field-label" style="margin-top:10px">约见内容</div>
          <div class="content-body">{{ rec.content }}</div>
          <template v-if="rec.conclusions">
            <div class="field-label" style="margin-top:10px">沟通结论</div>
            <div class="content-body">{{ rec.conclusions }}</div>
          </template>
          <template v-if="rec.followUpItems">
            <div class="field-label" style="margin-top:10px">后续跟进事项</div>
            <div class="content-body">{{ rec.followUpItems }}</div>
          </template>
        </div>
      </el-card>

      <!-- 第八块：评价信息 -->
      <el-card class="detail-card" header="企业评价">
        <template v-if="detail.evaluation">
          <el-descriptions :column="3" border>
            <el-descriptions-item label="满意度">{{ formatSatisfaction(detail.evaluation.satisfaction) }}</el-descriptions-item>
            <el-descriptions-item label="星级评分">
              <el-rate :model-value="detail.evaluation.score" disabled show-score />
            </el-descriptions-item>
            <el-descriptions-item label="是否解决主要诉求">
              {{ formatResolvedFlag(detail.evaluation.resolvedFlag) }}
            </el-descriptions-item>
            <el-descriptions-item label="评价意见" :span="3">{{ detail.evaluation.comment || '--' }}</el-descriptions-item>
            <el-descriptions-item label="评价时间">{{ formatDate(detail.evaluation.createdAt) }}</el-descriptions-item>
          </el-descriptions>
        </template>
        <template v-else-if="detail.status === 'PENDING_EVALUATION'">
          <el-empty description="等待企业提交评价" :image-size="60" />
        </template>
        <template v-else>
          <div style="color:#999;font-size:13px;padding:8px 0">暂无评价信息</div>
        </template>
      </el-card>
    </template>

    <el-empty v-if="!loading && !detail" description="申请记录不存在" />

    <!-- ====== 受理通过弹窗 ====== -->
    <el-dialog v-model="acceptVisible" title="受理通过" width="520px" :close-on-click-modal="false">
      <el-form :model="acceptForm" ref="acceptFormRef" label-width="130px">
        <el-form-item label="后台研判约见层级">
          <el-select v-model="acceptForm.finalLevelCode" placeholder="请选择（选填）" clearable style="width:100%"
            @change="onFinalLevelChange">
            <el-option v-for="lv in levelOptions" :key="lv.value" :label="lv.label" :value="lv.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="受理意见">
          <el-input v-model="acceptForm.opinion" type="textarea" :rows="3" placeholder="可填写受理意见（选填）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="acceptVisible = false">取消</el-button>
        <el-button type="primary" :loading="opLoading" @click="handleAccept">确认受理</el-button>
      </template>
    </el-dialog>

    <!-- ====== 退回补正弹窗 ====== -->
    <el-dialog v-model="returnVisible" title="退回补正" width="480px" :close-on-click-modal="false">
      <el-form :model="returnForm" :rules="returnRules" ref="returnFormRef" label-width="110px">
        <el-form-item label="退回意见" prop="opinion">
          <el-input v-model="returnForm.opinion" type="textarea" :rows="3" placeholder="请说明退回补正原因" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="returnVisible = false">取消</el-button>
        <el-button type="warning" :loading="opLoading" @click="handleReturn">确认退回</el-button>
      </template>
    </el-dialog>

    <!-- ====== 不予受理弹窗 ====== -->
    <el-dialog v-model="rejectVisible" title="不予受理" width="520px" :close-on-click-modal="false">
      <el-form :model="rejectForm" :rules="rejectRules" ref="rejectFormRef" label-width="110px">
        <el-form-item label="不予受理原因" prop="rejectReasonCode">
          <el-select v-model="rejectForm.rejectReasonCode" placeholder="请选择" style="width:100%"
            @change="onRejectReasonChange">
            <el-option v-for="r in rejectReasonOptions" :key="r.value" :label="r.label" :value="r.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="处理意见">
          <el-input v-model="rejectForm.opinion" type="textarea" :rows="3" placeholder="可补充说明（选填）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="rejectVisible = false">取消</el-button>
        <el-button type="danger" :loading="opLoading" @click="handleReject">确认不予受理</el-button>
      </template>
    </el-dialog>

    <!-- ====== 安排约见 / 变更安排 弹窗 ====== -->
    <el-dialog v-model="arrangeVisible" :title="isUpdateArrange ? '变更约见安排' : '安排约见'" width="780px" :close-on-click-modal="false">
      <el-form :model="arrangeForm" :rules="arrangeRules" ref="arrangeFormRef" label-width="110px">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="约见日期" prop="meetingDate">
              <el-date-picker v-model="arrangeForm.meetingDate" type="date" value-format="YYYY-MM-DD"
                placeholder="请选择日期" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="约见方式" prop="meetingMethod">
              <el-select v-model="arrangeForm.meetingMethod" placeholder="请选择" style="width:100%">
                <el-option label="现场会议" value="ON_SITE" />
                <el-option label="视频会议" value="VIDEO" />
                <el-option label="电话沟通" value="PHONE" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="开始时间">
              <el-date-picker v-model="arrangeForm.startTime" type="datetime" value-format="YYYY-MM-DDTHH:mm:ss"
                placeholder="约见开始时间（选填）" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="结束时间">
              <el-date-picker v-model="arrangeForm.endTime" type="datetime" value-format="YYYY-MM-DDTHH:mm:ss"
                placeholder="约见结束时间（选填）" style="width:100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="约见地点" prop="meetingPlace">
          <el-input v-model="arrangeForm.meetingPlace" placeholder="请输入约见地点" />
        </el-form-item>
        <el-form-item label="主持部门">
          <el-input v-model="arrangeForm.hostDeptName" placeholder="主持部门名称（选填）" />
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="政府联系人">
              <el-input v-model="arrangeForm.govContactName" placeholder="联系人姓名" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="联系电话">
              <el-input v-model="arrangeForm.govContactPhone" placeholder="联系电话" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="备注说明">
          <el-input v-model="arrangeForm.notes" type="textarea" :rows="2" placeholder="备注说明（选填）" />
        </el-form-item>
        <el-form-item label="注意事项">
          <el-input v-model="arrangeForm.remark" type="textarea" :rows="2" placeholder="注意事项（选填）" />
        </el-form-item>

        <!-- 参会人员 -->
        <el-divider content-position="left">参会人员</el-divider>
        <div style="margin-bottom:10px">
          <el-button size="small" type="primary" plain @click="addParticipant">+ 添加参会人员</el-button>
        </div>
        <el-table :data="arrangeForm.participants" border size="small">
          <el-table-column label="类型" width="110">
            <template #default="{ row }">
              <el-select v-model="row.participantType" size="small" style="width:100%">
                <el-option v-for="t in participantTypeOptions" :key="t.value" :label="t.label" :value="t.value" />
              </el-select>
            </template>
          </el-table-column>
          <el-table-column label="姓名" width="100">
            <template #default="{ row }">
              <el-input v-model="row.participantName" size="small" placeholder="姓名" />
            </template>
          </el-table-column>
          <el-table-column label="职务" width="110">
            <template #default="{ row }">
              <el-input v-model="row.participantTitle" size="small" placeholder="职务" />
            </template>
          </el-table-column>
          <el-table-column label="参会角色" width="110">
            <template #default="{ row }">
              <el-input v-model="row.roleName" size="small" placeholder="如：主持人/列席" />
            </template>
          </el-table-column>
          <el-table-column label="所在部门" min-width="130">
            <template #default="{ row }">
              <el-input v-model="row.participantDeptName" size="small" placeholder="所在部门" />
            </template>
          </el-table-column>
          <el-table-column label="联系电话" width="120">
            <template #default="{ row }">
              <el-input v-model="row.contactPhone" size="small" placeholder="联系电话" />
            </template>
          </el-table-column>
          <el-table-column label="操作" width="65">
            <template #default="{ $index }">
              <el-button link type="danger" @click="removeParticipant($index)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-form>
      <template #footer>
        <el-button @click="arrangeVisible = false">取消</el-button>
        <el-button type="primary" :loading="opLoading" @click="handleArrangeSubmit">保存</el-button>
      </template>
    </el-dialog>

    <!-- ====== 确认通知弹窗 ====== -->
    <el-dialog v-model="confirmVisible" title="确认并通知企业" width="480px" :close-on-click-modal="false">
      <el-alert type="info" :closable="false" show-icon style="margin-bottom:16px">
        确认后将通知企业约见安排，状态变为"待约见"。
      </el-alert>
      <el-form :model="confirmForm" label-width="90px">
        <el-form-item label="备注">
          <el-input v-model="confirmForm.opinion" type="textarea" :rows="2" placeholder="可添加备注（选填）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="confirmVisible = false">取消</el-button>
        <el-button type="primary" :loading="opLoading" @click="handleConfirm">确认通知</el-button>
      </template>
    </el-dialog>

    <!-- ====== 标记约见完成弹窗 ====== -->
    <el-dialog v-model="completeVisible" title="标记约见完成" width="480px" :close-on-click-modal="false">
      <el-form :model="completeForm" label-width="110px">
        <el-form-item label="实际约见时间">
          <el-date-picker v-model="completeForm.meetingAt" type="datetime" value-format="YYYY-MM-DDTHH:mm:ss"
            placeholder="默认为当前时间" style="width:100%" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="completeForm.opinion" type="textarea" :rows="2" placeholder="可添加备注（选填）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="completeVisible = false">取消</el-button>
        <el-button type="success" :loading="opLoading" @click="handleComplete">确认完成</el-button>
      </template>
    </el-dialog>

    <!-- ====== 填写约见纪要弹窗 ====== -->
    <el-dialog v-model="recordVisible" title="填写约见纪要" width="600px" :close-on-click-modal="false">
      <el-form :model="recordForm" :rules="recordRules" ref="recordFormRef" label-width="110px">
        <el-form-item label="约见内容" prop="content">
          <el-input v-model="recordForm.content" type="textarea" :rows="4" placeholder="请详细填写约见内容和纪要" maxlength="2000" show-word-limit />
        </el-form-item>
        <el-form-item label="沟通结论">
          <el-input v-model="recordForm.conclusions" type="textarea" :rows="3" placeholder="主要结论和达成共识（选填）" maxlength="1000" show-word-limit />
        </el-form-item>
        <el-form-item label="后续跟进事项">
          <el-input v-model="recordForm.followUpItems" type="textarea" :rows="2" placeholder="需后续跟进的事项（选填）" maxlength="1000" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="recordVisible = false">取消</el-button>
        <el-button type="primary" :loading="opLoading" @click="handleRecord">保存纪要</el-button>
      </template>
    </el-dialog>

    <!-- ====== 发送评价 / 办结弹窗 ====== -->
    <el-dialog v-model="finishVisible" title="发送评价通知 / 办结" width="480px" :close-on-click-modal="false">
      <el-form :model="finishForm" label-width="130px">
        <el-form-item label="是否发送评价通知">
          <el-radio-group v-model="finishForm.sendEvaluation">
            <el-radio :value="1">是（发送评价，进入待评价）</el-radio>
            <el-radio :value="0">否（直接办结）</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="办结意见">
          <el-input v-model="finishForm.opinion" type="textarea" :rows="2" placeholder="可填写办结说明（选填）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="finishVisible = false">取消</el-button>
        <el-button type="primary" :loading="opLoading" @click="handleFinish">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import type { FormInstance } from 'element-plus'
import { ElMessage } from 'element-plus'
import { ArrowLeft } from '@element-plus/icons-vue'
import {
  getGovMeetingDetail,
  auditGovMeeting,
  arrangeGovMeeting,
  updateGovMeetingArrangement,
  confirmGovMeeting,
  completeGovMeeting,
  recordGovMeeting,
  finishGovMeeting,
} from '@/api/govMeeting'
import type { GovMeetingDetail, GovMeetingParticipant } from '@/api/govMeeting'
import { statusText, statusTagType, formatDate, formatDateOnly } from '@/utils/format'
import { formatSatisfaction, formatResolvedFlag } from '@/utils/appealConsts'
import { getDictionary } from '@/api/common'

const route = useRoute()
const router = useRouter()
const applyId = Number(route.params.id)

const loading = ref(false)
const opLoading = ref(false)
const detail = ref<GovMeetingDetail | null>(null)

// ── Constants ──────────────────────────────────────────────────────────────
const MEETING_METHOD_MAP: Record<string, string> = {
  ON_SITE: '现场会议', VIDEO: '视频会议', PHONE: '电话沟通',
}
const PARTICIPANT_TYPE_MAP: Record<string, string> = {
  GOV: '政府', ENTERPRISE: '企业',
}
const participantTypeOptions = [
  { value: 'GOV', label: '政府' },
  { value: 'ENTERPRISE', label: '企业' },
]

// ── Dict options ───────────────────────────────────────────────────────────
const rejectReasonOptions = ref<{ value: string; label: string }[]>([])
const levelOptions = ref<{ value: string; label: string }[]>([])

// ── Load detail ────────────────────────────────────────────────────────────
async function fetchDetail() {
  loading.value = true
  try {
    detail.value = await getGovMeetingDetail(applyId)
  } catch {
    detail.value = null
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  const [reasons, levels] = await Promise.all([
    getDictionary('GOV_MEETING_REJECT_REASON'),
    getDictionary('GOV_MEETING_LEVEL'),
    fetchDetail(),
  ])
  rejectReasonOptions.value = reasons.length
    ? reasons.map(d => ({ value: d.dictCode, label: d.dictLabel }))
    : [
        { value: 'NOT_QUALIFIED', label: '不符合约见条件' },
        { value: 'MATERIAL_INCOMPLETE', label: '材料不完整' },
        { value: 'OTHER', label: '其他' },
      ]
  levelOptions.value = levels.map(d => ({ value: d.dictCode, label: d.dictLabel }))
})

// ── Helpers ────────────────────────────────────────────────────────────────
function formatSize(bytes?: number): string {
  if (!bytes) return '--'
  if (bytes < 1024) return `${bytes}B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)}KB`
  return `${(bytes / 1024 / 1024).toFixed(1)}MB`
}

function downloadAtt(id: number) {
  window.open(`/api/common/attachments/${id}/download`, '_blank')
}

// ── 受理通过 ────────────────────────────────────────────────────────────────
const acceptVisible = ref(false)
const acceptFormRef = ref<FormInstance>()
const acceptForm = reactive({ opinion: '', finalLevelCode: '', finalLevelName: '' })

function openAcceptDialog() {
  Object.assign(acceptForm, { opinion: '', finalLevelCode: '', finalLevelName: '' })
  acceptFormRef.value?.clearValidate()
  acceptVisible.value = true
}

function onFinalLevelChange(val: string) {
  const opt = levelOptions.value.find(lv => lv.value === val)
  acceptForm.finalLevelName = opt?.label || ''
}

async function handleAccept() {
  opLoading.value = true
  try {
    await auditGovMeeting(applyId, {
      auditType: 'ACCEPT',
      opinion: acceptForm.opinion || undefined,
      finalLevelCode: acceptForm.finalLevelCode || undefined,
      finalLevelName: acceptForm.finalLevelName || undefined,
    })
    ElMessage.success('受理成功，状态进入"待安排"')
    acceptVisible.value = false
    fetchDetail()
  } finally {
    opLoading.value = false
  }
}

// ── 退回补正 ────────────────────────────────────────────────────────────────
const returnVisible = ref(false)
const returnFormRef = ref<FormInstance>()
const returnForm = reactive({ opinion: '' })
const returnRules = {
  opinion: [{ required: true, message: '请填写退回意见', trigger: 'blur' }],
}

function openReturnDialog() {
  returnForm.opinion = ''
  returnFormRef.value?.clearValidate()
  returnVisible.value = true
}

async function handleReturn() {
  await returnFormRef.value?.validate()
  opLoading.value = true
  try {
    await auditGovMeeting(applyId, { auditType: 'RETURN_SUPPLEMENT', opinion: returnForm.opinion })
    ElMessage.success('已退回补正')
    returnVisible.value = false
    fetchDetail()
  } finally {
    opLoading.value = false
  }
}

// ── 不予受理 ────────────────────────────────────────────────────────────────
const rejectVisible = ref(false)
const rejectFormRef = ref<FormInstance>()
const rejectForm = reactive({ rejectReasonCode: '', rejectReasonName: '', opinion: '' })
const rejectRules = {
  rejectReasonCode: [{ required: true, message: '请选择不予受理原因', trigger: 'change' }],
}

function openRejectDialog() {
  Object.assign(rejectForm, { rejectReasonCode: '', rejectReasonName: '', opinion: '' })
  rejectFormRef.value?.clearValidate()
  rejectVisible.value = true
}

function onRejectReasonChange(val: string) {
  const opt = rejectReasonOptions.value.find(r => r.value === val)
  rejectForm.rejectReasonName = opt?.label || ''
}

async function handleReject() {
  await rejectFormRef.value?.validate()
  opLoading.value = true
  try {
    await auditGovMeeting(applyId, {
      auditType: 'REJECT',
      rejectReasonCode: rejectForm.rejectReasonCode,
      rejectReasonName: rejectForm.rejectReasonName,
      opinion: rejectForm.opinion || undefined,
    })
    ElMessage.success('已不予受理')
    rejectVisible.value = false
    fetchDetail()
  } finally {
    opLoading.value = false
  }
}

// ── 安排约见 / 变更安排 ────────────────────────────────────────────────────
const arrangeVisible = ref(false)
const isUpdateArrange = ref(false)
const arrangeFormRef = ref<FormInstance>()
const arrangeForm = reactive({
  meetingDate: '',
  meetingMethod: '',
  meetingPlace: '',
  startTime: '',
  endTime: '',
  hostDeptName: '',
  govContactName: '',
  govContactPhone: '',
  notes: '',
  remark: '',
  participants: [] as GovMeetingParticipant[],
})
const arrangeRules = {
  meetingDate: [{ required: true, message: '请选择约见日期', trigger: 'change' }],
  meetingPlace: [{ required: true, message: '请输入约见地点', trigger: 'blur' }],
  meetingMethod: [{ required: true, message: '请选择约见方式', trigger: 'change' }],
}

function openArrangeDialog(isUpdate: boolean) {
  isUpdateArrange.value = isUpdate
  if (isUpdate && detail.value?.arrangement) {
    const arr = detail.value.arrangement
    Object.assign(arrangeForm, {
      meetingDate: arr.meetingDate ? arr.meetingDate.slice(0, 10) : '',
      meetingMethod: arr.meetingMethod || '',
      meetingPlace: arr.meetingPlace || '',
      startTime: arr.startTime || '',
      endTime: arr.endTime || '',
      hostDeptName: arr.hostDeptName || '',
      govContactName: arr.govContactName || '',
      govContactPhone: arr.govContactPhone || '',
      notes: arr.notes || '',
      remark: arr.remark || '',
      participants: (arr.participants || []).map(p => ({ ...p })),
    })
  } else {
    Object.assign(arrangeForm, {
      meetingDate: '', meetingMethod: '', meetingPlace: '',
      startTime: '', endTime: '', hostDeptName: '',
      govContactName: '', govContactPhone: '', notes: '', remark: '',
      participants: [],
    })
  }
  arrangeFormRef.value?.clearValidate()
  arrangeVisible.value = true
}

function addParticipant() {
  arrangeForm.participants.push({
    participantType: 'GOV',
    participantName: '',
    participantTitle: '',
    roleName: '',
    participantDeptName: '',
    contactPhone: '',
    sortNo: arrangeForm.participants.length,
  })
}

function removeParticipant(index: number) {
  arrangeForm.participants.splice(index, 1)
}

async function handleArrangeSubmit() {
  await arrangeFormRef.value?.validate()
  for (const p of arrangeForm.participants) {
    if (!p.participantName?.trim()) { ElMessage.warning('请填写所有参会人员姓名'); return }
  }
  opLoading.value = true
  try {
    const payload = {
      meetingDate: arrangeForm.meetingDate || undefined,
      meetingMethod: arrangeForm.meetingMethod || undefined,
      meetingPlace: arrangeForm.meetingPlace || undefined,
      startTime: arrangeForm.startTime || undefined,
      endTime: arrangeForm.endTime || undefined,
      hostDeptName: arrangeForm.hostDeptName || undefined,
      govContactName: arrangeForm.govContactName || undefined,
      govContactPhone: arrangeForm.govContactPhone || undefined,
      notes: arrangeForm.notes || undefined,
      remark: arrangeForm.remark || undefined,
      participants: arrangeForm.participants.length
        ? arrangeForm.participants.map((p, i) => ({
            participantType: p.participantType,
            participantName: p.participantName,
            participantTitle: p.participantTitle || undefined,
            roleName: p.roleName || undefined,
            participantDeptName: p.participantDeptName || undefined,
            contactPhone: p.contactPhone || undefined,
            sortNo: i,
          }))
        : undefined,
    }
    if (isUpdateArrange.value && detail.value?.arrangement?.id) {
      await updateGovMeetingArrangement(applyId, detail.value.arrangement.id, payload)
      ElMessage.success('安排已更新')
    } else {
      await arrangeGovMeeting(applyId, payload)
      ElMessage.success('约见已安排，状态进入"已安排"')
    }
    arrangeVisible.value = false
    fetchDetail()
  } finally {
    opLoading.value = false
  }
}

// ── 确认通知 ────────────────────────────────────────────────────────────────
const confirmVisible = ref(false)
const confirmForm = reactive({ opinion: '' })

function openConfirmDialog() {
  confirmForm.opinion = ''
  confirmVisible.value = true
}

async function handleConfirm() {
  opLoading.value = true
  try {
    await confirmGovMeeting(applyId, { opinion: confirmForm.opinion || undefined })
    ElMessage.success('已通知企业，状态进入"待约见"')
    confirmVisible.value = false
    fetchDetail()
  } finally {
    opLoading.value = false
  }
}

// ── 标记约见完成 ────────────────────────────────────────────────────────────
const completeVisible = ref(false)
const completeForm = reactive({ meetingAt: '', opinion: '' })

function openCompleteDialog() {
  completeForm.meetingAt = ''
  completeForm.opinion = ''
  completeVisible.value = true
}

async function handleComplete() {
  opLoading.value = true
  try {
    await completeGovMeeting(applyId, {
      meetingAt: completeForm.meetingAt || undefined,
      opinion: completeForm.opinion || undefined,
    })
    ElMessage.success('约见已完成，状态进入"约见完成"')
    completeVisible.value = false
    fetchDetail()
  } finally {
    opLoading.value = false
  }
}

// ── 填写约见纪要 ────────────────────────────────────────────────────────────
const recordVisible = ref(false)
const recordFormRef = ref<FormInstance>()
const recordForm = reactive({ content: '', conclusions: '', followUpItems: '' })
const recordRules = {
  content: [{ required: true, message: '请填写约见内容', trigger: 'blur' }],
}

function openRecordDialog() {
  Object.assign(recordForm, { content: '', conclusions: '', followUpItems: '' })
  recordFormRef.value?.clearValidate()
  recordVisible.value = true
}

async function handleRecord() {
  await recordFormRef.value?.validate()
  opLoading.value = true
  try {
    await recordGovMeeting(applyId, {
      arrangementId: detail.value?.arrangement?.id,
      content: recordForm.content,
      conclusions: recordForm.conclusions || undefined,
      followUpItems: recordForm.followUpItems || undefined,
    })
    ElMessage.success('约见纪要已保存')
    recordVisible.value = false
    fetchDetail()
  } finally {
    opLoading.value = false
  }
}

// ── 发送评价 / 办结 ─────────────────────────────────────────────────────────
const finishVisible = ref(false)
const finishForm = reactive({ sendEvaluation: 1, opinion: '' })

function openFinishDialog() {
  finishForm.sendEvaluation = 1
  finishForm.opinion = ''
  finishVisible.value = true
}

async function handleFinish() {
  opLoading.value = true
  try {
    await finishGovMeeting(applyId, {
      sendEvaluation: finishForm.sendEvaluation,
      opinion: finishForm.opinion || undefined,
    })
    const msg = finishForm.sendEvaluation === 1 ? '已发送评价通知，状态进入"待评价"' : '已直接办结'
    ElMessage.success(msg)
    finishVisible.value = false
    fetchDetail()
  } finally {
    opLoading.value = false
  }
}
</script>

<style scoped>
.detail-page { padding-bottom: 40px; }

.detail-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}
.header-title {
  flex: 1;
  font-size: 16px;
  font-weight: 600;
  color: #333;
  min-width: 0;
}
.apply-no { font-family: monospace; color: #666; font-size: 14px; }
.header-actions { display: flex; gap: 8px; flex-wrap: wrap; }

.detail-card {
  margin-bottom: 16px;
}

.field-label {
  font-size: 13px;
  font-weight: 600;
  color: #555;
  margin-bottom: 6px;
}

.content-body {
  color: #444;
  line-height: 1.8;
  font-size: 14px;
  white-space: pre-wrap;
  background: #f9f9f9;
  padding: 10px 14px;
  border-radius: 4px;
  border: 1px solid #eee;
}

.timeline-card {
  margin-bottom: 0;
  border: none;
  background: #fafafa;
  padding: 10px 14px !important;
}

.timeline-row { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
.tl-operator { font-weight: 600; color: #333; font-size: 14px; }
.tl-dept { color: #888; font-size: 13px; }
.tl-status { font-size: 13px; color: #888; margin: 4px 0; }
.tl-opinion { font-size: 13px; color: #555; margin-top: 4px; }

.record-item {
  padding: 12px;
  background: #fafafa;
  border-radius: 6px;
  margin-bottom: 12px;
  border: 1px solid #eee;
}
.record-meta { font-size: 12px; color: #999; }
</style>
