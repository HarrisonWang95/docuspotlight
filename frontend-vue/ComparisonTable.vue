<template>
  <div>
    <h4 class="text-subtitle-1 mb-2">{{ title }}</h4>
    <v-table density="compact" class="comparison-table">
      <thead>
        <tr>
          <th class="field-column">字段</th>
          <template v-for="channel in channels" :key="channel.channel">
            <th class="equal-width-column">{{ channel.channel }}</th>
          </template>
          <th v-if="showDecision" class="equal-width-column">人工核对结果</th>
        </tr>
      </thead>
      <tbody>
        <template v-for="(field, index) in fields" :key="getFieldKey(field)">
          <tr :class="getFieldRowClass(getOriginalField(field))">
            <td class="field-name">
              {{ getDisplayFieldName(field) }}
              <v-tooltip activator="parent" location="top">
                {{ getFieldDescription(field) }}
              </v-tooltip>
            </td>

            <template v-for="(channel, channelIndex) in channels" :key="`${channel.channel}-${channelIndex}`">
              <td :class="[
                getValueClass(getParsedField(field), channel.data[getParsedField(field)], channelIndex),
                type === 'original' ? 'original-value' : '',
                'equal-width-column',
                'value-cell'
              ]">
                <!-- 原始值显示（仅用于 original 类型） -->
                <template v-if="type === 'original'">
                  <div class="original-text clickable-value"
                    @click="onValueSelect(getParsedField(field), channel.data[getParsedField(field)], channel.channel)">
                    {{ channel.data[getOriginalField(field)] || '未提供' }}
                  </div>
                  <div class="parsed-value clickable-value"
                    @click="onValueSelect(getParsedField(field), channel.data[getParsedField(field)], channel.channel)">
                    {{ formatValue(channel.data[getParsedField(field)]) }}
                  </div>
                </template>
                
                <!-- 普通值显示 -->
                <template v-else>
                  <div class="clickable-value"
                    @click="onValueSelect(field, channel.data[field], channel.channel)">
                    {{ formatValue(channel.data[field]) }}
                  </div>
                </template>
              </td>
            </template>

            <!-- 人工核对结果列 -->
            <td v-if="showDecision" class="equal-width-column">
              <component :is="getInputComponent(getParsedField(field))"
                v-model="decisionData[getParsedField(field)]"
                density="compact"
                variant="outlined"
                :error-messages="validationErrors[getParsedField(field)]"
                :type="getInputType(getParsedField(field))"
                :class="getDecisionClass(getParsedField(field))"
                @update:model-value="onValidateField(getParsedField(field), $event)"
                :items="getFieldItems(getParsedField(field))"
                :placeholder="getDateFormatPlaceholder(getParsedField(field))"
                :format="getFieldFormat(getParsedField(field))">
                <template v-slot:selection="{ item }">
                  <span>{{ typeof item === 'object' ? item.raw || item.title : item }}</span>
                </template>
                <template v-slot:item="{ item, props }">
                  <v-list-item v-bind="props"
                    :title="typeof item === 'object' ? item.raw || item.title : item"
                    :subtitle="item.channel ? `来自: ${item.channel}` : ''"
                    :class="item.channel ? `channel-${getChannelIndex(item.channel)}` : ''">
                  </v-list-item>
                </template>
              </component>
            </td>
          </tr>
        </template>
      </tbody>
    </v-table>
  </div>
</template>

<script setup>
const props = defineProps({
  title: String,
  type: {
    type: String,
    validator: (value) => ['original', 'required', 'other'].includes(value)
  },
  fields: Array,
  channels: Array,
  showDecision: {
    type: Boolean,
    default: true
  },
  schemaData: Object,
  decisionData: Object,
  validationErrors: Object,
  fieldTypes: Object,
  // 传入所需的方法
  getFieldRowClass: Function,
  getValueClass: Function,
  getInputComponent: Function,
  getInputType: Function,
  formatValue: Function,
  getDateFormatPlaceholder: Function,
  getChannelValues: Function,
  getChannelIndex: Function,
  getDecisionClass: Function,
  validateField: Function
});

const emit = defineEmits(['update:decisionData', 'valueSelect']);

// 辅助方法
const getFieldKey = (field) => {
  return typeof field === 'object' ? field.original : field;
};

const getDisplayFieldName = (field) => {
  return typeof field === 'object' ? field.parsed : field;
};

const getParsedField = (field) => {
  return typeof field === 'object' ? field.parsed : field;
};

const getOriginalField = (field) => {
  return typeof field === 'object' ? field.original : field;
};

const getFieldDescription = (field) => {
  const fieldName = getParsedField(field);
  return props.schemaData.properties[fieldName]?.description;
};

const getFieldItems = (fieldName) => {
  return props.fieldTypes[fieldName]?.enum ? 
    props.fieldTypes[fieldName].enum : 
    props.getChannelValues(fieldName);
};

const getFieldFormat = (fieldName) => {
  return props.fieldTypes[fieldName]?.format === 'date' ? 
    props.fieldTypes[fieldName].dateFormat : 
    undefined;
};

const onValueSelect = (fieldName, value, channel) => {
  emit('valueSelect', { fieldName, value, channel });
};

const onValidateField = (fieldName, value) => {
  props.validateField(fieldName, value);
};
</script>

<style scoped>
/* 保持原有样式 */
</style>