-- 元数据管理：数据资产目录
-- 功能：数据资产清单和价值评估

{{ config(
    materialized='table',
    tags=['metadata', 'data_asset']
) }}

WITH table_stats AS (
    SELECT 
        'dwd.dwd_toll_transaction_detail' AS table_name,
        COUNT(*) AS record_count,
        MAX(etl_time) AS last_update_time
    FROM {{ ref('dwd_toll_transaction_detail') }}
    GROUP BY 1
    UNION ALL
    SELECT 
        'dws.dws_toll_revenue_daily',
        COUNT(*),
        MAX(last_update_time)
    FROM {{ ref('dws_toll_revenue_daily') }}
    GROUP BY 1
    UNION ALL
    SELECT 
        'dws.dws_traffic_flow_daily',
        COUNT(*),
        MAX(last_update_time)
    FROM {{ ref('dws_traffic_flow_daily') }}
    GROUP BY 1
    UNION ALL
    SELECT 
        'ads.ads_toll_revenue_report',
        COUNT(*),
        MAX(last_update_time)
    FROM {{ ref('ads_toll_revenue_report') }}
    GROUP BY 1
)

SELECT 
    ti.schema_name,
    ti.table_name,
    ti.table_description,
    ti.business_domain,
    ti.data_layer,
    ti.owner,
    COALESCE(ts.record_count, 0) AS record_count,
    COALESCE(ts.last_update_time, CURRENT_TIMESTAMP) AS last_update_time,
    -- 资产等级评估
    CASE 
        WHEN ti.data_layer IN ('dwd', 'dws') THEN '核心资产'
        WHEN ti.data_layer = 'ads' THEN '应用资产'
        ELSE '基础资产'
    END AS asset_level,
    -- 使用频率评估（基于更新频率）
    CASE 
        WHEN ti.update_frequency = '实时' THEN '高频'
        WHEN ti.update_frequency = '日' THEN '中频'
        ELSE '低频'
    END AS usage_frequency,
    -- 数据新鲜度
    CASE 
        WHEN ts.last_update_time IS NULL THEN '未知'
        WHEN CURRENT_TIMESTAMP - ts.last_update_time < INTERVAL 1 DAY THEN '新鲜'
        WHEN CURRENT_TIMESTAMP - ts.last_update_time < INTERVAL 7 DAY THEN '较新'
        ELSE '陈旧'
    END AS data_freshness,
    CURRENT_TIMESTAMP AS catalog_time
FROM {{ ref('meta_table_info') }} ti
LEFT JOIN table_stats ts ON CONCAT(ti.schema_name, '.', ti.table_name) = ts.table_name

