<script setup>
import { ref, watch, computed } from 'vue'
import { useToast } from '@/components/ui/toast/use-toast'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription
} from '@/components/ui/dialog'
import { Loader2, Check, ImageOff } from 'lucide-vue-next'
import { coverUrl, applyCover } from '../plugins/asmr_one/api'

const props = defineProps({
  open: { type: Boolean, default: false },
  taskId: { type: [Number, String], default: null },
  workId: { type: [Number, String], required: true }
})
const emit = defineEmits(['update:open', 'applied'])

const toast = useToast()
const selected = ref('main')
const applying = ref(false)

// asmr.one 提供三种封面尺寸
const candidates = computed(() => [
  { type: 'main', label: '主封面', desc: '原始尺寸' },
  { type: 'sam', label: '小图', desc: '缩略图' },
  { type: '240x240', label: '240x240', desc: '正方形' }
])

// 用时间戳避免缓存
const coverSrc = (type) => `${coverUrl(props.workId, type)}?_t=${Date.now()}`

// 图片加载失败时显示占位
const erroredTypes = ref(new Set())
const onError = (type) => erroredTypes.value.add(type)
watch(() => props.open, (v) => {
  if (v) {
    selected.value = 'main'
    erroredTypes.value = new Set()
  }
})

async function onConfirm() {
  if (!props.taskId) {
    emit('update:open', false)
    return
  }
  applying.value = true
  try {
    const res = await applyCover(props.taskId, selected.value)
    if (res.cover_applied) {
      toast.success('封面已应用')
    } else {
      toast.warning('封面未写入（可能没有音频文件或获取失败）')
    }
    emit('applied', res)
    emit('update:open', false)
  } catch (e) {
    toast.error('应用封面失败', e?.response?.data?.detail || e.message)
  } finally {
    applying.value = false
  }
}
</script>

<template>
  <Dialog :open="open" @update:open="(v) => emit('update:open', v)">
    <DialogContent class="sm:max-w-[640px]">
      <DialogHeader>
        <DialogTitle>选择封面</DialogTitle>
        <DialogDescription>
          选中的封面会嵌入到本次下载的所有音频文件中。可在下载完成后随时更换。
        </DialogDescription>
      </DialogHeader>

      <div class="grid grid-cols-3 gap-3 py-2">
        <button
          v-for="c in candidates"
          :key="c.type"
          type="button"
          class="relative flex flex-col items-center gap-2 rounded-lg border-2 p-3 transition-colors"
          :class="selected === c.type
            ? 'border-primary bg-accent'
            : 'border-border hover:bg-accent/50'"
          @click="selected = c.type"
        >
          <div class="aspect-square w-full overflow-hidden rounded bg-muted flex items-center justify-center">
            <img
              v-if="!erroredTypes.has(c.type)"
              :src="coverSrc(c.type)"
              :alt="c.label"
              class="h-full w-full object-contain"
              loading="lazy"
              @error="onError(c.type)"
            />
            <ImageOff v-else class="h-8 w-8 text-muted-foreground" />
          </div>
          <div class="text-center">
            <div class="text-sm font-medium">{{ c.label }}</div>
            <div class="text-xs text-muted-foreground">{{ c.desc }}</div>
          </div>
          <div
            v-if="selected === c.type"
            class="absolute right-2 top-2 rounded-full bg-primary text-primary-foreground p-0.5"
          >
            <Check class="h-3 w-3" />
          </div>
        </button>
      </div>

      <DialogFooter>
        <Button variant="outline" @click="emit('update:open', false)" :disabled="applying">
          取消
        </Button>
        <Button @click="onConfirm" :disabled="applying || !taskId">
          <Loader2 v-if="applying" class="h-4 w-4 animate-spin mr-1" />
          应用封面
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>
