<script setup>
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  Search, User, Library, ListMusic, Settings, RefreshCw,
  Wand2, Copy, TrendingUp, Network, Users, ChevronDown, ChevronRight, Package
} from 'lucide-vue-next'
import PlaylistTree from './components/PlaylistTree.vue'
import PlayerBar from './components/PlayerBar.vue'
import ConfirmDialog from './components/ConfirmDialog.vue'
import { Toaster } from '@/components/ui/toast'
import { useToast } from '@/components/ui/toast/use-toast'
import { useConfirm } from '@/composables/use-confirm'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem } from '@/components/ui/dropdown-menu'
import { useNodesStore } from './stores/nodes'
import { useLibraryStore } from './stores/library'
import { usePluginsStore } from './stores/plugins'
import { getPluginNavItems } from './plugins'

const router = useRouter()
const route = useRoute()
const nodesStore = useNodesStore()
const libraryStore = useLibraryStore()
const pluginsStore = usePluginsStore()
const toast = useToast()
const { confirm } = useConfirm()

// 已登录节点数（用于顶部静态指示器）
const loggedInCount = computed(() => nodesStore.loggedInNodes.length)
const hasLoggedInNode = computed(() => loggedInCount.value > 0)

// 任一已登录节点是 admin 则显示管理功能入口
const isAdmin = computed(() =>
  nodesStore.loggedInNodes.some((n) => n.userInfo?.is_admin)
)

const searchKeyword = computed({
  get: () => libraryStore.keyword,
  set: (v) => (libraryStore.keyword = v || '')
})

// 核心导航（始终显示）
const coreNavItems = [
  { path: '/library', label: '工作台', icon: Library },
  { path: '/playlists', label: '播放列表', icon: ListMusic },
  { path: '/nodes', label: '节点设置', icon: Settings },
  { path: '/plugins', label: '插件管理', icon: Package }
]

// 插件贡献的导航项（按已启用插件动态聚合）
const pluginNavItems = computed(() =>
  getPluginNavItems(pluginsStore.enabledNames)
)

// 合并后的完整导航
const navItems = computed(() => [...coreNavItems, ...pluginNavItems.value])

// 可折叠分组：记录展开的组 label 集合
// 默认：当前路由命中某组的子项时自动展开
const collapsedGroups = ref(new Set())

function isGroupExpanded(item) {
  // 命中子项时强制展开
  if (item.children?.some((c) => currentPath.value === c.path || currentPath.value.startsWith(c.path + '/'))) {
    return true
  }
  return !collapsedGroups.value.has(item.label)
}

function toggleGroup(item) {
  const next = new Set(collapsedGroups.value)
  if (isGroupExpanded(item) && !item.children.some((c) => currentPath.value === c.path)) {
    next.add(item.label)
  } else {
    next.delete(item.label)
  }
  collapsedGroups.value = next
}

// 管理功能
const adminNavItems = [
  { path: '/admin/scan', label: '扫描管理', icon: RefreshCw },
  { path: '/admin/metadata', label: '元数据编辑', icon: Wand2 },
  { path: '/admin/dedup', label: '去重检测', icon: Copy },
  { path: '/admin/quality', label: '音质升级', icon: TrendingUp },
  { path: '/admin/permissions', label: '播放列表授权', icon: Network },
  { path: '/admin/users', label: '用户管理', icon: Users }
]

const currentPath = computed(() => route.path)
const showTree = computed(() =>
  currentPath.value === '/library' || currentPath.value === '/playlists'
)

async function onSearch() {
  if (!searchKeyword.value.trim()) return
  try {
    await libraryStore.globalSearch(searchKeyword.value.trim())
    router.push('/library')
  } catch (e) {
    toast.error('搜索失败', e.message || String(e))
  }
}

function go(path) {
  router.push(path)
}

// 点击顶部节点指示器：跳转到 /nodes
function goNodes() {
  router.push('/nodes')
}
</script>

