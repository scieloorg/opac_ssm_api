OPAC SSM GRPC API
===============================

version number: 0.1.4
author: SciELO

Badges:
-------
[![Code Health](https://landscape.io/github/scieloorg/opac_ssm_api/master/landscape.svg?style=flat)](https://landscape.io/github/scieloorg/opac_ssm_api/master)
[![Updates](https://pyup.io/repos/github/scieloorg/opac_ssm_api/shield.svg)](https://pyup.io/repos/github/scieloorg/opac_ssm_api/)

Overview
--------

gRPC API of OPAC-SSM service

Installation / Usage
--------------------

To install use pip:

    $ pip install -e git+https://git@github.com/scieloorg/opac_ssm_api@v0.1.2#egg=opac_ssm_api


Or clone the repo:

    $ git clone git@github.com:scieloorg/opac_ssm_api.git
    $ python setup.py install

API Usage
---------

Create any instance of client and add new asset, return id of the task:

```python
from opac_ssm_api.client import Client
cli = Client()
cli.add_asset(pfile='data/fixtures/sample.img')
'3fcc9270-1740-44a3-86ad-8b0a1b7b9774'
```

Get any exist asset:

```python
from opac_ssm_api.client import Client
cli = Client()
cli.get_asset('3fcc9270-1740-44a3-86ad-8b0a1b7b9774')
(True,
{'bucket': 'UNKNOW',
'file': b'#!/usr/bin/env bash\n\n# build the docs\ncd docs\nmake clean\nmake html\ncd ..\n\n# commit and push\ngit add -A\ngit commit -m "building and pushing docs"\ngit push origin master\n\n# switch branches and pull the data we want\ngit checkout gh-pages\nrm -rf .\ntouch .nojekyll\ngit checkout master docs/build/html\nmv ./docs/build/html/* ./\nrm -rf ./docs\ngit add -A\ngit commit -m "publishing updated docs..."\ngit push origin gh-pages\n\n# switch back\ngit checkout master',
'filename': 'update_docs.sh',
'metadata': '{}',
'type': '',
'uuid': '02aac94c-8654-4ea9-9906-29601692edcb'})
```

Get any inexist asset:

```python
from opac_ssm_api.client import Client
cli = Client()
cli.get_asset('3fcc9270-1740-44a3-86ad-8b0a1b7b9774')
(False, {'error_message': 'Asset matching query does not exist.'})
```

Get URLs from asset:

```python
from opac_ssm_api.client import Client
cli = Client()
# Exist asset
cli.get_asset_info('3fcc9270-1740-44a3-86ad-8b0a1b7b9774')
(True, {'url': 'http://localhost:8001/media/assets/1248/update_docs_w7s25ZB.sh',
       'url_path': '/media/assets/1248/update_docs_w7s25ZB.sh'})

# Unexist asset
cli.get_asset_info('3fcc9270-1740-44a3-86ad-8b0a1b7b9774')
(False, {'error_message': 'Asset matching query does not exist.'})
```

Get task state:

```python
from opac_ssm_api.client import Client
cli = Client()
cli.get_task_state('3fcc9270-1740-44a3-86ad-8b0a1b7b9774')
'SUCCESS'
```

Update asset:

```python
from opac_ssm_api.client import Client
cli = Client()
help(cli.update_asset)
Update asset to SSM.

Params:
    :param uuid: uuid to update
    :param pfile: pfile path (Mandatory) or a file pointer
    :param filetype: string
    :param metadata: dict
    :param filename: filename is mandatory if pfile is a file pointer
    :param bucket_name: name of bucket

Return id of the asset, string of (UUID4)

Raise ValueError if param uuid is not a str|unicode

cli.update_asset(uuid='3fcc9270-1740-44a3-86ad-8b0a1b7b9774', filetype="jpg")
cli.get_task_state('3fcc9270-1740-44a3-86ad-8b0a1b7b9774')
'SUCESS'
cli.get_asset('3fcc9270-1740-44a3-86ad-8b0a1b7b9774')
(True, {'bucket': 'UNKNOW',
        'file': b'A\xd8\x01\x00,
        'filename': '_mdb_catalog.wt',
        'metadata': '{}',
        'type': 'jpg',
        'uuid': '3fcc9270-1740-44a3-86ad-8b0a1b7b9774'})
```

Remove any asset by id:

```python
from opac_ssm_api.client import Client
cli = Client()
cli.remove_asset('3fcc9270-1740-44a3-86ad-8b0a1b7b9774')
'd9180f82-eb22-4c9c-b25c-56747986303c'
cli.get_task_state('d9180f82-eb22-4c9c-b25c-56747986303c')
'SUCCESS'
cli.get_asset('d9180f82-eb22-4c9c-b25c-56747986303c')
(False, {'error_message': 'Asset matching query does not exist.'})
```


Create a new bucket, return id of the task:

```python
cli.add_bucket('sample')
'1d0ce52b-106f-4975-8827-07ea6f8ea573'
````

Create a new bucket, get the task id and check status:

```python
cli.add_bucket('sample')
'1d0ce52b-106f-4975-8827-07ea6f8ea573'
cli.get_task_state('1d0ce52b-106f-4975-8827-07ea6f8ea573')
'SUCCESS'
````

The method ``get_task_state`` can return ['PENDING', 'STARTED', 'RETRY', 'FAILURE', 'SUCCESS']

Remove any bucket

```python
cli.remove_bucket('sample')
'b41d4912-cb34-4dc6-b862-f67e8257b112'
cli.get_task_state('b41d4912-cb34-4dc6-b862-f67e8257b112')
'SUCCESS'
````

Create a new bucket and update name, get the task id and check status:

```python
cli.add_bucket('sample')
'1d0ce52b-106f-4975-8827-07ea6f8ea573'
cli.update_bucket('sample', 'rename_sample')
cli.get_task_state('1d0ce52b-106f-4975-8827-07ea6f8ea573')
'SUCCESS'
````

GRPC Server
===========

Command to generate GRPC class:

    python -m grpc_tools.protoc -I opac_ssm_api --python_out=opac_ssm_api --grpc_python_out=opac_ssm_api opac_ssm_api/opac.proto
