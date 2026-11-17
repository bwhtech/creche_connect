<script setup lang="ts">
import { computed, ref } from 'vue'
import { Avatar, Dialog, LoadingIndicator } from 'frappe-ui'
import { errorText, excerpt, fetchEditHistory, userById, when } from '../lib/store'

const props = defineProps<{ doctype: 'CrecheConnect Thread' | 'CrecheConnect Reply'; name: string }>()
const open = defineModel<boolean>('open', { default: false })
const versions = ref<any[] | null>(null)
const error = ref('')
const label = (i: number) => (i === 0 ? 'Current' : i === versions.value!.length - 1 ? 'Original' : `Edit ${versions.value!.length - 1 - i}`)

const MARK = { '': '', add: 'font-bold text-ink-gray-9', del: 'hidden' }

function diff(before: string, after: string) {
  const a = before.split(/(\s+)/)
  const b = after.split(/(\s+)/)
  const lcs = Array.from({ length: a.length + 1 }, () => Array(b.length + 1).fill(0))
  for (let i = a.length - 1; i >= 0; i--)
    for (let j = b.length - 1; j >= 0; j--) lcs[i][j] = a[i] === b[j] ? lcs[i + 1][j + 1] + 1 : Math.max(lcs[i + 1][j], lcs[i][j + 1])
  const out: { text: string; op: keyof typeof MARK }[] = []
  let i = 0
  let j = 0
  while (i < a.length || j < b.length) {
    let next: (typeof out)[number]
    if (i < a.length && j < b.length && a[i] === b[j]) {
      next = { text: a[i++], op: '' }
      j++
    } else if (j < b.length && (i === a.length || lcs[i][j + 1] >= lcs[i + 1][j])) next = { text: b[j++], op: 'add' }
    else next = { text: a[i++], op: 'del' }
    const last = out[out.length - 1]
    if (last?.op === next.op) last.text += next.text
    else out.push(next)
  }
  return out
}
const changes = computed(() =>
  (versions.value ?? []).slice(0, -1).map((v, i) => {
    const prev = versions.value![i + 1]
    return { title: diff(prev.title ?? '', v.title ?? ''), body: diff(excerpt(prev.body ?? ''), excerpt(v.body ?? '')) }
  }),
)

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
        <template v-if="i === versions.length - 1">
          <p v-if="v.title" class="mt-2 text-base-semibold text-ink-gray-9">{{ v.title }}</p>
          <div class="rich mt-1 text-p-base text-ink-gray-8" v-html="v.body" />
        </template>
        <template v-else>
          <p v-if="v.title" class="mt-2 text-base-semibold text-ink-gray-9">
            <span v-for="(c, k) in changes[i].title" :key="k" :class="MARK[c.op]">{{ c.text }}</span>
          </p>
          <p class="mt-1 text-p-base text-ink-gray-8">
            <span v-for="(c, k) in changes[i].body" :key="k" :class="MARK[c.op]">{{ c.text }}</span>
          </p>
        </template>
      </li>
    </ol>
  </Dialog>
</template>
