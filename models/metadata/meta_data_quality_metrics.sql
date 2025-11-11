-- 元数据管理：数据质量指标表
-- 功能：记录数据质量指标和趋势

{{ config(
    materialized='table',
    tags=['metadata', 'data_quality']
) }}

SELECT 
    transaction_date AS metric_date,
    'dwd_toll_transaction_detail' AS table_name,
    -- 完整性指标
    COUNT(*) AS total_records,
    SUM(CASE WHEN transaction_id IS NOT NULL THEN 1 ELSE 0 END) AS complete_transaction_id,
    SUM(CASE WHEN station_id IS NOT NULL THEN 1 ELSE 0 END) AS complete_station_id,
    SUM(CASE WHEN vehicle_plate IS NOT NULL AND vehicle_plate != '' THEN 1 ELSE 0 END) AS complete_vehicle_plate,
    -- 完整性率
    SUM(CASE WHEN transaction_id IS NOT NULL THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS transaction_id_completeness_rate,
    SUM(CASE WHEN station_id IS NOT NULL THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS station_id_completeness_rate,
    SUM(CASE WHEN vehicle_plate IS NOT NULL AND vehicle_plate != '' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS vehicle_plate_completeness_rate,
    -- 准确性指标
    SUM(CASE WHEN is_normal_transaction = 1 THEN 1 ELSE 0 END) AS normal_transactions,
    SUM(CASE WHEN is_normal_transaction = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS accuracy_rate,
    -- 一致性指标
    SUM(CASE WHEN data_quality_flag = '正常' THEN 1 ELSE 0 END) AS consistent_records,
    SUM(CASE WHEN data_quality_flag = '正常' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS consistency_rate,
    -- 及时性指标
    MAX(etl_time) AS last_etl_time,
    CURRENT_TIMESTAMP - MAX(etl_time) AS etl_delay,
    -- 综合质量得分（0-100）
    (
        (SUM(CASE WHEN transaction_id IS NOT NULL THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) * 0.2 +
        (SUM(CASE WHEN station_id IS NOT NULL THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) * 0.2 +
        (SUM(CASE WHEN vehicle_plate IS NOT NULL AND vehicle_plate != '' THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) * 0.2 +
        (SUM(CASE WHEN is_normal_transaction = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) * 0.2 +
        (SUM(CASE WHEN data_quality_flag = '正常' THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) * 0.2
    ) AS overall_quality_score,
    CURRENT_TIMESTAMP AS metric_time
FROM {{ ref('dwd_toll_transaction_detail') }}
GROUP BY transaction_date

