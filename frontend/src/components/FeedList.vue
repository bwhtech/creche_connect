<script setup lang="ts">
import { Button, Skeleton } from 'frappe-ui'
import ThreadCard from './ThreadCard.vue'

defineProps<{ rows: any[]; loading: boolean }>()
</script>

<template>
  <div v-if="loading" class="space-y-4">
    <div v-for="i in 4" :key="i" class="flex gap-4 rounded-5 border border-outline-gray-1 p-5">
      <Skeleton class="size-8 rounded-full" />
      <div class="flex-1 space-y-2.5">
        <Skeleton class="h-3 w-1/3" />
        <Skeleton class="h-4 w-2/3" />
        <Skeleton class="h-3 w-full" />
      </div>
    </div>
  </div>

  <div v-else-if="rows.length" class="space-y-4">
    <ThreadCard v-for="t in rows" :key="t.id" :thread="t" />
  </div>

  <div v-else class="flex flex-col items-center justify-center gap-3 rounded-5 border border-dashed border-outline-gray-2 py-20 text-center">
    <div class="rounded-full bg-surface-gray-2 p-3 text-ink-gray-5">
      <span class="lucide-inbox size-6" aria-hidden="true" />
    </div>
    <p class="text-base text-ink-gray-7">Nothing here</p>
    <p class="text-sm text-ink-gray-5">No threads match this view yet.</p>
    <Button v-if="Object.keys($route.query).length" label="Back to feed" route="/" class="mt-2" />
  </div>
</template>
