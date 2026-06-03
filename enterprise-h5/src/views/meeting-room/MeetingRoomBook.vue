<template>
  <div class="page">
    <van-nav-bar title="预约会议室" left-arrow @click-left="router.back()" fixed />

    <div class="page-body page-body--action">
      <!-- 会议室信息条 -->
      <div class="room-bar" v-if="room">
        <van-icon name="home-o" size="16" color="#1989fa" />
        <span class="room-bar-name">{{ room.roomName || room.room_name }}</span>
        <span class="room-bar-cap">· 容量 {{ room.capacity }} 人</span>
      </div>

      <div class="tip-box">
        <div>① 最晚提前 2 天预约</div>
        <div>② 周末及节假日不开放（特殊安排除外）</div>
        <div>③ 30 分钟起约，单次不超过 4 小时</div>
        <div>④ 取消/变更需至少提前半天通知</div>
        <div>⑤ 爽约累计 2 次后将限制预约资格</div>
      </div>

      <!-- 表单 -->
      <van-cell-group inset style="margin-top:12px">
        <van-field
          v-model="form.meetingSubject"
          label="会议主题"
          placeholder="请输入会议主题"
          required
          :rules="[{required:true,message:'请输入会议主题'}]"
          maxlength="200"
          show-word-limit
        />
        <van-field
          v-model.number="form.participantCount"
          label="使用人数"
          type="number"
          placeholder="参会人数"
          required
          :rules="[{required:true,message:'请输入使用人数'}]"
        />
        <van-field
          v-model="form.contactName"
          label="联系人"
          placeholder="联系人姓名"
          required
          :rules="[{required:true,message:'请输入联系人'}]"
        />
        <van-field
          v-model="form.contactPhone"
          label="联系电话"
          type="tel"
          placeholder="联系人电话"
          required
          :rules="[{required:true,message:'请输入联系电话'}]"
        />
        <van-field
          v-model="enterpriseTypeLabel"
          label="申请主体类型"
          placeholder="请选择申请主体类型"
          readonly
          is-link
          required
          @click="showEnterpriseTypePicker = true"
        />
      </van-cell-group>

      <!-- 时间选择 -->
      <van-cell-group inset style="margin-top:12px" title="预约时间">
        <van-field
          v-model="form.bookingDate"
          label="预约日期"
          placeholder="点击选择日期"
          readonly
          is-link
          required
          @click="showDatePicker = true"
        />
        <van-field
          v-model="form.startTime"
          label="开始时间"
          placeholder="点击选择开始时间"
          readonly
          is-link
          required
          :disabled="!form.bookingDate"
          @click="form.bookingDate && (showStartPicker = true)"
        />
        <van-field
          v-model="form.endTime"
          label="结束时间"
          placeholder="点击选择结束时间"
          readonly
          is-link
          required
          :disabled="!form.startTime"
          @click="form.startTime && (showEndPicker = true)"
        />
      </van-cell-group>

      <div v-if="bookingTimeDisplay" class="tip-box" style="margin:12px">
        已选时间：{{ bookingTimeDisplay }}
      </div>

      <!-- 当日已占用时段 -->
      <div v-if="calendar && form.bookingDate" style="margin:12px 12px 0">
        <div class="section-title">当日已占用时段</div>
        <div v-if="calendarLoading" style="padding:12px 0;text-align:center">
          <van-loading size="20" />
        </div>
        <template v-else>
          <div v-if="allBusySlots.length === 0" class="tip-text">当日暂无占用记录</div>
          <div v-else class="busy-list">
            <van-tag
              v-for="(slot, i) in allBusySlots"
              :key="i"
              type="danger"
              plain
              style="margin:4px"
            >{{ slot }}</van-tag>
          </div>
          <div v-if="dayOpenRule" class="tip-text open-tip">
            <template v-if="dayOpenRule.openFlag || dayOpenRule.open_flag">
              当日开放时段：{{ dayOpenRule.startTime || dayOpenRule.start_time }} - {{ dayOpenRule.endTime || dayOpenRule.end_time }}
            </template>
            <template v-else>
              <span style="color:#ee0a24">当日不开放（可在特殊安排开放时预约）</span>
            </template>
          </div>
        </template>
      </div>

      <!-- 使用物品（来自当前会议室设施） -->
      <van-cell-group inset style="margin-top:12px" title="使用物品（可多选）">
        <div v-if="!hasFacilityOptions" class="tip-box" style="margin:8px 16px">
          该会议室暂无可选配套设施，如有其他需求请在下方填写。
        </div>
        <van-checkbox-group
          v-else
          v-model="form.selectedSupportItems"
          style="padding:10px 16px;display:flex;flex-wrap:wrap;gap:8px"
        >
          <van-checkbox
            v-for="opt in supportFacilityOptions"
            :key="opt.value"
            :name="opt.value"
            shape="square"
            style="width:calc(50% - 4px)"
          >{{ opt.label }}</van-checkbox>
        </van-checkbox-group>
        <van-field
          v-model="form.customSupportItem"
          placeholder="其他需求（选填，可输入白板、激光笔等）"
          @keyup.enter="addCustomItem"
          clearable
        />
        <div v-if="form.customItems.length" style="padding:4px 16px 10px;display:flex;flex-wrap:wrap;gap:6px">
          <van-tag
            v-for="ci in form.customItems"
            :key="ci"
            closeable
            type="primary"
            @close="removeCustomItem(ci)"
          >{{ ci }}</van-tag>
        </div>
      </van-cell-group>

      <!-- 申请材料（按规则动态展示） -->
      <div v-if="form.enterpriseType" style="margin-top:12px">
        <div class="section-title">申请材料</div>
        <div v-if="materialRulesLoading" style="padding:16px;text-align:center">
          <van-loading size="20" />
        </div>
        <div v-else-if="!materialRules.length" class="tip-box" style="margin:12px">
          当前未配置材料规则，请联系管理员。
        </div>
        <div
          v-for="rule in materialRules"
          :key="matCode(rule)"
          class="material-block"
        >
          <div class="material-head">
            <span class="material-name">{{ matName(rule) }}</span>
            <van-tag v-if="matRequired(rule)" type="danger">必传</van-tag>
            <van-button
              v-if="rule.templateDownloadUrl"
              type="primary"
              size="mini"
              plain
              @click="openTemplate(rule.templateDownloadUrl!)"
            >下载模板</van-button>
          </div>
          <div v-if="rule.description" class="tip-text">{{ rule.description }}</div>
          <div
            v-for="f in materialFiles[matCode(rule)] || []"
            :key="f.id"
            class="file-item"
          >
            <van-icon name="description" color="#1989fa" size="18" />
            <span class="file-name">{{ f.originalName }}</span>
            <span class="file-size">{{ formatSize(f.fileSize) }}</span>
            <van-icon name="cross" @click="removeMaterialFile(matCode(rule), f.id)" />
          </div>
          <van-uploader
            :after-read="(item) => handleMaterialUpload(matCode(rule), item)"
            accept=".jpg,.jpeg,.png,.pdf,.doc,.docx"
            :max-size="10 * 1024 * 1024"
            @oversize="showToast('单个文件不能超过10MB')"
            :disabled="fileUploading"
          >
            <van-button icon="plus" size="small" plain type="primary" :loading="fileUploading">
              上传{{ matName(rule) }}
            </van-button>
          </van-uploader>
        </div>
        <div class="tip-text" style="padding:0 16px 8px">{{ MAX_UPLOAD_TIP }}</div>
      </div>
      <div v-else class="tip-box" style="margin:12px">请先选择申请主体类型，系统将展示需上传的材料清单。</div>

      <div class="bottom-bar">
        <van-button
          type="primary"
          round
          block
          size="large"
          :loading="submitting"
          @click="handleSubmit"
        >提交预约申请</van-button>
      </div>
    </div>

    <!-- 日期选择 popup -->
    <van-popup v-model:show="showDatePicker" position="bottom" round>
      <van-date-picker
        v-model="pickerDate"
        title="选择预约日期"
        :min-date="minDate"
        :max-date="maxDate"
        @confirm="onDateConfirm"
        @cancel="showDatePicker = false"
      />
    </van-popup>

    <!-- 开始时间 popup -->
    <van-popup v-model:show="showStartPicker" position="bottom" round>
      <van-picker
        :columns="startTimeOptions"
        title="选择开始时间"
        @confirm="onStartTimeConfirm"
        @cancel="showStartPicker = false"
      />
    </van-popup>

    <!-- 申请主体类型 -->
    <van-popup v-model:show="showEnterpriseTypePicker" position="bottom" round>
      <van-picker
        :columns="enterpriseTypeOptions"
        title="选择申请主体类型"
        @confirm="onEnterpriseTypeConfirm"
        @cancel="showEnterpriseTypePicker = false"
      />
    </van-popup>

    <!-- 结束时间 popup -->
    <van-popup v-model:show="showEndPicker" position="bottom" round>
      <van-picker
        :columns="endTimeOptions"
        title="选择结束时间"
        @confirm="onEndTimeConfirm"
        @cancel="showEndPicker = false"
      />
    </van-popup>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { showToast } from 'vant'
