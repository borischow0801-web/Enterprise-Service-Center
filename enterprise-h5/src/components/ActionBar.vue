<template>
  <div class="bottom-bar action-bar">
    <slot />
  </div>
</template>

<style scoped>
.action-bar :deep(.van-button + .van-button) {
  margin-top: 8px;
}
</style>
