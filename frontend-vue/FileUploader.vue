<template>
  <div class="d-flex flex-column align-center pa-3" style="border: 2px dashed #ccc; border-radius: 8px; background-color: #f9f9f9;">
    <h6 class="text-h6 mb-2">上传文档</h6>
    <p class="text-body-2 text-secondary mb-2">支持PDF和图片文件(JPG, PNG)</p>
    
    <input
      accept=".pdf,.jpg,.jpeg,.png"
      style="display: none"
      id="file-upload"
      type="file"
      @change="handleFileChange"
      :disabled="loading"
    />
    <label for="file-upload">
      <v-btn
        variant="contained"
        :disabled="loading"
      >
        {{ loading ? '上传中...' : '选择文件' }}
      </v-btn>
    </label>
    
    <div v-if="loading" class="d-flex align-center mt-2">
      <v-progress-circular size="24" class="mr-2" indeterminate />
      <span class="text-body-2">正在上传和解析文档...</span>
    </div>
    
    <p v-if="error" class="text-body-2 text-error mt-2">
      {{ error }}
    </p>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import axios from 'axios';
import { API_BASE_URL } from '../config';

const emit = defineEmits(['file-upload']);

const loading = ref(false);
const error = ref('');

const handleFileChange = async (event) => {
  const file = event.target.files[0];
  if (!file) return;

  const allowedTypes = ['application/pdf', 'image/jpeg', 'image/png', 'image/jpg'];
  if (!allowedTypes.includes(file.type)) {
    error.value = '只支持PDF和图片文件(JPG, PNG)';
    return;
  }

  loading.value = true;
  error.value = '';

  try {
    const formData = new FormData();
    formData.append('file', file);

    const response = await axios.post(`${API_BASE_URL}/api/upload`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    // 直接使用上传后的文件名作为文档ID
    const documentId = response.data.filename;
    emit('file-upload', {
      id: documentId,
      name: documentId,
      type: file.type
    });
  } catch (err) {
    console.error('上传文件时出错:', err);
    error.value = '上传文件时出错，请重试';
  } finally {
    loading.value = false;
  }
};
</script>