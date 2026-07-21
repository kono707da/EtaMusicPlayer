import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

// 网易云插件前端构建配置
// 输出 ESM 格式，依赖通过 window.__etamusic 取用（不打包 vue/pinia/ui 等）
// base 设置为 /plugins-assets/netease_music/，确保动态 import 的 chunk URL 正确
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './')
    }
  },
  base: '/plugins-assets/netease_music/',
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
      // 不 external 任何依赖，但因为插件代码从 window.__etamusic 取用，
      // 实际不会 import vue/pinia 等裸模块，所以无需 external 配置
      output: {
        chunkFileNames: 'assets/[name]-[hash].js',
        assetFileNames: 'assets/[name]-[hash][extname]'
      }
    },
    minify: 'esbuild',
    sourcemap: false
  }
})
