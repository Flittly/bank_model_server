# 任务-断面-基础参数管理 API 接口设计（重构版 v2）

## 概述

本文档描述了重构后的任务管理、断面管理、基础参数管理的 API 接口，用于前端和后端数据对接。

**主要变化**：
- 移除了 `bank_segments` 表
- 新增 `tasks` 表（任务表）
- 新增 `basic_params` 表（基础参数表）
- 修改 `cross_sections` 表结构
- 移除了 `correction_lines` 表
- 新增断面更新接口 `PUT /bank/sections/{section_id}`

---

## 通用说明

### 基础路径
```
/v0
```

### 数据格式
- 请求和响应统一使用 JSON 格式
- 几何数据使用标准 GeoJSON 格式
- 坐标系：WGS84 (EPSG:4326)

---

## 一、任务管理接口

### 1.1 创建任务

**接口**: `POST /bank/tasks`

**请求体**:
```json
{
  "tasks": [
    {
      "task_id": "TASK_001",
      "task_name": "监测任务001",
      "bank_ids": ["BANK_001", "BANK_002", "BANK_003"],
      "description": "这是一个示例监测任务"
    }
  ],
  "overwrite": false
}
```

**字段说明**:
- `task_id`: 任务唯一ID
- `task_name`: 任务名称
- `bank_ids`: 岸段ID列表（JSON数组）
- `description`: 任务描述（可选）

**响应**:
```json
{
  "success": true,
  "inserted_count": 1,
  "tasks": [
    {
      "id": 1,
      "task_id": "TASK_001",
      "task_name": "监测任务001"
    }
  ]
}
```

---

### 1.2 获取任务列表

**接口**: `GET /bank/tasks`

**响应**:
```json
{
  "success": true,
  "tasks": [
    {
      "id": 1,
      "task_id": "TASK_001",
      "task_name": "监测任务001",
      "bank_ids": ["BANK_001", "BANK_002"],
      "description": "这是一个示例监测任务",
      "created_at": "2026-03-03T12:00:00Z",
      "updated_at": "2026-03-03T12:00:00Z"
    }
  ]
}
```

---

### 1.3 获取单个任务详情

**接口**: `GET /bank/tasks/{task_id}`

**响应**:
```json
{
  "success": true,
  "task": {
    "id": 1,
    "task_id": "TASK_001",
    "task_name": "监测任务001",
    "bank_ids": ["BANK_001", "BANK_002"],
    "description": "这是一个示例监测任务",
    "created_at": "2026-03-03T12:00:00Z",
    "updated_at": "2026-03-03T12:00:00Z"
  }
}
```

---

### 1.4 删除任务

**接口**: `DELETE /bank/tasks/{task_id}`

**说明**: 删除任务会级联删除相关的断面、风险结果

**响应**:
```json
{
  "success": true,
  "message": "Task deleted successfully"
}
```

---

## 二、基础参数管理接口

### 2.1 创建基础参数

**接口**: `POST /bank/basic-params`

**请求体**:
```json
{
  "params": [
    {
      "param_id": "PARAM_001",
      "param_name": "默认参数模板",
      
      "segment": "Mzs",
      "current_timepoint": "2024-01-15",
      "set_name": "standard",
      "water_qs": "45000",
      "tidal_level": "zc",
      
      "bench_id": "dem_2024.tif",
      "ref_id": "dem_2020.tif",
      
      "hs": 0.5,
      "hc": 2.0,
      
      "protection_level": "systemic",
      "control_level": "strict",
      
      "comparison_timepoint": "2020-01-15",
      
      "risk_thresholds": {
        "Dsed": [0.3, 0.5, 0.7],
        "Zb": [2.0, 4.0, 6.0],
        "Sa": [15, 25, 35],
        "Ln": [0.5, 1.0, 1.5],
        "PQ": [1000, 2000, 3000],
        "Ky": [0.5, 0.3, 0.1],
        "Zd": [0.1, 0.2, 0.3],
        "all": [0.2, 0.4, 0.6]
      },
      
      "weights": {
        "wRE": [0.3, 0.4, 0.3],
        "wNM": [0.4, 0.3, 0.3],
        "wGE": [0.4, 0.4, 0.2],
        "wRL": [0.3, 0.3, 0.4]
      },
      
      "other_params": {
        "note": "这是默认参数"
      }
    }
  ],
  "overwrite": false
}
```

**响应**:
```json
{
  "success": true,
  "inserted_count": 1,
  "params": [
    {
      "id": 1,
      "param_id": "PARAM_001",
      "param_name": "默认参数模板"
    }
  ]
}
```

