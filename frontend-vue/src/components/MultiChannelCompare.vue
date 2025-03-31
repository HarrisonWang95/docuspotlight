<template>
    <div class="multi-channel-compare pa-4">
        <div v-if="!schemaData || !channelsData.length" class="d-flex justify-center align-center"
            style="height: 200px;">
            <v-progress-circular indeterminate color="primary"></v-progress-circular>
            <span class="ml-2">加载数据中...</span>
        </div>

        <div v-else>
            <div class="d-flex align-center mb-4">
                <h3 class="text-h6">多渠道解析结果比对</h3>
                <v-spacer></v-spacer>
                <v-btn color="primary" @click="saveDecision" :loading="saving">
                    保存人工核对结果
                </v-btn>
            </div>

            <!-- 上侧区域：展示含有original的字段组 -->
            <div v-if="getOriginalFieldPairs().length > 0" class="mb-6">
                <h4 class="text-subtitle-1 mb-2">格式化字段</h4>
                <v-table density="compact" class="comparison-table">
                    <thead>
                        <tr>
                            <th class="field-column">字段</th>
                            <template v-for="channel in channelsData" :key="channel.channel">
                                <th class="equal-width-column">{{ channel.channel }}</th>
                            </template>
                            <th class="equal-width-column">人工核对结果</th>
                        </tr>
                    </thead>
                    <tbody>
                        <template v-for="(fieldName, index) in getOriginalFieldPairs()" :key="fieldName.original">
                            <!-- 现有的表格行内容保持不变 -->
                            <tr>
                                <!-- 合并显示字段名 -->
                                <td class="field-name" :class="getFieldRowClass(fieldName.original)" @dblclick="zoomToField(fieldName.original)">
                                    {{ fieldName.parsed }}
                                    <v-tooltip activator="parent" location="top">
                                        {{ schemaData.properties[fieldName.parsed].description }}
                                    </v-tooltip>
                                </td>

                                <!-- 原始值 -->
                                <template v-for="(channel, channelIndex) in channelsData"
                                    :key="`${channel.channel}-${channelIndex}`">
                                    <td
                                        :class="[getValueClass(fieldName.parsed, channel.data[fieldName.parsed], channelIndex), 'original-value', 'equal-width-column', 'value-cell']">
                                        <div class="original-text clickable-value"
                                            @click="selectValue(fieldName.parsed, channel.data[fieldName.parsed], channel.channel)">
                                            {{ channel.data[fieldName.original] || '未提供' }}
                                        </div>
                                        <div class="parsed-value clickable-value"
                                            @click="selectValue(fieldName.parsed, channel.data[fieldName.parsed], channel.channel)">
                                            {{ formatValue(channel.data[fieldName.parsed]) }}
                                        </div>
                                    </td>
                                </template>

                                <!-- 人工核对结果 -->
                                <td class="equal-width-column">
                                    <component :is="getInputComponent(fieldName.parsed)"
                                        v-model="decisionData[fieldName.parsed]" 
                                        density="compact" 
                                        variant="outlined"
                                        hide-details
                                        :error-messages="validationErrors[fieldName.parsed]"
                                        :type="getInputType(fieldName.parsed)"
                                        :class="getDecisionClass(fieldName.parsed)"
                                        @update:model-value="validateField(fieldName.parsed, $event)"
                                        :items="fieldTypes[fieldName.parsed]?.enum ? 
                                            fieldTypes[fieldName.parsed].enum : 
                                            getChannelValues(fieldName.parsed)"
                                        :placeholder="getDateFormatPlaceholder(fieldName.parsed)"
                                        :date-picker-options="{ format: 'yyyy-MM-dd' }"
                                        :date-format="'yyyy-MM-dd'"
                                        :format="'yyyy-MM-dd'">
                                        <template v-slot:selection="{ item }">
                                            <span>{{ typeof item === 'object' ? item.raw || item.title : item }}</span>
                                        </template>
                                        <template v-slot:item="{ item, props }">
                                            <v-list-item v-bind="props"
                                                :title="typeof item === 'object' ? item.raw || item.title : item"
                                                :subtitle="item.channel ? `来自: ${item.channel}` : ''"
                                                :class="item.channel ? `channel-${getChannelIndex(item.channel)}` : ''"></v-list-item>
                                        </template>
                                    </component>
                                </td>
                            </tr>
                        </template>
                    </tbody>
                </v-table>
            </div>

            <!-- 中侧区域：展示必填字段 -->
            <div v-if="getRequiredFields().length > 0" class="mb-6">
                <h4 class="text-subtitle-1 mb-2">必填字段</h4>
                <v-table density="compact" class="comparison-table">
                    <thead>
                        <tr>
                            <th class="field-column">字段</th>
                            <template v-for="channel in channelsData" :key="channel.channel">
                                <th class="equal-width-column">{{ channel.channel }}</th>
                            </template>
                            <th class="equal-width-column">人工核对结果</th>
                        </tr>
                    </thead>
                    <tbody>
                        <!-- 现有的表格行内容保持不变 -->
                        <template v-for="(fieldName, index) in getRequiredFields()" :key="fieldName">
                            <tr :class="getFieldRowClass(fieldName)">
                                <td class="field-name" @dblclick="zoomToField(fieldName)">
                                    {{ fieldName }}
                                    <v-tooltip activator="parent" location="top">
                                        {{ schemaData.properties[fieldName].description }}
                                    </v-tooltip>
                                </td>

                                <template v-for="(channel, channelIndex) in channelsData"
                                    :key="`${channel.channel}-${channelIndex}`">
                                    <td
                                        :class="[getValueClass(fieldName, channel.data[fieldName], channelIndex), 'equal-width-column', 'value-cell']">
                                        <div class="clickable-value"
                                            @click="selectValue(fieldName, channel.data[fieldName], channel.channel)">
                                            {{ formatValue(channel.data[fieldName]) }}
                                        </div>
                                    </td>
                                </template>

                                <td class="equal-width-column">
                                    <component :is="getInputComponent(fieldName)"
                                        v-model="decisionData[fieldName]" 
                                        density="compact" 
                                        variant="outlined"
                                        hide-details
                                        :error-messages="validationErrors[fieldName]"
                                        :type="getInputType(fieldName)"
                                        :class="getDecisionClass(fieldName)"
                                        @update:model-value="validateField(fieldName, $event)"
                                        :items="fieldTypes[fieldName]?.enum || getChannelValues(fieldName)"
                                        :placeholder="getDateFormatPlaceholder(fieldName)"
                                        :format="fieldTypes[fieldName]?.format === 'date' ? fieldTypes[fieldName].dateFormat : undefined">
                                        <template v-slot:selection="{ item }">
                                            <span>{{ typeof item === 'object' ? item.raw || item.title : item }}</span>
                                        </template>
                                        <template v-slot:item="{ item, props }">
                                            <v-list-item v-bind="props"
                                                :title="typeof item === 'object' ? item.raw || item.title : item"
                                                :subtitle="item.channel ? `来自: ${item.channel}` : ''"
                                                :class="item.channel ? `channel-${getChannelIndex(item.channel)}` : ''"></v-list-item>
                                        </template>
                                    </component>
                                </td>
                            </tr>
                        </template>
                    </tbody>
                </v-table>
            </div>

            <!-- 下侧区域：展示其他字段 -->
            <div v-if="getOtherFields().length > 0">
                <h4 class="text-subtitle-1 mb-2">其他字段</h4>
                <v-table density="compact" class="comparison-table">
                    <thead>
                        <tr>
                            <th class="field-column">字段</th>
                            <template v-for="channel in channelsData" :key="channel.channel">
                                <th class="equal-width-column">{{ channel.channel }}</th>
                            </template>
                            <!-- 移除人工核对结果列标题 -->
                        </tr>
                    </thead>
                    <tbody>
                        <template v-for="(fieldName, index) in getOtherFields()" :key="fieldName">
                            <tr :class="getFieldRowClass(fieldName)">
                                <td class="field-name" @dblclick="zoomToField(fieldName)">
                                    {{ fieldName }}
                                    <v-tooltip activator="parent" location="top">
                                        {{ schemaData.properties[fieldName].description }}
                                    </v-tooltip>
                                </td>

                                <template v-for="(channel, channelIndex) in channelsData"
                                    :key="`${channel.channel}-${channelIndex}`">
                                    <td
                                        :class="[getValueClass(fieldName, channel.data[fieldName]), 'equal-width-column', 'value-cell']">
                                        <div class="clickable-value"
                                            @click="selectValue(fieldName, channel.data[fieldName], channel.channel)">
                                            {{ formatValue(channel.data[fieldName]) }}
                                        </div>
                                    </td>
                                </template>
                                <!-- 移除人工核对结果列内容 -->
                            </tr>
                        </template>
                    </tbody>
                </v-table>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue';
