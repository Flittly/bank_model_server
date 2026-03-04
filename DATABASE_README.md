# 数据库表结构设计说明

## 概述

本文档描述了岸段、断面、修正线、风险等级结果四个核心表的设计，以及它们之间的关系。

- **bank_segments (岸段表)**: 存储岸线的段落划分和属性参数
- **cross_sections (断面表)**: 存储断面信息，关联岸段并继承属性，是模型计算的对象
- **correction_lines (修正线表)**: 存储修正线及修改规则，通过空间范围影响岸段和断面
- **bank_risk_results (风险等级结果表)**: 存储按照断面计算的风险等级结果

## 表关系图

```
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│  bank_segments  │         │ cross_sections  │         │correction_lines │
│    (岸段表)      │───────▶│    (断面表)      │         │   (修正线表)     │
└─────────────────┘         └────────┬────────┘         └─────────────────┘
       │                           │                          │
       │                           │                          │
       └──────────────────────────────┴──────────────────────────┘
                   通过空间几何关系影响
       
                                   │
                                   ▼
                          ┌─────────────────┐
                          │bank_risk_results│
                          │  (风险结果表)   │
                          └─────────────────┘
```

## 表结构详情

### 1. bank_segments (岸段表)

**说明**: 存储岸线的人工划分段落及其属性参数，是基础数据表。存储该岸段范围内所有断面共享的模型参数。

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | SERIAL | 主键 | PRIMARY KEY |
| case_id | VARCHAR(50) | 关联任务ID | NOT NULL |
| segment_id | VARCHAR(100) | 岸段编号 | UNIQUE, NOT NULL |
| segment_name | VARCHAR(100) | 岸段完整名称 | NOT NULL |
| region_code | VARCHAR(50) | 区域代码 | NOT NULL |
| start_point | GEOMETRY(Point, 4326) | 起点坐标 | - |
| end_point | GEOMETRY(Point, 4326) | 终点坐标 | - |
| geom | GEOMETRY(LineString, 4326) | 岸段几何线 | - |
| dem_id | VARCHAR(100) | DEM数据ID | - |
| bench_id | VARCHAR(100) | 基准DEM数据ID | - |
| ref_id | VARCHAR(100) | 参考DEM数据ID | - |
| hydro_segment | VARCHAR(50) | 水动力河段名称 | - |
| hydro_year | VARCHAR(20) | 水动力数据年份 | - |
| hydro_set | VARCHAR(50) | 水动力数据集名称 | - |
| protection_level | VARCHAR(20) | 岸坡防护等级 | - |
| control_level | VARCHAR(20) | 荷载控制等级 | - |
| other_params | JSONB | 其他参数 | - |
| created_at | TIMESTAMP | 创建时间 | DEFAULT CURRENT_TIMESTAMP |
| updated_at | TIMESTAMP | 更新时间 | DEFAULT CURRENT_TIMESTAMP |

**索引**:
- idx_segments_region: region_code
- idx_segments_geom: geom (GIST)
- idx_segments_id: segment_id

### 2. cross_sections (断面表)

**说明**: 存储垂直于岸段的断面信息，关联岸段并继承属性参数。断面是模型主要计算的对象。存储该断面从岸段继承的参数，以及修正线修改后的所有参数。

**重要说明**: 
- `multipleIndicators` 模型计算出的坡度(Sa)、高差(Zb)、近岸冲刷(Ln)、抗冲击流速(Ky)、水位波动(Zd)等**不需要存储在数据库中**，由模型实时计算并存储在模型实例的响应中

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | SERIAL | 主键 | PRIMARY KEY |
| case_id | VARCHAR(50) | 关联任务ID | NOT NULL |
| section_id | VARCHAR(100) | 断面编号 | UNIQUE, NOT NULL |
| section_name | VARCHAR(100) | 断面完整名称 | NOT NULL |
| segment_id | INTEGER | 关联岸段ID | FOREIGN KEY → bank_segments(id), NOT NULL |
| region_code | VARCHAR(50) | 区域代码 | NOT NULL |
| segment_index | INTEGER | 岸段序号 | - |
| start_point | GEOMETRY(Point, 4326) | 起点坐标（岸上） | - |
| end_point | GEOMETRY(Point, 4326) | 终点坐标（河里） | - |
| geom | GEOMETRY(LineString, 4326) | 断面几何线 | - |
| hs | NUMERIC | 砂土层厚度（米） | - |
| hc | NUMERIC | 土层总覆盖厚度（米） | - |
| protection_level | VARCHAR(20) | 岸坡防护等级（继承自岸段，可被修正线修改） | - |
| control_level | VARCHAR(20) | 荷载控制等级（继承自岸段，可被修正线修改） | - |
| water_qs | VARCHAR(20) | 流量值（m³/s） | - |
| tidal_level | VARCHAR(20) | 潮位等级 | - |
| current_timepoint | DATE | 当前时间点 | - |
| comparison_timepoint | DATE | 对比时间点 | - |
| risk_thresholds | JSONB | 风险阈值配置 | - |
| weights | JSONB | 权重配置 | - |
| other_params | JSONB | 其他参数 | - |
| created_at | TIMESTAMP | 创建时间 | DEFAULT CURRENT_TIMESTAMP |
| updated_at | TIMESTAMP | 更新时间 | DEFAULT CURRENT_TIMESTAMP |

