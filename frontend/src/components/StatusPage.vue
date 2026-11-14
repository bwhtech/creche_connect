<script setup lang="ts">
defineProps<{ icon: string; title: string; text?: string }>()
</script>

<template>
  <div class="flex h-full flex-1 flex-col items-center justify-center gap-3 px-6 text-center">
    <div class="rounded-full bg-surface-gray-2 p-3 text-ink-gray-5">
      <span :class="icon" class="block size-6" aria-hidden="true" />
    </div>
    <p class="text-base text-ink-gray-7">{{ title }}</p>
    <p v-if="text" class="max-w-sm text-p-sm text-ink-gray-5">{{ text }}</p>
    <slot />
  </div>
</template>
