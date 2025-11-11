-- 车型字典数据清洗层

{{ config(
    materialized='view',
    tags=['staging', 'data_dictionary']
) }}

SELECT 
    vehicle_type_code,
    TRIM(vehicle_type_name) AS vehicle_type_name,
    TRIM(vehicle_type_desc) AS vehicle_type_desc,
    toll_rate_multiplier,
    CURRENT_TIMESTAMP AS etl_time
FROM {{ source('raw', 'vehicle_type_dict') }}

