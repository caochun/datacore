-- 数据一致性检查宏

{% macro check_consistency(table_name, column1, column2, relationship='=') %}
    -- 检查两个字段之间的一致性
    SELECT 
        COUNT(*) AS total_count,
        SUM(CASE 
            {% if relationship == '=' %}
                WHEN {{ column1 }} = {{ column2 }} THEN 1
            {% elif relationship == '>=' %}
                WHEN {{ column1 }} >= {{ column2 }} THEN 1
            {% elif relationship == '<=' %}
                WHEN {{ column1 }} <= {{ column2 }} THEN 1
            {% else %}
                WHEN {{ column1 }} = {{ column2 }} THEN 1
            {% endif %}
            ELSE 0 
        END) AS consistent_count,
        SUM(CASE 
            {% if relationship == '=' %}
                WHEN {{ column1 }} = {{ column2 }} THEN 1
            {% elif relationship == '>=' %}
                WHEN {{ column1 }} >= {{ column2 }} THEN 1
            {% elif relationship == '<=' %}
                WHEN {{ column1 }} <= {{ column2 }} THEN 1
            {% else %}
                WHEN {{ column1 }} = {{ column2 }} THEN 1
            {% endif %}
            ELSE 0 
        END) * 100.0 / COUNT(*) AS consistency_rate
    FROM {{ ref(table_name) }}
{% endmacro %}

