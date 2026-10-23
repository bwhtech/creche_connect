<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { Button, PageHeader } from 'frappe-ui'
import FeedList from '../components/FeedList.vue'
import TagFilter from '../components/TagFilter.vue'
import { state, useMe, canStart, tagById, loadThreads, loadCounts } from '../lib/store'

const me = useMe()
const route = useRoute()
const loading = computed(() => !state.threadsLoaded)

const filter = computed(() => route.query.filter as string | undefined)
const tag = computed(() => tagById(route.query.tag as string))

watch(
  () => [filter.value, route.query.tag as string | undefined],
  ([f, t]) => {
    state.feed = { filter: f, tag: t }
    loadThreads().catch(() => {})
  },
  { immediate: true },
)
watch(filter, () => loadCounts().catch(() => {}), { immediate: true })

const loadingMore = ref(false)
async function more() {
  loadingMore.value = true
  try {
    await loadThreads('more')
  } finally {
    loadingMore.value = false
  }
}

const title = computed(
  () => ({ unread: 'Unread', ack: 'To acknowledge', mine: 'Started by me' })[filter.value ?? ''] ?? 'Feed',
)
</script>

<template>
  <div class="flex h-full flex-col">
    <PageHeader>
      <h1 class="truncate text-2xl text-ink-gray-9">{{ title }}</h1>
      <Button v-if="canStart(me)" class="ml-auto" variant="solid" theme="gray" icon-left="lucide-plus" label="New thread" route="/new" />
    </PageHeader>

    <div class="min-h-0 flex-1 overflow-y-auto">
      <div class="mx-auto max-w-[860px] px-3 pt-8 pb-20 sm:px-6">
        <TagFilter />
        <div class="mt-8">
          <FeedList :rows="state.threads" :loading="loading" />
          <Button v-if="state.cursor" class="mt-4 w-full" label="Load more" :loading="loadingMore" @click="more" />
        </div>
      </div>
    </div>
  </div>
</template>
