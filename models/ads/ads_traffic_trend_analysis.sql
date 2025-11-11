-- ADS层：车流趋势分析
-- 功能：车流趋势和模式分析

{{ config(
    materialized='table',
    tags=['ads', 'analysis', 'traffic']
) }}

SELECT 
    transaction_date,
    city,
    highway_code,
    day_type,
    -- 车流量趋势
    SUM(total_vehicles) AS daily_vehicles,
    SUM(unique_vehicles) AS daily_unique_vehicles,
    -- 时段分布
    SUM(CASE WHEN time_period = '早高峰' THEN total_vehicles ELSE 0 END) AS morning_peak_vehicles,
    SUM(CASE WHEN time_period = '晚高峰' THEN total_vehicles ELSE 0 END) AS evening_peak_vehicles,
    SUM(CASE WHEN time_period = '平峰' THEN total_vehicles ELSE 0 END) AS normal_vehicles,
    SUM(CASE WHEN time_period = '夜间' THEN total_vehicles ELSE 0 END) AS night_vehicles,
    -- 车型分布
    SUM(passenger_vehicle_count) AS passenger_vehicles,
    SUM(bus_count) AS bus_vehicles,
    SUM(truck_count) AS truck_vehicles,
    -- ETC使用率
    SUM(etc_count) * 100.0 / SUM(total_vehicles) AS etc_usage_rate,
    -- 平均通行时长
    AVG(avg_travel_minutes) AS avg_travel_minutes,
    -- 时间维度
    MAX(last_update_time) AS last_update_time
FROM {{ ref('dws_traffic_flow_daily') }}
GROUP BY 
    transaction_date,
    city,
    highway_code,
    day_type

