<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { Avatar, Badge, Button, Dialog, FormControl, PageHeader, Switch, TextInput, toast } from 'frappe-ui'
import { List, ListHeader, ListHeaderCell, ListRows, ListRow, ListCell } from 'frappe-ui/list'
import { state, useMe, STATES, DESIGNATIONS, districtsOf, blocksOf, placeById, placePath, placeFrom, saveUser, chain, inPlace, errorText } from '../lib/store'

const me = useMe()
const query = ref('')
const stateFilter = ref('')
const stateChoices = computed(() => STATES.value.map((s) => ({ label: s.name, value: s.id })))
const stateOptions = computed(() => [{ label: 'All states', value: '' }, { label: 'National', value: 'national' }, ...stateChoices.value])

const people = computed(() =>
  state.users.map((u) => {
    const levels = chain(u.place).reverse().map((p) => p.name)
    return { ...u, levels, search: `${u.name} ${u.designation} ${levels.join(' ')}`.toLowerCase() }
  }),
)
const rows = computed(() => {
  const s = stateFilter.value
  const q = query.value.toLowerCase()
  return people.value.filter((u) => {
    if (s === 'national' && u.place) return false
    if (s && s !== 'national' && !(u.place && inPlace(u.place, s))) return false
    return u.search.includes(q)
  })
})

const open = ref(false)
const saving = ref(false)
const form = ref(blank())
function blank() {
  return { id: '', email: '', name: '', designation: DESIGNATIONS.value.at(-1) ?? '', state: '', district: '', block: '', canPost: false }
}
function edit(u) {
  const [s, d, b] = chain(u.place).reverse().map((p) => p.id)
  form.value = {
    id: u.id,
    email: u.id,
    name: u.name,
    designation: u.designation,
    state: s ?? '',
    district: d ?? '',
    block: b ?? '',
    canPost: u.canPost,
  }
  open.value = true
}
function add() {
  form.value = blank()
  open.value = true
}
watch(() => form.value.state, (v) => placeById(form.value.district)?.parentId !== v && (form.value.district = '', form.value.block = ''))
watch(() => form.value.district, (v) => placeById(form.value.block)?.parentId !== v && (form.value.block = ''))

const districtOptions = computed(() => [{ label: 'Whole state', value: '' }, ...districtsOf(form.value.state).map((p) => ({ label: p.name, value: p.id }))])
const blockOptions = computed(() => [{ label: 'Whole district', value: '' }, ...blocksOf(form.value.district).map((p) => ({ label: p.name, value: p.id }))])
const formPlace = computed(() => placeFrom(form.value.state, form.value.district, form.value.block))

