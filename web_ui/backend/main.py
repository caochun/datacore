"""
数据中台Web UI后端API
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import duckdb
import os
import yaml
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime, timedelta
import logging
from metricflow_client import MetricFlowClient
from llm_query_parser import LLMQueryParser, LLMQueryParserWithAPI

# 加载 .env 文件（如果存在）
try:
    from dotenv import load_dotenv
    # 尝试从项目根目录加载 .env 文件
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    env_path = os.path.join(project_root, ".env")
    if os.path.exists(env_path):
        load_dotenv(env_path)
        logger = logging.getLogger(__name__)
        logger.info(f"已加载 .env 文件: {env_path}")
    else:
        # 也尝试从当前目录加载
        load_dotenv()
except ImportError:
    # python-dotenv 未安装，跳过
    pass

logger = logging.getLogger(__name__)

# 配置日志级别和格式，确保 INFO 级别的日志能够输出
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

app = FastAPI(title="数据中台API", version="1.0.0")

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件目录（前端构建后的dist目录）
FRONTEND_DIST = os.path.join(os.path.dirname(__file__), "../frontend/dist")

# 数据库连接
# 尝试多个可能的路径
possible_paths = [
    os.path.join(os.path.dirname(__file__), "../../datacore.duckdb"),
    os.path.join(os.path.dirname(__file__), "../../../datacore.duckdb"),
    "datacore.duckdb"
]

DB_PATH = None
for path in possible_paths:
    if os.path.exists(path):
        DB_PATH = os.path.abspath(path)
        break

if not DB_PATH:
    raise FileNotFoundError("找不到 datacore.duckdb 数据库文件")

# dbt 项目路径
DBT_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

# 初始化 MetricFlow 客户端
_metricflow_client = None

def get_db():
    """获取数据库连接"""
    return duckdb.connect(DB_PATH)

def get_metricflow_client() -> MetricFlowClient:
    """获取 MetricFlow 客户端（单例）"""
    global _metricflow_client
    if _metricflow_client is None:
        _metricflow_client = MetricFlowClient(
            project_dir=DBT_PROJECT_ROOT,
            profiles_dir=os.path.join(DBT_PROJECT_ROOT, ".")
        )
    return _metricflow_client

def load_metrics_config():
    """从 dbt 配置文件加载指标定义"""
    metrics_file = os.path.join(DBT_PROJECT_ROOT, "models", "metrics.yml")
    if not os.path.exists(metrics_file):
        return []
    
    with open(metrics_file, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
        return config.get('metrics', [])

def load_semantic_model():
    """从 dbt schema.yml 加载语义模型定义"""
    schema_file = os.path.join(DBT_PROJECT_ROOT, "models", "dws", "schema.yml")
    if not os.path.exists(schema_file):
        return None
    
    with open(schema_file, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
        semantic_models = config.get('semantic_models', [])
        if semantic_models:
            return semantic_models[0]  # 返回第一个语义模型
        return None

def get_measure_info(measure_name: str, semantic_model: Dict) -> Optional[Dict]:
    """获取 measure 的定义信息"""
    if not semantic_model:
        return None
    measures = semantic_model.get('measures', [])
    for measure in measures:
        if measure.get('name') == measure_name:
            return measure
    return None

def generate_metric_sql(metric: Dict, semantic_model: Dict, dimensions: List[str] = None, 
                        start_date: str = None, end_date: str = None, filters: Dict = None) -> str:
    """根据指标定义和语义模型生成 SQL（从 dbt 配置动态生成）"""
    metric_type = metric.get('type')
    type_params = metric.get('type_params', {})
    
    # 获取语义模型对应的表
    model_ref = semantic_model.get('model', 'dws_toll_revenue_daily')
    # 从 ref('xxx') 中提取表名
    if isinstance(model_ref, str) and "ref('" in model_ref:
        table_name = model_ref.split("ref('")[1].split("')")[0]
    else:
        table_name = str(model_ref).replace("ref('", "").replace("')", "")
    
    # 构建表名（DuckDB 格式）
    full_table_name = f"main_dws.{table_name}"
    
    # 构建 SELECT 子句
    select_fields = ["transaction_date"]
    
    # 添加维度字段
    valid_dimensions = []
    if dimensions:
        semantic_dims = {d['name']: d for d in semantic_model.get('dimensions', [])}
        for dim in dimensions:
            if dim in semantic_dims:
                select_fields.append(dim)
                valid_dimensions.append(dim)
    
    # 构建聚合表达式
    if metric_type == 'simple':
        # 简单指标：直接使用 measure 的聚合
        measure_name = type_params.get('measure')
        measure_info = get_measure_info(measure_name, semantic_model)
        
        if not measure_info:
            raise ValueError(f"找不到 measure: {measure_name}")
        
        measure_expr = measure_info.get('expr')
        measure_agg = measure_info.get('agg', 'sum')
        
        if measure_agg == 'sum':
            agg_expr = f"SUM({measure_expr})"
        elif measure_agg == 'average':
            agg_expr = f"AVG({measure_expr})"
        elif measure_agg == 'count':
            agg_expr = f"COUNT({measure_expr})"
        else:
            agg_expr = f"{measure_agg.upper()}({measure_expr})"
        select_fields.append(f"{agg_expr} as metric_value")
    
    elif metric_type == 'ratio':
        # 比率指标：分子/分母
        numerator_measure = get_measure_info(type_params.get('numerator'), semantic_model)
        denominator_measure = get_measure_info(type_params.get('denominator'), semantic_model)
        
        if not numerator_measure or not denominator_measure:
            raise ValueError(f"比率指标需要定义 numerator 和 denominator")
        
        num_expr = numerator_measure.get('expr')
        num_agg = numerator_measure.get('agg', 'sum')
        den_expr = denominator_measure.get('expr')
        den_agg = denominator_measure.get('agg', 'sum')
        
        if num_agg == 'sum':
            numerator = f"SUM({num_expr})"
        else:
            numerator = f"{num_agg.upper()}({num_expr})"
        
        if den_agg == 'sum':
            denominator = f"SUM({den_expr})"
        else:
            denominator = f"{den_agg.upper()}({den_expr})"
        
        select_fields.append(f"{numerator} * 100.0 / {denominator} as metric_value")
    
    else:
        raise ValueError(f"不支持的指标类型: {metric_type}")
    
    # 构建 SQL
    sql = f"SELECT {', '.join(select_fields)}\n"
    sql += f"FROM {full_table_name}\n"
    sql += "WHERE 1=1\n"
    
    # 添加时间过滤
    if start_date:
        sql += f" AND transaction_date >= '{start_date}'\n"
    if end_date:
        sql += f" AND transaction_date <= '{end_date}'\n"
    
    # 添加其他过滤条件
    if filters:
        for key, value in filters.items():
            if key in valid_dimensions:
                if isinstance(value, list):
                    values_str = ', '.join([f"'{v}'" for v in value])
                    sql += f" AND {key} IN ({values_str})\n"
                else:
                    sql += f" AND {key} = '{value}'\n"
    
    # 添加 GROUP BY（排除 metric_value）
    group_by_fields = select_fields[:-1]  # 排除最后一个 metric_value
    sql += f" GROUP BY {', '.join(group_by_fields)}\n"
    
    # 添加 ORDER BY
    sql += " ORDER BY transaction_date"
    
    return sql

# ==================== 数据模型 ====================

class TableInfo(BaseModel):
    schema_name: str
    table_name: str
    table_name_cn: Optional[str] = None
    table_description: str
    business_domain: str
    data_source: str
    update_frequency: str
    owner: str
    data_layer: str
    record_count: Optional[int] = None
    last_update_time: Optional[str] = None
    asset_level: Optional[str] = None
    usage_frequency: Optional[str] = None
    data_freshness: Optional[str] = None

class LineageEdge(BaseModel):
    source_table: str
    target_table: str
    transformation_type: str
    transformation_desc: str

class QualityMetric(BaseModel):
    metric_date: str
    table_name: str
    total_records: int
    normal_rate: float
    data_quality_rate: float
    overall_quality_score: float
    alert_status: str

class ColumnInfo(BaseModel):
    name: str
    description: Optional[str] = None
    data_type: Optional[str] = None

class MetricInfo(BaseModel):
    name: str
    description: str
    label: str
    type: str
    business_domain: Optional[str] = None
    owner: Optional[str] = None
    unit: Optional[str] = None

class MetricQuery(BaseModel):
    metric_name: str
    dimensions: Optional[List[str]] = None
    filters: Optional[Dict[str, Any]] = None
    time_granularity: Optional[str] = None  # day, week, month, year
    start_date: Optional[str] = None
    end_date: Optional[str] = None

class NaturalLanguageQuery(BaseModel):
    query: str  # 用户的自然语言问题
    use_llm: Optional[bool] = False  # 是否使用 LLM（需要配置 API Key）
    provider: Optional[str] = None  # LLM 提供商 ("openai", "deepseek")，默认从环境变量读取
    model: Optional[str] = None  # 模型名称，默认从环境变量读取

# ==================== API路由 ====================

@app.get("/api/")
async def api_root():
    return {"message": "数据中台API", "version": "1.0.0"}

@app.get("/api/tables", response_model=List[TableInfo])
async def get_tables(
    layer: Optional[str] = None,
    business_domain: Optional[str] = None,
    owner: Optional[str] = None,
    search: Optional[str] = None
):
    """获取数据表列表"""
    conn = get_db()
    try:
        query = """
        SELECT 
            ti.schema_name,
            ti.table_name,
            COALESCE(ti.table_name_cn, ti.table_name) as table_name_cn,
            ti.table_description,
            ti.business_domain,
            ti.data_source,
            ti.update_frequency,
            ti.owner,
            ti.data_layer,
            COALESCE(ac.record_count, 0) as record_count,
            CASE 
                WHEN ac.last_update_time IS NOT NULL 
                THEN CAST(ac.last_update_time AS VARCHAR)
                ELSE NULL
            END as last_update_time,
            COALESCE(ac.asset_level, '基础资产') as asset_level,
            COALESCE(ac.usage_frequency, '低频') as usage_frequency,
            COALESCE(ac.data_freshness, '未知') as data_freshness
        FROM main_metadata.meta_table_info ti
        LEFT JOIN main_metadata.meta_data_asset_catalog ac 
            ON ti.schema_name = ac.schema_name AND ti.table_name = ac.table_name
        WHERE 1=1
        """
        params = []
        
        if layer:
            query += " AND ti.data_layer = ?"
            params.append(layer)
        if business_domain:
            query += " AND ti.business_domain = ?"
            params.append(business_domain)
        if owner:
            query += " AND ti.owner = ?"
            params.append(owner)
        if search:
            query += " AND (ti.table_name LIKE ? OR ti.table_description LIKE ?)"
            params.extend([f"%{search}%", f"%{search}%"])
        
        query += " ORDER BY ti.data_layer, ti.table_name"
        
        result = conn.execute(query, params).fetchall()
        columns = [desc[0] for desc in conn.description]
        
        tables = []
        for row in result:
            table_dict = dict(zip(columns, row))
            # 转换datetime为字符串
            if 'last_update_time' in table_dict and table_dict['last_update_time']:
                if hasattr(table_dict['last_update_time'], 'isoformat'):
                    table_dict['last_update_time'] = table_dict['last_update_time'].isoformat()
            tables.append(TableInfo(**table_dict))
        
        return tables
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/api/tables/{schema_name}/{table_name}")
async def get_table_detail(schema_name: str, table_name: str):
    """获取表详情"""
    conn = get_db()
    try:
        # 获取表基本信息
        table_info = conn.execute("""
            SELECT * FROM main_metadata.meta_table_info
            WHERE schema_name = ? AND table_name = ?
        """, [schema_name, table_name]).fetchone()
        
        if not table_info:
            raise HTTPException(status_code=404, detail="表不存在")
        
        columns_info = conn.description
        table_dict = dict(zip([c[0] for c in columns_info], table_info))
        
        # 获取资产信息
        asset_info = conn.execute("""
            SELECT * FROM main_metadata.meta_data_asset_catalog
            WHERE schema_name = ? AND table_name = ?
        """, [schema_name, table_name]).fetchone()
        
        if asset_info:
            asset_columns = [c[0] for c in conn.description]
            table_dict.update(dict(zip(asset_columns, asset_info)))
        
        # 获取质量指标（最新）
        quality_info = conn.execute("""
            SELECT * FROM main_metadata.meta_data_quality_metrics
            WHERE table_name = ?
            ORDER BY metric_date DESC
            LIMIT 1
        """, [table_name]).fetchone()
        
        if quality_info:
            quality_columns = [c[0] for c in conn.description]
            table_dict['quality_metrics'] = dict(zip(quality_columns, quality_info))
        
        # 获取字段信息（从information_schema和字段元数据表）
        try:
            fields = conn.execute(f"""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_schema = ? AND table_name = ?
                ORDER BY ordinal_position
            """, [schema_name, table_name]).fetchall()
            
            # 获取字段中文名
            column_info_map = {}
            try:
                column_info = conn.execute("""
                    SELECT column_name, column_name_cn
                    FROM main_metadata.meta_column_info
                    WHERE schema_name = ? AND table_name = ?
                """, [schema_name, table_name]).fetchall()
                column_info_map = {row[0]: row[1] for row in column_info}
            except:
                pass
            
            table_dict['columns'] = [
                {
                    "name": f[0], 
                    "data_type": f[1],
                    "name_cn": column_info_map.get(f[0], f[0])
                } 
                for f in fields
            ]
        except:
            table_dict['columns'] = []
        
        return table_dict
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/api/tables/{schema_name}/{table_name}/preview")
async def get_table_preview(
    schema_name: str, 
    table_name: str,
    limit: int = 100,
    offset: int = 0
):
    """获取数据预览"""
    conn = get_db()
    try:
        # 获取数据
        full_table_name = f"{schema_name}.{table_name}"
        result = conn.execute(f"""
            SELECT * FROM {full_table_name}
            LIMIT ? OFFSET ?
        """, [limit, offset]).fetchall()
        
        # 获取列名
        columns = [desc[0] for desc in conn.description]
        
        # 获取字段中文名
        column_info_map = {}
        try:
            column_info = conn.execute("""
                SELECT column_name, column_name_cn
                FROM main_metadata.meta_column_info
                WHERE schema_name = ? AND table_name = ?
            """, [schema_name, table_name]).fetchall()
            column_info_map = {row[0]: row[1] for row in column_info}
        except:
            pass
        
        # 获取总数
        total = conn.execute(f"SELECT COUNT(*) FROM {full_table_name}").fetchone()[0]
        
        return {
            "columns": columns,
            "columns_cn": {col: column_info_map.get(col, col) for col in columns},
            "data": [dict(zip(columns, row)) for row in result],
            "total": total,
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/api/lineage", response_model=List[LineageEdge])
async def get_lineage(
    table_name: Optional[str] = None,
    direction: Optional[str] = None  # 'up' or 'down'
):
    """获取数据溯源关系"""
    conn = get_db()
    try:
        query = "SELECT * FROM main_metadata.meta_data_lineage WHERE 1=1"
        params = []
        
        if table_name:
            if direction == 'up':
                query += " AND target_table LIKE ?"
            elif direction == 'down':
                query += " AND source_table LIKE ?"
            else:
                query += " AND (source_table LIKE ? OR target_table LIKE ?)"
                params.append(f"%{table_name}%")
            
            params.append(f"%{table_name}%")
        
        query += " ORDER BY source_table, target_table"
        
        result = conn.execute(query, params).fetchall()
        columns = [desc[0] for desc in conn.description]
        
        lineage = []
        for row in result:
            edge_dict = dict(zip(columns, row))
            lineage.append(LineageEdge(**edge_dict))
        
        return lineage
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/api/lineage/graph")
async def get_lineage_graph():
    """获取溯源关系图数据（用于可视化）"""
    conn = get_db()
    try:
        # 获取所有溯源关系
        edges = conn.execute("SELECT * FROM main_metadata.meta_data_lineage").fetchall()
        edge_columns = [desc[0] for desc in conn.description]
        
        # 获取所有表信息
        tables = conn.execute("SELECT schema_name, table_name, data_layer FROM main_metadata.meta_table_info").fetchall()
        
        # 构建节点集合
        nodes_set = set()
        for edge in edges:
            nodes_set.add(edge[0])  # source_table
            nodes_set.add(edge[1])  # target_table
        
        # 构建节点列表
        nodes = []
        for node_id in nodes_set:
            # 查找对应的表信息
            table_info = next((t for t in tables if f"{t[0]}.{t[1]}" == node_id), None)
            layer = table_info[2] if table_info else "unknown"
            
            nodes.append({
                "id": node_id,
                "label": node_id.split(".")[-1],
                "layer": layer,
                "full_name": node_id
            })
        
        # 构建边列表
        edges_list = []
        for edge in edges:
            edge_dict = dict(zip(edge_columns, edge))
            edges_list.append({
                "source": edge_dict["source_table"],
                "target": edge_dict["target_table"],
                "type": edge_dict["transformation_type"],
                "description": edge_dict["transformation_desc"]
            })
        
        return {
            "nodes": nodes,
            "edges": edges_list
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/api/quality/metrics", response_model=List[QualityMetric])
async def get_quality_metrics(
    days: int = 30,
    table_name: Optional[str] = None
):
    """获取数据质量指标"""
    conn = get_db()
    try:
        query = f"""
            SELECT 
                metric_date,
                table_name,
                total_records,
                accuracy_rate as normal_rate,
                consistency_rate as data_quality_rate,
                overall_quality_score,
                CASE 
                    WHEN overall_quality_score >= 95 THEN '正常'
                    WHEN overall_quality_score >= 80 THEN '警告'
                    ELSE '告警'
                END as alert_status
            FROM main_metadata.meta_data_quality_metrics
            WHERE metric_date >= CURRENT_DATE - INTERVAL '{days} days'
        """
        params = []
        
        if table_name:
            query += " AND table_name = ?"
            params.append(table_name)
        
        query += " ORDER BY metric_date DESC"
        
        if params:
            result = conn.execute(query, params).fetchall()
        else:
            result = conn.execute(query).fetchall()
        columns = [desc[0] for desc in conn.description]
        
        metrics = []
        for row in result:
            metric_dict = dict(zip(columns, row))
            # 转换date/datetime为字符串
            if 'metric_date' in metric_dict and metric_dict['metric_date']:
                if hasattr(metric_dict['metric_date'], 'isoformat'):
                    metric_dict['metric_date'] = metric_dict['metric_date'].isoformat()
                elif hasattr(metric_dict['metric_date'], 'strftime'):
                    metric_dict['metric_date'] = metric_dict['metric_date'].strftime('%Y-%m-%d')
            metrics.append(QualityMetric(**metric_dict))
        
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/api/quality/dashboard")
async def get_quality_dashboard():
    """获取质量监控看板数据"""
    conn = get_db()
    try:
        # 获取最新的质量看板数据
        result = conn.execute("""
            SELECT * FROM main_ads.ads_quality_monitoring_dashboard
            ORDER BY transaction_date DESC
            LIMIT 30
        """).fetchall()
        
        columns = [desc[0] for desc in conn.description]
        
        dashboard_data = []
        for row in result:
            row_dict = dict(zip(columns, row))
            # 转换日期字段
            if 'transaction_date' in row_dict and row_dict['transaction_date']:
                if hasattr(row_dict['transaction_date'], 'isoformat'):
                    row_dict['transaction_date'] = row_dict['transaction_date'].isoformat()
                elif hasattr(row_dict['transaction_date'], 'strftime'):
                    row_dict['transaction_date'] = row_dict['transaction_date'].strftime('%Y-%m-%d')
            dashboard_data.append(row_dict)
        
        # 计算汇总统计
        if dashboard_data:
            latest = dashboard_data[0]
            summary = {
                "total_transactions": latest.get("total_transactions", 0),
                "normal_rate": latest.get("normal_rate", 0),
                "data_quality_rate": latest.get("data_quality_rate", 0),
                "alert_status": latest.get("alert_status", "正常"),
                "abnormal_count": latest.get("abnormal_transactions", 0)
            }
        else:
            summary = {}
        
        return {
            "summary": summary,
            "trend": dashboard_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/api/reports/revenue")
async def get_revenue_report(days: int = 30):
    """获取收费收入报表"""
    conn = get_db()
    try:
        # DuckDB使用DATE_SUB或直接计算日期
        result = conn.execute(f"""
            SELECT * FROM main_ads.ads_toll_revenue_report
            WHERE transaction_date >= CURRENT_DATE - INTERVAL '{days} days'
            ORDER BY transaction_date DESC
        """).fetchall()
        
        columns = [desc[0] for desc in conn.description]
        
        # 转换日期字段为字符串
        result_list = []
        for row in result:
            row_dict = dict(zip(columns, row))
            # 转换transaction_date
            if 'transaction_date' in row_dict and row_dict['transaction_date']:
                if hasattr(row_dict['transaction_date'], 'isoformat'):
                    row_dict['transaction_date'] = row_dict['transaction_date'].isoformat()
                elif hasattr(row_dict['transaction_date'], 'strftime'):
                    row_dict['transaction_date'] = row_dict['transaction_date'].strftime('%Y-%m-%d')
            result_list.append(row_dict)
        
        return result_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/api/reports/traffic")
async def get_traffic_report(days: int = 30):
    """获取车流趋势报表"""
    conn = get_db()
    try:
        result = conn.execute(f"""
            SELECT * FROM main_ads.ads_traffic_trend_analysis
            WHERE transaction_date >= CURRENT_DATE - INTERVAL '{days} days'
            ORDER BY transaction_date DESC
        """).fetchall()
        
        columns = [desc[0] for desc in conn.description]
        
        # 转换日期字段为字符串
        result_list = []
        for row in result:
            row_dict = dict(zip(columns, row))
            # 转换transaction_date
            if 'transaction_date' in row_dict and row_dict['transaction_date']:
                if hasattr(row_dict['transaction_date'], 'isoformat'):
                    row_dict['transaction_date'] = row_dict['transaction_date'].isoformat()
                elif hasattr(row_dict['transaction_date'], 'strftime'):
                    row_dict['transaction_date'] = row_dict['transaction_date'].strftime('%Y-%m-%d')
            result_list.append(row_dict)
        
        return result_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/api/metrics", response_model=List[MetricInfo])
async def get_metrics():
    """获取所有可用的业务指标列表（优先从 MetricFlow 读取，失败则从 dbt metrics.yml 读取）"""
    try:
        # 首先尝试从 MetricFlow 获取
        mf_client = get_metricflow_client()
        mf_metrics = mf_client.list_metrics()
        
        if mf_metrics:
            # 转换 MetricFlow 格式到 API 格式
            metrics = []
            for mf_metric in mf_metrics:
                # MetricFlow 返回的格式可能不同，需要适配
                metric_name = mf_metric.get('name') or mf_metric.get('metric_name', '')
                if metric_name:
                    metrics.append({
                        "name": metric_name,
                        "description": mf_metric.get('description', ''),
                        "label": mf_metric.get('label') or mf_metric.get('display_name', metric_name),
                        "type": mf_metric.get('type', 'simple'),
                        "business_domain": mf_metric.get('business_domain'),
                        "owner": mf_metric.get('owner'),
                        "unit": mf_metric.get('unit')
                    })
            
            if metrics:
                return [MetricInfo(**m) for m in metrics]
        
        # 如果 MetricFlow 失败，回退到配置文件
        logger.info("MetricFlow 未返回指标，使用配置文件")
        metrics_config = load_metrics_config()
        if not metrics_config:
            return []
        
        # 转换为 API 响应格式
        metrics = []
        for metric in metrics_config:
            meta = metric.get('meta', {})
            metrics.append({
                "name": metric.get('name'),
                "description": metric.get('description', ''),
                "label": metric.get('label', metric.get('name')),
                "type": metric.get('type', 'simple'),
                "business_domain": meta.get('business_domain'),
                "owner": meta.get('owner'),
                "unit": meta.get('unit')
            })
        
        return [MetricInfo(**m) for m in metrics]
    except Exception as e:
        logger.error(f"加载指标失败: {e}")
        raise HTTPException(status_code=500, detail=f"加载指标配置失败: {str(e)}")

@app.post("/api/metrics/query")
async def query_metric(query: MetricQuery):
    """根据指标名称和维度查询数据（使用 MetricFlow 生成 SQL）"""
    conn = get_db()
    try:
        # 使用 MetricFlow 生成 SQL
        mf_client = get_metricflow_client()
        
        # 构建 WHERE 条件
        where_conditions = []
        if query.filters:
            for key, value in query.filters.items():
                if isinstance(value, list):
                    values_str = ', '.join([f"'{v}'" for v in value])
                    where_conditions.append(f"{key} IN ({values_str})")
                else:
                    where_conditions.append(f"{key} = '{value}'")
        
        # 构建分组维度（包括时间维度）
        group_by = []
        if query.dimensions:
            group_by.extend(query.dimensions)
        # MetricFlow 需要时间维度
        group_by.append('transaction_date')
        
        # 使用 MetricFlow 生成 SQL
        mf_result = mf_client.query_metrics(
            metrics=[query.metric_name],
            group_by=group_by if group_by else None,
            where=where_conditions if where_conditions else None,
            start_time=query.start_date,
            end_time=query.end_date
        )
        
        if not mf_result.get('success', True) or not mf_result.get('sql'):
            # 如果 MetricFlow 失败，回退到原来的方法
            logger.warning(f"MetricFlow 生成 SQL 失败，使用备用方法: {mf_result.get('error', 'Unknown error')}")
            return await _query_metric_fallback(query, conn)
        
        sql = mf_result['sql']
        
        # 执行查询
        result = conn.execute(sql).fetchall()
        columns = [desc[0] for desc in conn.description]
        
        return {
            "metric_name": query.metric_name,
            "data": [dict(zip(columns, row)) for row in result],
            "query_sql": sql,  # 返回生成的SQL，便于调试和审计
            "generated_by": "MetricFlow"  # 标识由 MetricFlow 生成
        }
    except HTTPException:
        raise
    except Exception as e:
        # 如果出错，回退到原来的方法
        logger.error(f"MetricFlow 查询失败: {e}，使用备用方法")
        return await _query_metric_fallback(query, conn)
    finally:
        conn.close()

async def _query_metric_fallback(query: MetricQuery, conn):
    """备用查询方法（使用原来的配置驱动方式）"""
    try:
        # 从 dbt 配置文件加载指标定义
        metrics_config = load_metrics_config()
        semantic_model = load_semantic_model()
        
        if not metrics_config:
            raise HTTPException(status_code=500, detail="无法加载指标配置")
        
        if not semantic_model:
            raise HTTPException(status_code=500, detail="无法加载语义模型")
        
        # 查找指定的指标
        metric = None
        for m in metrics_config:
            if m.get('name') == query.metric_name:
                metric = m
                break
        
        if not metric:
            raise HTTPException(status_code=404, detail=f"指标 {query.metric_name} 不存在")
        
        # 使用 dbt 配置动态生成 SQL
        sql = generate_metric_sql(
            metric=metric,
            semantic_model=semantic_model,
            dimensions=query.dimensions,
            start_date=query.start_date,
            end_date=query.end_date,
            filters=query.filters
        )
        
        # 执行查询
        result = conn.execute(sql).fetchall()
        columns = [desc[0] for desc in conn.description]
        
        return {
            "metric_name": query.metric_name,
            "data": [dict(zip(columns, row)) for row in result],
            "query_sql": sql,
            "generated_by": "Config-based"  # 标识由配置生成
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")

@app.post("/api/metrics/query/natural")
async def query_metric_natural(nl_query: NaturalLanguageQuery):
    """
    使用自然语言查询指标（支持 LLM 解析）
    
    示例：
    - "查询最近7天的日收入，按城市分组"
    - "显示北京本月的交易笔数"
    - "查看昨天的正常交易率"
    """
    try:
        # 获取可用指标和维度
        metrics_config = load_metrics_config()
        if not metrics_config:
            raise HTTPException(status_code=500, detail="无法加载指标配置")
        
        # 可用维度
        semantic_model = load_semantic_model()
        available_dimensions = []
        if semantic_model:
            available_dimensions = [d['name'] for d in semantic_model.get('dimensions', [])]
        
        # 转换为 API 格式
        metrics_for_parser = []
        for m in metrics_config:
            metrics_for_parser.append({
                'name': m.get('name'),
                'label': m.get('label', m.get('name')),
                'description': m.get('description', '')
            })
        
        # 选择解析器
        if nl_query.use_llm:
            # 使用 LLM 解析（需要配置 API Key）
            # 可以从环境变量读取，支持 OpenAI 和 DeepSeek
            api_key = os.getenv('DEEPSEEK_API_KEY') or os.getenv('OPENAI_API_KEY') or os.getenv('LLM_API_KEY')
            
            # 根据参数或环境变量选择提供商
            provider = nl_query.provider or os.getenv('LLM_PROVIDER', 'openai').lower()
            if provider == 'deepseek' or os.getenv('DEEPSEEK_API_KEY'):
                provider = 'deepseek'
                model = nl_query.model or os.getenv('DEEPSEEK_MODEL', 'deepseek-chat')
                # 确保使用 DeepSeek API Key
                if not api_key or not os.getenv('DEEPSEEK_API_KEY'):
                    api_key = os.getenv('DEEPSEEK_API_KEY')
            else:
                provider = 'openai'
                model = nl_query.model or os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')
            
            logger.info(f"使用 LLM 解析自然语言查询: provider={provider}, model={model}, query={nl_query.query}")
            
            parser = LLMQueryParserWithAPI(
                available_metrics=metrics_for_parser,
                available_dimensions=available_dimensions,
                api_key=api_key,
                model=model,
                provider=provider
            )
        else:
            # 使用规则解析
            logger.info(f"使用规则解析自然语言查询: query={nl_query.query}")
            parser = LLMQueryParser(
                available_metrics=metrics_for_parser,
                available_dimensions=available_dimensions
            )
        
        # 解析自然语言查询
        parsed_query = parser.parse(nl_query.query)
        logger.info(f"解析结果: {parsed_query}")
        
        if not parsed_query.get('metric_name'):
            raise HTTPException(
                status_code=400, 
                detail=f"无法从问题中识别指标。可用指标: {[m['name'] for m in metrics_for_parser]}"
            )
        
        # 构建 MetricQuery
        metric_query = MetricQuery(
            metric_name=parsed_query['metric_name'],
            dimensions=parsed_query.get('dimensions'),
            start_date=parsed_query.get('start_date'),
            end_date=parsed_query.get('end_date'),
            filters=parsed_query.get('filters')
        )
        
        # 执行查询（复用现有逻辑）
        conn = get_db()
        try:
            result = await _query_metric_fallback(metric_query, conn)
            result['parsed_query'] = parsed_query  # 返回解析结果，便于调试
            result['original_query'] = nl_query.query
            return result
        finally:
            conn.close()
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"自然语言查询失败: {e}")
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")

@app.get("/api/stats/overview")
async def get_stats_overview():
    """获取统计概览"""
    conn = get_db()
    try:
        # 表统计
        table_stats = conn.execute("""
            SELECT 
                data_layer,
                COUNT(*) as count
            FROM main_metadata.meta_table_info
            GROUP BY data_layer
        """).fetchall()
        
        # 质量统计
        quality_stats = conn.execute("""
            SELECT 
                AVG(overall_quality_score) as avg_score,
                COUNT(CASE WHEN overall_quality_score < 80 THEN 1 END) as alert_count
            FROM main_metadata.meta_data_quality_metrics
            WHERE metric_date = (SELECT MAX(metric_date) FROM main_metadata.meta_data_quality_metrics)
        """).fetchone()
        
        return {
            "tables_by_layer": {row[0]: row[1] for row in table_stats},
            "quality": {
                "avg_score": quality_stats[0] if quality_stats[0] else 0,
                "alert_count": quality_stats[1] if quality_stats[1] else 0
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

# 前端路由处理（必须在所有API路由之后）
if os.path.exists(FRONTEND_DIST):
    # 挂载静态文件
    app.mount("/static", StaticFiles(directory=os.path.join(FRONTEND_DIST, "static")), name="static")
    
    # 前端路由处理（SPA需要）- 放在最后，确保API路由优先
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        """服务前端应用，处理所有非API路由"""
        # API路由不处理（这些路由应该已经在上面定义了）
        if full_path.startswith("api") or full_path.startswith("docs") or full_path.startswith("openapi.json"):
            raise HTTPException(status_code=404, detail="Not found")
        
        # 检查是否是静态资源
        file_path = os.path.join(FRONTEND_DIST, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        
        # 其他路由返回index.html（SPA路由）
        index_path = os.path.join(FRONTEND_DIST, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        
        raise HTTPException(status_code=404, detail="Not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8090)

