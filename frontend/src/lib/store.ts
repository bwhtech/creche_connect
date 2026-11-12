import { reactive, computed } from 'vue'
import { call, frappeRequest, dayjsLocal, upload } from 'frappe-ui'
import { io } from 'socket.io-client'
import { RichTextKit } from 'frappe-ui/editor'

const COLORS = {
  blue: { dot: 'bg-surface-blue-7', soft: 'bg-surface-blue-2', ink: 'text-ink-blue-6' },
  green: { dot: 'bg-surface-green-7', soft: 'bg-surface-green-2', ink: 'text-ink-green-6' },
  amber: { dot: 'bg-surface-amber-7', soft: 'bg-surface-amber-2', ink: 'text-ink-amber-6' },
  violet: { dot: 'bg-surface-violet-7', soft: 'bg-surface-violet-2', ink: 'text-ink-violet-6' },
  red: { dot: 'bg-surface-red-7', soft: 'bg-surface-red-2', ink: 'text-ink-red-6' },
}
const uploadFunction = (file: File, o?: Parameters<typeof upload>[1]) => upload(file, { ...o, private: false, optimize: true })
export const editorKit = [
  RichTextKit.configure({
    textAlign: false,
    image: { uploadFunction },
    contentPaste: { uploadFunction },
    video: false,
    attachment: false,
  }),
]
export const colorOf = (c: string) => COLORS[c] ?? COLORS.blue
const PLACE_COLORS = { Country: 'amber', State: 'green', District: 'blue', Block: 'violet' }
export const when = (s: string) => dayjsLocal(s)
export const errorText = (e, fallback: string) => e?.messages?.[0] ?? fallback

const BUSY = ['QueryDeadlockError', 'QueryTimeoutError']
async function post(method: string, params = {}, tries = 5) {
  try {
    return await call(method, params)
  } catch (e) {
    if (tries <= 1 || !BUSY.includes(e?.exc_type)) throw e
    await new Promise((r) => setTimeout(r, 150 + Math.random() * 350))
    return post(method, params, tries - 1)
  }
}

export const get = (method: string, params = {}) =>
  frappeRequest({ url: method, method: 'GET', params: Object.fromEntries(Object.entries(params).filter(([, v]) => v != null)) })

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
  cursor: null as string | null,
  feed: { filter: undefined as string | undefined, tag: undefined as string | undefined },
  counts: { total: 0, tags: {} as Record<string, number>, unread: 0, ack: 0 },
  activity: null as { thread: string } | null,
})

const placeMap = computed(() => Object.fromEntries(state.places.map((p) => [p.id, p])))
export const placeById = (id: string) => placeMap.value[id]
export const rootPlace = computed(() => state.places.find((p) => p.kind === 'Country'))
export const STATES = computed(() => state.places.filter((p) => p.kind === 'State'))
export const inPlace = (userPlace: string, place: string) =>
  place === rootPlace.value?.id || userPlace === place || (userPlace ?? '').startsWith(place + '-')
export const districtsOf = (s: string) => state.places.filter((p) => p.kind === 'District' && p.parentId === s)
export const blocksOf = (d: string) => state.places.filter((p) => p.kind === 'Block' && p.parentId === d)
export function chain(id: string) {
  const out = []
  for (let p = placeById(id); p && p.kind !== 'Country'; p = placeById(p.parentId)) out.push(p)
  return out
}
export const placePath = (id: string) => (id ? chain(id).map((p) => p.name).join(', ') : 'National')

export const peopleByPlace = computed(() => {
  const counts = {}
  for (const u of state.users) for (const p of chain(u.place)) counts[p.id] = (counts[p.id] ?? 0) + 1
  if (rootPlace.value) counts[rootPlace.value.id] = state.users.length
  return counts
})

export const DESIGNATIONS = computed(() => state.designations.map((d) => d.name))
export const NATIONAL_DESIGNATIONS = computed(() => state.designations.filter((d) => d.is_national).map((d) => d.name))

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

const tagMap = computed(() => Object.fromEntries(state.tags.map((t) => [t.id, t])))
export const tagById = (id: string) => tagMap.value[id]
const shapeTag = (t) => ({ id: t.name, name: t.name, color: t.color })

export function toggleIn(list: string[], v: string) {
  return list.includes(v) ? list.filter((x) => x !== v) : [...list, v]
}

export const canStart = (u) => !!u?.canPost

export const POLICIES = [
  { value: 'everyone', label: 'Anyone in the audience can reply', short: 'Open replies', icon: 'lucide-messages-square', theme: 'green' },
  { value: 'posters', label: 'Only people who can start threads can reply', short: 'Leads reply', icon: 'lucide-shield', theme: 'blue' },
  { value: 'none', label: 'Announcement, replies off', short: 'Announcement', icon: 'lucide-megaphone', theme: 'amber' },
]
export const policyOf = (v: string) => POLICIES.find((p) => p.value === v)!

