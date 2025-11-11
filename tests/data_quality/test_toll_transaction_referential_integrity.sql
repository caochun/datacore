-- 测试：收费交易数据引用完整性

SELECT 
    t.transaction_id,
    t.station_id,
    t.vehicle_type_code,
    t.payment_method_code
FROM {{ ref('dwd_toll_transaction_detail') }} t
LEFT JOIN {{ ref('ods_toll_station') }} s ON t.station_id = s.station_id
LEFT JOIN {{ ref('stg_vehicle_type_dict') }} vt ON t.vehicle_type_code = vt.vehicle_type_code
LEFT JOIN {{ ref('stg_payment_method_dict') }} pm ON t.payment_method_code = pm.payment_method_code
WHERE 
    s.station_id IS NULL
    OR vt.vehicle_type_code IS NULL
    OR pm.payment_method_code IS NULL

