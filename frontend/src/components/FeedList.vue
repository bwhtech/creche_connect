<script setup lang="ts">
import { Button, Skeleton } from 'frappe-ui'
import ThreadCard from './ThreadCard.vue'
import StatusPage from './StatusPage.vue'

defineProps<{ rows: any[]; loading: boolean }>()
const EMPTY = {
  unread: { icon: 'lucide-check-check', title: "You're all caught up", text: 'No unread threads.' },
  ack: { icon: 'lucide-badge-check', title: 'Nothing to acknowledge', text: "You've acknowledged everything sent to you." },
  mentions: { icon: 'lucide-at-sign', title: 'No mentions yet', text: 'When someone @mentions you, it shows here.' },
  mine: { icon: 'lucide-send', title: 'No posts yet', text: 'Threads you post show here.' },
}
const NOTHING = { icon: 'lucide-inbox', title: 'Nothing here', text: 'No threads match this view yet.' }
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

  <div v-else class="rounded-5 border border-dashed border-outline-gray-2 py-20">
    <StatusPage v-bind="EMPTY[$route.query.filter as string] ?? NOTHING">
      <Button v-if="Object.keys($route.query).length" label="Back to feed" route="/" class="mt-2" />
    </StatusPage>
  </div>
</template>