export const excerpt = (html: string) => html.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim()
export const isBlank = (html: string) => !excerpt(html) && !html.includes('<img')
const feedRow = (id: string) => state.threads.find((x) => x.id === id)

export async function loadBoot() {
  try {
    const b: any = await get('creche_connect.api.get_boot')
    const places = b.places.map((r) => ({ id: r.name, name: r.place_name, kind: r.kind, parentId: r.parent_place, color: PLACE_COLORS[r.kind] }))
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
    state.error = errorText(e, e?.message ?? 'Could not load CrecheConnect')
  }
}

const latest = <A extends any[], R>(fn: (...args: A) => Promise<R>) => {
  let last = 0
  return (...args: A): Promise<R | undefined> => {
    const call = ++last
    return fn(...args).then(
      (r) => (call === last ? r : undefined),
      (e) => {
        if (call === last) throw e
      },
    )
  }
}

const fetchFeed = latest((params) => get('creche_connect.api.get_threads', params))
export async function loadThreads(mode: 'reset' | 'more' | 'refresh' = 'reset') {
  if (mode === 'reset') state.cursor = null
  try {
    const page: any = await fetchFeed({
      ...state.feed,
      cursor: mode === 'more' ? state.cursor : null,
      limit: mode === 'refresh' ? state.threads.length : null,
    })
    if (!page) return
    state.threads = mode === 'more' ? [...state.threads, ...page.threads] : page.threads
    state.cursor = page.cursor
  } finally {
    state.threadsLoaded = true
  }
}

const fetchCounts = latest((filter?: string) => get('creche_connect.api.get_counts', { filter }))
export async function loadCounts() {
  const counts: any = await fetchCounts(state.feed.filter)
  if (counts) state.counts = counts
}

// The socket namespace must be the site name.
export function listenForActivity() {
  const { hostname, protocol, origin } = window.location
  const host = window.socketio_port ? `${protocol}//${hostname}:${window.socketio_port}` : origin
  const site = window.site_name && !window.site_name.includes('{{') ? window.site_name : hostname
  let timer: ReturnType<typeof setTimeout>
  const socket = io(`${host}/${site}`, { withCredentials: true })
  socket.on('crecheconnect_poll', (payload) => (state.activity = payload))
  socket.on('crecheconnect_activity', (payload) => {
    clearTimeout(timer)
    timer = setTimeout(() => {
      state.activity = payload
      loadThreads('refresh')
      loadCounts()
    }, 300)
  })
}

export const fetchThread = latest((id: string) => get('creche_connect.api.get_thread', { name: id }))
export async function logout() {
  await call('logout')
  window.location.href = '/login?redirect-to=/c'
}

export const searchThreads = latest((params) => post('creche_connect.search.search', params))
export const fetchOlderReplies = (id: string, before: string) => get('creche_connect.api.get_replies', { thread: id, before })

export async function markRead(t) {
  await post('creche_connect.api.mark_read', { name: t.id })
  if (t.unread) loadCounts()
  const row = feedRow(t.id)
  for (const x of [t, row]) if (x) x.unread = false
  if (t.authorId !== state.me.id && !t.seenBy.includes(state.me.id)) {
    t.seenBy.push(state.me.id)
    if (row) row.seenCount += 1
  }
}

export async function createThread({ title, body, geo, tags, policy, ackRequired, poll }) {
  const res: any = await post('creche_connect.api.create_thread', {
    title,
    content: body,
    places: geo.places,
    designations: geo.designations,
    tags,
    reply_policy: policy,
    ack_required: ackRequired,
    poll_options: poll?.options,
    poll_multiple: poll?.multiple,
    poll_anonymous: poll?.anonymous,
    poll_closes_at: poll?.closesAt,
  })
  for (const t of res.tags) if (!tagById(t.name)) state.tags.push(shapeTag(t))
  loadThreads('refresh')
  loadCounts()
  return res.name
}

export async function addReply(t, body: string) {
  const reply: any = await post('creche_connect.api.add_reply', { thread: t.id, content: body })
  t.replies.push(reply)
  for (const x of [t, feedRow(t.id)]) if (x) Object.assign(x, { replyCount: x.replyCount + 1, lastActivity: reply.at, unread: false })
}

export const isAuthor = (authorId: string) => authorId === state.me.id
export const canDelete = (authorId: string) => isAuthor(authorId) || state.me.admin

