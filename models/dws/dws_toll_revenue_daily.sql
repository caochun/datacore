-- DWS层：日收费收入汇总
-- 功能：按日期、收费站、车型、支付方式等维度汇总

{{ config(
    materialized='table',
    tags=['dws', 'revenue', 'daily']
) }}

SELECT 
    transaction_date,
    station_id,
    station_name,
    city,
    highway_code,
    station_type,
    vehicle_type_code,
    vehicle_type_name,
    payment_method_code,
    payment_method_name,
    -- 汇总指标
    COUNT(*) AS transaction_count,
    COUNT(DISTINCT vehicle_plate) AS vehicle_count,
    SUM(toll_amount) AS total_toll_amount,
    SUM(actual_amount) AS total_actual_amount,
    SUM(discount_amount) AS total_discount_amount,
    AVG(actual_amount) AS avg_transaction_amount,
    MAX(actual_amount) AS max_transaction_amount,
    MIN(actual_amount) AS min_transaction_amount,
    -- 正常交易统计
    SUM(CASE WHEN is_normal_transaction = 1 THEN 1 ELSE 0 END) AS normal_transaction_count,
    SUM(CASE WHEN is_normal_transaction = 1 THEN actual_amount ELSE 0 END) AS normal_transaction_amount,
    -- 异常交易统计
    SUM(CASE WHEN is_normal_transaction = 0 THEN 1 ELSE 0 END) AS abnormal_transaction_count,
    -- 数据质量指标
    SUM(CASE WHEN data_quality_flag = '正常' THEN 1 ELSE 0 END) AS quality_normal_count,
    SUM(CASE WHEN data_quality_flag != '正常' THEN 1 ELSE 0 END) AS quality_abnormal_count,
    -- 时间维度
    MAX(etl_time) AS last_update_time
FROM {{ ref('dwd_toll_transaction_detail') }}
GROUP BY 
    transaction_date,
    station_id,
    station_name,
    city,
    highway_code,
    station_type,
    vehicle_type_code,
    vehicle_type_name,
    payment_method_code,
    payment_method_name

