<script setup lang="ts">
import { computed, ref } from 'vue'
import { Button, Checkbox, TextInput } from 'frappe-ui'
import { state, useMe, allowedPlaces, inPlace, rootPlace, peopleByPlace, DESIGNATIONS, NATIONAL_DESIGNATIONS, toggleIn, colorOf, placeById } from '../lib/store'

const draft = defineModel<{ places: string[]; designations: string[] }>({ required: true })

const me = useMe()
const query = ref('')
const root = computed(() => (me.value.place ? placeById(me.value.place) : rootPlace.value))
const isCountry = computed(() => root.value.kind === 'Country')
const allPlaces = computed(() => draft.value.places.length === 1 && draft.value.places[0] === root.value.id)
const toggleAllPlaces = () => (draft.value.places = allPlaces.value ? [] : [root.value.id])

const scope = computed(() => allowedPlaces(me.value).filter((p) => p.id !== root.value.id))
const scopeIds = computed(() => new Set(scope.value.map((p) => p.id)))
const expanded = ref<string[]>([])
const toggleExpand = (id: string) => (expanded.value = toggleIn(expanded.value, id))
const shown = (p) => !scopeIds.value.has(p.parentId) || (expanded.value.includes(p.parentId) && shown(placeById(p.parentId)))
const results = computed(() => {
  const q = query.value.trim().toLowerCase()
  return (q ? scope.value.filter((p) => p.name.toLowerCase().includes(q)) : scope.value.filter(shown)).slice(0, 80)
})
const childCounts = computed(() => {
  const counts = {}
  for (const p of scope.value) counts[p.parentId] = (counts[p.parentId] ?? 0) + 1
  return counts
})
const childLabel = (p) => `${childCounts.value[p.id]} ${p.kind === 'State' ? 'districts' : 'blocks'}`
const indent = (kind: string) => (query.value ? 'pl-4' : ({ Country: 'pl-4', State: 'pl-4', District: 'pl-10', Block: 'pl-16' })[kind])
const iconFor = (kind: string) => ({ Country: 'lucide-globe', State: 'lucide-map' })[kind] ?? 'lucide-map-pin'
const togglePlace = (id: string) => (draft.value.places = toggleIn(draft.value.places, id))

const inSelected = computed(() => state.users.filter((u) => draft.value.places.some((p) => inPlace(u.place, p))))
const designations = computed(() =>
  draft.value.places.includes(rootPlace.value?.id)
    ? DESIGNATIONS.value
    : DESIGNATIONS.value.filter((d) => !NATIONAL_DESIGNATIONS.value.includes(d)),
)
const designationCounts = computed(() => {
  const counts = {}
  for (const u of inSelected.value) counts[u.designation] = (counts[u.designation] ?? 0) + 1
  return counts
})
const allDesignations = computed(() => designations.value.every((d) => draft.value.designations.includes(d)))
const toggleAllDesignations = () => (draft.value.designations = allDesignations.value ? [] : [...designations.value])
</script>

