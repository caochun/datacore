-- 数据准确性检查宏

{% macro check_accuracy(table_name, condition_column, expected_value, threshold=90.0) %}
    -- 检查数据准确性，返回准确率
    SELECT 
        COUNT(*) AS total_count,
        SUM(CASE WHEN {{ condition_column }} = {{ expected_value }} THEN 1 ELSE 0 END) AS accurate_count,
        SUM(CASE WHEN {{ condition_column }} = {{ expected_value }} THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS accuracy_rate,
        CASE 
            WHEN SUM(CASE WHEN {{ condition_column }} = {{ expected_value }} THEN 1 ELSE 0 END) * 100.0 / COUNT(*) >= {{ threshold }} THEN 'PASS'
            ELSE 'FAIL'
        END AS check_result
    FROM {{ ref(table_name) }}
{% endmacro %}

