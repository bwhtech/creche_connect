<script setup lang="ts">
import { computed } from 'vue'
import { Avatar, Tooltip } from 'frappe-ui'
import Reactions from './Reactions.vue'
import { userById, when } from '../lib/store'

const props = defineProps<{ message: any; compact?: boolean }>()
const author = computed(() => userById(props.message.authorId))
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
      <div class="rich mt-0.5 text-p-base text-ink-gray-8" v-html="message.body" />
      <!-- With no reactions yet, the add button only shows on hover. -->
      <div
        class="mt-1.5"
        :class="Object.keys(message.reactions).length ? '' : 'h-0 overflow-hidden group-hover:h-auto group-hover:overflow-visible focus-within:h-auto'"
      >
        <Reactions :target="message" doctype="Samvaad Reply" />
      </div>
    </div>
  </div>
</template>
