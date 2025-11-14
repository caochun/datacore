#!/usr/bin/env python3
"""
测试 DeepSeek API 集成

使用方法：
1. 设置环境变量：
   export DEEPSEEK_API_KEY="your-api-key"
   export LLM_PROVIDER="deepseek"

2. 或者运行：
   source setup_deepseek.sh
   python3 test_deepseek.py
"""
import os
import sys
sys.path.insert(0, 'web_ui/backend')

# 从环境变量读取 API Key（不要硬编码到代码中）
api_key = os.getenv('DEEPSEEK_API_KEY')
if not api_key:
    print("❌ 错误：未设置 DEEPSEEK_API_KEY 环境变量")
    print("   请运行: source setup_deepseek.sh")
    print("   或者设置: export DEEPSEEK_API_KEY='your-api-key'")
    sys.exit(1)

from llm_query_parser import LLMQueryParserWithAPI

# 模拟指标和维度
metrics = [
    {'name': 'daily_revenue', 'label': '日收费收入', 'description': '日收费收入'},
    {'name': 'daily_transactions', 'label': '日交易笔数', 'description': '日交易笔数'},
    {'name': 'normal_transaction_rate', 'label': '正常交易率', 'description': '正常交易率'}
]

dimensions = ['city', 'station_name', 'vehicle_type_name']

print("=" * 60)
print("测试 DeepSeek API 集成")
print("=" * 60)

try:
    parser = LLMQueryParserWithAPI(
        available_metrics=metrics,
        available_dimensions=dimensions,
        api_key=api_key,
        model=os.getenv('DEEPSEEK_MODEL', 'deepseek-chat'),
        provider=os.getenv('LLM_PROVIDER', 'deepseek')
    )
    
    print("\n✅ DeepSeek 解析器初始化成功")
    
    # 测试查询
    test_query = "查询最近7天的日收入，按城市分组"
    print(f"\n测试查询: {test_query}")
    
    result = parser.parse(test_query)
    
    print("\n✅ 解析成功！")
    print(f"解析结果:")
    print(f"  指标: {result.get('metric_name')}")
    print(f"  维度: {result.get('dimensions')}")
    print(f"  时间范围: {result.get('start_date')} 到 {result.get('end_date')}")
    print(f"  过滤条件: {result.get('filters')}")
    
except Exception as e:
    print(f"\n❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()