<template>
  <div class="space-y-8">
    <div>
      <div class="flex items-baseline gap-2">
        <span class="text-base-semibold text-ink-gray-8">1. Where</span>
        <span class="text-sm text-ink-gray-5">State, district or block</span>
      </div>

      <div v-if="draft.places.length" class="mt-3 flex flex-wrap gap-1.5">
        <Button
          v-for="id in draft.places"
          :key="id"
          size="sm"
          variant="subtle"
          icon-left="lucide-map-pin"
          icon-right="lucide-x"
          :label="`${placeById(id).name} · ${placeById(id).kind}`"
          @click="togglePlace(id)"
        />
      </div>

      <div class="mt-3 rounded-5 border border-outline-gray-1">
        <div class="border-b border-outline-gray-1 p-2">
          <TextInput v-model="query" placeholder="Search a state, district or block, e.g. Jashpur" aria-label="Search places">
            <template #prefix><span class="lucide-search size-4 text-ink-gray-5" aria-hidden="true" /></template>
          </TextInput>
        </div>
        <label v-if="!query" class="flex cursor-pointer items-center gap-3 border-b border-outline-gray-1 bg-surface-gray-1 py-3 pr-4 pl-4 hover:bg-surface-gray-2">
          <Checkbox :model-value="allPlaces" @update:model-value="toggleAllPlaces" />
          <span class="inline-flex size-6 shrink-0 items-center justify-center rounded-4" :class="[colorOf(root.color).soft, colorOf(root.color).ink]">
            <span class="lucide-globe size-3.5" aria-hidden="true" />
          </span>
          <div class="min-w-0">
            <div class="truncate text-sm-semibold text-ink-gray-9">{{ isCountry ? root.name : `All of ${root.name}` }}</div>
            <div class="truncate text-xs text-ink-gray-5">Every {{ isCountry ? 'state, district and block' : 'place below it' }}</div>
          </div>
          <span class="ml-auto text-xs text-ink-gray-5 tabular-nums">{{ peopleByPlace[root.id] ?? 0 }} people</span>
        </label>
        <div class="max-h-72 divide-y divide-outline-gray-1 overflow-y-auto" :class="allPlaces && 'pointer-events-none opacity-50'">
          <div v-for="p in results" :key="p.id" class="flex items-center gap-3 py-2 pr-4 hover:bg-surface-gray-1" :class="indent(p.kind)">
            <Checkbox :model-value="allPlaces || draft.places.includes(p.id)" :disabled="allPlaces" :aria-label="`Send to ${p.name}`" @update:model-value="togglePlace(p.id)" />
            <button
              type="button"
              class="flex min-w-0 flex-1 items-center gap-3 py-0.5 text-left"
              :aria-expanded="childCounts[p.id] && !query ? expanded.includes(p.id) : undefined"
              @click="childCounts[p.id] && !query ? toggleExpand(p.id) : togglePlace(p.id)"
            >
              <span class="inline-flex size-6 shrink-0 items-center justify-center rounded-4" :class="[colorOf(p.color).soft, colorOf(p.color).ink]">
                <span :class="iconFor(p.kind)" class="size-3.5" aria-hidden="true" />
              </span>
              <span class="min-w-0">
                <span class="block truncate text-sm text-ink-gray-8">{{ p.name }}</span>
                <span class="block truncate text-xs text-ink-gray-5">{{ p.kind }}{{ p.parent ? ` · ${p.parent}` : '' }}</span>
              </span>
              <span class="ml-auto shrink-0 text-xs text-ink-gray-5 tabular-nums">{{ peopleByPlace[p.id] ?? 0 }} people</span>
              <span class="flex w-28 shrink-0 items-center justify-end gap-1 text-xs text-ink-gray-6">
                <template v-if="childCounts[p.id] && !query">
                  {{ childLabel(p) }}
                  <span class="size-4" :class="expanded.includes(p.id) ? 'lucide-chevron-up' : 'lucide-chevron-down'" aria-hidden="true" />
                </template>
              </span>
            </button>
          </div>
          <p v-if="!results.length" class="px-4 py-6 text-center text-sm text-ink-gray-5">No place matches “{{ query }}”</p>
        </div>
      </div>
    </div>

    <div>
      <div class="flex items-baseline gap-2">
        <span class="text-base-semibold text-ink-gray-8">2. Designations</span>
        <span class="text-sm text-ink-gray-5">Optional. Leave empty to reach everyone there.</span>
      </div>
      <div class="mt-3 grid gap-x-6 gap-y-1 rounded-5 border border-outline-gray-1 p-3 sm:grid-cols-2" :class="!draft.places.length && 'opacity-50'">
        <label class="mb-1 flex cursor-pointer items-center gap-3 rounded-4 bg-surface-gray-1 px-2 py-2 hover:bg-surface-gray-2 sm:col-span-2">
          <Checkbox :model-value="allDesignations" :disabled="!draft.places.length" @update:model-value="toggleAllDesignations" />
          <span class="truncate text-sm-semibold text-ink-gray-9">All designations</span>
          <span class="ml-auto text-xs text-ink-gray-5 tabular-nums">{{ draft.places.length ? inSelected.length : '—' }}</span>
        </label>
        <label v-for="d in designations" :key="d" class="flex cursor-pointer items-center gap-3 rounded-4 px-2 py-2 hover:bg-surface-gray-1">
          <Checkbox
            :model-value="draft.designations.includes(d)"
            :disabled="!draft.places.length"
            @update:model-value="draft.designations = toggleIn(draft.designations, d)"
          />
          <span class="truncate text-sm text-ink-gray-8">{{ d }}</span>
          <span class="ml-auto text-xs text-ink-gray-5 tabular-nums">{{ draft.places.length ? designationCounts[d] ?? 0 : '—' }}</span>
        </label>
      </div>
    </div>
  </div>
</template>
