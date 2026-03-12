# Bank Model Service (v0.07)

Model service applications for Collapse-Bank Monitoring and Warning.  

---

## What Is <font color=red>Async</font>

Some of the BMS APIs are marked with <font color=red>**Async**</font>. It means that, if a model case, related to a specific async api request, has not existed, model will run asynchronously and return response with  content "NONE" at once.

---

## Model Case

### Get Status of Model Case

Get the status of a specific model case.

```
GET /v0/mc/status?id="{ case-id }"
```

#### Responses  

<font color=green> **200** OK </font>  

**Response schema**: application/json

```json
{
  	"status": "UNLOCK" || "LOCK" || "NONE" || "RUNNING" || "COMPLETE" || "ERROR"
}
```

<font color=red> **404** Model Case ID Not Found </font>   



### Get Status of Model Cases

Get the status of specific model cases.

```
POST /v0/mcs/status
```

**Request body schema**: application/json

```json
{
    "case-ids": [
        "{ case-id-0 }",
        "{ case-id-1 }",
        "{ case-id-n }"
    ]
}
```

#### Responses  

<font color=green> **200** OK </font>  

**Response schema**: application/json

```json
{
  	"{ case-id-0 }": "UNLOCK" || "LOCK" || "NONE" || "RUNNING" || "COMPLETE" || "ERROR",
  	"{ case-id-1 }": "UNLOCK" || "LOCK" || "NONE" || "RUNNING" || "COMPLETE" || "ERROR",
  	"{ case-id-n }": "UNLOCK" || "LOCK" || "NONE" || "RUNNING" || "COMPLETE" || "ERROR"
}
```

<font color=red> **404** Model Case ID Not Found </font>  



### Get Call Time of Model Cases

Get the id and the last call time (Unix Epoch) of all model cases. The response array is sorted by the call time from the newest to oldest.

```
GET /v0/mcs/time
```

#### Responses  

<font color=green> **200** OK </font>  

**Response schema**: application/json

```json
{
    "timestamps": [
        {
            "id": "{ case-id }",
            "time": "{ unix-timestamp }",
            "status": "LOCK" || "UNLOCK"
        }
    ]
}
```



### Get Serialized Content of Model Cases

Get the serialized content (request url and body) of model cases.

```
POST /v0/mcs/serialization
```

**Request body schema**: application/json

```json
{
    "case-ids": [
        "{ case-id-0 }",
        "{ case-id-1 }"
    ]
}
```

#### Responses  

<font color=green> **200** OK </font>  

**Response schema**: application/json

```json
{
    "serialization-list": [
        {
            "id": "{ case-id }",
            "serialization": {
                "url": "{ request-url }",
                "json": "{ request-json }"
            }
        }
    ]
}
```

<font color=red> **404** Model Case ID Not Found </font>  



### Get Model Case Result

Get the result of a specific model case.

```
GET /v0/mc/result?id="{ case-id }"
```

#### Responses  

<font color=green> **200** OK </font>  

**Response schema**: application/json

```json
{
  	"result": "{ model-case-result-json }"
}
```

<font color=red> **404** Model Case ID Not Found </font>  



### Get Error Log

Get the error log of a specific model case.

```
GET /v0/mc/error?id="{ case-id }"
```

#### Responses  

<font color=green> **200** OK </font>  

**Response schema**: text/plain

```txt
"{ error-log }"
```

<font color=red> **404** Model Case ID Not Found </font> 



### Get Preceding Error Cases

Get ids of preceding error cases that a specific model case dependences (The response list also contains the model case itself).

```
GET /v0/mc/pre-error-cases?id="{ case-id }"
```

#### Responses  

<font color=green> **200** OK </font>  

**Response schema**: application/json

```json
{
    "case-list": [
        "{ case-ids }"
    ]
}
```

<font color=red> **404** Model Case ID Not Found </font> 



### Delete Model Case

Delete a specific model case.

```
DELETE /v0/mc?id="{ case-id }"
```

#### Responses  

<font color=green> **200** OK </font>  

<font color=red> **404** Model Case ID Not Found </font>  



### Delete Model Cases

Delete model cases.

```
POST /v0/mcs
```

**Request body schema**: application/json

```json
{
    "case-ids": [
        "{ case-id }"
    ]
}
```

#### Responses  

<font color=green> **200** OK </font>  

<font color=red> **404** Model Case ID Not Found </font>  

---

## File

### Get Disk Usage

Get the size of the storage utilization (GB).

```
GET /v0/fs/usage
```

#### Response

