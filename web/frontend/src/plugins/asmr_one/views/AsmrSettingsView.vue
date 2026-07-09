<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowLeft, Save, Loader2 } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { useToast } from '@/components/ui/toast/use-toast'
import { getSettings, updateSettings } from '../api'

const router = useRouter()
const toast = useToast()

const form = ref({
  proxy_url: '',
  verify_ssl: true,
  subdir: '',
  default_watch_dir_id: ''
})
const loading = ref(false)
const saving = ref(false)

async function load() {
  loading.value = true
  try {
    const data = await getSettings()
    form.value = {
      proxy_url: data.proxy_url ?? '',
      verify_ssl: data.verify_ssl !== 'false' && data.verify_ssl !== '0',
      subdir: data.subdir ?? '',
      default_watch_dir_id: data.default_watch_dir_id ?? ''
    }
  } catch (e) {
    toast.error('加载失败', e?.response?.data?.detail || e.message)
  } finally {
    loading.value = false
  }
}

async function save() {
  saving.value = true
  try {
    await updateSettings({
      ...form.value,
      verify_ssl: form.value.verify_ssl ? 'true' : 'false'
    })
    toast.success('设置已保存')
  } catch (e) {
    toast.error('保存失败', e?.response?.data?.detail || e.message)
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="flex h-full flex-col gap-4">
    <div class="flex items-center gap-3">
      <Button variant="ghost" size="sm" @click="router.push('/asmr')">
        <ArrowLeft class="h-4 w-4" />
        返回
      </Button>
      <h2 class="text-lg font-semibold">ASMR 设置</h2>
    </div>

    <div v-if="loading" class="flex items-center justify-center py-12 text-muted-foreground">
      <Loader2 class="mr-2 h-5 w-5 animate-spin" />
      加载中...
    </div>

    <div v-else class="max-w-xl rounded-lg border border-border bg-card/40 p-5 flex flex-col gap-4">
      <div class="flex flex-col gap-1.5">
        <Label>代理地址</Label>
        <Input v-model="form.proxy_url" placeholder="http://127.0.0.1:7897" />
        <p class="text-xs text-muted-foreground">
          访问 asmr.one 时使用的 HTTP 代理。留空则不使用代理。
        </p>
      </div>

      <div class="flex items-center justify-between gap-3">
        <div class="flex flex-col gap-1">
          <Label>验证 SSL 证书</Label>
          <p class="text-xs text-muted-foreground">
            通过代理访问时如遇 SSL 错误（如 SSLEOFError），可关闭此选项。
          </p>
        </div>
        <Switch v-model:checked="form.verify_ssl" />
      </div>

      <div class="flex flex-col gap-1.5">
        <Label>下载子目录</Label>
        <Input v-model="form.subdir" placeholder="ASMR" />
        <p class="text-xs text-muted-foreground">
          文件将下载到 <code>{watch_dir}/{子目录}/{作品名}/{文件路径}</code>。
          留空表示直接放在 watch_dir 根下。
        </p>
      </div>

      <div class="flex justify-end">
        <Button variant="gold" :disabled="saving" @click="save">
          <Loader2 v-if="saving" class="h-4 w-4 animate-spin" />
          <Save v-else class="h-4 w-4" />
          保存
        </Button>
      </div>
    </div>
  </div>
</template>
