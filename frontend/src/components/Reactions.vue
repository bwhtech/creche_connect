<script setup lang="ts">
import { computed, ref } from 'vue'
import { Button, Popover, Tooltip, toast } from 'frappe-ui'
import { state, useMe, toggleReaction, userById } from '../lib/store'

const props = defineProps<{ target: any; doctype: 'Samvaad Thread' | 'Samvaad Reply' }>()
const me = useMe()
const open = ref(false)

const entries = computed(() => Object.entries(props.target.reactions))
const names = (uids: string[]) => uids.map((id) => (id === me.value.id ? 'You' : userById(id)?.name)).join(', ')

function toggle(emoji: string) {
  toggleReaction(props.target, emoji, props.doctype).catch(() => toast.error('Could not save your reaction'))
}
function pick(emoji: string) {
  toggle(emoji)
  open.value = false
}
</script>

<template>
  <!-- Stop clicks here from following a surrounding thread link. -->
  <div class="flex flex-wrap items-center gap-1.5" @click.stop.prevent>
    <Tooltip v-for="[emoji, uids] in entries" :key="emoji" :text="names(uids)">
      <button
        type="button"
        class="inline-flex h-6 items-center gap-1 rounded-full border px-2 text-xs tabular-nums transition-colors"
        :class="
          uids.includes(me.id)
            ? 'border-outline-blue-2 bg-surface-blue-2 text-ink-blue-7'
            : 'border-outline-gray-1 bg-surface-gray-1 text-ink-gray-7 hover:bg-surface-gray-2'
        "
        :aria-pressed="uids.includes(me.id)"
        @click="toggle(emoji)"
      >
        <span class="text-sm leading-none">{{ emoji }}</span>
        <span>{{ uids.length }}</span>
      </button>
    </Tooltip>
    <Popover v-model:open="open">
      <template #trigger>
        <Button size="sm" variant="ghost" icon="lucide-smile-plus" aria-label="Add reaction" />
      </template>
      <template #default>
        <div class="flex gap-0.5 rounded-4 bg-surface-elevation-2 p-1 shadow-md">
          <button
            v-for="e in state.emojis"
            :key="e"
            type="button"
            class="flex size-8 items-center justify-center rounded-4 text-lg transition-transform hover:scale-110 hover:bg-surface-gray-2"
            :aria-label="`React with ${e}`"
            @click="pick(e)"
          >
            {{ e }}
          </button>
        </div>
      </template>
    </Popover>
  </div>
</template>