<font color=green> **200** OK </font>

**Response schema**: application/json

```json
{
  	"usage": "{ disk-usage-giga-bytes }"
}
```


### Get Result File by Case ID

Get a result file in a specific model case through file's name.

```
GET /v0/fs/result/file?id="{ case-id }"&name="{ filename }"
```

#### Responses  

<font color=green> **200** OK </font>  

**Response schema**: application/octet-stream

<font color=red> **404** Filename Not Found </font>  

<font color=red> **404** Model Case ID Not Found </font>  


### Get Resource File by Directory

Get a resoruce file by directory.

```
GET /v0/fs/resource/file?name="{ file-directory }"
```

#### Responses  

<font color=green> **200** OK </font>  

**Response schema**: application/octet-stream

<font color=red> **404** Filename Not Found </font>  

<font color=red> **404** Model Case ID Not Found </font>  



### Get Result File Zip

Get a zip of the result files in a specific model case.

```
GET /v0/fs/result/zip?id="{ case-id }"
```

#### Responses  

<font color=green> **200** OK </font>  

**Response schema**: application/octet-stream

<font color=red> **404** Model Case ID Not Found </font>  



### Get Hydrodynamic Resource List

Get the list of all hydrodynamic resource sets.

```
GET /v0/fs/resource/hydrodynamic/list
```

#### Responses  

<font color=green> **200** OK </font>  

**Response schema**: application/json

```json
{
    "resource": [
        {
            "name": "{ segment-name }",
            "date": [
                {
                    "year": "{ YYYY }",
                    "sets": [
                        {
                            "name": "{ set-name }",
                            "list": [
                                {
                                    "name": "{ case-name }",
                                    "temp": true || false,
                                    "description": "{ case-description }"
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    ]
}
```



### Upload Resource File Zip

Send a resource file in zip format to a designated directory. After this file zip is unzipped in the directory, model cases can use its resource files.

```
POST /v0/fs/resource/zip
```

**Request body schema**: multipart/form-data

| Field | Type |              Description               |
| :---: | :--: | :------------------------------------: |
| json  | JSON | Json data containing the resource type |
| file  | File |          Zip file of resource          |

**Json Part**:

```json
{
    "type": "geojson" || "json" || "dem" || "tiff" || "shp" || "riskLevel" || "hydrodynamic"
}
```

#### Responses  

<font color=green> **200** OK </font>  

<font color=red> **404** Dem Resource Not Found </font>  



### Upload Resource of ADF

Send a resource adf of a specific segment.

```
POST /v0/fs/resource/adf
```

**Request body schema**: multipart/form-data

| Field | Type |             Description              |
| :---: | :--: | :----------------------------------: |
| json  | JSON | Json data containing the description |
| file  | File |             Zip about adf            |

**Json Part**:

```json
{
    "segment": "{ segment-name }",
    "year": "{ YYYY }",
    "set": "{ set-name }",
    "name": "{ shp-name }"
}
```

#### Responses  

<font color=green> **200** OK </font>  

**Response schema**: application/json

```json
{
    "directory": "{ resource-directory }"
}
```

<font color=red> **400** No JSON Data Provided </font>  

<font color=red> **400** No File Part Provided </font>  

<font color=red> **400** No Selected File </font>  

<font color=red> **400** Files Provided Are Incomplete </font>  

<font color=red> **400** File Type Not Allowed </font>  



### Upload Resource of Tiff

Send a resource tiff of a specific segment.

```
POST /v0/fs/resource/tiff
```

**Request body schema**: multipart/form-data

| Field | Type |             Description              |
| :---: | :--: | :----------------------------------: |
| json  | JSON | Json data containing the description |
| file  | File |            Zip about tiff            |

**Json Part**:

```json
{
    "segment": "{ segment-name }",
    "year": "{ YYYY }",
    "set": "{ set-name }",
    "name": "{ shp-name }"
}
```

#### Responses  

<font color=green> **200** OK </font>  

**Response schema**: application/json

```json
{
    "directory": "{ resource-directory }"
}
```

<font color=red> **400** No JSON Data Provided </font>  

<font color=red> **400** No File Part Provided </font>  

<font color=red> **400** No Selected File </font>  

<font color=red> **400** Files Provided Are Incomplete </font>  

<font color=red> **400** File Type Not Allowed </font>  



### Upload Resource of Json

Send a resource json of a specific segment.

```
POST /v0/fs/resource/json
```

**Request body schema**: multipart/form-data

