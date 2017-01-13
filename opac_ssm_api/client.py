# coding: utf-8
import os

import grpc

try:
    import opac_pb2
except ImportError:
    from cli import generate_pb_files
    generate_pb_files()
    import opac_pb2


class Client(object):

    def __init__(self, host='localhost', port='5000'):
        """
        Initialize channel and stub objects.

        Params:
            :param: host: string, default='localhost'
            :param: port: string, default='5000' (default of the SSM server service)
        """
        self.channel = grpc.insecure_channel('{0}:{1}'.format(host, port))
        self.stub = opac_pb2.AssetServiceStub(self.channel)


    def add_asset(self, file, type='', metadata=''):
        """
        Add asset to SSM.

        Params:
            :param file: file path (Mandatory)
            :param type: string
            :param metadata: dict

        Return id of the asset, string of (UUID4)
        """
        fp = open(file, 'rb')

        if not metadata:
            metadata = {}

        if not isinstance(metadata, dict):
            raise ValueError('Param metadata must be a Dict.')

        filename = os.path.basename(getattr(fp, 'name', None))

        asset = opac_pb2.Asset(file=fp.read(), filename=filename, type=type,
                       metadata=str(metadata))

        return self.stub.add_asset(asset).id

    def get_asset(self, id):
        """
        Get asset by id

        Params:
            :param id: string id of the asset (Mandatory)
        """
        if not isinstance(id, basestring):
            raise ValueError('Param id must be a str|unicode.')

        asset = self.stub.get_asset(opac_pb2.TaskId(id=id))

        return {'file': asset.file,
                'filename': asset.filename,
                'type': asset.type,
                'metadata': asset.metadata,
                'task_id': asset.task_id}

    def get_asset_info(self, id):
        """
        Get asset info by id

        Params:
            :param id: string id of the asset (Mandatory)
        """
        if not isinstance(id, basestring):
            raise ValueError('Param id must be a str|unicode.')

        asset_info = self.stub.get_asset_info(opac_pb2.TaskId(id=id))

        return {'url': asset_info.url,
                'url_path': asset_info.url_path}

    def get_task_state(self, id):
        """
        Get task state by id

        Params:
            :param id: string id of the task (Mandatory)
        """
        if not isinstance(id, basestring):
            raise ValueError('Param id must be a str|unicode.')

        task_state = self.stub.get_task_state(opac_pb2.TaskId(id=id))

        return task_state.state
