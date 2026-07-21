/**
 * 主应用运行时暴露给插件使用的依赖
 *
 * 插件前端构建时不打包这些依赖，运行时通过 window.__etamusic 取用。
 * 插件代码约定：
 *   const { ref, computed } = window.__etamusic.vue
 *   const { Button, Input } = window.__etamusic.ui
 *   const { usePlayerStore } = window.__etamusic.stores
 *
 * 必须在 app.mount() 之前完成挂载，确保插件加载时可用。
 */
import * as vue from 'vue'
import * as pinia from 'pinia'
import * as vueRouter from 'vue-router'
import axios from 'axios'
import { Howl } from 'howler'

// UI 组件库
import * as alert from '@/components/ui/alert'
import * as badge from '@/components/ui/badge'
import * as button from '@/components/ui/button'
import * as card from '@/components/ui/card'
import * as dialog from '@/components/ui/dialog'
import * as dropdownMenu from '@/components/ui/dropdown-menu'
import * as empty from '@/components/ui/empty'
import * as input from '@/components/ui/input'
import * as label from '@/components/ui/label'
import * as pagination from '@/components/ui/pagination'
import * as select from '@/components/ui/select'
import * as slider from '@/components/ui/slider'
import * as switchModule from '@/components/ui/switch'
import * as table from '@/components/ui/table'
import * as toast from '@/components/ui/toast'

// 共享业务组件（部分插件需要）
import CoverPickerDialog from '@/components/CoverPickerDialog.vue'

// 核心 stores
import { usePlayerStore } from '@/stores/player'
import { useNodesStore } from '@/stores/nodes'
import { usePluginsStore } from '@/stores/plugins'
import { useAuthStore } from '@/stores/auth'
import { useLibraryStore } from '@/stores/library'

// 工具函数
import { cn } from '@/lib/utils'

// 图标库（lucide-vue-next 按需导入常用图标，插件如需其他图标可按需扩展）
import {
  Music, Search, Play, Plus, Pause, SkipForward, SkipBack, X, Loader2,
  AlertCircle, CheckCircle2, RefreshCw, User, ListMusic, Flame, ArrowLeft,
  Clock, Headphones, Download, Settings, Tag, Mic2, Users, Home, Captions,
  QrCode, Trash2, Heart, Star, BookmarkIcon, ChevronDown, ChevronRight,
  ChevronLeft, ChevronUp, MoreVertical, Filter, SortAsc, SortDesc, Folder,
  FolderOpen, File, FileImage, Video, Volume2, VolumeX, Shuffle, Repeat,
  Pencil, Save, Upload, Eye, Shield, Sparkles,
  // asmr_one / bili_audio 插件需要的额外图标
  LogOut, FileAudio, FileText, Check, Square, ExternalLink, HardDrive,
  CheckSquare, XCircle, Ban, Image as ImageIcon, ImageOff, ImagePlus,
  Link, List, CheckCircle
} from 'lucide-vue-next'

// 从 vue 模块解构出插件常用的 API（import * 后变量名访问也行，这里显式列出便于阅读）
const {
  ref, reactive, computed, watch, watchEffect, onMounted, onUnmounted,
  onBeforeMount, onBeforeUnmount, onUpdated, defineComponent, h,
  nextTick, toRef, toRefs, unref, isRef, provide, inject,
  defineAsyncComponent, shallowRef, shallowReactive, readonly
} = vue

const { defineStore, storeToRefs, getActivePinia } = pinia
const { useRouter, useRoute, onBeforeRouteLeave, onBeforeRouteUpdate } = vueRouter

/**
 * 暴露到 window.__etamusic
 */
