-- 自动生成表信息元数据的宏
-- 从 dbt graph 中提取所有模型信息，并从 schema.yml 的 meta 字段获取业务信息

{% macro generate_table_info() %}
    {% set model_rows = [] %}
    
    {% for node_id in graph.nodes %}
        {% set node = graph.nodes[node_id] %}
        {% if node.resource_type == 'model' %}
            {% set schema_name = node.schema %}
            {% set table_name = node.name %}
            {% set description = node.description or '' %}
            
            {# 从 meta 字段获取业务信息，如果没有则使用默认值 #}
            {% set meta = node.meta or {} %}
            {% set business_domain = meta.get('business_domain', '未分类') %}
            {% set data_source = meta.get('data_source', '数据中台') %}
            {% set update_frequency = meta.get('update_frequency', '按需') %}
            {% set owner = meta.get('owner', '数据团队') %}
            {% set table_name_cn = meta.get('table_name_cn', description) %}
            
            {# 如果没有设置table_name_cn，尝试从description中提取 #}
            {% if not table_name_cn or table_name_cn == description %}
                {# 如果description是中文，直接使用description的前30个字符作为中文名 #}
                {% if description and description|length > 0 %}
                    {% set table_name_cn = description.split('，')[0].split('（')[0].split('(')[0].strip() %}
                {% else %}
                    {% set table_name_cn = table_name %}
                {% endif %}
            {% endif %}
            
            {# 从 schema 名称推断数据分层 #}
            {% set data_layer = schema_name %}
            
            {# 转义单引号 #}
            {% set description_escaped = description | replace("'", "''") %}
            {% set table_name_cn_escaped = table_name_cn | replace("'", "''") %}
            
            {% set row = "SELECT '" ~ schema_name ~ "' AS schema_name, '" ~ 
                        table_name ~ "' AS table_name, '" ~ 
                        table_name_cn_escaped ~ "' AS table_name_cn, '" ~
                        description_escaped ~ "' AS table_description, '" ~
                        business_domain ~ "' AS business_domain, '" ~
                        data_source ~ "' AS data_source, '" ~
                        update_frequency ~ "' AS update_frequency, '" ~
                        owner ~ "' AS owner, '" ~
                        data_layer ~ "' AS data_layer, " ~
                        "CURRENT_TIMESTAMP AS create_time" %}
            
            {% do model_rows.append(row) %}
        {% endif %}
    {% endfor %}
    
    {{ return(model_rows | join('\nUNION ALL\n')) }}
{% endmacro %}