---

### 2.2 获取基础参数列表

**接口**: `GET /bank/basic-params`

**响应**:
```json
{
  "success": true,
  "params": [
    {
      "id": 1,
      "param_id": "PARAM_001",
      "param_name": "默认参数模板",
      "segment": "Mzs",
      "current_timepoint": "2024-01-15",
      "hs": 0.5,
      "hc": 2.0,
      "protection_level": "systemic",
      "control_level": "strict",
      "created_at": "2026-03-03T12:00:00Z",
      "updated_at": "2026-03-03T12:00:00Z"
    }
  ]
}
```

---

### 2.3 获取单个基础参数详情

**接口**: `GET /bank/basic-params/{param_id}`

**响应**:
```json
{
  "success": true,
  "param": {
    "id": 1,
    "param_id": "PARAM_001",
    "param_name": "默认参数模板",
    "segment": "Mzs",
    "current_timepoint": "2024-01-15",
    "set_name": "standard",
    "water_qs": "45000",
    "tidal_level": "zc",
    "bench_id": "dem_2024.tif",
    "ref_id": "dem_2020.tif",
    "hs": 0.5,
    "hc": 2.0,
    "protection_level": "systemic",
    "control_level": "strict",
    "comparison_timepoint": "2020-01-15",
    "risk_thresholds": {...},
    "weights": {...},
    "other_params": {...},
    "created_at": "2026-03-03T12:00:00Z",
    "updated_at": "2026-03-03T12:00:00Z"
  }
}
```

---

### 2.4 更新基础参数

**接口**: `PUT /bank/basic-params/{param_id}`

**请求体**:
```json
{
  "param_name": "更新后的参数名称",
  "hs": 0.6,
  "water_qs": "50000",
  "protection_level": "low"
}
```

**响应**:
```json
{
  "success": true,
  "param_id": "PARAM_001",
  "updated": true
}
```

---

## 三、断面管理接口（重构版）

### 3.1 创建断面

**接口**: `POST /bank/sections`

**请求体**:
```json
{
  "task_id": "TASK_001",
  "sections": [
    {
      "section_id": "SEC_001",
      "section_name": "断面001",
      "bank_id": "BANK_001",
      "region_code": "Mzs",
      "segment_index": 1,
      "geometry": {
        "type": "LineString",
        "coordinates": [
          [121.473, 31.235],
          [121.475, 31.237]
        ]
      },
      "section_geometry": {
        "type": "LineString",
        "coordinates": [
          [121.473, 31.235],
          [121.475, 31.237]
        ]
      },
      "basic_param_id": 1
    }
  ],
  "inherit_from_basic_param": true,
  "overwrite": false
}
```

**字段说明**:
- `task_id`: 所属任务的ID
- `bank_id`: 所属岸段的ID
- `basic_param_id`: 关联的基础参数ID（数据库自增ID，可选）
- `inherit_from_basic_param`: 是否从基础参数继承（目前仅标记，逻辑需完善）

**响应**:
```json
{
  "success": true,
  "task_id": "TASK_001",
  "inserted_count": 1,
  "sections": [
    {
      "id": 1,
      "section_id": "SEC_001",
      "section_name": "断面001",
      "bank_id": "BANK_001"
    }
  ]
}
```

---

### 3.2 获取断面列表

**接口**: `GET /bank/sections`

**查询参数**:
- `task_id`: 可选，按任务筛选
- `bank_id`: 可选，按岸段筛选

**响应**:
```json
{
  "success": true,
  "task_id": "TASK_001",
  "sections": [
    {
      "id": 1,
      "task_id": "TASK_001",
      "task_name": "监测任务001",
      "section_id": "SEC_001",
      "section_name": "断面001",
      "bank_id": "BANK_001",
      "region_code": "Mzs",
      "segment_index": 1,
      "geometry": {
        "type": "LineString",
        "coordinates": [[121.473, 31.235], [121.475, 31.237]]
      },
      "section_geometry": {...},
      "basic_param_id": 1,
      "created_at": "2026-03-03T12:00:00Z",
      "updated_at": "2026-03-03T12:00:00Z"
    }
  ]
}
```

---

### 3.3 获取单个断面详情

**接口**: `GET /bank/sections/{section_id}`

**响应**:
```json
{
  "success": true,
  "section": {
    "id": 1,
    "task_id": "TASK_001",
    "task_name": "监测任务001",
    "section_id": "SEC_001",
    "section_name": "断面001",
    "bank_id": "BANK_001",
    "region_code": "Mzs",
    "segment_index": 1,
    "geometry": {...},
    "section_geometry": {...},
    "basic_param_id": 1,
    "basic_param": {...},
    "created_at": "2026-03-03T12:00:00Z",
    "updated_at": "2026-03-03T12:00:00Z"
  }
}
```

