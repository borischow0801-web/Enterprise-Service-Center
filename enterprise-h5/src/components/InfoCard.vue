<template>
  <div class="content-block">
    <div v-if="title" class="content-block__title">{{ title }}</div>
    <slot />
  </div>
</template>

<script setup lang="ts">
defineProps<{ title?: string }>()
</script>
