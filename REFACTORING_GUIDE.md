# 重构说明文档

## 概述

本文档说明了本次项目重构的主要变化和新的架构设计。

---

## 主要变化

### 1. 数据库表结构变更

#### 移除的表
- `bank_segments` - 岸段表（已移除）

#### 新增的表
- `banks` - 岸段表（新增，存储岸段几何信息）
- `tasks` - 任务表
- `basic_params` - 基础参数表

#### 修改的表
- `cross_sections` - 断面表（重构版，**每个section独立存储完整参数**）
- `correction_lines` - 修正线表（重构版）
- `bank_risk_results` - 风险结果表（重构版）

---

## 新的数据库表结构

### 1. tasks 表（任务表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | SERIAL | 主键 |
| task_id | VARCHAR(100) | 任务唯一ID |
| task_name | VARCHAR(100) | 任务名称 |
| bank_ids | JSONB | 岸段ID列表（JSON数组） |
| description | TEXT | 任务描述 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

**说明**：
- `bank_ids` 字段存储该任务涉及的所有岸段ID，使用JSONB格式
- 例如：`["BANK_001", "BANK_002", "BANK_003"]`

---

### 2. basic_params 表（基础参数表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | SERIAL | 主键 |
| param_id | VARCHAR(100) | 参数唯一ID |
| param_name | VARCHAR(100) | 参数名称 |
| segment | VARCHAR(50) | 水动力分段 |
| current_timepoint | VARCHAR(20) | 当前时间点 |
| set_name | VARCHAR(50) | 数据集名称 |
| water_qs | VARCHAR(20) | 流量 |
| tidal_level | VARCHAR(20) | 潮位 |
| bench_id | VARCHAR(100) | 基准DEM ID |
| ref_id | VARCHAR(100) | 参考DEM ID |
| hs | NUMERIC | 水深参数1 |
| hc | NUMERIC | 水深参数2 |
| protection_level | VARCHAR(20) | 防护等级 |
| control_level | VARCHAR(20) | 控制等级 |
| comparison_timepoint | VARCHAR(20) | 对比时间点 |
| risk_thresholds | JSONB | 风险阈值 |
| weights | JSONB | 权重参数 |
| other_params | JSONB | 其他参数 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

**说明**：
- 此表存储模型计算所需的所有基础参数
- 可以创建多个参数模板供不同任务复用
- 断面可以通过 `basic_param_id` 关联到某个参数模板

---

### 2. banks 表（岸段表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | SERIAL | 主键 |
| bank_id | VARCHAR(100) | 岸段唯一ID |
| bank_name | VARCHAR(100) | 岸段名称 |
| region_code | VARCHAR(50) | 区域代码 |
| start_point | GEOMETRY(Point, 4326) | 起点 |
| end_point | GEOMETRY(Point, 4326) | 终点 |
| geom | GEOMETRY(LineString, 4326) | 几何数据 |
| bank_geometry | JSONB | 岸段几何（用于前端展示） |
| description | TEXT | 描述 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

**说明**：
- 存储岸段的几何信息
- 不存储模型运行参数
- 断面通过 `bank_id` 关联到岸段

---

### 3. cross_sections 表（断面表 - 重构版）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | SERIAL | 主键 |
| task_id | INTEGER | 外键 → tasks.id |
| section_id | VARCHAR(100) | 断面唯一ID |
| section_name | VARCHAR(100) | 断面名称 |
| bank_id | VARCHAR(100) | 岸段ID → banks.bank_id |
| region_code | VARCHAR(50) | 区域代码 |
| segment_index | INTEGER | 岸段内索引 |
| start_point | GEOMETRY(Point, 4326) | 起点 |
| end_point | GEOMETRY(Point, 4326) | 终点 |
| geom | GEOMETRY(LineString, 4326) | 几何数据 |
| section_geometry | JSONB | 断面几何（用于前端展示） |
| basic_param_id | INTEGER | 外键 → basic_params.id（可选，仅用于参考） |
| param_name | VARCHAR(100) | 参数名称（独立存储） |
| segment | VARCHAR(50) | 河段编码（独立存储） |
| current_timepoint | VARCHAR(20) | 当前时间点（独立存储） |
| set_name | VARCHAR(50) | 数据集名称（独立存储） |
| water_qs | VARCHAR(20) | 流量（独立存储） |
| tidal_level | VARCHAR(20) | 潮位（独立存储） |
| bench_id | VARCHAR(100) | 基准DEM ID（独立存储） |
| ref_id | VARCHAR(100) | 参考DEM ID（独立存储） |
| hs | NUMERIC | 水深参数hs（独立存储） |
| hc | NUMERIC | 水深参数hc（独立存储） |
| protection_level | VARCHAR(20) | 防护等级（独立存储） |
| control_level | VARCHAR(20) | 控制等级（独立存储） |
| comparison_timepoint | VARCHAR(20) | 对比时间点（独立存储） |
| risk_thresholds | JSONB | 风险阈值（独立存储） |
| weights | JSONB | 权重参数（独立存储） |
| other_params | JSONB | 其他参数（独立存储） |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

