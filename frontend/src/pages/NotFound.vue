<script setup lang="ts">
import { Button } from 'frappe-ui'
import StatusPage from '../components/StatusPage.vue'
</script>

<template>
  <StatusPage icon="lucide-compass" title="Page not found" text="This link doesn't lead anywhere in CrecheConnect. It may be mistyped or out of date.">
    <Button label="Back to feed" route="/" class="mt-2" />
  </StatusPage>
</template>
