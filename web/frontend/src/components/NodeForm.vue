<script setup>
import { ref, reactive, watch } from 'vue'
import { login as apiLogin } from '../api/node'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter
} from '@/components/ui/dialog'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { useToast } from '@/components/ui/toast/use-toast'
import { Eye, EyeOff, Loader2 } from 'lucide-vue-next'

const props = defineProps({
  // 编辑模式时传入已有节点；新增时为 null
  node: { type: Object, default: null },
  // 新增模式的预填充数据（如快速添加本地节点），不触发编辑态
  preset: { type: Object, default: null },
  visible: { type: Boolean, default: false }
})

const emit = defineEmits(['update:visible', 'saved'])

const toast = useToast()
const testing = ref(false)
const showPassword = ref(false)

const form = reactive({
  name: '',
  baseUrl: '',
  username: '',
  password: ''
})

const errors = reactive({})

// 监听 visible/node/preset 变化，填充表单
watch(
  () => [props.visible, props.node, props.preset],
  ([vis, node, preset]) => {
    if (vis) {
      if (node) {
        // 编辑已有节点
        form.name = node.name || ''
        form.baseUrl = node.baseUrl || ''
        form.username = node.username || ''
        form.password = node.password || ''
      } else if (preset) {
        // 预填充（如快速添加本地节点）
        form.name = preset.name || ''
        form.baseUrl = preset.baseUrl || ''
        form.username = preset.username || ''
        form.password = preset.password || ''
      } else {
        // 空白新增
        form.name = ''
        form.baseUrl = 'http://127.0.0.1:8000'
        form.username = ''
        form.password = ''
      }
      Object.keys(errors).forEach((k) => delete errors[k])
    }
  },
  { immediate: true }
)

function close() {
  emit('update:visible', false)
}

function validate() {
  Object.keys(errors).forEach((k) => delete errors[k])
  if (!form.name) errors.name = '请输入节点名称'
  if (!form.baseUrl) errors.baseUrl = '请输入 baseUrl'
  else if (!/^(https?:\/\/.+|\/.+)/.test(form.baseUrl))
    errors.baseUrl = '请输入完整 URL（如 http://127.0.0.1:8000）或相对路径（如 /local_node）'
  if (!form.username) errors.username = '请输入用户名'
  if (!form.password) errors.password = '请输入密码'
  return Object.keys(errors).length === 0
}

// 保存即登录：用账号密码调 /api/auth/login 拿 token，连同配置一起返回
async function onSubmit() {
  if (!validate()) return
  testing.value = true
  try {
    const data = await apiLogin(
      { baseUrl: form.baseUrl.replace(/\/$/, '') },
      { username: form.username, password: form.password }
    )
    const token = data.access_token || data.token || ''
    const userInfo = data.user || data.userInfo || null
    if (!token) {
      toast.error('登录未返回 token')
      return
    }
    toast.success('登录成功')
    emit('saved', {
      id: props.node?.id,
      name: form.name,
      baseUrl: form.baseUrl.replace(/\/$/, ''),
      username: form.username,
      password: form.password,
      token,
      userInfo
    })
    close()
  } catch (e) {
    toast.error('登录失败', e.response?.data?.detail || e.message)
  } finally {
    testing.value = false
  }
}
</script>

<template>
  <Dialog :open="visible" @update:open="(v) => !v && close()">
    <DialogContent class="max-w-md">
      <DialogHeader>
        <DialogTitle>
          {{ node ? '编辑节点（保存会重新登录）' : '添加节点（保存即登录）' }}
        </DialogTitle>
        <DialogDescription>
          填写节点连接信息，保存时会用账号密码登录该节点。
        </DialogDescription>
      </DialogHeader>

      <div class="space-y-4">
        <div class="space-y-2">
          <Label for="nf-name">节点名称</Label>
          <Input
            id="nf-name"
            v-model="form.name"
            placeholder="如：本地节点"
            class="bg-secondary/60"
          />
          <p v-if="errors.name" class="text-xs text-destructive">{{ errors.name }}</p>
        </div>

        <div class="space-y-2">
          <Label for="nf-url">Base URL</Label>
          <Input
            id="nf-url"
            v-model="form.baseUrl"
            placeholder="http://127.0.0.1:8000"
            class="bg-secondary/60"
          />
          <p v-if="errors.baseUrl" class="text-xs text-destructive">{{ errors.baseUrl }}</p>
        </div>

        <div class="space-y-2">
          <Label for="nf-user">用户名</Label>
          <Input id="nf-user" v-model="form.username" class="bg-secondary/60" />
          <p v-if="errors.username" class="text-xs text-destructive">{{ errors.username }}</p>
        </div>

        <div class="space-y-2">
          <Label for="nf-pwd">密码</Label>
          <div class="relative">
            <Input
              id="nf-pwd"
              v-model="form.password"
              :type="showPassword ? 'text' : 'password'"
              class="bg-secondary/60 pr-10"
            />
            <button
              type="button"
              class="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground transition-colors hover:text-foreground"
              @click="showPassword = !showPassword"
            >
              <Eye v-if="!showPassword" class="h-4 w-4" />
              <EyeOff v-else class="h-4 w-4" />
            </button>
          </div>
          <p v-if="errors.password" class="text-xs text-destructive">{{ errors.password }}</p>
        </div>

        <Alert class="border-primary/30 bg-primary/5">
          <AlertDescription class="text-muted-foreground">
            保存时会用账号密码登录该节点，登录成功后节点内容才会出现在工作台。
          </AlertDescription>
        </Alert>
      </div>

      <DialogFooter class="gap-2">
        <Button variant="ghost" @click="close">取消</Button>
        <Button variant="gold" :disabled="testing" @click="onSubmit">
          <Loader2 v-if="testing" class="h-4 w-4 animate-spin" />
          登录并保存
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>
