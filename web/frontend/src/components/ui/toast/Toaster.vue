<script setup>
import { useToast } from './use-toast'
import Toast from './Toast.vue'

const { toasts, remove } = useToast()
</script>

<template>
  <div
    class="fixed top-4 right-4 z-[100] flex flex-col gap-2 pointer-events-none"
  >
    <div
      v-for="t in toasts"
      :key="t.id"
      class="pointer-events-auto"
    >
      <Toast
        :type="t.type"
        :title="t.title"
        :description="t.description"
        @close="remove(t.id)"
      />
    </div>
  </div>
</template>