**索引**:
- idx_sections_segment: segment_id
- idx_sections_region: region_code
- idx_sections_geom: geom (GIST)
- idx_sections_id: section_id

**外键关系**:
- segment_id → bank_segments(id) (ON DELETE CASCADE)

### 3. correction_lines (修正线表)

**说明**: 存储用于修改岸段和断面属性的修正线及其修改规则。通过空间几何范围影响范围内的岸段和断面。

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | SERIAL | 主键 | PRIMARY KEY |
| correction_id | VARCHAR(50) | 修正线编号 | UNIQUE, NOT NULL |
| geom | GEOMETRY(LineString, 4326) | 修正线几何范围 | - |
| correction_rules | JSONB | 属性修改规则 | NOT NULL |
| description | TEXT | 备注信息 | - |
| created_at | TIMESTAMP | 创建时间 | DEFAULT CURRENT_TIMESTAMP |
| updated_at | TIMESTAMP | 更新时间 | DEFAULT CURRENT_TIMESTAMP |

**索引**:
- idx_correction_geom: geom (GIST)
- idx_correction_id: correction_id

**correction_rules 示例**:
```json
{
  "roughness": 0.03,
  "slope": 0.02,
  "d50": 0.5
}
```

### 4. bank_risk_results (风险等级结果表)

**说明**: 存储按照断面计算的风险等级结果，关联断面表。

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | SERIAL | 主键 | PRIMARY KEY |
| case_id | VARCHAR(50) | 关联任务ID | NOT NULL |
| section_id | INTEGER | 关联断面ID | FOREIGN KEY → cross_sections(id), NOT NULL |
| section_name | VARCHAR(100) | 断面名称 | - |
| region_code | VARCHAR(50) | 区域代码 | - |
| segment_id | INTEGER | 所属岸段ID | - |
| segment_name | VARCHAR(100) | 所属岸段名称 | - |
| run_time | TIMESTAMP | 计算时间 | DEFAULT CURRENT_TIMESTAMP |
| risk_level | INTEGER | 风险等级 | - |
| indicators | JSONB | 子指标详情 (JSON) | - |
| geom | GEOMETRY(LineString, 4326) | 空间几何 (复制自断面) | - |

**索引**:
- idx_bank_results_section: section_id
- idx_bank_results_region: region_code
- idx_bank_results_geom: geom (GIST)
- idx_bank_results_case: case_id

**外键关系**:
- section_id → cross_sections(id) (ON DELETE CASCADE)

## 使用场景

### 场景1: 创建岸段数据

```sql
INSERT INTO bank_segments (
    segment_id, segment_name, region_code,
    start_point, end_point, geom,
    roughness, slope, elevation, d50
) VALUES (
    'Mzs_Seg001', 'Mzs_Seg001_202401', 'Mzs',
    ST_SetSRID(ST_MakePoint(121.5, 31.2), 4326),
    ST_SetSRID(ST_MakePoint(121.6, 31.3), 4326),
    ST_SetSRID(ST_MakeLine(ST_MakePoint(121.5, 31.2), ST_MakePoint(121.6, 31.3)), 4326),
    0.025, 0.015, 3.5, 0.2
);
```

### 场景2: 创建断面（继承岸段属性）

```sql
-- 方法1: 直接插入，手动指定继承的属性
INSERT INTO cross_sections (
    section_id, section_name, segment_id, region_code,
    start_point, end_point, geom,
    roughness, slope, elevation, d50
) SELECT 
    'CS_001', 'Cross_Section_001', s.id, s.region_code,
    s.start_point, s.end_point, s.geom,
    s.roughness, s.slope, s.elevation, s.d50
FROM bank_segments s
WHERE s.segment_id = 'Mzs_Seg001';
```

### 场景3: 应用修正线修改属性

```sql
-- 步骤1: 创建修正线
INSERT INTO correction_lines (
    correction_id, geom, correction_rules, description
) VALUES (
    'CORR_001',
    ST_SetSRID(ST_MakeLine(ST_MakePoint(121.55, 31.25), ST_MakePoint(121.58, 31.28)), 4326),
    '{"roughness": 0.03, "slope": 0.02}'::jsonb,
    '修正Mzs区域的部分岸段参数'
);

-- 步骤2: 查找受影响的岸段（空间相交）
SELECT s.id, s.segment_id, c.correction_rules
FROM bank_segments s, correction_lines c
WHERE ST_Intersects(s.geom, c.geom) AND c.correction_id = 'CORR_001';

-- 步骤3: 更新受影响的岸段属性
UPDATE bank_segments s
SET 
    roughness = c.correction_rules->>'roughness',
    slope = c.correction_rules->>'slope'
FROM correction_lines c
WHERE ST_Intersects(s.geom, c.geom) AND c.correction_id = 'CORR_001';

-- 步骤4: 级联更新关联的断面属性
UPDATE cross_sections cs
SET 
    roughness = s.roughness,
    slope = s.slope
FROM bank_segments s
WHERE cs.segment_id = s.id;
```

