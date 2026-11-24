import { RichTextKit } from 'frappe-ui/editor'
import { Audio } from './audio'
import { __ } from './translate'
import { DESIGNATIONS, state, uploadFunction } from './store'

const mentionItems = (people: any[]) => [
  ...DESIGNATIONS.value.filter((d) => people.some((u) => u.designation === d)).map((d) => ({ label: __(d), value: `designation:${d}`, group: __('Groups') })),
  ...people.map((u) => ({ label: u.name, value: u.id, group: __('People') })),
]
export const editorKit = (people: () => any[]) => [
  RichTextKit.configure({
    textAlign: false,
    image: { uploadFunction },
    contentPaste: { uploadFunction },
    video: { uploadFunction, HTMLAttributes: { preload: 'metadata' } },
    attachment: false,
    mention: { items: () => mentionItems(people().filter((u) => u.id !== state.me?.id)) },
  }),
  Audio,
]
