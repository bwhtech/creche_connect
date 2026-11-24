<script setup lang="ts">
import { computed, ref } from 'vue'
import { Avatar, Button, Dialog, Textarea, Tooltip, toast } from 'frappe-ui'
import { errorText, excerpt, namesOf, placeById, state, toggleReshare, userById, when } from '../lib/store'

const props = defineProps<{ thread: any }>()
const busy = ref(false)
const open = ref(false)
const note = ref('')
const MAX_NOTE = 500
const author = computed(() => userById(props.thread.authorId))
const area = computed(() => (state.me.place ? `people in ${placeById(state.me.place)?.name}` : 'everyone who can see it'))
const media = computed(() => /<video/.test(props.thread.body) ? 'lucide-video' : /<img/.test(props.thread.body) ? 'lucide-image' : /<audio/.test(props.thread.body) ? 'lucide-audio-lines' : '')
const mine = computed(() => props.thread.reshares.includes(state.me.id))
const tip = computed(() => {
  if (mine.value) return 'Undo reshare'
  if (props.thread.canReshare) return 'Reshare'
  return `Reshared by ${namesOf(props.thread.reshares)}`
})

async function toggle() {
  busy.value = true
  try {
    await toggleReshare(props.thread, note.value)
    if (mine.value) toast.success('Reshared')
    open.value = false
    note.value = ''
  } catch (e) {
    toast.error(errorText(e, 'Could not reshare'))
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <Tooltip v-if="thread.canReshare || thread.reshares.length" :text="tip">
    <Button
      variant="ghost"
      size="sm"
      :icon="thread.reshares.length ? undefined : 'lucide-repeat-2'"
      :icon-left="thread.reshares.length ? 'lucide-repeat-2' : undefined"
      :class="mine && '!text-ink-green-6'"
      :disabled="!thread.canReshare && !mine"
      :loading="busy && !open"
      :aria-label="tip"
      @click="mine ? toggle() : (open = true)"
    >
      <template v-if="thread.reshares.length">{{ thread.reshares.length }}</template>
    </Button>
  </Tooltip>
  <Dialog v-model:open="open" title="Reshare">
    <div class="flex items-center gap-2.5">
      <Avatar :label="state.me.name" size="md" />
      <span class="text-base font-medium text-ink-gray-9">{{ state.me.name }}</span>
    </div>
    <Textarea
      v-model="note"
      variant="ghost"
      class="-mx-2 mt-2 [&_textarea]:resize-none [&_textarea]:text-base"
      :rows="3"
      :maxlength="MAX_NOTE"
      placeholder="Add your thoughts (optional)"
      aria-label="Your thoughts"
      autofocus
    />
    <div class="mt-2 rounded-4 border border-outline-gray-2 bg-surface-gray-1 p-3">
      <div class="flex items-center gap-2 text-xs text-ink-gray-5">
        <Avatar :label="author.name" size="xs" />
        <span class="text-ink-gray-7">{{ author.name }}</span>· {{ when(thread.createdAt).fromNow() }}
      </div>
      <div class="mt-1.5 flex items-center gap-1.5 text-base font-medium text-ink-gray-9">
        <span v-if="media" :class="media" class="size-4 shrink-0 text-ink-gray-5" aria-hidden="true" />
        <span class="truncate">{{ thread.title }}</span>
      </div>
      <p class="mt-1 line-clamp-2 text-p-sm text-ink-gray-6">{{ excerpt(thread.body) }}</p>
    </div>
    <div class="mt-4 flex items-center gap-2">
      <p class="mr-auto text-xs text-ink-gray-5">
        Moves to the top for {{ area }}<span v-if="note.length > MAX_NOTE - 100"> · {{ MAX_NOTE - note.length }} left</span>
      </p>
      <Button label="Cancel" @click="open = false" />
      <Button variant="solid" theme="gray" label="Reshare" icon-left="lucide-repeat-2" :loading="busy" @click="toggle" />
    </div>
  </Dialog>
</template>
