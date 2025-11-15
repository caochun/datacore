# MetricFlow 使用指南

## 概述

MetricFlow 是 dbt 的语义层工具，用于根据预定义的指标和维度生成 SQL 查询。

## 安装

```bash
pip install dbt-metricflow
```

## 基本命令

### 1. 列出所有可用指标

```bash
mf list metrics
```

**输出示例**：
```
Available Metrics:
  - daily_revenue: 日收费收入
  - monthly_revenue: 月收费收入
  - daily_transactions: 日交易笔数
  - normal_transaction_rate: 正常交易率
  ...
```

### 2. 生成 SQL 查询（不执行）

```bash
mf query \
  --metrics daily_revenue \
  --group-by transaction_date,city \
  --start-time 2025-01-01 \
  --end-time 2025-01-31 \
  --explain
```

**输入参数**：

| 参数 | 说明 | 示例 |
|------|------|------|
| `--metrics` | 指标名称（可多个，逗号分隔） | `daily_revenue` 或 `daily_revenue,normal_transaction_rate` |
| `--group-by` | 分组维度（可多个，逗号分隔） | `transaction_date,city` |
| `--start-time` | 开始时间（ISO 8601 格式） | `2025-01-01` 或 `2025-01-01T00:00:00` |
| `--end-time` | 结束时间（ISO 8601 格式） | `2025-01-31` 或 `2025-01-31T23:59:59` |
| `--where` | WHERE 条件（可多个） | `city='北京'` 或 `station_id IN (1,2,3)` |
| `--limit` | 结果限制数量 | `100` |
| `--explain` | 只生成 SQL，不执行查询 | （标志，无需值） |

**输出示例**：
```
Query Plan:
  Metric: daily_revenue
  Dimensions: transaction_date, city
  Time Range: 2025-01-01 to 2025-01-31

Generated SQL:
```sql
SELECT 
  transaction_date,
  city,
  SUM(total_actual_amount) AS daily_revenue
FROM main_dws.dws_toll_revenue_daily
WHERE transaction_date >= '2025-01-01'
  AND transaction_date <= '2025-01-31'
GROUP BY transaction_date, city
ORDER BY transaction_date, city
```
```

### 3. 执行查询并返回数据

```bash
mf query \
  --metrics daily_revenue \
  --group-by transaction_date,city \
  --start-time 2025-01-01 \
  --end-time 2025-01-31 \
  --output json
```

**输出格式选项**：
- `--output json`: JSON 格式
- `--output csv`: CSV 格式
- `--output table`: 表格格式（默认）

**输出示例（JSON）**：
```json
{
  "query_id": "abc123",
  "metrics": ["daily_revenue"],
  "dimensions": ["transaction_date", "city"],
  "data": [
    {
      "transaction_date": "2025-01-01",
      "city": "北京",
      "daily_revenue": 125000.50
    },
    {
      "transaction_date": "2025-01-01",
      "city": "上海",
      "daily_revenue": 98000.25
    }
  ]
}
```

## 在 Python 中使用

### 使用 MetricFlowClient（项目中的封装）

```python
from metricflow_client import MetricFlowClient

# 初始化客户端
client = MetricFlowClient(
    project_dir="/path/to/dbt/project",
    profiles_dir="."
)

# 生成 SQL
result = client.generate_sql(
    metrics=['daily_revenue'],
    group_by=['transaction_date', 'city'],
    start_time='2025-01-01',
    end_time='2025-01-31',
    where=['city = "北京"']
)

if result['success']:
    sql = result['sql']
    print("生成的 SQL:")
    print(sql)
else:
    print(f"错误: {result['error']}")
```

**输入参数**：

```python
generate_sql(
    metrics: List[str],              # 指标名称列表，如 ['daily_revenue']
    group_by: Optional[List[str]],   # 分组维度，如 ['transaction_date', 'city']
    where: Optional[List[str]],       # WHERE 条件，如 ['city = "北京"']
    start_time: Optional[str],        # 开始时间，如 '2025-01-01'
    end_time: Optional[str],          # 结束时间，如 '2025-01-31'
    limit: Optional[int]              # 结果限制，如 100
)
```

