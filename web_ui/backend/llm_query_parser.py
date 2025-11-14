"""
LLM 自然语言查询解析器
将用户的自然语言问题转换为 MetricQuery

根据 dbt 官方博客，MetricFlow 的核心价值是：
1. 提供可信的指标定义，供 AI/LLM 使用
2. 确保 AI 使用正确的业务逻辑，而不是猜测 SQL
3. 生成可检查的、优化的 SQL

本模块实现了自然语言到 MetricFlow 查询的转换层：
- 规则解析：基于关键词匹配（无需 API Key）
- LLM 解析：使用 LLM 理解用户意图，然后调用 MetricFlow 生成正确的 SQL
"""
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import re

logger = logging.getLogger(__name__)

class LLMQueryParser:
    """自然语言查询解析器"""
    
    def __init__(self, available_metrics: List[Dict[str, Any]], available_dimensions: List[str]):
        """
        初始化解析器
        
        Args:
            available_metrics: 可用指标列表
            available_dimensions: 可用维度列表
        """
        self.available_metrics = available_metrics
        self.available_dimensions = available_dimensions
        
        # 构建指标名称映射（支持中文和英文）
        self.metric_map = {}
        for metric in available_metrics:
            name = metric.get('name', '')
            label = metric.get('label', '')
            description = metric.get('description', '')
            
            # 建立多个映射
            self.metric_map[name.lower()] = name
            if label:
                self.metric_map[label.lower()] = name
            if description:
                # 提取关键词
                keywords = self._extract_keywords(description)
                for keyword in keywords:
                    self.metric_map[keyword.lower()] = name
        
        # 维度映射
        self.dimension_map = {
            '城市': 'city',
            '收费站': 'station_name',
            '车型': 'vehicle_type_name',
            '支付方式': 'payment_method_name',
            '高速公路': 'highway_code',
            'city': 'city',
            'station': 'station_name',
            'vehicle': 'vehicle_type_name',
            'payment': 'payment_method_name',
            'highway': 'highway_code'
        }
    
    def _extract_keywords(self, text: str) -> List[str]:
        """从文本中提取关键词"""
        # 简单的关键词提取（可以改进）
        keywords = []
        # 提取2-4字的中文词
        chinese_words = re.findall(r'[\u4e00-\u9fa5]{2,4}', text)
        keywords.extend(chinese_words)
        return keywords
    
    def parse(self, query: str) -> Dict[str, Any]:
        """
        解析自然语言查询
        
        Args:
            query: 用户的自然语言问题
            
        Returns:
            解析后的查询参数
        """
        query_lower = query.lower()
        
        # 1. 识别指标
        metric_name = self._extract_metric(query_lower)
        
        # 2. 识别维度
        dimensions = self._extract_dimensions(query_lower)
        
        # 3. 识别时间范围
        start_date, end_date = self._extract_time_range(query)
        
        # 4. 识别过滤条件
        filters = self._extract_filters(query)
        
        return {
            'metric_name': metric_name,
            'dimensions': dimensions,
            'start_date': start_date,
            'end_date': end_date,
            'filters': filters,
            'original_query': query
        }
    
    def _extract_metric(self, query: str) -> Optional[str]:
        """从查询中提取指标名称"""
        # 按优先级匹配
        for key, metric_name in self.metric_map.items():
            if key in query:
                return metric_name
        
        # 如果没有找到，尝试模糊匹配
        for metric in self.available_metrics:
            name = metric.get('name', '')
            label = metric.get('label', '')
            
            # 检查是否包含指标相关的关键词
            if any(keyword in query for keyword in ['收入', 'revenue', '交易', 'transaction', '质量', 'quality']):
                if '收入' in label or 'revenue' in name:
                    return name
                elif '交易' in label or 'transaction' in name:
                    return name
                elif '质量' in label or 'quality' in name:
                    return name
        
        # 默认返回第一个指标
        if self.available_metrics:
            return self.available_metrics[0].get('name')
        
        return None
    
    def _extract_dimensions(self, query: str) -> List[str]:
        """从查询中提取维度"""
        dimensions = []
        
        for key, dim in self.dimension_map.items():
            if key.lower() in query:
                if dim not in dimensions:
                    dimensions.append(dim)
        
        return dimensions
    
    def _extract_time_range(self, query: str) -> tuple:
        """从查询中提取时间范围"""
        today = datetime.now()
        start_date = None
        end_date = None
        
        # 识别具体日期（优先处理，避免被其他规则覆盖）
        date_pattern = r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})'
        dates = re.findall(date_pattern, query)
        if dates:
            if len(dates) == 1:
                year, month, day = dates[0]
                start_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                end_date = start_date
            elif len(dates) >= 2:
                year, month, day = dates[0]
                start_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                year, month, day = dates[1]
                end_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            # 如果找到了具体日期，直接返回
            if start_date and end_date:
                return start_date, end_date
        
        # 识别时间关键词
        if '今天' in query or 'today' in query.lower():
            start_date = today.strftime('%Y-%m-%d')
            end_date = today.strftime('%Y-%m-%d')
        elif '昨天' in query or 'yesterday' in query.lower():
            yesterday = today - timedelta(days=1)
            start_date = yesterday.strftime('%Y-%m-%d')
            end_date = yesterday.strftime('%Y-%m-%d')
        elif '本周' in query or 'this week' in query.lower():
            # 本周一
            days_since_monday = today.weekday()
            monday = today - timedelta(days=days_since_monday)
            start_date = monday.strftime('%Y-%m-%d')
            end_date = today.strftime('%Y-%m-%d')
        elif '本月' in query or 'this month' in query.lower():
            start_date = today.replace(day=1).strftime('%Y-%m-%d')
            end_date = today.strftime('%Y-%m-%d')
        elif '最近' in query or 'last' in query.lower():
            # 提取天数
            days_match = re.search(r'(\d+)天', query)
            if days_match:
                days = int(days_match.group(1))
                # 计算开始日期：今天往前推 days 天
                start_date = (today - timedelta(days=days-1)).strftime('%Y-%m-%d')  # days-1 因为包含今天
                end_date = today.strftime('%Y-%m-%d')
            else:
                # 默认最近7天（包含今天）
                start_date = (today - timedelta(days=6)).strftime('%Y-%m-%d')  # 6天前到今天是7天
                end_date = today.strftime('%Y-%m-%d')
        
        return start_date, end_date
    
    def _extract_filters(self, query: str) -> Dict[str, Any]:
        """从查询中提取过滤条件"""
        filters = {}
        
        # 提取城市过滤
        cities = ['北京', '上海', '南京', '天津', '德州', '廊坊']
        for city in cities:
            if city in query:
                filters['city'] = city
                break
        
        # 提取其他维度过滤
        for key, dim in self.dimension_map.items():
            if key in query and dim not in filters:
                # 尝试提取值（简化版）
                # 实际可以使用更复杂的 NLP 方法
                pass
        
        return filters