import axios from 'axios';
import { API_BASE_URL } from '../config';

const props = defineProps({
    taskId: {
        type: String,
        required: true
    }
});

const emit = defineEmits(['decision-saved', 'zoom-to-field']);

const schemaData = ref(null);
const channelsData = ref([]);
const decisionData = ref({});
const defaultDecisionData = ref({}); // 保存初始决策数据，保持不变
const onThePage = ref([]);
const saving = ref(false);
const schemaOrder = ref([]); // 存储schema中字段的顺序
const fieldTypes = ref({}); // 存储字段类型信息
const requiredFields = ref([]); // 存储必填字段
const validationErrors = ref({}); // 存储字段验证错误信息
const normBoxData = ref({}); // 存储norm_box数据

// 设置CSS变量以确保列宽一致
const setCssColumnVariable = () => {
    if (channelsData.value.length) {
        // 计算列数（渠道数 + 人类决策列）
        const columnCount = channelsData.value.length + 1;
        document.documentElement.style.setProperty('--column-count', columnCount.toString());
    }
};

// 加载数据
onMounted(async () => {
    try {
        // 加载Schema
        const schemaResponse = await axios.get(`${API_BASE_URL}/api/schema/${props.taskId}`);
        schemaData.value = schemaResponse.data;

        // 提取schema中的字段顺序和类型信息
        if (schemaData.value && schemaData.value.properties) {
            // 保存字段顺序
            schemaOrder.value = Object.keys(schemaData.value.properties);

            // 保存字段类型信息并处理日期格式
            Object.keys(schemaData.value.properties).forEach(field => {
                const fieldSchema = schemaData.value.properties[field];
                fieldTypes.value[field] = fieldSchema;

                // 如果是日期字段，处理日期格式转换
                if (fieldSchema.format === 'date') {
                    fieldTypes.value[field].dateFormat = fieldSchema.dateFormat;
                    
                    // 如果有初始值，将字符串转换为Date对象
                    if (decisionData.value[field]) {
                        const dateStr = decisionData.value[field];
                        try {
                            decisionData.value[field] = parse(dateStr, fieldSchema.dateFormat, new Date());
                        } catch (error) {
                            console.error(`日期解析错误: ${dateStr}`, error);
                            decisionData.value[field] = null;
                        }
                    }
                }
            });

            // 保存必填字段
            requiredFields.value = schemaData.value.required || [];
        }

        // 加载多渠道解析结果
        // 修改 API 调用，使用 taskId
        // 加载多渠道解析结果
        const resultsResponse = await axios.get(`${API_BASE_URL}/api/multi-channel-results/${props.taskId}`);
        console.log('API 返回的完整数据:', resultsResponse.data);
        console.log('norm_box 数据:', resultsResponse.data.norm_box);
        
        channelsData.value = resultsResponse.data.channels;
        onThePage.value = resultsResponse.data.onThePage;
        normBoxData.value = resultsResponse.data.normBox || {}; // 存储norm_box数据
        console.log('normBoxData:', normBoxData.value);
        // 设置默认决策数据
        decisionData.value = resultsResponse.data.defaultDecision || {};
        defaultDecisionData.value = JSON.parse(JSON.stringify(resultsResponse.data.defaultDecision || {}));

        // 如果没有默认决策数据，则设置默认值为第一个渠道的值
        if (channelsData.value.length > 0) {
            const firstChannelData = channelsData.value[0].data;
            Object.keys(firstChannelData).forEach(key => {
                if (!decisionData.value[key]) {
                    decisionData.value[key] = firstChannelData[key];
                    defaultDecisionData.value[key] = firstChannelData[key];
                }
            });
        }

        // 初始化验证错误信息对象
        Object.keys(decisionData.value).forEach(field => {
            validationErrors.value[field] = '';
        });

        // 设置CSS变量
        setCssColumnVariable();
    } catch (error) {
        console.error('加载数据失败:', error);
    }
});

