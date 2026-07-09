import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

// EtaMusic 前端 Vite 配置
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')
    }
  },
  server: {
    host: '0.0.0.0',
    port: 5173,
    // 开发环境代理：/api → 访问端骨架，/local_node → 本地节点插件
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      },
      '/local_node': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      }
    }
  }
})