class LLMQueryParserWithAPI:
    """使用 LLM API 的查询解析器（支持 OpenAI、DeepSeek 等）"""
    
    def __init__(self, available_metrics: List[Dict[str, Any]], 
                 available_dimensions: List[str],
                 api_key: Optional[str] = None,
                 model: str = "gpt-3.5-turbo",
                 provider: str = "openai"):
        """
        初始化 LLM 解析器
        
        Args:
            available_metrics: 可用指标列表
            available_dimensions: 可用维度列表
            api_key: LLM API Key
            model: 使用的模型名称
            provider: 模型提供商 ("openai", "deepseek", "custom")
        """
        self.available_metrics = available_metrics
        self.available_dimensions = available_dimensions
        self.api_key = api_key
        self.model = model
        self.provider = provider.lower()
        self.use_llm = api_key is not None
    
    def parse(self, query: str) -> Dict[str, Any]:
        """
        使用 LLM 解析自然语言查询
        
        采用混合策略：
        1. LLM 识别指标、维度、时间关键词（不计算具体日期）
        2. 后端规则解析器计算具体日期范围
        
        这样可以避免 LLM 返回错误日期的问题
        
        Args:
            query: 用户的自然语言问题
            
        Returns:
            解析后的查询参数
        """
        if not self.use_llm:
            # 回退到规则解析
            parser = LLMQueryParser(self.available_metrics, self.available_dimensions)
            return parser.parse(query)
        
        try:
            # 构建提示词（只让LLM识别指标、维度、时间关键词，不计算具体日期）
            prompt = self._build_prompt_for_llm(query)
            
            # 根据提供商调用不同的 LLM API
            llm_result = None
            if self.provider == "deepseek":
                llm_result = self._parse_with_deepseek(prompt, query)
            elif self.provider == "openai" or self.model.startswith('gpt'):
                llm_result = self._parse_with_openai(prompt, query)
            else:
                # 默认尝试 DeepSeek
                try:
                    llm_result = self._parse_with_deepseek(prompt, query)
                except:
                    llm_result = self._parse_with_openai(prompt, query)
            
            # 如果 LLM 返回了具体日期，使用规则解析器重新计算（更可靠）
            if llm_result and ('start_date' in llm_result or 'end_date' in llm_result):
                # 使用规则解析器计算时间范围（基于原始查询）
                rule_parser = LLMQueryParser(self.available_metrics, self.available_dimensions)
                rule_result = rule_parser.parse(query)
                
                # 合并结果：使用 LLM 的指标和维度，使用规则解析器的时间范围
                final_result = {
                    'metric_name': llm_result.get('metric_name') or rule_result.get('metric_name'),
                    'dimensions': llm_result.get('dimensions') or rule_result.get('dimensions'),
                    'start_date': rule_result.get('start_date'),  # 使用规则解析器的时间（更可靠）
                    'end_date': rule_result.get('end_date'),      # 使用规则解析器的时间（更可靠）
                    'filters': llm_result.get('filters') or rule_result.get('filters'),
                    'original_query': query
                }
                
                logger.info(f"混合解析：LLM识别指标/维度，规则解析器计算时间")
                return final_result
            
            return llm_result
        
        except Exception as e:
            logger.error(f"LLM 解析失败: {e}，使用规则解析")
            parser = LLMQueryParser(self.available_metrics, self.available_dimensions)
            return parser.parse(query)
    
    def _build_prompt_for_llm(self, query: str) -> str:
        """
        构建 LLM 提示词（只识别指标、维度、时间关键词，不计算具体日期）
        
        这是更可靠的方法：让 LLM 只做它擅长的事（语义理解），
        时间计算交给后端的规则解析器（更准确、更可靠）
        """
        metrics_info = "\n".join([
            f"- {m.get('name')}: {m.get('label')} ({m.get('description', '')})"
            for m in self.available_metrics
        ])
        
        dimensions_info = ", ".join(self.available_dimensions)
        
        prompt = f"""你是一个数据查询助手，使用 MetricFlow 语义层来查询指标。

重要原则：
1. 必须使用下面定义的指标，不要自己猜测 SQL 或计算方式
2. 指标定义已经包含了正确的业务逻辑（JOIN、过滤、聚合等）
3. 你的任务是理解用户意图，选择正确的指标和维度
4. MetricFlow 会自动生成正确的 SQL
5. **重要**：对于时间范围，只返回时间关键词（如"最近7天"、"本月"），不要计算具体日期

可用指标（已定义，包含正确的业务逻辑）：
{metrics_info}

可用维度：
{dimensions_info}

用户问题：{query}

请返回 JSON 格式的查询参数：
{{
    "metric_name": "指标名称（必须从上面的列表中选择）",
    "dimensions": ["维度1", "维度2"],
    "time_keyword": "时间关键词（如：最近7天、本月、昨天等，不要计算具体日期）",
    "filters": {{"key": "value"}}
}}

只返回 JSON，不要其他内容。记住：
- 不要猜测 SQL，使用已定义的指标
- 对于时间，只返回关键词，不要计算具体日期
"""
        return prompt
    
    def _build_prompt(self, query: str) -> str:
        """
        构建 LLM 提示词
        
        重要：根据 dbt 官方博客，MetricFlow 的核心价值是确保 AI 使用正确的业务逻辑。
        这里的提示词强调使用已定义的指标，而不是让 LLM 猜测 SQL。
        """
        from datetime import datetime
        today = datetime.now()
        current_date_str = today.strftime('%Y-%m-%d')
        
        metrics_info = "\n".join([
            f"- {m.get('name')}: {m.get('label')} ({m.get('description', '')})"
            for m in self.available_metrics
        ])
        
        dimensions_info = ", ".join(self.available_dimensions)
        
        prompt = f"""你是一个数据查询助手，使用 MetricFlow 语义层来查询指标。

重要原则：
1. 必须使用下面定义的指标，不要自己猜测 SQL 或计算方式
2. 指标定义已经包含了正确的业务逻辑（JOIN、过滤、聚合等）
3. 你的任务是理解用户意图，选择正确的指标和维度
4. MetricFlow 会自动生成正确的 SQL
5. **重要**：当前日期是 {current_date_str}，所有日期计算必须基于这个日期

可用指标（已定义，包含正确的业务逻辑）：
{metrics_info}

可用维度：
{dimensions_info}

用户问题：{query}

请返回 JSON 格式的查询参数，这些参数将传递给 MetricFlow 生成正确的 SQL：
{{
    "metric_name": "指标名称（必须从上面的列表中选择）",
    "dimensions": ["维度1", "维度2"],
    "start_date": "YYYY-MM-DD（必须是 {current_date_str} 之前的日期）",
    "end_date": "YYYY-MM-DD（不能超过 {current_date_str}）",
    "filters": {{"key": "value"}}
}}

只返回 JSON，不要其他内容。记住：
- 不要猜测 SQL，使用已定义的指标
- 当前日期是 {current_date_str}，日期计算必须基于此
- "最近7天" 表示从 {current_date_str} 往前推7天
"""
        return prompt
    
    def _parse_with_openai(self, prompt: str, query: str) -> Dict[str, Any]:
        """使用 OpenAI API 解析"""
        try:
            import openai
            
            openai.api_key = self.api_key
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个数据查询助手，将自然语言转换为结构化查询。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            result_text = response.choices[0].message.content.strip()
            # 提取 JSON
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                parsed_result = json.loads(json_match.group())
                # 验证和修复日期
                parsed_result = self._validate_and_fix_dates(parsed_result)
                return parsed_result
            else:
                raise ValueError("无法从 LLM 响应中提取 JSON")
        
        except ImportError:
            logger.error("OpenAI 库未安装，请运行: pip install openai")
            raise
        except Exception as e:
            logger.error(f"OpenAI API 调用失败: {e}")
            raise
    
    def _parse_with_deepseek(self, prompt: str, query: str) -> Dict[str, Any]:
        """使用 DeepSeek API 解析"""
        try:
            import requests
            
            # DeepSeek API 端点
            api_url = "https://api.deepseek.com/v1/chat/completions"
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            payload = {
                "model": self.model,  # 如 "deepseek-chat"
                "messages": [
                    {"role": "system", "content": "你是一个数据查询助手，将自然语言转换为结构化查询。"},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3,
                "max_tokens": 1000
            }
            
            response = requests.post(api_url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            result_text = result['choices'][0]['message']['content'].strip()
            
            # 提取 JSON
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                parsed_result = json.loads(json_match.group())
                # 验证和修复日期
                parsed_result = self._validate_and_fix_dates(parsed_result)
                return parsed_result
            else:
                raise ValueError("无法从 DeepSeek 响应中提取 JSON")
        
        except ImportError:
            logger.error("requests 库未安装，请运行: pip install requests")
            raise
        except Exception as e:
            logger.error(f"DeepSeek API 调用失败: {e}")
            raise
    
    def _validate_and_fix_dates(self, parsed_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证和修复 LLM 返回的日期
        
        如果 LLM 返回了错误的年份（如2023、2024），自动修复为当前年份
        """
        from datetime import datetime
        today = datetime.now()
        current_year = today.year
        
        # 检查并修复开始日期
        if 'start_date' in parsed_result and parsed_result['start_date']:
            start_date_str = parsed_result['start_date']
            try:
                date_obj = datetime.strptime(start_date_str, '%Y-%m-%d')
                # 如果年份不是当前年份，修复为当前年份
                if date_obj.year != current_year:
                    # 保持月日不变，只修改年份
                    fixed_date = date_obj.replace(year=current_year)
                    # 如果修复后的日期在未来，则使用当前日期
                    if fixed_date > today:
                        fixed_date = today
                    parsed_result['start_date'] = fixed_date.strftime('%Y-%m-%d')
                    logger.warning(f"修复开始日期: {start_date_str} -> {parsed_result['start_date']}")
            except ValueError:
                pass
        
        # 检查并修复结束日期
        if 'end_date' in parsed_result and parsed_result['end_date']:
            end_date_str = parsed_result['end_date']
            try:
                date_obj = datetime.strptime(end_date_str, '%Y-%m-%d')
                # 如果年份不是当前年份，修复为当前年份
                if date_obj.year != current_year:
                    # 保持月日不变，只修改年份
                    fixed_date = date_obj.replace(year=current_year)
                    # 如果修复后的日期在未来，则使用当前日期
                    if fixed_date > today:
                        fixed_date = today
                    parsed_result['end_date'] = fixed_date.strftime('%Y-%m-%d')
                    logger.warning(f"修复结束日期: {end_date_str} -> {parsed_result['end_date']}")
            except ValueError:
                pass
        
        return parsed_result
    
    def _parse_with_other_llm(self, prompt: str, query: str) -> Dict[str, Any]:
        """使用其他 LLM 服务解析"""
        # 可以集成其他 LLM 服务，如：
        # - 本地模型（Ollama, LM Studio）
        # - 其他 API（Claude, Gemini 等）
        raise NotImplementedError("请实现具体的 LLM 服务集成")

