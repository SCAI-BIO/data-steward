# Clinical Backend API Doku
## Technical notes on clinical Backend  
The Clinical Backend is a [__Django__](https://www.djangoproject.com/)  application with a [__MongoDB__](https://www.mongodb.com/) as database. All applications are implemented in  [__REST__](https://restfulapi.net/) architectural style.
Django is organized in _apps_. The Clinical Backend Project is mainly devided into two _apps_ : __Upload__ and __API__. The upload app manages the data integration logic and interface. The api app is responsible for providing several apis for filtering and accessing data. The django application is deployed with any __ASGI__ Webserver, like _Daphne_ or _Uvicorn_. For production Fraunhofer SCAI provides a docker image to run on any docker capable maschine.



## RESTful Endpoints

Each api-view is tagged with the python decorator: __@api_view__.

### Session init
```
URL: https://idsn.dzne.de/clinical-backend/api/init
TYPE: POST
```
_Description_  
This API must be executed, when the Clinical-Viewer is accessed from the user to ensure that a session is established and available in the database.

_Query Parameters_  

| name | type | description |
|------|------|-------------|
|  usertoken    |   String   |      Any unique per user token to identify a session       |
|plot_ids|List of Strings|The List of hash_codes of the plots you want to initialize|

_Return Parameters_

| name | type | description |
|------|------|-------------|
|  Message   |   String   |      A response message from the backend     |
|Session| Json/Object | The session object for that particular user |

__fetch__ example:
```js
fetch('https://idsn.dzne.de/clinicla-backend/api/init', {
    method: 'POST',
    body: {
      'usertoken': "myuniqueusertoken"
      },
    headers: {
      'Content-Type': 'application/json'
    }
  });
```

### Session reset
```
URL: https://idsn.dzne.de/clinical-viewer/api/reset-session
TYPE: POST
```

_Description_  
This API is used to reset the current user session.

_Query Parameters_  

| name | type | description |
|------|------|-------------|
|  usertoken    |   String   |      The usertoken of the session that should be reset     |

_Return Parameters_

| name | type | description |
|------|------|-------------|
|  Message   |   String   |      A response message from the backend     |

__fetch__ example  
```js
fetch('https://idsn.dzne.de/clinical-backend/api/reset-session', {
    method: 'POST',
    body: {
      'usertoken': "myuniqueusertoken"
      },
    headers: {
      'Content-Type': 'application/json'
    }
  });
```

### Get data (main)
```
URL: https://idsn.dzne.de/clinical-backend/api/getdata
TYPE: GET
```

_Description_
This is the main api to get plotly data. The request body contains a control json with attributes and plot types.

_Query Parameters_  

| name | type | description |
|------|------|-------------|
|  usertoken    |   String   |      The usertoken of the session that should be reset     |
| controls | json/object | The controls json with all configurations |

_Controls Parameters_


|name|type|description|
|----|----||
|type|String|The plot type (Histo, Bar, ...)|
|attX|String|The x-axis attribute|
|attY|String|The y-axis attribute|
|attC|String|The color attribute|
|Dt|String|The delta T argument (Timeframe)|
|visit|String||
|followup|String||
|tolerance|String||
|norm|String||
|stack|String||
|fit|String||
|plot|String|the plot hash_code|
|legend|String|||


_Return Parameters_


|name|type|Description|
|--|--|--|
|Status|String|Response message from backend|
|figure|json/PlotlyJSONEncoder-Object|The plotly figure object|
|vis_per_pid|List of Tupels|Number of visits per patient ID|
|bins|String|The binning parameter|
|max_bin|String|Maximum binning|

__fetch__ example
```js
fetch('https://idsn.dzne.de/clinical-backend/api/getdata', {
    method: 'GET',
    body: {
      'usertoken': "myuniqueusertoken",      
      'controls': {
				"type": 1,
				"attX": "SARASUM",
				"attY": "LONG",
				"attC": "SCACAT2",
				"Dt": -1,
				"visit": "followup",
				"followup": 12,
				"tolerance": 2,
				"condenseX": "mean",
				"condenseY": "count",
				"condenseC": None,
				"bin": null,
				"normalize": null,
				"stack": null,
				"fit": "line",
				"legend": "right"
			}
      },
    headers: {
      'Content-Type': 'application/json'
    }
  });
```

### Filter plot

```
URL: https://idsn.dzne.de/clinical-backend/api/filter-plot
TYPE: GET
```
_Description_  
Filtering the plot and shrink the current population to a sub cohort.


_Query Parameters_


|Name|Type|Description|
|--|--|--|
|usertoken|String|The unique user token|
|select|json/object|The currently selected subgroup|
|pos|Int|||

_Response Parameters_

|Name|Type|Description|
|--|--|--|
|filter|List|List of current filters|


__fetch__ example
```js
fetch('https://idsn.dzne.de/clinical-backend/api/filter-plot', {
    method: 'GET',
    body: {
        'usertoken': "youruniqueusertoken",
        'select':{selection...},
        'pos':'0'
      },
    headers: {
      'Content-Type': 'application/json'
    }
  });
```

### Filter reset
```
URL: https://idsn.dzne.de/clinical-backend/api/filter-reset
TYPE: GET
```
_Description_

Reset the current filter.

_Query Parameters_


|Name|Type|Description|
|--|--|--|
|usertoken|String|Unique usertoken from the user|


_Response Parameters_


|Name|Type|Description|
|--|--|--|
|Message|String|A Response message from the backend|

__fetch__ example

```js
fetch('https://idsn.dzne.de/clinical-backend/api/filter-reset', {
    method: 'GET',
    body: {
        'usertoken': "youruniqueusertoken",
      },
    headers: {
      'Content-Type': 'application/json'
    }
  });
```
### Filter edit
```
URL: https://idsn.dzne.de/clinical-backend/api/filter-edit
TYPE: GET
```
_Description_

Edit the current filter.

_Query Parameters_

|Name|Type|Description|
|--|--|--|
|usertoken|String|The unique user token|
|filter_table|json/object|The plotly filter table|

_Response Parameters_

|Name|Type|Description|
|--|--|--|
|constraints|List|The List of constraints|

__fetch__ example
```js
fetch('https://idsn.dzne.de/clinical-backend/api/filter-edit', {
    method: 'GET',
    body: {
        'usertoken': "youruniqueusertoken",
        'filter_table': {}
      },
    headers: {
      'Content-Type': 'application/json'
    }
  });
```

### Filter recall  

```
URL: https://idsn.dzne.de/clinical-backend/api/filter-recall
TYPE: GET
```
_Description_

Recalling the current filter.

_Query Parameters_

|Name|Type|Description|
|--|--|--|
|subgroup|String|The filtered subgroup|
|usertoken|String| The unique usertoken|


_Response Parameters_

|Name|Type|Description|
|--|--|--|
|constraints|List|List of constraints for the plot|

__fetch__ example

```js
fetch('https://idsn.dzne.de/clinical-backend/api/filter-edit', {
    method: 'GET',
    body: {
        'usertoken': "youruniqueusertoken",
        'subgroup': {}
      },
    headers: {
      'Content-Type': 'application/json'
    }
  });
```
### Filter concept

```
URL: https://idsn.dzne.de/clinical-backend/api/filter-filter
TYPE: GET
```

_Description_


_Query Parameters_

|Name|Type|Description|
|--|--|--|
|concept|String|Concept|
|usertoken|String| The unique usertoken|


_Response Parameters_    

|Name|Type|Description|
|--|--|--|
|constraints|List|List of constraints|


__fetch__ example

```js
fetch('https://idsn.dzne.de/clinical-backend/api/filter-edit', {
    method: 'GET',
    body: {
        'usertoken': "youruniqueusertoken",
        'concept': {}
      },
    headers: {
      'Content-Type': 'application/json'
    }
  });
```

### Subgroup define

```
URL: https://idsn.dzne.de/clinical-backend/api/subgroup-subgroup
TYPE: GET
```

_Description_

Defining a subgroup for the current filter set.


_Query Parameters_

|Name|Type|Description|
|--|--|--|
|name|String|Name for the subgroup|
|usertoken|String| The unique usertoken|


_Response Parameters_

|Name|Type|Description|
|--|--|--|
|subgroup_define_output|List|A List with the keys of thhe subgroups|

__The list-key for the subgroups keys has the key "name".__

__fetch__ example

```js
fetch('https://idsn.dzne.de/clinical-backend/api/filter-edit', {
    method: 'GET',
    body: {
        'usertoken': "youruniqueusertoken",
        'name': "patients_old"
      },
    headers: {
      'Content-Type': 'application/json'
    }
  });
```

### Filter update  

```
URL: https://idsn.dzne.de/clinical-backend/api/update-filter
TYPE: POST
```

_Description_

This endpoint updates the current filter set and returns the filtered figures.

_Query Parameters_

|Name|Type|Description|
|--|--|--|
|usertoken|String|Your unique usertoken|
|filter_table|List of JSON/Object|The filtertable generated by plotly|
|concept|Int|The filter concept|


_Response Parameters_

|Name| Type| Description|
|--|--|--|
|plots|List|The list of plots where each plot looks like to output of __getdata__ (s.o.)|


__fetch__ example

```js
fetch('https://idsn.dzne.de/clinical-backend/api/update-filter', {
    method: 'POST',
    body: {
        'usertoken': "youruniqueusertoken",
        'filter_table': [{"attribute": "SARASUM", "lower": 5.312837767369539, "upper": 32.9827406799909, "list": null}],
        'concept': 1
      },
    headers: {
      'Content-Type': 'application/json'
    }
  });
```


### Authentification 
See Docu[https://djoser.readthedocs.io/en/latest/base_endpoints.html]
