<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useDropZone } from '@vueuse/core'
import { Badge, Button, Dialog, FormControl, PageHeader, Switch, TabButtons, TextInput, toast, useFileUpload } from 'frappe-ui'
import FileViewer, { canView, fileKind } from '../components/FileViewer.vue'
import GeoPicker from '../components/GeoPicker.vue'
import AudienceChips from '../components/AudienceChips.vue'
import { state, useMe, addResource, updateResource, deleteResource, setPinned, errorText, RESOURCE_KINDS, colorOf, isMobile } from '../lib/store'

const me = useMe()
const route = useRoute()
const router = useRouter()
const selected = computed(() => state.resources.find((r) => r.id === route.query.r) || (isMobile.value ? null : state.resources[0]))
const pick = (r) => router.replace({ query: r ? { r: r.id } : {} })

const isFile = (url: string) => url.startsWith('/private/files/')
const isVideo = (url: string) => fileKind(url) === 'video'
const fileName = (url: string) => decodeURIComponent(url.split('/').pop())
const fileLabel = (f) => f.label || (isFile(f.url) ? fileName(f.url) : f.url.replace(/^https?:\/\//, ''))
const fileIcon = (f) => (!isFile(f.url) ? 'lucide-link' : isVideo(f.url) ? 'lucide-file-video' : 'lucide-file-text')
const kindOf = (r) => ({ ...RESOURCE_KINDS[r.kind], ...colorOf(RESOURCE_KINDS[r.kind].color) })
const viewing = ref(null)
const viewable = (f) => isFile(f.url) && canView(f.url)
const view = (f) => (viewing.value = { url: f.url, name: fileLabel(f) })
const filesCount = (r) => `${r.files.length} ${r.files.length === 1 ? 'file' : 'files'}`

const showNew = ref(false)
const editing = ref(null)
const blankForm = () => ({ title: '', kind: 'Document', description: '', files: [], places: [], designations: [] })
const form = ref(blankForm())
const link = ref('')
const saving = ref(false)
const audience = ref('everyone')
const AUDIENCES = [
  { label: 'Every member', value: 'everyone' },
  { label: 'Selected places', value: 'places' },
]
const { upload, isUploading, progress } = useFileUpload()
const picker = ref<HTMLInputElement>()
const linking = ref(false)
const zone = ref<HTMLElement>()
const SOURCES = [
  { label: 'My device', icon: 'lucide-monitor', go: () => picker.value?.click() },
  { label: 'Link', icon: 'lucide-link', go: () => (linking.value = true) },
]

async function uploadFiles(files: FileList | File[] | null | undefined) {
  const list = [...(files ?? [])]
  if (picker.value) picker.value.value = ''
  for (const file of list) {
    try {
      addFile((await upload(file, { private: true })).file_url)
    } catch (e) {
      toast.error(errorText(e, e?.message || `Could not upload ${file.name}`))
    }
  }
}
const { isOverDropZone } = useDropZone(zone, { onDrop: uploadFiles, multiple: true })
const kindOptions = Object.entries(RESOURCE_KINDS).map(([value, k]) => ({ label: k.label, value }))

function addFile(url: string) {
  if (!form.value.files.length) form.value.kind = !isFile(url) ? 'Link' : isVideo(url) ? 'Video' : 'Document'
  form.value.files.push({ label: '', url })
}
function addLink() {
  if (!link.value.trim()) return
  addFile(link.value.trim())
  link.value = ''
  linking.value = false
}
function openNew() {
  editing.value = null
  form.value = blankForm()
  audience.value = 'everyone'
  linking.value = false
  link.value = ''
  showNew.value = true
}
function openEdit(r) {
  editing.value = r
  form.value = { title: r.title, kind: r.kind, description: r.description || '', files: r.files.map(({ label, url }) => ({ label, url })), places: [...r.places], designations: [...r.designations] }
  audience.value = r.places.length ? 'places' : 'everyone'
  linking.value = false
  link.value = ''
  showNew.value = true
}
async function save() {
  if (!form.value.title.trim() || !form.value.files.length) return toast.error('Add a title and at least one file or link')
  if (audience.value === 'places' && !form.value.places.length) return toast.error('Pick at least one place, or show it to every member')
  if (audience.value === 'everyone') Object.assign(form.value, { places: [], designations: [] })
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
              <AudienceChips v-if="me.admin && selected.places.length" :geo="selected" class="mt-2" />
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
              @click.exact="viewable(f) && ($event.preventDefault(), view(f))"
            >
              <span class="w-4 shrink-0 text-right text-xs text-ink-gray-4 tabular-nums">{{ i + 1 }}</span>
              <span :class="fileIcon(f)" class="size-4 shrink-0 text-ink-gray-6" aria-hidden="true" />
              <span class="min-w-0 flex-1 truncate text-base text-ink-gray-8" :title="fileLabel(f)">{{ fileLabel(f) }}</span>
              <span :class="viewable(f) ? 'lucide-eye' : 'lucide-arrow-up-right'" class="size-4 shrink-0 text-ink-gray-5" aria-hidden="true" />
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
          <div
            class="rounded-4 border border-dashed px-3 py-6 text-center transition-colors"
            ref="zone"
            :class="isOverDropZone ? 'border-outline-gray-4 bg-surface-gray-2' : 'border-outline-gray-3'"
          >
            <div v-if="linking" class="flex gap-2">
              <TextInput v-model="link" class="flex-1" placeholder="https://" aria-label="Link" autofocus @keydown.enter="addLink" />
              <Button variant="solid" theme="gray" label="Add link" @click="addLink" />
              <Button icon="lucide-x" aria-label="Cancel link" @click="linking = false" />
            </div>
            <template v-else>
              <p class="text-p-sm text-ink-gray-6">{{ isUploading ? `Uploading ${progress}%…` : 'Drag and drop files here or add from' }}</p>
              <div class="mt-4 flex justify-center gap-8">
                <button
                  v-for="s in SOURCES"
                  :key="s.label"
                  type="button"
                  class="group flex flex-col items-center gap-1.5 text-sm text-ink-gray-7"
                  :disabled="isUploading"
                  @click="s.go"
                >
                  <span class="inline-flex size-10 items-center justify-center rounded-full bg-surface-gray-2 group-hover:bg-surface-gray-3">
                    <span :class="s.icon" class="size-5 text-ink-gray-7" aria-hidden="true" />
                  </span>
                  {{ s.label }}
                </button>
              </div>
            </template>
            <input ref="picker" type="file" multiple class="hidden" @change="uploadFiles(picker?.files)" />
          </div>
        </div>
        <div>
          <div class="flex items-center gap-3">
            <div class="shrink-0 text-xs text-ink-gray-6">Who can see this</div>
            <TabButtons v-model="audience" class="ml-auto" :options="AUDIENCES" />
          </div>
          <p class="mt-1.5 text-p-xs text-ink-gray-5">Files are private: only members who can see this resource can open them.</p>
          <GeoPicker v-if="audience === 'places'" v-model="form" class="mt-3" />
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
    <FileViewer :file="viewing" @close="viewing = null" />
  </div>
</template>