async function save() {
  if (!form.value.name.trim()) return toast.error('Add a name')
  if (!form.value.email.trim()) return toast.error('Add an email')
  const isNew = !form.value.id
  saving.value = true
  try {
    await saveUser(form.value)
    open.value = false
    toast.success(isNew ? 'User added' : 'User updated')
  } catch (e) {
    toast.error(errorText(e, 'Could not save the user'))
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="flex h-full flex-col">
    <PageHeader>
      <h1 class="text-2xl text-ink-gray-9">Users</h1>
      <div class="ml-auto flex items-center gap-2">
        <div class="w-40">
          <FormControl v-model="stateFilter" type="select" :options="stateOptions" aria-label="Filter by state" />
        </div>
        <div class="w-56">
          <TextInput v-model="query" placeholder="Search users" aria-label="Search users">
            <template #prefix><span class="lucide-search size-4 text-ink-gray-5" aria-hidden="true" /></template>
          </TextInput>
        </div>
        <Button v-if="me.admin" variant="solid" theme="gray" icon-left="lucide-user-plus" label="Add user" @click="add" />
      </div>
    </PageHeader>

    <div class="min-h-0 flex-1 overflow-y-auto">
      <div class="px-3 pt-6 pb-20 sm:px-5">
        <p class="mb-5 text-p-sm text-ink-gray-5">
          Each user has a state, district, block and designation. Threads reach people by these four fields.
          <span class="tabular-nums">{{ rows.length }} of {{ state.users.length }}</span> shown.
        </p>
        <List :columns="['minmax(0,1.4fr)', 'minmax(0,1fr)', 'minmax(0,1fr)', 'minmax(0,1fr)', '8rem', '4rem']" :row-height="56">
          <ListHeader>
            <ListHeaderCell>Name</ListHeaderCell>
            <ListHeaderCell>State</ListHeaderCell>
            <ListHeaderCell>District</ListHeaderCell>
            <ListHeaderCell>Block</ListHeaderCell>
            <ListHeaderCell>Posting</ListHeaderCell>
            <ListHeaderCell />
          </ListHeader>
          <ListRows :items="rows" v-slot="{ item }">
            <ListRow>
              <ListCell>
                <div class="flex min-w-0 items-center gap-3">
                  <Avatar :label="item.name" size="lg" />
                  <div class="min-w-0">
                    <div class="truncate text-base text-ink-gray-8">
                      {{ item.name }}
                      <span v-if="item.admin" class="ml-1 text-xs text-ink-gray-5">Admin</span>
                    </div>
                    <div class="truncate text-xs text-ink-gray-5">{{ item.designation }}</div>
                  </div>
                </div>
              </ListCell>
              <ListCell>
                <span class="truncate text-sm" :class="item.place ? 'text-ink-gray-7' : 'text-ink-gray-5'">{{ item.levels[0] || 'National' }}</span>
              </ListCell>
              <ListCell><span class="truncate text-sm text-ink-gray-7">{{ item.levels[1] || '—' }}</span></ListCell>
              <ListCell><span class="truncate text-sm text-ink-gray-7">{{ item.levels[2] || '—' }}</span></ListCell>
              <ListCell>
                <Badge v-if="item.canPost" label="Can start threads" theme="green" variant="subtle" size="sm" />
                <span v-else class="text-sm text-ink-gray-4">Read and reply</span>
              </ListCell>
              <ListCell class="justify-end">
                <Button v-if="me.admin" size="sm" variant="ghost" icon="lucide-pencil" :aria-label="`Edit ${item.name}`" @click="edit(item)" />
              </ListCell>
            </ListRow>
          </ListRows>
        </List>
        <div v-if="!rows.length" class="flex flex-col items-center gap-2 py-16 text-center">
          <span class="lucide-users size-6 text-ink-gray-4" aria-hidden="true" />
          <p class="text-sm text-ink-gray-5">No users match.</p>
        </div>
      </div>
    </div>

    <Dialog v-model:open="open" :title="form.id ? 'Edit user' : 'Add user'">
      <div class="space-y-5">
        <FormControl v-model="form.name" label="Full name" required />
        <FormControl v-model="form.email" type="email" label="Email" required :disabled="!!form.id" />
        <FormControl v-model="form.designation" type="select" label="Designation" :options="DESIGNATIONS.map((d) => ({ label: d, value: d }))" />

        <div class="rounded-5 border border-outline-gray-1 p-4">
          <div class="mb-3 flex items-center gap-1.5 text-sm text-ink-gray-6">
            <span class="lucide-map-pin size-3.5" aria-hidden="true" />Location
          </div>
          <div class="grid gap-3 sm:grid-cols-3">
            <FormControl
              v-model="form.state"
              type="select"
              label="State"
              :options="[{ label: 'None (national)', value: '' }, ...stateChoices]"
            />
            <FormControl v-model="form.district" type="select" label="District" :options="districtOptions" :disabled="!form.state" />
            <FormControl v-model="form.block" type="select" label="Block" :options="blockOptions" :disabled="!form.district" />
          </div>
          <p class="mt-3 text-p-xs text-ink-gray-5">{{ placePath(formPlace) }}</p>
        </div>

        <Switch
          v-model="form.canPost"
          label="Can start threads"
          :description="`They can post to people in ${formPlace ? placePath(formPlace) : 'all of India'} and below.`"
        />

        <div class="flex justify-end gap-2 pt-1">
          <Button label="Cancel" @click="open = false" />
          <Button variant="solid" theme="gray" :label="form.id ? 'Save' : 'Add user'" :loading="saving" @click="save" />
        </div>
      </div>
    </Dialog>
  </div>
</template>
