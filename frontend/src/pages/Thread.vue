<script setup lang="ts">
import { computed, ref, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useStorage } from '@vueuse/core'
import { Avatar, Badge, BottomSheet, Breadcrumbs, Button, Dialog, Dropdown, LoadingIndicator, PageHeader, PageHeaderBackButton, PageHeaderMobile, TextInput, Tooltip, dialog, toast } from 'frappe-ui'
import { Editor, EditorContent } from 'frappe-ui/editor'
import AudienceChips from '../components/AudienceChips.vue'
import MessageItem from '../components/MessageItem.vue'
import TagChips from '../components/TagChips.vue'
import Reactions from '../components/Reactions.vue'
import EditHistory from '../components/EditHistory.vue'
import Poll from '../components/Poll.vue'
import ThreadInfo from '../components/ThreadInfo.vue'
import {
  useMe,
  fetchThread,
  fetchOlderReplies,
  acknowledge,
  addReply,
  markRead,
  userById,
  reachOf,
  policyOf,
  state,
  isBlank,
  when,
  errorText,
  canDelete,
  isAuthor,
  updateMessage,
  deleteThread,
  deleteReply,
  editorKit,
  closePoll,
  isMobile,
} from '../lib/store'

const props = defineProps<{ id: string }>()
const me = useMe()
const thread = ref<any>(null)
const loading = ref(true)
const visible = computed(() => !!thread.value)
const author = computed(() => thread.value && userById(thread.value.authorId))
const reach = computed(() => (thread.value ? reachOf(thread.value) : 0))
const showInfo = ref(false)
const seenBefore = ref<string | null>()
const firstNew = computed(() => {
  const since = seenBefore.value
  return since ? (thread.value?.replies ?? []).findIndex((r) => r.at > since && r.authorId !== me.value.id) : -1
})

const removed = ref(false)
const unavailable = computed(() =>
  removed.value
    ? { icon: 'lucide-trash-2', title: 'This thread was removed', text: "It was deleted, so it can't be opened." }
    : { icon: 'lucide-lock', title: "You can't see this thread", text: "It was sent to a place or designation that doesn't include you." },
)
async function load() {
  try {
    const t = await fetchThread(props.id)
    if (!t) return
    thread.value = t
    if (seenBefore.value === undefined) seenBefore.value = t.lastVisit
    markRead(t)
  } catch (e) {
    thread.value = null
    removed.value = e?.exc_type === 'DoesNotExistError'
  } finally {
    loading.value = false
  }
}
watch(() => props.id, () => ((loading.value = true), (seenBefore.value = undefined), load()), { immediate: true })
watch(
  () => state.activity,
  (a) => a?.thread === props.id && load(),
)

const drafts = useStorage<Record<string, string>>(`crecheconnect:reply-drafts:${me.value.id}`, {})
const reply = computed({ get: () => drafts.value[props.id] ?? '', set: (v) => (drafts.value[props.id] = v) })
const replyEmpty = computed(() => isBlank(reply.value))
const sending = ref(false)
const scroller = ref<HTMLElement>()
async function send() {
  if (replyEmpty.value || sending.value) return
  sending.value = true
  const id = props.id
  try {
    await addReply(thread.value, reply.value)
    delete drafts.value[id]
    nextTick(() => scroller.value?.scrollTo({ top: scroller.value.scrollHeight, behavior: 'smooth' }))
  } catch (e) {
    toast.error(errorText(e, 'Could not send your reply'))
  } finally {
    sending.value = false
  }
}
function onKey(e: KeyboardEvent) {
  if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) send()
}
const acking = ref(false)
async function ack() {
  acking.value = true
  try {
    await acknowledge(thread.value)
    toast.success('Acknowledged')
  } catch (e) {
    toast.error(errorText(e, 'Could not acknowledge'))
  } finally {
    acking.value = false
  }
}

