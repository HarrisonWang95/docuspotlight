<template>
  <v-container class="mt-4 mb-4" fluid>
    <div class="d-flex align-center mb-4">
      <div class="d-flex align-center">
        <img src="/logo.png" alt="Logo" height="40" class="mr-2" />
        <h1 class="text-h4">文档聚光灯 DocuSpotlight</h1>
      </div>
    </div>
    
    <div v-if="loading" class="d-flex justify-center align-center" style="height: 200px;">
      <v-progress-circular indeterminate color="primary"></v-progress-circular>
      <span class="ml-2">加载数据中...</span>
    </div>
    
    <v-row v-if="!loading" :cols="12">
      <!-- 左侧：文档上传和预览区域 -->
      <v-col cols="12" md="4">
        <v-card class="mb-4 document-card">
          <v-tabs v-model="activeTab" bg-color="primary">
            <v-tab value="documents">文档上传与预览</v-tab>
            <v-tab value="schema">
              <v-menu v-model="schemaMenu">
                <template v-slot:activator="{ props }">
                  <div class="d-flex align-center" v-bind="props">
                    JSON Schema 编辑器
                    <v-icon end>mdi-menu-down</v-icon>
                  </div>
                </template>
                <v-list>
                  <v-list-item @click="handleSchemaMode('code')">
                    <v-list-item-title>源码编辑</v-list-item-title>
                  </v-list-item>
                  <v-list-item @click="handleSchemaMode('visual')">
                    <v-list-item-title>可视化编辑</v-list-item-title>
                  </v-list-item>
                </v-list>
              </v-menu>
            </v-tab>
          </v-tabs>
          
          <v-window v-model="activeTab" class="tab-content-window">
            <!-- 文档上传与预览 Tab -->
            <v-window-item value="documents">
              <div class="pa-4">
                <!-- 上传完成后显示的小型上传区域 -->
                <div v-if="uploadComplete" class="compact-upload-area mb-3">
                  <v-btn 
                    prepend-icon="mdi-upload" 
                    color="primary" 
                    variant="tonal" 
                    size="small"
                    @click="toggleUploadArea"
                  >
                    上传新文件
                  </v-btn>
                  <v-chip class="ml-2" color="success" size="small" v-if="filesList.length > 0">
                    已上传 {{ filesList.length }} 个文件
                  </v-chip>
                </div>
                
                <!-- 可展开/收起的上传区域 -->
                <v-expand-transition>
                  <div v-show="!uploadComplete || showUploadArea">
                    <multi-file-uploader 
                      :task-id="props.taskId"
                      @upload-complete="handleUploadComplete"
                      class="mb-4"
                      style="max-height: 250px; overflow-y: auto;"
                    />
                    <v-alert v-if="showUploadArea" type="info" variant="tonal" density="compact" class="mb-3">
                      <div class="text-caption">支持PDF、Word、Excel等常见文档格式</div>
                    </v-alert>
                  </div>
                </v-expand-transition>
                
                <!-- 文档预览区域 -->
                <div class="document-preview-wrapper position-relative">
                  <!-- 文档查看器组件 -->
                  <document-viewer 
                    ref="documentViewer" 
                    :files="filesList" 
                    :zoom-level="zoomLevel"
                    :rotation="rotation"
                    :fullscreen="isFullscreen"
                    @fullscreen-changed="handleFullscreenChange"
                  />
                </div>
              </div>
            </v-window-item>
        
        <!-- JSON Schema 编辑器 Tab -->
        <v-window-item value="schema">
          <div class="pa-4">
            <json-schema-editor 
              :task-id="props.taskId"
              :active-tab="schemaEditorMode"
              @schema-saved="handleSchemaSaved"
            />
          </div>
        </v-window-item>
      </v-window>
    </v-card>
  </v-col>
      
      <!-- 右侧：多渠道比对区域 -->
      <v-col cols="12" md="8">
        <v-card class="mb-4 compare-card">
          <multi-channel-compare 
            :task-id="props.taskId"
            @decision-saved="handleDecisionSaved"
            @zoom-to-field="handleZoomToField"
            class="compare-content"
          />
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';
import DocumentViewer from './DocumentViewer.vue';
import MultiChannelCompare from './MultiChannelCompare.vue';
import MultiFileUploader from './MultiFileUploader.vue';
import JsonSchemaEditor from './JsonSchemaEditor.vue';
import { API_BASE_URL } from '../config';
import { useToast } from 'vue-toastification';

const toast = useToast();

// 定义 props
const props = defineProps({
  taskId: {
    type: String,
    required: true
  }
});

const fileUrl = ref('');
const fileType = ref('');
const documentId = ref('');
const loading = ref(true);
const activeTab = ref('documents');
const schemaEditorMode = ref('code'); // 添加schemaEditorMode变量，默认为code模式
const uploadComplete = ref(true); // 修改初始值为 true
const showUploadArea = ref(false);
const documentViewer = ref(null);
const zoomLevel = ref(1);
const rotation = ref(0);
const isFullscreen = ref(false);
const router = useRouter();