| Field | Type |             Description              |
| :---: | :--: | :----------------------------------: |
| json  | JSON | Json data containing the description |
| file  | File |            Zip about json            |

**Json Part**:

```json
{
    "segment": "{ segment-name }",
    "year": "{ YYYY }",
    "set": "{ set-name }",
    "name": "{ json-name }"
}
```

#### Responses  

<font color=green> **200** OK </font>  

**Response schema**: application/json

```json
{
    "directory": "{ resource-directory }"
}
```

<font color=red> **400** No JSON Data Provided </font>  

<font color=red> **400** No File Part Provided </font>  

<font color=red> **400** No Selected File </font>  

<font color=red> **400** Files Provided Are Incomplete </font>  

<font color=red> **400** File Type Not Allowed </font>  



### Upload Resource of Geojson

Send a resource geojson of a specific segment.

```
POST /v0/fs/resource/geojson
```

**Request body schema**: multipart/form-data

| Field | Type |             Description              |
| :---: | :--: | :----------------------------------: |
| json  | JSON | Json data containing the description |
| file  | File |         Zip about geojson            |

**Json Part**:

```json
{
    "segment": "{ segment-name }",
    "year": "{ YYYY }",
    "set": "{ set-name }",
    "name": "{ geojson-name }"
}
```

#### Responses  

<font color=green> **200** OK </font>  

**Response schema**: application/json

```json
{
    "directory": "{ resource-directory }"
}
```

<font color=red> **400** No JSON Data Provided </font>  

<font color=red> **400** No File Part Provided </font>  

<font color=red> **400** No Selected File </font>  

<font color=red> **400** Files Provided Are Incomplete </font>  

<font color=red> **400** File Type Not Allowed </font>  



### Upload Resource of Shapefile

Send a resource shapefile of a specific segment.

```
POST /v0/fs/resource/shapefile
```

**Request body schema**: multipart/form-data

| Field | Type |             Description              |
| :---: | :--: | :----------------------------------: |
| json  | JSON | Json data containing the description |
| file  | File |         Zip about shapefile          |

**Json Part**:

```json
{
    "segment": "{ segment-name }",
    "year": "{ YYYY }",
    "set": "{ set-name }",
    "name": "{ shp-name }"
}
```

#### Responses  

<font color=green> **200** OK </font>  

**Response schema**: application/json

```json
{
    "directory": "{ resource-directory }"
}
```

<font color=red> **400** No JSON Data Provided </font>  

<font color=red> **400** No File Part Provided </font>  

<font color=red> **400** No Selected File </font>  

<font color=red> **400** Files Provided Are Incomplete </font>  

<font color=red> **400** File Type Not Allowed </font>  



### Upload Resource of Hydrodynamic Case

Send a resource file of a specific hydrodynamic case in zip format. After this file zip is unzipped in the directory, render resource of this resource case will be generated.

```
POST /v0/fs/resource/hydrodynamic
```

**Request body schema**: multipart/form-data

| Field | Type |             Description              |
| :---: | :--: | :----------------------------------: |
| json  | JSON | Json data containing the description |
| file  | File |    Zip about fort.63 and fort.64     |

**Json Part**:

```json
{
    "segment": "{ segment-name }",
    "year": "{ YYYY }",
    "set": "{ set-name }",
    "name": "{ case-name }",
    "temp": true || false,
    "boundary": "{ directory-boundary-file }"
}
```

#### Responses  

<font color=green> **200** OK </font>


### Delete Resource Directory

Delete the directory of a specific resource content.

```
DELETE /v0/fs/resource?directory="{ directory }"
```

#### Responses  

<font color=green> **200** OK </font>  

**Response schema**: application/json

```json
{
    "directory": "{ resource-directory }"
}
```

<font color=red> **400** No JSON Data Provided </font>  

<font color=red> **400** No File Part Provided </font>  

<font color=red> **400** No Selected File </font>  

<font color=red> **400** Files Provided Are Incomplete </font>  

<font color=red> **400** File Type Not Allowed </font>  

---

## Riverbed Evolution  

### Calculate Region Flush (<font color=red>Async</font>)

Calculate the flush result by dem resource at two timepoints within a specific region or the full area. 

- If "region-geometry" in request body is "NONE", server will calculate the global flush.

```
POST /v0/re/region-flush
```

**Request body schema**: application/json

```json
{
    "bench-id": "{ dem-file-name }",
    "ref-id": "{ dem-file-name }",
    "region-geometry": "{ GeoJson }" || "NONE"
}
```

**Example**

