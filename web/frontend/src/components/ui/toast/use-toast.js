import { reactive } from 'vue'

// 模块级共享状态：所有调用 useToast() 的组件共享同一份 toasts 列表
const toasts = reactive([])
let seq = 0

function remove(id) {
  const idx = toasts.findIndex((t) => t.id === id)
  if (idx > -1) toasts.splice(idx, 1)
}

function add({ type = 'default', title = '', description = '', duration = 3000 }) {
  const id = ++seq
  toasts.push({ id, type, title, description })
  if (duration > 0) {
    setTimeout(() => remove(id), duration)
  }
  return id
}

/**
 * 异步上报前端错误到后端日志（fire-and-forget）。
 * 仅在 error 类型 toast 触发时调用，失败时静默，不影响 UI。
 */
function reportErrorToBackend(title, description = '') {
  try {
    fetch('/api/system/frontend-error', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title,
        description,
        url: window.location.href,
        timestamp: new Date().toISOString()
      })
    }).catch(() => {})
  } catch {
    // 静默失败
  }
}

/**
 * 全局 toast 状态管理
 * @returns {{ toasts: Array, toast: Function, success: Function, error: Function, warning: Function, info: Function, remove: Function }}
 */
export function useToast() {
  return {
    toasts,
    toast: (opts = {}) => add(opts),
    success: (title, description = '') => add({ type: 'success', title, description }),
    error: (title, description = '') => {
      const id = add({ type: 'error', title, description })
      reportErrorToBackend(title, description)
      return id
    },
    warning: (title, description = '') => add({ type: 'warning', title, description }),
    info: (title, description = '') => add({ type: 'info', title, description }),
    remove
  }
}