// 获取日期格式占位符
const getDateFormatPlaceholder = (fieldName) => {
    if (!fieldTypes.value[fieldName]) return '';

    //   const fieldType = fieldTypes.value[fieldName];
    //   if (fieldType.format === 'date') {
    //     return `格式: ${fieldType.dateFormat || 'yyyy-mm-dd'}`;
    //   }
    return '';
};

// 修改 getInputComponent 方法
const getInputComponent = (fieldName) => {
    if (!fieldTypes.value[fieldName]) return 'v-text-field';

    const fieldType = fieldTypes.value[fieldName];

    if (fieldType.type === 'string' && fieldType.format === 'date') {
        return 'v-text-field'; // 使用文本框处理日期
    } else if (fieldType.enum) {
        return 'v-select';
    }

    return 'v-text-field';
};

// 获取对应的解析后字段名
const getCorrespondingField = (originalField) => {
    if (!originalField.startsWith('original')) return null;

    // 移除'original'前缀，并将首字母小写
    const fieldName = originalField.substring(8);
    const correspondingField = fieldName.charAt(0).toLowerCase() + fieldName.slice(1);

    // 检查该字段是否存在于schema中
    return schemaData.value && schemaData.value.properties[correspondingField] ? correspondingField : null;
};

// 获取对应的原始字段名
const getOriginalField = (parsedField) => {
    if (parsedField.startsWith('original')) return null;

    // 添加'original'前缀，并将首字母大写
    const originalField = 'original' + parsedField.charAt(0).toUpperCase() + parsedField.slice(1);

    // 检查该字段是否存在于schema中
    return schemaData.value && schemaData.value.properties[originalField] ? originalField : null;
};

