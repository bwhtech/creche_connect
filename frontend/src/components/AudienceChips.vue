<script setup lang="ts">
import { computed } from 'vue'
import { Badge } from 'frappe-ui'
import { placeById, DESIGNATIONS, NATIONAL_DESIGNATIONS } from '../lib/store'

const props = defineProps<{ geo?: any }>()
const chip = computed(() => {
  const g = props.geo
  if (!g?.places?.length) return null
  const places = g.places.map((id) => placeById(id)?.name).join(', ')
  const plural = (d: string) => (d === 'Head of operations' ? 'Heads of operations' : `${d}s`)
  // Every field designation ticked reads the same as none: everyone there.
  const all = DESIGNATIONS.value.filter((d) => !NATIONAL_DESIGNATIONS.value.includes(d)).every((d) => g.designations.includes(d))
  const who = g.designations.length && !all ? g.designations.map(plural).join(', ') : 'Everyone'
  return { label: `${places} · ${who}`, color: placeById(g.places[0])?.color ?? 'blue' }
})
</script>

<template>
  <Badge v-if="chip" :label="chip.label" variant="subtle" :theme="chip.color" size="sm" class="max-w-full">
    <template #prefix><span class="lucide-map-pin size-3 shrink-0" aria-hidden="true" /></template>
  </Badge>
</template>
