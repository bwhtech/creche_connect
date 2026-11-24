<script setup lang="ts">
import { computed, ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { useResizeObserver } from '@vueuse/core'
import { Avatar, Badge, Button } from 'frappe-ui'
import AudienceChips from './AudienceChips.vue'
import TagChips from './TagChips.vue'
import Reactions from './Reactions.vue'
import ReshareButton from './ReshareButton.vue'
import { shareThread, userById, policyOf, threadReach, when, isAuthor } from '../lib/store'

const props = defineProps<{ thread: any }>()
const router = useRouter()
const to = computed(() => `/threads/${props.thread.id}`)
const html = computed(() => props.thread.body.replaceAll('<img ', '<img loading="lazy" ').replaceAll('<video ', '<video preload="metadata" '))
const body = ref<HTMLElement>()
const clipped = ref(false)
useResizeObserver(body, () => (clipped.value = body.value!.scrollHeight > body.value!.clientHeight + 1))

function open(e: MouseEvent) {
  const controls = 'a, button, input, audio, video, [role=button]'
  if (e.composedPath().some((el) => el instanceof Element && el.matches(controls)) || getSelection()?.toString()) return
  router.push(to.value)
}
</script>

<template>
  <div
    class="cursor-pointer overflow-hidden rounded-5 border border-outline-gray-1 bg-surface-base transition-shadow hover:border-outline-gray-2 hover:shadow-sm"
    @click="open"
  >
    <div class="flex gap-3 p-4 md:gap-4 md:p-5">
      <Avatar :label="userById(thread.authorId).name" size="lg" class="mt-0.5 max-md:hidden" />
      <div class="min-w-0 flex-1">
        <p v-if="thread.resharedBy" class="mb-1.5 flex items-center gap-1.5 text-xs text-ink-gray-5">
          <span class="lucide-repeat-2 size-3.5" aria-hidden="true" />{{ userById(thread.resharedBy).name }} reshared
        </p>
        <div class="flex items-center gap-2 text-sm">
          <span class="shrink-0 text-ink-gray-8">{{ userById(thread.authorId).name }}</span>
          <span class="truncate text-ink-gray-5 max-md:hidden">{{ userById(thread.authorId).designation }}</span>
          <span class="ml-auto shrink-0 text-xs text-ink-gray-5">{{ when(thread.lastActivity).fromNow() }}</span>
        </div>

        <div class="mt-2 flex items-center gap-2">
          <RouterLink :to="to" class="text-lg max-md:line-clamp-2 md:truncate" :class="thread.unread ? 'font-semibold text-ink-gray-9' : 'text-ink-gray-8'">
            {{ thread.title }}
          </RouterLink>
          <span v-if="thread.unread" class="size-2 shrink-0 rounded-full bg-surface-blue-7" aria-label="Unread" />
        </div>
        <div
          ref="body"
          class="rich card-media mt-1.5 max-h-[44rem] text-p-sm text-ink-gray-7"
          :class="clipped && '[mask-image:linear-gradient(to_bottom,black_70%,transparent)]'"
          v-html="html"
        />
        <span v-if="clipped" class="text-sm text-ink-blue-link">Show more</span>

        <div class="mt-4 flex flex-wrap items-center gap-2">
          <AudienceChips :geo="thread.geo" />
          <Badge v-if="thread.policy !== 'everyone'" :label="policyOf(thread.policy).short" :theme="policyOf(thread.policy).theme" variant="outline" size="sm">
            <template #prefix><span :class="policyOf(thread.policy).icon" class="size-3" aria-hidden="true" /></template>
          </Badge>
          <Badge v-if="thread.needsAck" label="Needs your acknowledgment" theme="blue" variant="solid" size="sm" />
          <template v-if="thread.poll">
            <Badge :label="thread.poll.closed ? 'Poll closed' : 'Poll'" theme="violet" variant="outline" size="sm" class="!rounded-md">
              <template #prefix><span :class="thread.poll.closed ? 'lucide-lock' : 'lucide-chart-bar-big'" class="size-3" aria-hidden="true" /></template>
            </Badge>
            <Badge v-if="!thread.poll.closed && !thread.poll.voted && !isAuthor(thread.authorId)" label="Waiting for your vote" theme="violet" variant="solid" size="sm" />
          </template>
          <TagChips v-if="thread.tags.length" :tags="thread.tags" />
        </div>
      </div>
    </div>
    <div class="flex items-center gap-3 border-t border-outline-gray-1 bg-surface-gray-1 py-2 pr-4 pl-2.5 md:pr-5 md:pl-[4.25rem]">
      <Reactions :target="thread" doctype="CrecheConnect Thread" />
      <ReshareButton :thread="thread" />
      <Button variant="ghost" size="sm" icon="lucide-share-2" aria-label="Share" @click="shareThread(thread)" />
      <div class="ml-auto flex items-center gap-3 whitespace-nowrap text-xs text-ink-gray-5 md:gap-4">
        <span v-if="thread.poll" class="flex items-center gap-1 max-md:hidden">
          <span class="lucide-vote size-3.5" aria-hidden="true" />{{ thread.poll.voterCount }} voted
        </span>
        <span class="flex items-center gap-1">
          <span class="lucide-message-square size-3.5" aria-hidden="true" />{{ thread.replyCount }}
          {{ thread.replyCount === 1 ? 'reply' : 'replies' }}
        </span>
        <span class="flex items-center gap-1">
          <span class="lucide-eye size-3.5" aria-hidden="true" />{{ thread.seenCount }} of {{ threadReach(thread) }} seen
        </span>
      </div>
    </div>
  </div>
</template>
