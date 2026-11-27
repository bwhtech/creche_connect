<script setup lang="ts">
import { Button } from 'frappe-ui'
import StatusPage from '../components/StatusPage.vue'
</script>

<template>
  <StatusPage icon="lucide-compass" :title="__('Page not found')" :text="__('This link doesn’t lead anywhere in CrecheConnect. It may be mistyped or out of date.')">
    <Button :label="__('Back to feed')" route="/" class="mt-2" />
  </StatusPage>
</template>