``````json
{
    "bench-id": "199801_dem/w001001.adf",
    "ref-id": "200408_dem/w001001.adf",
    "region-geometry": {
      "type": "FeatureCollection",
      "features": [
        {
          "type": "Feature",
          "properties": {
            "name": "Example Polygon"
          },
          "geometry": {
            "type": "Polygon",
            "coordinates": [
              [
                [121.35857784308524,31.660508611487913],
                [121.29264135171792,31.576285441022137],
                [121.45748258013526,31.57394482076768],
                [121.3860513811536,31.508383603511106],
                [121.50693494865948,31.56458175211411],
                [121.35857784308524,31.660508611487913]
              ]
            ]
          }
        }
      ]
  	}
}
``````

#### Responses  

<font color=green> **200** OK </font>  

**Response schema**: application/json

```json
{
    "case-id": "{ case-id }",
  	"model": "{ model-name }",
    "raw-tif": "{ file-name }" || "NONE",
    "extent-json": "{ file-name }" || "NONE",
    "visualization-png": "{ file-name }" || "NONE",
}
```

<font color=red> **404** Dem Resource Not Found </font>  



### Calculate Section View (<font color=red>Async</font>)

Calculate the section view and slope ratio by a specific dem resource.

```
POST /v0/re/section-view
```

**Request body schema**: application/json

```json
{
    "dem-id": "{ dem-file-name }",
    "section-geometry": "{ GeoJson }"
}
```

#### Responses  

<font color=green> **200** OK </font>  

**Response schema**: application/json

```json
{
    "case-id": "{ case-id }",
  	"model": "{ model-name }",
    "raw-json": "{ file-name }" || "NONE",
    "visualization-txt": "{ file-name }" || "NONE"
    "interval": "{ number }" || "NONE"
}
```

<font color=red> **404** Dem Resource Not Found </font>  



### Calculate Section Contrast (<font color=red>Async</font>)

Calculate the flush from the perspective of section and provide a section views at two timepoints.

```
POST /v0/re/section-contrast
```

**Request body schema**: application/json

```json
{
    "bench-id": "{ dem-file-name }",
  	"ref-id": "{ dem-file-name }",
    "section-geometry": "{ GeoJson }"
}
```

#### Responses  

<font color=green> **200** OK </font>  

**Response schema**: application/json

```json
{
    "case-id": "{ case-id }",
  	"model": "{ model-name }",
    "raw-txt": "{ file-name }" || "NONE"
    "interval": "{ number }" || "NONE"
}
```

<font color=red> **404** Dem Resource Not Found </font>  



### Calculate River Volume (<font color=red>Async</font>)

Calculate the river volume within a specific region.

```
POST /v0/re/river-volume
```

**Request body schema**: application/json

```json
{
  	"dem-id": "{ dem-file-name }",
    "region-geometry": "{ GeoJson }",
    "water-depth": "{ number-water-depth }"
}
```

#### Responses  

<font color=green> **200** OK </font>  

**Response schema**: application/json

```json
{
    "case-id": "{ case-id }",
  	"model": "{ model-name }",
  	"raw-tif": "{ file-name }" || "NONE",
    "extent-json": "{ file-name }" || "NONE",
  	"visualization-png": "{ file-name }" || "NONE",
    "volume-summary-txt": "{ file-name }" || "NONE",
}
```

<font color=red> **404** Dem Resource Not Found </font>  



### Calculate Region Contour (<font color=red>Async</font>)

Calculate the contour lines within a specific region or the full area. 

- If "region-geometry" in request body is "NONE", server will calculate the global flush contour lines.

```
POST /v0/re/region-contour
```

**Request body schema**: application/json

```json
{
  	"bench-id": "{ dem-file-name }",
  	"ref-id": "{ dem-file-name }",
    "region-geometry": "{ GeoJson }"
}
```

#### Responses  

<font color=green> **200** OK </font>  

**Response schema**: application/json

```json
{
    "case-id": "{ case-id }",
  	"model": "{ model-name }",
  	"raw-shp": "{ file-name }" || "NONE",
    "visualization-geojson": "{ file-name }" || "NONE"
}
```

<font color=red> **404** Dem Resource Not Found </font>  

---

## Numerical Model

### Calculate Hydrodynamic (<font color=red>Async</font>)

Calculate the water level, depth and speed by water-qs and tidal-level.

```
POST /v0/nm/hydrodynamic
```

**Request body schema**: application/json

