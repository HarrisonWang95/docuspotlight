<template>
  <div class="document-viewer" ref="viewerContainer" :class="{ 'fullscreen-mode': isFullscreen }">
    <!-- 退出全屏按钮 -->
    <v-btn v-if="isFullscreen" icon="mdi-fullscreen-exit" size="small" color="primary" class="exit-fullscreen-btn"
      @click="toggleFullscreen"></v-btn>

    <div v-if="loading" class="d-flex justify-center align-center" style="height: 200px;">
      <v-progress-circular indeterminate color="primary"></v-progress-circular>
    </div>

    <div v-else class="documents-container">
      <!-- 文件预览区域 -->
      <div v-if="selectedFileUrl" class="preview-container" 
            @wheel.ctrl.prevent="handleWheel"
            @mousemove="isToolbarVisible = true"
            @mouseleave="isToolbarVisible = false">
            <!-- 工具栏 -->
            <div class="toolbar-container" :class="{ 'toolbar-visible': isToolbarVisible }">
              <v-chip-group>
                <v-chip size="small" @click="zoomIn" variant="tonal">放大</v-chip>
                <v-chip size="small" @click="zoomOut" variant="tonal">缩小</v-chip>
                <v-chip size="small" @click="rotate" variant="tonal">旋转</v-chip>
                <v-chip size="small" @click="resetView" variant="tonal">重置</v-chip>
                <v-chip size="small" @click="toggleFullscreen" variant="tonal">全屏</v-chip>
                <v-chip size="small" @click="zoomToRect" variant="tonal">预设放大</v-chip>
              </v-chip-group>
            </div>

        <div v-if="isPdf" class="pdf-container" :style="transformStyle"
            @mousedown="handleMouseDown"
            @mousemove="handleMouseMove"
            @mouseup="handleMouseUp"
            @mouseleave="handleMouseUp">
          <vue-pdf-embed :source="selectedFileUrl" />
        </div>

        <div v-else class="image-container" :style="transformStyle"
            @mousedown="handleMouseDown"
            @mousemove="handleMouseMove"
            @mouseup="handleMouseUp"
            @mouseleave="handleMouseUp">
          <img :src="selectedFileUrl" alt="文档预览" ref="previewImage" @load="imageLoaded" />
        </div>
      </div>
      <!-- 文件列表选择器 -->
      <div class="file-selector mb-4">
        <v-select v-model="selectedFileUrl" :items="fileUrls" item-title="filename" item-value="url" label="选择文件"
          density="compact" variant="outlined" hide-details>
          <template v-slot:prepend>
            <v-icon :color="getFileIconColor(selectedFile?.type)" size="small">
              {{ getFileIcon(selectedFile?.type) }}
            </v-icon>
          </template>
        </v-select>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, defineExpose } from 'vue';
import VuePdfEmbed from 'vue-pdf-embed';
import { API_BASE_URL } from '../config';

