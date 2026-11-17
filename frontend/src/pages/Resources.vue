<script setup lang="ts">
import { ref } from 'vue'
import { Badge, Button, Dialog, FileUploader, FormControl, PageHeader, Switch, TabButtons, toast } from 'frappe-ui'
import { state, useMe, addResource, updateResource, deleteResource, setPinned, errorText, RESOURCE_KINDS, colorOf, isMobile } from '../lib/store'

const me = useMe()
const showNew = ref(false)
const editing = ref(null)
const blankForm = () => ({ title: '', kind: 'Document', url: '', description: '' })
const form = ref(blankForm())
const source = ref('file')
const SOURCES = [{ label: 'File', value: 'file' }, { label: 'Link', value: 'link' }]
const isFile = (url: string) => url.startsWith('/private/files/')
const fileName = (url: string) => decodeURIComponent(url.split('/').pop())
const onUploaded = (f) => Object.assign(form.value, { url: f.file_url, kind: /\.(mp4|mov|webm|m4v)$/i.test(f.file_url) ? 'Video' : 'Document' })
const saving = ref(false)
const kindOptions = Object.entries(RESOURCE_KINDS).map(([value, k]) => ({ label: k.label, value }))

function openNew() {
  editing.value = null
  form.value = blankForm()
  source.value = 'file'
  showNew.value = true
}
function openEdit(r) {
  editing.value = r
  form.value = { title: r.title, kind: r.kind, url: r.url, description: r.description || '' }
  source.value = isFile(r.url) ? 'file' : 'link'
  showNew.value = true
}
async function save() {
  if (!form.value.title.trim() || !form.value.url.trim()) return toast.error('Add a title and a link or file')
  saving.value = true
  try {
    if (editing.value) await updateResource(editing.value, { ...form.value })
    else await addResource({ ...form.value })
    showNew.value = false
    toast.success(editing.value ? 'Resource updated' : 'Resource added')
  } catch (e) {
    toast.error(errorText(e, editing.value ? 'Could not update the resource' : 'Could not add the resource'))
  } finally {
    saving.value = false
  }
}
const confirmingDelete = ref(false)
const deleteActions = [
  { label: 'Cancel', onClick: ({ close }) => close() },
  { label: 'Delete', variant: 'solid', theme: 'red', onClick: remove },
]
async function remove({ close }) {
  try {
    await deleteResource(editing.value)
    close()
    showNew.value = false
    toast.success('Resource deleted')
  } catch (e) {
    toast.error(errorText(e, 'Could not delete the resource'))
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
      <Button v-if="me.admin" class="ml-auto" variant="solid" theme="gray" icon-left="lucide-plus" :label="isMobile ? 'Add' : 'Add resource'" @click="openNew" />
    </PageHeader>

    <div class="min-h-0 flex-1 overflow-y-auto">
      <div class="mx-auto max-w-[860px] px-3 pt-8 pb-20 sm:px-6">
        <p class="mb-6 text-p-sm text-ink-gray-5">
          Videos, courses, documents and links for everyone in the program.
          {{ me.admin ? 'Pinned resources show in the sidebar.' : '' }}
        </p>
        <div class="divide-y divide-outline-gray-1 rounded-5 border border-outline-gray-1">
          <div v-for="r in state.resources" :key="r.id" class="flex items-center gap-3 px-4 py-3.5 md:gap-4 md:px-5 md:py-4">
            <span
              class="inline-flex size-10 shrink-0 items-center justify-center rounded-5"
              :class="[colorOf(RESOURCE_KINDS[r.kind].color).soft, colorOf(RESOURCE_KINDS[r.kind].color).ink]"
            >
              <span :class="RESOURCE_KINDS[r.kind].icon" class="size-5" aria-hidden="true" />
            </span>
            <div class="min-w-0 flex-1">
              <div class="flex items-center gap-2">
                <span class="truncate text-base text-ink-gray-8">{{ r.title }}</span>
                <Badge class="max-md:hidden" :label="RESOURCE_KINDS[r.kind].label" :theme="RESOURCE_KINDS[r.kind].color" variant="subtle" size="sm" />
              </div>
              <div class="mt-0.5 truncate text-sm text-ink-gray-5">{{ r.description }}</div>
            </div>
            <Switch v-if="me.admin" :model-value="r.pinned" :label="isMobile ? undefined : 'Pinned'" aria-label="Pinned" @update:model-value="togglePin(r, $event)" />
            <Button v-if="me.admin" icon="lucide-pencil" aria-label="Edit resource" variant="ghost" @click="openEdit(r)" />
            <Button icon-right="lucide-arrow-up-right" :label="isMobile ? undefined : 'Open'" aria-label="Open" :href="r.url" />
          </div>
        </div>
      </div>
    </div>

    <Dialog v-model:open="showNew" :title="editing ? 'Edit resource' : 'Add resource'">
      <div class="space-y-4">
        <FormControl v-model="form.title" label="Title" required />
        <div>
          <div class="mb-1.5 flex items-center">
            <span class="text-xs text-ink-gray-6">Source</span>
            <TabButtons
              v-model="source"
              class="ml-auto [&_[data-state=active]]:font-medium [&_[data-state=active]_*]:!text-ink-gray-9 [&_[data-state=inactive]_*]:!text-ink-gray-7"
              :options="SOURCES"
              @update:model-value="form.url = ''"
            />
          </div>
          <FileUploader v-if="source === 'file'" @success="onUploaded" @failure="toast.error('Could not upload the file')">
            <template #default="{ openFileSelector, uploading, progress }">
              <div v-if="form.url" class="flex items-center gap-2 rounded-4 border border-outline-gray-2 px-3 py-2">
                <span :class="RESOURCE_KINDS[form.kind].icon" class="size-4 shrink-0 text-ink-gray-6" aria-hidden="true" />
                <span class="min-w-0 flex-1 truncate text-base text-ink-gray-8">{{ fileName(form.url) }}</span>
                <Button size="sm" :label="uploading ? `${progress}%` : 'Replace'" :loading="uploading" @click="openFileSelector" />
                <Button size="sm" variant="ghost" icon="lucide-x" aria-label="Remove file" @click="form.url = ''" />
              </div>
              <div v-else class="flex flex-col items-center gap-2 rounded-4 border border-dashed border-outline-gray-3 px-3 py-5 text-center">
                <Button icon-left="lucide-upload" :label="uploading ? `Uploading ${progress}%` : 'Choose file'" :loading="uploading" @click="openFileSelector" />
                <span class="text-p-sm text-ink-gray-5">PDF, document, picture or video. Only members can open it.</span>
              </div>
            </template>
          </FileUploader>
          <FormControl v-else v-model="form.url" placeholder="https://" aria-label="Link" />
        </div>
        <FormControl v-model="form.kind" type="select" label="Type" :options="kindOptions" />
        <FormControl v-model="form.description" label="Short description" placeholder="Optional" />
        <div class="flex justify-end gap-2 pt-2">
          <Button v-if="editing" class="mr-auto" theme="red" icon-left="lucide-trash-2" label="Delete" @click="confirmingDelete = true" />
          <Button label="Cancel" @click="showNew = false" />
          <Button variant="solid" theme="gray" :label="editing ? 'Save' : 'Add'" :loading="saving" @click="save" />
        </div>
      </div>
    </Dialog>

    <Dialog
      v-model:open="confirmingDelete"
      title="Delete this resource?"
      message="It will be removed from the resources list and the sidebar."
      icon="lucide-trash-2"
      theme="red"
      :actions="deleteActions"
    />
  </div>
</template>