**输出格式**：

```python
{
    'sql': str,           # 生成的 SQL 语句
    'raw_output': str,    # MetricFlow 的原始输出
    'success': bool       # 是否成功
}
```

或失败时：

```python
{
    'sql': None,
    'error': str,         # 错误信息
    'success': False
}
```

## 实际使用示例

### 示例 1: 查询最近7天的日收入，按城市分组

**命令行**：
```bash
mf query \
  --metrics daily_revenue \
  --group-by transaction_date,city \
  --start-time 2025-01-25 \
  --end-time 2025-01-31 \
  --explain
```

**Python 代码**：
```python
result = client.generate_sql(
    metrics=['daily_revenue'],
    group_by=['transaction_date', 'city'],
    start_time='2025-01-25',
    end_time='2025-01-31'
)
```

**生成的 SQL**：
```sql
SELECT 
  transaction_date,
  city,
  SUM(total_actual_amount) AS daily_revenue
FROM main_dws.dws_toll_revenue_daily
WHERE transaction_date >= '2025-01-25'
  AND transaction_date <= '2025-01-31'
GROUP BY transaction_date, city
ORDER BY transaction_date, city
```

### 示例 2: 查询正常交易率，按收费站分组

**命令行**：
```bash
mf query \
  --metrics normal_transaction_rate \
  --group-by station_name \
  --start-time 2025-01-01 \
  --end-time 2025-01-31 \
  --where "city='北京'" \
  --explain
```

**Python 代码**：
```python
result = client.generate_sql(
    metrics=['normal_transaction_rate'],
    group_by=['station_name'],
    start_time='2025-01-01',
    end_time='2025-01-31',
    where=['city = "北京"']
)
```

**生成的 SQL**：
```sql
SELECT 
  station_name,
  SUM(normal_transaction_count) * 100.0 / SUM(transaction_count) AS normal_transaction_rate
FROM main_dws.dws_toll_revenue_daily
WHERE transaction_date >= '2025-01-01'
  AND transaction_date <= '2025-01-31'
  AND city = '北京'
GROUP BY station_name
ORDER BY station_name
```

### 示例 3: 查询多个指标

**命令行**：
```bash
mf query \
  --metrics daily_revenue,daily_transactions \
  --group-by transaction_date \
  --start-time 2025-01-01 \
  --end-time 2025-01-07 \
  --explain
```

**Python 代码**：
```python
result = client.generate_sql(
    metrics=['daily_revenue', 'daily_transactions'],
    group_by=['transaction_date'],
    start_time='2025-01-01',
    end_time='2025-01-07'
)
```

## 输入输出总结

### 输入（Input）

1. **指标名称**：从 `models/metrics.yml` 中定义的指标
2. **维度**：从 `models/dws/schema.yml` 中定义的维度
3. **时间范围**：ISO 8601 格式的日期
4. **过滤条件**：SQL WHERE 子句格式的条件

### 输出（Output）

1. **SQL 语句**：根据语义层定义生成的 SQL
   - 自动处理 JOIN（如果有多个表）
   - 自动处理聚合（SUM、AVG 等）
   - 自动处理比率计算（如 normal_transaction_rate）
   - 自动优化查询性能

2. **元数据**：
   - 使用的指标定义
   - 使用的维度
   - 时间范围
   - 过滤条件

## 优势

1. **标准化**：所有查询使用相同的指标定义，确保一致性
2. **可维护**：指标定义集中管理，修改一处即可
3. **可复用**：同一个指标可以在多个 BI 工具、API、AI 系统中使用
4. **准确性**：避免手动编写 SQL 时的错误
5. **性能优化**：MetricFlow 自动优化生成的 SQL

## 注意事项

1. 必须先在 `models/dws/schema.yml` 中定义语义模型
2. 必须先在 `models/metrics.yml` 中定义指标
3. 时间维度（如 `transaction_date`）通常需要包含在 `group_by` 中
4. WHERE 条件使用 SQL 语法，注意引号的使用
5. 使用 `--explain` 只生成 SQL，不执行查询（适合调试）

