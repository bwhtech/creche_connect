<script lang="ts">
import { isMobile } from '../lib/store'

const KINDS = { pdf: /\.pdf$/i, image: /\.(png|jpe?g|gif|webp)$/i, video: /\.(mp4|mov|webm|m4v)$/i, docx: /\.docx$/i }
export const fileKind = (url: string) => (Object.keys(KINDS) as (keyof typeof KINDS)[]).find((k) => KINDS[k].test(url)) ?? 'other'
export function zoomedImage(e: Event, name = '') {
  const img = e.target
  if (!(img instanceof HTMLImageElement) || !img.closest('.zoomable')) return null
  if (new URL(img.src).origin !== location.origin || fileKind(img.src) !== 'image') return null
  return { url: img.src, name: img.alt || name }
}
export const canView = (url: string) => !['other', isMobile.value && 'pdf'].includes(fileKind(url))
</script>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { onKeyStroke } from '@vueuse/core'
import DOMPurify from 'dompurify'
import { Button, LoadingIndicator } from 'frappe-ui'

const props = defineProps<{ file: { url: string; name: string } | null }>()
const emit = defineEmits<{ close: [] }>()

const kind = computed(() => props.file && fileKind(props.file.url))

const docxEl = ref<HTMLElement | null>(null)
const loading = ref(false)
const failed = ref(false)

watch(docxEl, async (el) => {
  if (!el || !props.file) return
  loading.value = true
  failed.value = false
  try {
    const [{ renderAsync }, blob] = await Promise.all([import('docx-preview'), fetch(props.file.url).then((r) => r.blob())])
    const draft = document.createElement('div')
    await renderAsync(blob, draft, undefined, { inWrapper: true, renderAltChunks: false, ignoreFonts: true, ignoreWidth: isMobile.value, ignoreHeight: isMobile.value })
    el.innerHTML = DOMPurify.sanitize(draft.innerHTML, { FORCE_BODY: true })
  } catch {
    failed.value = true
  } finally {
    loading.value = false
  }
})

onKeyStroke('Escape', () => props.file && emit('close'))
</script>

<template>
  <Teleport to="body">
    <div v-if="file" class="fixed inset-0 z-50 flex flex-col bg-surface-gray-2" role="dialog" aria-modal="true" :aria-label="file.name">
      <div class="flex shrink-0 items-center gap-2 border-b border-outline-gray-1 bg-surface-base px-3 pb-2 pt-[max(0.5rem,env(safe-area-inset-top))]">
        <Button variant="ghost" icon="lucide-x" aria-label="Close" @click="emit('close')" />
        <span class="min-w-0 flex-1 truncate text-base font-medium text-ink-gray-8">{{ file.name }}</span>
        <Button :href="file.url" :download="file.name" icon-left="lucide-download" label="Download" />
      </div>
      <div class="flex min-h-0 flex-1 overflow-auto">
        <iframe v-if="kind === 'pdf'" :src="file.url" :title="file.name" class="size-full bg-surface-base" />
        <img v-else-if="kind === 'image'" :src="file.url" :alt="file.name" class="m-auto max-h-full max-w-full object-contain" />
        <video v-else-if="kind === 'video'" :src="file.url" controls class="m-auto max-h-full max-w-full" />
        <div v-else-if="kind === 'docx'" class="relative w-full">
          <LoadingIndicator v-if="loading" class="absolute left-1/2 top-10 size-5 text-ink-gray-6" />
          <p v-if="failed" class="p-10 text-center text-p-base text-ink-gray-6">Could not open this document. Use Download.</p>
          <div ref="docxEl" class="docx-view" />
        </div>
        <p v-else class="m-auto p-6 text-center text-p-base text-ink-gray-6">This file can't be shown here. Use Download.</p>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.docx-view :deep(.docx-wrapper) {
  background: transparent;
  padding: 24px 12px;
}
.docx-view :deep(.docx-wrapper > section.docx) {
  max-width: 100%;
  margin-bottom: 16px;
  box-shadow: 0 1px 4px rgb(0 0 0 / 0.12);
}
@media (max-width: 767px) {
  .docx-view :deep(.docx-wrapper > section.docx) {
    padding: 24px 20px !important;
  }
}
</style>
