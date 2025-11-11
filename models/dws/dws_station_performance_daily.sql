-- DWS层：收费站日绩效汇总
-- 功能：收费站维度的综合绩效指标

{{ config(
    materialized='table',
    tags=['dws', 'performance', 'daily']
) }}

SELECT 
    transaction_date,
    station_id,
    station_name,
    city,
    highway_code,
    station_type,
    -- 交易量指标
    COUNT(*) AS total_transactions,
    COUNT(DISTINCT vehicle_plate) AS unique_vehicles,
    COUNT(DISTINCT lane_id) AS active_lanes,
    -- 收入指标
    SUM(actual_amount) AS total_revenue,
    AVG(actual_amount) AS avg_revenue_per_transaction,
    -- 效率指标
    AVG(travel_minutes) AS avg_processing_time_minutes,
    -- 质量指标
    SUM(CASE WHEN is_normal_transaction = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS normal_rate,
    SUM(CASE WHEN data_quality_flag = '正常' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS data_quality_rate,
    -- 支付方式分布
    SUM(CASE WHEN payment_method_code = 'P01' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS etc_rate,
    -- 高峰时段占比
    SUM(CASE WHEN time_period IN ('早高峰', '晚高峰') THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS peak_hour_rate,
    -- 时间维度
    MAX(etl_time) AS last_update_time
FROM {{ ref('dwd_toll_transaction_detail') }}
GROUP BY 
    transaction_date,
    station_id,
    station_name,
    city,
    highway_code,
    station_type

