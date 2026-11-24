<script setup lang="ts">
import { computed, ref } from 'vue'
import { Avatar, Badge, Button, Tooltip, toast } from 'frappe-ui'
import { errorText, reachOf, remindPoll, userById, vote, when } from '../lib/store'

const props = defineProps<{ thread: any }>()
const poll = computed(() => props.thread.poll)
const reach = computed(() => reachOf(props.thread))
const showResults = computed(() => poll.value.closed || poll.value.voted || poll.value.canManage)
const top = computed(() => Math.max(0, ...poll.value.options.map((o) => o.count)))
const leaders = computed(() => (top.value ? poll.value.options.filter((o) => o.count === top.value) : []))
const names = (ids: string[]) => ids.map((id) => userById(id).name)
const pct = (o) => (poll.value.voterCount ? Math.round((o.count / poll.value.voterCount) * 100) : 0)
const icon = (o) =>
  o.mine
    ? [poll.value.multiple ? 'lucide-square-check' : 'lucide-circle-check', 'text-ink-violet-7']
    : [poll.value.multiple ? 'lucide-square' : 'lucide-circle', 'text-ink-gray-6']
const closes = computed(() => poll.value.closesAt && when(poll.value.closesAt))
const ends = computed(() => !poll.value.closed && closes.value && `Closes ${closes.value.fromNow()} (${closes.value.format('ddd D MMM, h:mm A')})`)
const result = computed(() => {
  if (!poll.value.closed || !top.value) return ''
  const votes = `${top.value} ${top.value === 1 ? 'vote' : 'votes'}`
  return leaders.value.length === 1 ? `${leaders.value[0].label} won with ${votes}` : `Tie at ${votes}: ${leaders.value.map((o) => o.label).join(', ')}`
})
const hint = computed(() => {
  if (poll.value.closed) return ''
  return poll.value.voted ? 'You voted · tap to change' : 'Tap to vote · results show after you vote'
})

function pick(o) {
  vote(props.thread, o.id).catch((e) => toast.error(errorText(e, 'Could not save your vote')))
}

const reminding = ref(false)
async function remind() {
  reminding.value = true
  try {
    const sent = await remindPoll(props.thread)
    toast.success(sent ? `Reminder emailed to ${sent} ${sent === 1 ? 'person' : 'people'}` : 'Everyone has voted')
  } catch (e) {
    toast.error(errorText(e, 'Could not send the reminder'))
  } finally {
    reminding.value = false
  }
}
</script>

<template>
  <div class="space-y-3 rounded-4 border border-outline-gray-1 bg-surface-elevation-1 p-2.5 md:p-3.5">
    <div class="space-y-1">
      <div class="flex flex-wrap items-center gap-2">
        <span class="text-p-sm text-ink-gray-7">{{ poll.multiple ? 'Pick one or more' : 'Pick one' }}</span>
        <Badge v-if="poll.anonymous" label="Anonymous" theme="violet" variant="subtle" size="sm" />
        <Badge v-if="poll.closed" label="Closed" variant="subtle" size="sm">
          <template #prefix><span class="lucide-lock size-3" aria-hidden="true" /></template>
        </Badge>
      </div>
      <p v-if="ends" class="text-p-xs text-ink-gray-6">{{ ends }}</p>
      <p v-if="result" class="flex items-center gap-1.5 text-p-sm text-ink-gray-8">
        <span class="lucide-trophy size-3.5 shrink-0 text-ink-green-6" aria-hidden="true" />{{ result }}
      </p>
    </div>
    <div class="space-y-2">
      <button
        v-for="o in poll.options"
        :key="o.id"
        type="button"
        :disabled="poll.closed"
        :aria-pressed="o.mine"
        :title="o.label"
        class="relative flex h-7 w-full items-center gap-2 overflow-hidden rounded-full px-2.5 text-left transition-colors [corner-shape:squircle]"
        :class="o.mine ? 'bg-surface-violet-1' : 'bg-surface-gray-2 enabled:hover:bg-surface-gray-3'"
        @click="pick(o)"
      >
        <span
          v-if="showResults"
          class="absolute inset-y-0 left-0 transition-[width] duration-300"
          :class="o.mine ? 'bg-surface-violet-4' : 'bg-surface-gray-4'"
          :style="{ width: `${pct(o)}%` }"
        />
        <span v-if="!poll.closed || o.mine" class="relative size-3.5 shrink-0" :class="icon(o)" aria-hidden="true" />
        <span class="relative min-w-0 flex-1 truncate text-sm" :class="o.mine ? 'font-medium text-ink-gray-9' : 'text-ink-gray-7'">
          {{ o.label }}
        </span>
        <template v-if="showResults">
          <span class="relative shrink-0 text-xs font-medium text-ink-gray-6 tabular-nums">
            {{ o.count }} {{ o.count === 1 ? 'vote' : 'votes' }}<span class="max-sm:hidden"> • {{ pct(o) }}%</span>
          </span>
          <Tooltip v-if="o.voters.length" :text="names(o.voters).join(', ')">
            <span class="relative -mr-1.5 flex shrink-0 items-center -space-x-1 max-sm:hidden">
              <Avatar v-for="id in o.voters.slice(0, 4)" :key="id" :label="userById(id).name" size="xs" class="ring-2 ring-[color:var(--surface-base)]" />
            </span>
          </Tooltip>
        </template>
      </button>
    </div>
    <div class="flex flex-wrap items-center gap-x-2 gap-y-1">
      <p class="px-1 text-sm text-ink-gray-6">
        {{ poll.voterCount }} of {{ reach }} voted<template v-if="hint"> · {{ hint }}</template>
      </p>
      <Button
        v-if="!poll.closed && poll.canManage"
        class="ml-auto"
        variant="ghost"
        icon-left="lucide-bell-ring"
        label="Remind those who haven't voted"
        :loading="reminding"
        @click="remind"
      />
    </div>
  </div>
</template>
