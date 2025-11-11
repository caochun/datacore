-- 支付方式字典数据清洗层

{{ config(
    materialized='view',
    tags=['staging', 'data_dictionary']
) }}

SELECT 
    payment_method_code,
    TRIM(payment_method_name) AS payment_method_name,
    TRIM(payment_method_desc) AS payment_method_desc,
    CURRENT_TIMESTAMP AS etl_time
FROM {{ source('raw', 'payment_method_dict') }}

