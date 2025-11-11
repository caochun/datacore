# Web UI 快速启动指南

## 前置条件

1. 确保已运行 `dbt run` 生成所有数据模型
2. 确保 `datacore.duckdb` 文件存在于项目根目录
3. Python 3.8+ 和 Node.js 16+ 已安装

## 方式一：生产模式（推荐）- 前后端合并

前后端通过同一个端口提供服务，适合生产环境：

```bash
cd web_ui/backend
./build_and_serve.sh
```

访问地址：**http://localhost:8090**

## 方式二：开发模式 - 前后端分离

适合开发调试，前端支持热更新：

```bash
cd web_ui
./start.sh
```

访问地址：
- **前端应用**: http://localhost:3000
- **后端API**: http://localhost:8090
- **API文档**: http://localhost:8090/docs

## 方式三：手动启动

### 1. 构建前端

```bash
cd web_ui/frontend
npm install
npm run build
```

### 2. 启动后端（包含前端）

```bash
cd web_ui/backend
source ../../venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8090 --reload
```

访问地址：**http://localhost:8090**

## 功能页面

1. **首页概览** (`/`) - 数据统计、质量趋势
2. **数据资产目录** (`/catalog`) - 浏览所有数据表
3. **数据溯源** (`/lineage`) - 交互式溯源关系图
4. **数据质量** (`/quality`) - 质量监控和告警
5. **数据浏览** (`/explorer`) - 数据预览和查询
6. **业务报表** (`/reports`) - 收入报表、车流趋势

## 故障排查

### 后端无法连接数据库

检查 `datacore.duckdb` 文件路径是否正确。

### 前端无法连接后端

检查后端是否在 8090 端口运行，查看 `vite.config.js` 中的代理配置。

### 依赖安装失败

- Python: 使用虚拟环境 `source ../../venv/bin/activate`
- Node: 使用国内镜像 `npm config set registry https://registry.npmmirror.com`

### 生产模式前端不显示

确保已运行 `npm run build` 生成 `frontend/dist` 目录。
