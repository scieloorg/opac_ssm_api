# coding: utf-8
import os
import six
import grpc
import json
import logging
from imp import reload

from grpc_health.v1 import health_pb2

from opac_ssm_api import utils

logger = logging.getLogger(__name__)

HOST_NAME = os.getenv('OPAC_SSM_GRPC_SERVER_HOST', 'localhost')
HOST_PORT = os.getenv('OPAC_SSM_GRPC_SERVER_PORT', '5000')

HOST_PROTO_NAME = os.getenv('OPAC_SSM_PROTO_FILE_HOST', 'raw.githubusercontent.com')
HTTP_PROTO_PORT = os.getenv('OPAC_SSM_PROTO_FILE_PORT', '80')
PROTO_PATH = os.getenv('OPAC_SSM_PROTO_FILE_PATH', '/scieloorg/opac_ssm/master/grpc_ssm/opac.proto')
PROTO_UPDATE = os.getenv('OPAC_SSM_PROTO_UPDATE', 'False') == 'True'

MAX_RECEIVE_MESSAGE_LENGTH = int(os.getenv('MAX_RECEIVE_MESSAGE_LENGTH', 90 * 1024 * 1024))  # 90MB
MAX_SEND_MESSAGE_LENGTH = int(os.getenv('MAX_SEND_MESSAGE_LENGTH', 90 * 1024 * 1024))  # 90MB

try:
    from opac_ssm_api import opac_pb2_grpc, opac_pb2
except ImportError:
    logger.warning("Retrieving proto file from URL: http://%s:%s%s", HOST_PROTO_NAME, HTTP_PROTO_PORT, PROTO_PATH)
    utils.generate_pb_files(host=HOST_PROTO_NAME, port=HTTP_PROTO_PORT, proto_path=PROTO_PATH)
    from opac_ssm_api import opac_pb2_grpc, opac_pb2


