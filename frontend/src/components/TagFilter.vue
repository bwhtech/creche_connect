<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { state, colorOf } from '../lib/store'

const route = useRoute()
const router = useRouter()

const active = computed(() => route.query.tag as string | undefined)
const options = computed(() =>
  state.tags
    .map((t) => ({ ...t, count: state.counts.tags[t.id] ?? 0 }))
    .filter((t) => t.count),
)
const setTag = (id?: string) => router.push({ path: '/', query: { ...route.query, tag: id === active.value ? undefined : id } })
</script>

<template>
  <div class="flex flex-wrap items-center gap-2">
    <button
      type="button"
      class="inline-flex h-8 items-center gap-1.5 rounded-full border px-3.5 text-sm transition-colors"
      :class="!active ? 'border-transparent bg-surface-gray-3 text-ink-gray-9' : 'border-outline-gray-2 text-ink-gray-7 hover:bg-surface-gray-1'"
      @click="setTag(undefined)"
    >
      All topics
      <span class="text-ink-gray-5 tabular-nums">{{ state.counts.total }}</span>
    </button>
    <button
      v-for="t in options"
      :key="t.id"
      type="button"
      class="inline-flex h-8 items-center gap-2 rounded-full border px-3.5 text-sm transition-colors"
      :class="active === t.id ? [colorOf(t.color).soft, 'border-transparent text-ink-gray-9'] : 'border-outline-gray-2 text-ink-gray-7 hover:bg-surface-gray-1'"
      :aria-pressed="active === t.id"
      @click="setTag(t.id)"
    >
      <span class="size-2 rounded-full" :class="colorOf(t.color).dot" aria-hidden="true" />
      {{ t.name }}
      <span class="text-ink-gray-5 tabular-nums">{{ t.count }}</span>
    </button>
  </div>
</template>
