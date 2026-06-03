<template>
  <div class="page">
    <van-nav-bar title="我的约见" left-arrow @click-left="router.push('/home')" fixed>
      <template #right>
        <van-icon name="plus" size="20" @click="router.push('/gov-meetings/notice')" />
      </template>
    </van-nav-bar>

    <div class="page-body page-body--tabs">
      <van-tabs v-model:active="activeTab" @change="onTabChange" sticky offset-top="46px">
        <van-tab v-for="tab in tabs" :key="tab.value" :title="tab.label" :name="tab.value" />
      </van-tabs>

      <van-pull-refresh v-model="refreshing" @refresh="onRefresh">
        <van-list
          v-model:loading="loading"
          :finished="finished"
          finished-text="没有更多了"
          @load="loadMore"
        >
          <EmptyState
            v-if="!loading && list.length === 0 && finished"
            description="暂无约见记录"
            action-text="去发起约见"
            @action="router.push('/gov-meetings/notice')"
          />

          <div
            v-for="item in list"
            :key="item.id"
            class="list-card"
            @click="router.push(`/gov-meetings/${item.id}`)"
          >
            <div class="list-card__header">
              <span class="list-card__title">{{ getTitle(item) }}</span>
              <StatusTag module="govMeeting" :code="item.status" />
            </div>
            <div class="list-card__no">编号：{{ getApplyNo(item) }}</div>
            <div class="card-row" v-if="getTopicName(item)">
              <van-icon name="label-o" size="13" color="#999" />
              {{ getTopicName(item) }}
            </div>
            <div class="card-row" v-if="getExpectedLevel(item)">
              <van-icon name="flag-o" size="13" color="#999" />
              期望层级：{{ getExpectedLevel(item) }}
            </div>
            <div class="card-row" v-if="getFinalLevel(item)">
              <van-icon name="award-o" size="13" color="#07c160" />
              <span style="color:#07c160">研判层级：{{ getFinalLevel(item) }}</span>
            </div>
            <div class="card-footer">
              提交于 {{ formatDt(getSubmittedAt(item)) }}
            </div>
            <div v-if="item.status === 'NEED_SUPPLEMENT'" class="card-tip supplement">
              <van-icon name="warning-o" size="13" />需要补充材料，点击查看
            </div>
            <div v-if="item.status === 'PENDING_EVALUATION' || item.status === 'MEETING_COMPLETED'" class="card-tip evaluate">
              <van-icon name="star-o" size="13" />约见已完成，请点击评价
            </div>
          </div>
        </van-list>
      </van-pull-refresh>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { getMyGovMeetings } from '@/api/govMeeting'
import type { GovMeetingApply } from '@/api/govMeeting'
import StatusTag from '@/components/StatusTag.vue'
import EmptyState from '@/components/EmptyState.vue'

const router = useRouter()
const loading = ref(false)
const refreshing = ref(false)
const finished = ref(false)
const list = ref<GovMeetingApply[]>([])
const pageNo = ref(1)
const activeTab = ref('')

const tabs = [
  { label: '全部', value: '' },
  { label: '待审核', value: 'PENDING_AUDIT' },
  { label: '待安排', value: 'PENDING_ARRANGE' },
  { label: '待约见', value: 'WAIT_MEETING' },
  { label: '待评价', value: 'PENDING_EVALUATION' },
  { label: '已完成', value: 'COMPLETED' },
  { label: '其他', value: 'OTHER' },
]

const OTHER_STATUSES = ['NEED_SUPPLEMENT', 'REJECTED', 'ACCEPTED', 'ARRANGED', 'MEETING_COMPLETED', 'EVALUATED']

function getApplyNo(a: GovMeetingApply) { return a.applyNo || a.apply_no || '--' }
function getTitle(a: GovMeetingApply) { return a.title || a.topicName || a.topic_name || '约见申请' }
function getTopicName(a: GovMeetingApply) { return a.topicName || a.topic_name || '' }
function getExpectedLevel(a: GovMeetingApply) { return a.expectedLevelName || a.expected_level_name || a.meetingLevel || a.meeting_level || '' }
function getFinalLevel(a: GovMeetingApply) { return a.finalLevelName || a.final_level_name || '' }
function getSubmittedAt(a: GovMeetingApply) { return a.submittedAt || a.submitted_at || a.createdAt || a.created_at || '' }

function formatDt(dt?: string): string {
  if (!dt) return '--'
  const d = new Date(dt.replace(' ', 'T'))
  if (isNaN(d.getTime())) return dt.slice(0, 16).replace('T', ' ')
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

async function loadMore() {
  try {
    const statusParam = activeTab.value === '' ? undefined
      : activeTab.value === 'OTHER' ? undefined
      : activeTab.value

    const res = await getMyGovMeetings({ status: statusParam, pageNo: pageNo.value, pageSize: 10 })
    let records = res.records || []

    if (activeTab.value === 'OTHER') {
      records = records.filter(b => OTHER_STATUSES.includes(b.status))
    }

    list.value = pageNo.value === 1 ? records : [...list.value, ...records]
    pageNo.value++
    if (list.value.length >= res.total || (res.records || []).length < 10) finished.value = true
  } catch {
    finished.value = true
  } finally {
    loading.value = false
    refreshing.value = false
  }
}

function onRefresh() {
  list.value = []
  pageNo.value = 1
  finished.value = false
  loading.value = true
  loadMore()
}

function onTabChange() {
  list.value = []
  pageNo.value = 1
  finished.value = false
  loading.value = true
  loadMore()
}
</script>

<style scoped>
.empty-wrap { text-align: center; padding: 20px; display: flex; flex-direction: column; align-items: center; gap: 12px; }
.meeting-card {
  background: #fff;
  margin: 8px 12px;
  border-radius: 10px;
  padding: 14px 16px;
  box-shadow: 0 1px 6px rgba(0,0,0,0.07);
  cursor: pointer;
  &:active { opacity: 0.7; }
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 8px;
  margin-bottom: 8px;
}
.card-title {
  font-size: 15px;
  font-weight: 500;
  color: #1a1a1a;
  flex: 1;
  line-height: 1.4;
}
.card-no { font-size: 12px; color: #999; margin-bottom: 8px; font-family: monospace; }
.card-row {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
  color: #777;
  margin-bottom: 5px;
}
.card-footer { font-size: 11px; color: #bbb; margin-top: 8px; padding-top: 8px; border-top: 1px solid #f5f5f5; }
.card-tip {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  font-weight: 500;
  margin-top: 8px;
  padding: 6px 10px;
  border-radius: 6px;
  &.supplement { background: #fff7e6; color: #ff976a; }
  &.evaluate { background: #e6f7ff; color: #1989fa; }
}
</style>