export async function updateMessage(target, doctype: 'CrecheConnect Thread' | 'CrecheConnect Reply', body: string, title?: string) {
  const res: any = await post('creche_connect.api.update_message', { doctype, name: target.id, content: body, title })
  Object.assign(target, { body: res.body, editedAt: res.editedAt })
  if (doctype === 'CrecheConnect Thread') for (const x of [target, feedRow(target.id)]) if (x) Object.assign(x, res)
}

export const fetchEditHistory = (doctype: 'CrecheConnect Thread' | 'CrecheConnect Reply', name: string) =>
  get('creche_connect.api.get_edit_history', { doctype, name })

export async function deleteReply(t, reply) {
  await post('creche_connect.api.delete_message', { doctype: 'CrecheConnect Reply', name: reply.id })
  t.replies = t.replies.filter((r) => r.id !== reply.id)
  for (const x of [t, feedRow(t.id)]) if (x) x.replyCount -= 1
}

export async function deleteThread(t) {
  await post('creche_connect.api.delete_message', { doctype: 'CrecheConnect Thread', name: t.id })
  state.threads = state.threads.filter((x) => x.id !== t.id)
}

export async function acknowledge(t) {
  await post('creche_connect.api.acknowledge', { thread: t.id })
  loadCounts()
  for (const x of [t, feedRow(t.id)]) if (x) Object.assign(x, { needsAck: false, acks: [...x.acks, state.me.id] })
}

export async function toggleReaction(target, emoji: string, doctype: 'CrecheConnect Thread' | 'CrecheConnect Reply') {
  const flip = () => {
    const next = toggleIn(target.reactions[emoji] ?? [], state.me.id)
    if (next.length) target.reactions[emoji] = next
    else delete target.reactions[emoji]
  }
  flip()
  try {
    await post('creche_connect.api.toggle_reaction', { doctype, name: target.id, emoji })
  } catch (e) {
    flip()
    throw e
  }
}

function applyVote(poll, optionId: string) {
  const target = poll.options.find((o) => o.id === optionId)
  const on = !target.mine
  for (const o of poll.options) {
    const pick = o === target ? on : poll.multiple && o.mine
    if (pick === o.mine) continue
    o.mine = pick
    o.count += pick ? 1 : -1
    if (!poll.anonymous) o.voters = toggleIn(o.voters, state.me.id)
  }
  const voted = poll.options.some((o) => o.mine)
  if (voted !== poll.voted) poll.voterCount += voted ? 1 : -1
  poll.voted = voted
}

export async function vote(t, optionId: string) {
  const targets = [t, feedRow(t.id)].filter((x) => x?.poll)
  const before = targets.map((x) => JSON.parse(JSON.stringify(x.poll)))
  for (const x of targets) applyVote(x.poll, optionId)
  try {
    await post('creche_connect.api.vote', { thread: t.id, option: optionId })
  } catch (e) {
    targets.forEach((x, i) => (x.poll = before[i]))
    throw e
  }
}

export async function closePoll(t) {
  const res: any = await post('creche_connect.api.close_poll', { thread: t.id })
  for (const x of [t, feedRow(t.id)]) if (x?.poll) Object.assign(x.poll, { closed: true, closesAt: res.closesAt })
}

export const remindPoll = (t) => post('creche_connect.api.remind_poll', { thread: t.id })

export const placeFrom = (s: string, district: string, block: string) => block || district || s || ''

export async function saveUser(form) {
  const user = shapeUser(
    await post('creche_connect.api.save_member', {
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

export const RESOURCE_KINDS = {
  Video: { label: 'Video', icon: 'lucide-circle-play', color: 'red' },
  Course: { label: 'Course', icon: 'lucide-graduation-cap', color: 'violet' },
  Document: { label: 'Document', icon: 'lucide-file-text', color: 'blue' },
  Link: { label: 'Link', icon: 'lucide-link', color: 'green' },
}

export async function addResource({ title, kind, url, description }) {
  const doc: any = await post('frappe.client.insert', {
    doc: { doctype: 'CrecheConnect Resource', title, kind, url, description },
  })
  state.resources.push({ ...doc, id: doc.name, pinned: !!doc.pinned })
}

export async function updateResource(r, { title, kind, url, description }) {
  await post('frappe.client.set_value', { doctype: 'CrecheConnect Resource', name: r.id, fieldname: { title, kind, url, description } })
  Object.assign(r, { title, kind, url, description })
}

export async function deleteResource(r) {
  await post('frappe.client.delete', { doctype: 'CrecheConnect Resource', name: r.id })
  state.resources = state.resources.filter((x) => x.id !== r.id)
}

export async function setPinned(r, pinned: boolean) {
  r.pinned = pinned
  await post('frappe.client.set_value', { doctype: 'CrecheConnect Resource', name: r.id, fieldname: 'pinned', value: pinned ? 1 : 0 })
}
