<script setup lang="ts">
import { computed, nextTick, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useStorage } from '@vueuse/core'
import { Breadcrumbs, Button, DateTimePicker, FormControl, PageHeader, Switch, TabButtons, TextInput, toast } from 'frappe-ui'
import { Editor, EditorContent, EditorFixedMenu, minimalToolbar } from 'frappe-ui/editor'
import GeoPicker from '../components/GeoPicker.vue'
import AudienceChips from '../components/AudienceChips.vue'
import dayjs from 'dayjs'
import { state, editorKit, useMe, canStart, createThread, reachOf, toggleIn, colorOf, errorText, POLICIES } from '../lib/store'

const me = useMe()
const router = useRouter()
const key = `crecheconnect:compose-draft:${me.value.id}`
const text = useStorage(key, { title: '', body: '' })
const draft = useStorage(`${key}:audience`, { places: [] as string[], designations: [] as string[] })
const policy = useStorage(`${key}:policy`, 'everyone')
const ackRequired = useStorage(`${key}:ack`, false)
const picked = useStorage<string[]>(`${key}:tags`, [])
const addedTags = useStorage<any[]>(`${key}:new-tags`, [])
const kind = useStorage(`${key}:kind`, 'discussion')
const isPoll = computed(() => kind.value === 'poll')
const KINDS = [
  { label: 'Discussion', value: 'discussion' },
  { label: 'Poll', value: 'poll' },
]
const blankPoll = () => ({ options: ['', ''], multiple: false, anonymous: false, closesAt: '' })
const poll = useStorage(`${key}:poll`, blankPoll())
const filledOptions = computed(() => poll.value.options.map((o) => o.trim()).filter(Boolean))
const MAX_OPTIONS = 10
function insertOptions(at: number, labels: string[]) {
  const room = MAX_OPTIONS - poll.value.options.length + 1
  poll.value.options.splice(at, 1, ...labels.slice(0, room))
  const next = at + Math.min(labels.length, room)
  nextTick(() => document.querySelector<HTMLInputElement>(`[aria-label="Option ${Math.min(next, poll.value.options.length)}"]`)?.focus())
}
function addOptionAfter(i: number) {
  if (poll.value.options[i + 1] === '') insertOptions(i + 1, [''])
  else if (poll.value.options.length < MAX_OPTIONS) insertOptions(i, [poll.value.options[i], ''])
}
function pasteOptions(i: number, e: ClipboardEvent) {
  const lines = (e.clipboardData?.getData('text') ?? '').split('\n').map((l) => l.trim()).filter(Boolean)
  if (lines.length < 2) return
  e.preventDefault()
  insertOptions(i, lines)
}
function setDeadline(on: boolean) {
  poll.value.closesAt = on ? dayjs().add(3, 'day').hour(18).minute(0).second(0).format('YYYY-MM-DD HH:mm:ss') : ''
}
const newTag = ref('')
const tags = computed(() => [...state.tags, ...addedTags.value])
const posting = ref(false)

const geo = computed(() => (draft.value.places.length ? { ...draft.value } : null))
const reach = computed(() => reachOf({ geo: geo.value }))

function addTag() {
  if (!newTag.value.trim()) return
  const name = newTag.value.trim()
  const existing = tags.value.find((t) => t.name.toLowerCase() === name.toLowerCase())
  if (!existing) addedTags.value.push({ id: name, name, color: 'blue' })
  const id = existing?.id ?? name
  if (!picked.value.includes(id)) picked.value.push(id)
  newTag.value = ''
}

async function post() {
  if (!geo.value) return toast.error('Pick at least one place')
  if (!text.value.title.trim()) return toast.error(isPoll.value ? 'Write the poll question' : 'Give the thread a topic')
  if (isPoll.value && filledOptions.value.length < 2) return toast.error('Add at least two options')
  const sentTo = reach.value
  posting.value = true
  try {
    const id = await createThread({
      title: text.value.title.trim(),
      body: text.value.body || '<p></p>',
      geo: geo.value,
      tags: picked.value,
      policy: policy.value,
      ackRequired: ackRequired.value,
      poll: isPoll.value
        ? { options: filledOptions.value, multiple: poll.value.multiple, anonymous: poll.value.anonymous, closesAt: poll.value.closesAt || null }
        : null,
    })
    text.value = { title: '', body: '' }
    draft.value = { places: [], designations: [] }
    policy.value = 'everyone'
    ackRequired.value = false
    picked.value = []
    addedTags.value = []
    toast.success(`${isPoll.value ? 'Poll' : 'Thread'} sent to ${sentTo} people`)
    kind.value = 'discussion'
    poll.value = blankPoll()
    router.push(`/threads/${id}`)
  } catch (e) {
    toast.error(errorText(e, 'Could not start the thread'))
  } finally {
    posting.value = false
  }
}
</script>

