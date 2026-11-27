<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { Avatar, Button, LoadingIndicator, toast } from 'frappe-ui'
import { Editor, EditorContent } from 'frappe-ui/editor'
import MessageItem from './MessageItem.vue'
import { editorKit } from '../lib/editor'
import { __ } from '../lib/translate'
import { audienceOf, confirmDelete, errorText, addReply, isBlank, state, replyDraft, clearDraft } from '../lib/store'

const props = defineProps<{ thread: any; replies: Promise<any> }>()
const emit = defineEmits<{ failed: [] }>()
const to = computed(() => `/threads/${props.thread.id}`)
const latest = ref<any>(null)
const kit = editorKit(() => audienceOf(props.thread.geo, props.thread.authorId))
onMounted(async () => {
  try {
    const page: any = await props.replies
    latest.value = { id: props.thread.id, replyCount: props.thread.replyCount, replies: page.replies }
  } catch (e) {
    emit('failed')
    toast.error(errorText(e, __('Could not load replies')))
  }
})
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
    toast.error(errorText(e, __('Could not send your reply')))
  } finally {
    sending.value = false
  }
}
function onKey(e: KeyboardEvent) {
  if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) send()
}
</script>

<template>
  <div class="cursor-auto bg-surface-gray-1 px-2 pt-1 pb-3 reply-preview md:pr-5 md:pl-[3.75rem]" @click.stop>
    <LoadingIndicator v-if="!latest" class="mx-auto my-4 size-5 text-ink-gray-6" />
    <template v-else>
      <RouterLink v-if="thread.replyCount > shown.length" :to="to" class="mx-2 block py-1 text-sm font-medium text-ink-gray-6 hover:text-ink-gray-8">
        {{ __('View all {0} replies', thread.replyCount) }}
      </RouterLink>
      <MessageItem v-for="m in shown" :key="m.id" :message="m" :kit="kit" @delete="confirmDelete(latest, m)" />
      <p v-if="!shown.length && !thread.canReply" class="px-2 py-2 text-sm text-ink-gray-6">{{ __('No replies yet.') }}</p>
      <div v-if="thread.canReply" class="mt-2 flex items-end gap-3 px-2" @keydown="onKey">
        <Avatar :label="state.me.name" :image="state.me.image" size="lg" class="mb-0.5 max-md:hidden" />
        <div class="min-w-0 flex-1 rounded-4 border border-outline-gray-2 bg-surface-base">
          <Editor v-model="draft" :extensions="kit" :placeholder="shown.length ? __('Write a reply…') : __('Be the first to reply…')">
            <div class="flex items-end">
              <EditorContent class="rich max-h-40 min-h-[2.25rem] flex-1 overflow-y-auto px-3 py-1.5 text-p-base text-ink-gray-8" />
              <Button class="m-1" variant="ghost" icon="lucide-send-horizontal" :aria-label="__('Send reply')" :disabled="isBlank(draft)" :loading="sending" @click="send" />
            </div>
          </Editor>
        </div>
      </div>
    </template>
  </div>
</template>
