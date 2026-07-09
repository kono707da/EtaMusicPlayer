import axios from 'axios'

/**
 * 创建针对单个节点的 axios 实例
 * - baseURL 取节点 baseUrl
 * - 请求拦截器：自动加上 Authorization: Bearer token
 * - 响应拦截器：401 时用保存的账号密码重新登录刷新 token，重试原请求
 *
 * @param {Object} node 节点配置对象 {id, name, baseUrl, username, password, token, userInfo}
 * @param {Object} options 额外选项 { onTokenRefresh } token 刷新回调
 * @returns {import('axios').AxiosInstance}
 */
export function createNodeClient(node, options = {}) {
  const instance = axios.create({
    baseURL: node.baseUrl,
    timeout: 15000
  })

  // 请求拦截器：注入 token
  instance.interceptors.request.use(
    (config) => {
      if (node.token) {
        config.headers = config.headers || {}
        config.headers.Authorization = `Bearer ${node.token}`
      }
      return config
    },
    (err) => Promise.reject(err)
  )

  // 响应拦截器：401 自动重登重试
  instance.interceptors.response.use(
    (resp) => resp,
    async (error) => {
      const originalRequest = error.config
      const status = error.response?.status

      // 401 且未重试过 且有账号密码 → 重新登录
      if (
        status === 401 &&
        !originalRequest.__retried &&
        node.username &&
        node.password
      ) {
        originalRequest.__retried = true
        try {
          const newToken = await refreshToken(node)
          node.token = newToken
          // 通知外部刷新 token（用于持久化）
          if (typeof options.onTokenRefresh === 'function') {
            options.onTokenRefresh(node)
          }
          // 更新请求头并重试
          originalRequest.headers = originalRequest.headers || {}
          originalRequest.headers.Authorization = `Bearer ${newToken}`
          return instance(originalRequest)
        } catch (refreshErr) {
          return Promise.reject(refreshErr)
        }
      }
      return Promise.reject(error)
    }
  )

  return instance
}

/**
 * 用账号密码重新登录刷新 token
 */
async function refreshToken(node) {
  const resp = await axios.post(`${node.baseUrl}/api/auth/login`, {
    username: node.username,
    password: node.password
  })
  return resp.data?.token || resp.data?.access_token
}
