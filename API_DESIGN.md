# 岸段-断面-修正线管理 API 接口设计

## 概述

本文档描述了岸段、断面、修正线的管理 API 接口，用于前端和后端数据对接。

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

## 一、岸段管理接口

### 1.1 创建岸段

**接口**: `POST /segments`

**请求体**:
```json
{
  "case_id": "case_001",
  "segments": [
    {
      "segment_id": "SEG_001",
      "segment_name": "岸段001",
      "region_code": "Mzs",
      "geometry": {
        "type": "LineString",
        "coordinates": [
          [121.47, 31.23],
          [121.48, 31.24],
          [121.49, 31.23]
        ]
      },
      "dem_id": "dem_2024.tif",
      "bench_id": "dem_2024.tif",
      "ref_id": "dem_2020.tif",
      "hydro_segment": "Mzs",
      "hydro_year": "2024",
      "hydro_set": "standard",
      "protection_level": "systemic",
      "control_level": "strict"
    }
  ],
  "overwrite": false
}
```

**响应**:
```json
{
  "success": true,
  "case_id": "case_001",
  "inserted_count": 1,
  "segments": [
    {
      "id": 1,
      "segment_id": "SEG_001",
      "segment_name": "岸段001"
    }
  ]
}
```

---

### 1.2 获取岸段列表

**接口**: `GET /segments/{case_id}`

**响应**:
```json
{
  "success": true,
  "case_id": "case_001",
  "segments": [
    {
      "id": 1,
      "segment_id": "SEG_001",
      "segment_name": "岸段001",
      "region_code": "Mzs",
      "geometry": {
        "type": "LineString",
        "coordinates": [[121.47, 31.23], [121.48, 31.24]]
      },
      "dem_id": "dem_2024.tif",
      "bench_id": "dem_2024.tif",
      "ref_id": "dem_2020.tif",
      "hydro_segment": "Mzs",
      "hydro_year": "2024",
      "hydro_set": "standard",
      "protection_level": "systemic",
      "control_level": "strict",
      "created_at": "2026-03-03T12:00:00Z",
      "updated_at": "2026-03-03T12:00:00Z"
    }
  ]
}
```

---

### 1.3 更新岸段

**接口**: `PUT /segments/{case_id}/{segment_id}`

**请求体**:
```json
{
  "segment_name": "更新后的岸段名称",
  "dem_id": "dem_2025.tif",
  "protection_level": "low"
}
```

**响应**:
```json
{
  "success": true,
  "segment_id": "SEG_001",
  "updated": true
}
```

---

### 1.4 删除岸段

**接口**: `DELETE /segments/{case_id}/{segment_id}`

**响应**:
```json
{
  "success": true,
  "segment_id": "SEG_001",
  "deleted": true,
  "sections_deleted": 5
}
```

---

## 二、断面管理接口

### 2.1 创建断面

**接口**: `POST /sections`

**请求体**:
```json
{
  "case_id": "case_001",
  "sections": [
    {
      "section_id": "SEC_001",
      "section_name": "断面001",
      "segment_id": "SEG_001",
      "region_code": "Mzs",
      "segment_index": 1,
      "geometry": {
        "type": "LineString",
        "coordinates": [
          [121.473, 31.235],
          [121.475, 31.237]
        ]
      },
      "hs": 0.5,
      "hc": 2.0,
      "water_qs": "45000",
      "tidal_level": "zc",
      "current_timepoint": "2024-01-15",
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
      }
    }
  ],
  "inherit_from_segment": true,
  "overwrite": false
}
```

**说明**:
- `inherit_from_segment`: 如果为 true，断面会从关联的岸段继承参数（protection_level, control_level 等）
- 断面可以覆盖继承的参数

**响应**:
```json
{
  "success": true,
  "case_id": "case_001",
  "inserted_count": 1,
  "sections": [
    {
      "id": 1,
      "section_id": "SEC_001",
      "section_name": "断面001",
      "segment_id": "SEG_001"
    }
  ]
}
```

---

### 2.2 获取断面列表

**接口**: `GET /sections/{case_id}`

**查询参数**:
- `segment_id`: 可选，按岸段筛选

