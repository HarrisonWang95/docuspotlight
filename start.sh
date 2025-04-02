#!/bin/bash

# 启动前端服务
cd /app/frontend/dist
# 使用更好的静态文件服务器
python3 -c '
import http.server
import socketserver

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if not "." in self.path:
            self.path = "index.html"
        return http.server.SimpleHTTPRequestHandler.do_GET(self)

with socketserver.TCPServer(("", 8080), Handler) as httpd:
    print("前端服务已启动在端口 8080")
    httpd.serve_forever()
' &

# 等待前端服务启动
sleep 2

# 启动后端服务
cd /app/backend
echo "启动后端服务在端口 5050"
exec python app.py