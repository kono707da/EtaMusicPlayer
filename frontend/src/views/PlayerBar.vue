<script setup>
/**
 * 底部播放控制条
 * 说明：本文件不是独立路由视图，仅作为组件复用入口。
 * 实际实现位于 components/PlayerBar.vue，这里通过 re-export 方式
 * 满足目录结构约定（views/PlayerBar.vue + components/PlayerBar.vue 并存）。
 */
import PlayerBar from '../components/PlayerBar.vue'
</script>

<template>
  <PlayerBar />
</template>
