-- ADS层：收费收入报表
-- 功能：面向业务应用的收入报表

{{ config(
    materialized='table',
    tags=['ads', 'report', 'revenue']
) }}

SELECT 
    transaction_date,
    city,
    highway_code,
    -- 总体指标
    SUM(total_actual_amount) AS daily_revenue,
    SUM(transaction_count) AS daily_transactions,
    SUM(vehicle_count) AS daily_vehicles,
    AVG(avg_transaction_amount) AS avg_transaction_amount,
    -- 按支付方式
    SUM(CASE WHEN payment_method_code = 'P01' THEN total_actual_amount ELSE 0 END) AS etc_revenue,
    SUM(CASE WHEN payment_method_code != 'P01' THEN total_actual_amount ELSE 0 END) AS non_etc_revenue,
    -- 按车型
    SUM(CASE WHEN vehicle_type_code LIKE 'V0%' AND vehicle_type_code < 'V05' THEN total_actual_amount ELSE 0 END) AS passenger_revenue,
    SUM(CASE WHEN vehicle_type_code >= 'V05' THEN total_actual_amount ELSE 0 END) AS truck_revenue,
    -- 质量指标
    SUM(normal_transaction_count) * 100.0 / SUM(transaction_count) AS normal_rate,
    SUM(quality_normal_count) * 100.0 / SUM(transaction_count) AS data_quality_rate,
    -- 时间维度
    MAX(last_update_time) AS last_update_time
FROM {{ ref('dws_toll_revenue_daily') }}
GROUP BY 
    transaction_date,
    city,
    highway_code