**说明**：
- 每个断面属于一个任务（`task_id`）
- `bank_id` 字段表示该断面属于哪个岸段（关联 banks.bank_id）
- `basic_param_id` 字段可选，用于参考关联基础参数模板
- **核心变化：每个断面独立存储完整的模型运行参数！**
- 创建断面时，如果提供了 `basic_param_id`，后端会自动从 `basic_params` 表复制参数到 `cross_sections` 表
- 修改断面的参数时，直接修改 `cross_sections` 表中的字段，**不会影响 `basic_params` 表**
- 删除任务时会级联删除相关断面

---

### 4. correction_lines 表（修正线表 - 重构版）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | SERIAL | 主键 |
| task_id | INTEGER | 外键 → tasks.id |
| correction_id | VARCHAR(100) | 修正线唯一ID |
| geom | GEOMETRY(LineString, 4326) | 几何数据 |
| correction_rules | JSONB | 修正规则 |
| description | TEXT | 描述 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

**说明**：
- 每条修正线属于一个任务
- 删除任务时会级联删除相关修正线

---

### 5. bank_risk_results 表（风险结果表 - 重构版）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | SERIAL | 主键 |
| task_id | INTEGER | 外键 → tasks.id |
| section_id | INTEGER | 外键 → cross_sections.id |
| section_name | VARCHAR(100) | 断面名称 |
| region_code | VARCHAR(50) | 区域代码 |
| bank_id | VARCHAR(100) | 岸段ID |
| run_time | TIMESTAMP | 运行时间 |
| risk_level | INTEGER | 风险等级 |
| indicators | JSONB | 指标数据 |
| geom | GEOMETRY(LineString, 4326) | 几何数据 |

---

## 新的工作流程

### 前端使用流程

1. **创建岸段**（可选，首次使用时）
   - 接口：`POST /bank/banks`
   - 创建一个或多个岸段

2. **创建基础参数模板**（可选，首次使用时）
   - 接口：`POST /bank/basic-params`
   - 创建一个或多个参数模板供后续使用

3. **创建任务**
   - 接口：`POST /bank/tasks`
   - 指定任务名称、岸段ID列表等

4. **选择断面并创建**
   - 前端用户选择/绘制断面
   - 接口：`POST /bank/sections`
   - 断面数据包含：`section_id`、`section_name`、`bank_id`、`geometry`、`basic_param_id`
   - `basic_param_id` 关联到基础参数模板
   - **后端会自动从 basic_params 复制参数到 cross_sections 表**

5. **获取断面及参数**
   - 接口：`GET /bank/sections/{section_id}`
   - 返回断面信息 + **section表中独立存储的完整参数**
   - **注意：参数已经是section的独立副本**

6. **前端展示参数**
   - 展示section自己的参数
   - 允许用户确认或修改参数

7. **用户修改参数后，直接更新section**
   - 接口：`PUT /bank/sections/{section_id}`
   - **直接修改section的参数字段**
   - **修改只影响该section，不影响basic_params表**
   - 无需修正线表

8. **调用模型计算**
   - 接口：`POST /v0/mi/risk-level`

---

## API 接口变更

### 旧接口（已废弃）

| 旧接口 | 说明 |
|--------|------|
| `POST /bank/segments` | 创建岸段 |
| `GET /bank/segments/{case_id}` | 获取岸段列表 |
| `DELETE /bank/segments/{case_id}/{segment_id}` | 删除岸段 |
| `POST /bank/sections` | 创建断面（旧版） |
| `GET /bank/sections/{case_id}` | 获取断面列表（旧版） |
| `DELETE /bank/sections/{case_id}/{section_id}` | 删除断面（旧版） |
| `POST /bank/corrections` | 创建修正线（旧版） |
| `GET /bank/corrections/{case_id}` | 获取修正线列表（旧版） |
| `DELETE /bank/corrections/{case_id}/{correction_id}` | 删除修正线（旧版） |
| `GET /bank/cases/{case_id}/full` | 获取完整数据（旧版） |
| `DELETE /bank/cases/{case_id}` | 清空case数据（旧版） |

