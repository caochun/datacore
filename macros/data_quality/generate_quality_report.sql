-- 生成数据质量报告宏

{% macro generate_quality_report(table_name, date_column=None) %}
    -- 生成数据质量报告
    SELECT 
        {% if date_column %}
            {{ date_column }} AS report_date,
        {% endif %}
        '{{ table_name }}' AS table_name,
        COUNT(*) AS total_records,
        -- 完整性指标
        SUM(CASE WHEN transaction_id IS NOT NULL THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS transaction_id_completeness,
        SUM(CASE WHEN station_id IS NOT NULL THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS station_id_completeness,
        SUM(CASE WHEN vehicle_plate IS NOT NULL AND vehicle_plate != '' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS vehicle_plate_completeness,
        -- 准确性指标
        SUM(CASE WHEN is_normal_transaction = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS accuracy_rate,
        -- 一致性指标
        SUM(CASE WHEN data_quality_flag = '正常' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS consistency_rate,
        -- 综合质量得分
        (
            (SUM(CASE WHEN transaction_id IS NOT NULL THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) * 0.2 +
            (SUM(CASE WHEN station_id IS NOT NULL THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) * 0.2 +
            (SUM(CASE WHEN vehicle_plate IS NOT NULL AND vehicle_plate != '' THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) * 0.2 +
            (SUM(CASE WHEN is_normal_transaction = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) * 0.2 +
            (SUM(CASE WHEN data_quality_flag = '正常' THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) * 0.2
        ) AS overall_quality_score,
        CURRENT_TIMESTAMP AS report_time
    FROM {{ ref(table_name) }}
    {% if date_column %}
    GROUP BY {{ date_column }}
    {% endif %}
{% endmacro %}