<template>
  <div class="flex h-full flex-col">
    <PageHeader>
      <Breadcrumbs :items="[{ label: 'Feed', route: { path: '/' } }, { label: 'New thread' }]" />
      <div v-if="canStart(me)" class="ml-auto flex items-center gap-2">
        <Button label="Cancel" route="/" />
        <Button variant="solid" theme="gray" icon-left="lucide-send" :label="isPoll ? 'Start poll' : 'Start thread'" :loading="posting" @click="post" />
      </div>
    </PageHeader>

    <div v-if="!canStart(me)" class="flex flex-1 flex-col items-center justify-center gap-3 text-center">
      <div class="rounded-full bg-surface-gray-2 p-3 text-ink-gray-5">
        <span class="lucide-lock size-6" aria-hidden="true" />
      </div>
      <p class="text-base text-ink-gray-7">You can't start threads</p>
      <p class="max-w-sm text-p-sm text-ink-gray-5">
        An admin can turn on “Can start threads” for you on the Users page.
      </p>
      <Button label="Back to feed" route="/" class="mt-2" />
    </div>

    <div v-else class="flex min-h-0 flex-1 flex-col overflow-y-auto lg:flex-row lg:overflow-hidden">
      <div class="min-w-0 flex-1 lg:overflow-y-auto">
        <div class="mx-auto max-w-[770px] space-y-12 px-3 pt-10 pb-20 sm:px-6">
          <section class="space-y-5">
            <div class="flex items-center gap-3">
              <h2 class="text-xl text-ink-gray-9">What's it about?</h2>
              <TabButtons
                v-model="kind"
                size="md"
                class="ml-auto [&_[data-state=active]]:font-medium [&_[data-state=active]_*]:!text-ink-gray-9 [&_[data-state=inactive]_*]:!text-ink-gray-7"
                :options="KINDS"
              />
            </div>
            <FormControl v-model="text.title" :label="isPoll ? 'Question' : 'Topic'" required />
            <div>
              <div class="mb-1.5 text-xs text-ink-gray-6">Message</div>
              <div class="rounded-4 border border-outline-gray-2 bg-surface-base">
                <Editor v-model="text.body" :extensions="editorKit">
                  <div class="border-b border-outline-gray-1 px-1 py-1">
                    <EditorFixedMenu :items="minimalToolbar" />
                  </div>
                  <EditorContent class="rich min-h-[10rem] px-3 py-2 text-p-base text-ink-gray-8" />
                </Editor>
              </div>
            </div>
            <div v-if="isPoll">
              <div class="mb-1.5 flex items-baseline text-xs text-ink-gray-6">
                Options
                <span class="ml-auto text-ink-gray-5 tabular-nums">{{ poll.options.length }} of {{ MAX_OPTIONS }}</span>
              </div>
              <div class="divide-y divide-outline-gray-2 rounded-4 border border-outline-gray-2 bg-surface-base">
                <div v-for="(o, i) in poll.options" :key="i" class="group flex items-center gap-2 pr-1.5 pl-3 focus-within:bg-surface-gray-1">
                  <span class="size-4 shrink-0 text-ink-gray-5" :class="poll.multiple ? 'lucide-square' : 'lucide-circle'" aria-hidden="true" />
                  <TextInput
                    v-model="poll.options[i]"
                    variant="ghost"
                    class="flex-1 py-1"
                    :placeholder="`Option ${i + 1}`"
                    :aria-label="`Option ${i + 1}`"
                    @keydown.enter.prevent="addOptionAfter(i)"
                    @paste="pasteOptions(i, $event)"
                  />
                  <Button
                    v-if="poll.options.length > 2"
                    variant="ghost"
                    size="sm"
                    icon="lucide-x"
                    class="opacity-0 group-hover:opacity-100 focus-visible:opacity-100 group-focus-within:opacity-100"
                    :aria-label="`Remove option ${i + 1}`"
                    @click="poll.options.splice(i, 1)"
                  />
                </div>
                <button
                  v-if="poll.options.length < MAX_OPTIONS"
                  type="button"
                  class="flex w-full items-center gap-2 px-3 py-2.5 text-left text-sm text-ink-gray-6 hover:bg-surface-gray-1 hover:text-ink-gray-8"
                  @click="addOptionAfter(poll.options.length - 1)"
                >
                  <span class="lucide-plus size-4" aria-hidden="true" />Add option
                </button>
              </div>
              <p class="mt-1.5 text-xs text-ink-gray-5">Press Enter for the next option, or paste a list to fill them all.</p>
            </div>
            <div>
              <div class="mb-2 text-xs text-ink-gray-6">Tags</div>
              <div class="flex flex-wrap items-center gap-1.5">
                <button
                  v-for="t in tags"
                  :key="t.id"
                  type="button"
                  class="inline-flex h-7 items-center gap-1.5 rounded-full border px-2.5 text-sm transition-colors"
                  :class="
                    picked.includes(t.id)
                      ? [colorOf(t.color).soft, 'border-transparent text-ink-gray-9']
                      : 'border-outline-gray-2 text-ink-gray-6 hover:bg-surface-gray-1'
                  "
                  :aria-pressed="picked.includes(t.id)"
                  @click="picked = toggleIn(picked, t.id)"
                >
                  <span class="size-2 rounded-full" :class="colorOf(t.color).dot" aria-hidden="true" />
                  {{ t.name }}
                </button>
                <div class="w-36">
                  <TextInput v-model="newTag" size="sm" placeholder="New tag…" aria-label="New tag" @keydown.enter.prevent="addTag" />
                </div>
              </div>
            </div>
          </section>

          <section>
            <h2 class="text-xl text-ink-gray-9">Who is this for?</h2>
            <p class="mt-1.5 mb-6 text-p-sm text-ink-gray-5">
              Pick where, then optionally who. Everyone who matches sees the thread in their feed.
            </p>
            <GeoPicker v-model="draft" />
          </section>
        </div>
      </div>

      <aside class="shrink-0 border-t border-outline-gray-1 lg:w-[22rem] lg:overflow-y-auto lg:border-t-0 lg:border-l">
        <div class="space-y-8 p-6">
          <section>
            <h2 class="text-sm text-ink-gray-5">Reach</h2>
            <div class="mt-1.5 flex items-baseline gap-1.5">
              <span class="text-3xl font-semibold text-ink-gray-9 tabular-nums">{{ reach }}</span>
              <span class="text-sm text-ink-gray-5">unique people</span>
            </div>
            <AudienceChips v-if="geo" :geo="geo" class="mt-4" />
            <div v-else class="mt-3 flex items-center gap-2 rounded-4 bg-surface-gray-2 px-3 py-2.5">
              <span class="lucide-map-pin size-4 shrink-0 text-ink-gray-6" aria-hidden="true" />
              <p class="text-p-sm text-ink-gray-7">Pick a place below to see who this reaches.</p>
            </div>
            <p v-if="draft.places.length" class="mt-4 text-p-xs text-ink-gray-5">
              {{ draft.designations.length ? 'Only the ticked designations in these places.' : 'Everyone in these places, any designation.' }}
            </p>
          </section>
          <section v-if="isPoll" class="space-y-4">
            <h2 class="text-sm text-ink-gray-5">Poll settings</h2>
            <Switch v-model="poll.multiple" label="Allow more than one answer" description="People can tick every option that works for them." />
            <Switch v-model="poll.anonymous" label="Anonymous votes" description="Show counts only. Nobody, including you, sees who voted for what." />
            <Switch :model-value="!!poll.closesAt" label="Set a deadline" description="Voting closes on its own. You can also close it any time." @update:model-value="setDeadline" />
            <DateTimePicker v-if="poll.closesAt" v-model="poll.closesAt" label="Voting closes" />
          </section>
          <section class="space-y-4">
            <h2 class="text-sm text-ink-gray-5">Thread rules</h2>
            <FormControl v-model="policy" type="select" label="Who can reply" :options="POLICIES.map((p) => ({ label: p.label, value: p.value }))" />
            <Switch v-model="ackRequired" label="Ask for acknowledgment" description="Members confirm they have read it. You see who did." />
          </section>
        </div>
      </aside>
    </div>
  </div>
</template>