### 场景4: 查询岸段及其关联的断面

```sql
SELECT 
    s.segment_id,
    s.segment_name,
    s.roughness,
    s.slope,
    COUNT(cs.id) as section_count
FROM bank_segments s
LEFT JOIN cross_sections cs ON s.id = cs.segment_id
GROUP BY s.id, s.segment_id, s.segment_name, s.roughness, s.slope;
```

### 场景5: 保存风险等级结果

```sql
-- 模型计算完成后，将断面级别的风险等级存入结果表
INSERT INTO bank_risk_results (
    case_id, section_id, section_name,
    region_code, segment_id, segment_name,
    risk_level, indicators, geom
) SELECT 
    'case_001', cs.id, cs.section_name,
    cs.region_code, cs.segment_id, s.segment_name,
    3, 
    '{"slope_risk": 2, "flow_risk": 3, "erosion_risk": 4}'::jsonb,
    cs.geom
FROM cross_sections cs
JOIN bank_segments s ON cs.segment_id = s.id
WHERE cs.section_id = 'CS_001';
```

### 场景6: 查询断面的风险等级结果

```sql
SELECT 
    cs.section_id,
    cs.section_name,
    s.segment_name,
    br.risk_level,
    br.indicators,
    br.run_time
FROM bank_risk_results br
JOIN cross_sections cs ON br.section_id = cs.id
JOIN bank_segments s ON cs.segment_id = s.id
WHERE br.case_id = 'case_001'
ORDER BY br.risk_level DESC;
```

## 数据流程

1. **初始化阶段**:
   - 前端绘制岸段 → 插入 bank_segments
   - 前端绘制修正线 → 插入 correction_lines

2. **断面生成阶段**:
   - 根据岸段生成断面 → 插入 cross_sections（继承岸段属性）

3. **属性修正阶段**:
   - 应用修正线 → 更新受影响的 bank_segments
   - 级联更新关联的 cross_sections

4. **模型计算阶段**:
   - 从 cross_sections 获取断面属性
   - 将断面数据传递给模型进行运算
   - 结果存入 bank_risk_results

## 执行SQL

使用以下命令执行表创建脚本：

```bash
# 方法1: 使用psql命令行
psql -h localhost -p 5432 -U postgres -d bank_risk_db -f database_schema.sql

# 方法2: 使用Python脚本（需要先安装依赖）
python util/db_init.py

# 方法3: 在数据库管理工具中直接执行
# 打开 database_schema.sql 文件，复制SQL语句在PgAdmin或DBeaver中执行
```

## 注意事项

1. **几何坐标系**: 所有几何数据使用 WGS84 (SRID 4326)
2. **外键约束**: 
   - 断面表的外键设置了 ON DELETE CASCADE，删除岸段会自动删除关联的断面
   - 风险结果表的外键设置了 ON DELETE CASCADE，删除断面会自动删除关联的风险结果
3. **索引优化**: 为空间查询和常用查询字段创建了索引
4. **JSONB使用**: other_params、risk_thresholds、weights、correction_rules 使用 JSONB 类型，支持高效的JSON查询
5. **时间戳**: 自动记录创建和更新时间，便于追踪数据变更
6. **风险等级**: 风险等级是按照断面计算和存储的，每个断面对应一个风险等级
7. **参数继承规则**:
   - 断面默认从关联的岸段继承参数（protection_level、control_level等）
   - 修正线可以修改断面上的参数
   - 断面表中的参数值优先级：修正线修改值 > 岸段继承值
8. **模型计算参数说明**:
   - **multipleIndicators 模型**: 复杂多指标风险评估模型
   - 坡度(Sa)、高差(Zb)、近岸冲刷(Ln)、抗冲击流速(Ky)、水位波动(Zd)等参数**由模型实时计算得出**
   - 这些计算参数**不需要存储在数据库中**，由模型实时计算并存储在模型实例的响应中
9. **前端提供的参数**:
   - DEM TIFF 文件（存储在 resource/tiff/ 目录）
   - 土壤参数（hs、hc）
   - 地质工程参数（protection_level、control_level）
   - 地形参数（通过选择 DEM 文件）
   - 水文参数（hydro_segment、hydro_year、hydro_set、water_qs、tidal_level）
   - 断面几何参数（通过前端绘制）
   - 风险阈值和指标权重（risk_thresholds、weights）
10. **新增字段说明**:
    - **bank_segments 新增**: dem_id、bench_id、ref_id、hydro_segment、hydro_year、hydro_set、protection_level、control_level
    - **cross_sections 新增**: hs、hc、protection_level、control_level、water_qs、tidal_level、current_timepoint、comparison_timepoint、risk_thresholds、weights

## 后续扩展

如需添加新字段或表，请参考现有结构并保持一致性：
- 使用 SERIAL 作为主键
- 使用 GEOMETRY 类型存储空间数据
- 为外键添加适当的约束
- 为查询频繁的字段创建索引
- 添加必要的注释说明字段用途
