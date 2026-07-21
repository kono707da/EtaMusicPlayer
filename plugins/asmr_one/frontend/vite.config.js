import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

// asmr_one 插件前端构建配置
// 输出 ESM 格式，依赖通过 window.__etamusic 取用（不打包 vue/pinia/ui 等）
// base 设置为 /plugins-assets/asmr_one/，确保动态 import 的 chunk URL 正确
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './')
    }
  },
  base: '/plugins-assets/asmr_one/',
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    emptyOutDir: true,
    // 使用 library mode 构建为 ESM 模块
    lib: {
      entry: 'index.js',
      formats: ['es'],
      fileName: () => 'index.js'
    },
    rollupOptions: {
      output: {
        chunkFileNames: 'assets/[name]-[hash].js',
        assetFileNames: 'assets/[name]-[hash][extname]'
      }
    },
    minify: 'esbuild',
    sourcemap: false
  }
})
