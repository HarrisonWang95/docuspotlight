<template>
  <div class="multi-file-uploader">
    <div class="d-flex align-center mb-4">
      <h3 class="text-h6">文件上传</h3>
      <v-spacer></v-spacer>
      <v-btn color="primary" @click="completeUpload" :disabled="files.length === 0 || uploading">
        完成上传
      </v-btn>
    </div>

    <div class="upload-area pa-3 mb-3" :class="{ 'dragging': isDragging }" @dragover.prevent="onDragOver" @dragleave.prevent="onDragLeave" @drop.prevent="onDrop">
      <div class="text-center">
        <div class="d-flex align-center justify-center">
          <v-icon size="36" color="primary" class="mr-2">mdi-cloud-upload</v-icon>
          <div>
            <h4 class="text-subtitle-1 mb-1">拖放文件到此处</h4>
            <p class="text-caption text-secondary mb-1">支持PDF、Word、Excel等常见文档格式</p>
          </div>
        </div>
        <input
          accept=".pdf,.doc,.docx,.xls,.xlsx,.jpg,.jpeg,.png"
          style="display: none"
          ref="fileInput"
          id="multi-file-upload"
          type="file"
          multiple
          @change="handleFileChange"
          :disabled="uploading"
        />
        <v-btn
          variant="outlined"
          color="primary"
          size="small"
          class="mt-2"
          :disabled="uploading"
          @click="$refs.fileInput.click()"
        >
          选择文件
        </v-btn>
      </div>
    </div>

    <!-- 文件列表 -->
    <div v-if="files.length > 0" class="file-list">
      <h4 class="text-subtitle-1 mb-2">已选择的文件</h4>
      <v-list density="compact">
        <v-list-item v-for="(file, index) in files" :key="index" :title="file.name">
          <template v-slot:prepend>
            <v-icon :color="getFileIconColor(file.name)">
              {{ getFileIcon(file.name) }}
            </v-icon>
          </template>
          <template v-slot:append>
            <v-btn icon="mdi-close" size="small" @click="removeFile(index)" :disabled="uploading"></v-btn>
          </template>
          <template v-slot:subtitle>
            <div v-if="file.status === 'pending'">
              {{ formatFileSize(file.size) }}
            </div>
            <div v-else-if="file.status === 'uploading'" class="d-flex align-center">
              <v-progress-linear :model-value="file.progress" height="5" color="primary" class="mr-2"></v-progress-linear>
              {{ file.progress }}%
            </div>
            <div v-else-if="file.status === 'success'" class="text-success">
              上传成功
            </div>
            <div v-else-if="file.status === 'error'" class="text-error">
              上传失败: {{ file.error }}
            </div>
          </template>
        </v-list-item>
      </v-list>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';
import { API_BASE_URL } from '../config';

const fileInput = ref(null); // 添加这一行来引用文件输入元素

const props = defineProps({
  taskId: {
    type: String,
    default: ''
  }
});

const emit = defineEmits(['upload-complete']);
const router = useRouter();

const files = ref([]);
const uploading = ref(false);
const isDragging = ref(false);
const currentTaskId = ref(props.taskId);

// 处理文件选择
const handleFileChange = (event) => {
  const selectedFiles = Array.from(event.target.files);
  addFiles(selectedFiles);
  // 重置input，允许重复选择相同文件
  event.target.value = '';
};

// 处理拖放
const onDragOver = () => {
  isDragging.value = true;
};

const onDragLeave = () => {
  isDragging.value = false;
};

const onDrop = (event) => {
  isDragging.value = false;
  const droppedFiles = Array.from(event.dataTransfer.files);
  addFiles(droppedFiles);
};

