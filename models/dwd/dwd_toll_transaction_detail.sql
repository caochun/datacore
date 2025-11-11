-- DWD层：收费交易明细数据
-- 功能：业务明细数据，便于后续分析

{{ config(
    materialized='table',
    tags=['dwd', 'toll_transaction']
) }}

SELECT 
    transaction_id,
    station_id,
    station_name,
    city,
    highway_code,
    station_type,
    lane_id,
    vehicle_plate,
    vehicle_type_code,
    vehicle_type_name,
    vehicle_type_desc,
    entry_station_id,
    entry_station_name,
    entry_time,
    exit_time,
    travel_minutes,
    -- 计算通行距离（估算，基于时间）
    CASE 
        WHEN travel_minutes > 0 THEN 
            ROUND(travel_minutes * 60 / 100.0, 2)  -- 假设平均速度100km/h
        ELSE 0
    END AS estimated_distance_km,
    payment_method_code,
    payment_method_name,
    payment_method_desc,
    toll_amount,
    actual_amount,
    discount_amount,
    transaction_status,
    data_quality_flag,
    transaction_date,
    transaction_hour,
    day_of_week,
    is_normal_transaction,
    -- 业务分类
    CASE 
        WHEN transaction_hour BETWEEN 6 AND 9 THEN '早高峰'
        WHEN transaction_hour BETWEEN 17 AND 20 THEN '晚高峰'
        WHEN transaction_hour BETWEEN 22 AND 6 THEN '夜间'
        ELSE '平峰'
    END AS time_period,
    CASE 
        WHEN day_of_week IN (0, 6) THEN '周末'  -- DOW: 0=周日, 6=周六
        ELSE '工作日'
    END AS day_type,
    create_time,
    update_time,
    etl_time
FROM {{ ref('ods_toll_transaction') }}

