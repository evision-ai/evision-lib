# -*- coding: utf-8 -*-
# @author: Chen Shijiang (chenshijiang@evision.ai)
# @version: 1.0
#

from fields import Fields

__all__ = [
    'Keys', 'ParamKey', 'Fields', 'Error', 'Status', 'Message',
    'Suffix', 'DeploymentType'
]


# Request Keys
class Keys(object):
    # APP related
    AUTO_STARTING = 'auto_starting'

    # General
    CODE = 'code'
    MESSAGE = 'msg'
    DATA = 'data'
    FORCE = 'force'
    FILE = 'file'
    SOURCE = 'source'
    TYPE = 'type'

    ID = 'id'
    NAME = 'name'
    PROPERTIES = 'properties'
    URL = 'url'

    WIDTH = 'width'
    HEIGHT = 'height'
    FPS = 'fps'
    DESCRIPTION = 'description'

    # Camera
    CAMERA_ID = 'camera_id'

    CAMERA_ZONE_START_X = 'zone_start_x'
    CAMERA_ZONE_START_Y = 'zone_start_y'
    CAMERA_ZONE_WIDTH = 'zone_width'
    CAMERA_ZONE_HEIGHT = 'zone_height'


class _Error(Fields.code.message):
    pass


class Error(object):
    """封装的API调用失败信息"""

    @staticmethod
    def check(obj):
        return obj is not None and isinstance(obj, _Error)

    # -10x coordinator related error
    COORDINATOR_NOT_INITIALIZED = _Error(-101, '服务未初始化')
    """
    @apiDefine NotInitializedError
    @apiError (ValueError) {json} NotInitializedError 服务未初始化
    @apiErrorExample {json} NotInitializedError-Response:
        HTTP/1.1 200
        {
            "status": -101,
            "message": "服务未初始化"
        }
    """

    APP_INFO_NOT_PROVIDED = _Error(-606, '未提供APP ID或APP SECRET')
    """
    @apiDefine AppInfoNotProvidedError
    @apiError (ValueError) {json} AppInfoNotProvidedError 未提供APP ID或APP SECRET
    @apiErrorExample {json} AppInfoNotProvidedError-Response:
        HTTP/1.1 200
        {
            "status": -606,
            "message": "未提供APP ID或APP SECRET"
        }
    """

    # -70x process related errors
    FILE_NOT_UPLOADED = _Error(-701, '未上传文件')
    """
    @apiDefine FileNotProvidedError
    @apiError (ValueError) {json} FileNotProvidedError 未上传文件
    @apiErrorExample {json} FileNotProvidedError-Response:
        HTTP/1.1 200
        {
            "status": -701,
            "message": "未上传文件"
        }
    """

    INVALID_IMAGE_SOURCE_TYPE = _Error(-702, '不支持的图像上传类型')
    """
    @apiDefine InvalidImageSourceType
    @apiError (ValueError) {json} InvalidImageSourceType 不支持的图像上传类型
    @apiErrorExample {json} InvalidImageSourceType-Response:
        HTTP/1.1 200
        {
            "status": -702,
            "message": "不支持的图像上传类型"
        }
    """

    FAILED_LOADING_IMAGE = _Error(-703, '读取图像失败')
    """
    @apiDefine FailedLoadingImage
    @apiError (Failed) {json} FailedLoadingImage 读取图像失败
    @apiErrorExample {json} FailedLoadingImage-Response:
        HTTP/1.1 200
        {
            "status": -703,
            "message": "读取图像失败"
        }
    """

    @staticmethod
    def create(code, message):
        return _Error(code, message)


class ParamKey(Keys):
    pass


# Database fields
class Fields(object):
    pass


# Program status
class Status(object):
    OK = 1
    FAILED = 0
    ERROR = -1


# Program message
class Message(object):
    OK = 'success'
    FAILED = 'failed'
    ERROR = 'error'


class Suffix(object):
    TXT = 'txt'
    PKL = 'pkl'
    PNG = 'png'
    JPG = 'jpg'


class DeploymentType:
    def __init__(self):
        pass

    DEV = 'dev'
    RELEASE_CANDIDATE = 'rc'
    PROD = 'prod'
    dict = {
        DEV: 1,
        PROD: 2,
    }
