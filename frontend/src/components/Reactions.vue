<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { Avatar, BottomSheet, Button, Popover, Tooltip, toast } from 'frappe-ui'
import { state, useMe, toggleReaction, namesOf as names, isMobile, userById } from '../lib/store'

const props = defineProps<{ target: any; doctype: 'CrecheConnect Thread' | 'CrecheConnect Reply' }>()
const me = useMe()
const open = ref(false)

const entries = computed(() => Object.entries(props.target.reactions))
const total = computed(() => entries.value.reduce((n, [, uids]) => n + uids.length, 0))
const reactedByMe = computed(() => entries.value.some(([, uids]) => uids.includes(me.value.id)))
const tab = ref('all')
const tabs = computed(() => [['all', `All ${total.value}`], ...entries.value.map(([emoji, uids]) => [emoji, `${emoji} ${uids.length}`])])
const people = computed(() =>
  entries.value.flatMap(([emoji, uids]) => (tab.value === 'all' || tab.value === emoji ? uids.map((uid) => ({ uid, emoji })) : [])),
)
watch(open, () => (tab.value = 'all'))
const pillClass = (mine: boolean) => [
  'inline-flex h-6 items-center gap-1 rounded-full border px-2 text-xs tabular-nums transition-colors',
  mine ? 'border-outline-blue-2 bg-surface-blue-2 text-ink-blue-7' : 'border-outline-gray-1 bg-surface-gray-1 text-ink-gray-7 hover:bg-surface-gray-2',
]

function toggle(emoji: string) {
  toggleReaction(props.target, emoji, props.doctype).catch(() => toast.error('Could not save your reaction'))
}
function pick(emoji: string) {
  toggle(emoji)
  open.value = false
}
</script>

<template>
  <div class="flex flex-wrap items-center gap-1.5" @click.stop.prevent>
    <button
      v-if="isMobile && entries.length"
      type="button"
      :class="pillClass(reactedByMe)"
      :aria-label="`${total} reactions`"
      @click="open = true"
    >
      <span class="text-sm leading-none">{{ entries.slice(0, 3).map(([emoji]) => emoji).join('') }}</span>
      <span>{{ total }}</span>
    </button>
    <Tooltip v-for="[emoji, uids] in isMobile ? [] : entries" :key="emoji" :text="names(uids)">
      <button
        type="button"
        :class="pillClass(uids.includes(me.id))"
        :aria-pressed="uids.includes(me.id)"
        @click="toggle(emoji)"
      >
        <span class="text-sm leading-none">{{ emoji }}</span>
        <span>{{ uids.length }}</span>
      </button>
    </Tooltip>
    <Button v-if="isMobile && !entries.length" size="sm" variant="ghost" icon="lucide-smile-plus" aria-label="Add reaction" @click="open = true" />
    <Popover v-else-if="!isMobile" v-model:open="open">
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
    <BottomSheet v-if="isMobile" v-model:open="open" title="Reactions">
      <div class="grid grid-cols-6 gap-2 px-4 pb-6">
        <button
          v-for="e in state.emojis"
          :key="e"
          type="button"
          class="flex h-12 items-center justify-center rounded-4 text-2xl"
          :class="target.reactions[e]?.includes(me.id) ? 'bg-surface-blue-2' : 'bg-surface-gray-1'"
          :aria-label="`React with ${e}`"
          @click="toggle(e)"
        >
          {{ e }}
        </button>
      </div>
      <div v-if="entries.length" class="-mt-2 border-t border-outline-gray-1">
        <div class="flex overflow-x-auto border-b border-outline-gray-1 px-2">
          <button
            v-for="[id, label] in tabs"
            :key="id"
            type="button"
            class="shrink-0 border-b-2 px-4 py-3 text-base tabular-nums"
            :class="tab === id ? 'border-current font-medium text-ink-gray-9' : 'border-transparent text-ink-gray-6'"
            @click="tab = id"
          >
            {{ label }}
          </button>
        </div>
        <ul class="max-h-[50dvh] divide-y divide-outline-gray-1 overflow-y-auto overscroll-contain px-4 pb-8">
          <li v-for="p in people" :key="p.uid" class="flex items-center gap-3 py-3">
            <span class="relative shrink-0">
              <Avatar :label="userById(p.uid).name" size="2xl" />
              <span class="absolute -right-1 -bottom-1 flex size-5 items-center justify-center rounded-full bg-surface-white text-sm leading-none">{{ p.emoji }}</span>
            </span>
            <span class="min-w-0">
              <span class="block truncate text-base font-medium text-ink-gray-9">{{ p.uid === me.id ? 'You' : userById(p.uid).name }}</span>
              <span class="block truncate text-sm text-ink-gray-6">{{ userById(p.uid).designation }}</span>
            </span>
          </li>
        </ul>
      </div>
    </BottomSheet>
  </div>
</template>
