-- DWS层：日车流量汇总
-- 功能：按日期、收费站、时段等维度汇总车流量

{{ config(
    materialized='table',
    tags=['dws', 'traffic', 'daily']
) }}

SELECT 
    transaction_date,
    station_id,
    station_name,
    city,
    highway_code,
    station_type,
    time_period,
    day_type,
    -- 车流量指标
    COUNT(*) AS total_vehicles,
    COUNT(DISTINCT vehicle_plate) AS unique_vehicles,
    -- 车型分布
    SUM(CASE WHEN vehicle_type_code LIKE 'V0%' THEN 1 ELSE 0 END) AS passenger_vehicle_count,
    SUM(CASE WHEN vehicle_type_code LIKE 'V0%' AND vehicle_type_code != 'V01' THEN 1 ELSE 0 END) AS bus_count,
    SUM(CASE WHEN vehicle_type_code LIKE 'V0%' AND vehicle_type_code >= 'V05' THEN 1 ELSE 0 END) AS truck_count,
    -- 平均通行时长
    AVG(travel_minutes) AS avg_travel_minutes,
    -- 支付方式分布
    SUM(CASE WHEN payment_method_code = 'P01' THEN 1 ELSE 0 END) AS etc_count,
    SUM(CASE WHEN payment_method_code != 'P01' THEN 1 ELSE 0 END) AS non_etc_count,
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
    time_period,
    day_type

