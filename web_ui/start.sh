#!/bin/bash
# 启动Web UI的便捷脚本

echo "启动数据中台Web UI..."

# 检查数据库文件
if [ ! -f "../datacore.duckdb" ]; then
    echo "错误: 找不到 datacore.duckdb 数据库文件"
    echo "请先运行 dbt run 生成数据模型"
    exit 1
fi

# 启动后端
echo "启动后端服务..."
cd backend
source ../../venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8090 --reload &
BACKEND_PID=$!

# 等待后端启动
sleep 3

# 启动前端
echo "启动前端服务..."
cd ../frontend
if [ ! -d "node_modules" ]; then
    echo "安装前端依赖..."
    npm install
fi
npm run dev &
FRONTEND_PID=$!

echo ""
echo "=========================================="
echo "Web UI 启动成功！"
echo "后端API: http://localhost:8090"
echo "前端应用: http://localhost:3000"
echo "API文档: http://localhost:8090/docs"
echo ""
echo "按 Ctrl+C 停止服务"
echo "=========================================="

# 等待用户中断
trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT TERM
wait

