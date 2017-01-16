#!/usr/bin/python
# coding: UTF-8
import os
import requests
import argparse
import logging

from grpc.tools import protoc


logger = logging.getLogger(__name__)
PATH_PB_FILES = os.path.abspath(os.path.dirname(__file__))
PROTO_URL_DEFAULT = 'http://localhost:8000/static/proto/opac.proto'


def get_proto_file(url):
    """
    Get the proto file and save.
    """

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


def generate_pb_files(url=PROTO_URL_DEFAULT):
    """
    Generete de pb classes.
    """

    get_proto_file(url)

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


def main():

    parser = argparse.ArgumentParser(
            description='Command line to handler GRPC enviroment')

    parser.add_argument(
        '--url',
        default=PROTO_URL_DEFAULT,
        help='URL to .proto file, default is: %s' % PROTO_URL_DEFAULT)
    args = parser.parse_args()

    if args.url:
        logger.info("Retrieving proto file from: %s", args.url)
        generate_pb_files(url=args.url)
    else:
        raise ValueError("Invalid Argument. You must provide an 'url'")


if __name__ == '__main__':
    main()
