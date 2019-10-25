# -*- coding: utf-8 -*-
#
# Copyright 2019 eVision.ai Inc. All Rights Reserved.
#
# @author: Chen Shijiang (chenshijiang@evision.ai)
# @date: 2019-10-18 20:21
# @version: 1.0
#
import queue
from queue import Queue
from threading import RLock

import time

from evision.lib.constant import Keys
from evision.lib.entity import Zone
from evision.lib.log import logutil
from evision.lib.mixin import FailureCountMixin, SaveAndLoadConfigMixin
from evision.lib.parallel import ThreadWrapper
from evision.lib.util import CacheUtil
from evision.lib.video import ImageSourceType, ImageSourceUtil

logger = logutil.get_logger()


class BaseImageSource(ThreadWrapper, FailureCountMixin, SaveAndLoadConfigMixin):
    _MAX_FAIL_TIMES = 100

    def __init__(self, source: [str, int] = None,
                 source_type: [ImageSourceType, int] = None,
                 source_id: str = None,
                 width: int = None, height: int = None, fps: int = 5,
                 frame_queue_size: int = 1,
                 name: str = None, description: str = None, **kwargs):
        FailureCountMixin.__init__(self)
        SaveAndLoadConfigMixin.__init__(self)

        self.__image_source_inited = False
        self._lock = RLock()

        # 需要在初始化图像源信息时更新
        self.width, self.height = None, None
        self.frame_size = width, height

        # 图像源 FPS
        self.original_fps = None
        self._fps, self._frame_interval = None, None
        self.fps = fps

        # 图像源地址及类型
        self.source_config, self.source_type = \
            ImageSourceUtil.parse_source_config(source, source_type)
        # 图像源，如 VideoCapture、File、HttpRequest
        self.source = None

        ThreadWrapper.__init__(self, exclusive_init_lock=self._lock, name=name,
                               **kwargs)

        self._frame_queue = Queue(frame_queue_size)

        # 图像源配置信息
        self.source_id = source_id if source_id else CacheUtil.random_id()
        self.description = description
        self.debug = True if kwargs and kwargs.get('debug') else False

        logger.info('{}[{}] inited, source={}, type={}, frame size={}, fps={}, '
                    'name={}, description={}',
                    self.__class__.__name__, self.source_id,
                    self.source_config, self.source_type,
                    self.frame_size, self.fps,
                    self.name, self.description)
        self.__image_source_inited = True

    def provide(self):
        """图像源向外提供单帧图像"""
        try:
            if self._frame_queue.empty():
                return None
            return self._frame_queue.get()
        except queue.Empty:
            logger.warn('Failed getting image frame with empty queue')
        except Exception as e:
            logger.exception('Failed getting image frame: {}', e)
            return None

    get = provide

    def process(self):
        """图像源工作进程"""
        image_frame = self.read_frame()
        if image_frame is None:
            if self.frame_interval:
                logger.debug('[{}] Read no frame, waiting for {:.3f}s',
                             self.name, self.frame_interval)
                time.sleep(self.frame_interval)

        try:
            if self._frame_queue.full():
                self._frame_queue.get_nowait()
            self._frame_queue.put_nowait(image_frame)
        except queue.Empty:
            pass
        except queue.Full:
            pass

    @staticmethod
    def validate_source(source_config, source_type, release=True):
        """验证视频源是否有效
        对应参数： source_config、source_type
        :param release 图像源校验完成后是否释放资源
        :return 校验通过的图像源
        """
        raise NotImplementedError

    def read_frame(self):
        """
        :return: 图像帧
        """
        raise NotImplementedError

    def reload_source(self):
        """重载视频源"""
        pass

    @property
    def frame_size(self):
        """图像源尺寸
        :return: tuple of width and height
        """
        return self.width, self.height

    @frame_size.setter
    def frame_size(self, value):
        assert value and hasattr(value, '__len__') and len(value) == 2
        width, height = value
        if width == self.width and height == self.height:
            return
        width, height = ImageSourceUtil.check_frame_shape(*value)
        self.width, self.height = width, height

    @property
    def fps(self):
        return self._fps

    @property
    def frame_interval(self):
        return self._frame_interval

    @fps.setter
    def fps(self, fps: [int, None] = None):
        """更新图像源帧率及帧间隔"""
        # 图像源帧率
        if not fps:
            return
        if self._fps and self._fps == fps:
            return
        if not fps and fps < 1:
            raise ValueError('Invalid FPS setting')
        self._fps = fps
        self._frame_interval = float(1) / self._fps
        if self.__image_source_inited:
            logger.info('[{}] Set fps={}, frame interval={}',
                        self.alias, self.fps, self.frame_interval)

    @property
    def alias(self):
        return self.name if self.name else str(self.source_config)

    @property
    def config_section(self):
        return f'image_source_{self.source_id}'

    @property
    def info(self):
        return {
            Keys.ID: self.source_id,
            Keys.SOURCE: self.source_config,
            Keys.TYPE: self.source_type.value,
            Keys.NAME: self.name,
            Keys.DESCRIPTION: self.description
        }

    @property
    def type_and_source(self):
        if self.source_config is None or self.source_type is None:
            raise ValueError('Invalid video source={} or type={}'.format(
                self.source_config, self.source_type))
        return '{}-{}'.format(self.source_type.value, self.source_config)

    def set_name_description(self, name, description):
        if self.name == name and self.description == description:
            return
        if self.name != name:
            self.name = name
        self.description = description
        if self.__image_source_inited:
            logger.info('[{}} Set name={}, description={}',
                        self.alias, self.name, self.description)

    def random_frame_id(self):
        """ 生成随机图像帧ID"""
        return '{}-{:d}'.format(self.name, int(time.time()))

    def get_config(self):
        if not self.__image_source_inited:
            return None, {}
        _properties = self.get_properties()
        if _properties is None:
            _properties = {}
        _properties.update({'id': self.source_id})
        return self.config_section, _properties

    def get_properties(self):
        _source_type = self.source_type.value \
            if isinstance(self.source_type, ImageSourceType) \
            else self.source_type

        return {
            Keys.SOURCE: self.source_config,
            Keys.TYPE: _source_type,
            Keys.WIDTH: self.width,
            Keys.HEIGHT: self.height,
            Keys.FPS: self.fps,
            Keys.NAME: self.name,
            Keys.DESCRIPTION: self.description,
        }


