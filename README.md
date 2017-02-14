OPAC SSM GRPC API
===============================

version number: 0.0.1
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

    $ pip install opac_ssm_api


Or clone the repo:

    $ git clone https://github.com/wdm0006/opac_ssm_api.git
    $ python setup.py install


GRPC Server
===========

Command to generate GRPC class:

    python -m grpc_tools.protoc -I opac_ssm_api --python_out=opac_ssm_api --grpc_python_out=opac_ssm_api opac_ssm_api/opac.proto
