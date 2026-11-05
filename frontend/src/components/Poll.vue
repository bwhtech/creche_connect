<script setup lang="ts">
import { computed, ref } from 'vue'
import { Avatar, Button, Tooltip, toast } from 'frappe-ui'
import { errorText, reachOf, remindPoll, userById, vote, when } from '../lib/store'

const props = defineProps<{ thread: any }>()
const poll = computed(() => props.thread.poll)
const reach = computed(() => reachOf(props.thread))
const showResults = computed(() => poll.value.closed || poll.value.voted || poll.value.canManage)
const top = computed(() => Math.max(0, ...poll.value.options.map((o) => o.count)))
const leaders = computed(() => (top.value ? poll.value.options.filter((o) => o.count === top.value) : []))
const isLeader = (o) => showResults.value && leaders.value.includes(o)
const names = (ids: string[]) => ids.map((id) => userById(id).name)
const icon = (o) =>
  o.mine
    ? [poll.value.multiple ? 'lucide-square-check' : 'lucide-circle-check', 'text-ink-blue-6']
    : [poll.value.multiple ? 'lucide-square' : 'lucide-circle', 'text-ink-gray-5']
const closes = computed(() => poll.value.closesAt && when(poll.value.closesAt))
const meta = computed(() =>
  [
    poll.value.multiple ? 'Pick one or more' : 'Pick one',
    poll.value.anonymous && 'Anonymous',
    poll.value.closed ? 'Closed' : closes.value && `Closes ${closes.value.fromNow()} (${closes.value.format('ddd D MMM, h:mm A')})`,
  ]
    .filter(Boolean)
    .join(' · '),
)
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
  <div class="space-y-2">
    <div class="flex items-center gap-2 text-sm text-ink-gray-6">
      <span class="lucide-chart-bar-big size-4 shrink-0" aria-hidden="true" />{{ meta }}
    </div>
    <div v-if="result" class="flex items-center gap-2 rounded-4 bg-surface-green-2 px-3 py-2.5 text-p-sm text-ink-gray-8">
      <span class="lucide-trophy size-4 shrink-0 text-ink-green-6" aria-hidden="true" />{{ result }}
    </div>
    <button
      v-for="o in poll.options"
      :key="o.id"
      type="button"
      :disabled="poll.closed"
      :aria-pressed="o.mine"
      class="relative flex w-full items-center gap-3 overflow-hidden rounded-4 border px-3 py-3 text-left transition-colors enabled:hover:border-outline-gray-5"
      :class="o.mine ? 'border-outline-blue-4' : 'border-outline-gray-3'"
      @click="pick(o)"
    >
      <span
        v-if="showResults && top"
        class="absolute inset-y-0 left-0 transition-all duration-300"
        :class="o.mine ? 'bg-surface-blue-3' : 'bg-surface-gray-3'"
        :style="{ width: `${(o.count / top) * 100}%` }"
      />
      <span class="relative size-4 shrink-0" :class="icon(o)" aria-hidden="true" />
      <span class="relative flex min-w-0 flex-1 flex-col gap-1.5 sm:flex-row sm:items-center sm:gap-3">
        <span class="flex-1 text-base" :class="isLeader(o) ? 'font-semibold text-ink-gray-9' : 'text-ink-gray-8'">
          {{ o.label }}
        </span>
        <Tooltip v-if="showResults && o.voters.length" :text="names(o.voters).join(', ')">
          <span class="flex shrink-0 items-center -space-x-1">
            <Avatar v-for="n in names(o.voters.slice(0, 3))" :key="n" :label="n" size="sm" class="ring-2 ring-surface-base" />
            <span v-if="o.voters.length > 3" class="pl-2 text-xs text-ink-gray-5 tabular-nums">+{{ o.voters.length - 3 }}</span>
          </span>
        </Tooltip>
      </span>
      <span v-if="showResults" class="relative w-16 shrink-0 text-right text-sm font-medium text-ink-gray-9 tabular-nums">
        {{ o.count }} {{ o.count === 1 ? 'vote' : 'votes' }}
      </span>
    </button>
    <div class="flex flex-wrap items-center gap-x-2 gap-y-1">
      <p class="text-sm text-ink-gray-6">
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