// 添加文件到列表
const addFiles = (newFiles) => {
  for (const file of newFiles) {
    // 检查文件类型
    const fileExt = file.name.split('.').pop().toLowerCase();
    const allowedTypes = ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'jpg', 'jpeg', 'png'];
    
    if (allowedTypes.includes(fileExt)) {
      files.value.push({
        file: file,
        name: file.name,
        size: file.size,
        type: file.type,
        status: 'pending',
        progress: 0,
        error: ''
      });
    }
  }
};

// 移除文件
const removeFile = (index) => {
  files.value.splice(index, 1);
};

// 获取文件图标
const getFileIcon = (filename) => {
  const ext = filename.split('.').pop().toLowerCase();
  
  switch (ext) {
    case 'pdf':
      return 'mdi-file-pdf';
    case 'doc':
    case 'docx':
      return 'mdi-file-word';
    case 'xls':
    case 'xlsx':
      return 'mdi-file-excel';
    case 'jpg':
    case 'jpeg':
    case 'png':
      return 'mdi-file-image';
    default:
      return 'mdi-file';
  }
};

// 获取文件图标颜色
const getFileIconColor = (filename) => {
  const ext = filename.split('.').pop().toLowerCase();
  
  switch (ext) {
    case 'pdf':
      return 'red';
    case 'doc':
    case 'docx':
      return 'blue';
    case 'xls':
    case 'xlsx':
      return 'green';
    case 'jpg':
    case 'jpeg':
    case 'png':
      return 'purple';
    default:
      return 'grey';
  }
};

// 格式化文件大小
const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

// 上传所有文件
const uploadFiles = async () => {
  if (files.value.length === 0) return null;
  
  uploading.value = true;
  let taskId = currentTaskId.value;
  
  // 如果没有任务ID，先创建一个
  if (!taskId) {
    try {
      const response = await axios.post(`${API_BASE_URL}/api/create-task`);
      taskId = response.data.task_id;
      currentTaskId.value = taskId;
    } catch (error) {
      console.error('创建任务失败:', error);
      uploading.value = false;
      return null;
    }
  }
  
  // 上传所有文件
  for (let i = 0; i < files.value.length; i++) {
    const fileObj = files.value[i];
    
    if (fileObj.status === 'success') continue;
    
    fileObj.status = 'uploading';
    fileObj.progress = 0;
    
    try {
      const formData = new FormData();
      formData.append('file', fileObj.file);
      // formData.append('task_id', taskId);
      
      const response = await axios.post(`${API_BASE_URL}/api/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          fileObj.progress = percentCompleted;
        }
      });
      
      console.log('文件上传响应:', response.data);
      
      // 解析后端返回的task_id和chucking_result
      if (response.data && response.data.task_id) {
        taskId = response.data.task_id;
        currentTaskId.value = taskId;
        console.log('从响应中获取任务ID:', taskId);
      }
      
      // 存储解析结果以备后用
      if (response.data && response.data.chucking_result) {
        fileObj.chuckingResult = response.data.chucking_result;
        console.log('解析结果:', fileObj.chuckingResult);
      }
      
      fileObj.status = 'success';
      fileObj.progress = 100;
    } catch (error) {
      console.error('上传文件失败:', error);
      fileObj.status = 'error';
      fileObj.error = error.response?.data?.error || '上传失败';
    }
  }
  
  uploading.value = false;
  return taskId;
};

// 完成上传并跳转
const completeUpload = async () => {
  const taskId = await uploadFiles();
  
  if (taskId) {
    emit('upload-complete', { taskId });
    router.push(`/comparison/task/${taskId}`);
  } else {
    console.error('未获取到有效的任务ID，无法跳转');
  }
};
</script>

<style scoped>
.multi-file-uploader {
  width: 100%;
}

.upload-area {
  border: 2px dashed #ccc;
  border-radius: 8px;
  background-color: #f9f9f9;
  transition: all 0.3s ease;
}

.upload-area.dragging {
  border-color: #1976d2;
  background-color: rgba(25, 118, 210, 0.05);
}

.file-list {
  max-height: 300px;
  overflow-y: auto;
}
</style>