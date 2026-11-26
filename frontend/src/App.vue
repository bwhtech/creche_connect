<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useOnline } from '@vueuse/core'
import { RouterView, useRoute, useRouter } from 'vue-router'
import { useTitle } from '@vueuse/core'
import { DesktopShell, MobileShell, MobileNav, MobileNavItem, Badge, Sidebar, SidebarHeader, SidebarItem, ScrollArea, Button, Avatar, Dropdown, Skeleton, useColorScheme, toast } from 'frappe-ui'
import StatusPage from './components/StatusPage.vue'
import AvatarPicker from './components/AvatarPicker.vue'
import { state, loadBoot, loadCounts, listenForActivity, useMe, canStart, RESOURCE_KINDS, logout, isMobile, errorText } from './lib/store'
import { pushSupported, pushOn, checkPush, enablePush, disablePush } from './lib/push'

const me = useMe()
onMounted(() => {
  loadBoot()
  loadCounts().catch(() => {})
  listenForActivity()
  checkPush()
})
const online = useOnline()
const offline = { icon: 'lucide-wifi-off', title: "You're offline", text: "Check your mobile data or Wi-Fi. CrecheConnect will carry on from here once you're back online." }
watch(online, (on) => on && !state.ready && loadBoot())
const reload = () => window.location.reload()
const route = useRoute()
const router = useRouter()

const isActive = (to: string) => {
  const [path, qs] = to.split('?')
  if (path !== route.path) return false
  return path !== '/' || (new URLSearchParams(qs).get('filter') ?? '') === ((route.query.filter as string) ?? '')
}

const unreadCount = computed(() => state.counts.unread)
const ackCount = computed(() => state.counts.ack)
useTitle(computed(() => (unreadCount.value ? `(${unreadCount.value}) CrecheConnect` : 'CrecheConnect')))
const pinned = computed(() => state.resources.filter((r) => r.pinned))

const mainNav = computed(() => [
  { label: 'Feed', icon: 'lucide-rss', to: '/' },
  { label: 'Unread', icon: 'lucide-circle-dot', to: '/?filter=unread', count: unreadCount.value },
  { label: 'To acknowledge', icon: 'lucide-badge-check', to: '/?filter=ack', count: ackCount.value },
  { label: 'Mentions', icon: 'lucide-at-sign', to: '/?filter=mentions' },
  ...(canStart(me.value) ? [{ label: 'My posts', icon: 'lucide-send', to: '/?filter=mine' }] : []),
])
const { resolvedColorScheme, toggleColorScheme } = useColorScheme()
const isIOS = /iPhone|iPad/.test(navigator.userAgent)
async function togglePush() {
  if (!pushSupported) return toast.info('On iPhone, add CrecheConnect to your Home Screen first: tap Share, then Add to Home Screen. Open it from there and turn notifications on.', { duration: 10000 })
  try {
    await (pushOn.value ? disablePush() : enablePush())
    toast.success(pushOn.value ? 'Notifications are on for this device' : 'Notifications are off for this device')
  } catch (e) {
    toast.error(errorText(e, e?.message || 'Could not change notifications'))
  }
}
const pickingAvatar = ref(false)
const userMenu = computed(() => [
  { label: me.value.image ? 'Change photo' : 'Add photo', icon: 'lucide-circle-user-round', onClick: () => (pickingAvatar.value = true) },
  ...(pushSupported || isIOS ? [{ label: pushOn.value ? 'Turn off notifications' : 'Turn on notifications', icon: pushOn.value ? 'lucide-bell-off' : 'lucide-bell', onClick: togglePush }] : []),
  resolvedColorScheme.value === 'dark'
    ? { label: 'Light mode', icon: 'lucide-sun', onClick: toggleColorScheme }
    : { label: 'Dark mode', icon: 'lucide-moon', onClick: toggleColorScheme },
  { label: 'Log out', icon: 'lucide-log-out', onClick: logout },
])
const mobileMenu = computed(() => [
  ...(me.value.admin ? [{ label: 'Insights', icon: 'lucide-chart-column', onClick: () => router.push('/insights') }] : []),
  { label: 'Users', icon: 'lucide-users', onClick: () => router.push('/users') },
  ...userMenu.value,
])
const showTabs = computed(() => !/^\/(threads|new)/.test(route.path))
</script>

