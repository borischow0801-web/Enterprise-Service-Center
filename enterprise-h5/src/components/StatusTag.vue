<template>
  <van-tag :type="meta.type" :color="meta.background" :text-color="meta.color" round>
    {{ meta.label }}
  </van-tag>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { getStatusMeta, type StatusModule } from '@/utils/status'

const props = defineProps<{
  module: StatusModule
  code?: string | null
}>()

const meta = computed(() => getStatusMeta(props.module, props.code))
</script>
