-- ADS层：数据质量监控看板
-- 功能：数据质量监控和告警

{{ config(
    materialized='table',
    tags=['ads', 'dashboard', 'quality']
) }}

SELECT 
    transaction_date,
    -- 总体质量指标
    COUNT(*) AS total_transactions,
    SUM(CASE WHEN is_normal_transaction = 1 THEN 1 ELSE 0 END) AS normal_transactions,
    SUM(CASE WHEN is_normal_transaction = 0 THEN 1 ELSE 0 END) AS abnormal_transactions,
    SUM(CASE WHEN data_quality_flag = '正常' THEN 1 ELSE 0 END) AS quality_normal,
    SUM(CASE WHEN data_quality_flag != '正常' THEN 1 ELSE 0 END) AS quality_abnormal,
    -- 质量率
    SUM(CASE WHEN is_normal_transaction = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS normal_rate,
    SUM(CASE WHEN data_quality_flag = '正常' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS data_quality_rate,
    -- 异常类型分布
    SUM(CASE WHEN transaction_status = '异常' THEN 1 ELSE 0 END) AS status_abnormal_count,
    SUM(CASE WHEN transaction_status = '逃费' THEN 1 ELSE 0 END) AS status_evasion_count,
    SUM(CASE WHEN transaction_status = '设备故障' THEN 1 ELSE 0 END) AS status_equipment_failure_count,
    SUM(CASE WHEN transaction_status = '数据缺失' THEN 1 ELSE 0 END) AS status_missing_count,
    SUM(CASE WHEN data_quality_flag = '数据缺失' THEN 1 ELSE 0 END) AS quality_missing_count,
    SUM(CASE WHEN data_quality_flag = '收费站缺失' THEN 1 ELSE 0 END) AS quality_station_missing_count,
    SUM(CASE WHEN data_quality_flag = '车牌缺失' THEN 1 ELSE 0 END) AS quality_plate_missing_count,
    SUM(CASE WHEN data_quality_flag = '时间异常' THEN 1 ELSE 0 END) AS quality_time_abnormal_count,
    SUM(CASE WHEN data_quality_flag = '金额异常' THEN 1 ELSE 0 END) AS quality_amount_abnormal_count,
    -- 告警标记
    CASE 
        WHEN SUM(CASE WHEN is_normal_transaction = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) < 90 THEN '告警'
        WHEN SUM(CASE WHEN data_quality_flag = '正常' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) < 95 THEN '告警'
        ELSE '正常'
    END AS alert_status,
    -- 时间维度
    MAX(etl_time) AS last_update_time
FROM {{ ref('dwd_toll_transaction_detail') }}
GROUP BY transaction_date

