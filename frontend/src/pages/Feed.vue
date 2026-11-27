<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Button, PageHeader, TabButtons } from 'frappe-ui'
import FeedList from '../components/FeedList.vue'
import TagFilter from '../components/TagFilter.vue'
import { __ } from '../lib/translate'
import FeedSidebar from '../components/FeedSidebar.vue'
import { state, useMe, canStart, tagById, loadThreads, loadCounts, isMobile } from '../lib/store'

const me = useMe()
const route = useRoute()
const router = useRouter()
const loading = computed(() => !state.threadsLoaded)

const filter = computed(() => route.query.filter as string | undefined)
const tag = computed(() => tagById(route.query.tag as string))

watch(
  () => [filter.value, route.query.tag as string | undefined],
  ([f, t], old) => {
    state.feed = { filter: f, tag: t }
    loadThreads().catch(() => {})
    if (f !== old?.[0]) loadCounts().catch(() => {})
  },
  { immediate: true },
)

const loadingMore = ref(false)
async function more() {
  loadingMore.value = true
  try {
    await loadThreads('more')
  } finally {
    loadingMore.value = false
  }
}

const count = (n: number) => (n ? ` ${n}` : '')
const filters = computed(() => [
  { label: __('All'), value: '' },
  { label: `${__('Unread')}${count(state.counts.unread)}`, value: 'unread' },
  { label: `${__('To acknowledge')}${count(state.counts.ack)}`, value: 'ack' },
  { label: __('Mentions'), value: 'mentions' },
  ...(canStart(me.value) ? [{ label: __('My posts'), value: 'mine' }] : []),
])
const setFilter = (f: string) => router.push({ path: '/', query: { ...route.query, filter: f || undefined } })

const title = computed(
  () => ({ unread: __('Unread'), ack: __('To acknowledge'), mentions: __('Mentions'), mine: __('My posts') })[filter.value ?? ''] ?? __('Feed'),
)
</script>

<template>
  <div class="flex h-full flex-col">
    <PageHeader>
      <h1 class="truncate text-2xl text-ink-gray-9">{{ title }}</h1>
      <Button v-if="canStart(me)" class="ml-auto max-md:hidden" variant="solid" theme="gray" icon-left="lucide-plus" :label="__('New thread')" route="/new" />
    </PageHeader>

    <div class="flex min-h-0 flex-1">
      <div class="min-w-0 flex-1 overflow-y-auto">
        <div class="mx-auto max-w-[860px] px-3 pt-4 pb-20 sm:px-6 md:pt-8 lg:max-w-[680px]">
          <TabButtons v-if="isMobile" class="mb-3 w-full overflow-x-auto [scrollbar-width:none] [&>*]:flex-1" :model-value="filter ?? ''" :options="filters" @update:model-value="setFilter" />
          <TagFilter v-if="!isMobile || !filter || tag" class="lg:hidden" />
          <div class="mt-4 md:mt-8 lg:mt-0">
            <FeedList :rows="state.threads" :loading="loading" />
            <Button v-if="state.cursor" class="mt-4 w-full" :label="__('Load more')" :loading="loadingMore" @click="more" />
          </div>
        </div>
      </div>
      <FeedSidebar v-if="!isMobile" class="hidden lg:block" />
    </div>
  </div>
</template>
