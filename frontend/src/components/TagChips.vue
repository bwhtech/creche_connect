<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink } from 'vue-router'
import { tagById, colorOf } from '../lib/store'

const props = defineProps<{ tags: string[] }>()
const list = computed(() => props.tags.map(tagById).filter(Boolean))
</script>

<template>
  <div class="flex flex-wrap items-center gap-1.5">
    <RouterLink
      v-for="t in list"
      :key="t.id"
      :to="{ path: '/', query: { tag: t.id } }"
      class="inline-flex h-5 items-center gap-1.5 rounded-full px-2 text-xs text-ink-gray-7 hover:bg-surface-gray-3"
      :class="colorOf(t.color).soft"
      @click.stop
    >
      <span class="size-1.5 rounded-full" :class="colorOf(t.color).dot" aria-hidden="true" />
      {{ t.name }}
    </RouterLink>
  </div>
</template>
