<script setup lang="ts">
import { computed, ref } from 'vue'
import { usePointerSwipe } from '@vueuse/core'
import { Avatar, BottomSheet, Dialog, LoadingIndicator } from 'frappe-ui'
import HtmlDiff from 'htmldiff-js'
import DOMPurify from 'dompurify'
import { __ } from '../lib/translate'
import { errorText, fetchEditHistory, isMobile, userById, when } from '../lib/store'

const props = defineProps<{ doctype: 'CrecheConnect Thread' | 'CrecheConnect Reply'; name: string }>()
const open = defineModel<boolean>('open', { default: false })
const versions = ref<any[] | null>(null)
const error = ref('')
const current = ref(0)
const label = (i: number) => (i === 0 ? __('Current') : i === versions.value!.length - 1 ? __('Original') : __('Edit {0}', versions.value!.length - 1 - i))

const execute = (HtmlDiff as any).default?.execute || HtmlDiff.execute
const makeDiff = (before: string, after: string) => DOMPurify.sanitize(execute(before, after))
const escape = (t = '') => t.replace(/&/g, '&amp;').replace(/</g, '&lt;')
const shown = computed(() => {
  const v = versions.value?.[current.value]
  if (!v) return null
  const prev = versions.value![current.value + 1]
  return {
    ...v,
    title: v.title && (prev ? makeDiff(escape(prev.title), escape(v.title)) : escape(v.title)),
    body: prev ? makeDiff(prev.body ?? '', v.body ?? '') : DOMPurify.sanitize(v.body ?? ''),
  }
})

const preview = ref<HTMLElement | null>(null)
const { distanceX } = usePointerSwipe(preview, {
  pointerTypes: ['touch'],
  onSwipeEnd(_, direction) {
    if (Math.abs(distanceX.value) < 60 || !versions.value) return
    if (direction === 'left') current.value = Math.min(current.value + 1, versions.value.length - 1)
    if (direction === 'right') current.value = Math.max(current.value - 1, 0)
  },
})

fetchEditHistory(props.doctype, props.name)
  .then((v) => (versions.value = v))
  .catch((e) => (error.value = errorText(e, __('Could not load the edit history'))))
</script>

<template>
  <component :is="isMobile ? BottomSheet : Dialog" v-model:open="open" :title="__('Edit history')" :size="isMobile ? undefined : '4xl'">
    <div :class="isMobile && 'px-4 pb-6'">
      <LoadingIndicator v-if="!versions && !error" class="mx-auto my-6 size-5 text-ink-gray-6" />
      <p v-else-if="error" class="text-p-sm text-ink-red-4">{{ error }}</p>
      <div v-else class="grid gap-6 md:grid-cols-[200px_minmax(0,1fr)]">
        <div v-if="isMobile" class="flex justify-center gap-1.5">
          <button
            v-for="(v, i) in versions"
            :key="v.at"
            type="button"
            class="size-2 rounded-full transition-transform"
            :class="i === current ? 'scale-125 bg-surface-gray-9' : 'bg-surface-gray-3'"
            :aria-label="label(i)"
            @click="current = i"
          />
        </div>
        <div v-else class="max-h-[60vh] space-y-1 overflow-y-auto" role="listbox">
          <button
            v-for="(v, i) in versions"
            :key="v.at"
            type="button"
            role="option"
            :aria-selected="i === current"
            class="w-full rounded-4 px-3 py-2 text-left transition-colors"
            :class="i === current ? 'bg-surface-gray-2 text-ink-gray-9' : 'text-ink-gray-7 hover:bg-surface-gray-1'"
            @click="current = i"
          >
            <div class="text-sm font-medium">{{ label(i) }}</div>
            <div class="mt-0.5 text-xs text-ink-gray-6">{{ when(v.at).format('DD MMM YYYY, h:mm A') }}</div>
          </button>
        </div>
        <div v-if="shown" ref="preview" class="min-w-0 md:max-h-[60vh] md:overflow-y-auto">
          <div class="mb-3 flex items-center gap-2">
            <Avatar :label="userById(shown.by).name" :image="userById(shown.by).image" size="md" />
            <div>
              <div class="text-sm font-medium text-ink-gray-8">{{ userById(shown.by).name }}</div>
              <div class="text-xs text-ink-gray-6">{{ label(current) }} · {{ when(shown.at).format('DD MMM YYYY, h:mm A') }}</div>
            </div>
          </div>
          <p v-if="shown.title" class="diff text-base-semibold text-ink-gray-9" v-html="shown.title" />
          <div class="diff rich mt-1 text-p-base text-ink-gray-8" v-html="shown.body" />
        </div>
      </div>
    </div>
  </component>
</template>

<style scoped>
.diff :deep(ins) {
  all: unset;
  @apply bg-surface-green-2;
}
.diff :deep(del) {
  all: unset;
  @apply bg-surface-red-2;
}
</style>
