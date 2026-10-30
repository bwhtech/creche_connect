<script setup lang="ts">
import { computed, ref, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useStorage } from '@vueuse/core'
import { Avatar, Badge, Breadcrumbs, Button, Dialog, Dropdown, LoadingIndicator, PageHeader, Progress, TextInput, Tooltip, toast } from 'frappe-ui'
import { Editor, EditorContent, RichTextKit } from 'frappe-ui/editor'
import AudienceChips from '../components/AudienceChips.vue'
import MessageItem from '../components/MessageItem.vue'
import TagChips from '../components/TagChips.vue'
import Reactions from '../components/Reactions.vue'
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
  matchesGeo,
  placeById,
  placePath,
  state,
  excerpt,
  when,
  errorText,
  colorOf,
  canDelete,
  isAuthor,
  updateMessage,
  deleteThread,
  deleteReply,
} from '../lib/store'

const props = defineProps<{ id: string }>()
const me = useMe()
const thread = ref<any>(null)
const loading = ref(true)
const visible = computed(() => !!thread.value)
const author = computed(() => thread.value && userById(thread.value.authorId))
const reach = computed(() => (thread.value ? reachOf(thread.value) : 0))
const geoPlaces = computed(() => (thread.value?.geo?.places ?? []).map(placeById).filter(Boolean))
const viaGeo = computed(() => thread.value?.geo && matchesGeo(me.value, thread.value.geo))
const seenPct = computed(() => (reach.value ? Math.min(100, Math.round((thread.value.seenBy.length / reach.value) * 100)) : 0))

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
    markRead(t)
  } catch (e) {
    thread.value = null
    removed.value = e?.exc_type === 'DoesNotExistError'
  } finally {
    loading.value = false
  }
}
watch(() => props.id, () => ((loading.value = true), load()), { immediate: true })
watch(
  () => state.activity,
  (a) => a?.thread === props.id && load(),
)