<template>
  <div class="h-dvh w-full bg-surface-base text-ink-gray-9">
    <StatusPage v-if="!state.ready && (!online || state.unreachable)" v-bind="offline">
      <Button label="Try again" class="mt-2" @click="reload" />
    </StatusPage>
    <div v-else-if="!state.ready" class="flex h-full flex-col items-center justify-center gap-3 text-center">
      <template v-if="state.error">
        <span class="lucide-lock size-6 text-ink-gray-6" aria-hidden="true" />
        <p class="max-w-sm text-p-sm text-ink-gray-7">{{ state.error }}</p>
      </template>
      <div v-else data-testid="app-loading-skeleton" class="flex h-full w-full">
        <aside class="hidden w-56 shrink-0 border-r border-outline-gray-1 p-3 md:block">
          <Skeleton class="h-8 w-36" />
          <div class="mt-8 space-y-2">
            <Skeleton v-for="i in 6" :key="i" class="h-8 w-full" />
          </div>
        </aside>
        <main class="flex-1 p-4 sm:p-6">
          <Skeleton class="h-8 w-32" />
          <div class="mx-auto mt-8 max-w-[860px] space-y-4">
            <div v-for="i in 4" :key="i" class="flex gap-4 rounded-5 border border-outline-gray-1 p-5">
              <Skeleton class="size-8 rounded-full" />
              <div class="flex-1 space-y-2.5">
                <Skeleton class="h-3 w-1/3" />
                <Skeleton class="h-4 w-2/3" />
                <Skeleton class="h-3 w-full" />
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
    <MobileShell v-else-if="isMobile">
      <StatusPage v-if="!online" v-bind="offline" />
      <RouterView v-show="online" :class="!showTabs && 'pb-[env(safe-area-inset-bottom)]'" />
      <template v-if="showTabs" #nav>
        <MobileNav>
          <MobileNavItem label="Feed" route="/" :active="route.path === '/'">
            <template #default="{ active }">
              <span class="relative">
                <span class="lucide-rss block size-6" :class="active ? 'text-ink-gray-8' : 'text-ink-gray-6'" aria-hidden="true" />
                <Badge v-if="unreadCount" class="absolute -top-1.5 left-4" :label="String(unreadCount)" theme="red" variant="solid" size="sm" />
              </span>
            </template>
          </MobileNavItem>
          <MobileNavItem label="Search" icon="lucide-search" route="/search" :active="route.path === '/search'" />
          <MobileNavItem v-if="canStart(me)" label="New" icon="lucide-square-pen" route="/new" />
          <MobileNavItem label="Resources" icon="lucide-library" route="/resources" :active="route.path === '/resources'" />
          <Dropdown :options="mobileMenu" side="top" align="end">
            <MobileNavItem label="You" :active="['/users', '/insights'].includes(route.path)">
              <Avatar :label="me.name" :image="me.image" size="md" />
            </MobileNavItem>
          </Dropdown>
        </MobileNav>
      </template>
    </MobileShell>
    <DesktopShell v-else :scroll="false">
      <template #sidebar>
        <Sidebar width="14rem" class="border-r">
          <SidebarHeader title="CrecheConnect" logo="/assets/creche_connect/logo.png" />
          <ScrollArea class="min-h-0 flex-1" viewport-class="px-2 pt-0.5 pb-10">
            <div class="space-y-0.5">
              <SidebarItem label="Search" icon="lucide-search" route="/search" :active="route.path === '/search'" />
              <SidebarItem v-for="n in mainNav" :key="n.to" :label="n.label" :icon="n.icon" :route="n.to" :active="isActive(n.to)">
                <template v-if="n.count" #suffix>
                  <span class="text-xs text-ink-gray-6 tabular-nums">{{ n.count }}</span>
                </template>
              </SidebarItem>
            </div>

            <template v-if="pinned.length">
              <div class="flex items-center px-2 pt-6 pb-1.5">
                <span class="text-sm text-ink-gray-6">Program resources</span>
                <Button class="ml-auto" size="sm" variant="ghost" icon="lucide-ellipsis" aria-label="All resources" route="/resources" />
              </div>
              <div class="space-y-0.5">
                <SidebarItem
                  v-for="r in pinned"
                  :key="r.id"
                  :label="r.title"
                  :icon="RESOURCE_KINDS[r.kind].icon"
                  :route="{ path: '/resources', query: { r: r.id } }"
                  :active="route.path === '/resources' && route.query.r === r.id"
                >
                  <template #suffix>
                    <span class="text-xs text-ink-gray-6 tabular-nums">{{ r.files.length }}</span>
                  </template>
                </SidebarItem>
              </div>
            </template>

            <div class="px-2 pt-6 pb-1.5 text-sm text-ink-gray-6">Directory</div>
            <div class="space-y-0.5">
              <SidebarItem v-if="me.admin" label="Insights" icon="lucide-chart-column" route="/insights" />
              <SidebarItem label="Users" icon="lucide-users" route="/users" />
              <SidebarItem label="Resources" icon="lucide-library" route="/resources" />
            </div>
          </ScrollArea>
          <Dropdown :options="userMenu" side="top" align="start">
            <button type="button" class="flex w-full items-center gap-2 border-t border-outline-gray-1 p-3 text-left hover:bg-surface-gray-2">
              <Avatar :label="me.name" :image="me.image" size="md" />
              <div class="min-w-0 flex-1">
                <div class="truncate text-sm text-ink-gray-8">{{ me.name }}</div>
                <div class="truncate text-xs text-ink-gray-6">{{ [me.admin && 'Admin', me.title].filter(Boolean).join(' · ') }}</div>
              </div>
              <span class="lucide-chevrons-up-down size-4 shrink-0 text-ink-gray-6" aria-hidden="true" />
            </button>
          </Dropdown>
        </Sidebar>
      </template>
      <StatusPage v-if="!online" v-bind="offline" />
      <RouterView v-show="online" />
    </DesktopShell>
    <AvatarPicker v-if="state.ready" v-model:open="pickingAvatar" />
  </div>
</template>
