-- 测试：收费交易数据准确性

SELECT 
    transaction_id,
    toll_amount,
    actual_amount,
    discount_amount
FROM {{ ref('dwd_toll_transaction_detail') }}
WHERE 
    actual_amount < 0
    OR actual_amount > toll_amount
    OR discount_amount < 0
    OR discount_amount > toll_amount
    OR (actual_amount + discount_amount) > toll_amount * 1.1  -- 允许10%误差

