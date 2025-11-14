# MetricFlow 与 AI/LLM 集成说明

## MetricFlow 的核心价值

根据 [dbt 官方博客](https://www.getdbt.com/blog/open-source-metricflow-governed-metrics)，MetricFlow 的核心价值是：

### 1. 提供可信的指标定义，供 AI/LLM 使用

> "Metrics should not be probabilistic or depend on an LLM guessing each calculation. They should be deterministic."

**核心思想**：
- MetricFlow 提供标准化的、受治理的指标定义
- AI/LLM 系统调用 MetricFlow 来生成正确的 SQL，而不是自己猜测
- 确保每次 LLM 调用（无论 GPT、Claude 或代理）使用相同的计算方式

### 2. 确保 AI 使用正确的业务逻辑

**问题**：LLM 直接生成 SQL 时可能：
- 猜测错误的 JOIN 关系
- 使用错误的过滤条件
- 计算方式不一致
- 性能不佳

**解决方案**：MetricFlow 提供：
- 预定义的指标（包含正确的业务逻辑）
- 自动生成优化的 SQL
- 可检查的查询计划
- 支持复杂计算（JOIN、窗口函数、队列等）

### 3. 实际应用流程

```
用户自然语言问题
    ↓
LLM 理解意图
    ↓
调用 MetricFlow API（选择指标、维度、过滤条件）
    ↓
MetricFlow 生成正确的 SQL（包含正确的 JOIN、过滤、聚合）
    ↓
执行查询，返回结果
```

## 项目中的实现

### 架构设计

```
自然语言查询
    ↓
LLMQueryParser（理解用户意图）
    ↓
转换为 MetricQuery（指标名称、维度、过滤条件）
    ↓
MetricFlow 生成 SQL（使用语义层定义）
    ↓
执行查询，返回结果
```

### 关键组件

1. **语义层定义** (`models/dws/schema.yml`, `models/metrics.yml`)
   - 定义指标和维度
   - 包含正确的业务逻辑

2. **MetricFlow 客户端** (`web_ui/backend/metricflow_client.py`)
   - 调用 MetricFlow 生成 SQL
   - 确保使用正确的指标定义

3. **LLM 查询解析器** (`web_ui/backend/llm_query_parser.py`)
   - 将自然语言转换为 MetricQuery
   - 支持规则解析和 LLM 解析

4. **API 端点** (`/api/metrics/query/natural`)
   - 接收自然语言查询
   - 调用解析器和 MetricFlow
   - 返回结果

## 使用示例

### 示例 1：自然语言查询

**用户问题**：
```
"查询最近7天的日收入，按城市分组"
```

**处理流程**：
1. LLMQueryParser 识别：
   - 指标：`daily_revenue`
   - 维度：`city`
   - 时间范围：最近7天

2. 转换为 MetricQuery：
```json
{
    "metric_name": "daily_revenue",
    "dimensions": ["city"],
    "start_date": "2025-11-07",
    "end_date": "2025-11-14"
}
```

3. MetricFlow 生成 SQL（使用语义层定义）：
```sql
SELECT 
    transaction_date, 
    city,
    SUM(total_actual_amount) as metric_value
FROM main_dws.dws_toll_revenue_daily
WHERE transaction_date >= '2025-11-07'
  AND transaction_date <= '2025-11-14'
GROUP BY transaction_date, city
ORDER BY transaction_date
```

4. 执行查询，返回结果

### 示例 2：复杂查询

**用户问题**：
```
"显示北京本月的正常交易率，按收费站分组"
```

**处理流程**：
1. LLMQueryParser 识别：
   - 指标：`normal_transaction_rate`（比率指标）
   - 维度：`station_name`
   - 过滤：`city = '北京'`
   - 时间范围：本月

2. MetricFlow 自动处理：
   - 识别这是比率指标
   - 正确计算分子/分母
   - 应用城市过滤
   - 按收费站分组

3. 生成正确的 SQL（包含正确的业务逻辑）

## 与直接让 LLM 生成 SQL 的对比

### ❌ 直接让 LLM 生成 SQL

```python
# 问题：LLM 可能猜测错误的 SQL
prompt = "查询最近7天的日收入，按城市分组"
sql = llm.generate_sql(prompt)
# 可能生成错误的 SQL，缺少正确的 JOIN、过滤等
```

**风险**：
- SQL 可能不正确
- 业务逻辑不一致
- 性能问题
- 难以维护

### ✅ 使用 MetricFlow + LLM

```python
# LLM 只负责理解意图，选择指标
prompt = "查询最近7天的日收入，按城市分组"
query = llm.parse_to_metric_query(prompt)
# MetricFlow 生成正确的 SQL
sql = metricflow.generate_sql(query)
```

**优势**：
- SQL 始终正确（使用预定义指标）
- 业务逻辑一致
- 性能优化
- 易于维护和治理

## 配置 LLM 集成

### 方式 1：使用 OpenAI（推荐）

```bash
export OPENAI_API_KEY="your-api-key"
```

```python
query = {
    "query": "查询最近7天的日收入，按城市分组",
    "use_llm": True  # 使用 LLM 解析
}
```

### 方式 2：使用规则解析（无需 API Key）

```python
query = {
    "query": "查询最近7天的日收入，按城市分组",
    "use_llm": False  # 使用规则解析
}
```

## 最佳实践

1. **定义清晰的指标**
   - 在 `metrics.yml` 中明确定义所有业务指标
   - 包含详细的描述和元数据

2. **使用语义层**
   - 所有查询都通过 MetricFlow
   - 不要绕过语义层直接写 SQL

3. **LLM 只负责理解意图**
   - LLM 选择指标和维度
   - MetricFlow 生成 SQL

4. **可检查性**
   - 返回生成的 SQL
   - 提供查询计划
   - 记录所有查询

## 总结

MetricFlow 的核心价值不是"直接集成 LLM"，而是：

1. **提供可信的指标定义**：确保业务逻辑正确
2. **供 AI 系统使用**：LLM 调用 MetricFlow 而不是猜测 SQL
3. **保证一致性**：无论使用哪个 LLM，都使用相同的计算方式
4. **可治理**：指标定义在代码中，可版本控制、可审查

这就是 dbt 官方博客中强调的"可信 AI"（Trusted AI）的核心思想。

