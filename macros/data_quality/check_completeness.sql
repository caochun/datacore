-- 数据完整性检查宏

{% macro check_completeness(table_name, column_name, threshold=95.0) %}
    -- 检查字段完整性，返回完整性率
    SELECT 
        COUNT(*) AS total_count,
        SUM(CASE WHEN {{ column_name }} IS NOT NULL AND {{ column_name }} != '' THEN 1 ELSE 0 END) AS complete_count,
        SUM(CASE WHEN {{ column_name }} IS NOT NULL AND {{ column_name }} != '' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS completeness_rate,
        CASE 
            WHEN SUM(CASE WHEN {{ column_name }} IS NOT NULL AND {{ column_name }} != '' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) >= {{ threshold }} THEN 'PASS'
            ELSE 'FAIL'
        END AS check_result
    FROM {{ ref(table_name) }}
{% endmacro %}