// 检查字段是否为对应字段（即是否有original前缀的对应字段）
const isCorrespondingField = (fieldName) => {
    if (fieldName.startsWith('original')) return false;

    const originalField = 'original' + fieldName.charAt(0).toUpperCase() + fieldName.slice(1);
    return schemaData.value && schemaData.value.properties[originalField];
};

// 获取所有original字段和对应的解析字段对，按schema顺序排序
const getOriginalFieldPairs = () => {
    if (!schemaData.value) return [];

    const pairs = [];
    // 使用schemaOrder确保按照schema中的顺序
    schemaOrder.value.forEach(fieldName => {
        if (fieldName.startsWith('original')) {
            const parsedField = getCorrespondingField(fieldName);
            if (parsedField) {
                pairs.push({
                    original: fieldName,
                    parsed: parsedField
                });
            }
        }
    });

    return pairs;
};

// 获取所有必填字段（排除含original的字段组），按schema顺序排序
const getRequiredFields = () => {
    if (!schemaData.value || !requiredFields.value) return [];

    return schemaOrder.value.filter(fieldName => {
        return requiredFields.value.includes(fieldName) &&
               !fieldName.startsWith('original') &&
               !isCorrespondingField(fieldName);
    });
};

// 获取所有非original字段且非必填字段的普通字段，按schema顺序排序
const getOtherFields = () => {
    if (!schemaData.value) return [];

    // 使用schemaOrder确保按照schema中的顺序
    return schemaOrder.value.filter(fieldName => {
        return !fieldName.startsWith('original') &&
               !isCorrespondingField(fieldName) &&
               !requiredFields.value.includes(fieldName);
    });
};