export function setupRuntime() {
  window.__etamusic = {
    // Vue 运行时
    vue: {
      ref, reactive, computed, watch, watchEffect, onMounted, onUnmounted,
      onBeforeMount, onBeforeUnmount, onUpdated, defineComponent, h,
      nextTick, toRef, toRefs, unref, isRef, provide, inject,
      defineAsyncComponent, shallowRef, shallowReactive, readonly
    },
    // Pinia
    pinia: { defineStore, storeToRefs, getActivePinia },
    // Vue Router
    vueRouter: { useRouter, useRoute, onBeforeRouteLeave, onBeforeRouteUpdate },
    // UI 组件库（扁平化导出，插件按需取用）
    ui: {
      // alert
      Alert: alert.Alert, AlertTitle: alert.AlertTitle, AlertDescription: alert.AlertDescription,
      // badge
      Badge: badge.Badge,
      // button
      Button: button.Button,
      // card
      Card: card.Card, CardHeader: card.CardHeader, CardTitle: card.CardTitle,
      CardDescription: card.CardDescription, CardContent: card.CardContent, CardFooter: card.CardFooter,
      // dialog
      Dialog: dialog.Dialog, DialogContent: dialog.DialogContent, DialogHeader: dialog.DialogHeader,
      DialogTitle: dialog.DialogTitle, DialogDescription: dialog.DialogDescription,
      DialogFooter: dialog.DialogFooter, DialogClose: dialog.DialogClose, DialogTrigger: dialog.DialogTrigger,
      // dropdown-menu
      DropdownMenu: dropdownMenu.DropdownMenu, DropdownMenuTrigger: dropdownMenu.DropdownMenuTrigger,
      DropdownMenuContent: dropdownMenu.DropdownMenuContent, DropdownMenuItem: dropdownMenu.DropdownMenuItem,
      DropdownMenuLabel: dropdownMenu.DropdownMenuLabel, DropdownMenuSeparator: dropdownMenu.DropdownMenuSeparator,
      // empty
      Empty: empty.Empty,
      // input
      Input: input.Input,
      // label
      Label: label.Label,
      // pagination
      Pagination: pagination.Pagination,
      // select
      Select: select.Select, SelectTrigger: select.SelectTrigger, SelectValue: select.SelectValue,
      SelectContent: select.SelectContent, SelectItem: select.SelectItem,
      // slider
      Slider: slider.Slider,
      // switch
      Switch: switchModule.Switch,
      // table
      Table: table.Table, TableHeader: table.TableHeader, TableBody: table.TableBody,
      TableRow: table.TableRow, TableHead: table.TableHead, TableCell: table.TableCell,
      // toast
      Toast: toast.Toast, Toaster: toast.Toaster, useToast: toast.useToast,
      // 共享业务组件
      CoverPickerDialog
    },
    // 核心 stores
    stores: {
      usePlayerStore, useNodesStore, usePluginsStore, useAuthStore, useLibraryStore
    },
    // HTTP 客户端
    axios,
    // 音频播放库
    howler: { Howl },
    // 工具函数
    utils: { cn },
    // 图标库
    icons: {
      Music, Search, Play, Plus, Pause, SkipForward, SkipBack, X, Loader2,
      AlertCircle, CheckCircle2, RefreshCw, User, ListMusic, Flame, ArrowLeft,
      Clock, Headphones, Download, Settings, Tag, Mic2, Users, Home, Captions,
      QrCode, Trash2, Heart, Star, BookmarkIcon, ChevronDown, ChevronRight,
      ChevronLeft, ChevronUp, MoreVertical, Filter, SortAsc, SortDesc, Folder,
      FolderOpen, File, FileImage, Video, Volume2, VolumeX, Shuffle, Repeat,
      Pencil, Save, Upload, Eye, Shield, Sparkles,
      LogOut, FileAudio, FileText, Check, Square, ExternalLink, HardDrive,
      CheckSquare, XCircle, Ban, ImageIcon, ImageOff, ImagePlus,
      Link, List, CheckCircle
    },
    // 版本号（便于插件做兼容性检查）
    version: '1.4.0'
  }
}
