<template>
  <div class="page">
    <van-nav-bar title="约见评价" left-arrow @click-left="router.back()" fixed />

    <div class="page-body page-body--action">
      <div class="eval-intro">
        <van-icon name="good-job-o" size="32" color="#1989fa" />
        <div>
          <div class="intro-title">请对本次政企约见服务进行评价</div>
          <div class="intro-sub">您的评价将帮助我们持续提升服务质量</div>
        </div>
      </div>

      <van-cell-group inset>
        <!-- 满意度 -->
        <div class="eval-section">
          <div class="eval-label">满意度 <span class="required">*</span></div>
          <div class="satisfaction-btns">
            <div
              v-for="opt in satisfactionOptions"
              :key="opt.value"
              class="sat-btn"
              :class="{ active: form.satisfaction === opt.value }"
              :style="form.satisfaction === opt.value ? { background: opt.color, borderColor: opt.color, color: '#fff' } : {}"
              @click="form.satisfaction = opt.value"
            >
              {{ opt.emoji }} {{ opt.label }}
            </div>
          </div>
        </div>

        <!-- 星级评分 -->
        <div class="eval-section">
          <div class="eval-label">星级评分 <span class="required">*</span></div>
          <van-rate v-model="form.score" size="32" color="#ffd21e" void-icon="star" void-color="#eee" />
          <span class="score-text">{{ scoreText }}</span>
        </div>

        <!-- 是否解决主要诉求 -->
        <div class="eval-section">
          <div class="eval-label">是否解决主要诉求 <span class="required">*</span></div>
          <van-radio-group v-model="form.resolvedFlag" direction="horizontal">
            <van-radio :name="1">已解决</van-radio>
            <van-radio :name="0">未解决</van-radio>
          </van-radio-group>
        </div>

        <!-- 评价意见 -->
        <div class="eval-section">
          <div class="eval-label">评价意见（可选）</div>
          <van-field
            v-model="form.comment"
            type="textarea"
            rows="3"
            placeholder="请输入您对本次约见的意见和建议"
            :border="false"
            maxlength="500"
            show-word-limit
          />
        </div>
      </van-cell-group>

      <div class="bottom-bar">
        <van-button type="primary" round block :loading="loading" @click="handleSubmit">
          提交评价
        </van-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showToast, showSuccessToast } from 'vant'
import { evaluateGovMeeting } from '@/api/govMeeting'

const route = useRoute()
const router = useRouter()
const loading = ref(false)

const form = ref({
  satisfaction: 'SATISFIED',
  score: 5,
  resolvedFlag: 1 as 0 | 1,
  comment: '',
})

const satisfactionOptions = [
  { value: 'SATISFIED', label: '满意', emoji: '😊', color: '#07c160' },
  { value: 'BASIC_SATISFIED', label: '基本满意', emoji: '🙂', color: '#ff976a' },
  { value: 'UNSATISFIED', label: '不满意', emoji: '😞', color: '#ee0a24' },
]

const scoreText = computed(() => {
  const texts = ['', '很差', '较差', '一般', '较好', '很好']
  return texts[form.value.score] || ''
})

async function handleSubmit() {
  if (!form.value.satisfaction) { showToast('请选择满意度'); return }
  if (!form.value.score) { showToast('请进行星级评分'); return }
  loading.value = true
  try {
    await evaluateGovMeeting(Number(route.params.id), {
      satisfaction: form.value.satisfaction,
      score: form.value.score,
      resolvedFlag: form.value.resolvedFlag,
      comment: form.value.comment || undefined,
    })
    showSuccessToast('评价成功，感谢您的反馈！')
    setTimeout(() => router.replace(`/gov-meetings/${route.params.id}`), 1500)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.eval-intro {
  display: flex;
  align-items: center;
  gap: 14px;
  background: #e8f4ff;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 16px;
  .intro-title { font-size: 15px; font-weight: 600; color: #1989fa; margin-bottom: 4px; }
  .intro-sub { font-size: 12px; color: #888; }
}
.eval-section {
  padding: 16px;
  border-bottom: 1px solid #f5f5f5;
  &:last-child { border-bottom: none; }
}
.eval-label {
  font-size: 14px;
  font-weight: 500;
  color: #333;
  margin-bottom: 12px;
}
.required { color: #ee0a24; }
.satisfaction-btns {
  display: flex;
  gap: 10px;
}
.sat-btn {
  flex: 1;
  padding: 12px 6px;
  border: 1.5px solid #eee;
  border-radius: 8px;
  text-align: center;
  font-size: 13px;
  color: #666;
  cursor: pointer;
  transition: all 0.2s;
  &.active { font-weight: 500; }
}
.score-text {
  margin-left: 12px;
  font-size: 13px;
  color: #ffc107;
  font-weight: 500;
}
</style>
