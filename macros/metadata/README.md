# 元数据自动化生成说明

## 概述

metadata 目录下的元数据模型已实现完全自动化，通过 dbt 的 `graph` 对象自动提取模型信息和溯源关系。

## 自动化模型

### 1. `meta_table_info` - 表信息自动生成

**自动化内容：**
- ✅ 自动发现所有模型（从 `graph.nodes`）
- ✅ 自动提取 schema 名称、表名、描述
- ✅ 自动从 `schema.yml` 的 `meta` 字段获取业务信息
- ✅ 自动推断数据分层（从 schema 名称）

**需要手工维护：**
- 在 `schema.yml` 中为每个模型添加 `meta` 字段：
  ```yaml
  models:
    - name: your_model
      description: "模型描述"
      meta:
        business_domain: "业务域"
        data_source: "数据源"
        update_frequency: "更新频率"
        owner: "负责人"
  ```

### 2. `meta_data_lineage` - 溯源关系自动生成

**自动化内容：**
- ✅ 自动识别 `ref()` 依赖关系
- ✅ 自动识别 `source()` 依赖关系
- ✅ 自动推断转换类型（根据 schema 层级）
- ✅ 自动生成溯源关系记录

**转换类型自动推断规则：**
- `staging → ods`: 关联
- `ods → dwd`: 转换
- `dwd → dws`: 汇总
- `dws → ads`: 聚合
- `source → staging`: 清洗

**无需手工维护** - 完全自动化！

## 使用方法

### 1. 添加新模型时

只需在 `schema.yml` 中添加 meta 信息：

```yaml
models:
  - name: new_model
    description: "新模型描述"
    meta:
      business_domain: "收费业务"
      data_source: "收费系统"
      update_frequency: "实时"
      owner: "收费中心"
```

运行 `dbt run` 后，元数据会自动更新。

### 2. 查看生成的元数据

```sql
-- 查看所有表信息
SELECT * FROM main_metadata.meta_table_info;

-- 查看溯源关系
SELECT * FROM main_metadata.meta_data_lineage;

-- 查看特定表的溯源
SELECT * FROM main_metadata.meta_data_lineage 
WHERE target_table LIKE '%your_model%';
```

### 3. 验证自动化

```bash
# 运行元数据模型
dbt run --select metadata

# 查看生成的表信息数量
# 应该等于项目中的模型数量
```

## 优势

1. **零维护成本**：新增模型无需手动更新元数据
2. **自动同步**：元数据始终与代码保持一致
3. **减少错误**：避免手工维护导致的遗漏和错误
4. **完整覆盖**：自动发现所有模型和依赖关系

## 技术实现

- 使用 `graph.nodes` 遍历所有模型节点
- 使用 `node.depends_on.nodes` 获取依赖关系
- 使用 `node.sources` 获取 source 引用
- 使用 `node.meta` 获取业务元数据
- 使用 Jinja2 宏生成 SQL UNION ALL 语句

## 注意事项

1. **meta 字段是必需的**：虽然宏有默认值，但建议为每个模型添加完整的 meta 信息
2. **schema 命名规范**：数据分层通过 schema 名称推断，确保命名规范
3. **描述信息**：模型描述会自动转义单引号，支持中文和特殊字符

