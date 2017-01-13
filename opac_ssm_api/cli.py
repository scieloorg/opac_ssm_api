#!/usr/bin/python
# coding: UTF-8
import os
import requests
import argparse

from grpc.tools import protoc

PATH_PB_FILES = os.path.abspath(os.path.dirname(__file__))

def get_proto_file(url):
    """
    Get the proto file and save.
    """
    resp = requests.get(url)

    if resp.status_code == 200:
        fp = open('{0}/opac.proto'.format(PATH_PB_FILES), 'w')
        fp.write(resp.text)
        fp.close()

def generate_pb_files(url='http://localhost:8000/static/proto/opac.proto'):
    """
    Generete de pb classes.
    """
    get_proto_file(url)

    protoc.main((
      '',
      '--proto_path={0}'.format(PATH_PB_FILES),
      '--python_out={0}'.format(PATH_PB_FILES),
      '--grpc_python_out={0}'.format(PATH_PB_FILES),
      '{0}/opac.proto'.format(PATH_PB_FILES)
    ))


def main():

    parser = argparse.ArgumentParser(
            description='Command line to handler GRPC enviroment')

    parser.add_argument('--url', default='http://localhost:8000/static/proto/opac.proto',
                        help='Give the URL to .proto file, default is: http://localhost:8000/static/proto/opac.proto')
    args = parser.parse_args()

    if args.url:
        generate_pb_files(url=args.url)


if __name__ == '__main__':
    main()
