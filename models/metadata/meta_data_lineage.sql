-- 元数据管理：数据溯源关系表（自动化生成）
-- 功能：从 dbt graph 自动提取数据表之间的溯源关系
-- 自动识别 ref() 和 source() 依赖关系

{{ config(
    materialized='table',
    tags=['metadata', 'lineage']
) }}

{{ generate_lineage() }}