// 页面加载时获取文档数据
onMounted(async () => {
  try {
    // 使用 taskId 获取文档
    const response = await axios.get(`${API_BASE_URL}/api/documents/${props.taskId}`);
    if (response.data && response.data.documents && response.data.documents.length > 0) {
      await loadDocument(response.data.documents[0].id);
    } else {
      alert('没有可用的文档');
      loading.value = false;
    }
  } catch (error) {
    console.error('获取文档列表失败:', error);
    alert('获取文档列表失败');
    loading.value = false;
  }
});

const loadDocument = async (docId) => {
  try {
    const docResponse = await axios.get(`${API_BASE_URL}/api/files/${docId}`);
    
    fileUrl.value = `${API_BASE_URL}/api/files/${docResponse.data.id}`;
    fileType.value = docResponse.data.file_type;
    documentId.value = docId;
    
    loading.value = false;
  } catch (error) {
    console.error('加载文档失败:', error);
    alert('加载文档失败');
    loading.value = false;
  }
};

// 创建一个计算属性，将单个文件转换为数组格式
const filesList = computed(() => {
  if (!fileUrl.value) return [];
  
  return [{
    filename: documentId.value,
    file_type: fileType.value
  }];
});

const handleDecisionSaved = (decisionData) => {
  console.log('决策结果已保存:', decisionData);
  // 可以在这里添加其他处理逻辑
};

const handleUploadComplete = ({ taskId }) => {
  console.log('文件上传完成，任务ID:', taskId);
  uploadComplete.value = true;
  showUploadArea.value = false;
  toast.success('文件上传成功！');
  
  // 延迟切换到Schema编辑器，让用户先看到上传成功提示
  setTimeout(() => {
    activeTab.value = 'schema';
  }, 1500);
};

// 切换上传区域显示/隐藏
const toggleUploadArea = () => {
  showUploadArea.value = !showUploadArea.value;
};

// 文档预览操作函数
const zoomIn = () => {
  if (documentViewer.value) {
    documentViewer.value.zoomIn();
    zoomLevel.value += 0.25;
  }
};

const zoomOut = () => {
  if (documentViewer.value) {
    documentViewer.value.zoomOut();
    zoomLevel.value -= 0.25;
  }
};

const rotateImage = () => {
  if (documentViewer.value) {
    documentViewer.value.rotate();
    rotation.value = (rotation.value + 90) % 360;
  }
};

const resetView = () => {
  if (documentViewer.value) {
    documentViewer.value.resetView();
    zoomLevel.value = 1;
    rotation.value = 0;
  }
};

const toggleFullscreen = () => {
  if (documentViewer.value) {
    documentViewer.value.toggleFullscreen();
  }
};

const handleFullscreenChange = (isFullscreenMode) => {
  isFullscreen.value = isFullscreenMode;
};

const zoomToRect = () => {
  if (documentViewer.value) {
    documentViewer.value.zoomToRect();
    zoomLevel.value = 2;
  }
};

const handleSchemaSaved = (schemaData) => {
  console.log('Schema已保存:', schemaData);
  // 可以在这里添加其他处理逻辑
};

const schemaMenu = ref(false);

const handleSchemaMode = (mode) => {
  schemaEditorMode.value = mode;
  schemaMenu.value = false; // 关闭菜单
};

// 处理字段放大事件
const handleZoomToField = (rect) => {
  if (documentViewer.value) {
    documentViewer.value.zoomToRect(rect);
    zoomLevel.value = 2; // 设置放大级别
  }
};
</script>

<style scoped>
.document-card {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.tab-content-window {
  max-height: 70vh;
  overflow-y: auto;
}

.compare-card {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.compare-content {
  max-height: 70vh;
  overflow-y: auto;
}

.document-preview-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 400px;
}

.preview-toolbar {
  background-color: rgba(0, 0, 0, 0.02);
  border-radius: 8px;
  padding: 8px;
  overflow-x: auto;
  white-space: nowrap;
}

.floating-toolbar {
  position: absolute;
  bottom: 16px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 10;
  background-color: rgba(255, 255, 255, 0.7); /* 更改为半透明背景 */
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(1px); /* 保留模糊效果以提高可读性 */
  border-radius: 8px;
  padding: 8px 16px;
  transition: opacity 0.3s ease;
}

.compact-upload-area {
  display: flex;
  align-items: center;
  padding: 8px;
  border-radius: 8px;
  background-color: rgba(0, 0, 0, 0.02);
}

/* 响应式设计 */
@media (max-width: 960px) {
  .preview-toolbar {
    flex-wrap: nowrap;
    justify-content: flex-start;
    overflow-x: auto;
  }
  
  .document-preview-wrapper {
    min-height: 300px;
  }
}
</style>