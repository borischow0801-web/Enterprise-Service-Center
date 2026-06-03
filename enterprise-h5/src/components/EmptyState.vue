<template>
  <div class="empty-state">
    <van-empty :description="description" :image="image">
      <slot />
    </van-empty>
    <van-button
      v-if="actionText"
      type="primary"
      round
      size="small"
      class="empty-state__btn"
      @click="$emit('action')"
    >
      {{ actionText }}
    </van-button>
  </div>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    description?: string
    actionText?: string
    image?: string
  }>(),
  {
    description: '暂无数据',
    image: 'default',
  }
)

defineEmits<{ action: [] }>()
</script>

<style scoped>
.empty-state {
  padding: 32px 16px 24px;
  text-align: center;
}
.empty-state__btn {
  margin-top: 12px;
}
</style>