const drafts = useStorage<Record<string, string>>(`samvaad:reply-drafts:${me.value.id}`, {})
const reply = computed({ get: () => drafts.value[props.id] ?? '', set: (v) => (drafts.value[props.id] = v) })
const replyEmpty = computed(() => !excerpt(reply.value))
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
  if (!id || !thread.value) return
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
const threadMenu = computed(() => [
  isAuthor(thread.value.authorId) && { label: 'Edit', icon: 'lucide-pencil', onClick: () => (editing.value = { title: thread.value.title, body: thread.value.body }) },
  { label: 'Delete', icon: 'lucide-trash-2', theme: 'red', onClick: () => confirmDelete() },
].filter(Boolean))
async function saveEdit() {
  saving.value = true
  try {
    await updateMessage(thread.value, 'Samvaad Thread', editing.value!.body, editing.value!.title)
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
    <PageHeader>
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
          <div class="mx-auto max-w-[770px] px-3 pt-10 pb-12 sm:px-6">
            <AudienceChips :geo="thread.geo" />
            <TextInput v-if="editing" v-model="editing.title" class="mt-4" size="lg" aria-label="Topic" />
            <h1 v-else class="mt-4 text-3xl font-semibold text-ink-gray-9">{{ thread.title }}</h1>
            <div class="mt-4 flex items-center gap-2.5">
              <Avatar :label="author.name" size="md" />
              <span class="text-sm text-ink-gray-8">{{ author.name }}</span>
              <span class="text-sm text-ink-gray-5">{{ author.title }} · {{ when(thread.createdAt).fromNow() }}</span>
              <Tooltip v-if="thread.editedAt" :text="`Edited ${when(thread.editedAt).format('DD MMM YYYY, h:mm A')}`">
                <span class="text-sm text-ink-gray-5">(edited)</span>
              </Tooltip>
              <Dropdown
                v-if="canDelete(thread.authorId) && !editing"
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
                <Editor v-model="editing.body" :extensions="[RichTextKit]">
                  <EditorContent class="rich min-h-[10rem] px-3 py-2 text-p-md text-ink-gray-8" />
                </Editor>
              </div>
              <div class="mt-2 flex justify-end gap-2">
                <Button label="Cancel" @click="editing = null" />
                <Button variant="solid" theme="gray" label="Save" :disabled="!editing.title.trim() || !excerpt(editing.body)" :loading="saving" @click="saveEdit" />
              </div>
            </div>
            <div v-else class="rich mt-8 text-p-md text-ink-gray-8" v-html="thread.body" />
            <div class="mt-10 space-y-6 border-t border-outline-gray-1 pt-6">
              <TagChips v-if="thread.tags.length" :tags="thread.tags" />
              <div><Reactions :target="thread" doctype="Samvaad Thread" /></div>
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
              <MessageItem
                v-for="(m, i) in thread.replies"
                :id="`reply-${m.id}`"
                :key="m.id"
                :message="m"
                :compact="sameAuthor(i)"
                class="transition-colors duration-700"
                :class="{ 'bg-surface-amber-1': highlighted === m.id }"
                @delete="confirmDelete(m)"
              />
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
                    <Editor v-model="reply" :extensions="[RichTextKit]" placeholder="Write a reply…  (Ctrl + Enter to send)">
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

      <aside class="hidden w-[20rem] shrink-0 overflow-y-auto border-l border-outline-gray-1 lg:block">
        <div class="space-y-8 p-6">
          <section>
            <h2 class="text-sm text-ink-gray-5">Audience</h2>
            <div class="mt-3 space-y-2">
              <div v-for="p in geoPlaces" :key="p.id" class="flex items-center gap-2.5 py-1">
                <span class="inline-flex size-6 shrink-0 items-center justify-center rounded-4" :class="[colorOf(p.color).soft, colorOf(p.color).ink]">
                  <span class="lucide-map-pin size-3.5" aria-hidden="true" />
                </span>
                <div class="min-w-0">
                  <div class="truncate text-sm text-ink-gray-8">{{ p.name }}</div>
                  <div class="truncate text-xs text-ink-gray-5">{{ p.kind }}{{ p.parent ? ` · ${p.parent}` : '' }}</div>
                </div>
              </div>
              <div v-if="thread.geo" class="pt-1 text-xs text-ink-gray-5">
                {{ thread.geo.designations.length ? thread.geo.designations.join(', ') : 'Every designation' }}
              </div>
            </div>
            <div class="mt-3 flex justify-between border-t border-outline-gray-1 pt-3 text-sm">
              <span class="text-ink-gray-6">Unique people</span>
              <span class="text-ink-gray-9 tabular-nums">{{ reach }}</span>
            </div>
          </section>

          <section>
            <h2 class="text-sm text-ink-gray-5">Seen</h2>
            <div class="mt-2 flex items-baseline justify-between">
              <span class="text-xl text-ink-gray-9 tabular-nums">{{ seenPct }}%</span>
              <span class="text-xs text-ink-gray-5 tabular-nums">{{ thread.seenBy.length }} of {{ reach }}</span>
            </div>
            <Progress class="mt-2" :value="seenPct" />
          </section>

          <section v-if="thread.ackRequired">
            <h2 class="text-sm text-ink-gray-5">Acknowledged</h2>
            <div class="mt-2.5 flex items-center gap-2">
              <div class="flex -space-x-1.5">
                <Tooltip v-for="uid in thread.acks.slice(0, 6)" :key="uid" :text="userById(uid).name">
                  <Avatar :label="userById(uid).name" size="sm" class="ring-2 ring-surface-base" />
                </Tooltip>
              </div>
              <span class="text-sm text-ink-gray-7 tabular-nums">{{ thread.acks.length }} of {{ reach }}</span>
            </div>
          </section>

          <section>
            <h2 class="text-sm text-ink-gray-5">Your access</h2>
            <div class="mt-2.5 flex flex-wrap gap-1">
              <Badge v-if="thread.authorId === me.id" label="You started this" theme="blue" variant="subtle" />
              <Badge v-if="viaGeo" :label="`Via ${placePath(me.place)}`" :theme="geoPlaces[0]?.color ?? 'blue'" variant="subtle" />
            </div>
            <p class="mt-2 text-p-xs text-ink-gray-5">{{ thread.canReply ? 'You can reply.' : 'You can read but not reply.' }}</p>
          </section>
        </div>
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
  </div>
</template>
