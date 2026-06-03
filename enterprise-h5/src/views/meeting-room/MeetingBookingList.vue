<template>
  <div class="page">
    <van-nav-bar title="我的预约" left-arrow @click-left="router.push('/home')" fixed />

    <div class="page-body page-body--tabs">
      <!-- 状态筛选 -->
      <van-tabs v-model:active="activeTab" @change="onTabChange" sticky offset-top="46">
        <van-tab title="全部" name="" />
        <van-tab title="待审核" name="PENDING_AUDIT" />
        <van-tab title="待使用" name="WAIT_USE" />
        <van-tab title="已完成" name="COMPLETED" />
        <van-tab title="已取消" name="CANCELED" />
        <van-tab title="其他" name="OTHER" />
      </van-tabs>

      <van-pull-refresh v-model="refreshing" @refresh="onRefresh">
        <van-list
          v-model:loading="loading"
          :finished="finished"
          finished-text="没有更多了"
          @load="loadMore"
        >
          <EmptyState
            v-if="list.length === 0 && !loading && finished"
            description="暂无预约记录"
            action-text="去预约会议室"
            @action="router.push('/meeting-rooms')"
          />

          <div
            v-for="booking in list"
            :key="booking.id"
            class="list-card"
            @click="router.push(`/meeting-bookings/${booking.id}`)"
          >
            <div class="list-card__header">
              <span class="list-card__title">{{ booking.meetingSubject || booking.meeting_subject || '--' }}</span>
              <StatusTag module="booking" :code="booking.status" />
            </div>
            <div class="list-card__no">编号：{{ booking.bookingNo || booking.booking_no || '--' }}</div>
            <div class="list-card__meta">
              <span><van-icon name="home-o" size="13" /> {{ booking.roomName || booking.room_name || '--' }}</span>
            </div>
            <div class="list-card__meta" style="margin-top:4px">
              <span><van-icon name="clock-o" size="13" /> {{ formatDt(booking.startTime || booking.start_time) }} — {{ fmtTime(booking.endTime || booking.end_time) }}</span>
            </div>
            <div class="list-card__meta" style="margin-top:8px;padding-top:8px;border-top:1px solid var(--esc-border)">
              <span>提交于 {{ formatDt(booking.submittedAt || booking.submitted_at || booking.createdAt || booking.created_at) }}</span>
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
import { getMyMeetingBookings } from '@/api/meetingRoom'
import type { MeetingBooking } from '@/api/meetingRoom'
import StatusTag from '@/components/StatusTag.vue'
import EmptyState from '@/components/EmptyState.vue'

const router = useRouter()

const activeTab = ref('')
const list = ref<MeetingBooking[]>([])
const loading = ref(false)
const finished = ref(false)
const refreshing = ref(false)
let page = 1

function formatDt(dt?: string): string {
  if (!dt) return '--'
  const d = new Date(dt.replace(' ', 'T'))
  if (isNaN(d.getTime())) return dt.slice(0, 16).replace('T', ' ')
  return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}
function fmtTime(dt?: string): string {
  if (!dt) return '--'
  const d = new Date(dt.replace(' ', 'T'))
  if (isNaN(d.getTime())) return dt.slice(11, 16)
  return `${pad(d.getHours())}:${pad(d.getMinutes())}`
}
function pad(n: number) { return String(n).padStart(2, '0') }

// 'OTHER' tab: statuses not covered by the other tabs
const OTHER_STATUSES = ['NEED_SUPPLEMENT', 'REJECTED', 'APPROVED', 'NO_SHOW']

async function fetchList(reset = false) {
  if (reset) { page = 1; list.value = []; finished.value = false }
  loading.value = true
  try {
    // For OTHER tab, we fetch all and filter; simpler than multiple requests
    const statusParam = activeTab.value === '' ? undefined
      : activeTab.value === 'OTHER' ? undefined
      : activeTab.value

    const res = await getMyMeetingBookings({ status: statusParam, pageNo: page, pageSize: 20 })
    let records = res.records || []

    if (activeTab.value === 'OTHER') {
      records = records.filter(b => OTHER_STATUSES.includes(b.status))
    }

    list.value = reset ? records : [...list.value, ...records]
    if (list.value.length >= res.total || (res.records || []).length < 20) {
      finished.value = true
    } else {
      page++
    }
  } catch {
    finished.value = true
  } finally {
    loading.value = false
    refreshing.value = false
  }
}

async function loadMore() { await fetchList(false) }
async function onRefresh() { await fetchList(true) }
function onTabChange() { fetchList(true) }
</script>

