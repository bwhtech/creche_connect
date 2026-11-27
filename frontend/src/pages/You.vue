<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Avatar, Button, useColorScheme } from 'frappe-ui'
import AvatarPicker from '../components/AvatarPicker.vue'
import { __, lang } from '../lib/translate'
import { state, useMe, logout, togglePush, changeLanguage } from '../lib/store'
import { pushOffered, pushOn } from '../lib/push'

const me = useMe()
const router = useRouter()
const picking = ref(false)
const { resolvedColorScheme, toggleColorScheme } = useColorScheme()
const dark = computed(() => resolvedColorScheme.value === 'dark')

const groups = computed(() => [
  [
    { label: __('Users'), icon: 'lucide-users', onClick: () => router.push('/users') },
    ...(me.value.admin ? [{ label: __('Insights'), icon: 'lucide-chart-column', onClick: () => router.push('/insights') }] : []),
  ],
  [
    ...(pushOffered ? [{ label: __('Notifications'), icon: 'lucide-bell', value: pushOn.value ? __('On') : __('Off'), onClick: togglePush }] : []),
    { label: __('Theme'), icon: dark.value ? 'lucide-moon' : 'lucide-sun', value: dark.value ? __('Dark') : __('Light'), onClick: toggleColorScheme },
    ...(state.languages.length > 1 ? [{ label: __('Language'), icon: 'lucide-languages', value: state.languages.find((l) => l.name === lang)?.language_name, select: true }] : []),
    { label: __('Log out'), icon: 'lucide-log-out', onClick: logout },
  ],
])
</script>

<template>
  <div class="h-full overflow-y-auto bg-surface-gray-1 px-4 pt-8 pb-28">
    <div class="mx-auto max-w-md">
      <div class="flex flex-col items-center text-center">
        <button type="button" class="rounded-full active:opacity-70" :aria-label="me.image ? __('Change photo') : __('Add photo')" @click="picking = true">
          <Avatar :label="me.name" :image="me.image" size="3xl" />
        </button>
        <div class="mt-5 max-w-full truncate text-2xl font-semibold text-ink-gray-9">{{ me.name }}</div>
        <p v-if="me.admin || me.title" class="text-p-base text-ink-gray-6">{{ [me.admin && __('Admin'), me.title].filter(Boolean).join(' · ') }}</p>
        <Button variant="ghost" size="lg" class="mt-2" :label="me.image ? __('Change photo') : __('Add photo')" @click="picking = true" />
      </div>

      <nav v-for="(items, i) in groups" :key="i" class="mt-6 overflow-hidden rounded-7 bg-surface-base">
        <component :is="item.select ? 'label' : 'button'" v-for="(item, j) in items" :key="item.label" :type="item.select ? undefined : 'button'" class="relative block w-full text-left active:bg-surface-gray-2" @click="item.onClick">
          <span class="flex min-h-14 w-full items-stretch">
            <span class="flex w-14 shrink-0 items-center justify-center">
              <span :class="[item.icon, 'size-5 text-ink-gray-8']" aria-hidden="true" />
            </span>
            <span class="flex min-w-0 flex-1 items-center gap-3 py-3 pr-4" :class="j > 0 && 'border-t border-outline-gray-1'">
              <span class="min-w-0 flex-1 truncate text-base text-ink-gray-9">{{ item.label }}</span>
              <span v-if="item.value" class="shrink-0 text-base text-ink-gray-5">{{ item.value }}</span>
              <span class="lucide-chevron-right size-4 shrink-0 text-ink-gray-4" aria-hidden="true" />
            </span>
          </span>
          <select v-if="item.select" class="absolute inset-0 opacity-0" :value="lang" :aria-label="item.label" @change="changeLanguage(($event.target as HTMLSelectElement).value)">
            <option v-for="l in state.languages" :key="l.name" :value="l.name">{{ l.language_name }}</option>
          </select>
        </component>
      </nav>
    </div>
    <AvatarPicker v-model:open="picking" />
  </div>
</template>
