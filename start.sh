#!/bin/bash

# 启动前端服务
cd /app/frontend/dist
nohup python -m http.server 8080 &

# 等待前端服务启动
sleep 2
echo "前端服务已启动在端口 8080"

# 启动后端服务
cd /app/backend
echo "启动后端服务在端口 5000"
exec python app.py