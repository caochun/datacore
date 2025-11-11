-- 自动生成数据溯源关系的宏
-- 从 dbt graph 中提取模型之间的依赖关系

{% macro generate_lineage() %}
    {% set lineage_rows = [] %}
    
    {% for node_id in graph.nodes %}
        {% set node = graph.nodes[node_id] %}
        {% if node.resource_type == 'model' %}
            {% set target_schema = node.schema %}
            {% set target_table = node.name %}
            {% set target_full = target_schema ~ '.' ~ target_table %}
            
            {# 处理通过 ref() 引用的模型依赖 #}
            {% if node.depends_on and node.depends_on.nodes %}
                {% for depends_on_node_id in node.depends_on.nodes %}
                    {% if graph.nodes[depends_on_node_id] %}
                        {% set source_node = graph.nodes[depends_on_node_id] %}
                        {% if source_node.resource_type == 'model' %}
                            {% set source_schema = source_node.schema %}
                            {% set source_table = source_node.name %}
                            {% set source_full = source_schema ~ '.' ~ source_table %}
                            
                            {# 根据 schema 推断转换类型 #}
                            {% if source_schema == 'staging' and target_schema == 'ods' %}
                                {% set trans_type = '关联' %}
                                {% set trans_desc = '关联字典表和业务字段扩展' %}
                            {% elif source_schema == 'ods' and target_schema == 'dwd' %}
                                {% set trans_type = '转换' %}
                                {% set trans_desc = '业务明细数据转换' %}
                            {% elif source_schema == 'dwd' and target_schema == 'dws' %}
                                {% set trans_type = '汇总' %}
                                {% set trans_desc = '按维度汇总' %}
                            {% elif source_schema == 'dws' and target_schema == 'ads' %}
                                {% set trans_type = '聚合' %}
                                {% set trans_desc = '生成应用报表' %}
                            {% elif source_schema == 'staging' and target_schema == 'staging' %}
                                {% set trans_type = '清洗' %}
                                {% set trans_desc = '数据清洗和标准化' %}
                            {% else %}
                                {% set trans_type = '转换' %}
                                {% set trans_desc = '数据转换' %}
                            {% endif %}
                            
                            {% set row = "SELECT '" ~ source_full ~ "' AS source_table, '" ~ 
                                        target_full ~ "' AS target_table, '" ~
                                        trans_type ~ "' AS transformation_type, '" ~
                                        trans_desc ~ "' AS transformation_desc" %}
                            
                            {% do lineage_rows.append(row) %}
                        {% endif %}
                    {% endif %}
                {% endfor %}
            {% endif %}
            
            {# 处理通过 source() 引用的原始数据 #}
            {% if node.sources %}
                {% for source_info in node.sources %}
                    {% set source_full = source_info.source_name ~ '.' ~ source_info.name %}
                    {% set row = "SELECT '" ~ source_full ~ "' AS source_table, '" ~ 
                                target_full ~ "' AS target_table, '" ~
                                "清洗' AS transformation_type, '" ~
                                "数据清洗和标准化' AS transformation_desc" %}
                    {% do lineage_rows.append(row) %}
                {% endfor %}
            {% endif %}
        {% endif %}
    {% endfor %}
    
    {{ return(lineage_rows | join('\nUNION ALL\n')) }}
{% endmacro %}

