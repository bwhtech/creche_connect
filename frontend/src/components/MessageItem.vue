<script setup lang="ts">
import { computed, ref } from 'vue'
import { Avatar, Button, Dropdown, Tooltip, toast } from 'frappe-ui'
import { Editor, EditorContent } from 'frappe-ui/editor'
import Reactions from './Reactions.vue'
import { canDelete, editorKit, isAuthor, errorText, excerpt, updateMessage, userById, when } from '../lib/store'

const props = defineProps<{ message: any; compact?: boolean }>()
const emit = defineEmits<{ delete: [] }>()
const author = computed(() => userById(props.message.authorId))
const draft = ref<string | null>(null)
const saving = ref(false)
const menu = computed(() => [
  isAuthor(props.message.authorId) && { label: 'Edit', icon: 'lucide-pencil', onClick: () => (draft.value = props.message.body) },
  { label: 'Delete', icon: 'lucide-trash-2', theme: 'red', onClick: () => emit('delete') },
].filter(Boolean))
async function save() {
  saving.value = true
  try {
    await updateMessage(props.message, 'CrecheConnect Reply', draft.value!)
    draft.value = null
  } catch (e) {
    toast.error(errorText(e, 'Could not save your changes'))
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="group flex gap-3 rounded-4 px-2" :class="compact ? 'py-1' : 'pt-3 pb-1'">
    <div class="w-8 shrink-0">
      <Avatar v-if="!compact" :label="author.name" size="lg" />
      <span v-else class="invisible block pt-0.5 text-2xs text-ink-gray-4 tabular-nums group-hover:visible">
        {{ when(message.at).format('h:mm') }}
      </span>
    </div>
    <div class="min-w-0 flex-1">
      <div v-if="!compact" class="flex items-baseline gap-2">
        <span class="text-base-semibold text-ink-gray-9">{{ author.name }}</span>
        <span class="truncate text-xs text-ink-gray-5">{{ author.title }}</span>
        <Tooltip :text="when(message.at).format('DD MMM YYYY, h:mm A')">
          <span class="ml-auto shrink-0 text-xs text-ink-gray-5">{{ when(message.at).fromNow() }}</span>
        </Tooltip>
      </div>
      <div v-if="draft !== null" class="mt-1.5">
        <div class="rounded-4 border border-outline-gray-2 bg-surface-base">
          <Editor v-model="draft" :extensions="editorKit">
            <EditorContent class="rich max-h-60 min-h-[3.5rem] overflow-y-auto px-3 py-2 text-p-base text-ink-gray-8" />
          </Editor>
        </div>
        <div class="mt-2 flex justify-end gap-2">
          <Button label="Cancel" @click="draft = null" />
          <Button variant="solid" theme="gray" label="Save" :disabled="!excerpt(draft)" :loading="saving" @click="save" />
        </div>
      </div>
      <template v-else>
        <div class="rich mt-0.5 text-p-base text-ink-gray-8" v-html="message.body" />
        <Tooltip v-if="message.editedAt" :text="`Edited ${when(message.editedAt).format('DD MMM YYYY, h:mm A')}`">
          <span class="text-xs text-ink-gray-5">(edited)</span>
        </Tooltip>
      </template>
      <div
        class="mt-1.5"
        :class="Object.keys(message.reactions).length ? '' : 'h-0 overflow-hidden group-hover:h-auto group-hover:overflow-visible focus-within:h-auto'"
      >
        <Reactions :target="message" doctype="CrecheConnect Reply" />
      </div>
    </div>
    <Dropdown
      v-if="canDelete(message.authorId) && draft === null"
      :options="menu"
      align="end"
      :button="{ icon: 'lucide-ellipsis', variant: 'ghost', size: 'sm', 'aria-label': 'Reply actions' }"
      class="shrink-0 self-start"
    />
  </div>
</template>
