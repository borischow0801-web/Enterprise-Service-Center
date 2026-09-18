<template>
  <div>
    <div class="page-header">
      <h2>会议室管理</h2>
      <div class="header-actions" v-permission="Permission.MEETING_ROOM_MANAGE">
        <el-button @click="openSpecialDateDialog">配置特殊日期</el-button>
        <el-button @click="openMaterialRulesDialog">申请材料规则配置</el-button>
        <el-button type="primary" @click="openRoomForm(null)">+ 新增会议室</el-button>
      </div>
    </div>

    <!-- 查询区域 -->
    <el-card shadow="never" class="filter-card">
      <el-form :model="params" inline>
        <el-form-item label="区划">
          <el-select v-model="params.regionCode" placeholder="全部" clearable style="width:130px">
            <el-option v-for="r in regionOptions" :key="r.value" :label="r.label" :value="r.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="params.roomType" placeholder="全部" clearable style="width:130px">
            <el-option v-for="t in roomTypeOptions" :key="t.value" :label="t.label" :value="t.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="params.status" placeholder="全部" clearable style="width:110px">
            <el-option label="启用" value="ENABLED" />
            <el-option label="停用" value="DISABLED" />
          </el-select>
        </el-form-item>
        <el-form-item label="最小容量">
          <el-input-number v-model="params.capacityMin" :min="1" :controls="false" placeholder="不限" clearable style="width:90px" />
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
        <el-table-column label="封面" width="70">
          <template #default="{ row }">
            <el-image
              v-if="row.coverImageUrl"
              :src="row.coverImageUrl"
              style="width:48px;height:36px;border-radius:4px;object-fit:cover"
              fit="cover"
              :preview-src-list="[row.coverImageUrl]"
              preview-teleported
            />
            <span v-else style="color:#ccc;font-size:12px">无图</span>
          </template>
        </el-table-column>
        <el-table-column prop="roomName" label="会议室名称" min-width="150" show-overflow-tooltip />
        <el-table-column prop="roomType" label="类型" width="100">
          <template #default="{ row }">{{ roomTypeMap[row.roomType] || row.roomType || '--' }}</template>
        </el-table-column>
        <el-table-column prop="regionName" label="区划" width="90" />
        <el-table-column prop="serviceCenterName" label="服务中心" width="140" show-overflow-tooltip />
        <el-table-column prop="address" label="地址" min-width="160" show-overflow-tooltip />
        <el-table-column prop="capacity" label="容量(人)" width="80" align="center" />
        <el-table-column label="设施" min-width="130">
          <template #default="{ row }">
            <el-tag v-for="f in (row.facilities || [])" :key="f" size="small" style="margin:2px">{{ f }}</el-tag>
            <span v-if="!row.facilities?.length">--</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.status === 'ENABLED' ? 'success' : 'info'" size="small">
              {{ row.status === 'ENABLED' ? '启用' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="240" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" v-permission="Permission.MEETING_ROOM_MANAGE" @click="openRoomForm(row)">编辑</el-button>
            <el-button link :type="row.status === 'ENABLED' ? 'warning' : 'success'" v-permission="Permission.MEETING_ROOM_MANAGE" @click="handleToggleStatus(row)">
              {{ row.status === 'ENABLED' ? '停用' : '启用' }}
            </el-button>
            <el-button link type="primary" @click="openOpenRulesDialog(row)">开放规则</el-button>
            <el-button link type="warning" @click="openOccupyDialog(row)">手工占用</el-button>
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

    <!-- ====== 新增/编辑会议室弹窗 ====== -->
    <el-dialog
      v-model="roomFormVisible"
      :title="currentRoom ? '编辑会议室' : '新增会议室'"
      width="640px"
      :close-on-click-modal="false"
    >
      <el-form :model="roomForm" :rules="roomRules" ref="roomFormRef" label-width="100px">
        <el-form-item label="会议室名称" prop="roomName">
          <el-input v-model="roomForm.roomName" placeholder="请输入会议室名称" />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="roomForm.roomType" placeholder="请选择（可选）" clearable style="width:100%">
            <el-option v-for="t in roomTypeOptions" :key="t.value" :label="t.label" :value="t.value" />
          </el-select>
        </el-form-item>
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="区划" prop="regionCode">
              <el-select v-model="roomForm.regionCode" placeholder="请选择" style="width:100%"
                @change="onRegionChange">
                <el-option v-for="r in regionOptions" :key="r.value" :label="r.label" :value="r.value" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="容量(人)" prop="capacity">
              <el-input-number v-model="roomForm.capacity" :min="1" :controls="false" style="width:100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="所属中心">
          <el-select
            v-model="roomForm.serviceCenterId"
            placeholder="请选择所属中心（可选）"
            clearable
            filterable
            style="width:100%"
            :disabled="!roomForm.regionCode"
            :loading="serviceCenterLoading"
            @change="onServiceCenterChange"
            @clear="clearServiceCenter"
          >
            <el-option
              v-for="center in serviceCenterOptions"
              :key="center.id"
              :label="center.centerName"
              :value="center.id"
            >
              <span>{{ center.centerName }}</span>
              <span style="float:right;color:#909399;font-size:12px">{{ center.regionName }}</span>
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="地址">
          <el-input v-model="roomForm.address" placeholder="详细地址" />
        </el-form-item>
        <el-form-item label="会议室照片">
          <div class="room-images-wrap">
            <div v-for="img in roomForm.images" :key="img.attachmentId" class="room-image-item">
              <el-image :src="img.url" fit="cover" class="room-image-thumb" />
              <div class="room-image-actions">
                <el-tag v-if="img.isCover" type="success" size="small">封面</el-tag>
                <el-button v-else link type="primary" size="small" @click="setCoverImage(img.attachmentId)">设为封面</el-button>
                <el-button link type="danger" size="small" @click="removeRoomImage(img.attachmentId)">删除</el-button>
              </div>
            </div>
            <el-upload
              :show-file-list="false"
              :before-upload="handleRoomImageUpload"
              accept="image/*"
              :disabled="coverUploading"
            >
              <el-button size="small" :loading="coverUploading">上传照片</el-button>
            </el-upload>
          </div>
          <div class="form-tip">{{ MAX_UPLOAD_TIP }}</div>
        </el-form-item>
        <el-form-item label="设施">
          <el-select
            v-model="roomForm.facilities"
            multiple
            filterable
            allow-create
            default-first-option
            placeholder="选择或输入设施（回车添加）"
            style="width:100%"
          >
            <el-option v-for="f in facilityOptions" :key="f.value" :label="f.label" :value="f.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="简介">
          <el-input v-model="roomForm.description" type="textarea" :rows="2" placeholder="会议室简介" />
        </el-form-item>
        <el-form-item label="预约须知">
          <el-input v-model="roomForm.bookingNotice" type="textarea" :rows="3" placeholder="企业预约时显示的须知内容" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="roomFormVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleRoomSubmit">保存</el-button>
      </template>
    </el-dialog>

    <!-- ====== 开放规则弹窗 ====== -->
    <el-dialog
      v-model="openRulesVisible"
      :title="`开放规则配置 - ${currentRoom?.roomName || ''}`"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-alert type="info" :closable="false" show-icon style="margin-bottom:12px">
        周末及节假日是否开放，由此处规则和特殊日期共同控制；特殊日期优先级高于此规则。
      </el-alert>
      <el-table :data="openRules" border>
        <el-table-column label="星期" width="80">
          <template #default="{ row }">{{ weekdayLabel(row.weekday) }}</template>
        </el-table-column>
        <el-table-column label="是否开放" width="100">
          <template #default="{ row }">
            <el-switch v-model="row.openFlag" :active-value="1" :inactive-value="0" />
          </template>
        </el-table-column>
        <el-table-column label="开始时间">
          <template #default="{ row }">
            <el-time-select
              v-model="row.startTime"
              :disabled="!row.openFlag"
              start="07:00"
              step="00:30"
              end="22:00"
              placeholder="开始"
              style="width:100%"
            />
          </template>
        </el-table-column>
        <el-table-column label="结束时间">
          <template #default="{ row }">
            <el-time-select
              v-model="row.endTime"
              :disabled="!row.openFlag"
              start="07:30"
              step="00:30"
              end="23:00"
              placeholder="结束"
              style="width:100%"
            />
          </template>
        </el-table-column>
      </el-table>
      <template #footer>
        <el-button @click="openRulesVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleSaveOpenRules">保存规则</el-button>
      </template>
    </el-dialog>

    <!-- ====== 特殊日期配置弹窗 ====== -->
    <el-dialog v-model="specialDateVisible" title="配置特殊日期" width="480px" :close-on-click-modal="false">
      <el-form :model="specialDateForm" :rules="specialDateRules" ref="specialDateRef" label-width="100px">
        <el-form-item label="区划" prop="regionCode">
          <el-select v-model="specialDateForm.regionCode" placeholder="请选择" style="width:100%"
            @change="(val: string) => { const opt = regionOptions.find(r=>r.value===val); specialDateForm.regionName = opt?.label||'' }">
            <el-option v-for="r in regionOptions" :key="r.value" :label="r.label" :value="r.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="特殊日期" prop="specialDate">
          <el-date-picker v-model="specialDateForm.specialDate" type="date" value-format="YYYY-MM-DD"
            placeholder="请选择日期" style="width:100%" />
        </el-form-item>
        <el-form-item label="日期类型" prop="dateType">
          <el-select v-model="specialDateForm.dateType" placeholder="请选择" style="width:100%">
            <el-option label="法定节假日" value="HOLIDAY" />
            <el-option label="临时关闭" value="TEMP_CLOSE" />
            <el-option label="临时开放" value="TEMP_OPEN" />
          </el-select>
        </el-form-item>
        <el-form-item label="是否开放" prop="openFlag">
          <el-radio-group v-model="specialDateForm.openFlag">
            <el-radio :label="1">开放</el-radio>
            <el-radio :label="0">关闭</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="原因说明">
          <el-input v-model="specialDateForm.reason" placeholder="说明原因（可选）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="specialDateVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleSaveSpecialDate">提交</el-button>
      </template>
    </el-dialog>

    <!-- ====== 手工占用弹窗 ====== -->
    <el-dialog v-model="occupyVisible" :title="`手工占用 - ${currentRoom?.roomName || ''}`" width="480px" :close-on-click-modal="false">
      <el-form :model="occupyForm" :rules="occupyRules" ref="occupyRef" label-width="100px">
        <el-form-item label="占用标题" prop="occupyTitle">
          <el-input v-model="occupyForm.occupyTitle" placeholder="请输入占用标题" />
        </el-form-item>
        <el-form-item label="占用原因">
          <el-input v-model="occupyForm.occupyReason" type="textarea" :rows="2" placeholder="可选" />
        </el-form-item>
        <el-form-item label="开始时间" prop="startTime">
          <el-date-picker v-model="occupyForm.startTime" type="datetime" value-format="YYYY-MM-DDTHH:mm:ss"
            placeholder="请选择开始时间" style="width:100%" />
        </el-form-item>
        <el-form-item label="结束时间" prop="endTime">
          <el-date-picker v-model="occupyForm.endTime" type="datetime" value-format="YYYY-MM-DDTHH:mm:ss"
            placeholder="请选择结束时间" style="width:100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="occupyVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleSaveOccupy">确认占用</el-button>
      </template>
    </el-dialog>

    <!-- ====== 申请材料规则配置弹窗（区划/企服中心级别）====== -->
    <el-dialog v-model="materialRulesVisible" title="申请材料规则配置" width="960px" :close-on-click-modal="false">
      <el-alert type="info" :closable="false" show-icon style="margin-bottom:12px">
        同一区划/企服中心下的所有共享会议室统一使用本材料规则。企业端预约时按区划+企服中心匹配对应材料规则。
      </el-alert>

      <!-- 材料规则筛选 -->
      <div class="mat-filter-bar">
        <el-select v-model="matFilter.regionCode" placeholder="区划" clearable style="width:120px"
          @change="fetchMaterialRules">
          <el-option v-for="r in regionOptions" :key="r.value" :label="r.label" :value="r.value" />
        </el-select>
        <el-input v-model="matFilter.serviceCenterName" placeholder="企服中心名称" clearable style="width:140px"
          @input="fetchMaterialRules" />
        <el-select v-model="matFilter.enterpriseType" placeholder="企业类型" clearable style="width:120px"
          @change="fetchMaterialRules">
          <el-option label="通用" value="" />
          <el-option v-for="t in enterpriseTypeOptions" :key="t.value" :label="t.label" :value="t.value" />
        </el-select>
        <el-select v-model="matFilter.enabled" placeholder="启用状态" clearable style="width:110px"
          @change="fetchMaterialRules">
          <el-option label="启用" :value="1" />
          <el-option label="停用" :value="0" />
        </el-select>
        <el-button type="primary" size="small" v-permission="Permission.MEETING_ROOM_MANAGE" @click="openMaterialRuleForm(null)">+ 新增材料规则</el-button>
      </div>

      <el-table :data="materialRuleList" v-loading="matLoading" border stripe>
        <el-table-column prop="regionName" label="区划" width="90" />
        <el-table-column prop="serviceCenterName" label="企服中心" width="130" show-overflow-tooltip>
          <template #default="{ row }">{{ row.serviceCenterName || '（区划通用）' }}</template>
        </el-table-column>
        <el-table-column prop="materialName" label="材料名称" min-width="130" show-overflow-tooltip />
        <el-table-column prop="materialCode" label="编码" width="180" show-overflow-tooltip />
        <el-table-column prop="enterpriseType" label="企业类型" width="100">
          <template #default="{ row }">{{ row.enterpriseType || '通用' }}</template>
        </el-table-column>
        <el-table-column label="必传" width="60" align="center">
          <template #default="{ row }">
            <el-tag :type="row.requiredFlag ? 'danger' : 'info'" size="small">{{ row.requiredFlag ? '是' : '否' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="sortNo" label="排序" width="60" align="center" />
        <el-table-column prop="description" label="说明" min-width="120" show-overflow-tooltip />
        <el-table-column label="启用" width="60" align="center">
          <template #default="{ row }">
            <el-tag :type="row.enabled ? 'success' : 'info'" size="small">{{ row.enabled ? '是' : '否' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button link type="primary" v-permission="Permission.MEETING_ROOM_MANAGE" @click="openMaterialRuleForm(row)">编辑</el-button>
            <el-button link type="danger" v-permission="Permission.MEETING_ROOM_MANAGE" @click="handleDeleteMaterialRule(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 材料规则新增/编辑内嵌弹窗 -->
      <el-dialog v-model="matFormVisible" :title="currentMaterialRule ? '编辑材料规则' : '新增材料规则'"
        width="520px" :close-on-click-modal="false" append-to-body>
        <el-form :model="matForm" :rules="matRules" ref="matFormRef" label-width="110px">
          <el-row :gutter="12">
            <el-col :span="12">
              <el-form-item label="区划" prop="regionCode">
                <el-select v-model="matForm.regionCode" placeholder="请选择" style="width:100%"
                  @change="(val: string) => { const opt = regionOptions.find(r=>r.value===val); matForm.regionName = opt?.label||'' }">
                  <el-option v-for="r in regionOptions" :key="r.value" :label="r.label" :value="r.value" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="企业类型">
                <el-select v-model="matForm.enterpriseType" placeholder="留空=通用" clearable style="width:100%">
                  <el-option v-for="t in enterpriseTypeOptions" :key="t.value" :label="t.label" :value="t.value" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>
          <el-form-item label="企服中心名称">
            <el-input v-model="matForm.serviceCenterName" placeholder="留空表示该区划所有中心通用" clearable />
          </el-form-item>
          <el-form-item label="材料名称" prop="materialName">
            <el-input v-model="matForm.materialName" placeholder="例：盖章申请表" />
          </el-form-item>
          <el-form-item label="材料编码" prop="materialCode">
            <el-input v-model="matForm.materialCode" placeholder="例：STAMPED_APPLICATION_FORM" />
          </el-form-item>
          <el-row :gutter="12">
            <el-col :span="12">
              <el-form-item label="是否必传" prop="requiredFlag">
                <el-radio-group v-model="matForm.requiredFlag">
                  <el-radio :label="1">必传</el-radio>
                  <el-radio :label="0">非必传</el-radio>
                </el-radio-group>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="排序号">
                <el-input-number v-model="matForm.sortNo" :min="0" :controls="false" style="width:100%" />
              </el-form-item>
            </el-col>
          </el-row>
          <el-form-item label="说明">
            <el-input v-model="matForm.description" type="textarea" :rows="2" placeholder="材料说明（可选）" />
          </el-form-item>
          <el-form-item label="空表模板">
            <div class="template-upload-wrap">
              <div v-if="matForm.templateAttachmentId" class="template-file">
                <span>{{ matForm.templateAttachmentName || `附件ID：${matForm.templateAttachmentId}` }}</span>
                <el-button
                  v-if="matForm.templateDownloadUrl"
                  link
                  type="primary"
                  @click="openTemplateFile"
                >下载</el-button>
                <el-button link type="danger" @click="clearTemplateFile">清空</el-button>
              </div>
              <el-upload
                :show-file-list="false"
                :before-upload="handleTemplateUpload"
                accept=".doc,.docx,.xls,.xlsx,.pdf,.jpg,.jpeg,.png"
                :disabled="templateUploading"
              >
                <el-button size="small" :loading="templateUploading">
                  {{ matForm.templateAttachmentId ? '重新上传空表' : '上传空表' }}
                </el-button>
              </el-upload>
            </div>
            <div class="form-tip">企业端材料清单将显示「下载空表」，支持 Word、Excel、PDF、图片等常见文件。</div>
          </el-form-item>
          <el-form-item v-if="currentMaterialRule" label="启用">
            <el-switch v-model="matForm.enabled" :active-value="1" :inactive-value="0" />
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="matFormVisible = false">取消</el-button>
          <el-button type="primary" :loading="matSubmitLoading" @click="handleMatSubmit">保存</el-button>
        </template>
      </el-dialog>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import type { FormInstance, UploadRawFile } from 'element-plus'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import {
  getMeetingRoomList, getMeetingRoomDetail, createMeetingRoom, updateMeetingRoom,
  getServiceCenterList,
  updateMeetingRoomStatus, updateMeetingRoomOpenRules, getMeetingRoomOpenRules,
  createSpecialDate, createRoomOccupy,
  getMaterialRuleList, createMaterialRule, updateMaterialRule, deleteMaterialRule,
} from '@/api/meetingRoom'
import type { MeetingRoom, OpenRuleItem, MaterialRule, RoomImageItem, ServiceCenter } from '@/api/meetingRoom'
import { getDictionary, uploadAttachment } from '@/api/common'
import { MAX_UPLOAD_TIP, validateFileSize } from '@/constants/upload'
import { Permission } from '@/constants/permission'

// ── 字典选项 ──────────────────────────────────────────────────────────────────
const regionOptions = ref<{value:string;label:string}[]>([])
const roomTypeOptions = ref<{value:string;label:string}[]>([
  { value: 'SMALL', label: '小型会议室' },
  { value: 'MEDIUM', label: '中型会议室' },
  { value: 'LARGE', label: '大型会议室' },
  { value: 'TRAINING', label: '培训室' },
])
const roomTypeMap = ref<Record<string,string>>({
  SMALL: '小型会议室', MEDIUM: '中型会议室', LARGE: '大型会议室', TRAINING: '培训室',
})
const facilityOptions = ref<{value:string;label:string}[]>([
  { value: '投影仪', label: '投影仪' },
  { value: '白板', label: '白板' },
  { value: '视频会议', label: '视频会议' },
  { value: 'WiFi', label: 'WiFi' },
  { value: '电话会议', label: '电话会议' },
  { value: '空调', label: '空调' },
  { value: '停车场', label: '停车场' },
])
const enterpriseTypeOptions = ref<{value:string;label:string}[]>([])
const serviceCenterOptions = ref<ServiceCenter[]>([])
const serviceCenterLoading = ref(false)

onMounted(async () => {
  const [regions, roomTypes, enterpriseTypes] = await Promise.all([
    getDictionary('REGION'),
    getDictionary('MEETING_ROOM_TYPE'),
    getDictionary('ENTERPRISE_TYPE'),
  ])
  if (regions.length) {
    regionOptions.value = regions.map(d => ({ value: d.dictCode, label: d.dictLabel }))
  }
  if (roomTypes.length) {
    roomTypeOptions.value = roomTypes.map(d => ({ value: d.dictCode, label: d.dictLabel }))
    roomTypeMap.value = Object.fromEntries(roomTypes.map(d => [d.dictCode, d.dictLabel]))
  }
  if (enterpriseTypes.length) {
    enterpriseTypeOptions.value = enterpriseTypes.map(d => ({ value: d.dictCode, label: d.dictLabel }))
  }
  fetchList()
})

// ── 列表 ──────────────────────────────────────────────────────────────────────
const loading = ref(false)
const list = ref<MeetingRoom[]>([])
const total = ref(0)
const params = ref({
  regionCode: '',
  status: '',
  roomType: '',
  capacityMin: undefined as number | undefined,
  pageNo: 1,
  pageSize: 10,
})

async function fetchList() {
  loading.value = true
  try {
    const res = await getMeetingRoomList({
      regionCode: params.value.regionCode || undefined,
      status: params.value.status || undefined,
      roomType: params.value.roomType || undefined,
      capacityMin: params.value.capacityMin || undefined,
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
  params.value = { regionCode: '', status: '', roomType: '', capacityMin: undefined, pageNo: 1, pageSize: 10 }
  fetchList()
}

// ── 新增/编辑 ─────────────────────────────────────────────────────────────────
const roomFormVisible = ref(false)
const submitLoading = ref(false)
const currentRoom = ref<MeetingRoom | null>(null)
const roomFormRef = ref<FormInstance>()
const coverUploading = ref(false)
const roomForm = reactive({
  roomName: '',
  roomType: '',
  regionCode: '',
  regionName: '',
  serviceCenterId: undefined as number | undefined,
  serviceCenterName: '',
  address: '',
  capacity: 10,
  facilities: [] as string[],
  description: '',
  bookingNotice: '',
  coverAttachmentId: undefined as number | undefined,
  images: [] as RoomImageItem[],
})
const roomRules = {
  roomName: [{ required: true, message: '请输入会议室名称', trigger: 'blur' }],
  regionCode: [{ required: true, message: '请选择区划', trigger: 'change' }],
  capacity: [{ required: true, message: '请输入容量', trigger: 'blur' }],
}

async function fetchServiceCenters(regionCode?: string) {
  serviceCenterLoading.value = true
  try {
    serviceCenterOptions.value = await getServiceCenterList({ regionCode: regionCode || undefined })
  } finally {
    serviceCenterLoading.value = false
  }
}

async function onRegionChange(val: string) {
  const opt = regionOptions.value.find(r => r.value === val)
  roomForm.regionName = opt?.label || ''
  clearServiceCenter()
  await fetchServiceCenters(val)
}

function onServiceCenterChange(val?: number) {
  const center = serviceCenterOptions.value.find(item => item.id === val)
  roomForm.serviceCenterName = center?.centerName || ''
  if (center) {
    roomForm.regionCode = center.regionCode
    roomForm.regionName = center.regionName
  }
}

function clearServiceCenter() {
  roomForm.serviceCenterId = undefined
  roomForm.serviceCenterName = ''
}

async function openRoomForm(room: MeetingRoom | null) {
  currentRoom.value = room
  if (room) {
    const detail = await getMeetingRoomDetail(room.id)
    await fetchServiceCenters(detail.regionCode)
    const images = (detail.images || []).map(img => ({ ...img }))
    Object.assign(roomForm, {
      roomName: detail.roomName,
      roomType: detail.roomType || '',
      regionCode: detail.regionCode,
      regionName: detail.regionName,
      serviceCenterId: detail.serviceCenterId,
      serviceCenterName: detail.serviceCenterName || '',
      address: detail.address || '',
      capacity: detail.capacity,
      facilities: detail.facilities || [],
      description: detail.description || '',
      bookingNotice: detail.bookingNotice || '',
      coverAttachmentId: detail.coverAttachmentId,
      images,
    })
  } else {
    Object.assign(roomForm, {
      roomName: '', roomType: '', regionCode: '', regionName: '',
      serviceCenterId: undefined, serviceCenterName: '', address: '',
      capacity: 10, facilities: [], description: '', bookingNotice: '',
      coverAttachmentId: undefined, images: [],
    })
    serviceCenterOptions.value = []
  }
  roomFormRef.value?.clearValidate()
  roomFormVisible.value = true
}

async function handleRoomImageUpload(file: UploadRawFile): Promise<false> {
  const err = validateFileSize(file)
  if (err) {
    ElMessage.warning(err)
    return false
  }
  coverUploading.value = true
  try {
    const result = await uploadAttachment(file)
    const url = result.downloadUrl || `/api/common/attachments/${result.id}/download`
    const isFirst = roomForm.images.length === 0
    roomForm.images.push({
      attachmentId: result.id,
      url,
      isCover: isFirst ? 1 : 0,
      sortNo: roomForm.images.length,
    })
    if (isFirst) roomForm.coverAttachmentId = result.id
    ElMessage.success('图片上传成功')
  } catch {
    // error handled by uploadAttachment
  } finally {
    coverUploading.value = false
  }
  return false
}

function setCoverImage(attachmentId: number) {
  roomForm.images.forEach(img => { img.isCover = img.attachmentId === attachmentId ? 1 : 0 })
  roomForm.coverAttachmentId = attachmentId
}

function removeRoomImage(attachmentId: number) {
  roomForm.images = roomForm.images.filter(img => img.attachmentId !== attachmentId)
  if (roomForm.coverAttachmentId === attachmentId) {
    const first = roomForm.images[0]
    if (first) {
      first.isCover = 1
      roomForm.coverAttachmentId = first.attachmentId
    } else {
      roomForm.coverAttachmentId = undefined
    }
  }
}

async function handleRoomSubmit() {
  await roomFormRef.value?.validate()
  submitLoading.value = true
  try {
    const payload = {
      roomName: roomForm.roomName,
      roomType: roomForm.roomType || undefined,
      regionCode: roomForm.regionCode,
      regionName: roomForm.regionName,
      serviceCenterId: roomForm.serviceCenterId ?? null,
      serviceCenterName: roomForm.serviceCenterName || null,
      address: roomForm.address || undefined,
      capacity: roomForm.capacity,
      facilities: roomForm.facilities.length ? roomForm.facilities : undefined,
      description: roomForm.description || undefined,
      bookingNotice: roomForm.bookingNotice || undefined,
      coverAttachmentId: roomForm.coverAttachmentId,
      imageAttachmentIds: roomForm.images.map(img => img.attachmentId),
    }
    if (currentRoom.value) {
      await updateMeetingRoom(currentRoom.value.id, payload)
      ElMessage.success('修改成功')
    } else {
      await createMeetingRoom(payload)
      ElMessage.success('新增成功')
    }
    roomFormVisible.value = false
    fetchList()
  } finally {
    submitLoading.value = false
  }
}

// ── 启用/停用 ─────────────────────────────────────────────────────────────────
async function handleToggleStatus(room: MeetingRoom) {
  const newStatus = room.status === 'ENABLED' ? 'DISABLED' : 'ENABLED'
  const action = newStatus === 'ENABLED' ? '启用' : '停用'
  try {
    await ElMessageBox.confirm(`确定要${action}会议室「${room.roomName}」吗？`, '确认操作', {
      type: 'warning',
    })
  } catch {
    return
  }
  try {
    await updateMeetingRoomStatus(room.id, newStatus)
    ElMessage.success(`${action}成功`)
    fetchList()
  } catch {
    // error handled by interceptor
  }
}

// ── 开放规则 ──────────────────────────────────────────────────────────────────
const openRulesVisible = ref(false)
const openRules = ref<OpenRuleItem[]>([])
const WEEKDAY_NAMES = ['', '周一', '周二', '周三', '周四', '周五', '周六', '周日']
function weekdayLabel(d: number) { return WEEKDAY_NAMES[d] || `周${d}` }

const DEFAULT_RULES: OpenRuleItem[] = [1,2,3,4,5,6,7].map(d => ({
  weekday: d,
  openFlag: d <= 5 ? 1 : 0,
  startTime: d <= 5 ? '09:00' : undefined,
  endTime: d <= 5 ? '18:00' : undefined,
}))

async function openOpenRulesDialog(room: MeetingRoom) {
  currentRoom.value = room
  try {
    const res = await getMeetingRoomOpenRules(room.id)
    if (res.rules && res.rules.length === 7) {
      openRules.value = res.rules.map(r => ({ ...r }))
    } else {
      const rulesMap: Record<number, OpenRuleItem> = {}
      for (const r of (res.rules || [])) rulesMap[r.weekday] = { ...r }
      openRules.value = [1,2,3,4,5,6,7].map(d => rulesMap[d] ?? { ...DEFAULT_RULES[d-1] })
    }
  } catch {
    openRules.value = DEFAULT_RULES.map(r => ({ ...r }))
  }
  openRulesVisible.value = true
}

async function handleSaveOpenRules() {
  for (const rule of openRules.value) {
    if (rule.openFlag && (!rule.startTime || !rule.endTime)) {
      ElMessage.warning(`${weekdayLabel(rule.weekday)}已设为开放，请填写开始和结束时间`)
      return
    }
    if (rule.openFlag && rule.startTime && rule.endTime && rule.startTime >= rule.endTime) {
      ElMessage.warning(`${weekdayLabel(rule.weekday)}结束时间必须大于开始时间`)
      return
    }
  }
  submitLoading.value = true
  try {
    await updateMeetingRoomOpenRules(currentRoom.value!.id, openRules.value)
    ElMessage.success('开放规则保存成功')
    openRulesVisible.value = false
  } finally {
    submitLoading.value = false
  }
}

// ── 特殊日期 ──────────────────────────────────────────────────────────────────
const specialDateVisible = ref(false)
const specialDateRef = ref<FormInstance>()
const specialDateForm = reactive({
  regionCode: '',
  regionName: '',
  specialDate: '',
  dateType: 'HOLIDAY',
  openFlag: 0,
  reason: '',
})
const specialDateRules = {
  regionCode: [{ required: true, message: '请选择区划', trigger: 'change' }],
  specialDate: [{ required: true, message: '请选择日期', trigger: 'change' }],
  dateType: [{ required: true, message: '请选择日期类型', trigger: 'change' }],
}

function openSpecialDateDialog() {
  Object.assign(specialDateForm, { regionCode: '', regionName: '', specialDate: '', dateType: 'HOLIDAY', openFlag: 0, reason: '' })
  specialDateRef.value?.clearValidate()
  specialDateVisible.value = true
}

async function handleSaveSpecialDate() {
  await specialDateRef.value?.validate()
  submitLoading.value = true
  try {
    await createSpecialDate({
      regionCode: specialDateForm.regionCode,
      specialDate: specialDateForm.specialDate,
      dateType: specialDateForm.dateType,
      openFlag: specialDateForm.openFlag,
      reason: specialDateForm.reason || undefined,
    })
    ElMessage.success('特殊日期配置成功')
    specialDateVisible.value = false
  } finally {
    submitLoading.value = false
  }
}

// ── 手工占用 ──────────────────────────────────────────────────────────────────
const occupyVisible = ref(false)
const occupyRef = ref<FormInstance>()
const occupyForm = reactive({
  occupyTitle: '',
  occupyReason: '',
  startTime: '',
  endTime: '',
})
const occupyRules = {
  occupyTitle: [{ required: true, message: '请输入占用标题', trigger: 'blur' }],
  startTime: [{ required: true, message: '请选择开始时间', trigger: 'change' }],
  endTime: [{ required: true, message: '请选择结束时间', trigger: 'change' }],
}

function openOccupyDialog(room: MeetingRoom) {
  currentRoom.value = room
  Object.assign(occupyForm, { occupyTitle: '', occupyReason: '', startTime: '', endTime: '' })
  occupyRef.value?.clearValidate()
  occupyVisible.value = true
}

async function handleSaveOccupy() {
  await occupyRef.value?.validate()
  if (occupyForm.startTime >= occupyForm.endTime) {
    ElMessage.warning('开始时间必须早于结束时间')
    return
  }
  submitLoading.value = true
  try {
    await createRoomOccupy({
      roomId: currentRoom.value!.id,
      occupyTitle: occupyForm.occupyTitle,
      occupyReason: occupyForm.occupyReason || undefined,
      startTime: occupyForm.startTime,
      endTime: occupyForm.endTime,
    })
    ElMessage.success('手工占用登记成功')
    occupyVisible.value = false
  } catch (e: unknown) {
    const err = e as { message?: string }
    if (err?.message?.includes('冲突') || err?.message?.includes('conflict')) {
      ElMessage.error('该时段已被预约或占用，请选择其他时段')
    }
  } finally {
    submitLoading.value = false
  }
}

// ── 材料规则（区划/企服中心级别）────────────────────────────────────────────
const materialRulesVisible = ref(false)
const matLoading = ref(false)
const materialRuleList = ref<MaterialRule[]>([])
const matFilter = reactive({
  regionCode: '',
  serviceCenterName: '',
  enterpriseType: '',
  enabled: undefined as number | undefined,
})
const matFormVisible = ref(false)
const matSubmitLoading = ref(false)
const templateUploading = ref(false)
const currentMaterialRule = ref<MaterialRule | null>(null)
const matFormRef = ref<FormInstance>()
const matForm = reactive({
  regionCode: '',
  regionName: '',
  serviceCenterId: undefined as number | undefined,
  serviceCenterName: '',
  enterpriseType: '',
  materialName: '',
  materialCode: '',
  requiredFlag: 1,
  sortNo: 0,
  templateAttachmentId: undefined as number | undefined,
  templateAttachmentName: '',
  templateDownloadUrl: '',
  description: '',
  enabled: 1,
})
const matRules = {
  regionCode: [{ required: true, message: '请选择区划', trigger: 'change' }],
  materialName: [{ required: true, message: '请输入材料名称', trigger: 'blur' }],
  materialCode: [{ required: true, message: '请输入材料编码', trigger: 'blur' }],
}

function openMaterialRulesDialog() {
  materialRulesVisible.value = true
  fetchMaterialRules()
}

async function fetchMaterialRules() {
  matLoading.value = true
  try {
    materialRuleList.value = await getMaterialRuleList({
      regionCode: matFilter.regionCode || undefined,
      enterpriseType: matFilter.enterpriseType || undefined,
      enabled: matFilter.enabled,
    })
  } finally {
    matLoading.value = false
  }
}

function openMaterialRuleForm(rule: MaterialRule | null) {
  currentMaterialRule.value = rule
  if (rule) {
    Object.assign(matForm, {
      regionCode: rule.regionCode || '',
      regionName: rule.regionName || '',
      serviceCenterId: rule.serviceCenterId,
      serviceCenterName: rule.serviceCenterName || '',
      enterpriseType: rule.enterpriseType || '',
      materialName: rule.materialName,
      materialCode: rule.materialCode,
      requiredFlag: rule.requiredFlag,
      sortNo: rule.sortNo ?? 0,
      templateAttachmentId: rule.templateAttachmentId,
      templateAttachmentName: rule.templateAttachmentName || '',
      templateDownloadUrl: rule.templateDownloadUrl || '',
      description: rule.description || '',
      enabled: rule.enabled,
    })
  } else {
    Object.assign(matForm, {
      regionCode: matFilter.regionCode || '',
      regionName: '',
      serviceCenterId: undefined,
      serviceCenterName: '',
      enterpriseType: '',
      materialName: '',
      materialCode: 'STAMPED_APPLICATION_FORM',
      requiredFlag: 1,
      sortNo: 0,
      templateAttachmentId: undefined,
      templateAttachmentName: '',
      templateDownloadUrl: '',
      description: '',
      enabled: 1,
    })
    // Auto-fill regionName for pre-selected filter
    if (matForm.regionCode) {
      const opt = regionOptions.value.find(r => r.value === matForm.regionCode)
      matForm.regionName = opt?.label || ''
    }
  }
  matFormRef.value?.clearValidate()
  matFormVisible.value = true
}

async function handleTemplateUpload(file: UploadRawFile): Promise<false> {
  const err = validateFileSize(file)
  if (err) {
    ElMessage.warning(err)
    return false
  }
  templateUploading.value = true
  try {
    const result = await uploadAttachment(file)
    matForm.templateAttachmentId = result.id
    matForm.templateAttachmentName = result.originalName
    matForm.templateDownloadUrl = result.downloadUrl || `/api/common/attachments/${result.id}/download`
    ElMessage.success('空表上传成功')
  } finally {
    templateUploading.value = false
  }
  return false
}

function clearTemplateFile() {
  matForm.templateAttachmentId = undefined
  matForm.templateAttachmentName = ''
  matForm.templateDownloadUrl = ''
}

function openTemplateFile() {
  if (matForm.templateDownloadUrl) window.open(matForm.templateDownloadUrl, '_blank')
}

async function handleMatSubmit() {
  await matFormRef.value?.validate()
  matSubmitLoading.value = true
  try {
    if (currentMaterialRule.value) {
      await updateMaterialRule(currentMaterialRule.value.id, {
        regionCode: matForm.regionCode || undefined,
        regionName: matForm.regionName || undefined,
        serviceCenterId: matForm.serviceCenterId,
        serviceCenterName: matForm.serviceCenterName || undefined,
        materialName: matForm.materialName,
        requiredFlag: matForm.requiredFlag,
        sortNo: matForm.sortNo,
        templateAttachmentId: matForm.templateAttachmentId ?? null,
        description: matForm.description || undefined,
        enabled: matForm.enabled,
      })
      ElMessage.success('修改成功')
    } else {
      await createMaterialRule({
        regionCode: matForm.regionCode,
        regionName: matForm.regionName || undefined,
        serviceCenterId: matForm.serviceCenterId,
        serviceCenterName: matForm.serviceCenterName || undefined,
        enterpriseType: matForm.enterpriseType || undefined,
        materialName: matForm.materialName,
        materialCode: matForm.materialCode,
        requiredFlag: matForm.requiredFlag,
        sortNo: matForm.sortNo,
        templateAttachmentId: matForm.templateAttachmentId,
        description: matForm.description || undefined,
      })
      ElMessage.success('新增成功')
    }
    matFormVisible.value = false
    await fetchMaterialRules()
  } finally {
    matSubmitLoading.value = false
  }
}

async function handleDeleteMaterialRule(id: number) {
  try {
    await ElMessageBox.confirm('确定要删除该材料规则吗？', '确认删除', { type: 'warning' })
  } catch {
    return
  }
  try {
    await deleteMaterialRule(id)
    ElMessage.success('删除成功')
    await fetchMaterialRules()
  } catch {
    // error handled by interceptor
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
.mat-filter-bar {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
  margin-bottom: 12px;
}
.room-images-wrap {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}
.template-upload-wrap {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.template-file {
  display: flex;
  align-items: center;
  gap: 8px;
  min-height: 32px;
  padding: 6px 10px;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  background: #fafafa;
}
.template-file span {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.room-image-item {
  width: 120px;
}
.room-image-thumb {
  width: 120px;
  height: 80px;
  border-radius: 6px;
}
.room-image-actions {
  margin-top: 6px;
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  align-items: center;
}
.cover-upload-wrap {
  display: flex;
  align-items: center;
  gap: 10px;
}
.cover-preview {
  width: 120px;
  height: 80px;
  border-radius: 4px;
  border: 1px solid #dcdfe6;
  object-fit: cover;
}
.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}
</style>
