<script setup lang="ts">
import { computed, ref } from 'vue'
import { Button, Dialog, FormControl, Tooltip, toast } from 'frappe-ui'
import { errorText, namesOf, state, toggleReshare } from '../lib/store'

const props = defineProps<{ thread: any }>()
const busy = ref(false)
const open = ref(false)
const note = ref('')
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
    <p class="text-p-sm text-ink-gray-6">It moves back to the top of the feed. People in your area see that you reshared it.</p>
    <FormControl v-model="note" type="textarea" class="mt-4" label="Your thoughts" placeholder="Optional" :rows="3" :maxlength="500" />
    <div class="mt-4 flex justify-end gap-2">
      <Button label="Cancel" @click="open = false" />
      <Button variant="solid" theme="gray" label="Reshare" :loading="busy" @click="toggle" />
    </div>
  </Dialog>
</template>
