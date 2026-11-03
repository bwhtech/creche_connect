<script setup lang="ts">
import { computed, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { Button, LoadingIndicator, PageHeader, TabButtons, Tooltip, toast, useCall } from 'frappe-ui'
import { AreaChart, BarChart } from 'frappe-ui/charts'
import { useMe, tagById, colorOf, errorText, placeById } from '../lib/store'

const me = useMe()
const RANGES = [
  { label: '7 days', value: '7d' },
  { label: '30 days', value: '30d' },
  { label: '90 days', value: '90d' },
]
const range = ref('30d')
const insights = useCall<any>({
  url: '/api/v2/method/crecheconnect.insights.get_insights',
  params: () => ({ period: range.value }),
  immediate: me.value.admin,
  refetch: true,
  onError: (e) => toast.error(errorText(e, 'Could not load insights')),
})
const data = computed(() => insights.data)

const TILES = [
  ['JK', 'Jammu & Kashmir', 3, 0],
  ['PB', 'Punjab', 2, 1], ['HP', 'Himachal Pradesh', 3, 1], ['UK', 'Uttarakhand', 4, 1],
  ['RJ', 'Rajasthan', 1, 2], ['HR', 'Haryana', 2, 2], ['UP', 'Uttar Pradesh', 3, 2], ['BR', 'Bihar', 4, 2], ['SK', 'Sikkim', 5, 2], ['AS', 'Assam', 6, 2], ['AR', 'Arunachal Pradesh', 7, 2],
  ['GJ', 'Gujarat', 0, 3], ['MP', 'Madhya Pradesh', 1, 3], ['CG', 'Chhattisgarh', 2, 3], ['JH', 'Jharkhand', 3, 3], ['WB', 'West Bengal', 4, 3], ['ML', 'Meghalaya', 5, 3], ['NL', 'Nagaland', 6, 3],
  ['MH', 'Maharashtra', 1, 4], ['TS', 'Telangana', 2, 4], ['OD', 'Odisha', 3, 4], ['TR', 'Tripura', 5, 4], ['MN', 'Manipur', 6, 4],
  ['GA', 'Goa', 0, 5], ['KA', 'Karnataka', 1, 5], ['AP', 'Andhra Pradesh', 2, 5], ['MZ', 'Mizoram', 5, 5],
  ['KL', 'Kerala', 1, 6], ['TN', 'Tamil Nadu', 2, 6],
]
const stateName = (code: string) => placeById(code)?.name ?? code

const nf = new Intl.NumberFormat('en-IN')
const pct = (n: number) => `${Math.round(n * 100)}%`

const stateByCode = computed(() => data.value?.states ?? {})
const states = computed(() =>
  Object.entries(stateByCode.value)
    .map(([code, s]: [string, any]) => ({ code, ...s }))
    .sort((a, b) => b.reach - a.reach),
)

const kpis = computed(() => {
  const k = data.value.kpis
  const p = data.value.previous
  const delta = (key: string) => (p[key] ? (k[key] - p[key]) / p[key] : null)
  return [
    { label: 'Threads started', value: nf.format(k.threads), delta: delta('threads') },
    { label: 'People reached', value: nf.format(k.reached), delta: delta('reached') },
    { label: 'Seen rate', value: pct(k.seenRate), delta: delta('seenRate') },
    { label: 'Acknowledged', value: pct(k.ackRate), delta: delta('ackRate') },
    { label: 'Reactions', value: nf.format(k.reactions), delta: delta('reactions') },
  ]
})

const METRICS = [
  { label: 'Seen rate', value: 'seenRate', fmt: pct },
  { label: 'People reached', value: 'reach', fmt: nf.format },
  { label: 'Reactions', value: 'reactions', fmt: nf.format },
]
const metric = ref('seenRate')
const metricDef = computed(() => METRICS.find((m) => m.value === metric.value))
// One hue, light to dark. Literal classes so Tailwind keeps them.
const STEPS = ['bg-surface-blue-2', 'bg-surface-blue-3', 'bg-surface-blue-4', 'bg-surface-blue-5', 'bg-surface-blue-6']
const extent = computed(() => {
  const vals = states.value.map((s) => s[metric.value])
  return vals.length ? [Math.min(...vals), Math.max(...vals)] : [0, 0]
})
const stepFor = (v: number) => {
  const [lo, hi] = extent.value
  const i = hi === lo ? 4 : Math.min(4, Math.floor(((v - lo) / (hi - lo)) * 5))
  return STEPS[i]
}
const legendStops = computed(() => extent.value.map((v) => metricDef.value.fmt(v)))

const picked = ref('')
const selected = computed(() => (stateByCode.value[picked.value] ? picked.value : states.value[0]?.code))
const sel = computed(() => stateByCode.value[selected.value])
const districts = computed(() => data.value?.districts[selected.value] ?? [])
const maxDistrict = computed(() => Math.max(1, ...districts.value.map((d) => d.reach)))

const topics = computed(() => data.value.topics.map((t) => ({ topic: t.tag, Reactions: t.reactions })))
const stateBars = computed(() =>
  states.value.map((s) => ({ state: stateName(s.code), Reached: s.reach, Seen: Math.round(s.reach * s.seenRate) })),
)
const maxDesignation = computed(() => Math.max(1, ...data.value.designations.map((d) => d.people)))
</script>

<template>
  <div class="flex h-full flex-col">
    <PageHeader>
      <h1 class="text-2xl text-ink-gray-9">Insights</h1>
      <div v-if="me.admin" class="ml-auto">
        <TabButtons v-model="range" :options="RANGES" />
      </div>
    </PageHeader>

    <div v-if="!me.admin" class="flex flex-1 flex-col items-center justify-center gap-3 text-center">
      <div class="rounded-full bg-surface-gray-2 p-3 text-ink-gray-5">
        <span class="lucide-lock size-6" aria-hidden="true" />
      </div>
      <p class="text-base text-ink-gray-7">Insights are for admins</p>
      <Button label="Back to feed" route="/" class="mt-2" />
    </div>

    <div v-else-if="!data" class="flex flex-1 items-center justify-center">
      <LoadingIndicator class="size-5 text-ink-gray-5" />
    </div>

    <div v-else class="min-h-0 flex-1 overflow-y-auto">
      <div class="mx-auto max-w-6xl space-y-6 px-3 pt-6 pb-20 sm:px-6">
        <div class="grid grid-cols-2 divide-outline-gray-1 rounded-5 border border-outline-gray-1 sm:grid-cols-5 sm:divide-x">
          <div v-for="k in kpis" :key="k.label" class="px-5 py-4">
            <div class="text-sm text-ink-gray-5">{{ k.label }}</div>
            <div class="mt-1.5 text-3xl font-semibold text-ink-gray-9 tabular-nums">{{ k.value }}</div>
            <div v-if="k.delta !== null" class="mt-1 flex items-center gap-1 text-xs tabular-nums" :class="k.delta >= 0 ? 'text-ink-green-5' : 'text-ink-red-5'">
              <span :class="k.delta >= 0 ? 'lucide-trending-up' : 'lucide-trending-down'" class="size-3.5" aria-hidden="true" />
              {{ k.delta >= 0 ? '+' : '' }}{{ Math.round(k.delta * 100) }}%
              <span class="text-ink-gray-5">vs previous</span>
            </div>
            <div v-else class="mt-1 text-xs text-ink-gray-4">No earlier data</div>
          </div>
        </div>

        <div class="grid gap-6 lg:grid-cols-[minmax(0,1.25fr)_minmax(0,1fr)]">
          <section class="rounded-5 border border-outline-gray-1 p-5">
            <div class="flex items-start gap-3">
              <div>
                <h2 class="text-lg-semibold text-ink-gray-9">Reach across India</h2>
                <p class="mt-0.5 text-sm text-ink-gray-5">One tile per state. Pick a state to see its districts.</p>
              </div>
              <TabButtons v-model="metric" class="ml-auto shrink-0" :options="METRICS" />
            </div>

            <div class="mt-6 grid grid-cols-8 gap-1.5" role="group" aria-label="Map of programme states">
              <template v-for="[code, name, col, row] in TILES" :key="code">
                <Tooltip
                  v-if="stateByCode[code]"
                  :text="`${name}: ${metricDef.fmt(stateByCode[code][metric])}`"
                >
                  <button
                    type="button"
                    class="flex aspect-square flex-col items-center justify-center rounded-4 text-ink-gray-9 transition-transform hover:scale-105"
                    :class="[stepFor(stateByCode[code][metric]), selected === code && 'ring-2 ring-outline-gray-9 ring-offset-2 ring-offset-surface-base']"
                    :style="{ gridColumnStart: col + 1, gridRowStart: row + 1 }"
                    :aria-pressed="selected === code"
                    :aria-label="`${name}, ${metricDef.fmt(stateByCode[code][metric])}`"
                    @click="picked = code"
                  >
                    <span class="text-sm-semibold">{{ code }}</span>
                    <span class="text-2xs tabular-nums">{{ metricDef.fmt(stateByCode[code][metric]) }}</span>
                  </button>
                </Tooltip>
                <div
                  v-else
                  class="flex aspect-square items-center justify-center rounded-4 bg-surface-gray-1 text-2xs text-ink-gray-4"
                  :style="{ gridColumnStart: col + 1, gridRowStart: row + 1 }"
                  :title="`${name}: not in the programme`"
                >
                  {{ code }}
                </div>
              </template>
            </div>

            <div class="mt-5 flex items-center gap-2 text-xs text-ink-gray-5">
              <span class="tabular-nums">{{ legendStops[0] }}</span>
              <div class="flex overflow-hidden rounded-full">
                <span v-for="s in STEPS" :key="s" class="h-2 w-8" :class="s" />
              </div>
              <span class="tabular-nums">{{ legendStops[1] }}</span>
              <span class="ml-4 flex items-center gap-1.5"><span class="size-3 rounded-1 bg-surface-gray-1" />Not in the programme</span>
            </div>
          </section>

          <section v-if="sel" class="rounded-5 border border-outline-gray-1 p-5">
            <h2 class="text-lg-semibold text-ink-gray-9">{{ stateName(selected) }}</h2>
            <div class="mt-4 grid grid-cols-3 divide-x divide-outline-gray-1">
              <div class="pr-4">
                <div class="text-xs text-ink-gray-5">Reached</div>
                <div class="mt-1 text-xl text-ink-gray-9 tabular-nums">{{ nf.format(sel.reach) }}</div>
              </div>
              <div class="px-4">
                <div class="text-xs text-ink-gray-5">Seen</div>
                <div class="mt-1 text-xl text-ink-gray-9 tabular-nums">{{ pct(sel.seenRate) }}</div>
              </div>
              <div class="pl-4">
                <div class="text-xs text-ink-gray-5">Acknowledged</div>
                <div class="mt-1 text-xl text-ink-gray-9 tabular-nums">{{ pct(sel.ackRate) }}</div>
              </div>
            </div>

            <div class="mt-6 text-sm text-ink-gray-5">People reached by district</div>
            <div class="mt-3 space-y-3">
              <div v-for="d in districts" :key="d.id" class="grid grid-cols-[6rem_minmax(0,1fr)_7.5rem] items-center gap-3">
                <span class="truncate text-sm text-ink-gray-8">{{ placeById(d.id)?.name ?? d.id }}</span>
                <div class="h-2 rounded-full bg-surface-gray-2">
                  <div class="h-2 rounded-full bg-surface-blue-5" :style="{ width: `${(d.reach / maxDistrict) * 100}%` }" />
                </div>
                <span class="text-right text-xs text-ink-gray-6 tabular-nums">{{ nf.format(d.reach) }} · {{ pct(d.seenRate) }} seen</span>
              </div>
            </div>
          </section>
        </div>

        <section class="rounded-5 border border-outline-gray-1 p-5">
          <h2 class="text-lg-semibold text-ink-gray-9">New readers</h2>
          <p class="mt-0.5 text-sm text-ink-gray-5">{{ data.step === 'week' ? 'Per week' : 'Per day' }}, people opening a thread for the first time</p>
          <div class="mt-4 h-64">
            <AreaChart :data="data.engagement" x="date" y="people" />
          </div>
        </section>

        <div class="grid gap-6 lg:grid-cols-2">
          <section class="rounded-5 border border-outline-gray-1 p-5">
            <h2 class="text-lg-semibold text-ink-gray-9">Reactions by topic</h2>
            <p class="mt-0.5 text-sm text-ink-gray-5">Which tags people respond to most</p>
            <div class="mt-4 h-64">
              <BarChart :data="topics" x="topic" y="Reactions" />
            </div>
          </section>

          <section class="rounded-5 border border-outline-gray-1 p-5">
            <h2 class="text-lg-semibold text-ink-gray-9">Reach by designation</h2>
            <p class="mt-0.5 text-sm text-ink-gray-5">Unique people who received at least one thread</p>
            <div class="mt-5 space-y-4">
              <div v-for="d in data.designations" :key="d.name" class="grid grid-cols-[9.5rem_minmax(0,1fr)_4rem] items-center gap-3">
                <span class="truncate text-sm text-ink-gray-8">{{ d.name }}</span>
                <div class="h-2 rounded-full bg-surface-gray-2">
                  <div class="h-2 rounded-full bg-surface-blue-5" :style="{ width: `${(d.people / maxDesignation) * 100}%` }" />
                </div>
                <span class="text-right text-xs text-ink-gray-6 tabular-nums">{{ nf.format(d.people) }}</span>
              </div>
            </div>
          </section>
        </div>

        <section class="rounded-5 border border-outline-gray-1 p-5">
          <h2 class="text-lg-semibold text-ink-gray-9">Reached and seen, by state</h2>
          <p class="mt-0.5 text-sm text-ink-gray-5">The gap is people who got a thread but never opened it</p>
          <div class="mt-4 h-72">
            <BarChart :data="stateBars" x="state" :y="['Reached', 'Seen']" />
          </div>
        </section>

        <section class="rounded-5 border border-outline-gray-1">
          <div class="px-5 pt-5 pb-3">
            <h2 class="text-lg-semibold text-ink-gray-9">Most reacted threads</h2>
          </div>
          <p v-if="!data.topThreads.length" class="px-5 pb-5 text-sm text-ink-gray-5">No reactions in this period yet.</p>
          <div class="divide-y divide-outline-gray-1">
            <RouterLink
              v-for="(t, i) in data.topThreads"
              :key="t.id"
              :to="`/threads/${t.id}`"
              class="grid grid-cols-[1.5rem_minmax(0,1fr)_7rem_6rem] items-center gap-4 px-5 py-3 hover:bg-surface-gray-1"
            >
              <span class="text-sm text-ink-gray-4 tabular-nums">{{ i + 1 }}</span>
              <div class="min-w-0">
                <div class="truncate text-base text-ink-gray-8">{{ t.title }}</div>
                <div class="mt-0.5 flex gap-1.5">
                  <span
                    v-for="tg in t.tags.map(tagById).filter(Boolean)"
                    :key="tg.id"
                    class="inline-flex items-center gap-1 text-xs text-ink-gray-5"
                  >
                    <span class="size-1.5 rounded-full" :class="colorOf(tg.color).dot" aria-hidden="true" />{{ tg.name }}
                  </span>
                </div>
              </div>
              <span class="text-right text-sm text-ink-gray-7 tabular-nums">{{ nf.format(t.reactions) }} reactions</span>
              <span class="text-right text-sm text-ink-gray-7 tabular-nums">{{ pct(t.seenRate) }} seen</span>
            </RouterLink>
          </div>
        </section>
      </div>
    </div>
  </div>
</template>
