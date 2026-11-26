<script setup lang="ts">
import { ref } from 'vue'
import { Avatar, Button, Dialog, toast } from 'frappe-ui'
import { errorText, setAvatar, state, uploadFunction } from '../lib/store'

const open = defineModel<boolean>('open')
const PRESETS = Array.from({ length: 12 }, (_, i) => `/assets/creche_connect/avatars/${i + 1}.svg`)
const picker = ref<HTMLInputElement>()
const busy = ref(false)

async function save(image: () => Promise<string | null>) {
  busy.value = true
  try {
    await setAvatar(await image())
    open.value = false
  } catch (e) {
    toast.error(errorText(e, e?.message || 'Could not change your photo'))
  } finally {
    busy.value = false
  }
}
function upload(file?: File) {
  if (!file) return
  if (!file.type.startsWith('image/')) return toast.error('Pick a photo')
  save(async () => (await uploadFunction(file)).file_url)
}
</script>

<template>
  <Dialog v-if="open" v-model:open="open" title="Your photo">
    <div class="space-y-5">
      <div class="flex items-center gap-4">
        <Avatar :label="state.me.name" :image="state.me.image" size="3xl" />
        <div class="flex flex-wrap gap-2">
          <Button icon-left="lucide-upload" label="Upload photo" :loading="busy" @click="picker?.click()" />
          <Button v-if="state.me.image" label="Remove" :disabled="busy" @click="save(async () => null)" />
        </div>
        <input ref="picker" type="file" accept="image/*" class="hidden" @change="upload(($event.target as HTMLInputElement).files?.[0])" />
      </div>
      <div>
        <p class="mb-2 text-sm text-ink-gray-6">Or pick one</p>
        <div class="grid grid-cols-4 gap-3 sm:grid-cols-6">
          <button
            v-for="(src, i) in PRESETS"
            :key="src"
            type="button"
            class="overflow-hidden rounded-full ring-offset-2 ring-offset-[color:var(--surface-elevation-1)] hover:ring-2 hover:ring-outline-gray-3 disabled:opacity-50"
            :class="state.me.image === src && '!ring-2 !ring-outline-gray-5'"
            :disabled="busy"
            :aria-label="`Avatar ${i + 1}`"
            @click="save(async () => src)"
          >
            <img :src="src" alt="" class="aspect-square w-full" />
          </button>
        </div>
      </div>
    </div>
  </Dialog>
</template>
