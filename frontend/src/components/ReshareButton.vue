<script setup lang="ts">
import { computed, ref } from 'vue'
import { Button, Dialog, Dropdown, Textarea, Tooltip, toast } from 'frappe-ui'
import { errorText, namesOf, state, toggleReshare } from '../lib/store'

const props = defineProps<{ thread: any }>()
const MAX_NOTE = 500
const busy = ref(false)
const open = ref(false)
const note = ref('')
const count = computed(() => props.thread.reshares.length)
const mine = computed(() => props.thread.reshares.includes(state.me.id))
const menu = computed(() =>
  mine.value
    ? [{ label: 'Undo reshare', icon: 'lucide-undo-2', onClick: () => toggle() }]
    : [
        { label: 'Reshare', icon: 'lucide-repeat-2', onClick: () => toggle() },
        { label: 'Reshare with your thoughts', icon: 'lucide-pencil-line', onClick: () => (open.value = true) },
      ],
)

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
  <Dropdown v-if="thread.canReshare || mine" :options="menu">
    <Button
      variant="ghost"
      size="sm"
      :icon="count ? undefined : 'lucide-repeat-2'"
      :icon-left="count ? 'lucide-repeat-2' : undefined"
      :class="mine && '!text-ink-green-6'"
      :loading="busy && !open"
      :aria-label="mine ? 'Reshared' : 'Reshare'"
    >
      <template v-if="count">{{ count }}</template>
    </Button>
  </Dropdown>
  <Tooltip v-else-if="count" :text="`Reshared by ${namesOf(thread.reshares)}`">
    <Button variant="ghost" size="sm" icon-left="lucide-repeat-2" disabled :aria-label="`Reshared by ${namesOf(thread.reshares)}`">{{ count }}</Button>
  </Tooltip>
  <Dialog v-if="open" v-model:open="open" title="Reshare with your thoughts">
    <Textarea
      v-model="note"
      class="[&_textarea]:resize-none"
      :rows="4"
      :maxlength="MAX_NOTE"
      placeholder="Why should people see this?"
      aria-label="Your thoughts"
      autofocus
    />
    <div class="mt-4 flex justify-end gap-2">
      <Button label="Cancel" @click="open = false" />
      <Button variant="solid" theme="gray" label="Reshare" :disabled="!note.trim()" :loading="busy" @click="toggle" />
    </div>
  </Dialog>
</template>
