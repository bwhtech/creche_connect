<script setup lang="ts">
import { computed } from 'vue'
import { Avatar, Badge, Progress, Tooltip } from 'frappe-ui'
import { useMe, userById, matchesGeo, placeById, placePath, colorOf } from '../lib/store'

const props = defineProps<{ thread: any; reach: number }>()
const me = useMe()
const geoPlaces = computed(() => (props.thread.geo?.places ?? []).map(placeById).filter(Boolean))
const viaGeo = computed(() => props.thread.geo && matchesGeo(me.value, props.thread.geo))
const seenPct = computed(() => (props.reach ? Math.min(100, Math.round((props.thread.seenBy.length / props.reach) * 100)) : 0))
</script>

<template>
  <div class="space-y-8 p-6">
    <section>
      <h2 class="text-sm text-ink-gray-5">Audience</h2>
      <div class="mt-3 space-y-2">
        <div v-for="p in geoPlaces" :key="p.id" class="flex items-center gap-2.5 py-1">
          <span class="inline-flex size-6 shrink-0 items-center justify-center rounded-4" :class="[colorOf(p.color).soft, colorOf(p.color).ink]">
            <span class="lucide-map-pin size-3.5" aria-hidden="true" />
          </span>
          <div class="min-w-0">
            <div class="truncate text-sm text-ink-gray-8">{{ p.name }}</div>
            <div class="truncate text-xs text-ink-gray-5">{{ p.kind }}{{ p.parent ? ` · ${p.parent}` : '' }}</div>
          </div>
        </div>
        <div v-if="thread.geo" class="pt-1 text-xs text-ink-gray-5">
          {{ thread.geo.designations.length ? thread.geo.designations.join(', ') : 'Every designation' }}
        </div>
      </div>
      <div class="mt-3 flex justify-between border-t border-outline-gray-1 pt-3 text-sm">
        <span class="text-ink-gray-6">Unique people</span>
        <span class="text-ink-gray-9 tabular-nums">{{ reach }}</span>
      </div>
    </section>

    <section>
      <h2 class="text-sm text-ink-gray-5">Seen</h2>
      <div class="mt-2 flex items-baseline justify-between">
        <span class="text-xl text-ink-gray-9 tabular-nums">{{ seenPct }}%</span>
        <span class="text-xs text-ink-gray-5 tabular-nums">{{ thread.seenBy.length }} of {{ reach }}</span>
      </div>
      <Progress class="mt-2" :value="seenPct" />
    </section>

    <section v-if="thread.ackRequired">
      <h2 class="text-sm text-ink-gray-5">Acknowledged</h2>
      <div class="mt-2.5 flex items-center gap-2">
        <div class="flex -space-x-1.5">
          <Tooltip v-for="uid in thread.acks.slice(0, 6)" :key="uid" :text="userById(uid).name">
            <Avatar :label="userById(uid).name" size="sm" class="ring-2 ring-surface-base" />
          </Tooltip>
        </div>
        <span class="text-sm text-ink-gray-7 tabular-nums">{{ thread.acks.length }} of {{ reach }}</span>
      </div>
    </section>

    <section>
      <h2 class="text-sm text-ink-gray-5">Your access</h2>
      <div class="mt-2.5 flex flex-wrap gap-1">
        <Badge v-if="thread.authorId === me.id" label="You started this" theme="blue" variant="subtle" />
        <Badge v-if="viaGeo" :label="`Via ${placePath(me.place)}`" :theme="geoPlaces[0]?.color ?? 'blue'" variant="subtle" />
      </div>
      <p class="mt-2 text-p-xs text-ink-gray-5">{{ thread.canReply ? 'You can reply.' : 'You can read but not reply.' }}</p>
    </section>
  </div>
</template>
