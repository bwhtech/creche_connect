<script setup lang="ts">
import { ref } from 'vue'
import { Badge, Button, Dialog, FormControl, PageHeader, Switch, toast } from 'frappe-ui'
import { state, useMe, addResource, setPinned, errorText, RESOURCE_KINDS, colorOf } from '../lib/store'

const me = useMe()
const showNew = ref(false)
const form = ref({ title: '', kind: 'Video', url: '', description: '' })
const saving = ref(false)
const kindOptions = Object.entries(RESOURCE_KINDS).map(([value, k]) => ({ label: k.label, value }))

async function create() {
  if (!form.value.title.trim() || !form.value.url.trim()) return toast.error('Add a title and a link')
  saving.value = true
  try {
    await addResource({ ...form.value })
    showNew.value = false
    form.value = { title: '', kind: 'Video', url: '', description: '' }
    toast.success('Resource added and pinned to the sidebar')
  } catch (e) {
    toast.error(errorText(e, 'Could not add the resource'))
  } finally {
    saving.value = false
  }
}
function togglePin(r, pinned: boolean) {
  setPinned(r, pinned).catch(() => {
    r.pinned = !pinned
    toast.error('Could not update the resource')
  })
}
</script>

<template>
  <div class="flex h-full flex-col">
    <PageHeader>
      <h1 class="text-2xl text-ink-gray-9">Program resources</h1>
      <Button v-if="me.admin" class="ml-auto" variant="solid" theme="gray" icon-left="lucide-plus" label="Add resource" @click="showNew = true" />
    </PageHeader>

    <div class="min-h-0 flex-1 overflow-y-auto">
      <div class="mx-auto max-w-[860px] px-3 pt-8 pb-20 sm:px-6">
        <p class="mb-6 text-p-sm text-ink-gray-5">
          Videos, courses, documents and links for everyone in the program.
          {{ me.admin ? 'Pinned resources show in the sidebar.' : '' }}
        </p>
        <div class="divide-y divide-outline-gray-1 rounded-5 border border-outline-gray-1">
          <div v-for="r in state.resources" :key="r.id" class="flex items-center gap-4 px-5 py-4">
            <span
              class="inline-flex size-10 shrink-0 items-center justify-center rounded-5"
              :class="[colorOf(RESOURCE_KINDS[r.kind].color).soft, colorOf(RESOURCE_KINDS[r.kind].color).ink]"
            >
              <span :class="RESOURCE_KINDS[r.kind].icon" class="size-5" aria-hidden="true" />
            </span>
            <div class="min-w-0 flex-1">
              <div class="flex items-center gap-2">
                <span class="truncate text-base text-ink-gray-8">{{ r.title }}</span>
                <Badge :label="RESOURCE_KINDS[r.kind].label" :theme="RESOURCE_KINDS[r.kind].color" variant="subtle" size="sm" />
              </div>
              <div class="mt-0.5 truncate text-sm text-ink-gray-5">{{ r.description }}</div>
            </div>
            <Switch v-if="me.admin" :model-value="r.pinned" label="Pinned" @update:model-value="togglePin(r, $event)" />
            <Button icon-right="lucide-arrow-up-right" label="Open" :href="r.url" />
          </div>
        </div>
      </div>
    </div>

    <Dialog v-model:open="showNew" title="Add resource">
      <div class="space-y-4">
        <FormControl v-model="form.title" label="Title" required />
        <FormControl v-model="form.kind" type="select" label="Type" :options="kindOptions" />
        <FormControl v-model="form.url" label="Link" required />
        <FormControl v-model="form.description" label="Short description" />
        <div class="flex justify-end gap-2 pt-2">
          <Button label="Cancel" @click="showNew = false" />
          <Button variant="solid" theme="gray" label="Add and pin" :loading="saving" @click="create" />
        </div>
      </div>
    </Dialog>
  </div>
</template>
