import { reactive, computed } from 'vue'
import { call, frappeRequest, dayjsLocal } from 'frappe-ui'

const COLORS = {
  blue: { dot: 'bg-surface-blue-7', soft: 'bg-surface-blue-2', ink: 'text-ink-blue-6' },
  green: { dot: 'bg-surface-green-7', soft: 'bg-surface-green-2', ink: 'text-ink-green-6' },
  amber: { dot: 'bg-surface-amber-7', soft: 'bg-surface-amber-2', ink: 'text-ink-amber-6' },
  violet: { dot: 'bg-surface-violet-7', soft: 'bg-surface-violet-2', ink: 'text-ink-violet-6' },
  red: { dot: 'bg-surface-red-7', soft: 'bg-surface-red-2', ink: 'text-ink-red-6' },
}
export const colorOf = (c: string) => COLORS[c] ?? COLORS.blue
export const when = (s: string) => dayjsLocal(s)
export const errorText = (e, fallback: string) => e?.messages?.[0] ?? fallback

const get = (method: string, params = {}) => frappeRequest({ url: method, method: 'GET', params })

export const state = reactive({
  ready: false,
  error: '',
  me: null as any,
  users: [] as any[],
  places: [] as any[],
  designations: [] as any[],
  tags: [] as any[],
  resources: [] as any[],
  emojis: [] as string[],
  threads: [] as any[],
  threadsLoaded: false,
})

// ── Geography ────────────────────────────────────────────────────
// Place ids are code paths: 'CG', 'CG-JSP', 'CG-JSP-KNK'. The Country is the root.

const placeMap = computed(() => Object.fromEntries(state.places.map((p) => [p.id, p])))
export const placeById = (id: string) => placeMap.value[id]
export const rootPlace = computed(() => state.places.find((p) => p.kind === 'Country'))
export const STATES = computed(() => state.places.filter((p) => p.kind === 'State'))
export const inPlace = (userPlace: string, place: string) =>
  place === rootPlace.value?.id || userPlace === place || (userPlace ?? '').startsWith(place + '-')
export const districtsOf = (s: string) => state.places.filter((p) => p.kind === 'District' && p.parentId === s)
export const blocksOf = (d: string) => state.places.filter((p) => p.kind === 'Block' && p.parentId === d)
// The place and the ones above it, nearest first, without the Country.
export function chain(id: string) {
  const out = []
  for (let p = placeById(id); p && p.kind !== 'Country'; p = placeById(p.parentId)) out.push(p)
  return out
}
export const placePath = (id: string) => (id ? chain(id).map((p) => p.name).join(', ') : 'National')

// People at each place, counting everyone below it too.
export const peopleByPlace = computed(() => {
  const counts = {}
  for (const u of state.users) for (const p of chain(u.place)) counts[p.id] = (counts[p.id] ?? 0) + 1
  if (rootPlace.value) counts[rootPlace.value.id] = state.users.length
  return counts
})

export const DESIGNATIONS = computed(() => state.designations.map((d) => d.name))
export const NATIONAL_DESIGNATIONS = computed(() => state.designations.filter((d) => d.is_national).map((d) => d.name))

// ── People ───────────────────────────────────────────────────────

const shapeUser = (m) => ({
  id: m.user,
  name: m.full_name,
  designation: m.designation,
  place: m.place ?? '',
  title: m.place && placeById(m.place) ? `${m.designation}, ${placeById(m.place).name}` : m.designation ?? '',
  admin: !!m.is_admin,
  canPost: !!m.can_post,
})
const userMap = computed(() => Object.fromEntries(state.users.map((u) => [u.id, u])))
export const userById = (id: string) => userMap.value[id] ?? { id, name: id, designation: '', place: '', title: '' }
export const useMe = () => computed(() => state.me)

export const matchesGeo = (u, geo) =>
  !!geo?.places.length &&
  geo.places.some((p) => inPlace(u.place, p)) &&
  (!geo.designations.length || geo.designations.includes(u.designation))
export const reachOf = (a) => state.users.filter((u) => matchesGeo(u, a.geo)).length
const reachById = computed(() => Object.fromEntries(state.threads.map((t) => [t.id, reachOf(t)])))
export const threadReach = (t) => reachById.value[t.id] ?? reachOf(t)
export const allowedPlaces = (u) =>
  u.place ? state.places.filter((p) => p.kind !== 'Country' && inPlace(p.id, u.place)) : state.places

// ── Tags ─────────────────────────────────────────────────────────

const tagMap = computed(() => Object.fromEntries(state.tags.map((t) => [t.id, t])))
export const tagById = (id: string) => tagMap.value[id]
const shapeTag = (t) => ({ id: t.name, name: t.name, color: t.color })

export function toggleIn(list: string[], v: string) {
  return list.includes(v) ? list.filter((x) => x !== v) : [...list, v]
}

// ── Threads ──────────────────────────────────────────────────────

export const canStart = (u) => !!u?.canPost

