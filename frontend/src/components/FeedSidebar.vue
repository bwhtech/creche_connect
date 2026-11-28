<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { __ } from '../lib/translate'
import { state, colorOf, get, userById, when } from '../lib/store'

const route = useRoute()
const router = useRouter()

const active = computed(() => route.query.tag as string | undefined)
const tags = computed(() => [
  { id: undefined, name: __('All posts'), dot: 'bg-surface-gray-5', count: state.counts.total },
  ...state.tags
    .map((t) => ({ id: t.id, name: t.name, dot: colorOf(t.color).dot, count: state.counts.tags[t.id] ?? 0 }))
    .filter((t) => t.count),
])
const setTag = (id?: string) => router.push({ path: '/', query: { ...route.query, tag: id } })

const acks = ref<any[]>([])
watch(
  () => state.counts.ack,
  async (count, _, onCleanup) => {
    if (!count) {
      acks.value = []
      return
    }
    let current = true
    onCleanup(() => { current = false })
    const page: any = await get('creche_connect.api.get_threads', { filter: 'ack' }).catch(() => null)
    if (current && page) acks.value = page.threads.slice(0, 5)
  },
  { immediate: true },
)
</script>

<template>
  <aside class="w-[20rem] shrink-0 divide-y divide-outline-gray-1 overflow-y-auto border-l border-outline-gray-1 px-3 pt-2 pb-10">
    <section class="py-4">
      <h2 class="mb-2 px-2 text-sm text-ink-gray-5">{{ __('Tags') }}</h2>
      <button
        v-for="t in tags"
        :key="t.id ?? ''"
        type="button"
        class="flex h-8 w-full items-center gap-2.5 rounded-4 px-2 text-left text-base"
        :class="active === t.id ? 'bg-surface-gray-2 text-ink-gray-9' : 'text-ink-gray-7 hover:bg-surface-gray-1'"
        :aria-pressed="active === t.id"
        @click="setTag(t.id)"
      >
        <span class="size-2 shrink-0 rounded-full" :class="t.dot" aria-hidden="true" />
        <span class="flex-1 truncate">{{ t.name }}</span>
        <span class="text-sm text-ink-gray-5 tabular-nums">{{ t.count }}</span>
      </button>
    </section>

    <section class="py-4">
      <div class="mb-2 flex items-center gap-2 px-2">
        <h2 class="text-sm text-ink-gray-5">{{ __('Needs your acknowledgment') }}</h2>
        <span v-if="state.counts.ack" class="text-sm text-ink-gray-5 tabular-nums">{{ state.counts.ack }}</span>
        <RouterLink v-if="state.counts.ack" to="/?filter=ack" class="ml-auto text-sm text-ink-gray-6 hover:text-ink-gray-8">{{ __('See all') }}</RouterLink>
      </div>
      <p v-if="!acks.length" class="flex items-center gap-2 px-2 py-1.5 text-sm text-ink-gray-5">
        <span class="lucide-circle-check size-4 text-ink-green-5" aria-hidden="true" />
        {{ __('Nothing to acknowledge') }}
      </p>
      <RouterLink v-for="t in acks" :key="t.id" :to="`/threads/${t.id}`" class="flex gap-2.5 rounded-4 px-2 py-1.5 hover:bg-surface-gray-1">
        <span class="mt-1.5 size-2 shrink-0 rounded-full bg-surface-blue-7" aria-hidden="true" />
        <span class="min-w-0">
          <span class="line-clamp-2 text-p-sm text-ink-gray-8">{{ t.title }}</span>
          <span class="text-xs text-ink-gray-5">{{ userById(t.authorId).name }} · {{ when(t.lastActivity).fromNow() }}</span>
        </span>
      </RouterLink>
    </section>
  </aside>
</template>
