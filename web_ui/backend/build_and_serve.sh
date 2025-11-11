#!/bin/bash
# 构建前端并启动后端服务

cd "$(dirname "$0")"

echo "构建前端应用..."
cd ../frontend
if [ ! -d "node_modules" ]; then
    echo "安装前端依赖..."
    npm install
fi
npm run build

if [ ! -d "dist" ]; then
    echo "错误: 前端构建失败，dist目录不存在"
    exit 1
fi

echo "启动后端服务（包含前端静态文件）..."
cd ../backend
source ../../venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8090 --reload

