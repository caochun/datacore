# DeepSeek 模型集成指南

## 概述

项目已支持集成 DeepSeek 模型用于自然语言查询解析。DeepSeek 是一个高性能的 AI 模型，支持 API 调用。

## 配置方式

### 方式 1：环境变量（推荐）

```bash
# 设置 DeepSeek API Key
export DEEPSEEK_API_KEY="your-deepseek-api-key"

# 可选：指定模型（默认为 deepseek-chat）
export DEEPSEEK_MODEL="deepseek-chat"

# 或者指定提供商
export LLM_PROVIDER="deepseek"
```

### 方式 2：API 请求参数

```json
{
    "query": "查询最近7天的日收入，按城市分组",
    "use_llm": true,
    "provider": "deepseek",
    "model": "deepseek-chat"
}
```

## API 使用示例

### 基本查询

```bash
curl -X POST http://localhost:8090/api/metrics/query/natural \
  -H "Content-Type: application/json" \
  -d '{
    "query": "查询最近7天的日收入，按城市分组",
    "use_llm": true,
    "provider": "deepseek"
  }'
```

### Python 示例

```python
import requests
import os

# 设置 API Key
os.environ['DEEPSEEK_API_KEY'] = 'your-api-key'

# 发送查询
response = requests.post(
    'http://localhost:8090/api/metrics/query/natural',
    json={
        'query': '查询最近7天的日收入，按城市分组',
        'use_llm': True,
        'provider': 'deepseek'
    }
)

result = response.json()
print(result)
```

## DeepSeek API 信息

### API 端点

```
https://api.deepseek.com/v1/chat/completions
```

### 支持的模型

- `deepseek-chat` - 对话模型（推荐）
- `deepseek-coder` - 代码生成模型

### 获取 API Key

1. 访问 [DeepSeek 官网](https://www.deepseek.com/)
2. 注册账号并获取 API Key
3. 配置到环境变量或代码中

## 与 OpenAI 对比

| 特性 | DeepSeek | OpenAI |
|------|----------|--------|
| API 端点 | `https://api.deepseek.com/v1/chat/completions` | `https://api.openai.com/v1/chat/completions` |
| 默认模型 | `deepseek-chat` | `gpt-3.5-turbo` |
| 环境变量 | `DEEPSEEK_API_KEY` | `OPENAI_API_KEY` |
| 成本 | 通常更便宜 | 相对较贵 |
| 中文支持 | 优秀 | 良好 |

## 代码实现

### LLMQueryParserWithAPI 类

已更新 `llm_query_parser.py` 中的 `LLMQueryParserWithAPI` 类，支持：

1. **自动检测提供商**
   - 根据环境变量或参数选择
   - 支持 `openai` 和 `deepseek`

2. **统一接口**
   - 相同的调用方式
   - 自动适配不同的 API

3. **错误处理**
   - API 调用失败时自动回退到规则解析
   - 详细的错误日志

### 关键代码

```python
# 在 llm_query_parser.py 中
def _parse_with_deepseek(self, prompt: str, query: str) -> Dict[str, Any]:
    """使用 DeepSeek API 解析"""
    import requests
    
    api_url = "https://api.deepseek.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {self.api_key}"
    }
    
    payload = {
        "model": self.model,
        "messages": [
            {"role": "system", "content": "你是一个数据查询助手..."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3
    }
    
    response = requests.post(api_url, headers=headers, json=payload)
    # ... 处理响应
```

## 测试

### 测试 DeepSeek 集成

```python
import os
os.environ['DEEPSEEK_API_KEY'] = 'your-api-key'

from llm_query_parser import LLMQueryParserWithAPI

parser = LLMQueryParserWithAPI(
    available_metrics=[...],
    available_dimensions=[...],
    api_key=os.getenv('DEEPSEEK_API_KEY'),
    model='deepseek-chat',
    provider='deepseek'
)

result = parser.parse("查询最近7天的日收入")
print(result)
```

## 注意事项

1. **API Key 安全**
   - 不要将 API Key 提交到代码仓库
   - 使用环境变量或密钥管理服务

2. **速率限制**
   - DeepSeek API 可能有速率限制
   - 建议实现重试机制

3. **成本控制**
   - 监控 API 调用次数和成本
   - 考虑实现缓存机制

4. **错误处理**
   - API 调用失败时自动回退到规则解析
   - 记录详细的错误日志

## 故障排查

### 问题：API 调用失败

**可能原因**：
- API Key 无效或过期
- 网络连接问题
- API 端点变更

**解决方案**：
1. 检查 API Key 是否正确
2. 检查网络连接
3. 查看错误日志
4. 验证 API 端点是否可用

### 问题：解析结果不正确

**可能原因**：
- 提示词不够清晰
- 模型理解有误

**解决方案**：
1. 优化提示词
2. 调整 temperature 参数
3. 使用更精确的指标描述

## 未来扩展

可以进一步支持：
- 本地模型（Ollama, LM Studio）
- 其他云服务（Claude, Gemini）
- 自定义模型端点

