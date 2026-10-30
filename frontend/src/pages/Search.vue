<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { useStorage, watchDebounced } from '@vueuse/core'
import { Avatar, MultiSelect, PageHeader, TextInput } from 'frappe-ui'
import { searchThreads, state, useMe, userById, when } from '../lib/store'

const route = useRoute()
const router = useRouter()
const list = (v) => (v == null ? [] : [v].flat())
const query = ref((route.query.q as string) ?? '')
const filters = reactive({ tags: list(route.query.tag), authors: list(route.query.author), types: list(route.query.type) })
const found = ref<any>(null)
const loading = ref(false)
const recent = useStorage<string[]>(`samvaad:recent-searches:${useMe().value.id}`, [])

function remember() {
  const q = query.value.trim()
  if (q.length >= 2) recent.value = [q, ...recent.value.filter((r) => r !== q)].slice(0, 8)
}

const tagOptions = computed(() => state.tags.map((t) => ({ label: t.name, value: t.id })))
const authorOptions = computed(() => state.users.map((u) => ({ label: u.name, value: u.id })))
const typeOptions = [
  { label: 'Thread', value: 'Samvaad Thread' },
  { label: 'Reply', value: 'Samvaad Reply' },
]

watchDebounced(
  [query, filters],
  async () => {
    const q = query.value.trim()
    router.replace({ query: { q: q || undefined, tag: filters.tags, author: filters.authors, type: filters.types } })
    if (q.length < 2) return (found.value = null)
    loading.value = true
    try {
      found.value = (await searchThreads({ query: q, ...filters })) ?? found.value
    } finally {
      loading.value = false
    }
  },
  { debounce: 250, immediate: true, deep: true },
)
</script>

<template>
  <div class="flex h-full flex-col">
    <PageHeader>
      <h1 class="text-2xl text-ink-gray-9">Search</h1>
    </PageHeader>

    <div class="min-h-0 flex-1 overflow-y-auto">
      <div class="mx-auto max-w-[860px] px-3 pt-8 pb-20 sm:px-6">
        <TextInput v-model="query" size="lg" autofocus placeholder="Search threads and replies" aria-label="Search" @keydown.enter="remember">
          <template #prefix><span class="lucide-search size-4 text-ink-gray-5" aria-hidden="true" /></template>
        </TextInput>
        <div class="mt-3 flex flex-wrap gap-2">
          <MultiSelect v-model="filters.tags" :options="tagOptions" variant="outline" placeholder="Topic" class="w-40" />
          <MultiSelect v-model="filters.authors" :options="authorOptions" variant="outline" placeholder="Author" class="w-48" />
          <MultiSelect v-model="filters.types" :options="typeOptions" variant="outline" placeholder="Type" class="w-36" />
        </div>

        <p class="mt-3 min-h-5 text-sm text-ink-gray-5">
          <template v-if="query.trim().length < 2">Type at least two letters.</template>
          <template v-else-if="loading && !found">Searching…</template>
          <template v-else-if="found">
            {{ found.results.length }} {{ found.results.length === 1 ? 'match' : 'matches' }} ({{ found.duration }}s)
          </template>
        </p>

        <div v-if="query.trim().length < 2 && recent.length" class="mt-4">
          <div class="flex items-center px-2 pb-1 text-sm text-ink-gray-5">
            Recent searches
            <button type="button" class="ml-auto hover:text-ink-gray-8" @click="recent = []">Clear</button>
          </div>
          <button
            v-for="r in recent"
            :key="r"
            type="button"
            class="flex w-full items-center gap-2 rounded-4 px-2 py-2 text-left text-base text-ink-gray-8 hover:bg-surface-gray-1"
            @click="query = r"
          >
            <span class="lucide-history size-4 text-ink-gray-5" aria-hidden="true" />
            {{ r }}
          </button>
        </div>

        <div class="mt-4 divide-y divide-outline-gray-1">
          <RouterLink
            v-for="r in found?.results ?? []"
            :key="r.id"
            :to="{ path: `/threads/${r.thread}`, query: r.reply ? { reply: r.reply } : {} }"
            class="flex gap-3 rounded-4 px-2 py-3 hover:bg-surface-gray-1 [&_mark]:bg-surface-amber-2 [&_mark]:text-ink-gray-9"
            @click="remember"
          >
            <Avatar :label="userById(r.authorId).name" size="lg" class="mt-0.5" />
            <div class="min-w-0 flex-1">
              <div class="flex items-center gap-1.5 text-sm text-ink-gray-5">
                <span class="text-ink-gray-7">{{ userById(r.authorId).name }}</span>
                <span>· {{ r.reply ? 'Reply' : 'Thread' }}</span>
                <span class="ml-auto shrink-0 text-xs">{{ when(r.at * 1000).fromNow() }}</span>
              </div>
              <div class="mt-1 truncate text-base text-ink-gray-9" v-html="r.title" />
              <div class="mt-1 line-clamp-2 text-p-sm text-ink-gray-6" v-html="r.snippet" />
            </div>
          </RouterLink>
        </div>
      </div>
    </div>
  </div>
</template>
