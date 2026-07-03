<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { User, LogOut, Loader2, Heart, Star } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { useToast } from '@/components/ui/toast/use-toast'
import { useAsmrAccountStore } from '../store'

const router = useRouter()
const toast = useToast()
const account = useAsmrAccountStore()

const isRegister = ref(false)
const name = ref('')
const password = ref('')
const passwordConfirm = ref('')
const recommenderUuid = ref('')
const submitting = ref(false)

async function submit() {
  if (!name.value || !password.value) {
    toast.warning('请输入用户名和密码')
    return
  }
  if (isRegister.value && password.value !== passwordConfirm.value) {
    toast.warning('两次密码不一致')
    return
  }
  submitting.value = true
  try {
    if (isRegister.value) {
      await account.register(name.value, password.value, recommenderUuid.value || null)
      toast.success('注册成功，已自动登录')
    } else {
      await account.login(name.value, password.value)
      toast.success('登录成功')
    }
    name.value = ''
    password.value = ''
    passwordConfirm.value = ''
    recommenderUuid.value = ''
  } catch (e) {
    const detail = e?.response?.data?.detail || e.message
    toast.error(isRegister.value ? '注册失败' : '登录失败', detail)
  } finally {
    submitting.value = false
  }
}

async function doLogout() {
  await account.logout()
  toast.success('已退出登录')
}

function goReviews() {
  router.push('/asmr/reviews')
}

function goFavorites() {
  router.push('/asmr/favorites')
}

onMounted(() => {
  if (!account.loaded) account.load()
})
</script>

<template>
  <div class="flex h-full flex-col">
    <!-- 顶部标题 -->
    <div class="flex items-center gap-3 mb-4">
      <User class="h-5 w-5 text-primary" />
      <h2 class="text-lg font-semibold">ASMR 账户</h2>
    </div>

    <!-- 内容区：垂直 + 水平居中 -->
    <div class="flex-1 min-h-0 flex items-start justify-center pt-4">
      <!-- 已登录 -->
      <div
        v-if="account.isLoggedIn"
        class="w-full max-w-md rounded-lg border border-border bg-card/40 p-6 flex flex-col gap-5 shadow-sm"
      >
        <div class="flex items-center gap-3">
          <div class="h-14 w-14 rounded-full bg-primary/20 flex items-center justify-center">
            <User class="h-7 w-7 text-primary" />
          </div>
          <div class="flex-1">
            <div class="text-base font-medium text-foreground">{{ account.user?.name || '—' }}</div>
            <div class="text-xs text-muted-foreground mt-0.5">
              ID: {{ account.user?.id || '—' }}
              <Badge v-if="account.user?.role === 1" variant="gold" class="ml-2 text-[10px]">管理员</Badge>
            </div>
          </div>
        </div>

        <div v-if="account.user?.email" class="text-sm text-muted-foreground">
          邮箱：{{ account.user.email }}
        </div>

        <div class="flex gap-2 pt-1">
          <Button variant="gold" size="sm" @click="goFavorites">
            <Heart class="h-4 w-4" />
            我的收藏
          </Button>
          <Button variant="outline" size="sm" @click="goReviews">
            <Star class="h-4 w-4" />
            我的评价
          </Button>
          <Button variant="ghost" size="sm" class="ml-auto text-destructive" @click="doLogout">
            <LogOut class="h-4 w-4" />
            退出登录
          </Button>
        </div>
      </div>

      <!-- 未登录 -->
      <div
        v-else
        class="w-full max-w-md rounded-lg border border-border bg-card/40 p-6 flex flex-col gap-5 shadow-sm"
      >
        <div class="text-center">
          <div class="inline-flex h-12 w-12 rounded-full bg-primary/15 items-center justify-center mb-3">
            <User class="h-6 w-6 text-primary" />
          </div>
          <h3 class="text-lg font-medium text-foreground">
            {{ isRegister ? '注册 ASMR 账户' : '登录 ASMR 账户' }}
          </h3>
          <p class="text-xs text-muted-foreground mt-1">
            登录后可使用收藏、评价、个性化推荐等功能
          </p>
        </div>

        <div class="flex items-center justify-center gap-2">
          <button
            class="text-sm px-4 py-1.5 rounded-md transition-colors"
            :class="!isRegister ? 'bg-primary text-primary-foreground' : 'text-muted-foreground hover:bg-accent'"
            @click="isRegister = false"
          >
            登录
          </button>
          <button
            v-if="account.regEnabled"
            class="text-sm px-4 py-1.5 rounded-md transition-colors"
            :class="isRegister ? 'bg-primary text-primary-foreground' : 'text-muted-foreground hover:bg-accent'"
            @click="isRegister = true"
          >
            注册
          </button>
        </div>

        <div class="flex flex-col gap-3">
          <div class="flex flex-col gap-1.5">
            <Label>用户名</Label>
            <Input v-model="name" placeholder="用户名" class="h-9" @keyup.enter="submit" />
          </div>
          <div class="flex flex-col gap-1.5">
            <Label>密码</Label>
            <Input v-model="password" type="password" placeholder="密码" class="h-9" @keyup.enter="submit" />
          </div>
          <template v-if="isRegister">
            <div class="flex flex-col gap-1.5">
              <Label>确认密码</Label>
              <Input v-model="passwordConfirm" type="password" placeholder="再次输入密码" class="h-9" />
            </div>
            <div class="flex flex-col gap-1.5">
              <Label>推荐人 UUID（可选）</Label>
              <Input v-model="recommenderUuid" placeholder="可选" class="h-9" />
            </div>
          </template>

          <Button variant="gold" :disabled="submitting" class="mt-1" @click="submit">
            <Loader2 v-if="submitting" class="h-4 w-4 animate-spin" />
            {{ isRegister ? '注册并登录' : '登录' }}
          </Button>
        </div>

        <p class="text-xs text-muted-foreground text-center">
          账户信息存储在后端数据库中，用于访问 asmr.one 的收藏/评价/推荐等功能。
        </p>
      </div>
    </div>
  </div>
</template>