const replyBlock = computed(() =>
  thread.value.policy === 'none'
    ? { icon: 'lucide-megaphone', text: 'This is an announcement. Replies are off.' }
    : { icon: 'lucide-shield', text: 'Only people who can start threads can reply here.' },
)
const loadingOlder = ref(false)
async function loadOlder() {
  loadingOlder.value = true
  try {
    const page: any = await fetchOlderReplies(thread.value.id, thread.value.replies[0].id)
    thread.value.replies.unshift(...page.replies)
    thread.value.hasOlder = page.hasOlder
  } catch (e) {
    toast.error(errorText(e, 'Could not load older replies'))
  } finally {
    loadingOlder.value = false
  }
}

const router = useRouter()
const route = useRoute()
const highlighted = ref<string | null>(null)
async function revealReply() {
  const id = route.query.reply as string | undefined
  const loaded = () => thread.value.replies.some((r) => r.id === id)
  if (!thread.value) return
  if (!id) {
    await nextTick()
    return document.getElementById('new-replies')?.scrollIntoView({ block: 'center' })
  }
  while (!loaded() && thread.value.hasOlder) {
    const count = thread.value.replies.length
    await loadOlder()
    if (thread.value.replies.length === count) return
  }
  highlighted.value = id
  await nextTick()
  document.getElementById(`reply-${id}`)?.scrollIntoView({ block: 'center' })
  setTimeout(() => (highlighted.value = null), 2500)
}
watch(() => [thread.value?.id, route.query.reply], revealReply)

const editing = ref<{ title: string; body: string } | null>(null)
const saving = ref(false)
const showHistory = ref(false)
const threadMenu = computed(() => [
  isAuthor(thread.value.authorId) && { label: 'Edit', icon: 'lucide-pencil', onClick: () => (editing.value = { title: thread.value.title, body: thread.value.body }) },
  thread.value.editedAt && { label: 'Edit history', icon: 'lucide-history', onClick: () => (showHistory.value = true) },
  thread.value.poll?.canManage && !thread.value.poll.closed && { label: 'Close poll', icon: 'lucide-lock', onClick: confirmClose },
  canDelete(thread.value.authorId) && { label: 'Delete', icon: 'lucide-trash-2', theme: 'red', onClick: () => confirmDelete() },
].filter(Boolean))
function confirmClose() {
  dialog.confirm({
    title: 'Close this poll?',
    message: 'Nobody can vote or change their vote after this. Results stay visible.',
    confirmLabel: 'Close poll',
    onConfirm: async () => {
      await closePoll(thread.value)
      toast.success('Poll closed')
    },
  })
}
async function saveEdit() {
  saving.value = true
  try {
    await updateMessage(thread.value, 'CrecheConnect Thread', editing.value!.body, editing.value!.title)
    editing.value = null
  } catch (e) {
    toast.error(errorText(e, 'Could not save your changes'))
  } finally {
    saving.value = false
  }
}

const deleting = ref({ open: false, reply: null as any })
const confirmDelete = (reply = null) => (deleting.value = { open: true, reply })
const deleteActions = [
  { label: 'Cancel', onClick: ({ close }) => close() },
  { label: 'Delete', variant: 'solid', theme: 'red', onClick: remove },
]
async function remove({ close }) {
  const { reply } = deleting.value
  try {
    if (reply) await deleteReply(thread.value, reply)
    else await deleteThread(thread.value)
    close()
    toast.success(reply ? 'Reply deleted' : 'Thread deleted')
    if (!reply) router.push('/')
  } catch (e) {
    toast.error(errorText(e, 'Could not delete'))
  }
}

const sameAuthor = (i: number) => i > 0 && thread.value.replies[i - 1].authorId === thread.value.replies[i].authorId
</script>

