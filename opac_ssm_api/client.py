# coding: utf-8
import os
import grpc
import six
import logging

logger = logging.getLogger(__name__)

try:
    import opac_pb2
except ImportError:
    logger.warning("pb2 files not found. Retrieving via URL")
    from utils import generate_pb_files
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

        if not metadata:
            metadata = {}
        elif not isinstance(metadata, dict):
            error_msg = 'Param "metadata" must be a Dict or None.'
            logger.exception(error_msg)
            raise ValueError(error_msg)
        else:
            error_msg = 'Param "metadata" must be a Dict or None.'
            logger.exception(error_msg)
            raise ValueError(error_msg)

        try:
            if os.path.isfile(file) and os.access(file, os.R_OK):
                with open(file, 'rb') as fp:
                    filename = os.path.basename(getattr(fp, 'name', None))
                    file_content = fp.read()
            else:
                error_msg = "The file pointed: (%s) is not a file or is unreadable."
                logger.error(error_msg, file)
        except IOError as e:
            error_msg = "Error found when trying to open file: %s"
            logger.exception(error_msg, file)
            raise e
        else:
            asset = opac_pb2.Asset(
                file=file_content,
                filename=filename,
                type=type,
                metadata=str(metadata)
            )

            return self.stub.add_asset(asset).id

    def get_asset(self, id):
        """
        Get asset by id

        Params:
            :param id: string id of the asset (Mandatory)
        """

        if not isinstance(id, six.string_types):
            raise ValueError('Param "id" must be a str|unicode.')

        asset = self.stub.get_asset(opac_pb2.TaskId(id=id))

        return {
            'file': asset.file,
            'filename': asset.filename,
            'type': asset.type,
            'metadata': asset.metadata,
            'task_id': asset.task_id
        }

    def get_asset_info(self, id):
        """
        Get asset info by id

        Params:
            :param id: string id of the asset (Mandatory)
        """

        if not isinstance(id, six.string_types):
            msg = 'Param id must be a str|unicode.'
            logger.exception(msg)
            raise ValueError(msg)

        asset_info = self.stub.get_asset_info(opac_pb2.TaskId(id=id))

        return {
            'url': asset_info.url,
            'url_path': asset_info.url_path
        }

    def get_task_state(self, id):
        """
        Get task state by id

        Params:
            :param id: string id of the task (Mandatory)
        """

        if not isinstance(id, six.string_types):
            msg = 'Param id must be a str|unicode.'
            logger.exception(msg)
            raise ValueError(msg)

        task_state = self.stub.get_task_state(opac_pb2.TaskId(id=id))

        return task_state.state