// 验证字段值是否符合schema
const validateField = (fieldName, value) => {
    if (!fieldTypes.value[fieldName]) return { isValid: true, errorMessage: '' };

    const fieldType = fieldTypes.value[fieldName];
    let isValid = true;
    let errorMessage = '';

    // 检查必填字段
    if (requiredFields.value.includes(fieldName) && (value === null || value === undefined || value === '')) {
        isValid = false;
        errorMessage = '此字段为必填项';
        return { isValid, errorMessage };
    }

    // 如果值为空且不是必填字段，则视为有效
    if (value === null || value === undefined || value === '') {
        return { isValid, errorMessage };
    }

    // 根据字段类型进行验证
    switch (fieldType.type) {
        case 'number':
            // 检查是否为数字
            if (isNaN(Number(value))) {
                isValid = false;
                errorMessage = '请输入有效的数字';
            }
            break;
        case 'string':
            // 检查日期格式
            if (fieldType.format === 'date') {
                const dateRegex = /^\d{4}-\d{2}-\d{2}$/;
                if (!dateRegex.test(value)) {
                    isValid = false;
                    errorMessage = '请输入有效的日期格式 (YYYY-MM-DD)';
                }
            }
            // 检查正则表达式模式
            if (fieldType.pattern) {
                const patternRegex = new RegExp(fieldType.pattern);
                if (!patternRegex.test(value)) {
                    isValid = false;
                    errorMessage = '输入格式不符合要求';
                }
            }
            // 检查枚举值
            if (fieldType.enum && !fieldType.enum.includes(value)) {
                isValid = false;
                errorMessage = '请选择有效的选项';
            }
            break;
    }

    // 添加日期格式验证
    if (fieldType.dateFormat) {
        const formatRegex = {
            'YYYY-MM-DD': /^\d{4}-\d{2}-\d{2}$/,
            'YYYYMM': /^\d{6}$/
        }[fieldType.dateFormat];

        if (formatRegex && !formatRegex.test(value)) {
            isValid = false;
            errorMessage = `请按照 ${fieldType.dateFormat} 格式输入`;
        }
    }

    return { isValid, errorMessage };
};

// 验证所有字段
const validateAllFields = () => {
    let isAllValid = true;

    Object.keys(decisionData.value).forEach(field => {
        const { isValid, errorMessage } = validateField(field, decisionData.value[field]);
        validationErrors.value[field] = errorMessage;
        if (!isValid) isAllValid = false;
    });

    return isAllValid;
};

// 获取字段的输入组件类型
const getInputType = (fieldName) => {
    if (!fieldTypes.value[fieldName]) return 'text';

    const fieldType = fieldTypes.value[fieldName];

    if (fieldType.type === 'number') {
        return 'number';
    } else if (fieldType.type === 'string') {
        if (fieldType.format === 'date') {
            return 'date';
        } else if (fieldType.enum) {
            return 'select';
        } else if (fieldType.pattern) {
            // 特殊处理账期格式 YYYYMM
            if (fieldType.pattern.includes('\\d{6}')) {
                return 'month';
            }
        }
    }

    return 'text';
};

// 格式化显示值
const formatValue = (value) => {
    if (value === null || value === undefined) return '未提供';
    if (value instanceof Date) {
        // 根据字段类型选择格式化方式
        const fieldType = fieldTypes.value[fieldName];
        if (fieldType?.dateFormat === 'YYYYMM') {
            return value.getFullYear().toString() + 
                   (value.getMonth() + 1).toString().padStart(2, '0');
        } else {
            return value.toISOString().split('T')[0]; // YYYY-MM-DD
        }
    }
    if (typeof value === 'number') return value.toString();
    return value;
};

// 获取字段行的CSS类
const getFieldRowClass = (fieldName) => {
    // 检查字段是否在原文中检索到
    const isOnPage = onThePage.value.includes(fieldName);

    // 检查所有渠道的值是否一致
    const allValuesConsistent = areAllValuesConsistent(fieldName);

    if (isOnPage) {
        return 'field-on-page-consistent';
    } else if (!isOnPage && allValuesConsistent) {
        return 'field-not-on-page-consistent';
    } else {
        return 'field-inconsistent';
    }
};

// 检查所有渠道的值是否一致
const areAllValuesConsistent = (fieldName) => {
    if (channelsData.value.length <= 1) return true;

    const firstValue = channelsData.value[0].data[fieldName];
    return channelsData.value.every(channel => {
        const value = channel.data[fieldName];

        // 对于数字类型，考虑精度问题
        if (typeof firstValue === 'number' && typeof value === 'number') {
            return Math.abs(firstValue - value) < 0.001;
        }

        return firstValue === value;
    });
};