import type { UploaderFileListItem } from 'vant'
import {
  getMeetingRoomDetail, getMeetingRoomCalendar, createMeetingBooking,
  getMeetingRoomMaterialRules, matName, matRequired, matCode,
} from '@/api/meetingRoom'
import type { MeetingRoom, RoomCalendar, OpenRule, MaterialRule } from '@/api/meetingRoom'
import { uploadAttachment, getDictionary } from '@/api/common'
import { apiAssetUrl } from '@/utils/api'
import { MAX_UPLOAD_TIP, validateFileSize } from '@/constants/upload'
import { buildSupportItems, normalizeFacilities } from '@/utils/format'
import { loadFacilityLabelMap, facilityDisplayLabel } from '@/utils/facility'

const router = useRouter()
const route = useRoute()
const roomId = Number(route.params.id)

const room = ref<MeetingRoom | null>(null)
const calendar = ref<RoomCalendar | null>(null)
const calendarLoading = ref(false)

// ── Date/time pickers ──────────────────────────────────────────────────────
const showDatePicker = ref(false)
const showStartPicker = ref(false)
const showEndPicker = ref(false)
const pickerDate = ref<string[]>([])

// min date = day after tomorrow (2 days in advance)
const now = new Date()
const minDate = new Date(now.getTime() + 2 * 24 * 60 * 60 * 1000)
const maxDate = new Date(now.getTime() + 90 * 24 * 60 * 60 * 1000)

