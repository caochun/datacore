-- 元数据管理：数据字典表
-- 功能：统一管理业务数据字典

{{ config(
    materialized='table',
    tags=['metadata', 'data_dictionary']
) }}

-- 车型字典
SELECT 
    'vehicle_type' AS dict_type,
    vehicle_type_code AS dict_code,
    vehicle_type_name AS dict_name,
    vehicle_type_desc AS dict_desc,
    toll_rate_multiplier AS dict_value,
    '收费政策' AS dict_source,
    CURRENT_TIMESTAMP AS create_time
FROM {{ ref('stg_vehicle_type_dict') }}
UNION ALL
-- 支付方式字典
SELECT 
    'payment_method' AS dict_type,
    payment_method_code AS dict_code,
    payment_method_name AS dict_name,
    payment_method_desc AS dict_desc,
    NULL AS dict_value,
    '支付系统' AS dict_source,
    CURRENT_TIMESTAMP AS create_time
FROM {{ ref('stg_payment_method_dict') }}
UNION ALL
-- 交易状态字典
SELECT 
    'transaction_status' AS dict_type,
    status_code AS dict_code,
    status_name AS dict_name,
    status_desc AS dict_desc,
    NULL AS dict_value,
    '业务规则' AS dict_source,
    CURRENT_TIMESTAMP AS create_time
FROM (
    SELECT '正常' AS status_code, '正常' AS status_name, '正常交易' AS status_desc
    UNION ALL SELECT '异常', '异常', '异常交易'
    UNION ALL SELECT '逃费', '逃费', '逃费交易'
    UNION ALL SELECT '设备故障', '设备故障', '设备故障导致'
    UNION ALL SELECT '数据缺失', '数据缺失', '数据缺失'
) AS status_dict
UNION ALL
-- 数据质量标记字典
SELECT 
    'data_quality_flag' AS dict_type,
    flag_code AS dict_code,
    flag_name AS dict_name,
    flag_desc AS dict_desc,
    NULL AS dict_value,
    '数据质量规则' AS dict_source,
    CURRENT_TIMESTAMP AS create_time
FROM (
    SELECT '正常' AS flag_code, '正常' AS flag_name, '数据质量正常' AS flag_desc
    UNION ALL SELECT '数据缺失', '数据缺失', '关键字段缺失'
    UNION ALL SELECT '收费站缺失', '收费站缺失', '收费站信息缺失'
    UNION ALL SELECT '车牌缺失', '车牌缺失', '车牌号缺失'
    UNION ALL SELECT '时间异常', '时间异常', '时间逻辑异常'
    UNION ALL SELECT '金额异常', '金额异常', '金额逻辑异常'
) AS quality_dict

