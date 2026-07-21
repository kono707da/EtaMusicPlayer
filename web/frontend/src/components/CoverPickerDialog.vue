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
import { Loader2, Check, ImageOff, FileImage, Tag, ImagePlus } from 'lucide-vue-next'

const props = defineProps({
  open: { type: Boolean, default: false },
  taskId: { type: [Number, String], default: null },
  workId: { type: [Number, String], required: true },
  // 由调用方（插件）注入的封面 URL 构造函数
  coverUrl: { type: Function, required: true },
  // 由调用方（插件）注入的封面应用函数
  applyCover: { type: Function, required: true }
})
const emit = defineEmits(['update:open', 'applied'])

const toast = useToast()
const selected = ref('main')
const coverMode = ref('save')
const applying = ref(false)

// asmr.one 提供三种封面尺寸
const candidates = computed(() => [
  { type: 'main', label: '主封面', desc: '原始尺寸' },
  { type: 'sam', label: '小图', desc: '缩略图' },
  { type: '240x240', label: '240x240', desc: '正方形' }
])

// 封面应用模式（"单独保存" 排首位，Windows 上最稳定）
const modeOptions = computed(() => [
  {
    value: 'save',
    label: '单独保存 (推荐)',
    desc: '下载 cover.jpg 到音频所在目录，不修改音频文件',
    icon: FileImage
  },
  {
    value: 'embed',
    label: '嵌入文件',
    desc: '嵌入到音频文件标签（APIC/pictures/covr），嵌入失败自动回退保存',
    icon: Tag
  },
  {
    value: 'both',
    label: '保存 + 嵌入',
    desc: '同时保存 cover.jpg 并嵌入到音频文件',
    icon: ImagePlus
  }
])

// 用时间戳避免缓存（注意 coverUrl 已含 ?type=，需用 & 拼接）
const coverSrc = (type) => {
  const base = props.coverUrl(props.workId, type)
  return base.includes('?') ? `${base}&_t=${Date.now()}` : `${base}?_t=${Date.now()}`
}

// 图片加载失败时显示占位
const erroredTypes = ref(new Set())
const onError = (type) => erroredTypes.value.add(type)
watch(() => props.open, (v) => {
  if (v) {
    selected.value = 'main'
    coverMode.value = 'save'
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
    const res = await props.applyCover(props.taskId, selected.value, coverMode.value)
    if (res.cover_applied) {
      const modeLabel = modeOptions.value.find((m) => m.value === coverMode.value)?.label || ''
      toast.success(`封面已应用（${modeLabel}）`)
      // 嵌入模式需要刷新曲库以更新 cover_embedded 字段
      if (coverMode.value === 'embed' || coverMode.value === 'both') {
        // 通知父组件已应用，由父组件决定是否刷新
      }
    } else {
      toast.warning('封面未写入（可能没有音频文件或获取失败）')
    }
    emit('applied', res)
    emit('update:open', false)
  } catch (e) {
    toast.error('应用封面失败', e?.response?.data?.detail || e.message, e)
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
          选择封面图并指定应用方式。可在下载完成后随时更换。
        </DialogDescription>
      </DialogHeader>

      <!-- 封面图选择 -->
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

      <!-- 应用模式选择 -->
      <div class="space-y-2 py-2">
        <div class="text-sm font-medium text-foreground">应用方式</div>
        <div class="grid grid-cols-3 gap-2">
          <button
            v-for="m in modeOptions"
            :key="m.value"
            type="button"
            class="flex flex-col items-start gap-1.5 rounded-lg border-2 p-3 text-left transition-colors"
            :class="coverMode === m.value
              ? 'border-primary bg-accent'
              : 'border-border hover:bg-accent/50'"
            @click="coverMode = m.value"
          >
            <div class="flex items-center gap-1.5">
              <component :is="m.icon" class="h-4 w-4" />
              <span class="text-sm font-medium">{{ m.label }}</span>
            </div>
            <div class="text-xs text-muted-foreground leading-snug">{{ m.desc }}</div>
          </button>
        </div>
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
