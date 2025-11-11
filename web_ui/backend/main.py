"""
数据中台Web UI后端API
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import duckdb
import os
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime, timedelta

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

def get_db():
    """获取数据库连接"""
    return duckdb.connect(DB_PATH)

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