**响应**:
```json
{
  "success": true,
  "case_id": "case_001",
  "sections": [
    {
      "id": 1,
      "section_id": "SEC_001",
      "section_name": "断面001",
      "segment_id": "SEG_001",
      "segment_name": "岸段001",
      "region_code": "Mzs",
      "segment_index": 1,
      "geometry": {
        "type": "LineString",
        "coordinates": [[121.473, 31.235], [121.475, 31.237]]
      },
      "hs": 0.5,
      "hc": 2.0,
      "protection_level": "systemic",
      "control_level": "strict",
      "water_qs": "45000",
      "tidal_level": "zc",
      "current_timepoint": "2024-01-15",
      "comparison_timepoint": "2020-01-15",
      "risk_thresholds": {...},
      "weights": {...},
      "created_at": "2026-03-03T12:00:00Z",
      "updated_at": "2026-03-03T12:00:00Z"
    }
  ]
}
```

---

### 2.3 获取单个断面详情

**接口**: `GET /sections/{case_id}/{section_id}`

**响应**:
```json
{
  "success": true,
  "section": {
    "id": 1,
    "section_id": "SEC_001",
    "section_name": "断面001",
    "segment_id": "SEG_001",
    "segment": {
      "id": 1,
      "segment_id": "SEG_001",
      "segment_name": "岸段001",
      "dem_id": "dem_2024.tif",
      "bench_id": "dem_2024.tif",
      "ref_id": "dem_2020.tif",
      "hydro_segment": "Mzs",
      "hydro_year": "2024",
      "hydro_set": "standard"
    },
    "geometry": {...},
    "hs": 0.5,
    "hc": 2.0,
    "protection_level": "systemic",
    "control_level": "strict",
    "water_qs": "45000",
    "tidal_level": "zc",
    "current_timepoint": "2024-01-15",
    "comparison_timepoint": "2020-01-15",
    "risk_thresholds": {...},
    "weights": {...}
  }
}
```

---

### 2.4 更新断面

**接口**: `PUT /sections/{case_id}/{section_id}`

**请求体**:
```json
{
  "section_name": "更新后的断面名称",
  "hs": 0.6,
  "water_qs": "50000"
}
```

**响应**:
```json
{
  "success": true,
  "section_id": "SEC_001",
  "updated": true
}
```

---

### 2.5 删除断面

**接口**: `DELETE /sections/{case_id}/{section_id}`

**响应**:
```json
{
  "success": true,
  "section_id": "SEC_001",
  "deleted": true,
  "results_deleted": 1
}
```

---

## 三、修正线管理接口

### 3.1 创建修正线

**接口**: `POST /corrections`

**请求体**:
```json
{
  "case_id": "case_001",
  "corrections": [
    {
      "correction_id": "CORR_001",
      "geometry": {
        "type": "LineString",
        "coordinates": [
          [121.472, 31.234],
          [121.478, 31.236]
        ]
      },
      "correction_rules": {
        "protection_level": "low",
        "control_level": "low",
        "other_params": {
          "note": "此区域防护等级降低"
        }
      },
      "description": "临时修正此区域的参数"
    }
  ],
  "overwrite": false
}
```

**响应**:
```json
{
  "success": true,
  "case_id": "case_001",
  "inserted_count": 1,
  "corrections": [
    {
      "id": 1,
      "correction_id": "CORR_001",
      "description": "临时修正此区域的参数"
    }
  ]
}
```

---

### 3.2 获取修正线列表

**接口**: `GET /corrections/{case_id}`

**响应**:
```json
{
  "success": true,
  "case_id": "case_001",
  "corrections": [
    {
      "id": 1,
      "correction_id": "CORR_001",
      "geometry": {
        "type": "LineString",
        "coordinates": [[121.472, 31.234], [121.478, 31.236]]
      },
      "correction_rules": {
        "protection_level": "low",
        "control_level": "low",
        "other_params": {
          "note": "此区域防护等级降低"
        }
      },
      "description": "临时修正此区域的参数",
      "created_at": "2026-03-03T12:00:00Z",
      "updated_at": "2026-03-03T12:00:00Z"
    }
  ]
}
```

---

### 3.3 更新修正线

**接口**: `PUT /corrections/{case_id}/{correction_id}`

