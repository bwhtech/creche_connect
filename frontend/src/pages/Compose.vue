<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useStorage } from '@vueuse/core'
import { Breadcrumbs, Button, FormControl, PageHeader, Switch, TextInput, toast } from 'frappe-ui'
import { Editor, EditorContent, EditorFixedMenu, RichTextKit, minimalToolbar } from 'frappe-ui/editor'
import GeoPicker from '../components/GeoPicker.vue'
import AudienceChips from '../components/AudienceChips.vue'
import { state, useMe, canStart, createThread, reachOf, toggleIn, colorOf, errorText, POLICIES } from '../lib/store'

const me = useMe()
const router = useRouter()
const draft = reactive({ places: [] as string[], designations: [] as string[] })

const text = useStorage(`samvaad:compose-draft:${me.value.id}`, { title: '', body: '' })
const policy = ref('everyone')
const ackRequired = ref(false)
const picked = ref<string[]>([])
const newTag = ref('')
const addedTags = ref<any[]>([])
const tags = computed(() => [...state.tags, ...addedTags.value])
const posting = ref(false)

const geo = computed(() => (draft.places.length ? { ...draft } : null))
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
  if (!text.value.title.trim()) return toast.error('Give the thread a topic')
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
    })
    text.value = { title: '', body: '' }
    toast.success(`Thread sent to ${sentTo} people`)
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
        <Button variant="solid" theme="gray" icon-left="lucide-send" label="Start thread" :loading="posting" @click="post" />
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

    <div v-else class="flex min-h-0 flex-1">
      <div class="min-w-0 flex-1 overflow-y-auto">
        <div class="mx-auto max-w-[770px] space-y-12 px-3 pt-10 pb-20 sm:px-6">
          <section>
            <h2 class="text-xl text-ink-gray-9">Who is this for?</h2>
            <p class="mt-1.5 mb-6 text-p-sm text-ink-gray-5">
              Pick where, then optionally who. Everyone who matches sees the thread in their feed.
            </p>
            <GeoPicker v-model="draft" />
          </section>

          <section class="space-y-5">
            <h2 class="text-xl text-ink-gray-9">What's it about?</h2>
            <FormControl v-model="text.title" label="Topic" required />
            <div>
              <div class="mb-1.5 text-xs text-ink-gray-6">Message</div>
              <div class="rounded-4 border border-outline-gray-2 bg-surface-base">
                <Editor v-model="text.body" :extensions="[RichTextKit]">
                  <div class="border-b border-outline-gray-1 px-1 py-1">
                    <EditorFixedMenu :items="minimalToolbar" />
                  </div>
                  <EditorContent class="rich min-h-[10rem] px-3 py-2 text-p-base text-ink-gray-8" />
                </Editor>
              </div>
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

          <section class="space-y-5">
            <h2 class="text-xl text-ink-gray-9">Thread rules</h2>
            <FormControl v-model="policy" type="select" label="Who can reply" :options="POLICIES.map((p) => ({ label: p.label, value: p.value }))" />
            <Switch v-model="ackRequired" label="Ask for acknowledgment" description="Members get a prompt to confirm they have read it. You see who did." />
          </section>
        </div>
      </div>

      <aside class="hidden w-[20rem] shrink-0 overflow-y-auto border-l border-outline-gray-1 lg:block">
        <div class="p-6">
          <h2 class="text-sm text-ink-gray-5">Reach</h2>
          <div class="mt-1.5 flex items-baseline gap-1.5">
            <span class="text-3xl font-semibold text-ink-gray-9 tabular-nums">{{ reach }}</span>
            <span class="text-sm text-ink-gray-5">unique people</span>
          </div>
          <AudienceChips v-if="geo" :geo="geo" class="mt-4" />
          <div v-else class="mt-8 flex flex-col items-center gap-2 py-6 text-center">
            <span class="lucide-map-pin size-6 text-ink-gray-4" aria-hidden="true" />
            <p class="text-p-sm text-ink-gray-5">Pick a place to see who this reaches.</p>
          </div>
          <p v-if="draft.places.length" class="mt-4 text-p-xs text-ink-gray-5">
            {{ draft.designations.length ? 'Only the ticked designations in these places.' : 'Everyone in these places, any designation.' }}
          </p>
        </div>
      </aside>
    </div>
  </div>
</template>
