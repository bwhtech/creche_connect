<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { Button, PageHeader } from 'frappe-ui'
import FeedList from '../components/FeedList.vue'
import TagFilter from '../components/TagFilter.vue'
import { state, useMe, canStart, tagById } from '../lib/store'

const me = useMe()
const route = useRoute()
const loading = computed(() => !state.threadsLoaded)

const filter = computed(() => route.query.filter as string | undefined)
const tag = computed(() => tagById(route.query.tag as string))

const title = computed(
  () => ({ unread: 'Unread', ack: 'To acknowledge', mine: 'Started by me' })[filter.value ?? ''] ?? 'Feed',
)

// Threads after the sidebar filter. The tag filter applies on top, so it can show counts.
const base = computed(() => {
  const list = state.threads
  if (filter.value === 'unread') return list.filter((t) => t.unread)
  if (filter.value === 'ack') return list.filter((t) => t.needsAck)
  if (filter.value === 'mine') return list.filter((t) => t.authorId === me.value.id)
  return list
})
const rows = computed(() => (tag.value ? base.value.filter((t) => t.tags.includes(tag.value.id)) : base.value))
</script>

<template>
  <div class="flex h-full flex-col">
    <PageHeader>
      <h1 class="truncate text-2xl text-ink-gray-9">{{ title }}</h1>
      <Button v-if="canStart(me)" class="ml-auto" variant="solid" theme="gray" icon-left="lucide-plus" label="New thread" route="/new" />
    </PageHeader>

    <div class="min-h-0 flex-1 overflow-y-auto">
      <div class="mx-auto max-w-[860px] px-3 pt-8 pb-20 sm:px-6">
        <TagFilter :threads="base" />
        <div class="mt-8">
          <FeedList :rows="rows" :loading="loading" />
        </div>
      </div>
    </div>
  </div>
</template>