export const POLICIES = [
  { value: 'everyone', label: 'Anyone in the audience can reply', short: 'Open replies', icon: 'lucide-messages-square', theme: 'green' },
  { value: 'posters', label: 'Only people who can start threads can reply', short: 'Leads reply', icon: 'lucide-shield', theme: 'blue' },
  { value: 'none', label: 'Announcement, replies off', short: 'Announcement', icon: 'lucide-megaphone', theme: 'amber' },
]
export const policyOf = (v: string) => POLICIES.find((p) => p.value === v)!

export const excerpt = (html: string) => html.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim()
const feedRow = (id: string) => state.threads.find((x) => x.id === id)

export async function loadBoot() {
  try {
    const b: any = await get('samvaad.api.get_boot')
    const places = b.places.map((r) => ({ id: r.name, name: r.place_name, kind: r.kind, parentId: r.parent_place, color: r.color }))
    state.places = places
    for (const p of state.places) p.parent = chain(p.parentId).map((x) => x.name).join(', ')
    state.designations = b.designations
    state.tags = b.tags.map(shapeTag)
    state.resources = b.resources.map((r) => ({ ...r, id: r.name, pinned: !!r.pinned }))
    state.emojis = b.emojis
    state.users = b.members.map(shapeUser)
    state.me = shapeUser(b.me)
    state.ready = true
  } catch (e) {
    state.error = errorText(e, e?.message ?? 'Could not load Samvaad')
  }
}

export async function loadThreads() {
  try {
    state.threads = (await get('samvaad.api.get_threads')) as any[]
  } finally {
    state.threadsLoaded = true
  }
}

export const fetchThread = (id: string) => get('samvaad.api.get_thread', { name: id })

export async function markRead(t) {
  await call('samvaad.api.mark_read', { name: t.id })
  const row = feedRow(t.id)
  if (row) row.unread = false
  if (t.authorId !== state.me.id && !t.seenBy.includes(state.me.id)) t.seenBy.push(state.me.id)
}

export async function createThread({ title, body, geo, tags, policy, ackRequired }) {
  const res: any = await call('samvaad.api.create_thread', {
    title,
    content: body,
    places: geo.places,
    designations: geo.designations,
    tags,
    reply_policy: policy,
    ack_required: ackRequired,
  })
  for (const t of res.tags) if (!tagById(t.name)) state.tags.push(shapeTag(t))
  loadThreads()
  return res.name
}

export async function addReply(t, body: string) {
  const reply: any = await call('samvaad.api.add_reply', { thread: t.id, content: body })
  t.replies.push(reply)
  const row = feedRow(t.id)
  if (row) Object.assign(row, { replyCount: row.replyCount + 1, lastActivity: reply.at, unread: false })
}

export async function acknowledge(t) {
  await call('samvaad.api.acknowledge', { thread: t.id })
  for (const x of [t, feedRow(t.id)]) if (x) Object.assign(x, { needsAck: false, acks: [...x.acks, state.me.id] })
}

// `target` is a thread or a reply: both carry `reactions: { emoji: [uid] }`. Optimistic, rolled back on error.
export async function toggleReaction(target, emoji: string, doctype: 'Samvaad Thread' | 'Samvaad Reply') {
  const flip = () => {
    const next = toggleIn(target.reactions[emoji] ?? [], state.me.id)
    if (next.length) target.reactions[emoji] = next
    else delete target.reactions[emoji]
  }
  flip()
  try {
    await call('samvaad.api.toggle_reaction', { doctype, name: target.id, emoji })
  } catch (e) {
    flip()
    throw e
  }
}

// ── Members ──────────────────────────────────────────────────────

export const placeFrom = (s: string, district: string, block: string) => block || district || s || ''

export async function saveUser(form) {
  const user = shapeUser(
    await call('samvaad.api.save_member', {
      email: form.email.trim(),
      full_name: form.name.trim(),
      designation: form.designation,
      place: placeFrom(form.state, form.district, form.block),
      can_post: form.canPost,
      is_new: !form.id,
    }),
  )
  const i = state.users.findIndex((u) => u.id === user.id)
  if (i === -1) state.users.push(user)
  else state.users[i] = user
  if (user.id === state.me.id) state.me = user
}

// ── Program resources ──────────────────────────────────────────────

export const RESOURCE_KINDS = {
  Video: { label: 'Video', icon: 'lucide-circle-play', color: 'red' },
  Course: { label: 'Course', icon: 'lucide-graduation-cap', color: 'violet' },
  Document: { label: 'Document', icon: 'lucide-file-text', color: 'blue' },
  Link: { label: 'Link', icon: 'lucide-link', color: 'green' },
}

export async function addResource({ title, kind, url, description }) {
  const doc: any = await call('frappe.client.insert', {
    doc: { doctype: 'Samvaad Resource', title, kind, url, description, pinned: 1 },
  })
  state.resources.push({ ...doc, id: doc.name, pinned: true })
}

export async function setPinned(r, pinned: boolean) {
  r.pinned = pinned
  await call('frappe.client.set_value', { doctype: 'Samvaad Resource', name: r.id, fieldname: 'pinned', value: pinned ? 1 : 0 })
}
