<script setup lang="ts">
import { RouterLink } from 'vue-router'
import { Avatar, Badge } from 'frappe-ui'
import AudienceChips from './AudienceChips.vue'
import TagChips from './TagChips.vue'
import Reactions from './Reactions.vue'
import { excerpt, userById, policyOf, threadReach, when } from '../lib/store'

defineProps<{ thread: any }>()
</script>

<template>
  <RouterLink
    :to="`/threads/${thread.id}`"
    class="block overflow-hidden rounded-5 border border-outline-gray-1 bg-surface-base transition-shadow hover:border-outline-gray-2 hover:shadow-sm"
  >
    <div class="flex gap-4 p-5">
      <Avatar :label="userById(thread.authorId).name" size="lg" class="mt-0.5" />
      <div class="min-w-0 flex-1">
        <div class="flex items-center gap-2 text-sm">
          <span class="text-ink-gray-8">{{ userById(thread.authorId).name }}</span>
          <span class="truncate text-ink-gray-5">{{ userById(thread.authorId).designation }}</span>
          <span class="ml-auto shrink-0 text-xs text-ink-gray-5">{{ when(thread.lastActivity).fromNow() }}</span>
        </div>

        <div class="mt-2 flex items-center gap-2">
          <span class="truncate text-lg" :class="thread.unread ? 'font-semibold text-ink-gray-9' : 'text-ink-gray-8'">
            {{ thread.title }}
          </span>
          <span v-if="thread.unread" class="size-2 shrink-0 rounded-full bg-surface-blue-7" aria-label="Unread" />
        </div>
        <p class="mt-1.5 line-clamp-2 text-p-sm text-ink-gray-6">{{ excerpt(thread.body) }}</p>

        <div class="mt-4 flex flex-wrap items-center gap-2">
          <AudienceChips :geo="thread.geo" />
          <Badge v-if="thread.policy !== 'everyone'" :label="policyOf(thread.policy).short" :theme="policyOf(thread.policy).theme" variant="outline" size="sm">
            <template #prefix><span :class="policyOf(thread.policy).icon" class="size-3" aria-hidden="true" /></template>
          </Badge>
          <Badge v-if="thread.needsAck" label="Needs your acknowledgment" theme="amber" variant="solid" size="sm" />
          <TagChips v-if="thread.tags.length" :tags="thread.tags" />
        </div>
      </div>
    </div>
    <div class="flex items-center gap-3 border-t border-outline-gray-1 bg-surface-gray-1 py-2 pr-5 pl-[4.25rem]">
      <Reactions :target="thread" doctype="Samvaad Thread" />
      <div class="ml-auto flex items-center gap-4 text-xs text-ink-gray-5">
        <span class="flex items-center gap-1">
          <span class="lucide-message-square size-3.5" aria-hidden="true" />{{ thread.replyCount }}
          {{ thread.replyCount === 1 ? 'reply' : 'replies' }}
        </span>
        <span class="flex items-center gap-1">
          <span class="lucide-eye size-3.5" aria-hidden="true" />{{ thread.seenBy.length }} of {{ threadReach(thread) }} seen
        </span>
      </div>
    </div>
  </RouterLink>
</template>
