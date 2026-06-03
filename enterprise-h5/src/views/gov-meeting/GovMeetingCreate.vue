<template>
  <div class="page">
    <van-nav-bar title="发起约见" left-arrow @click-left="router.back()" fixed />

    <div class="page-body page-body--action">
      <div class="tip-box">请如实填写约见申请信息，提交后可在「我的约见」查看进度。</div>
      <van-form @submit="handleSubmit" ref="formRef">

        <!-- 约见需求信息 -->
        <van-cell-group inset title="约见需求信息" style="margin-top:12px">
          <van-field
            :model-value="form.topicName"
            name="topicCode"
            label="约见主题"
            is-link
            readonly
            placeholder="请选择"
            :rules="[{ required: true, message: '请选择约见主题', trigger: 'onChange' }]"
            @click="showTopicPicker = true"
          />
          <van-popup v-model:show="showTopicPicker" position="bottom" round>
            <van-picker :columns="topicOptions" @confirm="onTopicConfirm" @cancel="showTopicPicker = false" />
          </van-popup>

          <van-field
            v-model="form.title"
            name="title"
            label="约见标题"
            placeholder="请简要概括约见申请主题"
            :rules="[{ required: true, message: '请输入约见标题' }]"
            maxlength="100"
          />

          <van-field
            v-model="form.content"
            name="content"
            label="约见内容"
            type="textarea"
            rows="4"
            placeholder="请详细描述约见目的、背景及期望结果"
            :rules="[{ required: true, message: '请输入约见内容' }]"
            maxlength="1000"
            show-word-limit
          />

          <van-field
            v-model="form.discussionItem"
            name="discussionItem"
            label="洽谈事项"
            type="textarea"
            rows="2"
            placeholder="请列举本次约见希望重点讨论的事项（可选）"
            maxlength="500"
          />

          <van-field
            :model-value="urgencyLabel"
            name="urgencyLevel"
            label="紧急程度"
            is-link
            readonly
            placeholder="请选择"
            @click="showUrgencyPicker = true"
          />
          <van-popup v-model:show="showUrgencyPicker" position="bottom" round>
            <van-picker :columns="urgencyOptions" @confirm="onUrgencyConfirm" @cancel="showUrgencyPicker = false" />
          </van-popup>

          <van-field
            :model-value="form.expectedLevelName"
            name="expectedLevelCode"
            label="期望约见层级"
            is-link
            readonly
            placeholder="请选择期望约见的政府层级（可选）"
            @click="showLevelPicker = true"
          />
          <van-popup v-model:show="showLevelPicker" position="bottom" round>
            <van-picker :columns="levelOptions" @confirm="onLevelConfirm" @cancel="showLevelPicker = false" />
          </van-popup>
        </van-cell-group>

        <!-- 企业信息 -->
        <van-cell-group inset title="企业信息" style="margin-top:12px">
          <van-field
            v-model="form.registeredAddress"
            name="registeredAddress"
            label="注册地址"
            placeholder="请输入企业注册地址（可选）"
            maxlength="200"
          />

          <van-field
            :model-value="industryLabel"
            name="industryCode"
            label="所属行业"
            is-link
            readonly
            placeholder="请选择（可选）"
            @click="showIndustryPicker = true"
          />
          <van-popup v-model:show="showIndustryPicker" position="bottom" round>
            <van-picker :columns="industryOptions" @confirm="onIndustryConfirm" @cancel="showIndustryPicker = false" />
          </van-popup>

          <van-field
            :model-value="form.regionName"
            name="regionCode"
            label="所属区划"
            is-link
            readonly
            placeholder="请选择"
            :rules="[{ required: true, message: '请选择区划', trigger: 'onChange' }]"
            @click="showRegionPicker = true"
          />
          <van-popup v-model:show="showRegionPicker" position="bottom" round>
            <van-picker :columns="regionOptions" @confirm="onRegionConfirm" @cancel="showRegionPicker = false" />
          </van-popup>
        </van-cell-group>

        <!-- 联系方式 -->
        <van-cell-group inset title="联系方式" style="margin-top:12px">
          <van-field
            v-model="form.contactName"
            name="contactName"
            label="联系人"
            placeholder="请输入联系人姓名"
            :rules="[{ required: true, message: '请输入联系人' }]"
          />
          <van-field
            v-model="form.contactPhone"
            name="contactPhone"
            label="联系电话"
            type="tel"
            placeholder="请输入手机号"
            :rules="[{ required: true, message: '请输入联系电话' }]"
          />
        </van-cell-group>

        <!-- 附件上传 -->
        <van-cell-group inset title="附件材料（可选）" style="margin-top:12px">
          <div class="upload-wrap">
            <van-uploader
              v-model="fileList"
              multiple
              :max-count="5"
              :max-size="10 * 1024 * 1024"
              :after-read="handleFileUpload"
              @oversize="() => showToast('单个文件不超过10MB')"
            />
            <div class="upload-tip">可上传相关证明材料，支持图片/PDF，单个不超过10MB</div>
          </div>
        </van-cell-group>

        <!-- 承诺书 -->
        <div class="commitment-box">
          <div class="commitment-title">
            <van-icon name="records" color="#1989fa" size="18" />
            承诺声明
          </div>
          <div class="commitment-text">
            本企业承诺：上述所填信息真实、准确、完整，所提交约见事项属于政企约见受理范围，不存在虚假申请或重复申请情形。如有违反，本企业愿承担相应法律责任。
          </div>
          <van-checkbox v-model="commitmentChecked" class="commitment-check">
            我已阅读并同意以上承诺声明
          </van-checkbox>
        </div>

        <div class="bottom-bar">
          <van-button round block type="primary" native-type="submit" :loading="loading">
            提交约见申请
          </van-button>
        </div>
      </van-form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showToast, showSuccessToast } from 'vant'