```json
{
    "segment": "{ segment-name }",
    "year": "{ YYYY }",
    "set": "{ set-name }",
    "water-qs": "{ number-water-qs }",
    "tidal-level": "{ number-tidal-difference }" || "dc" || "zc" || "xc"
}
```

#### Responses  

<font color=green> **200** OK </font>  

**Response schema**: application/json

```json
{
    "case-id": "{ case-id }",
   	"segment": "{ segment-name }" || "NONE",
   	"year": "{ YYYY }" || "NONE",
   	"set": "{ set-name }" || "NONE",
   	"water-qs": "{ number-water-qs }" || "NONE",
   	"tidal-level": "{ number-tidal-difference }" || "dc" || "zc" || "xc" || "NONE",
   	"data-source": "database" || "NONE",
   	"visualization-uv-bin": [ "{ file-name }" ] || "NONE",
   	"visualization-station-bin": "{ file-name }" || "NONE",
    "visualization-description-json": "{ file-name }" || "NONE"
}
```

<font color=red> **404** Not Found </font>



### Calculate Real Hydrodynamic Case (<font color=red>Async</font>)

Send resource files of a specific hydrodynamic case. After flow-field data based on these files is calculated, raw data and render resource of this resource case will be generated.

- This service is verYYYYYYYYYYYYYY SSSSSSSSSSSSSSSSSlow.

```
POST /v0/fs/resource/real-hydrodynamic
```

**Request body schema**: multipart/form-data

|  Field  | Type |                  Description                  |
| :-----: | :--: | :-------------------------------------------: |
|  json   | JSON |     Json data containing the description      |
| fort.13 | File |         File about vertex attributes          |
| fort.14 | File |          File about flow field mesh           |
| fort.15 | File |           File about configuration            |
| fort.19 | File |   File about boundary conditions of runoff    |
| fort.20 | File | File about boundary conditions of tidel level |

**Json Part**:

```json
{
    "segment": "{ segment-name }",
    "year": "{ YYYY }",
    "set": "{ set-name }",
    "name": "{ case-name }",
    "temp": true || false,
    "boundary": "{ directory-boundary-file }"
}
```

#### Responses  

<font color=green> **200** OK </font>

<font color=red> **404** Not Found </font>



### Get Flow Field Velocity (<font color=red>Async</font>)

Get the flow field velocity by time-point, lng and lat.

```
GET /v0/nm/flow-field-velocity?case-id="{case-id}"&lng="{lng}"&lat="{lat}"
```

#### Responses  

<font color=green> **200** OK </font>  

**Response schema**: application/json

```json
{
    "case-id": "{ case-id }",
  	"model": "{ model-name }",
    "result": "NONE" || {
      "us": [ "{ number }" ],
      "vs": [ "{ number }" ]
    }
}
```

<font color=red> **404** Not Found </font>



### Get Flow Field Velocities (<font color=red>Async</font>)

Get the flow field velocities by time-point, lng and lat.

```
POST /v0/nm/flow-field-velocity
```

**Request body schema**: application/json

```json
{
    "case-id": "{ case-id }",
    "sample-points": [
      {
        "lng": "{ lng }",
        "lat": "{ lat }"
      }
    ]
}
```

#### Responses  

<font color=green> **200** OK </font>  

**Response schema**: application/json

```json
{
    "case-id": "{ case-id }",
  	"model": "{ model-name }",
    "result": "NONE" || [
      {
        "us": [ "{ number }" ],
        "vs": [ "{ number }" ]
      }
    ]
}
```

<font color=red> **404** Dem Resource Not Found </font>

---

## Erosion Model

### Calculate BSTEM (<font color=red>Async</font>)

Calculate the BSTEM.

``````
POST /v0/em/bstem
``````

Request body schema: application/json

``````json
{
    "dem-id": "{ dem-file-name }" || "NONE",
    "section-geometry": "{ GeoJson }" || "NONE",
    "x-values": [ "{ number }" ] || "NONE",
    "z-values": [ "{ number }" ] || "NONE",
    "index-toe":  "{ number }" || "NONE",
    "flow-elevation": "{ number-flow-elevation }",
    "bank-layer-thickness": [ "{ number }" ] || "NONE"
}
``````

#### Responses

<font color=green> **200** OK </font>  

**Response schema**: application/json

```json
{
    "case-id": "{ case-id }",
  	"model": "{ model-name }",
    "fos": "{ number }" || "NONE",
    "see": "{ number }" || "NONE",
    "ssa": "{ number }" || "NONE",
    "point1": [ "{ number-x }", "{ number-z }" ],
    "point2": [ "{ number-x }", "{ number-z }" ]
}
```

