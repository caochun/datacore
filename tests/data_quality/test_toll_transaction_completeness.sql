-- 测试：收费交易数据完整性

SELECT 
    transaction_id,
    station_id,
    vehicle_plate,
    vehicle_type_code,
    payment_method_code
FROM {{ ref('dwd_toll_transaction_detail') }}
WHERE 
    transaction_id IS NULL
    OR station_id IS NULL
    OR vehicle_plate IS NULL
    OR vehicle_plate = ''
    OR vehicle_type_code IS NULL
    OR payment_method_code IS NULL

