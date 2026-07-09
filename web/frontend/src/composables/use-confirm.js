import { reactive } from 'vue'

// 全局确认对话框状态
const state = reactive({
  open: false,
  title: '',
  message: '',
  type: 'warning', // warning | danger | info
  resolve: null
})

function confirm(message, options = {}) {
  return new Promise((resolve) => {
    state.title = options.title || '提示'
    state.message = message
    state.type = options.type || 'warning'
    state.open = true
    state.resolve = resolve
  })
}

function onConfirm() {
  state.open = false
  state.resolve?.(true)
  state.resolve = null
}

function onCancel() {
  state.open = false
  state.resolve?.(false)
  state.resolve = null
}

export function useConfirm() {
  return { state, confirm, onConfirm, onCancel }
}