### 新接口

| 新接口 | 说明 |
|--------|------|
| `POST /bank/banks` | 创建岸段 |
| `GET /bank/banks` | 获取岸段列表 |
| `GET /bank/banks/{bank_id}` | 获取单个岸段 |
| `PUT /bank/banks/{bank_id}` | 更新岸段 |
| `DELETE /bank/banks/{bank_id}` | 删除岸段 |
| `POST /bank/tasks` | 创建任务 |
| `GET /bank/tasks` | 获取任务列表 |
| `GET /bank/tasks/{task_id}` | 获取单个任务 |
| `DELETE /bank/tasks/{task_id}` | 删除任务 |
| `POST /bank/basic-params` | 创建基础参数 |
| `GET /bank/basic-params` | 获取基础参数列表 |
| `GET /bank/basic-params/{param_id}` | 获取单个基础参数 |
| `PUT /bank/basic-params/{param_id}` | 更新基础参数 |
| `POST /bank/sections` | 创建断面（新版） |
| `GET /bank/sections` | 获取断面列表（新版） |
| `GET /bank/sections/{section_id}` | 获取单个断面（新版） |
| `PUT /bank/sections/{section_id}` | 更新断面（新版） |
| `DELETE /bank/sections/{section_id}` | 删除断面（新版） |
| `POST /bank/corrections` | 创建修正线（新版） |
| `GET /bank/corrections` | 获取修正线列表（新版） |
| `DELETE /bank/corrections/{correction_id}` | 删除修正线（新版） |
| `GET /bank/tasks/{task_id}/full` | 获取完整数据（新版） |
| `DELETE /bank/tasks/{task_id}/clear` | 清空任务数据（保留任务） |

---

## 修改的文件清单

| 文件 | 修改类型 | 说明 |
|------|----------|------|
| `database_schema.sql` | 重写 | 全新的数据库表结构（新增banks表，更新cross_sections表） |
| `util/db_ops.py` | 重写 | 全新的数据库操作函数（新增banks操作） |
| `app/main/schemas.py` | 重写 | 全新的Pydantic数据模型（新增banks相关模型） |
| `app/main/controllers.py` | 部分修改 | 更新了bank_workflow_handlers部分（新增banks相关handler） |
| `app/main/routes.py` | 重写 | 全新的路由定义（新增banks相关API） |
| `API_DESIGN_v2.md` | 新增 | 新的API设计文档 |
| `REFACTORING_GUIDE.md` | 新增 | 本文档 |

---

## 注意事项

1. **数据库迁移**：
   - 需要先备份旧数据库
   - 使用新的 `database_schema.sql` 创建新表
   - 如需迁移旧数据，需要编写迁移脚本

2. **模型调用**：
   - 模型调用接口 `/v0/mi/risk-level` 保持不变
   - **需要从cross_sections表读取参数（而非basic_params表）**

3. **参数继承逻辑**：
   - ✅ **已实现！创建section时会自动从basic_params复制参数到section表**
   - ✅ **每个section独立存储参数，修改互不干扰**

4. **LSP错误**：
   - 代码中可能存在一些LSP类型检查错误
   - 这些错误不影响代码运行，主要是类型提示问题

---

## 完成的工作 ✅

1. ✅ 新增 `banks` 表（岸段表），存储岸段几何信息
2. ✅ 新增 `banks` 相关的完整API接口（CRUD）
3. ✅ 修改 `cross_sections` 表，添加所有参数字段，**每个section独立存储参数**
4. ✅ 实现创建section时从 `basic_params` 复制参数到 `cross_sections` 的逻辑
5. ✅ 更新所有相关文档（API文档、数据库设计文档、重构指南文档）
6. ✅ 新增bank表的数据库操作函数
7. ✅ 新增bank表的Pydantic数据模型
8. ✅ 新增bank表的业务逻辑处理器
9. ✅ 新增bank表的API路由

---

## 下一步工作

1. 实现修正线应用到断面的逻辑（如果需要）
2. 编写数据库迁移脚本（如需要）
3. 更新模型调用代码以适配新的表结构（从cross_sections读取参数）
4. 编写单元测试
5. 编写集成测试

---

**文档版本**: v1.0  
**最后更新**: 2026-03-06
