-- 测试：收费交易数据一致性

SELECT 
    transaction_id,
    entry_time,
    exit_time,
    travel_minutes
FROM {{ ref('dwd_toll_transaction_detail') }}
WHERE 
    exit_time < entry_time
    OR travel_minutes < 0
    OR travel_minutes > 1440  -- 超过24小时视为异常

