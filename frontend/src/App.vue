<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { RouterView, useRoute } from 'vue-router'
import { DesktopShell, Sidebar, SidebarHeader, SidebarItem, ScrollArea, Button, Avatar, LoadingIndicator } from 'frappe-ui'
import { state, loadBoot, loadThreads, listenForActivity, useMe, canStart, RESOURCE_KINDS } from './lib/store'

const me = useMe()
onMounted(() => {
  loadBoot()
  loadThreads().catch(() => {})
  listenForActivity()
})
const route = useRoute()

const isActive = (to: string) => {
  const [path, qs] = to.split('?')
  if (path !== route.path) return false
  return path !== '/' || (new URLSearchParams(qs).get('filter') ?? '') === ((route.query.filter as string) ?? '')
}

const unreadCount = computed(() => state.threads.filter((t) => t.unread).length)
const ackCount = computed(() => state.threads.filter((t) => t.needsAck).length)
const pinned = computed(() => state.resources.filter((r) => r.pinned))

const mainNav = computed(() => [
  { label: 'Feed', icon: 'lucide-rss', to: '/' },
  { label: 'Unread', icon: 'lucide-circle-dot', to: '/?filter=unread', count: unreadCount.value },
  { label: 'To acknowledge', icon: 'lucide-badge-check', to: '/?filter=ack', count: ackCount.value },
  ...(canStart(me.value) ? [{ label: 'Started by me', icon: 'lucide-send', to: '/?filter=mine' }] : []),
])
const openResource = (url: string) => window.open(url, '_blank', 'noopener')
</script>

<template>
  <div class="h-screen w-full bg-surface-base text-ink-gray-9">
    <div v-if="!state.ready" class="flex h-full flex-col items-center justify-center gap-3 text-center">
      <template v-if="state.error">
        <span class="lucide-lock size-6 text-ink-gray-5" aria-hidden="true" />
        <p class="max-w-sm text-p-sm text-ink-gray-7">{{ state.error }}</p>
      </template>
      <LoadingIndicator v-else class="size-5 text-ink-gray-5" />
    </div>
    <DesktopShell v-else>
      <template #sidebar>
        <Sidebar width="14rem" class="border-r">
          <SidebarHeader title="Samvaad" />
          <ScrollArea class="min-h-0 flex-1" viewport-class="px-2 pt-0.5 pb-10">
            <div class="space-y-0.5">
              <SidebarItem v-for="n in mainNav" :key="n.to" :label="n.label" :icon="n.icon" :route="n.to" :active="isActive(n.to)">
                <template v-if="n.count" #suffix>
                  <span class="text-xs text-ink-gray-5 tabular-nums">{{ n.count }}</span>
                </template>
              </SidebarItem>
            </div>

            <template v-if="pinned.length">
              <div class="flex items-center px-2 pt-6 pb-1.5">
                <span class="text-sm text-ink-gray-5">Program resources</span>
                <Button class="ml-auto" size="sm" variant="ghost" icon="lucide-ellipsis" aria-label="All resources" route="/resources" />
              </div>
              <div class="space-y-0.5">
                <SidebarItem
                  v-for="r in pinned"
                  :key="r.id"
                  :label="r.title"
                  :icon="RESOURCE_KINDS[r.kind].icon"
                  @click="openResource(r.url)"
                >
                  <template #suffix>
                    <span class="lucide-arrow-up-right size-3 text-ink-gray-4" aria-hidden="true" />
                  </template>
                </SidebarItem>
              </div>
            </template>

            <div class="px-2 pt-6 pb-1.5 text-sm text-ink-gray-5">Directory</div>
            <div class="space-y-0.5">
              <SidebarItem v-if="me.admin" label="Insights" icon="lucide-chart-column" route="/insights" />
              <SidebarItem label="Users" icon="lucide-users" route="/users" />
              <SidebarItem label="Resources" icon="lucide-library" route="/resources" />
            </div>
          </ScrollArea>
          <div class="flex items-center gap-2 border-t border-outline-gray-1 p-3">
            <Avatar :label="me.name" size="md" />
            <div class="min-w-0">
              <div class="truncate text-sm text-ink-gray-8">{{ me.name }}</div>
              <div class="truncate text-xs text-ink-gray-5">{{ me.admin ? 'Admin · ' : '' }}{{ me.title }}</div>
            </div>
          </div>
        </Sidebar>
      </template>
      <RouterView />
    </DesktopShell>
  </div>
</template>
