<template>
  <div class="page">
    <van-nav-bar title="共享会议室预约使用管理制度" left-arrow @click-left="goBack" fixed />

    <div class="page-body">
      <div class="rules-content">
        <section v-for="(sec, idx) in sections" :key="idx" class="rule-section">
          <h3 class="rule-title">{{ sec.title }}</h3>
          <p v-for="(p, pi) in sec.paragraphs" :key="pi" class="rule-p">{{ p }}</p>
        </section>
      </div>

      <div class="bottom-bar">
        <van-button type="primary" round block size="large" @click="goBack">我已阅读</van-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()

const sections = [
  {
    title: '一、开放范围',
    paragraphs: [
      '威海市（环翠区）企业综合服务中心免费对外开放共享会议室，包括一楼一号会议室、多功能厅，五楼政企会客厅、营商环境活动大厅等。',
    ],
  },
  {
    title: '二、开放时间',
    paragraphs: [
      '会议室使用原则上限定于工作日上班时间，上午 8:30-11:30，下午 13:30-17:30。',
      '周末及节假日不可预约。建议活动开始时间定于中心上班 30 分钟后。',
    ],
  },
  {
    title: '三、预约方式',
    paragraphs: [
      '各企业、社会组织和机关事业单位如有使用需求，应提前 2 个工作日提出预约。',
      '预约时应选择使用时间，并按要求提交材料，审核通过后方可使用。',
    ],
  },
  {
    title: '四、预约材料',
    paragraphs: [
      '申请人需提交会议室使用申请表、活动方案、申请人身份证信息等材料。',
      '不同主体应按要求提交相应资质证明，例如营业执照、民办非企业登记证书、办学许可证、医疗机构执业许可证、基金会法人登记证书、社会团体登记证书等。',
    ],
  },
  {
    title: '五、取消或变更预约',
    paragraphs: [
      '预约会议室如需取消或变更，至少提前半天通知企业服务中心工作人员。',
      '未取消预约或未按预约时间使用会议室的，视为爽约；累计爽约两次，该单位不再享受预约服务资格。',
    ],
  },
  {
    title: '六、使用要求',
    paragraphs: [
      '不得在会议室内从事违法违规行为，不得干扰正常办公和企业群众办事。',
      '活动现场不得举办食品、保健品、药品等销售活动。',
    ],
  },
  {
    title: '七、设备与会场管理',
    paragraphs: [
      '如需提前布置会场，应在审核通过后进行。使用外接设备前应做好病毒查杀。',
      '会议所需物资、引导人员和服务人员由申请方自备。',
    ],
  },
  {
    title: '八、环境与设施维护',
    paragraphs: [
      '会议室内禁止吸烟和乱扔纸屑，不得损坏设备设施。',
      '使用结束后应清理会场、关闭设备并通知工作人员。',
    ],
  },
  {
    title: '九、违规处理',
    paragraphs: [
      '对于违反规定的单位和个人，会议室管理部门有权警告、限制预约或取消预约资格。',
    ],
  },
]

function goBack() {
  router.back()
}
</script>

<style scoped>
.page-body {
  padding: 56px 16px 88px;
  min-height: 100vh;
  background: #f7f8fa;
}
.rules-content {
  background: #fff;
  border-radius: 8px;
  padding: 16px;
}
.rule-section {
  margin-bottom: 20px;
}
.rule-section:last-child {
  margin-bottom: 0;
}
.rule-title {
  font-size: 16px;
  font-weight: 600;
  color: #323233;
  margin: 0 0 10px;
}
.rule-p {
  font-size: 14px;
  color: #646566;
  line-height: 1.75;
  margin: 0 0 8px;
}
.rule-p:last-child {
  margin-bottom: 0;
}
</style>
