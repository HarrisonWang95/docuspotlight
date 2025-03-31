# 多渠道解析结果比对系统

这是一个用于比对多个渠道解析结果的可视化系统，支持字段级别的比对、差异标记和人类决策。

## Docker一键部署

本项目支持使用Docker进行一键部署，方便在任何环境中快速启动服务。

### 环境要求

- Docker
- Docker Compose

### 部署步骤

1. 克隆仓库
```bash
git clone <您的GitHub仓库URL>
cd pdf-preview
```

2. 构建并启动服务
```bash
docker-compose up -d
```
3. 环境变量配置，请从火山引擎配置相关服务和key配置，并添加到`backend/.env`文件中：
ARK_API_KEY="f5a2xxxx"
ARK_BASE_URL="https://ark.cn-beijing.volces.com"
VOLC_ACCESSKEY="Axxxxx"
VOLC_SECRETKEY="Wmxxxxxxxx"

4. 访问应用
- 前端界面: http://localhost:8080
- 后端API: http://localhost:5000

### 数据持久化

Docker Compose配置中已设置以下目录的数据持久化：
- `./backend/uploads`: 上传的文件
- `./backend/results`: 处理结果
- `./backend/extract_results`: 提取结果
- `./backend/parse_results`: 解析结果

### 常用命令

```bash
# 查看日志
docker-compose logs

# 停止服务
docker-compose down

# 重新构建（代码修改后）
docker-compose up -d --build
```

## 功能特点

1. **多渠道结果展示**：表格分列显示各渠道的解析结果
2. **双行显示**：原始字段和解析后字段在相邻行显示
3. **字段类型说明**：悬浮显示JSON schema中的字段描述
4. **颜色差异化**：
   - 🟢 绿色：原文有检索到且所有渠道结果一致
   - 🟡 黄色：原文未检索到且所有渠道结果一致
   - 🔴 红色：至少两个渠道的值不同
   - 🔵 蓝色：人工选择值与某渠道值相同
5. **人工核对结果保存**：支持保存人类人工核对结果

## 技术架构

### 前端

- Vue 3 + Vuetify 3
- 多页面路由
- 动态着色引擎
- 字段双行展示系统

### 后端

- Flask API
- 解析结果聚合服务
- 差异分析引擎
- 决策状态追踪

## API接口

### 获取多渠道解析结果

```
GET /api/multi-channel-results/<document_id>
```

返回示例：
```json
{
  "channels": [
    {
      "channel": "c1",
      "data": { ... }
    },
    {
      "channel": "c2",
      "data": { ... }
    }
  ],
  "onThePage": ["originalTotalAmount", "originalInvoiceDate", "originalBillingPeriod", "invoiceNumber"],
  "defaultDecision": { ... }
}
```

### 获取Schema定义

```
GET /api/schema/<schema_name>
```

返回示例：
```json
{
  "type": "object",
  "properties": {
    "originalTotalAmount": {
      "type": "string",
      "description": "账单上显示的原始总金额字符串。"
    },
    ...
  }
}
```

### 保存人工核对结果

```
POST /api/save-decision
```

请求体示例：
```json
{
  "document_id": "invoice.png",
  "decision": { ... }
}
```

## 使用方法

1. 启动后端服务：
   ```
   cd backend
   pip install -r requirements.txt
   python app.py
   ```

2. 启动前端服务：
   ```
   cd frontend-vue
   npm install
   npm run serve
   ```

3. 访问应用：
   - 文档验证页面：http://localhost:8080/
   - 多渠道比对页面：http://localhost:8080/comparison