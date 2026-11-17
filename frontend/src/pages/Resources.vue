<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Badge, Button, Dialog, FileUploader, FormControl, PageHeader, Switch, TextInput, toast } from 'frappe-ui'
import { state, useMe, addResource, updateResource, deleteResource, setPinned, errorText, RESOURCE_KINDS, colorOf, isMobile } from '../lib/store'

const me = useMe()
const route = useRoute()
const router = useRouter()
const selected = computed(() => state.resources.find((r) => r.id === route.query.r) || (isMobile.value ? null : state.resources[0]))
const pick = (r) => router.replace({ query: r ? { r: r.id } : {} })

const isFile = (url: string) => url.startsWith('/private/files/')
const isVideo = (url: string) => /\.(mp4|mov|webm|m4v)$/i.test(url)
const fileName = (url: string) => decodeURIComponent(url.split('/').pop())
const fileLabel = (f) => f.label || (isFile(f.url) ? fileName(f.url) : f.url.replace(/^https?:\/\//, ''))
const fileIcon = (f) => (!isFile(f.url) ? 'lucide-link' : isVideo(f.url) ? 'lucide-file-video' : 'lucide-file-text')
const kindOf = (r) => ({ ...RESOURCE_KINDS[r.kind], ...colorOf(RESOURCE_KINDS[r.kind].color) })
const filesCount = (r) => `${r.files.length} ${r.files.length === 1 ? 'file' : 'files'}`

const showNew = ref(false)
const editing = ref(null)
const blankForm = () => ({ title: '', kind: 'Document', description: '', files: [] })
const form = ref(blankForm())
const link = ref('')
const saving = ref(false)
const kindOptions = Object.entries(RESOURCE_KINDS).map(([value, k]) => ({ label: k.label, value }))

function addFile(url: string) {
  if (!form.value.files.length) form.value.kind = !isFile(url) ? 'Link' : isVideo(url) ? 'Video' : 'Document'
  form.value.files.push({ label: '', url })
}
function addLink() {
  if (!link.value.trim()) return
  addFile(link.value.trim())
  link.value = ''
}
function openNew() {
  editing.value = null
  form.value = blankForm()
  link.value = ''
  showNew.value = true
}
function openEdit(r) {
  editing.value = r
  form.value = { title: r.title, kind: r.kind, description: r.description || '', files: r.files.map(({ label, url }) => ({ label, url })) }
  link.value = ''
  showNew.value = true
}
async function save() {
  if (!form.value.title.trim() || !form.value.files.length) return toast.error('Add a title and at least one file or link')
  saving.value = true
  try {
    if (editing.value) await updateResource(editing.value, { ...form.value })
    else pick(await addResource({ ...form.value }))
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
    pick(null)
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

    <div class="flex min-h-0 flex-1">
      <aside v-if="!isMobile || !selected" class="space-y-0.5 overflow-y-auto p-2 md:w-[18rem] md:shrink-0 md:border-r md:border-outline-gray-1" :class="isMobile && 'flex-1'">
        <button
          v-for="r in state.resources"
          :key="r.id"
          class="flex w-full items-center gap-3 rounded-4 px-2 py-2 text-left"
          :class="selected?.id === r.id ? 'bg-surface-gray-3' : 'hover:bg-surface-gray-1'"
          @click="pick(r)"
        >
          <span class="inline-flex size-8 shrink-0 items-center justify-center rounded-5" :class="[kindOf(r).soft, kindOf(r).ink]">
            <span :class="kindOf(r).icon" class="size-4" aria-hidden="true" />
          </span>
          <div class="min-w-0 flex-1">
            <div class="truncate text-base text-ink-gray-8">{{ r.title }}</div>
            <div class="truncate text-xs text-ink-gray-5">{{ filesCount(r) }}</div>
          </div>
        </button>
        <p v-if="!state.resources.length" class="px-2 py-10 text-center text-p-sm text-ink-gray-5">No resources yet.</p>
      </aside>

      <div v-if="selected" class="min-w-0 flex-1 overflow-y-auto">
        <div class="mx-auto max-w-[720px] px-3 pt-6 pb-20 sm:px-6 md:pt-8">
          <Button v-if="isMobile" class="mb-4" variant="ghost" size="sm" icon-left="lucide-arrow-left" label="All resources" @click="pick(null)" />
          <div class="flex items-start gap-3">
            <span class="inline-flex size-10 shrink-0 items-center justify-center rounded-5" :class="[kindOf(selected).soft, kindOf(selected).ink]">
              <span :class="kindOf(selected).icon" class="size-5" aria-hidden="true" />
            </span>
            <div class="min-w-0 flex-1">
              <div class="flex items-center gap-2">
                <h2 class="text-xl text-ink-gray-9">{{ selected.title }}</h2>
                <Badge class="max-md:hidden" :label="kindOf(selected).label" :theme="kindOf(selected).color" variant="subtle" size="sm" />
              </div>
              <p v-if="selected.description" class="mt-1 text-p-sm text-ink-gray-5">{{ selected.description }}</p>
            </div>
            <Switch v-if="me.admin" :model-value="selected.pinned" :label="isMobile ? undefined : 'Pinned'" aria-label="Pinned" @update:model-value="togglePin(selected, $event)" />
            <Button v-if="me.admin" icon="lucide-pencil" aria-label="Edit resource" variant="ghost" @click="openEdit(selected)" />
          </div>
          <div class="mt-6 text-sm text-ink-gray-5">{{ filesCount(selected) }}</div>
          <div class="mt-2 divide-y divide-outline-gray-1 rounded-5 border border-outline-gray-1 p-1">
            <a
              v-for="(f, i) in selected.files"
              :key="f.url + i"
              :href="f.url"
              target="_blank"
              rel="noopener"
              class="flex items-center gap-3 rounded-4 px-3 py-2.5 hover:bg-surface-gray-1"
            >
              <span class="w-4 shrink-0 text-right text-xs text-ink-gray-4 tabular-nums">{{ i + 1 }}</span>
              <span :class="fileIcon(f)" class="size-4 shrink-0 text-ink-gray-6" aria-hidden="true" />
              <span class="min-w-0 flex-1 truncate text-base text-ink-gray-8" :title="fileLabel(f)">{{ fileLabel(f) }}</span>
              <span class="lucide-arrow-up-right size-4 shrink-0 text-ink-gray-5" aria-hidden="true" />
            </a>
          </div>
        </div>
      </div>
    </div>

    <Dialog v-model:open="showNew" :title="editing ? 'Edit resource' : 'Add resource'">
      <div class="space-y-4">
        <FormControl v-model="form.title" label="Title" required />
        <FormControl v-model="form.kind" type="select" label="Type" :options="kindOptions" />
        <FormControl v-model="form.description" label="Short description" placeholder="Optional" />
        <div>
          <div class="mb-1.5 text-xs text-ink-gray-6">Files and links</div>
          <div v-if="form.files.length" class="mb-2 divide-y divide-outline-gray-1 rounded-4 border border-outline-gray-2">
            <div v-for="(f, i) in form.files" :key="f.url + i" class="flex items-center gap-2 px-2 py-1.5">
              <span :class="fileIcon(f)" class="size-4 shrink-0 text-ink-gray-6" aria-hidden="true" />
              <TextInput v-model="f.label" class="min-w-0 flex-1" variant="ghost" :placeholder="fileLabel({ url: f.url })" aria-label="File name" />
              <Button size="sm" variant="ghost" icon="lucide-x" aria-label="Remove file" @click="form.files.splice(i, 1)" />
            </div>
          </div>
          <div class="space-y-2 rounded-4 border border-dashed border-outline-gray-3 px-3 py-4">
            <FileUploader @success="(f) => addFile(f.file_url)" @failure="toast.error('Could not upload the file')">
              <template #default="{ openFileSelector, uploading, progress }">
                <div class="flex flex-col items-center gap-2 text-center">
                  <Button icon-left="lucide-upload" :label="uploading ? `Uploading ${progress}%` : 'Upload file'" :loading="uploading" @click="openFileSelector" />
                  <span class="text-p-sm text-ink-gray-5">PDF, document, picture or video. Only members can open it.</span>
                </div>
              </template>
            </FileUploader>
            <div class="flex gap-2">
              <TextInput v-model="link" class="flex-1" placeholder="Or paste a link: https://" aria-label="Link" @keydown.enter="addLink" />
              <Button icon="lucide-plus" aria-label="Add this link" @click="addLink" />
            </div>
          </div>
        </div>
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