<template>
  <div class="flex h-full flex-col">
    <PageHeaderMobile v-if="isMobile" :title="thread?.title ?? 'Thread'">
      <template #prefix><PageHeaderBackButton :fallback-route="{ path: '/' }" /></template>
      <template v-if="visible" #suffix>
        <Button variant="ghost" icon="lucide-info" aria-label="Thread details" @click="showInfo = true" />
      </template>
    </PageHeaderMobile>
    <PageHeader v-else>
      <Breadcrumbs :items="[{ label: 'Feed', route: { path: '/' } }, { label: thread?.title ?? 'Thread' }]" />
    </PageHeader>

    <div v-if="loading" class="flex flex-1 items-center justify-center">
      <LoadingIndicator class="size-5 text-ink-gray-5" />
    </div>

    <div v-else-if="!visible" class="flex flex-1 flex-col items-center justify-center gap-3 text-center">
      <div class="rounded-full bg-surface-gray-2 p-3 text-ink-gray-5">
        <span :class="unavailable.icon" class="size-6" aria-hidden="true" />
      </div>
      <p class="text-base text-ink-gray-7">{{ unavailable.title }}</p>
      <p class="max-w-sm text-p-sm text-ink-gray-5">{{ unavailable.text }}</p>
      <Button label="Back to feed" route="/" class="mt-2" />
    </div>

    <div v-else class="flex min-h-0 flex-1">
      <div class="flex min-w-0 flex-1 flex-col">
        <div ref="scroller" class="min-h-0 flex-1 overflow-y-auto">
          <div class="mx-auto max-w-[770px] px-4 pt-5 pb-12 sm:px-6 md:pt-10">
            <AudienceChips :geo="thread.geo" />
            <TextInput v-if="editing" v-model="editing.title" class="mt-4" size="lg" aria-label="Topic" />
            <h1 v-else class="mt-4 text-2xl font-semibold text-ink-gray-9 md:text-3xl">{{ thread.title }}</h1>
            <div class="mt-4 flex items-center gap-2.5">
              <Avatar :label="author.name" size="md" />
              <span class="shrink-0 text-sm text-ink-gray-8">{{ author.name }}</span>
              <span class="truncate text-sm text-ink-gray-5"><span class="max-md:hidden">{{ author.title }} · </span>{{ when(thread.createdAt).fromNow() }}</span>
              <Tooltip v-if="thread.editedAt" :text="`Edited ${when(thread.editedAt).format('DD MMM YYYY, h:mm A')}`">
                <span class="text-sm text-ink-gray-5">(edited)</span>
              </Tooltip>
              <Dropdown
                v-if="threadMenu.length && !editing"
                class="ml-auto"
                align="end"
                :options="threadMenu"
                :button="{ icon: 'lucide-ellipsis', variant: 'ghost', 'aria-label': 'Thread actions' }"
              />
            </div>

            <div v-if="thread.needsAck" class="mt-8 flex items-center gap-3 rounded-5 bg-surface-amber-2 px-4 py-3.5">
              <span class="lucide-badge-check size-5 shrink-0 text-ink-amber-6" aria-hidden="true" />
              <p class="flex-1 text-p-sm text-ink-gray-8">
                {{ author.name.split(' ')[0] }} asked everyone in the audience to acknowledge this thread.
              </p>
              <Button variant="solid" theme="gray" label="Acknowledge" :loading="acking" @click="ack" />
            </div>

            <div v-if="editing" class="mt-8">
              <div class="rounded-4 border border-outline-gray-2 bg-surface-base">
                <Editor v-model="editing.body" :extensions="editorKit">
                  <EditorContent class="rich min-h-[10rem] px-3 py-2 text-p-md text-ink-gray-8" />
                </Editor>
              </div>
              <div class="mt-2 flex justify-end gap-2">
                <Button label="Cancel" @click="editing = null" />
                <Button variant="solid" theme="gray" label="Save" :disabled="!editing.title.trim() || isBlank(editing.body)" :loading="saving" @click="saveEdit" />
              </div>
            </div>
            <div v-else class="rich mt-8 text-p-md text-ink-gray-8" v-html="thread.body" />
            <Poll v-if="thread.poll" :thread="thread" class="mt-8" />
            <div class="mt-10 space-y-6 border-t border-outline-gray-1 pt-6">
              <TagChips v-if="thread.tags.length" :tags="thread.tags" />
              <div><Reactions :target="thread" doctype="CrecheConnect Thread" /></div>
            </div>

            <div class="mt-12 flex items-center gap-2 border-b border-outline-gray-1 pb-3">
              <span class="text-lg-semibold text-ink-gray-8">
                {{ thread.replyCount }} {{ thread.replyCount === 1 ? 'reply' : 'replies' }}
              </span>
              <Badge :label="policyOf(thread.policy).short" :theme="policyOf(thread.policy).theme" variant="subtle" size="sm" class="ml-auto">
                <template #prefix><span :class="policyOf(thread.policy).icon" class="size-3" aria-hidden="true" /></template>
              </Badge>
            </div>
            <div class="-mx-2 space-y-1 pt-3">
              <Button v-if="thread.hasOlder" class="mx-2 mb-2" variant="ghost" label="Load older replies" :loading="loadingOlder" @click="loadOlder" />
              <template v-for="(m, i) in thread.replies" :key="m.id">
                <div v-if="i === firstNew" id="new-replies" class="flex items-center gap-2 px-2 py-1 text-xs font-medium text-ink-red-4">
                  <span class="h-px flex-1 bg-surface-red-4" aria-hidden="true" />New
                </div>
                <MessageItem
                  :id="`reply-${m.id}`"
                  :message="m"
                  :compact="sameAuthor(i) && i !== firstNew"
                  class="transition-colors duration-700"
                  :class="{ 'bg-surface-amber-1': highlighted === m.id }"
                  @delete="confirmDelete(m)"
                />
              </template>
              <p v-if="!thread.replies.length" class="px-2 py-8 text-sm text-ink-gray-5">No replies yet.</p>
            </div>
          </div>
        </div>

        <div class="border-t border-outline-gray-1 bg-surface-base">
          <div class="mx-auto max-w-[770px] px-3 py-4 sm:px-6">
            <template v-if="thread.canReply">
              <div class="flex items-end gap-2" @keydown="onKey">
                <div class="flex-1">
                  <div class="rounded-4 border border-outline-gray-2 bg-surface-base">
                    <Editor v-model="reply" :extensions="editorKit" :placeholder="isMobile ? 'Write a reply…' : 'Write a reply…  (Ctrl + Enter to send)'">
                      <EditorContent class="rich max-h-60 min-h-[3.5rem] overflow-y-auto px-3 py-2 text-p-base text-ink-gray-8" />
                    </Editor>
                  </div>
                </div>
                <Button variant="solid" theme="gray" icon="lucide-send-horizontal" size="md" :disabled="replyEmpty" :loading="sending" @click="send" />
              </div>
              <p class="mt-2 text-xs text-ink-gray-5">Visible to {{ reach }} people in this thread's audience</p>
            </template>
            <div v-else class="flex items-center gap-2 rounded-4 bg-surface-gray-2 px-3 py-3 text-sm text-ink-gray-6">
              <span :class="replyBlock.icon" class="size-4 shrink-0" aria-hidden="true" />
              {{ replyBlock.text }}
            </div>
          </div>
        </div>
      </div>

      <aside v-if="!isMobile" class="hidden w-[20rem] shrink-0 overflow-y-auto border-l border-outline-gray-1 lg:block">
        <ThreadInfo :thread="thread" :reach="reach" />
      </aside>
    </div>

    <Dialog
      v-model:open="deleting.open"
      :title="deleting.reply ? 'Delete this reply?' : 'Delete this thread?'"
      :message="deleting.reply ? 'The reply and its reactions will be removed.' : 'All replies, reactions and acknowledgements in it will be removed too.'"
      icon="lucide-trash-2"
      theme="red"
      :actions="deleteActions"
    />
    <BottomSheet v-if="visible" v-model:open="showInfo" title="Thread details">
      <ThreadInfo :thread="thread" :reach="reach" class="pb-[env(safe-area-inset-bottom)]" />
    </BottomSheet>
    <EditHistory v-if="showHistory" v-model:open="showHistory" doctype="CrecheConnect Thread" :name="thread.id" />
  </div>
</template>
