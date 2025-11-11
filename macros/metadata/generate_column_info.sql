-- 自动生成字段信息元数据的宏
-- 从 dbt graph 中提取所有模型的字段信息，并从 schema.yml 的 columns meta 字段获取中文名

{% macro generate_column_info() %}
    {% set column_rows = [] %}
    
    {% for node_id in graph.nodes %}
        {% set node = graph.nodes[node_id] %}
        {% if node.resource_type == 'model' %}
            {% set schema_name = node.schema %}
            {% set table_name = node.name %}
            
            {# 获取字段信息 #}
            {% if node.columns %}
                {% for column_name, column_info in node.columns.items() %}
                    {% set column_description = column_info.get('description', '') %}
                    {% set column_meta = column_info.get('meta', {}) %}
                    {% set column_name_cn = column_meta.get('column_name_cn', column_description) %}
                    
                    {# 如果没有设置column_name_cn，尝试从description中提取 #}
                    {% if not column_name_cn or column_name_cn == column_description %}
                        {# 如果description是中文，直接使用description的前20个字符作为中文名 #}
                        {% if column_description and column_description|length > 0 %}
                            {% set column_name_cn = column_description.split('，')[0].split('（')[0].split('(')[0].strip() %}
                        {% else %}
                            {% set column_name_cn = column_name %}
                        {% endif %}
                    {% endif %}
                    
                    {# 转义单引号 #}
                    {% set column_name_cn_escaped = column_name_cn | replace("'", "''") %}
                    {% set column_description_escaped = column_description | replace("'", "''") %}
                    
                    {% set row = "SELECT '" ~ schema_name ~ "' AS schema_name, '" ~ 
                                table_name ~ "' AS table_name, '" ~ 
                                column_name ~ "' AS column_name, '" ~
                                column_name_cn_escaped ~ "' AS column_name_cn, '" ~
                                column_description_escaped ~ "' AS column_description, " ~
                                "CURRENT_TIMESTAMP AS create_time" %}
                    
                    {% do column_rows.append(row) %}
                {% endfor %}
            {% endif %}
        {% endif %}
    {% endfor %}
    
    {{ return(column_rows | join('\nUNION ALL\n')) }}
{% endmacro %}