**请求体**:
```json
{
  "description": "更新后的描述",
  "correction_rules": {
    "protection_level": "normal"
  }
}
```

**响应**:
```json
{
  "success": true,
  "correction_id": "CORR_001",
  "updated": true
}
```

---

### 3.4 删除修正线

**接口**: `DELETE /corrections/{case_id}/{correction_id}`

**响应**:
```json
{
  "success": true,
  "correction_id": "CORR_001",
  "deleted": true
}
```

---

## 四、综合查询接口

### 4.1 获取完整数据（岸段+断面+修正线）

**接口**: `GET /cases/{case_id}/full`

**响应**:
```json
{
  "success": true,
  "case_id": "case_001",
  "data": {
    "segments": [...],
    "sections": [...],
    "corrections": [...]
  }
}
```

---

### 4.2 应用修正线到断面

**接口**: `POST /cases/{case_id}/apply-corrections`

**说明**: 应用修正线到受影响的断面，更新断面参数

**响应**:
```json
{
  "success": true,
  "case_id": "case_001",
  "updated_sections": 5,
  "applied_corrections": 2
}
```

---

### 4.3 获取断面的有效参数（包含修正线）

**接口**: `GET /sections/{case_id}/{section_id}/effective`

**响应**:
```json
{
  "success": true,
  "section_id": "SEC_001",
  "effective_params": {
    "hs": 0.5,
    "hc": 2.0,
    "protection_level": "low",
    "control_level": "low",
    "water_qs": "45000",
    "tidal_level": "zc",
    "current_timepoint": "2024-01-15",
    "comparison_timepoint": "2020-01-15",
    "risk_thresholds": {...},
    "weights": {...}
  },
  "applied_corrections": [
    {
      "correction_id": "CORR_001",
      "applied_rules": ["protection_level", "control_level"]
    }
  ]
}
```

---

## 五、批量操作接口

### 5.1 批量导入数据

**接口**: `POST /cases/{case_id}/import`

**请求体**:
```json
{
  "case_id": "case_001",
  "segments": [...],
  "sections": [...],
  "corrections": [...],
  "overwrite": false
}
```

**响应**:
```json
{
  "success": true,
  "case_id": "case_001",
  "imported": {
    "segments": 10,
    "sections": 50,
    "corrections": 5
  }
}
```

---

### 5.2 清空 case 数据

**接口**: `DELETE /cases/{case_id}`

**响应**:
```json
{
  "success": true,
  "case_id": "case_001",
  "deleted": {
    "segments": 10,
    "sections": 50,
    "corrections": 5,
    "results": 50
  }
}
```

---

## 六、错误响应

### 通用错误格式

```json
{
  "success": false,
  "error": "错误描述",
  "details": {
    "code": "ERROR_CODE",
    "message": "详细错误信息"
  }
}
```

### 常见错误码

| 错误码 | 说明 |
|--------|------|
| `SEGMENT_NOT_FOUND` | 岸段不存在 |
| `SECTION_NOT_FOUND` | 断面不存在 |
| `CORRECTION_NOT_FOUND` | 修正线不存在 |
| `CASE_NOT_FOUND` | Case 不存在 |
| `INVALID_GEOMETRY` | 几何数据无效 |
| `DUPLICATE_ID` | ID 重复 |

---

## 七、使用流程示例

### 完整工作流

1. **创建 case 并导入数据**
   ```
   POST /cases/{case_id}/import
   ```

2. **获取数据查看**
   ```
   GET /cases/{case_id}/full
   ```

3. **应用修正线**
   ```
   POST /cases/{case_id}/apply-corrections
   ```

4. **获取断面有效参数**
   ```
   GET /sections/{case_id}/{section_id}/effective
   ```

5. **调用模型计算**
   ```
   POST /v0/mi/risk-level
   ```

---

## 附录：数据结构参考

### correction_rules 支持的字段

```json
{
  "protection_level": "systemic|normal|low|no",
  "control_level": "strict|normal|low|no",
  "hs": 0.5,
  "hc": 2.0,
  "water_qs": "45000",
  "tidal_level": "xc|zc|dc",
  "other_params": {
    "note": "备注信息",
    "reason": "修改原因"
  }
}
```

---

**文档版本**: v1.0  
**最后更新**: 2026-03-03
