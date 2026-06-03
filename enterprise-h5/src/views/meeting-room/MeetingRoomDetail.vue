<template>
  <div class="page">
    <van-nav-bar
      :title="room?.roomName || room?.room_name || '会议室详情'"
      left-arrow
      @click-left="router.back()"
      fixed
    />

    <div class="page-body page-body--action">
      <van-loading v-if="loading" size="32" vertical style="padding:60px 0;display:flex;justify-content:center">加载中...</van-loading>

      <template v-if="!loading && room">
        <!-- 图片轮播 -->
        <div class="cover-wrap">
          <van-swipe v-if="roomImages.length" :autoplay="4000" indicator-color="#1677ff">
            <van-swipe-item v-for="(img, idx) in roomImages" :key="img.url + idx">
              <van-image :src="img.url" width="100%" height="220" fit="cover" @error="onImageError(idx)" />
            </van-swipe-item>
          </van-swipe>
          <div v-else class="cover-placeholder">
            <van-icon name="photo-o" size="48" color="#ccc" />
            <div style="color:#ccc;margin-top:8px;font-size:13px">暂无图片</div>
          </div>
        </div>

        <!-- 基本信息 -->
        <van-cell-group inset style="margin-top:12px" title="基本信息">
          <van-cell title="会议室名称" :value="room.roomName || room.room_name" />
          <van-cell v-if="room.address" title="地址" :value="room.address" />
          <van-cell title="可容纳人数" :value="`${room.capacity} 人`" />
        </van-cell-group>

        <!-- 设施设备 -->
        <van-cell-group inset style="margin-top:12px" title="设施设备">
          <div v-if="facilityList.length" style="padding:10px 16px;display:flex;flex-wrap:wrap;gap:8px">
            <van-tag v-for="f in facilityList" :key="f" plain type="primary">{{ facilityLabel(f) }}</van-tag>
          </div>
          <div v-else style="padding:10px 16px;color:#999;font-size:13px">暂无设施信息</div>
        </van-cell-group>

        <!-- 简介 -->
        <van-cell-group v-if="room.description" inset style="margin-top:12px" title="会议室简介">
          <div style="padding:10px 16px;font-size:14px;color:#555;line-height:1.7">{{ room.description }}</div>
        </van-cell-group>

        <!-- 开放规则 -->
        <van-cell-group v-if="openRules.length" inset style="margin-top:12px" title="开放时间">
          <div style="padding:8px 16px">
            <div v-for="r in openRules" :key="r.weekday" class="rule-row">
              <span class="rule-day">{{ weekdayName(r.weekday) }}</span>
              <span v-if="getOpenFlag(r)" class="rule-time">{{ r.startTime || r.start_time }} - {{ r.endTime || r.end_time }}</span>
              <span v-else class="rule-closed">不开放</span>
            </div>
          </div>
        </van-cell-group>

        <!-- 预约须知 -->
        <van-cell-group v-if="room.bookingNotice" inset style="margin-top:12px" title="预约须知">
          <div style="padding:10px 16px;font-size:13px;color:#666;line-height:1.7;white-space:pre-wrap">{{ room.bookingNotice }}</div>
        </van-cell-group>

        <!-- 管理制度阅读确认 -->
        <div class="rules-agree">
          <van-checkbox v-model="rulesAgreed" icon-size="18px">
            <span class="rules-agree__text">
              我已阅读并同意
              <span class="rules-link" @click.stop="goRulesPage">《共享会议室预约使用管理制度》</span>
            </span>
          </van-checkbox>
        </div>

        <!-- 预约按钮 -->
        <div class="bottom-bar">
          <van-button
            type="primary"
            round
            block
            size="large"
            :disabled="!rulesAgreed"
            @click="handleBook"
          >立即预约</van-button>
        </div>
      </template>

      <van-empty v-if="!loading && !room" description="会议室不存在或已停用" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { showToast } from 'vant'
import { getMeetingRoomDetail, coverUrl } from '@/api/meetingRoom'
import { apiAssetUrl } from '@/utils/api'
import { normalizeFacilities } from '@/utils/format'
import { loadFacilityLabelMap, facilityDisplayLabel } from '@/utils/facility'
import type { MeetingRoom, OpenRule } from '@/api/meetingRoom'

const router = useRouter()
const route = useRoute()
const roomId = Number(route.params.id)

const RULES_AGREE_KEY = `meeting-room-rules-agreed-${roomId}`

const loading = ref(true)
const room = ref<MeetingRoom | null>(null)
const openRules = ref<OpenRule[]>([])
const rulesAgreed = ref(sessionStorage.getItem(RULES_AGREE_KEY) === '1')
const facilityLabelMap = ref<Record<string, string>>({})

const facilityList = computed(() => normalizeFacilities(room.value?.facilities))

function facilityLabel(code: string) {
  return facilityDisplayLabel(code, facilityLabelMap.value)
}

const WEEKDAY = ['', '周一', '周二', '周三', '周四', '周五', '周六', '周日']
function weekdayName(d: number) { return WEEKDAY[d] || `周${d}` }
function getOpenFlag(r: OpenRule) { return r.openFlag ?? r.open_flag ?? 0 }

const roomImages = computed(() => {
  if (!room.value) return []
  const imgs = room.value.images || []
  if (imgs.length) {
    return imgs.map(img => ({ url: apiAssetUrl(img.url), attachmentId: img.attachmentId }))
  }
  const single = coverUrl(room.value)
  return single ? [{ url: single, attachmentId: room.value.coverAttachmentId || 0 }] : []
})

const brokenImages = ref<Record<number, boolean>>({})
function onImageError(idx: number) {
  brokenImages.value[idx] = true
}

function goRulesPage() {
  router.push('/meeting-rooms/rules')
}

function handleBook() {
  if (!rulesAgreed.value) {
    showToast('请先阅读并同意《共享会议室预约使用管理制度》')
    return
  }
  sessionStorage.setItem(RULES_AGREE_KEY, '1')
  router.push(`/meeting-rooms/${roomId}/book`)
}

onMounted(async () => {
  facilityLabelMap.value = await loadFacilityLabelMap()
  try {
    const data = await getMeetingRoomDetail(roomId)
    room.value = data
    openRules.value = data.openRules || []
  } catch {
    room.value = null
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.cover-wrap { width: 100%; overflow: hidden; }
.cover-placeholder {
  height: 180px;
  background: #f0f0f0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}
.rule-row {
  display: flex;
  align-items: center;
  padding: 6px 0;
  border-bottom: 1px solid #f5f5f5;
  font-size: 13px;
  &:last-child { border-bottom: none; }
}
.rule-day { width: 50px; color: #555; font-weight: 500; }
.rule-time { color: #07c160; }
.rule-closed { color: #999; }
.rules-agree {
  margin: 16px 16px 0;
  padding: 12px;
  background: #fff;
  border-radius: 8px;
}
.rules-agree__text {
  font-size: 13px;
  color: #646566;
  line-height: 1.6;
}
.rules-link {
  color: #1989fa;
}
</style>
