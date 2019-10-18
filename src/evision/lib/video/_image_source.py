#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2019 eVision.ai Inc. All Rights Reserved.
#
# @author: Chen Shijiang(chenshijiang@evision.ai)
# @date: 2019-10-12 15:45
# @version: 1.0
#
import time
from queue import Queue
from threading import RLock

from evision.lib.constant import Keys
from evision.lib.entity import Zone
from evision.lib.log import LogHandlers, logutil
from evision.lib.mixin import FailureCountMixin, SaveAndLoadConfigMixin
from evision.lib.parallel import ThreadWrapper
from evision.lib.util import CacheUtil
from evision.lib.video.base import ImageSourceType, ImageSourceUtil

logger = logutil.get_logger(LogHandlers.DEFAULT)


class BaseImageSource(ThreadWrapper, FailureCountMixin, SaveAndLoadConfigMixin):
    _MAX_FAIL_TIMES = 100

    def __init__(self, source: [str, int] = None,
                 source_type: [ImageSourceType, int] = None,
                 width: int = None, height: int = None, fps: int = 5,
                 **kwargs):
        self._lock = RLock()
        super().__init__(exclusive_init_lock=self._lock, **kwargs)
        # 视频源地址及类型
        self.source_config, self.source_type = \
            ImageSourceUtil.parse_video_source(source, source_type)
        # 视频源，如 VideoCapture、File、HttpRequest
        self.source = None
        self.fps = None

        # 需要在初始化视频源信息时更新
        self.source_width = None
        self.source_height = None

    def init(self):
        self._set_frame_size(self.width, self.height)
        pass

    @property
    def frame_size(self):
        return (self.width, self.height)

    def _set_frame_size(self, width, height):
        """设置视频源画面尺寸"""
        if self.width == width and self.height == height:
            return
        width, height = ImageSourceUtil.check_frame_shape(width, height)
        # 画面尺寸
        self.width = width
        self.height = height
        # 缩放比

    def _update_zoom_ratio(self):
        """更新视频源图像帧的缩放比"""
        if self.original_frame_width:
            self.zoom_ratio = float(self.frame_width) / self.original_frame_width
            return
        if self.original_frame_height:
            self.zoom_ratio = float(self.frame_height) / self.original_frame_height
            return

    def process(self):
        pass