class Client(object):

    def __init__(self, host=HOST_NAME, port=HOST_PORT, proto_http_port=HTTP_PROTO_PORT,
                 proto_path=PROTO_PATH, update_pb_class=PROTO_UPDATE):
        """
        Initialize channel and stub objects.

        Params:
            :param: host: string, default='localhost'
            :param: port: string, default='5000' (default of the SSM server service)
            :param: proto_http_port: string, default='8001' (default of the HTTP server)
            :param: proto_path: string, default='/static/proto/opac.proto' (default path to proto file)
        """
        if update_pb_class:
            utils.generate_pb_files(host, proto_http_port, proto_path)
            reload(opac_pb2_grpc)

        options = [('grpc.max_receive_message_length', MAX_RECEIVE_MESSAGE_LENGTH),
                   ('grpc.max_send_message_length', MAX_SEND_MESSAGE_LENGTH)]

        self.channel = grpc.insecure_channel('{0}:{1}'.format(host, port), options)
        self.stubAsset = opac_pb2_grpc.AssetServiceStub(self.channel)
        self.stubBucket = opac_pb2_grpc.BucketServiceStub(self.channel)
        self.stubHealth = health_pb2.HealthStub(self.channel)

    def status(self, service_name=''):
        """
        Check service status.

        Params:
            :param service_name: service name.

        Return string: UNKNOWN, SERVING
        """
        expected_response_status = {
            0: "NOT SERVING",
            1: "SERVING",
            2: "UNKNOWN",
            3: "NOT FOUND",
        }

        request = health_pb2.HealthCheckRequest(service=service_name)

        try:
            resp = self.stubHealth.Check(request)
        except grpc.RpcError as e:
            if grpc.StatusCode.NOT_FOUND == e.code():
                return expected_response_status[3]
            elif grpc.StatusCode.UNAVAILABLE == e.code():
                return expected_response_status[0]
            else:
                return expected_response_status[2]
        else:
            return expected_response_status[resp.status]

    def add_asset(self, pfile, filename='', filetype='', metadata='',
                  bucket_name='UNKNOW'):
        """
        Add asset to SSM.

        Params:
            :param pfile: pfile path (Mandatory) or a file pointer
            :param filetype: string
            :param metadata: dict
            :param filename: filename is mandatory if pfile is a file pointer
            :param bucket_name: name of bucket

        Return id of the asset, string of (UUID4)

        Raise ValueError if param metadata is not a dict
        Raise ValueError if not set filename when pfile is a file pointer
        Raise IOError if pfile is not a file or cant read the file
        """
        if not metadata:
            metadata = {}
        elif not isinstance(metadata, dict):
            error_msg = 'Param "metadata" must be a Dict or None.'
            logger.error(error_msg)
            raise ValueError(error_msg)

        if hasattr(pfile, 'read'):
            if not filename:
                error_msg = 'Param "filename" is required'
                logger.error(error_msg)
                raise ValueError(error_msg)
            else:
                filename = filename
                file_content = pfile.read()
        else:
            if os.path.isfile(pfile) and os.access(pfile, os.R_OK):
                with open(pfile, 'rb') as fp:
                    filename = os.path.basename(getattr(fp, 'name', None))
                    file_content = fp.read()
            else:
                error_msg = "The file pointed: (%s) is not a file or is unreadable."
                logger.error(error_msg, pfile)
                raise IOError(error_msg)

        asset = opac_pb2.Asset(
            file=file_content,
            filename=filename,
            type=filetype,
            metadata=json.dumps(metadata),
            bucket=bucket_name
        )

        return self.stubAsset.add_asset(asset).id

    def get_asset(self, _id):
        """
        Get asset by id.

        Params:
            :param _id: string id of the asset (Mandatory)

        Return tuple (True  ) when exist asset and tuple (False, {ERROR_MESSAGE})
        when asset doesnt exist or other error.

        Raise ValueError if param id is not a str|unicode
        """

        if not isinstance(_id, six.string_types):
            msg = 'Param _id must be a str|unicode.'
            logger.exception(msg)
            raise ValueError(msg)
        try:
            asset = self.stubAsset.get_asset(opac_pb2.TaskId(id=_id))
        except Exception as e:
            logger.error(e)
            return (False, {'error_message': e.details()})
        else:
            return (True, {'file': asset.file,
                           'filename': asset.filename,
                           'type': asset.type,
                           'metadata': asset.metadata,
                           'uuid': asset.uuid,
                           'bucket': asset.bucket,
                           'checksum': asset.checksum})

    def query_asset(self, filters=None, metadata=None):
        """
        Get assets by any filters and any metadata.

        Params:
            :param filters: Dictionary
            :param metadata: JSON with metadada about asset

        Return a list of asset(dict) with all metadata, look:

        [
            {
                "type": "pdf",
                "asset_url": "media/assets/resp/v78n3/editorial.pdf",
                "bucket_name": "resp/v78n3",
                "checksum": "29a44233da06c80e36a6c73bfd4bc76f78b1e41d18f6fcac5801948c28b160ab",
                "filename": "editorial.pdf",
                "uuid": "9ad6762b-48fa-4ac3-9804-6cc554e78300",
                "metadata": {
                    "lang": "es",
                    "article_pid":"S1135-57272004000300001",
                    "registration_date": "2017-04-06T12:55:40.731500",
                    "bucket_name": "resp/v78n3",
                    "article_folder": "editorial",
                    "issue_folder": "v78n3",
                    "journal_folder": "resp"
                }
            }
        ]
        """

        if filters is None:
            filters = {}
        elif not isinstance(filters, dict):
            error_msg = 'Param "filters" must be a Dict or None.'
            logger.error(error_msg)
            raise ValueError(error_msg)

        if metadata:
            if isinstance(metadata, str):
                filters['metadata'] = metadata
            elif isinstance(metadata, dict):
                filters['metadata'] = json.dumps(metadata)
            else:
                raise ValueError("Metadada must be a dict or str")

        assets = self.stubAsset.query(opac_pb2.Asset(**filters)).assets

        ret_list = []

        if assets:

            dict_asset = {}

            for asset in assets:
                dict_asset['type'] = asset.type
                dict_asset['absolute_url'] = asset.absolute_url
                dict_asset['full_absolute_url'] = asset.full_absolute_url
                dict_asset['bucket'] = asset.bucket
                dict_asset['checksum'] = asset.checksum
                dict_asset['filename'] = asset.filename
                dict_asset['uuid'] = asset.uuid
                dict_asset['metadata'] = asset.metadata
                dict_asset['created_at'] = asset.created_at
                dict_asset['updated_at'] = asset.updated_at

                ret_list.append(dict_asset)

        return ret_list

    def get_bucket(self, _id):
        """
        Get bucket by id of asset.

        Params:
            :param _id: string id of the asset (Mandatory)

        Return tuple (True, Result) when exist asset and tuple (False, {ERROR_MESSAGE})
        when asset doesnt exist or other error.

        Raise ValueError if param id is not a str|unicode
        """

        if not isinstance(_id, six.string_types):
            msg = 'Param _id must be a str|unicode.'
            logger.exception(msg)
            raise ValueError(msg)
        try:
            bucket = self.stubAsset.get_bucket(opac_pb2.TaskId(id=_id))
        except Exception as e:
            logger.error(e)
            return (False, {'error_message': e.details()})
        else:
            return (True, {'name': bucket.name})

    def get_asset_info(self, _id):
        """
        Get asset info by id.

        Params:
            :param _id: string id of the asset (Mandatory)

        Return tuple (True, Result) when exist asset and tuple (False, {ERROR_MESSAGE})
        when asset doesnt exist or other error.

        Raise ValueError if param id is not a str|unicode
        """

        if not isinstance(_id, six.string_types):
            msg = 'Param _id must be a str|unicode.'
            logger.exception(msg)
            raise ValueError(msg)

        try:
            asset_info = self.stubAsset.get_asset_info(opac_pb2.TaskId(id=_id))
        except Exception as e:
            logger.error(e)
            return (False, {'error_message': e.details()})

        return (True, {
                        'url': asset_info.url,
                        'url_path': asset_info.url_path
                    })

    def get_task_state(self, _id):
        """
        Get task state by id

        Params:
            :param _id: string id of the task (Mandatory)

        Raise ValueError if param id is not a str|unicode
        """

        if not isinstance(_id, six.string_types):
            msg = 'Param _id must be a str|unicode.'
            logger.exception(msg)
            raise ValueError(msg)

        task_state = self.stubAsset.get_task_state(opac_pb2.TaskId(id=_id))

        return task_state.state

    def update_asset(self, uuid, pfile=None, filename=None, filetype=None, metadata=None,
                     bucket_name=None):
        """
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
        """

        if not isinstance(uuid, six.string_types):
            raise ValueError('Param "uuid" must be a str|unicode.')

        update_params = {}

        if self.stubAsset.exists_asset(opac_pb2_grpc.TaskId(id=uuid)):

            update_params['uuid'] = uuid

            if not metadata:
                update_params['metadata'] = json.dumps({})
            elif not isinstance(metadata, dict):
                error_msg = 'Param "metadata" must be a Dict or None.'
                logger.exception(error_msg)
                raise ValueError(error_msg)
            else:
                update_params['metadata'] = json.dumps(metadata)

            if pfile is not None:
                if hasattr(pfile, 'read'):
                    if not filename:
                        error_msg = 'Param "filename" is required'
                        logger.exception(error_msg)
                        raise IOError(error_msg)
                    else:
                        filename = filename
                        file_content = pfile.read()
                else:
                    if os.path.isfile(pfile) and os.access(pfile, os.R_OK):
                        with open(pfile, 'rb') as fp:
                            filename = os.path.basename(getattr(fp, 'name', None))
                            file_content = fp.read()
                    else:
                        error_msg = "The file pointed: (%s) is not a file or is unreadable."
                        logger.error(error_msg, pfile)
                        raise IOError(error_msg)

                update_params['file'] = file_content
                update_params['filename'] = filename

            if filetype:
                update_params['type'] = filetype

            if bucket_name:
                update_params['bucket'] = bucket_name

            asset = opac_pb2.Asset(**update_params)

            return self.stubAsset.update_asset(asset).id
        else:
            error_msg = "Dont exist asset with id: %s"
            logger.error(error_msg, uuid)

    def remove_asset(self, _id):
        """
        Task to remove asset by id.

        Params:
            :param _id: UUID (Mandatory)

        Raise ValueError if param _id is not a str|unicode
        """

        if not isinstance(_id, six.string_types):
            raise ValueError('Param "_id" must be a str|unicode.')

        if self.stubAsset.exists_asset(opac_pb2.TaskId(id=_id)):
            return self.stubAsset.remove_asset(opac_pb2.TaskId(id=_id))

    def add_bucket(self, name):
        """
        Add bucket.

        Params:
            :param name: name (Mandatory).

        Return id of the bucket, string of (UUID4)

        Raise ValueError if param name is not a str|unicode
        """

        if not isinstance(name, six.string_types):
            msg = 'Param name must be a str|unicode.'
            logger.exception(msg)
            raise ValueError(msg)

        return self.stubBucket.add_bucket(opac_pb2.BucketName(name=name)).id

    def update_bucket(self, name, new_name):
        """
        Update bucket.

        Params:
            :param name: name (Mandatory).
            :param new_name: new_name (Mandatory).

        Return id of the bucket, string of (UUID4)

        Raise ValueError if param name or new_name is not a str|unicode
        """

        if not isinstance(name, six.string_types):
            msg = 'Param name must be a str|unicode.'
            logger.exception(msg)
            raise ValueError(msg)

        if not isinstance(new_name, six.string_types):
            msg = 'Param new_name must be a str|unicode.'
            logger.exception(msg)
            raise ValueError(msg)

        return self.stubBucket.add_update(
                    opac_pb2.BucketName(name=name, new_name=new_name)).id

    def remove_bucket(self, name):
        """
        Remove bucket by name.

        Params:
            :param name: String (Mandatory)

        Raise ValueError if param name is not a str|unicode
        """

        if not isinstance(name, six.string_types):
            raise ValueError('Param "name" must be a str|unicode.')

        if self.stubBucket.exists_bucket(opac_pb2.BucketName(name=name)):
            return self.stubBucket.remove_bucket(opac_pb2.BucketName(name=name))

    def get_assets(self, name):
        """
        Return a list of asset by bucket.

        Params:
            :param name: String (Mandatory)

        Raise ValueError if param name is not a str|unicode
        """

        result = []

        if not isinstance(name, six.string_types):
            msg = 'Param name must be a str|unicode.'
            logger.exception(msg)
            raise ValueError(msg)

        assets = self.stubBucket.get_assets(opac_pb2.BucketName(name=name)).assets

        for asset in assets:
            result.append({'file': asset.file,
                           'filename': asset.filename,
                           'type': asset.type,
                           'metadata': asset.metadata,
                           'uuid': asset.uuid,
                           'bucket': asset.bucket,
                           'checksum': asset.checksum})

        return result
