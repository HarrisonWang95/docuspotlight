# 多阶段构建 - 前端构建阶段
FROM node:16-alpine as frontend-build

WORKDIR /app/frontend

# 复制前端项目文件
COPY frontend-vue/package*.json ./

# 安装依赖
RUN npm install

# 复制源代码
COPY frontend-vue/ ./

# 前端配置已经支持动态API地址，不需要修改

# 构建前端项目
RUN npm run build

# 后端构建阶段
FROM python:3.9-slim

WORKDIR /app

# 复制后端项目文件
COPY backend/ /app/backend/

# 安装后端依赖
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# 创建必要的目录
RUN mkdir -p /app/backend/uploads /app/backend/results /app/backend/extract_results /app/backend/parse_results

# 从前端构建阶段复制构建好的文件
COPY --from=frontend-build /app/frontend/dist /app/frontend/dist

# 复制启动脚本
COPY start.sh /app/
RUN chmod +x /app/start.sh

# 暴露端口
EXPOSE 5050 8080

# 启动服务
CMD ["/app/start.sh"]