import type { UploaderFileListItem } from 'vant'
import { createGovMeeting } from '@/api/govMeeting'
import { getDictionary, uploadAttachment } from '@/api/common'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()
const loading = ref(false)
const formRef = ref()
const commitmentChecked = ref(false)
const fileList = ref<UploaderFileListItem[]>([])
const uploadedIds = ref<number[]>([])

const showTopicPicker = ref(false)
const showUrgencyPicker = ref(false)
const showLevelPicker = ref(false)
const showIndustryPicker = ref(false)
const showRegionPicker = ref(false)

const form = ref({
  topicCode: '',
  topicName: '',
  title: '',
  content: '',
  discussionItem: '',
  urgencyLevel: 'NORMAL',
  urgencyName: '普通',
  expectedLevelCode: '',
  expectedLevelName: '',
  registeredAddress: '',
  industryCode: '',
  industryName: '',
  regionCode: '',
  regionName: '',
  contactName: (authStore.user as any)?.legalPersonName || '',
  contactPhone: (authStore.user as any)?.legalPersonMobile || '',
})

type PickerCol = { text: string; value: string }
const topicOptions = ref<PickerCol[]>([])
const urgencyOptions = ref<PickerCol[]>([])
const levelOptions = ref<PickerCol[]>([])
const industryOptions = ref<PickerCol[]>([])
const regionOptions = ref<PickerCol[]>([])

const urgencyLabel = computed(() => form.value.urgencyName || form.value.urgencyLevel || '')
const industryLabel = computed(() => form.value.industryName || '')

onMounted(async () => {
  const [topics, urgency, levels, industry, region] = await Promise.all([
    getDictionary('GOV_MEETING_TOPIC'),
    getDictionary('URGENCY_LEVEL'),
    getDictionary('GOV_MEETING_LEVEL'),
    getDictionary('INDUSTRY_TYPE'),
    getDictionary('REGION'),
  ])

  topicOptions.value = topics.length
    ? topics.map(d => ({ text: d.dictLabel, value: d.dictCode }))
    : [
        { text: '政策咨询', value: 'POLICY_CONSULT' },
        { text: '审批协调', value: 'APPROVAL_COORDINATION' },
        { text: '要素保障', value: 'FACTOR_SUPPORT' },
        { text: '纠纷化解', value: 'DISPUTE_RESOLUTION' },
        { text: '其他', value: 'OTHER' },
      ]

  urgencyOptions.value = urgency.length
    ? urgency.map(d => ({ text: d.dictLabel, value: d.dictCode }))
    : [
        { text: '普通', value: 'NORMAL' },
        { text: '紧急', value: 'URGENT' },
        { text: '非常紧急', value: 'VERY_URGENT' },
      ]

  levelOptions.value = [
    { text: '不指定', value: '' },
    ...(levels.length
      ? levels.map(d => ({ text: d.dictLabel, value: d.dictCode }))
      : [
          { text: '企服中心工作人员', value: 'CENTER_STAFF' },
          { text: '科室负责人', value: 'DEPARTMENT_SECTION' },
          { text: '局处负责人', value: 'DEPARTMENT_LEADER' },
          { text: '区县级领导', value: 'DISTRICT_LEADER' },
          { text: '市级领导', value: 'CITY_LEADER' },
        ]),
  ]

  industryOptions.value = [
    { text: '不选择', value: '' },
    ...industry.map(d => ({ text: d.dictLabel, value: d.dictCode })),
  ]

  regionOptions.value = region.map(d => ({ text: d.dictLabel, value: d.dictCode }))

  if (regionOptions.value.length && !form.value.regionCode) {
    form.value.regionCode = regionOptions.value[0].value
    form.value.regionName = regionOptions.value[0].text
  }
})