const props = defineProps({
  files: {
    type: Array,
    required: true
  },
  zoomLevel: {
    type: Number,
    default: 1
  },
  rotation: {
    type: Number,
    default: 0
  },
  fullscreen: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(['fullscreen-changed']);

const loading = ref(true);
const selectedFileUrl = ref('');
const viewerContainer = ref(null);
const previewImage = ref(null);
const currentZoom = ref(1);
const currentRotation = ref(0);
const isFullscreen = ref(false);
const imageNaturalWidth = ref(0);
const imageNaturalHeight = ref(0);

// 处理文件URL列表
const fileUrls = computed(() => {
  return props.files.map(file => ({
    filename: file.filename,
    url: `${API_BASE_URL}/api/files/${file.filename}`,
    type: file.file_type
  }));
});

// 获取当前选中的文件信息
const selectedFile = computed(() => {
  return fileUrls.value.find(f => f.url === selectedFileUrl.value);
});

// 判断当前选中的文件是否为PDF
const isPdf = computed(() => {
  return selectedFile.value?.type?.includes('pdf') ?? false;
});

// 计算变换样式
const position = ref({ x: 0, y: 0 });
const isDragging = ref(false);
const startPosition = ref({ x: 0, y: 0 });

const transformStyle = computed(() => {
  return {
    transform: `translate(${position.value.x}px, ${position.value.y}px) scale(${currentZoom.value}) rotate(${currentRotation.value}deg)`,
    transition: isDragging.value ? 'none' : 'transform 0.3s ease',
    cursor: isDragging.value ? 'grabbing' : 'grab'
  };
});

const handleMouseDown = (e) => {
  isDragging.value = true;
  startPosition.value = {
    x: e.clientX - position.value.x,
    y: e.clientY - position.value.y
  };
};

const handleMouseMove = (e) => {
  if (isDragging.value) {
    position.value = {
      x: e.clientX - startPosition.value.x,
      y: e.clientY - startPosition.value.y
    };
  }
};

const handleMouseUp = () => {
  isDragging.value = false;
};

// 监听文件变化
watch(() => props.files, (newFiles) => {
  if (newFiles?.length) {
    loading.value = false;
    // 默认选择第一个文件
    selectedFileUrl.value = fileUrls.value[0].url;
  }
}, { immediate: true });

// 监听选中文件的变化
watch(selectedFileUrl, (newUrl) => {
  if (newUrl) {
    loading.value = true;
    resetView();
    if (!isPdf.value) {
      const img = new Image();
      img.onload = () => {
        loading.value = false;
      };
      img.onerror = () => {
        loading.value = false;
        console.error('加载图片失败');
      };
      img.src = newUrl;
    } else {
      setTimeout(() => {
        loading.value = false;
      }, 1000);
    }
  }
});

// 监听缩放级别变化
watch(() => props.zoomLevel, (newZoom) => {
  if (newZoom !== currentZoom.value) {
    currentZoom.value = newZoom;
  }
});

// 监听旋转角度变化
watch(() => props.rotation, (newRotation) => {
  if (newRotation !== currentRotation.value) {
    currentRotation.value = newRotation;
  }
});

// 监听全屏状态变化
watch(() => props.fullscreen, (newValue) => {
  if (newValue !== isFullscreen.value) {
    toggleFullscreen();
  }
});

// 图片加载完成后获取原始尺寸
const imageLoaded = () => {
  if (previewImage.value) {
    imageNaturalWidth.value = previewImage.value.naturalWidth;
    imageNaturalHeight.value = previewImage.value.naturalHeight;
  }
};

// 放大
const zoomIn = () => {
  currentZoom.value = Math.min(currentZoom.value + 0.25, 3);
};

// 缩小
const zoomOut = () => {
  currentZoom.value = Math.max(currentZoom.value - 0.25, 0.5);
};

// 旋转
const rotate = () => {
  currentRotation.value = (currentRotation.value + 90) % 360;
};

// 重置视图
const resetView = () => {
  currentZoom.value = 1;
  currentRotation.value = 0;
  position.value = { x: 0, y: 0 };
};

// 预设放大到指定区域
const zoomToRect = (rect) => {
  console.log('接收到的矩形区域:', rect);
  
  // 如果没有提供矩形区域，使用默认值
  if (!rect) {
    rect = { y0: 142, x1: 547, y1: 247, x0: 61 };
  }

  // 确保selectedFileUrl有值，防止文件丢失
  if (!selectedFileUrl.value || loading.value) {
    console.log('文件未加载完成，无法执行缩放操作');
    // 将缩放操作延迟到文件加载完成后执行
    setTimeout(() => {
      if (selectedFileUrl.value && !loading.value) {
        zoomToRect(rect);
      }
    }, 500);
    return;
  }

  // 处理norm_box数据
  // 如果坐标值过大（如MultiChannelCompare中乘以1000的值），进行归一化处理
  const isNormalized = rect.x0 > 1 && rect.y0 > 1;
  let normalizedRect = { ...rect };
  
  if (isNormalized) {
    // 假设这些是像素坐标，需要根据实际情况调整缩放因子
    const scaleFactor = isPdf.value ? 1 : (imageNaturalWidth.value ? 1000 / imageNaturalWidth.value : 0.001);
    normalizedRect = {
      x0: rect.x0 * scaleFactor,
      y0: rect.y0 * scaleFactor,
      x1: rect.x1 * scaleFactor,
      y1: rect.y1 * scaleFactor
    };
  }

  // 计算矩形中心点
  const centerX = (normalizedRect.x0 + normalizedRect.x1) / 2;
  const centerY = (normalizedRect.y0 + normalizedRect.y1) / 2;
  console.log('计算的中心点:', { centerX, centerY });
  
  // 设置缩放级别 - 根据矩形大小动态调整缩放级别
  const rectWidth = Math.abs(normalizedRect.x1 - normalizedRect.x0);
  const rectHeight = Math.abs(normalizedRect.y1 - normalizedRect.y0);
  
  // 根据矩形大小计算合适的缩放级别，确保矩形区域能够完全显示
  const container = viewerContainer.value;
  if (container) {
    const containerRect = container.getBoundingClientRect();
    const containerCenterX = containerRect.width / 2;
    const containerCenterY = containerRect.height / 2;
    console.log('容器中心点:', { containerCenterX, containerCenterY });
    
    // 计算合适的缩放级别
    const widthRatio = containerRect.width / (rectWidth * 1.5); // 添加一些边距
    const heightRatio = containerRect.height / (rectHeight * 1.5);
    const zoomRatio = Math.min(widthRatio, heightRatio, 3); // 限制最大缩放级别为3
    currentZoom.value = Math.max(zoomRatio, 1); // 确保至少为1
    
    // 计算位移，使目标区域居中
    position.value = {
      x: containerCenterX - centerX * currentZoom.value,
      y: containerCenterY - centerY * currentZoom.value
    };
    console.log('设置的位移:', position.value);
    
    // 确保文件引用不丢失
    if (!selectedFileUrl.value) {
      console.warn('缩放过程中文件引用丢失，尝试恢复');
      if (fileUrls.value.length > 0) {
        selectedFileUrl.value = fileUrls.value[0].url;
      }
    }
  }
};

// 处理鼠标滚轮事件（按住Ctrl键时缩放）
const handleWheel = (event) => {
  if (event.ctrlKey) {
    if (event.deltaY < 0) {
      zoomIn();
    } else {
      zoomOut();
    }
  }
};

// 切换全屏模式
const toggleFullscreen = () => {
  isFullscreen.value = !isFullscreen.value;
  emit('fullscreen-changed', isFullscreen.value);
};

// 获取文件图标
const getFileIcon = (fileType) => {
  if (!fileType) return 'mdi-file-outline';

  if (fileType.includes('pdf')) return 'mdi-file-pdf-box';
  if (fileType.includes('doc')) return 'mdi-file-word-outline';
  if (fileType.includes('xls')) return 'mdi-file-excel-outline';
  if (fileType.includes('ppt')) return 'mdi-file-powerpoint-outline';
  if (fileType.includes('image') || fileType.includes('jpg') || fileType.includes('jpeg') || fileType.includes('png')) {
    return 'mdi-file-image-outline';
  }

  return 'mdi-file-outline';
};

// 获取文件图标颜色
const getFileIconColor = (fileType) => {
  if (!fileType) return 'grey';

  if (fileType.includes('pdf')) return 'red';
  if (fileType.includes('doc')) return 'blue';
  if (fileType.includes('xls')) return 'green';
  if (fileType.includes('ppt')) return 'orange';
  if (fileType.includes('image') || fileType.includes('jpg') || fileType.includes('jpeg') || fileType.includes('png')) {
    return 'purple';
  }

  return 'grey';
};

// 监听ESC键退出全屏
const handleKeyDown = (event) => {
  if (event.key === 'Escape' && isFullscreen.value) {
    toggleFullscreen();
  }
};

onMounted(() => {
  document.addEventListener('keydown', handleKeyDown);
});

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeyDown);
});

