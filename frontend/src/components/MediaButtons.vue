<script setup lang="ts">
import { ref, onBeforeUnmount } from 'vue'
import { Button, Tooltip, toast } from 'frappe-ui'
import { uploadFunction, errorText } from '../lib/store'

const props = defineProps<{ editor: any }>()
const MAX_SECONDS = 600
const picker = ref<HTMLInputElement>()
const uploading = ref(false)
const recorder = ref<MediaRecorder | null>(null)
const seconds = ref(0)
let timer: ReturnType<typeof setInterval>
let keep = false

async function addAudio(file: File) {
  uploading.value = true
  try {
    const { file_url } = await uploadFunction(file)
    props.editor.chain().focus().insertContent([{ type: 'audio', attrs: { src: file_url } }, { type: 'paragraph' }]).run()
  } catch (e) {
    toast.error(errorText(e, e?.message || 'Could not upload the audio'))
  } finally {
    uploading.value = false
  }
}
function attach(file?: File) {
  if (!file) return
  if (file.type.startsWith('video/')) props.editor.chain().focus().uploadVideo(file).run()
  else if (file.type.startsWith('audio/')) addAudio(file)
  else toast.error('Pick an audio or video file')
}
function onPick(e: Event) {
  const input = e.target as HTMLInputElement
  attach(input.files?.[0])
  input.value = ''
}

async function record() {
  let stream: MediaStream
  try {
    stream = await navigator.mediaDevices.getUserMedia({ audio: true })
  } catch {
    return toast.error('Allow microphone access to record a voice note')
  }
  const chunks: Blob[] = []
  const r = new MediaRecorder(stream, { audioBitsPerSecond: 32000 })
  r.ondataavailable = (e) => chunks.push(e.data)
  r.onstop = () => {
    stream.getTracks().forEach((t) => t.stop())
    clearInterval(timer)
    recorder.value = null
    const type = r.mimeType.split(';')[0]
    const ext = { 'audio/mp4': 'm4a', 'audio/ogg': 'ogg' }[type] ?? 'webm'
    if (keep) attach(new File(chunks, `voice-note.${ext}`, { type }))
  }
  seconds.value = 0
  timer = setInterval(() => ++seconds.value >= MAX_SECONDS && stop(true), 1000)
  r.start()
  recorder.value = r
}
function stop(save: boolean) {
  keep = save
  recorder.value?.stop()
}
onBeforeUnmount(() => stop(false))

const clock = (s: number) => `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`
</script>

<template>
  <div class="flex items-center gap-1">
    <template v-if="recorder">
      <span class="flex items-center gap-1.5 px-1 text-sm text-ink-red-4 tabular-nums">
        <span class="size-2 animate-pulse rounded-full bg-surface-red-5" aria-hidden="true" />{{ clock(seconds) }}
      </span>
      <Tooltip text="Discard">
        <Button variant="ghost" icon="lucide-x" aria-label="Discard recording" @click="stop(false)" />
      </Tooltip>
      <Tooltip text="Add voice note">
        <Button variant="ghost" icon="lucide-check" aria-label="Add voice note" @click="stop(true)" />
      </Tooltip>
    </template>
    <template v-else>
      <Tooltip text="Attach audio or video">
        <Button variant="ghost" icon="lucide-paperclip" aria-label="Attach audio or video" :loading="uploading" @click="picker?.click()" />
      </Tooltip>
      <Tooltip text="Record a voice note">
        <Button variant="ghost" icon="lucide-mic" aria-label="Record a voice note" @click="record" />
      </Tooltip>
    </template>
    <input ref="picker" type="file" accept="audio/*,video/*" class="hidden" @change="onPick" />
  </div>
</template>