<template>
  <div class="flex h-screen flex-col overflow-hidden bg-transparent">
    <!-- 顶部：磨砂玻璃黑 -->
    <header class="glass-dark z-50 flex h-16 shrink-0 items-center gap-4 border-b border-border px-6">
      <!-- Logo：金渐变 mark + 文字 -->
      <div class="flex cursor-pointer items-center gap-2.5 transition-opacity hover:opacity-80" @click="go('/library')">
        <span class="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-gold-400 to-gold-600 text-sm font-bold text-black">
          E
        </span>
        <span class="text-lg font-bold tracking-tight text-gold-gradient">EtaMusic</span>
      </div>

      <!-- 节点连接状态指示器（点击跳转 /nodes） -->
      <button
        class="flex h-9 items-center gap-2 rounded-md border border-border bg-secondary/60 px-3 text-sm transition-colors hover:bg-accent"
        :title="hasLoggedInNode ? `已连接 ${loggedInCount} 个节点` : '未连接任何节点'"
        @click="goNodes"
      >
        <span
          class="inline-block h-2 w-2 rounded-full"
          :class="hasLoggedInNode ? 'bg-green-500' : 'bg-muted-foreground/50'"
        ></span>
        <span class="text-muted-foreground">
          {{ hasLoggedInNode ? `已连接 ${loggedInCount} 个节点` : '未连接节点' }}
        </span>
      </button>

      <!-- 搜索框 -->
      <div class="relative flex-1 max-w-md">
        <Search class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          v-model="searchKeyword"
          placeholder="跨节点搜索曲目、艺术家、专辑..."
          class="h-9 pl-9 bg-secondary/60 border-border"
          @keyup.enter="onSearch"
        />
      </div>

      <!-- 用户菜单 -->
      <div class="ml-auto">
        <DropdownMenu>
          <DropdownMenuTrigger as-child>
            <button class="flex h-9 items-center gap-2 rounded-md px-3 text-sm text-muted-foreground transition-colors hover:bg-accent hover:text-foreground">
              <User class="h-4 w-4" />
              <span>{{ hasLoggedInNode ? '已登录' : '未登录' }}</span>
              <ChevronDown class="h-3.5 w-3.5" />
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" class="min-w-[160px]">
            <DropdownMenuItem @select="goNodes">
              <Network class="mr-2 h-4 w-4" />
              节点设置
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>

    <!-- 主体 -->
    <div class="flex flex-1 overflow-hidden">
      <!-- 侧边栏 -->
      <aside class="flex w-60 shrink-0 flex-col border-r border-border bg-card/40 backdrop-blur-sm p-3">
        <!-- 一级导航 -->
        <nav class="flex flex-col gap-0.5">
          <template v-for="item in navItems" :key="item.path || item.label">
            <!-- 可折叠分组 -->
            <template v-if="item.children">
              <div
                class="nav-item"
                :class="{ 'nav-item-active': item.children.some((c) => currentPath === c.path || currentPath.startsWith(c.path + '/')) }"
                role="button"
                tabindex="0"
                @click="toggleGroup(item)"
                @keydown.enter="toggleGroup(item)"
              >
                <component :is="item.icon" class="h-4 w-4" />
                <span class="flex-1">{{ item.label }}</span>
                <ChevronDown
                  v-if="isGroupExpanded(item)"
                  class="h-3.5 w-3.5 text-muted-foreground"
                />
                <ChevronRight v-else class="h-3.5 w-3.5 text-muted-foreground" />
              </div>
              <div v-show="isGroupExpanded(item)" class="flex flex-col gap-0.5 ml-3 pl-2 border-l border-border/60">
                <div
                  v-for="child in item.children"
                  :key="child.path"
                  class="nav-item"
                  :class="{ 'nav-item-active': currentPath === child.path || (child.path !== '/asmr' && currentPath.startsWith(child.path)) }"
                  role="button"
                  tabindex="0"
                  @click="go(child.path)"
                  @keydown.enter="go(child.path)"
                >
                  <component :is="child.icon" class="h-4 w-4" />
                  <span>{{ child.label }}</span>
                </div>
              </div>
            </template>
            <!-- 普通叶子项 -->
            <div
              v-else
              class="nav-item"
              :class="{ 'nav-item-active': currentPath === item.path }"
              role="button"
              tabindex="0"
              @click="go(item.path)"
              @keydown.enter="go(item.path)"
            >
              <component :is="item.icon" class="h-4 w-4" />
              <span>{{ item.label }}</span>
            </div>
          </template>
        </nav>

        <!-- 管理功能分组 -->
        <template v-if="isAdmin">
          <div class="mt-5 px-3 pb-1.5 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground/70">
            管理功能
          </div>
          <nav class="flex flex-col gap-0.5">
            <div
              v-for="item in adminNavItems"
              :key="item.path"
              class="nav-item"
              :class="{ 'nav-item-active': currentPath === item.path }"
              role="button"
              tabindex="0"
              @click="go(item.path)"
              @keydown.enter="go(item.path)"
            >
              <component :is="item.icon" class="h-4 w-4" />
              <span>{{ item.label }}</span>
            </div>
          </nav>
        </template>

        <!-- 分隔线 -->
        <div v-if="showTree" class="my-3 h-px bg-border"></div>

        <!-- 曲库树 -->
        <div v-if="showTree" class="flex-1 overflow-auto min-h-0">
          <PlaylistTree />
        </div>
      </aside>

      <!-- 主内容 -->
      <main class="flex-1 overflow-auto p-7 bg-transparent">
        <router-view />
      </main>
    </div>

    <!-- 底部播放器 -->
    <footer class="glass-dark z-50 h-[88px] shrink-0 border-t border-border">
      <PlayerBar />
    </footer>

    <!-- 全局弹窗与通知 -->
    <ConfirmDialog />
    <Toaster />
  </div>
</template>
