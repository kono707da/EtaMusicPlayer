<script setup>
import { computed } from 'vue'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { useConfirm } from '@/composables/use-confirm'

const { state, onConfirm, onCancel } = useConfirm()

const confirmText = computed(() => (state.type === 'danger' ? '确认删除' : '确定'))
</script>

<template>
  <Dialog :open="state.open" @update:open="(v) => !v && onCancel()">
    <DialogContent class="max-w-md">
      <DialogHeader>
        <DialogTitle>{{ state.title }}</DialogTitle>
        <DialogDescription>{{ state.message }}</DialogDescription>
      </DialogHeader>
      <DialogFooter class="gap-2">
        <Button variant="ghost" @click="onCancel">取消</Button>
        <Button
          :variant="state.type === 'danger' ? 'destructive' : 'gold'"
          @click="onConfirm"
        >
          {{ confirmText }}
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>
