-- ODS层：收费站操作数据存储

{{ config(
    materialized='table',
    tags=['ods', 'toll_station']
) }}

SELECT 
    station_id,
    station_name,
    city,
    highway_code,
    station_type,
    open_date,
    -- 业务字段
    CASE 
        WHEN station_type = '主线收费站' THEN 1
        ELSE 0
    END AS is_main_station,
    CURRENT_DATE - open_date AS days_since_open,
    etl_time
FROM {{ ref('stg_toll_station') }}

