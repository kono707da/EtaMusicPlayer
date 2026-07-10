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
 * 从任意错误对象中提取可读的详细信息，用于后端日志排查。
 * 支持 axios 错误（含 response/config）、普通 Error、字符串等。
 */
function extractErrorDetail(err) {
  if (!err) return ''
  const parts = []

  // axios 错误：提取 HTTP 状态、后端响应、请求 URL
  if (err.response) {
    const resp = err.response
    parts.push(`HTTP ${resp.status}`)
    if (resp.statusText) parts.push(resp.statusText)
    if (resp.data) {
      let body
      try {
        body = typeof resp.data === 'string' ? resp.data : JSON.stringify(resp.data)
      } catch {
        body = String(resp.data)
      }
      if (body) parts.push(`响应体: ${body}`)
    }
  }
  if (err.config) {
    const method = (err.config.method || 'GET').toUpperCase()
    const url = err.config.baseURL
      ? `${err.config.baseURL}${err.config.url || ''}`
      : err.config.url || ''
    if (url) parts.push(`请求: ${method} ${url}`)
  }
  // 网络层错误（无 response 时，err.message 通常是 "Network Error" 等）
  if (err.message) parts.push(`消息: ${err.message}`)
  // 原始错误名
  if (err.name && err.name !== 'Error') parts.push(`类型: ${err.name}`)
  // 堆栈（截断，避免日志过长）
  if (err.stack) {
    const stackLines = err.stack.split('\n').slice(0, 5).join('\n')
    parts.push(`堆栈:\n${stackLines}`)
  }

  return parts.join(' | ')
}

/**
 * 异步上报前端错误到后端日志（fire-and-forget）。
 * 仅在 error 类型 toast 触发时调用，失败时静默，不影响 UI。
 * @param {string} title 错误标题
 * @param {string} description UI 显示的简短描述
 * @param {*} errorObj 原始错误对象（可选），用于提取详细日志信息
 */
function reportErrorToBackend(title, description = '', errorObj = null) {
  try {
    const detail = errorObj ? extractErrorDetail(errorObj) : description
    fetch('/api/system/frontend-error', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title,
        description: detail || description,
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
    error: (title, description = '', errorObj = null) => {
      const id = add({ type: 'error', title, description })
      reportErrorToBackend(title, description, errorObj)
      return id
    },
    warning: (title, description = '') => add({ type: 'warning', title, description }),
    info: (title, description = '') => add({ type: 'info', title, description }),
    remove
  }
}
