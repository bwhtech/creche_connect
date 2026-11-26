<script setup lang="ts">
import { computed, ref, shallowRef } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { useResizeObserver } from '@vueuse/core'
import { Avatar, Badge, Button, LoadingIndicator, toast } from 'frappe-ui'
import AudienceChips from './AudienceChips.vue'
import MessageItem from './MessageItem.vue'
import Poll from './Poll.vue'
import { Editor, EditorContent } from 'frappe-ui/editor'
import TagChips from './TagChips.vue'
import Reactions from './Reactions.vue'
import ReshareButton from './ReshareButton.vue'
import FileViewer from './FileViewer.vue'
import { shareThread, userById, policyOf, when, fetchLatestReplies, editorKit, audienceOf, confirmDelete, errorText, addReply, isBlank, state, replyDraft, clearDraft, withPreviews } from '../lib/store'

const props = defineProps<{ thread: any }>()
const router = useRouter()
const to = computed(() => `/threads/${props.thread.id}`)
const html = computed(() => withPreviews(props.thread.body))
const body = ref<HTMLElement>()
const clipped = ref(false)
useResizeObserver(body, () => (clipped.value = body.value!.scrollHeight > body.value!.clientHeight + 1))

const viewing = ref<{ url: string; name: string } | null>(null)
function open(e: MouseEvent) {
  if (e.target instanceof HTMLImageElement && body.value?.contains(e.target)) {
    viewing.value = { url: e.target.src, name: e.target.alt || props.thread.title }
    return
  }
  const controls = 'a, button, input, audio, video, [role=button]'
  if (e.composedPath().some((el) => el instanceof Element && el.matches(controls)) || getSelection()?.toString()) return
  router.push(to.value)
}

const expanded = ref(false)
const latest = ref<any>(null)
const kit = shallowRef<any[]>()
async function toggle() {
  expanded.value = !expanded.value
  if (!expanded.value) return
  kit.value ??= editorKit(() => audienceOf(props.thread.geo, props.thread.authorId))
  try {
    const page: any = await fetchLatestReplies(props.thread.id, 3)
    latest.value = { id: props.thread.id, replyCount: props.thread.replyCount, replies: page.replies }
  } catch (e) {
    expanded.value = false
    toast.error(errorText(e, 'Could not load replies'))
  }
}
const shown = computed(() => latest.value.replies.slice(-3))
const draft = replyDraft(() => props.thread.id)
const sending = ref(false)
async function send() {
  if (isBlank(draft.value) || sending.value) return
  sending.value = true
  try {
    await addReply(latest.value, draft.value)
    clearDraft(props.thread.id)
  } catch (e) {
    toast.error(errorText(e, 'Could not send your reply'))
  } finally {
    sending.value = false
  }
}
function onKey(e: KeyboardEvent) {
  if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) send()
}
</script>

<template>
  <div
    class="cursor-pointer overflow-hidden rounded-5 border border-outline-gray-1 bg-surface-base transition-shadow hover:border-outline-gray-2 hover:shadow-sm"
    @click="open"
  >
    <div class="flex gap-3 p-4 md:gap-4 md:p-5">
      <Avatar :label="userById(thread.authorId).name" :image="userById(thread.authorId).image" size="lg" class="mt-0.5 max-md:hidden" />
      <div class="min-w-0 flex-1">
        <p v-if="thread.resharedBy" class="mb-1.5 flex items-center gap-1.5 text-xs text-ink-gray-6">
          <span class="lucide-repeat-2 size-3.5" aria-hidden="true" />{{ userById(thread.resharedBy).name }} reshared
        </p>
        <div class="flex items-center gap-2 text-sm">
          <span class="shrink-0 text-ink-gray-8">{{ userById(thread.authorId).name }}</span>
          <span class="truncate text-ink-gray-6">{{ userById(thread.authorId).designation }}</span>
          <span class="ml-auto shrink-0 text-xs text-ink-gray-6">{{ when(thread.lastActivity).fromNow() }}</span>
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
        <Poll v-if="thread.poll" :thread="thread" class="mt-3 cursor-auto" @click.stop />

        <div class="mt-4 flex flex-wrap items-center gap-2">
          <AudienceChips :geo="thread.geo" />
          <Badge v-if="thread.policy !== 'everyone'" :label="policyOf(thread.policy).short" :theme="policyOf(thread.policy).theme" variant="outline" size="sm">
            <template #prefix><span :class="policyOf(thread.policy).icon" class="size-3" aria-hidden="true" /></template>
          </Badge>
          <Badge v-if="thread.needsAck" label="Needs your acknowledgment" theme="blue" variant="solid" size="sm" />
          <TagChips v-if="thread.tags.length" :tags="thread.tags" />
        </div>
      </div>
    </div>
    <div class="flex items-center gap-3 border-t border-outline-gray-1 bg-surface-gray-1 py-2 pr-4 pl-2.5 md:pr-5 md:pl-[4.25rem]">
      <Reactions :target="thread" doctype="CrecheConnect Thread" />
      <Button
        variant="ghost"
        size="sm"
        icon-left="lucide-message-square"
        :class="expanded && '!bg-surface-gray-3'"
        :aria-label="expanded ? 'Hide replies' : 'Show replies'"
        :aria-expanded="expanded"
        @click="toggle"
      >
        {{ thread.replyCount }}
      </Button>
      <ReshareButton :thread="thread" />
      <Button variant="ghost" size="sm" icon="lucide-share-2" aria-label="Share" @click="shareThread(thread)" />
    </div>
    <div v-if="expanded" class="cursor-auto bg-surface-gray-1 px-2 pt-1 pb-3 reply-preview md:pr-5 md:pl-[3.75rem]" @click.stop>
      <LoadingIndicator v-if="!latest" class="mx-auto my-4 size-5 text-ink-gray-6" />
      <template v-else>
        <RouterLink v-if="thread.replyCount > shown.length" :to="to" class="mx-2 block py-1 text-sm font-medium text-ink-gray-6 hover:text-ink-gray-8">
          View all {{ thread.replyCount }} replies
        </RouterLink>
        <MessageItem v-for="m in shown" :key="m.id" :message="m" :kit="kit" @delete="confirmDelete(latest, m)" />
        <p v-if="!shown.length && !thread.canReply" class="px-2 py-2 text-sm text-ink-gray-6">No replies yet.</p>
        <div v-if="thread.canReply" class="mt-2 flex items-end gap-3 px-2" @keydown="onKey">
          <Avatar :label="state.me.name" :image="state.me.image" size="lg" class="mb-0.5 max-md:hidden" />
          <div class="min-w-0 flex-1 rounded-4 border border-outline-gray-2 bg-surface-base">
            <Editor v-model="draft" :extensions="kit" :placeholder="shown.length ? 'Write a reply…' : 'Be the first to reply…'">
              <div class="flex items-end">
                <EditorContent class="rich max-h-40 min-h-[2.25rem] flex-1 overflow-y-auto px-3 py-1.5 text-p-base text-ink-gray-8" />
                <Button class="m-1" variant="ghost" icon="lucide-send-horizontal" aria-label="Send reply" :disabled="isBlank(draft)" :loading="sending" @click="send" />
              </div>
            </Editor>
          </div>
        </div>
      </template>
    </div>
    <FileViewer :file="viewing" @close="viewing = null" />
  </div>
</template>
