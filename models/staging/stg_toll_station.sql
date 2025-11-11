-- 收费站数据清洗层

{{ config(
    materialized='view',
    tags=['staging', 'toll_station']
) }}

SELECT 
    station_id,
    TRIM(station_name) AS station_name,
    TRIM(city) AS city,
    TRIM(highway_code) AS highway_code,
    TRIM(station_type) AS station_type,
    open_date,
    CURRENT_TIMESTAMP AS etl_time
FROM {{ source('raw', 'toll_station') }}

