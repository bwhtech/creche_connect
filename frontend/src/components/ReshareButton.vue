<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { Button, Dialog, Dropdown, Switch, Textarea, Tooltip, toast } from 'frappe-ui'
import { errorText, namesOf, state, toggleReshare } from '../lib/store'
import GeoPicker from './GeoPicker.vue'

const props = defineProps<{ thread: any }>()
const MAX_NOTE = 500
const busy = ref(false)
const open = ref(false)
const note = ref('')
const toTeam = ref(false)
const geo = ref({ places: [], designations: [] })
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

watch(open, (isOpen) => {
  if (isOpen) return
  note.value = ''
  toTeam.value = false
  geo.value = { places: [], designations: [] }
})

async function toggle() {
  busy.value = true
  try {
    await toggleReshare(props.thread, note.value, toTeam.value ? geo.value : undefined)
    if (mine.value) toast.success('Reshared')
    open.value = false
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
    <div class="-mx-4 max-h-[70dvh] space-y-4 overflow-y-auto overscroll-contain px-4 sm:-mx-6 sm:px-6">
      <Textarea
        v-model="note"
        class="[&_textarea]:resize-none"
        :rows="4"
        :maxlength="MAX_NOTE"
        :placeholder="toTeam ? 'Add your thoughts (optional)…' : 'Add your thoughts…'"
        aria-label="Your thoughts"
        autofocus
      />
      <div>
        <Switch v-model="toTeam" label="Share with my team" description="Pick places and cadres in your area" />
        <GeoPicker v-if="toTeam" v-model="geo" class="mt-3" />
      </div>
      <div class="sticky bottom-0 flex justify-end gap-2 bg-surface-elevation-1 pt-2">
        <Button label="Cancel" @click="open = false" />
        <Button variant="solid" theme="gray" label="Reshare" :disabled="toTeam ? !geo.places.length : !note.trim()" :loading="busy" @click="toggle" />
      </div>
    </div>
  </Dialog>
</template>
