# 数据中台 Web UI

高速公路省级收费中心数据中台的Web可视化界面。

## 功能特性

- ✅ 数据资产目录：浏览所有数据表，查看元数据
- ✅ 数据溯源可视化：交互式溯源关系图
- ✅ 数据质量监控：质量指标、趋势分析、告警
- ✅ 数据浏览：数据预览、字段说明
- ✅ 业务报表：收费收入、车流趋势分析
- ✅ 首页概览：统计信息、质量趋势

## 技术栈

### 后端
- FastAPI：Python Web框架
- DuckDB：数据库连接
- Uvicorn：ASGI服务器

### 前端
- React 18：UI框架
- Ant Design 5：UI组件库
- ECharts：图表可视化
- Cytoscape.js：溯源图可视化
- Vite：构建工具

## 快速开始

### 方式一：生产模式（推荐）- 前后端合并

前后端通过同一个端口（8090）提供服务：

```bash
cd web_ui/backend
./build_and_serve.sh
```

这将：
1. 自动构建前端应用
2. 启动后端服务（包含前端静态文件）
3. 通过 http://localhost:8090 访问完整应用

### 方式二：开发模式 - 前后端分离

适合开发调试，前端支持热更新：

```bash
cd web_ui
./start.sh
```

这将：
1. 启动后端服务（http://localhost:8090）
2. 启动前端开发服务器（http://localhost:3000）

### 手动启动

#### 1. 安装后端依赖

```bash
cd web_ui/backend
source ../../venv/bin/activate
pip install -r requirements.txt
```

#### 2. 构建前端（生产模式）

```bash
cd web_ui/frontend
npm install
npm run build
```

#### 3. 启动后端服务

```bash
cd web_ui/backend
uvicorn main:app --host 0.0.0.0 --port 8090 --reload
```

## API文档

启动后端后，访问 http://localhost:8090/docs 查看Swagger API文档

## 主要API端点

- `GET /api/tables` - 获取数据表列表
- `GET /api/tables/{schema}/{table}` - 获取表详情
- `GET /api/tables/{schema}/{table}/preview` - 获取数据预览
- `GET /api/lineage/graph` - 获取溯源关系图数据
- `GET /api/quality/dashboard` - 获取质量监控看板
- `GET /api/quality/metrics` - 获取质量指标
- `GET /api/reports/revenue` - 获取收入报表
- `GET /api/reports/traffic` - 获取车流趋势
- `GET /api/stats/overview` - 获取统计概览

## 项目结构

```
web_ui/
├── backend/
│   ├── main.py           # FastAPI应用主文件
│   ├── requirements.txt   # Python依赖
│   └── start.sh          # 启动脚本
└── frontend/
    ├── src/
    │   ├── pages/        # 页面组件
    │   ├── components/   # 通用组件
    │   └── utils/        # 工具函数
    ├── package.json      # Node依赖
    └── vite.config.js    # Vite配置
```

## 注意事项

1. 确保 `datacore.duckdb` 数据库文件存在于项目根目录
2. 确保已运行 `dbt run` 生成所有数据模型
3. **生产模式**：只需运行后端，前端已集成
4. **开发模式**：需要同时运行后端和前端