<font color=red> **404** Dem Resource Not Found </font>

---

## Multiple Indicators

The result of each indicator is a 1 x 4 vector. The relationship between risk level and components of this vector is as follows:

|      Low       | Relatively Low | Relatively High |      High      |
| :------------: | :------------: | :-------------: | :------------: |
| [ 1, 0, 0, 0 ] | [ 0, 1, 0, 0 ] | [ 0, 0, 1, 0 ]  | [ 0, 0, 0, 1 ] |

### Calculate Soil Composition (<font color=red>Async</font>)

Calculate the soil composition indicator ( $D~sed~$ ).

``````
POST /v0/mi/soil-composition
``````

Request body schema: application/json

``````json
{
    "hs": "{ number-thickness-of-underlying-sand-layer }",
    "hc": "{ number-thickness-of-overlying-clay-layer }",
    "risk-threshold": "NONE" || [
      "{ number-threshold-between-low-and-relativelyLow-risk }",
      "{ number-threshold-between-relativelyLow-and-relativelyHigh-risk }",
      "{ number-threshold-between-relativelyHigh-and-high-risk }"
    ]
}
``````

#### Responses

<font color=green> **200** OK </font>  

**Response schema**: application/json

```json
{
    "case-id": "{ case-id }",
  	"model": "{ model-name }",
    "Dsed": "{ number-soil-composition }" || "NONE",
  	"risk-level": "{ vec4 }" || "NONE"
}
```

<font color=red> **400** Thichness of Overlying Clay Layer Not Allowed </font>

<font color=red> **404** Segment ID Not Found </font>



### Calculate Slope Protection (<font color=red>Async</font>)

Calculate the slope protection indicator.

``````
POST /v0/mi/slope-protection
``````

Request body schema: application/json

``````json
{
    "protection-level": "systemic" || "normal" || "low" || "no"
}
``````

#### Responses

<font color=green> **200** OK </font>  

**Response schema**: application/json

```json
{
    "case-id": "{ case-id }",
  	"model": "{ model-name }",
    "risk-level": "{ vec4 }" || "NONE"
}
```

<font color=red> **404** Segment ID Not Found </font>



### Calculate Load Control (<font color=red>Async</font>)

Calculate the load control indicator.

``````
POST /v0/mi/load-control
``````

Request body schema: application/json

``````json
{
    "control-level": "strict" || "normal" || "low" || "no"
}
``````

#### Responses

<font color=green> **200** OK </font>  

**Response schema**: application/json

```json
{
    "case-id": "{ case-id }",
  	"model": "{ model-name }",
    "risk-level": "{ vec4 }" || "NONE"
}
```

<font color=red> **404** Segment ID Not Found </font>



### Calculate Height Difference (<font color=red>Async</font>)

Calculate the height difference indicator ($Z~b~$) between beach and channel.

``````
POST /v0/mi/height-difference
``````

Request body schema: application/json

``````json
{
    "dem-id": "{ dem-file-name }",
    "section-geometry": "{ GeoJson }",
    "risk-threshold": "NONE" || [
      "{ number-threshold-between-low-and-relativelyLow-risk }",
      "{ number-threshold-between-relativelyLow-and-relativelyHigh-risk }",
      "{ number-threshold-between-relativelyHigh-and-high-risk }"
    ]
}
``````

#### Responses

<font color=green> **200** OK </font>  

**Response schema**: application/json

```json
{
    "case-id": "{ case-id }",
  	"model": "{ model-name }",
    "Zb": "{ number }" || "NONE",
    "risk-level": "{ vec4 }" || "NONE"
}
```

<font color=red> **404** DEM ID Not Found </font>



### Calculate Slope Rate (<font color=red>Async</font>)

Calculate the max slope rate ($S~a~$) among a specific section.

``````
POST /v0/mi/slope-rate
``````

Request body schema: application/json

``````json
{
    "dem-id": "{ dem-file-name }",
    "section-geometry": "{ GeoJson }",
    "risk-threshold": "NONE" || [
      "{ number-threshold-between-low-and-relativelyLow-risk }",
      "{ number-threshold-between-relativelyLow-and-relativelyHigh-risk }",
      "{ number-threshold-between-relativelyHigh-and-high-risk }"
    ]
}
``````

#### Responses

<font color=green> **200** OK </font>  

**Response schema**: application/json

```json
{
    "case-id": "{ case-id }",
  	"model": "{ model-name }",
    "Sa": "{ number }" || "NONE",
    "risk-level": "{ vec4 }" || "NONE"
}
```

