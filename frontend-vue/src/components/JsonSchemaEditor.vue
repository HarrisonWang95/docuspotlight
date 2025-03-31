<template>
  <div class="json-schema-editor">
    <div class="d-flex align-center mb-4 justify-end">
      <v-btn color="primary" @click="saveSchema" :loading="saving">
        保存 Schema
      </v-btn>
    </div>

    <v-window v-model="currentTab" class="mt-4">
      <v-window-item value="code">
        <v-card class="pa-4">
          <v-textarea
            v-model="jsonText"
            label="JSON Schema"
            rows="20"
            auto-grow
            :error-messages="jsonError"
            @input="validateJson"
            class="monospace-font"
            placeholder="在此粘贴或编辑JSON Schema..."
          ></v-textarea>
        </v-card>
      </v-window-item>

      <!-- 可视化编辑模式 -->
      <v-window-item value="visual">
        <v-card class="pa-4">
          <div v-if="schemaObject">
            <div v-for="(value, key) in schemaObject.properties" :key="key" class="mb-4">
              <h4 class="text-subtitle-1 mb-2">{{ key }}</h4>
              
              <v-row>
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model="schemaObject.properties[key].title"
                    label="标题"
                    density="compact"
                  ></v-text-field>
                </v-col>
                <v-col cols="12" md="6">
                  <v-select
                    v-model="schemaObject.properties[key].type"
                    :items="['string', 'number', 'integer', 'boolean', 'array', 'object']"
                    label="类型"
                    density="compact"
                  ></v-select>
                </v-col>
              </v-row>
              
              <v-row>
                <v-col cols="12">
                  <v-text-field
                    v-model="schemaObject.properties[key].description"
                    label="描述"
                    density="compact"
                  ></v-text-field>
                </v-col>
              </v-row>
              
              <!-- 根据类型显示不同的选项 -->
              <v-row v-if="schemaObject.properties[key].type === 'string'">
                <v-col cols="12" md="6">
                  <v-select
                    v-model="schemaObject.properties[key].format"
                    :items="['', 'date', 'date-time', 'email', 'uri']"
                    label="格式"
                    density="compact"
                  ></v-select>
                </v-col>
                <v-col cols="12" md="6">
                  <v-checkbox
                    v-model="schemaObject.properties[key].required"
                    label="必填"
                    density="compact"
                  ></v-checkbox>
                </v-col>
              </v-row>
              
              <v-divider class="my-2"></v-divider>
            </div>
            
            <v-btn color="secondary" class="mt-4" @click="addProperty">
              添加属性
            </v-btn>
          </div>
          <div v-else class="text-center pa-4">
            <p>无法解析JSON Schema，请检查源码格式</p>
          </div>
        </v-card>
      </v-window-item>
    </v-window>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, computed } from 'vue';
import axios from 'axios';
import { API_BASE_URL } from '../config';

const props = defineProps({
  taskId: {
    type: String,
    required: true
  },
  activeTab: {
    type: String,
    default: 'code'
  }
});

const emit = defineEmits(['schema-saved']);

// 使用 ref 来跟踪内部的 tab 状态
const currentTab = ref(props.activeTab);

// 监听父组件传入的 activeTab 变化
watch(() => props.activeTab, (newVal) => {
  currentTab.value = newVal;
});

// 移除冗余的activeTab变量，只使用currentTab
const jsonText = ref('');
const jsonError = ref('');
const schemaObject = ref(null);
const saving = ref(false);

// 加载Schema数据
onMounted(async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/api/schema/${props.taskId}`);
    jsonText.value = JSON.stringify(response.data, null, 2);
    schemaObject.value = response.data;
  } catch (error) {
    console.error('加载Schema失败:', error);
    // 如果没有现有Schema，创建一个基本结构
    const defaultSchema = {
      "$schema": "http://json-schema.org/draft-07/schema#",
      "title": "文档解析Schema",
      "type": "object",
      "properties": {
        "invoiceNumber": {
          "type": "string",
          "title": "发票号码",
          "description": "发票唯一标识号码"
        },
        "invoiceDate": {
          "type": "string",
          "format": "date",
          "title": "发票日期",
          "description": "发票开具日期"
        }
      },
      "required": ["invoiceNumber", "invoiceDate"]
    };
    
    jsonText.value = JSON.stringify(defaultSchema, null, 2);
    schemaObject.value = defaultSchema;
  }
});

// 验证JSON格式
const validateJson = () => {
  try {
    if (jsonText.value.trim()) {
      schemaObject.value = JSON.parse(jsonText.value);
      jsonError.value = '';
    } else {
      schemaObject.value = null;
    }
  } catch (e) {
    jsonError.value = '无效的JSON格式';
    schemaObject.value = null;
  }
};

// 监听可视化编辑的变化，更新JSON文本
watch(schemaObject, (newVal) => {
  if (newVal && currentTab.value === 'visual') {
    jsonText.value = JSON.stringify(newVal, null, 2);
  }
}, { deep: true });

// 保存Schema
const saveSchema = async () => {
  if (jsonError.value) {
    alert('请先修复JSON格式错误');
    return;
  }
  
  saving.value = true;
  try {
    const schema = currentTab.value === 'code' ? JSON.parse(jsonText.value) : schemaObject.value;
    
    const response = await axios.post(`${API_BASE_URL}/api/schema/${props.taskId}`, schema);
    
    emit('schema-saved', {
      taskId: props.taskId,
      schema: schema
    });
    
    alert('Schema保存成功');
    // 使用 window.location.href 重新导航到当前页面
    window.location.href = window.location.href;
  } catch (error) {
    console.error('保存Schema失败:', error);
    alert(`保存失败: ${error.response?.data?.error || error.message}`);
  } finally {
    saving.value = false;
  }
};
</script>

<style scoped>
.json-schema-editor {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.monospace-font {
  font-family: monospace;
}
</style>