<template>
  <div class="page">
    <van-nav-bar title="提交诉求" left-arrow @click-left="router.back()" fixed />

    <div class="page-body page-body--action">
      <div class="tip-box">
        请如实填写诉求信息，提交后可在「我的诉求」中查看办理进度。
      </div>
      <van-form @submit="handleSubmit">
        <van-cell-group inset title="诉求信息" style="margin-top:12px">
          <van-field
            v-model="form.title"
            name="title"
            label="诉求标题"
            placeholder="请简要描述诉求"
            :rules="[{ required: true, message: '请输入诉求标题' }]"
          />
          <van-field
            v-model="form.content"
            name="content"
            label="诉求内容"
            type="textarea"
            rows="4"
            placeholder="请详细描述诉求内容、期望结果等"
            :rules="[{ required: true, message: '请输入诉求内容' }]"
          />
          <van-field
            v-model="urgencyDisplay"
            name="urgencyLevel"
            label="紧急程度"
            is-link
            readonly
            placeholder="请选择"
            @click="showUrgencyPicker = true"
          />
          <van-popup v-model:show="showUrgencyPicker" position="bottom" round>
            <van-picker
              :columns="urgencyOptions"
              @confirm="onUrgencyConfirm"
              @cancel="showUrgencyPicker = false"
            />
          </van-popup>
        </van-cell-group>

        <van-cell-group inset title="企业信息" style="margin-top:12px">
          <van-field
            name="industryCode"
            label="所属行业"
            is-link
            readonly
            placeholder="请选择（可选）"
            :model-value="industryLabel"
            @click="showIndustryPicker = true"
          />
          <van-popup v-model:show="showIndustryPicker" position="bottom" round>
            <van-picker
              :columns="industryOptions"
              @confirm="onIndustryConfirm"
              @cancel="showIndustryPicker = false"
            />
          </van-popup>

          <van-field
            v-model="regionLabel"
            name="regionCode"
            label="所属区划"
            is-link
            readonly
            placeholder="请选择"
            :rules="[{ required: true, message: '请选择区划', trigger: 'onChange' }]"
            @click="showRegionPicker = true"
          />
          <van-popup v-model:show="showRegionPicker" position="bottom" round>
            <van-picker
              :columns="regionOptions"
              @confirm="onRegionConfirm"
              @cancel="showRegionPicker = false"
            />
          </van-popup>
        </van-cell-group>

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

        <div class="bottom-bar">
          <van-button round block type="primary" native-type="submit" :loading="loading">
            提交诉求
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
import { createAppeal } from '@/api/appeal'
import { getDictionary } from '@/api/common'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()
const loading = ref(false)
const showUrgencyPicker = ref(false)
const showIndustryPicker = ref(false)
const showRegionPicker = ref(false)

const form = ref({
  title: '',
  content: '',
  contactName: authStore.user?.legalPersonName || '',
  contactPhone: (authStore.user as any)?.legalPersonMobile || '',
  urgencyLevel: 'NORMAL',
  urgencyLabel: '普通',
  industryCode: '',
  industryName: '',
  regionCode: '',
  regionName: '',
})

const industryLabel = computed(() => form.value.industryName || '')
const regionLabel = computed(() => form.value.regionName || '')
const urgencyDisplay = computed(() => form.value.urgencyLabel || '普通')

type PickerCol = { text: string; value: string }
const urgencyOptions = ref<PickerCol[]>([])
const industryOptions = ref<PickerCol[]>([])
const regionOptions = ref<PickerCol[]>([])

onMounted(async () => {
  const [urgency, industry, region] = await Promise.all([
    getDictionary('URGENCY_LEVEL'),
    getDictionary('INDUSTRY_TYPE'),
    getDictionary('REGION'),
  ])
  urgencyOptions.value = urgency.length
    ? urgency.map(d => ({ text: d.dictLabel, value: d.dictCode }))
    : [{ text: '普通', value: 'NORMAL' }, { text: '紧急', value: 'URGENT' }]

  industryOptions.value = [
    { text: '不选择', value: '' },
    ...industry.map(d => ({ text: d.dictLabel, value: d.dictCode }))
  ]
  regionOptions.value = region.map(d => ({ text: d.dictLabel, value: d.dictCode }))

  // 默认区划
  if (regionOptions.value.length && !form.value.regionCode) {
    const first = regionOptions.value[0]
    form.value.regionCode = first.value
    form.value.regionName = first.text
  }
})

function onUrgencyConfirm({ selectedOptions }: { selectedOptions: PickerCol[] }) {
  const opt = selectedOptions[0]
  form.value.urgencyLevel = opt.value
  form.value.urgencyLabel = opt.text
  showUrgencyPicker.value = false
}

function onIndustryConfirm({ selectedOptions }: { selectedOptions: PickerCol[] }) {
  const opt = selectedOptions[0]
  form.value.industryCode = opt.value
  form.value.industryName = opt.text === '不选择' ? '' : opt.text
  showIndustryPicker.value = false
}

function onRegionConfirm({ selectedOptions }: { selectedOptions: PickerCol[] }) {
  const opt = selectedOptions[0]
  form.value.regionCode = opt.value
  form.value.regionName = opt.text
  showRegionPicker.value = false
}

async function handleSubmit() {
  if (!form.value.regionCode) {
    showToast('请选择区划')
    return
  }
  loading.value = true
  try {
    await createAppeal({
      title: form.value.title,
      content: form.value.content,
      contactName: form.value.contactName,
      contactPhone: form.value.contactPhone,
      urgencyLevel: form.value.urgencyLevel || undefined,
      industryCode: form.value.industryCode || undefined,
      industryName: form.value.industryName || undefined,
      regionCode: form.value.regionCode,
      regionName: form.value.regionName,
    })
    showSuccessToast('提交成功')
    setTimeout(() => router.replace('/appeals'), 1200)
  } finally {
    loading.value = false
  }
}
</script>