// 获取值单元格的CSS类
const getValueClass = (fieldName, value, channelIndex) => {
    // 检查该值是否与决策值匹配
    const allValuesConsistent = areAllValuesConsistent(fieldName);
    if ((defaultDecisionData.value[fieldName] === value) && allValuesConsistent) {
        return 'field-on-page-consistent';
    }
    return `channel-${channelIndex}`;
};

// 获取渠道的索引
const getChannelIndex = (channelName) => {
    return channelsData.value.findIndex(channel => channel.channel === channelName);
};

// 获取决策值的CSS类
const getDecisionClass = (fieldName) => {
    // 查找决策值匹配的渠道
    const allValuesConsistent = areAllValuesConsistent(fieldName);
    const value = decisionData.value[fieldName];  // 使用当前的 decisionData
    if (!value) return 'field-inconsistent';

    for (let i = 0; i < channelsData.value.length; i++) {
        const channel = channelsData.value[i];
        if (channel.data[fieldName] === value) {
            if (allValuesConsistent) {
                return 'field-on-page-consistent';
            } else {
                return `channel-${i}`;
            }
        }
    }
    
    return '';
};

    // 获取字段的所有渠道值（用于下拉选择）
    const getChannelValues = (fieldName) => {
        const values = [];
        const uniqueValues = new Set();
    
        channelsData.value.forEach(channel => {
            const value = channel.data[fieldName];
            if (value !== null && value !== undefined && !uniqueValues.has(value)) {
                uniqueValues.add(value);
                values.push({
                    title: value,
                    value: value,
                    channel: channel.channel,
                    raw: value
                });
            }
        });
    
        return values;
    };

    // 选择渠道值
    const selectValue = (fieldName, value, channelName) => {
        if (value !== null && value !== undefined) {
            decisionData.value[fieldName] = value;
        }
    };

    // 保存人工核对结果
    const saveDecision = async () => {
        // 先验证所有字段
        const isValid = validateAllFields();
        if (!isValid) {
            alert('表单验证失败，请检查输入内容');
            return;
        }

        saving.value = true;
        try {
            const response = await axios.post(`${API_BASE_URL}/api/save-decision`, {
                document_id: props.documentId,
                decision: decisionData.value
            });

            emit('decision-saved', decisionData.value);
            alert('人工核对结果已保存');
            
            // 将JSON数据下载到本地
            const jsonData = JSON.stringify(decisionData.value, null, 2);
            
            try {
                const blob = new Blob([jsonData], { type: 'application/json' });
                const url = URL.createObjectURL(blob);
                
                const link = document.createElement('a');
                link.href = url;
                link.download = `decision-${props.taskId || 'data'}-${new Date().toISOString().slice(0, 10)}.json`;
                
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                URL.revokeObjectURL(url);
            } catch (error) {
                console.error('下载JSON文件时出错:', error);
            }
        } catch (error) {
            console.error('保存人工核对结果失败:', error);
            alert('保存人工核对结果失败');
        } finally {
            saving.value = false;
        }
    };
const zoomToField = (fieldName) => {
    // 调试输出
    console.log('字段名称:', fieldName);
    console.log('normBoxData:', normBoxData.value);
    console.log('该字段的 normBox 数据:', normBoxData.value?.[fieldName]);
    console.log('渠道数据:', channelsData.value);
    
    // 检查是否有norm_box数据
    if (!normBoxData.value || !normBoxData.value[fieldName]) {
        console.log('未找到 normBox 数据');
        emit('zoom-to-field', null);
        return;
    }
    
    // 获取字段对应的norm_box数据
    const normBox = normBoxData.value[fieldName][0]; // 取第一个坐标框
    console.log('选中的 normBox:', normBox);
    
    if (!normBox || normBox.length !== 4) {
        console.log('normBox 数据格式不正确');
        emit('zoom-to-field', null);
        return;
    }
    
    // 计算矩形区域
    const rect = {
        x0: normBox[0] * 1000, // 转换为像素坐标
        y0: normBox[1] * 1000,
        x1: normBox[2] * 1000,
        y1: normBox[3] * 1000
    };
    
    // 发送事件到父组件
    emit('zoom-to-field', rect);
};
</script>