class BaseImageProvider(BaseImageSource):
    """ Video Source Base

    Denoting a video source, which can produce image frames
    """
    __DEFAULT_FPS = 5

    _should_crop_zone: bool
    _should_resize_frame: bool

    def __init__(self, source: [str, int] = None,
                 type: [ImageSourceType, int] = None,
                 width: int = None, height: int = None, fps: int = 5,
                 name: str = None, description: str = None,
                 zone_start_x: int = None, zone_start_y: int = None,
                 zone_width: int = None, zone_height: int = None,
                 frame_queue_size: int = 1, id: str = None, **kwargs):
        """视频源初始化

        :param source: 视频源地址
        :param type: 视频源类型
        :param width: 视频源宽度
        :param height: 视频源高度
        :param fps: 视频源帧率
        :param name: 视频源名称
        :param description: 视频源描述
        :param zone_start_x: 指定视频裁剪区域横向开始位置
        :param zone_start_y: 指定视频裁剪区域纵向开始位置
        :param zone_width: 指定视频裁剪区域宽度
        :param zone_height: 指定视频裁剪区域高度
        :param frame_queue_size: 帧队列长度
        :param id: 视频源 ID
        """
        super().__init__(source=source, source_type=type)

        # 视频源地址及类型
        self.__camera = None
        self._frame_queue = Queue(frame_queue_size)

        self._keep_running = True
        self._lock = RLock()
        self.__inited = False

        # 需要在初始化视频源信息时更新
        self.source_width = None
        self.source_height = None
        self.zoom_ratio = None
        # 视频源尺寸信息
        self.width = None
        self.height = None
        self._set_frame_size(width, height)

        self.original_fps = None
        self.fps = None
        self.frame_interval = None
        self.set_frame_rate(fps)

        self.zone = None
        self.set_zone_info(zone_start_x, zone_start_y, zone_width, zone_height)

        # 视频源名称等信息，覆盖 Thread 属性
        self.id = id if id else CacheUtil.random_id()
        self.name = name
        self.description = description

        self.kwargs = kwargs
        self.debug = True if kwargs and kwargs.get('debug') else False
        # 初始化视频源
        logger.info('{}[{}] inited, source={}, type={}, '
                    'frame size={}, fps={}, name={}, description={}, zone={}',
                    self.__class__.__name__, self.id,
                    self.source, self.source_type,
                    self.frame_size, self.fps,
                    self.name, self.description, self.zone)

    def set_frame_rate(self, fps):
        """更新视频源帧率及帧间隔"""
        # 视频源帧率
        if self.fps and self.fps == fps:
            return
        if not fps or fps < 1:
            raise ValueError('Invalid FPS setting')
        self.fps = fps
        self.frame_interval = float(1) / self.fps
        if self.__inited:
            logger.info('[{}] Set fps={}, frame interval={}',
                        self.alias, self.fps, self.frame_interval)

    def set_zone_info(self, zone_start_x, zone_start_y, zone_width, zone_height):
        """更新视频源检测区域"""
        self.zone = self.__check_detection_zone(
            zone_start_x, zone_start_y, zone_width, zone_height)
        if self.__inited:
            logger.info('[{}] Set detection zone={}', self.alias, self.zone)

    def set_name_description(self, name, description):
        if self.name == name and self.description == description:
            return
        if self.name != name:
            self.name = name
        self.description = description
        if self.__inited:
            logger.info('[{}} Set name={}, description={}',
                        self.alias, self.name, self.description)

    def get_config(self):
        if not self.__inited:
            return None, {}
        _properties = self.get_properties()
        if _properties is None:
            _properties = {}
        _properties.update({'id': self.id})
        return self.config_section, _properties

    def get_properties(self):
        # TODO 更新描述方式
        _camera_type = self.type.value \
            if isinstance(self.type, ImageSourceType) \
            else self.type

        _properties = {
            Keys.SOURCE: self.source,
            Keys.TYPE: _camera_type,
            Keys.WIDTH: self.width,
            Keys.HEIGHT: self.height,
            Keys.FPS: self.fps,
            Keys.NAME: self.name,
            Keys.DESCRIPTION: self.description,
        }
        if self.zone is not None:
            assert isinstance(self.zone, Zone)
            _properties.update({
                Keys.CAMERA_ZONE_START_X: self.zone.start_x,
                Keys.CAMERA_ZONE_START_Y: self.zone.start_y,
                Keys.CAMERA_ZONE_WIDTH: self.zone.width,
                Keys.CAMERA_ZONE_HEIGHT: self.zone.height
            })
        else:
            _properties.update({
                Keys.CAMERA_ZONE_START_X: None,
                Keys.CAMERA_ZONE_START_Y: None,
                Keys.CAMERA_ZONE_WIDTH: None,
                Keys.CAMERA_ZONE_HEIGHT: None
            })
        return _properties

    @property
    def config_section(self):
        return 'video_{}'.format(self.id)

    @property
    def alias(self):
        return self.name if self.name else str(self.source)

    @property
    def info(self):
        return {
            Keys.ID: self.id,
            Keys.SOURCE: self.source,
            Keys.TYPE: self.type.value,
            Keys.NAME: self.name,
            Keys.DESCRIPTION: self.description
        }

    @property
    def type_and_source(self):
        if self.source is None or self.type is None:
            raise ValueError('Invalid video source={} or type={}'.format(
                self.source, self.type))
        return '{}-{}'.format(self.type.value, self.source)

    def __check_detection_zone(self, start_x, start_y, width, height):
        if start_x is None or start_y is None or width is None or height is None:
            return None
        zone = Zone(start_x, start_y, width=width, height=height)
        zone.validate_shape(self.width, self.height)
        return zone

    def random_frame_id(self):
        """ 生成随机图像帧ID"""
        return '{}-{:d}'.format(self.name, int(time.time()))

    def work(self):
        """实际工作方法"""
        pass

    def start_working(self):
        """将服务作为后台服务启动"""
        if self.is_alive():
            logger.info('Camera[{}] already started', self.alias)
            return
        logger.info('Starting camera[{}]...', self.alias)
        self.daemon = True
        self.start()
        logger.info('Camera[{}] started.', self.alias)

    def get(self):
        """获取队列中图像帧"""
        try:
            if self._frame_queue.empty():
                return None
            return self._frame_queue.get()
        except Exception as e:
            logger.exception('Failed getting current frame zone: {}', e)
            return None

    def reload_source(self):
        """重载视频源"""
        pass

    @staticmethod
    def validate_camera_source(
        camera_source, camera_type=ImageSourceType.IP_CAMERA, release=True):
        """验证视频源是否有效"""
        pass

    def stop_reading(self, release=True):
        self._keep_running = False

    def __del__(self):
        self.stop_reading()
