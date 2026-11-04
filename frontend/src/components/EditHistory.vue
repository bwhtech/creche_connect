<script setup lang="ts">
import { ref } from 'vue'
import { Avatar, Dialog, LoadingIndicator } from 'frappe-ui'
import { errorText, fetchEditHistory, userById, when } from '../lib/store'

const props = defineProps<{ doctype: 'CrecheConnect Thread' | 'CrecheConnect Reply'; name: string }>()
const open = defineModel<boolean>('open', { default: false })
const versions = ref<any[] | null>(null)
const error = ref('')
const label = (i: number) => (i === 0 ? 'Current' : i === versions.value!.length - 1 ? 'Original' : `Edit ${versions.value!.length - 1 - i}`)

fetchEditHistory(props.doctype, props.name)
  .then((v) => (versions.value = v))
  .catch((e) => (error.value = errorText(e, 'Could not load the edit history')))
</script>

<template>
  <Dialog v-model:open="open" title="Edit history" size="xl">
    <LoadingIndicator v-if="!versions && !error" class="mx-auto my-6 size-5 text-ink-gray-5" />
    <p v-else-if="error" class="text-p-sm text-ink-red-4">{{ error }}</p>
    <ol v-else class="max-h-[60vh] space-y-4 overflow-y-auto">
      <li v-for="(v, i) in versions" :key="v.at" class="rounded-4 border border-outline-gray-1 p-3">
        <div class="flex items-center gap-2">
          <Avatar :label="userById(v.by).name" size="sm" />
          <span class="text-sm text-ink-gray-8">{{ userById(v.by).name }}</span>
          <span class="text-xs text-ink-gray-5">{{ when(v.at).format('DD MMM YYYY, h:mm A') }}</span>
          <span class="ml-auto text-xs text-ink-gray-5">{{ label(i) }}</span>
        </div>
        <p v-if="v.title" class="mt-2 text-base-semibold text-ink-gray-9">{{ v.title }}</p>
        <div class="rich mt-1 text-p-base text-ink-gray-8" v-html="v.body" />
      </li>
    </ol>
  </Dialog>
</template>
