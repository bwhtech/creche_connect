import { Node, mergeAttributes } from '@tiptap/core'

export const Audio = Node.create({
  name: 'audio',
  group: 'block',
  atom: true,
  selectable: true,
  draggable: true,
  addAttributes: () => ({ src: { default: null } }),
  parseHTML: () => [{ tag: 'audio[src]' }],
  renderHTML: ({ HTMLAttributes }) => ['audio', mergeAttributes(HTMLAttributes, { controls: '', preload: 'metadata' })],
})