// 暴露方法给父组件
defineExpose({
  zoomIn,
  zoomOut,
  rotate,
  resetView,
  toggleFullscreen,
  zoomToRect
});
</script>

<style scoped>
.document-viewer {
  height: 100%;
  overflow: auto;
  padding: 16px;
  border-radius: 8px;
  background-color: var(--card-color);
  position: relative;
  transition: all 0.3s ease;
}

.exit-fullscreen-btn {
  position: absolute;
  top: 16px;
  right: 16px;
  z-index: 100;
  opacity: 0.8;
  transition: opacity 0.2s ease;
}

.exit-fullscreen-btn:hover {
  opacity: 1;
}

.documents-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
  gap: 16px;
}

.file-selector {
  width: 100%;
  max-width: 500px;
  margin-bottom: 8px;
  z-index: 2;
}

.preview-container {
  width: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  background-color: rgba(0, 0, 0, 0.02);
  border-radius: 8px;
  padding: 12px;
  box-shadow: inset 0 0 8px rgba(0, 0, 0, 0.05);
  overflow: hidden;
  min-height: 300px;
  position: relative;
}

.pdf-container,
.image-container {
  width: 100%;
  display: flex;
  justify-content: center;
  border-radius: 4px;
  overflow: hidden;
  transform-origin: center center;
}

.image-container img {
  max-width: 100%;
  max-height: calc(100vh - 300px);
  object-fit: contain;
  transition: transform 0.3s ease;
}

.toolbar-container {
  position: absolute;
  top: 16px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 10;
  padding: 8px;
  width: auto;
  display: flex;
  justify-content: center;
  background-color: rgba(255, 255, 255, 0.9);
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(4px);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.toolbar-container.toolbar-visible {
  opacity: 1;
}

/* 确保全屏模式下工具栏始终可见 */
.fullscreen-mode .toolbar-container {
  opacity: 1;
}

/* 全屏模式样式 */
.fullscreen-mode {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  z-index: 9999;
  background-color: rgba(255, 255, 255, 0.95);
  padding: 20px;
  display: flex;
  flex-direction: column;
  overflow: auto;
}

.fullscreen-mode .preview-container {
  flex: 1;
  max-height: calc(100vh - 100px);
}

.fullscreen-mode .image-container img {
  max-height: calc(100vh - 150px);
}

.fullscreen-mode .toolbar-container {
  position: fixed;
  top: 16px;
  left: 50%;
  transform: translateX(-50%);
  background-color: rgba(255, 255, 255, 0.9);
}

/* 添加响应式设计 */
@media (max-width: 960px) {
  .file-selector {
    max-width: 100%;
  }

  .preview-container {
    min-height: 200px;
  }
}
</style>