-- 收费交易数据清洗层
-- 功能：数据清洗、标准化、异常值处理

{{ config(
    materialized='view',
    tags=['staging', 'toll_transaction']
) }}

WITH raw_data AS (
    SELECT 
        transaction_id,
        station_id,
        lane_id,
        vehicle_plate,
        vehicle_type_code,
        entry_station_id,
        entry_time,
        exit_time,
        payment_method_code,
        toll_amount,
        actual_amount,
        discount_amount,
        transaction_status,
        create_time,
        update_time
    FROM {{ source('raw', 'toll_transaction') }}
),

cleaned_data AS (
    SELECT 
        -- 主键
        transaction_id,
        
        -- 收费站信息（清洗）
        COALESCE(station_id, 'UNKNOWN') AS station_id,
        COALESCE(lane_id, 'UNKNOWN') AS lane_id,
        COALESCE(entry_station_id, 'UNKNOWN') AS entry_station_id,
        
        -- 车辆信息（清洗）
        UPPER(TRIM(COALESCE(vehicle_plate, ''))) AS vehicle_plate,
        COALESCE(vehicle_type_code, 'V01') AS vehicle_type_code,
        
        -- 时间信息（清洗和验证）
        entry_time,
        exit_time,
        CASE 
            WHEN exit_time < entry_time THEN entry_time + INTERVAL 1 HOUR
            ELSE exit_time
        END AS exit_time_cleaned,
        
        -- 计算通行时长（分钟）
        CAST(EXTRACT(EPOCH FROM (exit_time - entry_time)) AS INTEGER) / 60 AS travel_minutes,
        
        -- 支付信息
        COALESCE(payment_method_code, 'P02') AS payment_method_code,
        
        -- 金额信息（清洗和验证）
        COALESCE(toll_amount, 0) AS toll_amount,
        COALESCE(actual_amount, 0) AS actual_amount,
        COALESCE(discount_amount, 0) AS discount_amount,
        
        -- 金额合理性检查
        CASE 
            WHEN actual_amount < 0 THEN 0
            WHEN actual_amount > toll_amount THEN toll_amount
            ELSE actual_amount
        END AS actual_amount_cleaned,
        
        -- 交易状态
        COALESCE(transaction_status, '正常') AS transaction_status,
        
        -- 数据质量标记
        CASE 
            WHEN transaction_id IS NULL THEN '数据缺失'
            WHEN station_id = 'UNKNOWN' THEN '收费站缺失'
            WHEN vehicle_plate = '' THEN '车牌缺失'
            WHEN exit_time < entry_time THEN '时间异常'
            WHEN actual_amount < 0 OR actual_amount > toll_amount THEN '金额异常'
            ELSE '正常'
        END AS data_quality_flag,
        
        -- 元数据
        create_time,
        COALESCE(update_time, create_time) AS update_time,
        CURRENT_TIMESTAMP AS etl_time
        
    FROM raw_data
)

SELECT 
    transaction_id,
    station_id,
    lane_id,
    vehicle_plate,
    vehicle_type_code,
    entry_station_id,
    entry_time,
    exit_time_cleaned AS exit_time,
    travel_minutes,
    payment_method_code,
    toll_amount,
    actual_amount_cleaned AS actual_amount,
    discount_amount,
    transaction_status,
    data_quality_flag,
    create_time,
    update_time,
    etl_time
FROM cleaned_data

