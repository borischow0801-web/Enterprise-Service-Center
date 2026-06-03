<template>
  <div class="page">
    <van-nav-bar title="政企约见" left-arrow @click-left="router.push('/home')" fixed />

    <div class="page-body page-body--action">
      <!-- 标题横幅 -->
      <div class="notice-banner">
        <van-icon name="shield-o" size="32" color="#fff" />
        <div class="banner-title">政企约见服务须知</div>
        <div class="banner-sub">请认真阅读以下内容，了解政企约见流程和要求</div>
      </div>

      <!-- 须知内容 -->
      <div class="notice-body">
        <div class="notice-section" v-for="sec in sections" :key="sec.title">
          <div class="sec-title">
            <span class="sec-icon">{{ sec.icon }}</span>
            {{ sec.title }}
          </div>
          <div class="sec-content">
            <div v-for="(item, i) in sec.items" :key="i" class="sec-item">
              <span class="bullet">·</span>
              <span>{{ item }}</span>
            </div>
          </div>
        </div>

        <!-- 承诺提示 -->
        <div class="commitment-tip">
          <van-icon name="info-o" color="#ff976a" size="16" />
          <span>提交申请即表示您已阅读并同意本须知全部条款，所填信息真实有效。</span>
        </div>
      </div>
    </div>

    <!-- 底部按钮 -->
    <div class="bottom-bar">
      <van-button type="primary" round block @click="router.push('/gov-meetings/create')">
        我已知晓，发起约见
      </van-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()

const sections = [
  {
    icon: '📋',
    title: '受理范围',
    items: [
      '企业在生产经营中遇到的政策咨询、审批协调、要素保障等问题',
      '需要政府相关部门研究协调解决的重大事项',
      '政策落地执行中遇到的具体困难和诉求',
      '企业与政府部门之间需要面对面沟通的事项',
    ],
  },
  {
    icon: '🚫',
    title: '不予受理情形',
    items: [
      '已进入司法或行政复议程序的事项',
      '属于信访投诉类，应通过信访渠道反映',
      '申请内容存在恶意、虚假或重复提交情形',
      '提交材料不完整或不符合规定要求',
      '涉及国家秘密、商业秘密或个人隐私事项',
      '申请事项与企业生产经营无关',
      '超出政企约见服务受理范围的事项',
    ],
  },
  {
    icon: '📝',
    title: '提交要求',
    items: [
      '如实填写企业基本信息和联系方式',
      '约见主题需清晰准确，说明具体诉求',
      '约见内容需描述详细，说明背景和期望结果',
      '提供相关证明材料（可选，建议上传）',
      '勾选承诺书，保证所填信息真实有效',
    ],
  },
  {
    icon: '⏱️',
    title: '办理流程',
    items: [
      '企业提交申请 → 工作人员初审（3个工作日内）',
      '初审通过 → 安排约见时间、地点和参与人员',
      '企业收到约见通知 → 按约参加约见',
      '约见完成 → 工作人员记录纪要',
      '企业对约见服务进行满意度评价',
    ],
  },
  {
    icon: '⭐',
    title: '评价规则',
    items: [
      '约见完成后，企业可对本次约见服务进行评价',
      '每次约见申请只能评价一次',
      '评价内容包括满意度、星级评分和评价意见',
      '真实客观的评价有助于持续提升服务质量',
    ],
  },
  {
    icon: '🤝',
    title: '承诺说明',
    items: [
      '提交申请即代表您承诺所填信息真实、准确、完整',
      '所提交事项属于政企约见受理范围',
      '如提供虚假信息，将承担相应法律责任',
      '请按时参加已确认的约见，如有变更请提前告知',
    ],
  },
]
</script>

<style scoped>
.notice-banner {
  background: linear-gradient(135deg, #1989fa 0%, #0056b8 100%);
  padding: 28px 20px 24px;
  color: #fff;
  text-align: center;
  .banner-title { font-size: 18px; font-weight: 700; margin: 10px 0 6px; }
  .banner-sub { font-size: 12px; opacity: 0.85; line-height: 1.5; }
}
.notice-body {
  padding: 0 12px 16px;
}
.notice-section {
  background: #fff;
  border-radius: 10px;
  margin-top: 12px;
  overflow: hidden;
  box-shadow: 0 1px 6px rgba(0,0,0,0.06);
}
.sec-title {
  font-size: 15px;
  font-weight: 600;
  color: #333;
  padding: 14px 16px 10px;
  border-bottom: 1px solid #f5f5f5;
  display: flex;
  align-items: center;
  gap: 8px;
  .sec-icon { font-size: 16px; }
}
.sec-content { padding: 10px 16px 14px; }
.sec-item {
  display: flex;
  gap: 6px;
  font-size: 13px;
  color: #555;
  line-height: 1.7;
  margin-bottom: 4px;
  .bullet { color: #1989fa; flex-shrink: 0; margin-top: 1px; }
}
.commitment-tip {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  background: #fff7f0;
  border: 1px solid #ffe0c0;
  border-radius: 8px;
  padding: 12px 14px;
  margin-top: 12px;
  font-size: 12px;
  color: #c77b2a;
  line-height: 1.6;
}
.bottom-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 12px 16px;
  background: #fff;
  box-shadow: 0 -2px 8px rgba(0,0,0,0.08);
  z-index: 100;
}
</style>
