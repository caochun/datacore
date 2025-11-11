-- 元数据管理：字段信息表（自动化生成）
-- 功能：从 dbt graph 自动提取所有数据表字段的元数据信息
-- 字段中文名从 schema.yml 的 columns meta 字段获取

{{ config(
    materialized='table',
    tags=['metadata', 'column_info']
) }}

{{ generate_column_info() }}