function onTopicConfirm({ selectedOptions }: { selectedOptions: PickerCol[] }) {
  const opt = selectedOptions[0]
  form.value.topicCode = opt.value
  form.value.topicName = opt.text
  showTopicPicker.value = false
}

function onUrgencyConfirm({ selectedOptions }: { selectedOptions: PickerCol[] }) {
  const opt = selectedOptions[0]
  form.value.urgencyLevel = opt.value
  form.value.urgencyName = opt.text
  showUrgencyPicker.value = false
}

function onLevelConfirm({ selectedOptions }: { selectedOptions: PickerCol[] }) {
  const opt = selectedOptions[0]
  form.value.expectedLevelCode = opt.value
  form.value.expectedLevelName = opt.value ? opt.text : ''
  showLevelPicker.value = false
}

function onIndustryConfirm({ selectedOptions }: { selectedOptions: PickerCol[] }) {
  const opt = selectedOptions[0]
  form.value.industryCode = opt.value
  form.value.industryName = opt.value ? opt.text : ''
  showIndustryPicker.value = false
}

function onRegionConfirm({ selectedOptions }: { selectedOptions: PickerCol[] }) {
  const opt = selectedOptions[0]
  form.value.regionCode = opt.value
  form.value.regionName = opt.text
  showRegionPicker.value = false
}

async function handleFileUpload(items: UploaderFileListItem | UploaderFileListItem[]) {
  const list = Array.isArray(items) ? items : [items]
  for (const item of list) {
    if (!item.file) continue
    try {
      const result = await uploadAttachment(item.file)
      uploadedIds.value.push(result.id)
      item.status = 'done'
    } catch {
      item.status = 'failed'
      item.message = '上传失败'
    }
  }
}

async function handleSubmit() {
  if (!form.value.topicCode) { showToast('请选择约见主题'); return }
  if (!form.value.regionCode) { showToast('请选择所属区划'); return }
  if (!commitmentChecked.value) { showToast('请勾选承诺声明后提交'); return }

  loading.value = true
  try {
    await createGovMeeting({
      contactName: form.value.contactName,
      contactPhone: form.value.contactPhone,
      topicCode: form.value.topicCode,
      topicName: form.value.topicName,
      expectedLevelCode: form.value.expectedLevelCode || undefined,
      expectedLevelName: form.value.expectedLevelName || undefined,
      title: form.value.title,
      content: form.value.content,
      discussionItem: form.value.discussionItem || undefined,
      urgencyLevel: form.value.urgencyLevel || undefined,
      industryCode: form.value.industryCode || undefined,
      industryName: form.value.industryName || undefined,
      registeredAddress: form.value.registeredAddress || undefined,
      regionCode: form.value.regionCode,
      regionName: form.value.regionName,
      commitmentChecked: 1,
      attachmentIds: uploadedIds.value.length ? uploadedIds.value : undefined,
    })
    showSuccessToast('约见申请已提交，待后台审核')
    setTimeout(() => router.replace('/gov-meetings'), 1500)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.upload-wrap { padding: 12px 16px; }
.upload-tip { font-size: 11px; color: #999; margin-top: 8px; }
.commitment-box {
  background: #fff;
  margin: 12px;
  border-radius: 10px;
  padding: 16px;
  border: 1px solid #e8f4ff;
  box-shadow: 0 1px 6px rgba(0,0,0,0.06);
}
.commitment-title {
  font-size: 15px;
  font-weight: 600;
  color: #333;
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 10px;
}
.commitment-text {
  font-size: 13px;
  color: #555;
  line-height: 1.8;
  background: #f7f8fa;
  border-radius: 6px;
  padding: 10px 12px;
  margin-bottom: 12px;
}
.commitment-check {
  font-size: 13px;
  color: #333;
}
</style>