// ── Form ───────────────────────────────────────────────────────────────────
const form = reactive({
  meetingSubject: '',
  participantCount: undefined as number | undefined,
  contactName: '',
  contactPhone: '',
  enterpriseType: '',
  bookingDate: '',
  startTime: '',
  endTime: '',
  selectedSupportItems: [] as string[],
  customSupportItem: '',
  customItems: [] as string[],
})

const showEnterpriseTypePicker = ref(false)
const enterpriseTypeOptions = ref<{ text: string; value: string }[]>([])
const enterpriseTypeLabel = computed(() => {
  const opt = enterpriseTypeOptions.value.find(o => o.value === form.enterpriseType)
  return opt?.text || ''
})

const materialRules = ref<MaterialRule[]>([])
const materialRulesLoading = ref(false)
const materialFiles = ref<Record<string, { id: number; originalName: string; fileSize: number }[]>>({})

const facilityLabelMap = ref<Record<string, string>>({})

const supportFacilityOptions = computed(() => {
  const codes = normalizeFacilities(room.value?.facilities)
  return codes.map(value => ({
    value,
    label: facilityDisplayLabel(value, facilityLabelMap.value),
  }))
})

const hasFacilityOptions = computed(() => supportFacilityOptions.value.length > 0)

const bookingTimeDisplay = computed(() => {
  if (!form.bookingDate || !form.startTime || !form.endTime) return ''
  return `${form.bookingDate} ${form.startTime} 至 ${form.endTime}`
})

