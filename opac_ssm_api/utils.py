#!/usr/bin/python
# coding: UTF-8
import os
import requests
import logging

from grpc.tools import protoc


logger = logging.getLogger(__name__)
PATH_PB_FILES = os.path.abspath(os.path.dirname(__file__))


def get_proto_file(host='localhost', port='80', proto_path='/static/proto/opac.proto'):
    """
    Get the proto file and save.
    """

    url = 'http://{0}:{1}{2}'.format(host, port, proto_path)

    try:
        resp = requests.get(url)
    except (requests.exceptions.ConnectionError) as e:
        logger.error(
            "Fail when getting the proto file from: %s. Error: %s",
            url, str(e))
        raise e
    else:
        if resp.status_code == 200:
            filename = '{0}/opac.proto'.format(PATH_PB_FILES)
            with open(filename, 'w') as fp:
                fp.write(resp.text)
        else:
            logger.error(
                "Unexpected response when getting the proto file from: %s. Error (status code): %s",
                url, resp.status_code)


def generate_pb_files(host='localhost', port='80', proto_path='/static/proto/opac.proto'):
    """
    Generete de pb classes.
    """

    get_proto_file(host=host, port=port, proto_path=proto_path)

    try:
        protoc.main((
          '',
          '--proto_path={0}'.format(PATH_PB_FILES),
          '--python_out={0}'.format(PATH_PB_FILES),
          '--grpc_python_out={0}'.format(PATH_PB_FILES),
          '{0}/opac.proto'.format(PATH_PB_FILES)
        ))
    except Exception as e:
        msg = "Error found when generating PB files. Exception: %s"
        logger.error(msg, str(e))
        raise e
