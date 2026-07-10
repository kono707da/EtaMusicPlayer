<script setup>
import { ref, onMounted } from 'vue'
import { Save, Loader2 } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useToast } from '@/components/ui/toast/use-toast'
import { getSettings, updateSettings } from '../api'

const toast = useToast()

const form = ref({
  proxy_url: '',
  sessdata: '',
  cache_pool_size_mb: '500'
})
const loading = ref(false)
const saving = ref(false)

async function load() {
  loading.value = true
  try {
    const data = await getSettings()
    form.value = {
      proxy_url: data.proxy_url ?? '',
      sessdata: data.sessdata ?? '',
      cache_pool_size_mb: data.cache_pool_size_mb ?? '500'
    }
  } catch (e) {
    toast.error('加载失败', e?.response?.data?.detail || e.message, e)
  } finally {
    loading.value = false
  }
}

async function save() {
  saving.value = true
  try {
    const updates = [
      { key: 'proxy_url', value: form.value.proxy_url },
      { key: 'sessdata', value: form.value.sessdata },
      { key: 'cache_pool_size_mb', value: form.value.cache_pool_size_mb }
    ]
    await updateSettings(updates)
    toast.success('设置已保存')
  } catch (e) {
    toast.error('保存失败', e?.response?.data?.detail || e.message, e)
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="max-w-2xl mx-auto p-6 space-y-6">
    <h1 class="text-2xl font-bold">B站音频设置</h1>

    <div v-if="loading" class="flex items-center gap-2 text-muted-foreground">
      <Loader2 class="w-4 h-4 animate-spin" /> 加载中...
    </div>

    <div v-else class="space-y-4">
      <div class="space-y-2">
        <Label>代理地址</Label>
        <Input v-model="form.proxy_url" placeholder="http://127.0.0.1:7897（留空则不使用代理）" />
        <p class="text-xs text-muted-foreground">访问B站API时使用的HTTP代理</p>
      </div>

      <div class="space-y-2">
        <Label>SESSDATA Cookie</Label>
        <Input v-model="form.sessdata" type="password" placeholder="B站登录Cookie（可选）" />
        <p class="text-xs text-muted-foreground">
          部分视频需要登录才能获取音频流。从浏览器Cookie中复制SESSDATA值。
        </p>
      </div>

      <div class="space-y-2">
        <Label>缓存池大小（MB）</Label>
        <Input v-model="form.cache_pool_size_mb" type="number" placeholder="500" />
        <p class="text-xs text-muted-foreground">
          远程节点下载时，访问端缓存的临时文件最大大小（MB）。超过此大小会暂停下载并上传已有文件。
        </p>
      </div>

      <Button @click="save" :disabled="saving">
        <Save v-if="!saving" class="w-4 h-4 mr-2" />
        <Loader2 v-else class="w-4 h-4 mr-2 animate-spin" />
        保存设置
      </Button>
    </div>
  </div>
</template>