function addCustomItem() {
  const v = form.customSupportItem.trim()
  if (v && !form.customItems.includes(v)) form.customItems.push(v)
  form.customSupportItem = ''
}
function removeCustomItem(item: string) {
  form.customItems = form.customItems.filter(c => c !== item)
}

// ── Upload ─────────────────────────────────────────────────────────────────
const fileUploading = ref(false)

async function loadMaterialRules() {
  if (!form.enterpriseType) {
    materialRules.value = []
    materialFiles.value = {}
    return
  }
  materialRulesLoading.value = true
  try {
    materialRules.value = await getMeetingRoomMaterialRules(roomId, {
      enterpriseType: form.enterpriseType,
    })
    const next: Record<string, { id: number; originalName: string; fileSize: number }[]> = {}
    for (const r of materialRules.value) {
      const code = matCode(r)
      if (code) next[code] = materialFiles.value[code] || []
    }
    materialFiles.value = next
  } catch {
    materialRules.value = []
  } finally {
    materialRulesLoading.value = false
  }
}

async function handleMaterialUpload(
  materialCode: string,
  items: UploaderFileListItem | UploaderFileListItem[],
) {
  const itemList = Array.isArray(items) ? items : [items]
  for (const item of itemList) {
    if (!item.file) continue
    const sizeErr = validateFileSize(item.file)
    if (sizeErr) { showToast(sizeErr); continue }
    fileUploading.value = true
    try {
      const result = await uploadAttachment(item.file)
      const prev = materialFiles.value[materialCode] || []
      materialFiles.value = {
        ...materialFiles.value,
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
      fileUploading.value = false
    }
  }
}

function removeMaterialFile(materialCode: string, id: number) {
  materialFiles.value = {
    ...materialFiles.value,
    [materialCode]: (materialFiles.value[materialCode] || []).filter(f => f.id !== id),
  }
}

function openTemplate(url: string) {
  window.open(apiAssetUrl(url), '_blank')
}

function onEnterpriseTypeConfirm(payload: {
  selectedOptions?: { text: string; value: string }[]
  selectedValues?: string[]
}) {
  const opt = payload.selectedOptions?.[0]
  const val = opt?.value ?? payload.selectedValues?.[0]
  if (val) {
    form.enterpriseType = String(val)
    materialFiles.value = {}
    loadMaterialRules()
  } else {
    showToast('请选择申请主体类型')
  }
  showEnterpriseTypePicker.value = false
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes}B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)}KB`
  return `${(bytes / 1024 / 1024).toFixed(1)}MB`
}

// ── Calendar ───────────────────────────────────────────────────────────────
const dayOpenRule = computed<OpenRule | null>(() => {
  if (!calendar.value || !form.bookingDate) return null
  const date = new Date(form.bookingDate)
  // getDay: 0=Sunday, 1=Monday ... 6=Saturday → convert to 1=Mon..7=Sun
  const jsDay = date.getDay()
  const weekday = jsDay === 0 ? 7 : jsDay
  // Check special date first
  const special = calendar.value.specialDates.find(s => s.date === form.bookingDate)
  if (special) {
    const rule = calendar.value.openRules.find(r => r.weekday === weekday)
    return { weekday, openFlag: special.openFlag, startTime: rule?.startTime, endTime: rule?.endTime }
  }
  return calendar.value.openRules.find(r => r.weekday === weekday) || null
})

const allBusySlots = computed(() => {
  if (!calendar.value) return []
  const slots: string[] = []
  for (const b of calendar.value.bookedSlots) {
    slots.push(`${fmtTime(b.startTime)}-${fmtTime(b.endTime)} (已预约)`)
  }
  for (const o of calendar.value.occupiedSlots) {
    slots.push(`${fmtTime(o.startTime)}-${fmtTime(o.endTime)} (已占用)`)
  }
  return slots
})

function fmtTime(iso: string): string {
  if (!iso) return ''
  const d = new Date(iso)
  if (isNaN(d.getTime())) return iso.slice(11, 16)
  return `${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`
}

// Generate 30-min time slots
function generateSlots(startHour = 7, endHour = 22): string[] {
  const slots: string[] = []
  for (let h = startHour; h <= endHour; h++) {
    for (const m of [0, 30]) {
      if (h === endHour && m > 0) break
      slots.push(`${String(h).padStart(2,'0')}:${String(m).padStart(2,'0')}`)
    }
  }
  return slots
}

const allTimeSlots = generateSlots(7, 22)

const startTimeOptions = computed(() => {
  const rule = dayOpenRule.value
  if (rule && (rule.openFlag || rule.open_flag) && rule.startTime) {
    const openStart = rule.startTime
    const openEnd = rule.endTime || '22:00'
    return allTimeSlots.filter(t => t >= openStart && t < openEnd).map(t => ({ text: t, value: t }))
  }
  return allTimeSlots.map(t => ({ text: t, value: t }))
})

const endTimeOptions = computed(() => {
  if (!form.startTime) return allTimeSlots.map(t => ({ text: t, value: t }))
  // end must be at least 30min after start, and max 4h
  const [sh, sm] = form.startTime.split(':').map(Number)
  const startMinutes = sh * 60 + sm
  const minEnd = startMinutes + 30
  const maxEnd = startMinutes + 240
  const rule = dayOpenRule.value
  let openEndMinutes = 22 * 60
  if (rule && (rule.openFlag || rule.open_flag) && rule.endTime) {
    const [eh, em] = rule.endTime.split(':').map(Number)
    openEndMinutes = eh * 60 + em
  }
  return allTimeSlots
    .filter(t => {
      const [h, m] = t.split(':').map(Number)
      const mins = h * 60 + m
      return mins >= minEnd && mins <= Math.min(maxEnd, openEndMinutes)
    })
    .map(t => ({ text: t, value: t }))
})

function timeToMinutes(t: string): number {
  const [h, m] = t.split(':').map(Number)
  return h * 60 + m
}

function rangesOverlap(s1: number, e1: number, s2: number, e2: number): boolean {
  return s1 < e2 && e1 > s2
}

function validateSelectedTime(): boolean {
  if (!form.bookingDate || !form.startTime || !form.endTime) return true
  const startM = timeToMinutes(form.startTime)
  const endM = timeToMinutes(form.endTime)
  if (endM <= startM) {
    showToast('预约开始时间必须早于结束时间。')
    return false
  }
  const duration = endM - startM
  if (duration < 30) {
    showToast('预约时长不能少于 30 分钟。')
    return false
  }
  if (duration > 240) {
    showToast('单次预约不能超过 4 小时。')
    return false
  }
  const rule = dayOpenRule.value
  if (rule && (rule.openFlag || rule.open_flag)) {
    const openStart = rule.startTime || rule.start_time || '07:00'
    const openEnd = rule.endTime || rule.end_time || '22:00'
    const os = timeToMinutes(openStart)
    const oe = timeToMinutes(openEnd)
    if (startM < os || endM > oe) {
      showToast('当前选择不在会议室开放时间内。')
      return false
    }
  } else if (rule) {
    showToast('当前选择不在会议室开放时间内。')
    return false
  }
  if (calendar.value) {
    for (const b of calendar.value.bookedSlots) {
      const bs = timeToMinutes(fmtTime(b.startTime))
      const be = timeToMinutes(fmtTime(b.endTime))
      if (rangesOverlap(startM, endM, bs, be)) {
        showToast('该时段已被预约或占用，请重新选择。')
        return false
      }
    }
    for (const o of calendar.value.occupiedSlots) {
      const os = timeToMinutes(fmtTime(o.startTime))
      const oe = timeToMinutes(fmtTime(o.endTime))
      if (rangesOverlap(startM, endM, os, oe)) {
        showToast('该时段已被预约或占用，请重新选择。')
        return false
      }
    }
  }
  return true
}

// ── Date confirm ───────────────────────────────────────────────────────────
async function onDateConfirm({ selectedValues }: { selectedValues: string[] }) {
  const dateStr = selectedValues.join('-')
  const d = new Date(dateStr)
  const wd = d.getDay()
  if (wd === 0 || wd === 6) {
    showToast('周末不开放预约，请选择工作日。')
    showDatePicker.value = false
    return
  }
  form.bookingDate = dateStr
  form.startTime = ''
  form.endTime = ''
  showDatePicker.value = false
  calendarLoading.value = true
  try {
    calendar.value = await getMeetingRoomCalendar(roomId, {
      startDate: form.bookingDate,
      endDate: form.bookingDate,
    })
    const special = calendar.value?.specialDates?.find(s => s.date === form.bookingDate)
    if (special && !special.openFlag) {
      showToast('该日期为节假日或特殊关闭日，不可预约。')
      form.bookingDate = ''
      calendar.value = null
      return
    }
    const rule = dayOpenRule.value
    if (rule && !(rule.openFlag || rule.open_flag)) {
      const hasSpecialOpen = special && special.openFlag === 1
      if (!hasSpecialOpen) {
        showToast('该日期不可预约，请选择其他日期。')
        form.bookingDate = ''
        calendar.value = null
      }
    }
  } catch {
    calendar.value = null
  } finally {
    calendarLoading.value = false
  }
}

function pickTimeValue(payload: { selectedValues?: string[]; selectedOptions?: { value?: string; text?: string }[] }): string {
  const opt = payload.selectedOptions?.[0]
  const raw = opt?.value ?? opt?.text ?? payload.selectedValues?.[0]
  return typeof raw === 'string' ? raw : String(raw ?? '')
}

function onStartTimeConfirm(payload: { selectedValues?: string[]; selectedOptions?: { value?: string; text?: string }[] }) {
  form.startTime = pickTimeValue(payload)
  form.endTime = ''
  showStartPicker.value = false
}

function onEndTimeConfirm(payload: { selectedValues?: string[]; selectedOptions?: { value?: string; text?: string }[] }) {
  form.endTime = pickTimeValue(payload)
  showEndPicker.value = false
  validateSelectedTime()
}

function formatSubmitDateTime(dateStr: string, timeStr: string): string {
  const t = timeStr.length === 5 ? `${timeStr}:00` : timeStr
  return `${dateStr} ${t}`
}

// ── Submit ─────────────────────────────────────────────────────────────────
const submitting = ref(false)

async function handleSubmit() {
  if (!form.meetingSubject.trim()) { showToast('请输入会议主题'); return }
  if (!form.participantCount || form.participantCount < 1) { showToast('请输入使用人数'); return }
  if (!form.contactName.trim()) { showToast('请输入联系人'); return }
  if (!form.contactPhone.trim()) { showToast('请输入联系电话'); return }
  if (!form.bookingDate) { showToast('请选择预约日期'); return }
  if (!form.startTime) { showToast('请选择开始时间'); return }
  if (!form.endTime) { showToast('请选择结束时间'); return }
  if (!form.enterpriseType) { showToast('请选择申请主体类型'); return }
  if (!validateSelectedTime()) return

  const missing: string[] = []
  for (const rule of materialRules.value) {
    const code = matCode(rule)
    if (matRequired(rule) && code && !(materialFiles.value[code]?.length)) {
      missing.push(matName(rule))
    }
  }
  if (missing.length) {
    showToast(`请上传必传材料：${missing.join('、')}`)
    return
  }

  const startDateTime = formatSubmitDateTime(form.bookingDate, form.startTime)
  const endDateTime = formatSubmitDateTime(form.bookingDate, form.endTime)
  const selectedLabels = form.selectedSupportItems.map(
    v => facilityDisplayLabel(v, facilityLabelMap.value),
  )
  const supportItems = buildSupportItems(
    selectedLabels,
    form.customItems,
    form.customSupportItem,
  )

  const materials = materialRules.value
    .map(rule => {
      const code = matCode(rule)
      return {
        materialCode: code,
        materialName: matName(rule),
        attachmentIds: (materialFiles.value[code] || []).map(f => f.id),
      }
    })
    .filter(m => m.materialCode && m.attachmentIds.length > 0)

  const allIds = materials.flatMap(m => m.attachmentIds)

  const payload = {
    roomId,
    meetingSubject: form.meetingSubject.trim(),
    participantCount: Number(form.participantCount),
    contactName: form.contactName.trim(),
    contactPhone: form.contactPhone.trim(),
    enterpriseType: form.enterpriseType,
    startTime: startDateTime,
    endTime: endDateTime,
    supportItems: supportItems.length ? supportItems : undefined,
    materials,
    attachmentIds: allIds.length ? allIds : undefined,
  }

  if (import.meta.env.DEV) {
    console.debug('[MeetingBook] submit payload', {
      enterpriseType: form.enterpriseType,
      materialRules: materialRules.value.map(r => matCode(r)),
      materialFiles: materialFiles.value,
      materials,
      attachmentIds: allIds,
      payload,
    })
  }

  submitting.value = true
  try {
    await createMeetingBooking({
      ...payload,
    })
    showToast({ message: '预约申请已提交，待后台审核', duration: 2000 })
    setTimeout(() => router.push('/meeting-bookings'), 1500)
  } catch (e: unknown) {
    const err = e as { message?: string }
    if (err?.message?.includes('40902') || err?.message?.includes('冲突') || err?.message?.includes('占用')) {
      showToast('该时段已被预约或占用，请重新选择')
    }
    // other errors handled by interceptor
  } finally {
    submitting.value = false
  }
}

// ── Init ───────────────────────────────────────────────────────────────────
onMounted(async () => {
  facilityLabelMap.value = await loadFacilityLabelMap()
  try {
    room.value = await getMeetingRoomDetail(roomId)
    form.selectedSupportItems = form.selectedSupportItems.filter(
      v => normalizeFacilities(room.value?.facilities).includes(v),
    )
  } catch {
    room.value = null
  }
  const types = await getDictionary('ENTERPRISE_TYPE')
  enterpriseTypeOptions.value = types.map(t => ({ text: t.dictLabel, value: t.dictCode }))
})
</script>

<style scoped>
.room-bar {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 16px;
  background: #ecf5ff;
  font-size: 13px;
}
.room-bar-name { font-weight: 600; color: #333; }
.room-bar-cap { color: #888; }
.rules-text { font-size: 12px; line-height: 2; }
.section-title {
  font-size: 14px;
  font-weight: 600;
  color: #333;
  padding: 8px 16px 4px;
}
.busy-list { padding: 6px 0; }
.tip-text { font-size: 12px; color: #888; padding: 6px 0; }
.open-tip { color: #07c160; }
.material-block {
  margin: 8px 12px 12px;
  padding: 10px 12px;
  background: #f7f8fa;
  border-radius: 8px;
}
.material-head {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 6px;
}
.material-name { font-weight: 600; font-size: 14px; flex: 1; }
.file-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 0;
  border-bottom: 1px solid #f5f5f5;
}
.file-name { flex: 1; font-size: 13px; color: #333; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.file-size { font-size: 12px; color: #999; flex-shrink: 0; }
</style>