<style scoped>
.multi-channel-compare {
    width: 100%;
    overflow-x: auto;
}

.comparison-table {
    min-width: 100%;
    border-collapse: collapse;
    table-layout: fixed; /* 添加这行，强制使用固定表格布局 */
}

.field-name {
    position: relative;
    font-weight: 1000;
    min-width: 150px;
    width: 150px; /* 添加固定宽度 */
}

.equal-width-column {
    width: calc((100% - 150px) / var(--column-count, 3));
    min-width: 120px;
    max-width: none;
    padding: 0 !important; /* 移除单元格的内边距 */
}

/* 基础样式 */
.equal-width-column :deep(.v-input) {
    margin: 0;
    padding: 0;
    height: 100%;
}

.equal-width-column :deep(.v-input__control) {
    height: 100%;
}

.equal-width-column :deep(.v-field) {
    height: 100%;
    border-radius: 0;
}

.equal-width-column :deep(.v-field__field) {
    padding: 0 !important;
}

.equal-width-column :deep(.v-field__input) {
    padding: 4px !important;
    min-height: 36px;
    height: 100%;
}

.equal-width-column :deep(.v-field__outline) {
    border: none !important;
}

/* 格式化字段区域特定样式 */
.mb-6:first-of-type .equal-width-column :deep(.v-field__input) {
    background-color: rgba(0, 0, 0, 0.02); /* 稍微区分背景色 */
}

/* 必填字段区域特定样式 */
.mb-6:nth-of-type(2) .equal-width-column :deep(.v-field__input) {
    background-color: rgba(0, 0, 0, 0.01); /* 稍微区分背景色 */
}

/* 字段行着色 */
.field-on-page-consistent {
    background-color: rgba(144, 238, 144, 0.2);
    /* 浅绿色 */
}

.field-not-on-page-consistent {
    background-color: rgba(255, 215, 0, 0.2);
    /* 浅黄色 */
}

.field-inconsistent {
    background-color: rgba(255, 182, 193, 0.2);
    /* 浅红色 */
}

/* 值单元格着色 */
.value-matched-decision {
    background-color: rgba(225, 214, 54, 0.3);
    /* 浅蓝色 */
}

/* 渠道颜色 */

.channel-0 {
    border-left: 3px solid #1E88E5 !important;
    /* 蓝色 */
    background-color: #1E88E51A;
    /* 10% 不透明度 */
}

.channel-1 {
    border-left: 3px solid #87a043 !important;
    /* 绿色 */
    background-color: #87a0431A;
    /* 10% 不透明度 */
}

.channel-2 {
    border-left: 3px solid #FB8C00 !important;
    /* 橙色 */
    background-color: #FB8C001A;
    /* 10% 不透明度 */
}

.channel-3 {
    border-left: 3px solid #E53935 !important;
    /* 红色 */
    background-color: #E539351A;
    /* 10% 不透明度 */
}

.channel-4 {
    border-left: 3px solid #8E24AA !important;
    /* 紫色 */
    background-color: #8E24AA1A;
    /* 10% 不透明度 */
}

/* 原始值和解析值样式 - 上侧区域置灰变小 */
.original-value {
    position: relative;
    padding-bottom: 24px !important;
}

.original-text {
    font-size: 0.85rem;
    font-style: italic;
    color: #666;
}

.parsed-value {
    position: absolute;
    bottom: 4px;
    left: 12px;
    font-size: 1.2rem;
    color: #010101;

}

/* 下侧区域置黑变大 */
.value-cell .clickable-value {
    font-size: 1.05rem;
    /* color: #000; */
    font-weight: 500;
}

/* 可点击值样式 */
.clickable-value {
    cursor: pointer;
    padding: 4px;
    border-radius: 4px;
    transition: background-color 0.2s;
}

.clickable-value:hover {
    background-color: rgba(0, 0, 0, 0.05);
}

/* 决策选择器样式 */
.decision-select {
    margin-bottom: 4px;
}

/* 验证错误样式 */
.validation-error {
    color: #ff5252;
    font-size: 0.75rem;
    margin-top: 2px;
}
</style>
