<template>
  <div class="page">
    <van-nav-bar title="企业诉求" left-arrow @click-left="router.push('/home')" fixed />

    <div class="page-body page-body--action page-body--tabs">
      <van-tabs v-model:active="activeTab" @change="onTabChange" sticky :offset-top="46">
        <van-tab v-for="tab in tabs" :key="tab.value" :title="tab.label" :name="tab.value" />
      </van-tabs>

      <van-pull-refresh v-model="refreshing" @refresh="onRefresh">
        <van-list v-model:loading="loading" :finished="finished" finished-text="没有更多了" @load="loadMore">
          <EmptyState
            v-if="!loading && list.length === 0 && finished"
            description="暂无诉求记录"
            action-text="去提交诉求"
            @action="router.push('/appeals/create')"
          />

          <div
            v-for="item in list"
            :key="item.id"
            class="list-card"
            @click="router.push(`/appeals/${item.id}`)"
          >
            <div class="list-card__header">
              <span class="list-card__title">{{ item.title || '--' }}</span>
              <StatusTag module="appeal" :code="item.status" />
            </div>
            <div class="list-card__no">编号：{{ item.appealNo || '--' }}</div>
            <div class="list-card__meta">
              <span>{{ item.regionName || '--' }}</span>
              <span>{{ formatDate(item.submittedAt) }}</span>
            </div>
          </div>
        </van-list>
      </van-pull-refresh>
    </div>

    <ActionBar>
      <van-button type="primary" round block icon="plus" @click="router.push('/appeals/create')">
        提交诉求
      </van-button>
    </ActionBar>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { getMyAppeals } from '@/api/appeal'
import type { AppealItem } from '@/api/appeal'
import { formatDate } from '@/utils/format'
import StatusTag from '@/components/StatusTag.vue'
import EmptyState from '@/components/EmptyState.vue'
import ActionBar from '@/components/ActionBar.vue'

const router = useRouter()
const loading = ref(false)
const refreshing = ref(false)
const finished = ref(false)
const list = ref<AppealItem[]>([])
const pageNo = ref(1)
const activeTab = ref('')

const tabs = [
  { label: '全部', value: '' },
  { label: '待受理', value: 'PENDING_ACCEPT' },
  { label: '办理中', value: 'ACCEPTED' },
  { label: '待评价', value: 'PENDING_EVALUATION' },
  { label: '已完成', value: 'EVALUATED' },
]

async function loadMore() {
  try {
    const res = await getMyAppeals({
      status: activeTab.value || undefined,
      pageNo: pageNo.value,
      pageSize: 10,
    })
    list.value.push(...res.records)
    pageNo.value++
    if (list.value.length >= res.total) finished.value = true
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