<font color=red> **404** DEM ID Not Found </font>



### Calculate Nearshore Flush (<font color=red>Async</font>)

Calculate the max flush in a specific section per month ($L~n~$) between the current and the comparison dem data.

- The timepoint of the comparison dem data **MUST** be **EARLIER** than the current dem data.

``````
POST /v0/mi/nearshore-flush
``````

Request body schema: application/json

``````json
{
    "bench-id": "{ dem-file-name }",
    "ref-id": "{ dem-file-name }",
  	"current-timepoint": "{ YYYY-MM-DD }",
  	"comparison-timepoint": "{ YYYY-MM-DD }",
    "section-geometry": "{ GeoJson }",
    "risk-threshold": "NONE" || [
      "{ number-threshold-between-low-and-relativelyLow-risk }",
      "{ number-threshold-between-relativelyLow-and-relativelyHigh-risk }",
      "{ number-threshold-between-relativelyHigh-and-high-risk }"
    ]
}
``````

#### Responses

<font color=green> **200** OK </font>  

**Response schema**: application/json

```json
{
    "case-id": "{ case-id }",
  	"model": "{ model-name }",
    "Ln": "{ number }" || "NONE",
    "risk-level": "{ vec4 }" || "NONE"
}
```

<font color=red> **400** Comparison Timepoint Later Than Current Timepoint Not Allowed </font>

<font color=red> **404** DEM ID Not Found </font>



### Calculate Flow Equivalent (<font color=red>Async</font>)

Calculate the riverbed flow equivalent ($P~Q~$) in a specific year.

``````
POST /v0/mi/flow-equivalent
``````

Request body schema: application/json

``````json
{
    "segment": "{ segment-name }",
    "year": "{ YYYY }",
    "risk-threshold": "NONE" || [
      "{ number-threshold-between-low-and-relativelyLow-risk }",
      "{ number-threshold-between-relativelyLow-and-relativelyHigh-risk }",
      "{ number-threshold-between-relativelyHigh-and-high-risk }"
    ]
}
``````

#### Responses

<font color=green> **200** OK </font>  

**Response schema**: application/json

```json
{
    "case-id": "{ case-id }",
  	"model": "{ model-name }",
    "PQ": "{ number }" || "NONE",
    "risk-level": "{ vec4 }" || "NONE"
}
```

<font color=red> **404** Year Not Found </font>



### Calculate Anti-Impact Speed (<font color=red>Async</font>)

Calculate the anti-impact speed ($K~y~$) at the maximum point of the slope toe within a specific section.

``````
POST /v0/mi/anti-impact-speed
``````

Request body schema: application/json

``````json
{
    "dem-id": "{ dem-file-name }",
    "section-geometry": "{ GeoJson }",
    "segment": "{ segment-name }",
    "year": "{ YYYY }",
    "set": "{ set-name }",
    "water-qs": "{ number-water-qs }",
    "tidal-level": "{ number-tidal-difference }" || "dc" || "zc" || "xc",
    "risk-threshold": "NONE" || [
      "{ number-threshold-between-low-and-relativelyLow-risk }",
      "{ number-threshold-between-relativelyLow-and-relativelyHigh-risk }",
      "{ number-threshold-between-relativelyHigh-and-high-risk }"
    ]
}
``````

#### Responses

<font color=green> **200** OK </font>  

**Response schema**: application/json

```json
{
    "case-id": "{ case-id }",
  	"model": "{ model-name }",
    "Ky": "{ number }" || "NONE",
    "risk-level": "{ vec4 }" || "NONE"
}
```

<font color=red> **404** DEM ID Not Found </font>



### Calculate Water-Level Fluctuation (<font color=red>Async</font>)

Calculate the water-level fluctuation ($Z~d~$) at the maximum point of the slope toe within a specific section.

``````
POST /v0/mi/water-level-fluctuation
``````

Request body schema: application/json

``````json
{
    "dem-id": "{ dem-file-name }",
    "section-geometry": "{ GeoJson }",
    "segment": "{ segment-name }",
    "year": "{ YYYY }",
    "set": "{ set-name }",
    "water-qs": "{ number-water-qs }",
    "tidal-level": "{ number-tidal-difference }" || "dc" || "zc" || "xc",
    "risk-threshold": "NONE" || [
      "{ number-threshold-between-low-and-relativelyLow-risk }",
      "{ number-threshold-between-relativelyLow-and-relativelyHigh-risk }",
      "{ number-threshold-between-relativelyHigh-and-high-risk }"
    ]
}
``````

