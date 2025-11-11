-- 元数据管理：表信息表（自动化生成）
-- 功能：从 dbt graph 自动提取所有数据表的元数据信息
-- 业务信息从 schema.yml 的 meta 字段获取，如果没有则使用默认值

{{ config(
    materialized='table',
    tags=['metadata', 'table_info']
) }}

{{ generate_table_info() }}

