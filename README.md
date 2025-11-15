# 高速公路省级收费中心数据中台

基于 dbt 和 DuckDB 构建的现代化数据中台项目，专注于元数据管理、数据质量管理和数据资产管理。

## 📋 目录

- [项目理念](#项目理念)
- [系统架构](#系统架构)
- [快速开始](#快速开始)
- [详细说明](#详细说明)
- [项目结构](#项目结构)

## 🎯 项目理念

### 核心设计思想

本项目遵循**数据中台**的设计理念，旨在构建一个统一、规范、高质量的数据服务平台。

#### 1. **数据分层治理**
采用经典的数据仓库分层架构（Staging → ODS → DWD → DWS → ADS），确保数据从原始到应用的清晰流转路径，每一层都有明确的职责和规范。

#### 2. **元数据驱动**
- **自动化元数据管理**：通过 dbt 的 `graph` 对象自动提取表结构、字段信息、数据溯源关系
- **业务元数据**：在 `schema.yml` 中定义业务域、数据源、负责人等业务属性
- **中文表名和字段名**：支持中英文对照，提升业务人员使用体验

#### 3. **数据质量保障**
- **多层次质量检查**：完整性、准确性、一致性、参照完整性
- **质量监控看板**：实时监控数据质量指标和趋势
- **自动化测试**：通过 dbt 测试框架实现数据质量自动化验证

#### 4. **数据资产化**
- **资产目录**：统一管理所有数据资产
- **资产评估**：资产等级、使用频率、数据新鲜度等维度评估
- **数据溯源**：完整的数据流转链路追踪

#### 5. **开发即文档**
- **代码即配置**：所有数据模型、测试、元数据都通过代码定义
- **版本控制**：所有变更可追溯、可回滚
- **自动化文档**：dbt 自动生成数据文档

## 🏗️ 系统架构

### 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                      Web UI 层                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ 首页概览 │  │ 资产目录 │  │ 数据溯源 │  │ 数据质量 │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│  ┌──────────┐  ┌──────────┐                                │
│  │ 数据浏览 │  │ 业务报表 │                                │
│  └──────────┘  └──────────┘                                │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    API 服务层 (FastAPI)                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ 表管理   │  │ 溯源查询 │  │ 质量监控 │  │ 报表服务 │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   数据建模层 (dbt)                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ 模型定义 │  │ 测试定义 │  │ 宏定义   │  │ 元数据   │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   数据存储层 (DuckDB)                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Staging  │  │   ODS    │  │   DWD    │  │   DWS    │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│  ┌──────────┐  ┌──────────┐                                │
│  │   ADS    │  │ Metadata │                                │
│  └──────────┘  └──────────┘                                │
└─────────────────────────────────────────────────────────────┘
```

### 数据分层架构

```
原始数据 (raw)
    │
    ▼
┌─────────────────┐
│  Staging 层     │  数据清洗、标准化、异常值处理
│  (View)         │
└─────────────────┘
    │
    ▼
┌─────────────────┐
│  ODS 层         │  操作数据存储，关联字典表，增加业务字段
│  (Table)        │
└─────────────────┘
    │
    ▼
┌─────────────────┐
│  DWD 层         │  明细数据层，业务分类和维度扩展
│  (Table)        │
└─────────────────┘
    │
    ▼
┌─────────────────┐
│  DWS 层         │  汇总数据层，按维度汇总统计
│  (Table)        │
└─────────────────┘
    │
    ▼
┌─────────────────┐
│  ADS 层         │  应用数据服务层，面向业务应用
│  (Table)        │
└─────────────────┘
```

### 技术架构

#### 后端技术栈
- **dbt (Data Build Tool)**：数据建模和转换工具
- **DuckDB**：高性能分析型数据库
- **FastAPI**：现代 Python Web 框架
- **Uvicorn**：ASGI 服务器

#### 前端技术栈
- **React 18**：UI 框架
- **Ant Design 5**：企业级 UI 组件库
- **ECharts**：数据可视化图表库
- **Cytoscape.js**：图可视化库（用于数据溯源图）
- **Vite**：前端构建工具

### 核心组件

#### 1. 元数据管理
- **表信息管理** (`meta_table_info`)：自动提取所有表的元数据
- **字段信息管理** (`meta_column_info`)：自动提取所有字段的元数据（含中文名）
- **数据溯源** (`meta_data_lineage`)：自动生成数据流转关系
- **数据字典** (`meta_data_dictionary`)：统一管理业务字典
- **资产目录** (`meta_data_asset_catalog`)：数据资产清单和评估

#### 2. 数据质量管理
- **质量测试**：完整性、准确性、一致性、参照完整性测试
- **质量指标** (`meta_data_quality_metrics`)：质量得分和趋势
- **质量监控看板** (`ads_quality_monitoring_dashboard`)：实时质量监控

#### 3. Web UI
- **首页概览**：数据统计、质量趋势
- **数据资产目录**：浏览所有数据表，查看元数据
- **数据溯源**：交互式溯源关系图
- **数据质量**：质量监控和告警
- **数据浏览**：数据预览和查询
- **业务报表**：收入报表、车流趋势分析

## 🚀 快速开始

### 前置要求

- Python 3.8+
- Node.js 16+
- pip
- npm 或 yarn

### 1. 环境准备

#### 1.1 创建 Python 虚拟环境

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate
```

#### 1.2 安装 Python 依赖

```bash
# 安装所有依赖（dbt + 后端服务）
pip install -r requirements.txt
```

#### 1.3 安装前端依赖

```bash
cd web_ui/frontend
npm install
cd ../..
```

### 2. 数据准备

#### 2.1 生成测试数据

```bash
# 确保虚拟环境已激活
source venv/bin/activate

# 运行测试数据生成脚本
python scripts/generate_test_data.py
```

这将生成：
- 收费交易原始数据
- 收费站数据
- 车型字典数据
- 支付方式字典数据

### 3. 运行 dbt 数据模型

#### 3.1 配置 dbt

确保 `profiles.yml` 配置正确（通常已配置好）：

```yaml
datacore:
  target: dev
  outputs:
    dev:
      type: duckdb
      path: "datacore.duckdb"
      schema: main
```

#### 3.2 运行数据模型

```bash
# 运行所有模型
dbt run

# 运行数据质量测试
dbt test

# 生成文档（可选）
dbt docs generate
dbt docs serve  # 在浏览器中查看文档
```

#### 3.3 运行特定层级的模型

```bash
# 只运行 staging 层
dbt run --select staging.*

# 只运行元数据模型
dbt run --select metadata.*

# 运行特定模型
dbt run --select dwd_toll_transaction_detail
```

### 4. 启动 Web UI

#### 方式一：生产模式（推荐）

前后端通过同一个端口（8090）提供服务：

```bash
cd web_ui/backend
./build_and_serve.sh
```

这将：
1. 自动构建前端应用
2. 启动后端服务（包含前端静态文件）
3. 通过 http://localhost:8090 访问完整应用

#### 方式二：开发模式

适合开发调试，前端支持热更新：

```bash
cd web_ui
./start.sh
```

这将：
1. 启动后端服务（端口 8090）
2. 启动前端开发服务器（端口 3000）
3. 前端通过代理访问后端 API

访问地址：
- 前端应用：http://localhost:3000
- 后端 API：http://localhost:8090
- API 文档：http://localhost:8090/docs

### 5. 验证系统

1. **检查数据库**：确认 `datacore.duckdb` 文件已生成
2. **检查数据模型**：运行 `dbt run` 后检查各层数据表
3. **检查 Web UI**：访问 http://localhost:8090，查看各功能页面

## 📖 详细说明

### 数据分层说明

| 层级 | 说明 | 物化方式 | 职责 |
|------|------|----------|------|
| **Staging** | 清洗层 | View | 数据清洗、标准化、异常值处理 |
| **ODS** | 操作数据存储层 | Table | 保持业务原始逻辑，关联字典表，增加业务字段 |
| **DWD** | 明细数据层 | Table | 业务明细数据，包含业务分类和维度扩展 |
| **DWS** | 汇总数据层 | Table | 按维度汇总统计，支持多维度分析 |
| **ADS** | 应用数据服务层 | Table | 面向业务应用，提供报表和分析数据 |
| **Metadata** | 元数据层 | Table | 元数据管理，包括表信息、字段信息、溯源关系等 |

### 元数据自动化

本项目实现了**完全自动化**的元数据管理：

#### 自动生成内容

1. **表信息** (`meta_table_info`)
   - 自动发现所有模型
   - 自动提取 schema、表名、描述
   - 从 `schema.yml` 的 `meta` 字段获取业务信息
   - 自动推断数据分层

2. **字段信息** (`meta_column_info`)
   - 自动提取所有字段
   - 从 `schema.yml` 的 `meta.column_name_cn` 获取中文字段名
   - 自动提取字段描述

3. **数据溯源** (`meta_data_lineage`)
   - 自动识别 `ref()` 依赖关系
   - 自动识别 `source()` 依赖关系
   - 自动推断转换类型（清洗/关联/转换/汇总/聚合）

#### 需要手工维护

在 `schema.yml` 中为每个模型添加 `meta` 信息：

```yaml
models:
  - name: your_model
    description: "模型描述"
    meta:
      table_name_cn: "中文表名"  # 可选，不提供则从 description 提取
      business_domain: "业务域"
      data_source: "数据源"
      update_frequency: "更新频率"
      owner: "负责人"
    columns:
      - name: column_name
        description: "字段描述"
        meta:
          column_name_cn: "中文字段名"  # 可选
```

### 数据质量测试

#### 测试类型

1. **完整性测试** (`test_toll_transaction_completeness`)
   - 检查关键字段是否为空
   - 检查必填字段是否缺失

2. **准确性测试** (`test_toll_transaction_accuracy`)
   - 检查数据是否符合业务规则
   - 检查数值范围是否合理

3. **一致性测试** (`test_toll_transaction_consistency`)
   - 检查数据逻辑一致性
   - 检查时间逻辑、金额逻辑等

4. **参照完整性测试** (`test_toll_transaction_referential_integrity`)
   - 检查外键关联是否正确
   - 检查字典值是否有效

#### 运行测试

```bash
# 运行所有测试
dbt test

# 运行特定测试
dbt test --select test_toll_transaction_completeness

# 运行数据质量相关测试
dbt test --select data_quality.*
```

### Web UI 功能说明

#### 首页概览 (`/`)
- 数据表统计（总数、分层分布）
- 数据质量概览（平均得分、告警数）
- 质量趋势图表
- 最近更新的数据表

#### 数据资产目录 (`/catalog`)
- 浏览所有数据表
- 按数据分层、业务域、负责人筛选
- 查看表详情（元数据、质量指标、字段列表）
- 搜索表名（支持中英文）

#### 数据溯源 (`/lineage`)
- 交互式溯源关系图
- 支持多种布局（广度优先、网格、圆形等）
- 点击节点查看表详情
- 显示转换类型和描述

#### 数据质量 (`/quality`)
- 质量监控看板（综合得分、正常交易率等）
- 质量趋势图表
- 质量指标详情表
- 告警状态展示

#### 数据浏览 (`/explorer`)
- 选择数据表
- 数据预览（分页）
- 字段中文名显示
- 表信息展示

#### 业务报表 (`/reports`)
- 收费收入报表（日收入、交易笔数、正常率等）
- 车流趋势分析（日车流量、唯一车辆数等）
- 图表可视化
- 数据表格展示

## 📁 项目结构

```
datacore/
├── models/                    # dbt 数据模型
│   ├── staging/              # 清洗层模型
│   │   ├── stg_toll_transaction.sql
│   │   ├── stg_toll_station.sql
│   │   └── schema.yml
│   ├── ods/                  # ODS 层模型
│   │   ├── ods_toll_transaction.sql
│   │   └── schema.yml
│   ├── dwd/                  # DWD 层模型
│   │   ├── dwd_toll_transaction_detail.sql
│   │   └── schema.yml
│   ├── dws/                  # DWS 层模型
│   │   ├── dws_toll_revenue_daily.sql
│   │   ├── dws_traffic_flow_daily.sql
│   │   └── schema.yml
│   ├── ads/                  # ADS 层模型
│   │   ├── ads_toll_revenue_report.sql
│   │   ├── ads_traffic_trend_analysis.sql
│   │   └── schema.yml
│   ├── metadata/             # 元数据模型
│   │   ├── meta_table_info.sql
│   │   ├── meta_column_info.sql
│   │   ├── meta_data_lineage.sql
│   │   ├── meta_data_quality_metrics.sql
│   │   └── schema.yml
│   └── sources.yml           # 数据源定义
├── macros/                    # dbt 宏
│   ├── metadata/             # 元数据宏
│   │   ├── generate_table_info.sql
│   │   ├── generate_column_info.sql
│   │   └── generate_lineage.sql
│   ├── data_quality/         # 数据质量宏
│   │   ├── check_completeness.sql
│   │   ├── check_accuracy.sql
│   │   └── check_consistency.sql
│   └── utils/                # 工具宏
├── tests/                     # dbt 测试
│   └── data_quality/         # 数据质量测试
│       ├── test_toll_transaction_completeness.sql
│       ├── test_toll_transaction_accuracy.sql
│       └── test_toll_transaction_consistency.sql
├── seeds/                     # 种子数据
│   └── data_dictionary/
├── scripts/                   # 脚本
│   └── generate_test_data.py # 测试数据生成脚本
├── web_ui/                    # Web UI
│   ├── backend/              # 后端服务
│   │   ├── main.py          # FastAPI 应用
│   │   ├── requirements.txt
│   │   └── build_and_serve.sh
│   └── frontend/             # 前端应用
│       ├── src/
│       │   ├── pages/       # 页面组件
│       │   ├── components/  # 通用组件
│       │   └── utils/       # 工具函数
│       └── package.json
├── dbt_project.yml           # dbt 项目配置
├── profiles.yml              # dbt 配置文件
├── requirements.txt          # Python 依赖
└── README.md                 # 本文档
```

## 🔧 常用命令

### dbt 命令

```bash
# 运行所有模型
dbt run

# 运行特定模型
dbt run --select staging.*
dbt run --select metadata.*

# 运行测试
dbt test

# 查看模型依赖关系
dbt list
dbt list --select staging.*

# 生成文档
dbt docs generate
dbt docs serve

# 清理编译产物
dbt clean
```

### Web UI 命令

```bash
# 生产模式（推荐）
cd web_ui/backend
./build_and_serve.sh

# 开发模式
cd web_ui
./start.sh

# 单独启动后端
cd web_ui/backend
source ../../venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8090 --reload

# 单独启动前端
cd web_ui/frontend
npm run dev
```

## 📝 开发指南

### 添加新模型

1. 在对应的层级目录下创建 SQL 文件
2. 在 `schema.yml` 中添加模型定义和元数据
3. 运行 `dbt run --select your_model`
4. 运行 `dbt test --select your_model`

### 添加数据质量测试

1. 在 `tests/data_quality/` 下创建测试 SQL 文件
2. 在 `schema.yml` 中定义测试
3. 运行 `dbt test`

### 更新元数据

元数据会自动更新，只需：
1. 更新 `schema.yml` 中的 `meta` 字段
2. 运行 `dbt run --select metadata.*`

## 🐛 故障排查

### 常见问题

1. **数据库文件不存在**
   - 确保已运行 `python scripts/generate_test_data.py`
   - 检查 `datacore.duckdb` 文件是否存在

2. **dbt 运行失败**
   - 检查 `profiles.yml` 配置
   - 检查数据库连接
   - 查看 `logs/dbt.log` 日志

3. **Web UI 无法访问**
   - 检查后端服务是否启动
   - 检查端口是否被占用
   - 查看浏览器控制台错误

4. **前端构建失败**
   - 检查 Node.js 版本（需要 16+）
   - 删除 `node_modules` 重新安装
   - 检查 `package.json` 依赖

## 📄 许可证

本项目为内部项目，仅供学习和参考使用。

## 👥 贡献

欢迎提交 Issue 和 Pull Request。

---

**注意**：本项目为示例项目，实际使用时请根据业务需求进行调整和优化。