class ZoomImageProvider(BaseImageSource):
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
        super().__init__(source=source, source_type=type, source_id=id,
                         width=width, height=height, fps=fps,
                         name=name, description=description,
                         frame_queue_size=frame_queue_size, **kwargs)

        self._keep_running = True
        self.__inited = False

        # 需要在初始化视频源信息时更新
        self.zoom_ratio = None
        self.zoomed_width = None
        self.zoomed_height = None
        self.set_zoomed_size(width, height)

        self.zone = None
        self.set_zone_info(zone_start_x, zone_start_y, zone_width, zone_height)

        # 初始化视频源
        logger.info('{}[{}] inited, source={}, type={}, '
                    'frame size={}, fps={}, name={}, description={}, zone={}',
                    self.__class__.__name__, self.source_id,
                    self.source_config, self.source_type,
                    self.frame_size, self.fps,
                    self.name, self.description, self.zone)

    def read_frame(self):
        raise NotImplementedError()

    def set_zoomed_size(self, width, height):
        if self.zoomed_width == width and self.zoomed_height == height:
            return
        """设置视频源画面尺寸"""
        width, height = ImageSourceUtil.check_frame_shape(width, height)
        # 画面尺寸
        self.zoomed_width = width
        self.zoomed_height = height
        # 缩放比
        self.update_zoom_ratio()
        logger.info('[{}] Set zoomed frame size={}, zoom ratio={}',
                    self.alias, self.zoomed_size, self.zoom_ratio)

    def update_zoom_ratio(self):
        """更新视频源图像帧的缩放比"""
        if self.width:
            self.zoom_ratio = float(self.zoomed_width) / self.width
            return
        if self.height:
            self.zoom_ratio = float(self.zoomed_height) / self.height
            return

    def on_start(self):
        if self.zoomed_width:
            self.zoom_ratio = float(self.zoomed_width) / self.width
            self.zoomed_height = int(self.height * self.zoom_ratio)
        elif self.zoomed_height:
            self.zoom_ratio = float(self.zoomed_height) / self.height
            self.zoomed_width = int(self.width * self.zoom_ratio)
        else:
            self.zoom_ratio = 1
            self.zoomed_width = self.width
            self.zoomed_height = self.height

    @property
    def zoomed_size(self):
        return self.zoomed_width, self.zoomed_height

    def set_zone_info(self, zone_start_x, zone_start_y, zone_width, zone_height):
        """更新视频源检测区域"""
        self.zone = self.__check_detection_zone(
            zone_start_x, zone_start_y, zone_width, zone_height)
        if self.__inited:
            logger.info('[{}] Set detection zone={}', self.alias, self.zone)

    def get_properties(self):
        _properties = super().get_properties()
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

    def __check_detection_zone(self, start_x, start_y, width, height):
        if start_x is None or start_y is None or width is None or height is None:
            return None
        zone = Zone(start_x, start_y, width=width, height=height)
        zone.validate_shape(self.zoomed_width, self.zoomed_height)
        return zone

    def __del__(self):
        self.stop()
