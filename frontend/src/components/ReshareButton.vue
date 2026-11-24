<script setup lang="ts">
import { computed, ref } from 'vue'
import { Button, Tooltip, toast } from 'frappe-ui'
import { errorText, namesOf, placeById, state, toggleReshare } from '../lib/store'

const props = defineProps<{ thread: any }>()
const busy = ref(false)
const mine = computed(() => props.thread.reshares.includes(state.me.id))
const tip = computed(() => {
  if (mine.value) return 'Undo reshare'
  if (props.thread.canReshare) return `Reshare to ${placeById(state.me.place)?.name ?? 'your area'}`
  return `Reshared by ${namesOf(props.thread.reshares)}`
})

async function toggle() {
  busy.value = true
  try {
    await toggleReshare(props.thread)
    if (mine.value) toast.success('Reshared')
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
      :loading="busy"
      :aria-label="tip"
      @click="toggle"
    >
      <template v-if="thread.reshares.length">{{ thread.reshares.length }}</template>
    </Button>
  </Tooltip>
</template>
