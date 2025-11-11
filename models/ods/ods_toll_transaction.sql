-- ODS层：收费交易操作数据存储
-- 功能：保持业务原始逻辑，关联字典表，增加业务字段

{{ config(
    materialized='table',
    tags=['ods', 'toll_transaction']
) }}

SELECT 
    t.transaction_id,
    t.station_id,
    s.station_name,
    s.city,
    s.highway_code,
    s.station_type,
    t.lane_id,
    t.vehicle_plate,
    t.vehicle_type_code,
    vt.vehicle_type_name,
    vt.vehicle_type_desc,
    t.entry_station_id,
    es.station_name AS entry_station_name,
    t.entry_time,
    t.exit_time,
    t.travel_minutes,
    t.payment_method_code,
    pm.payment_method_name,
    pm.payment_method_desc,
    t.toll_amount,
    t.actual_amount,
    t.discount_amount,
    t.transaction_status,
    t.data_quality_flag,
    -- 业务字段
    DATE(t.exit_time) AS transaction_date,
    EXTRACT(HOUR FROM t.exit_time) AS transaction_hour,
    EXTRACT(DOW FROM t.exit_time) AS day_of_week,
    CASE 
        WHEN t.transaction_status = '正常' THEN 1 
        ELSE 0 
    END AS is_normal_transaction,
    t.create_time,
    t.update_time,
    t.etl_time
FROM {{ ref('stg_toll_transaction') }} t
LEFT JOIN {{ ref('stg_toll_station') }} s ON t.station_id = s.station_id
LEFT JOIN {{ ref('stg_toll_station') }} es ON t.entry_station_id = es.station_id
LEFT JOIN {{ ref('stg_vehicle_type_dict') }} vt ON t.vehicle_type_code = vt.vehicle_type_code
LEFT JOIN {{ ref('stg_payment_method_dict') }} pm ON t.payment_method_code = pm.payment_method_code

