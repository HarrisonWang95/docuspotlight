<template>
  <v-app>
    <v-main class="app-container">
      <router-view />
    </v-main>
  </v-app>
</template>

<script setup>
// 使用路由视图，所有功能已移至ComparisonPage组件
</script>

<style>
/* 全局样式 */
.app-container {
  background-color: var(--background-color);
  min-height: 100vh;
}

/* 现代化科技感主题 - 专业蓝色系 */
:root {
  --primary-color: #1976d2;
  --secondary-color: #0288d1;
  --accent-color: #03a9f4;
  --success-color: #4caf50;
  --warning-color: #ff9800;
  --error-color: #f44336;
  --background-color: #f0f4f8;
  --card-color: #ffffff;
  --text-primary: #263238;
  --text-secondary: #546e7a;
  --border-color: #e0e0e0;
  --hover-color: rgba(3, 169, 244, 0.05);
  --shadow-color: rgba(0, 0, 0, 0.1);
}

/* 文件上传区域样式 */
.upload-area {
  border: 2px dashed var(--primary-color);
  border-radius: 8px;
  transition: all 0.3s ease;
}

.upload-area.dragging {
  background-color: rgba(63, 81, 181, 0.1);
  border-color: var(--accent-color);
}

/* Tab样式优化 */
.v-tab {
  letter-spacing: 0.5px;
  font-weight: 500;
}

/* 科技感动画效果 */
@keyframes pulse {
  0% { box-shadow: 0 0 0 0 rgba(63, 81, 181, 0.4); }
  70% { box-shadow: 0 0 0 10px rgba(63, 81, 181, 0); }
  100% { box-shadow: 0 0 0 0 rgba(63, 81, 181, 0); }
}

.pulse-animation {
  animation: pulse 2s infinite;
}

/* JSON编辑器样式 */
.monospace-font {
  font-family: 'Roboto Mono', monospace;
  font-size: 14px;
  line-height: 1.5;
}
</style>
