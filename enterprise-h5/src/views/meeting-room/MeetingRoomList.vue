<template>
  <div class="page">
    <van-nav-bar title="共享会议室" left-arrow @click-left="router.push('/home')" fixed />

    <div class="page-body">
      <!-- 筛选区 -->
      <div class="filter-bar">
        <van-field
          v-model="searchText"
          placeholder="搜索会议室名称/地址"
          left-icon="search"
          clearable
          @update:model-value="onFilterChange"
          style="flex:1"
        />
        <van-button size="small" plain type="primary" @click="showFilter = true" style="margin-left:8px;flex-shrink:0">
          筛选
        </van-button>
      </div>

      <!-- 下拉筛选 -->
      <van-popup v-model:show="showFilter" position="top" :style="{ padding: '16px' }">
        <div class="filter-panel">
          <div class="filter-label">区划</div>
          <van-grid :column-num="3" :border="false" style="margin-bottom:8px">
            <van-grid-item v-for="r in regionOptions" :key="r.code"
              :class="['filter-tag', { active: filter.regionCode === r.code }]"
              @click="toggleRegion(r.code)">
              <span>{{ r.label }}</span>
            </van-grid-item>
          </van-grid>
          <div class="filter-label">最小容量</div>
          <van-stepper v-model="filter.capacityMin" min="0" step="5" style="margin-bottom:12px" />
          <div style="display:flex;gap:8px">
            <van-button block plain @click="resetFilter">重置</van-button>
            <van-button block type="primary" @click="applyFilter">确定</van-button>
          </div>
        </div>
      </van-popup>

      <!-- 列表 -->
      <van-pull-refresh v-model="refreshing" @refresh="onRefresh">
        <van-list
          v-model:loading="loading"
          :finished="finished"
          finished-text="没有更多了"
          @load="loadMore"
        >
          <EmptyState
            v-if="list.length === 0 && !loading && finished"
            description="暂无可用会议室"
            action-text="刷新列表"
            @action="onRefresh"
          />
          <div
            v-for="room in list"
            :key="room.id"
            class="room-card"
            @click="goDetail(room.id)"
          >
            <!-- 封面图 -->
            <div class="room-cover">
              <van-image
                v-if="getCoverUrl(room)"
                :src="getCoverUrl(room)"
                width="100%"
                height="160"
                fit="cover"
                radius="8 8 0 0"
              />
              <div v-else class="cover-placeholder">
                <van-icon name="photo-o" size="40" color="#ccc" />
              </div>
            </div>
            <!-- 信息 -->
            <div class="room-body">
              <div class="room-name">{{ room.roomName || room.room_name }}</div>
              <div class="room-meta">
                <van-icon name="location-o" size="12" />
                {{ room.regionName }}{{ room.serviceCenterName ? ` · ${room.serviceCenterName}` : '' }}
              </div>
              <div v-if="room.address" class="room-meta">
                <van-icon name="map-marked" size="12" />
                {{ room.address }}
              </div>
              <div class="room-row">
                <span class="room-capacity"><van-icon name="friends-o" size="12" /> 可容纳 {{ room.capacity }} 人</span>
              </div>
              <div v-if="room.facilities && room.facilities.length" class="room-facilities">
                <van-tag
                  v-for="f in room.facilities.slice(0, 4)"
                  :key="f"
                  plain
                  style="margin:2px 4px 0 0;font-size:11px"
                >{{ f }}</van-tag>
                <span v-if="room.facilities.length > 4" style="font-size:11px;color:#999">+{{ room.facilities.length - 4 }}</span>
              </div>
            </div>
            <div class="room-footer">
              <van-button size="small" type="primary" round>查看详情</van-button>
            </div>
          </div>
        </van-list>
      </van-pull-refresh>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getMeetingRooms, coverUrl } from '@/api/meetingRoom'
import type { MeetingRoom } from '@/api/meetingRoom'
import { getDictionary } from '@/api/common'
import EmptyState from '@/components/EmptyState.vue'

const router = useRouter()

const regionOptions = ref<{ code: string; label: string }[]>([])
const searchText = ref('')
const showFilter = ref(false)
const filter = ref({ regionCode: '', capacityMin: 0 })

onMounted(async () => {
  const regions = await getDictionary('REGION')
  regionOptions.value = regions.map(d => ({ code: d.dictCode, label: d.dictLabel }))
  // initial load handled by van-list @load
})

const list = ref<MeetingRoom[]>([])
const loading = ref(false)
const finished = ref(false)
const refreshing = ref(false)
let page = 1

function getCoverUrl(room: MeetingRoom): string {
  return coverUrl(room)
}

function goDetail(id: number) {
  router.push(`/meeting-rooms/${id}`)
}

async function fetchRooms(reset = false) {
  if (reset) {
    page = 1
    list.value = []
    finished.value = false
  }
  loading.value = true
  try {
    const res = await getMeetingRooms({
      regionCode: filter.value.regionCode || undefined,
      capacityMin: filter.value.capacityMin > 0 ? filter.value.capacityMin : undefined,
      pageNo: page,
      pageSize: 10,
    })
    const newItems = (res.records || []).filter(r => {
      if (!searchText.value) return true
      const keyword = searchText.value.toLowerCase()
      const name = (r.roomName || r.room_name || '').toLowerCase()
      const addr = (r.address || '').toLowerCase()
      return name.includes(keyword) || addr.includes(keyword)
    })
    list.value = reset ? newItems : [...list.value, ...newItems]
    if (list.value.length >= res.total || (res.records || []).length < 10) {
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

async function loadMore() {
  await fetchRooms(false)
}

async function onRefresh() {
  await fetchRooms(true)
}

function toggleRegion(code: string) {
  filter.value.regionCode = filter.value.regionCode === code ? '' : code
}

function resetFilter() {
  filter.value = { regionCode: '', capacityMin: 0 }
  showFilter.value = false
  fetchRooms(true)
}

function applyFilter() {
  showFilter.value = false
  fetchRooms(true)
}

function onFilterChange() {
  fetchRooms(true)
}
</script>

<style scoped>
.filter-bar {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  background: #fff;
  border-bottom: 1px solid #f0f0f0;
}
.filter-panel { padding-bottom: 8px; }
.filter-label { font-size: 13px; color: #666; margin-bottom: 8px; font-weight: 500; }
.filter-tag {
  border: 1px solid #ddd;
  border-radius: 6px;
  margin: 4px;
  padding: 6px 10px;
  font-size: 13px;
  cursor: pointer;
  text-align: center;
  &.active { border-color: #1989fa; color: #1989fa; background: #ecf5ff; }
}
.room-card {
  margin: 12px 12px 0;
  background: #fff;
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0,0,0,0.07);
}
.room-cover { position: relative; }
.cover-placeholder {
  height: 120px;
  background: #f5f5f5;
  display: flex;
  align-items: center;
  justify-content: center;
}
.room-body { padding: 12px 14px 8px; }
.room-name { font-size: 16px; font-weight: 600; color: #222; margin-bottom: 6px; }
.room-meta { font-size: 12px; color: #888; margin-bottom: 4px; display: flex; align-items: center; gap: 4px; }
.room-row { display: flex; align-items: center; justify-content: space-between; margin-top: 8px; }
.room-capacity { font-size: 13px; color: #555; display: flex; align-items: center; gap: 4px; }
.room-facilities { margin-top: 6px; display: flex; flex-wrap: wrap; align-items: center; }
.room-footer { padding: 10px 14px; display: flex; justify-content: flex-end; border-top: 1px solid #f5f5f5; }
.empty-wrap { padding: 60px 0; }
</style>