---

### 3.4 更新断面

**接口**: `PUT /bank/sections/{section_id}`

**说明**: 前端修改断面参数后，直接通过此接口更新断面信息。不再需要修正线表。

**请求体**:
```json
{
  "section_name": "更新后的断面名称",
  "bank_id": "BANK_002",
  "region_code": "Mzs",
  "segment_index": 2,
  "geometry": {
    "type": "LineString",
    "coordinates": [[121.474, 31.236], [121.476, 31.238]]
  },
  "section_geometry": {...},
  "basic_param_id": 2
}
```

**字段说明**:
- 所有字段都是可选的，只更新提供的字段
- `geometry`: 更新断面几何时，会自动更新 start_point、end_point 和 geom 字段

**响应**:
```json
{
  "success": true,
  "section_id": "SEC_001",
  "updated": true
}
```

---

### 3.5 删除断面

**接口**: `DELETE /bank/sections/{section_id}`

**响应**:
```json
{
  "success": true,
  "section_id": "SEC_001",
  "deleted": true
}
```

---

## 四、综合查询接口

### 4.1 获取完整数据（任务+断面）

**接口**: `GET /bank/tasks/{task_id}/full`

**响应**:
```json
{
  "success": true,
  "task_id": "TASK_001",
  "data": {
    "task": {...},
    "sections": [...]
  }
}
```

---

### 4.2 清空任务数据（保留任务本身）

**接口**: `DELETE /bank/tasks/{task_id}/clear`

**说明**: 清空任务相关的断面、风险结果，但保留任务记录

**响应**:
```json
{
  "success": true,
  "task_id": "TASK_001",
  "deleted": {
    "sections": 10,
    "results": 10
  }
}
```

---

## 五、完整工作流示例

### 前端使用流程

1. **创建基础参数模板**（可选，首次使用时）
   ```
   POST /bank/basic-params
   ```

2. **创建任务**
   ```
   POST /bank/tasks
   ```

3. **前端选择断面，发送到后端**
   ```
   POST /bank/sections
   ```
   - 断面数据包含：section_id, section_name, bank_id, geometry, basic_param_id
   - basic_param_id 关联到基础参数

4. **后端返回断面及继承的参数**
   ```
   GET /bank/sections/{section_id}
   ```
   - 返回断面信息 + 关联的 basic_param 完整参数

5. **前端展示参数供用户确认/修改**

6. **用户修改参数后，直接更新断面**
   ```
   PUT /bank/sections/{section_id}
   ```
   - 直接修改断面的字段，无需修正线表

7. **调用模型计算**
   ```
   POST /v0/mi/risk-level
   ```

---

## 六、设计说明

### 为什么移除修正线表？

1. **简化架构** - 不再需要维护额外的修正线表
2. **直接更新** - 前端修改参数后，直接通过 PUT 接口更新断面
3. **减少复杂度** - 不需要处理修正线与断面的合并逻辑
4. **更直观** - 断面数据的修改直接反映在断面表中

### 断面更新的优势

1. **灵活性** - 可以更新断面的任意字段
2. **原子性** - 一次更新操作完成所有修改
3. **可追溯** - updated_at 字段记录最后更新时间
4. **简单** - 不需要处理修正线的应用逻辑

---

## 七、数据关系图

```
tasks (任务表)
  ├─ id (主键)
  ├─ task_id (唯一标识)
  ├─ task_name
  ├─ bank_ids (JSON数组，存储岸段ID列表)
  └─ description

basic_params (基础参数表)
  ├─ id (主键)
  ├─ param_id (唯一标识)
  ├─ param_name
  ├─ segment, current_timepoint, water_qs, tidal_level...
  ├─ hs, hc, protection_level, control_level...
  └─ risk_thresholds, weights (JSONB)

cross_sections (断面表 - 重构版)
  ├─ id (主键)
  ├─ task_id (外键 → tasks.id)
  ├─ section_id (唯一标识)
  ├─ section_name
  ├─ bank_id (岸段ID)
  ├─ geometry (空间几何)
  ├─ section_geometry (JSONB，用于前端展示)
  └─ basic_param_id (外键 → basic_params.id，可选)
```

---

## 附录：数据库表结构参考

详见 `database_schema.sql` 文件。

---

**文档版本**: v2.1  
**最后更新**: 2026-03-06  
**主要变更**: 移除 correction_lines 表，新增断面更新接口