#### Responses

<font color=green> **200** OK </font>  

**Response schema**: application/json

```json
{
    "case-id": "{ case-id }",
  	"model": "{ model-name }",
    "Zd": "{ number }" || "NONE",
    "risk-level": "{ vec4 }" || "NONE"
}
```

<font color=red> **404** DEM ID Not Found </font>



### Calculate Risk Level (<font color=red>Async</font>)

Calculate the risk level at a specific section.

``````
POST /v0/mi/risk-level
``````

Request body schema: application/json

``````json
{
    "segment": "{ segment-name }",
    "set": "{ set-name }",
    "current-timepoint": "{ YYYY-MM-DD }",
    "comparison-timepoint": "{ YYYY-MM-DD }",
    "hs": "{ number-thickness-of-underlying-sand-layer }",
    "hc": "{ number-thickness-of-overlying-clay-layer }",
    "protection-level": "systemic" || "normal" || "low" || "no",
    "control-level": "strict" || "normal" || "low" || "no",
    "section-geometry": "{ GeoJson }",
    "bench-id": "{ dem-file-name }",
    "ref-id": "{ dem-file-name }",
    "water-qs": "{ number-water-qs }",
    "tidal-level": "{ number-tidal-difference }" || "dc" || "zc" || "xc",
    "wRE": "NONE" || "{ number-weight-riverbed-evolution }",
    "wNM": "NONE" || "{ number-weight-numerical-model }",
    "wGE": "NONE" || "{ number-weight-geology-andengineering }",
    "risk-thresholds": "NONE" || {
      "Dsed": "NONE" || [
        "{ number-threshold-between-low-and-relativelyLow-risk }",
        "{ number-threshold-between-relativelyLow-and-relativelyHigh-risk }",
        "{ number-threshold-between-relativelyHigh-and-high-risk }"
      ],
      "Zb": "NONE" || [
          "{ number-threshold-between-low-and-relativelyLow-risk }",
          "{ number-threshold-between-relativelyLow-and-relativelyHigh-risk }",
          "{ number-threshold-between-relativelyHigh-and-high-risk }"
      ],
      "Sa": "NONE" || [
          "{ number-threshold-between-low-and-relativelyLow-risk }",
          "{ number-threshold-between-relativelyLow-and-relativelyHigh-risk }",
          "{ number-threshold-between-relativelyHigh-and-high-risk }"
      ],
      "Ln": "NONE" || [
          "{ number-threshold-between-low-and-relativelyLow-risk }",
          "{ number-threshold-between-relativelyLow-and-relativelyHigh-risk }",
          "{ number-threshold-between-relativelyHigh-and-high-risk }"
      ],
      "PQ": "NONE" || [
          "{ number-threshold-between-low-and-relativelyLow-risk }",
          "{ number-threshold-between-relativelyLow-and-relativelyHigh-risk }",
          "{ number-threshold-between-relativelyHigh-and-high-risk }"
      ],
      "Ky": "NONE" || [
          "{ number-threshold-between-low-and-relativelyLow-risk }",
          "{ number-threshold-between-relativelyLow-and-relativelyHigh-risk }",
          "{ number-threshold-between-relativelyHigh-and-high-risk }"
      ],
      "Zd": "NONE" || [
          "{ number-threshold-between-low-and-relativelyLow-risk }",
          "{ number-threshold-between-relativelyLow-and-relativelyHigh-risk }",
          "{ number-threshold-between-relativelyHigh-and-high-risk }"
      ],
      "all": "NONE" || [
          "{ number-threshold-between-low-and-relativelyLow-risk }",
          "{ number-threshold-between-relativelyLow-and-relativelyHigh-risk }",
          "{ number-threshold-between-relativelyHigh-and-high-risk }"
      ],
    }
}
``````

#### Responses

<font color=green> **200** OK </font>  

**Response schema**: application/json

```json
{
    "case-id": "{ case-id }",
  	"model": "{ model-name }",
    "multi-indicator-ids": {
      "Dsed": "{ case-id }",
      "PL": "{ case-id }",
      "LC": "{ case-id }",
      "Zb": "{ case-id }",
      "Sa": "{ case-id }",
      "Ln": "{ case-id }",
      "PQ": "{ case-id }",
      "Ky": "{ case-id }",
      "Zd": "{ case-id }"
    },
    "result": "{ number }",
    "risk-level": "{ vec4 }" || "NONE"
}
```

<font color=red> **404** DEM ID Not Found </font>
