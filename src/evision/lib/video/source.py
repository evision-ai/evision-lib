# -*- coding: utf-8 -*-
#
# Copyright 2019 eVision.ai Inc. All Rights Reserved.
#
# @author: Chen Shijiang (chenshijiang@evision.ai)
# @date: 2019-10-18 20:21
# @version: 1.0
#
import queue
import time
from queue import Queue
from threading import Lock, RLock, Thread
from typing import Union

import cv2
import numpy as np
from pydantic import BaseModel, Extra
from walrus import Database

from evision.lib.constant import Keys
from evision.lib.log import logutil
from evision.lib.mixin import FailureCountMixin, PropertyHandlerMixin
from evision.lib.parallel import ThreadWrapper
from evision.lib.util import CacheUtil
from evision.lib.util.redis import RedisUtil
from evision.lib.util.types import ValueAsStrIntEnum
from evision.lib.video import ImageSourceType, ImageSourceUtil

logger = logutil.get_logger()

__all__ = [
    'BaseImageSource',
    'ImageSourceConfig',
    'VideoCaptureSource',
    'VideoFileImageSource',
    'ImageSourceHandler'
]


class ImageSourceHandler(ValueAsStrIntEnum):
    video_capture = 1
    video_file = 2


class ImageSourceConfig(BaseModel):
    source_uri: Union[str, int]
    source_type: Union[ImageSourceType, int]
    handler_name: Union[ImageSourceHandler, str] = ImageSourceHandler.video_capture
    source_id: str = None
    width: int = None
    height: int = None
    fps: float = 24
    frame_queue_size: int = 24
    name: str = None
    description: str = None

    class Config:
        extra = Extra.allow
        arbitrary_types_allowed = True


class BaseImageSource(ThreadWrapper, FailureCountMixin, PropertyHandlerMixin):
    _MAX_FAIL_TIMES = 100

    # 属性配置
    required_properties = [Keys.SOURCE_URI, Keys.SOURCE_TYPE]
    optional_properties = [Keys.WIDTH, Keys.HEIGHT, Keys.FPS, Keys.NAME, Keys.DESCRIPTION]
    handler_alias = None

    @classmethod
    def construct(cls, config: ImageSourceConfig):
        handler_cls = cls.get_handler_by_name(config.handler_name) \
            if config.handler_name is not None \
            else cls
        return handler_cls(**config.dict(exclude={'handler_name', }))

    def __init__(self, source_uri: Union[str, int] = None,
                 source_type: Union[ImageSourceType, int] = None,
                 source_id: str = None,
                 width: int = None, height: int = None, fps: float = 5,
                 frame_queue_size: int = 24,
                 name: str = None, description: str = None, **kwargs):
        FailureCountMixin.__init__(self)
        PropertyHandlerMixin.__init__(self)

        self.__image_source_inited = False
        self._lock = RLock()
        self.read_lock = Lock()

        # 需要在初始化图像源信息时更新
        self.width, self.height = None, None
        self.frame_size = width, height

        # 图像源 FPS
        self._fps = None
        self.fps = fps

        # 图像源地址及类型
        self.source_uri, self.source_type = \
            ImageSourceUtil.parse_source_config(source_uri, source_type)
        # 图像源，如 VideoCapture、File、HttpRequest
        self.source = None

        ThreadWrapper.__init__(self, exclusive_init_lock=self._lock, name=name,
                               interval=self.interval, **kwargs)

        self._frame_queue = Queue(frame_queue_size)

        # 图像源配置信息
        self.source_id = source_id if source_id else CacheUtil.random_string(8)
        self.description = description
        self.debug = True if kwargs and kwargs.get('debug') else False

        logger.info('{}[{}] inited, source={}, type={}, frame size={}, fps={}, '
                    'name={}, description={}',
                    self.__class__.__name__, self.source_id,
                    self.source_uri, self.source_type,
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

    def peek(self):
        if self._frame_queue.empty():
            return None
        return self.current(block=False)

    def current(self, n_frame=1, block=True, timeout=60):
        """获取当前队列中最新的 {n_frame} 帧图像

        :param n_frame: 需要获取的帧数目
        :param block: 是否阻塞
        :param timeout: 最多等待时间
        """
        if self._frame_queue.empty():
            return None

        if not block:
            return None if self._frame_queue.qsize() < n_frame \
                else [self._frame_queue.queue[i] for i in range(n_frame)]

        try:
            must_end = time.time() + timeout
            while time.time() < must_end:
                if self._frame_queue.qsize() >= n_frame:
                    # NOTE: 可能取到少于 n_frame 帧图像，不做处理
                    return [self._frame_queue.queue[i] for i in range(n_frame)]
                time.sleep(self.interval * (n_frame - self._frame_queue.qsize()))
            return None
        except queue.Empty:
            logger.warn('Failed getting current image frame with empty queue')
            return None

    def on_start(self):
        mirror_thread = Thread(target=RedisUtil.mirror_arrays,
                               args=(self._frame_queue, self.frames_key, self.fps))
        mirror_thread.daemon = True
        mirror_thread.start()
        logger.info('Mirroring {}[{}] frames to redis queue: {}',
                    self.name, self.source_id, self.frames_key)

    def on_stop(self):
        logger.info('Removing redis mirroring key for {}[{}] : {}',
                    self.name, self.source_id, self.frames_key)
        RedisUtil.remove_key(self.frames_key)
        assert not Database().exists(self.frames_key)

    def process(self):
        """图像源工作进程"""
        image_frame = self.read_frame()
        if image_frame is None:
            self.on_empty_frame()
            return

        self.reset_failure_count()
        try:
            if self._frame_queue.full():
                self._frame_queue.get_nowait()
            self._frame_queue.put_nowait(image_frame)
        except queue.Empty:
            pass
        except queue.Full:
            pass

    def read_frame(self):
        """
        :return: 图像帧
        """
        raise NotImplementedError

    def on_empty_frame(self):
        """读取空帧时的处理方式"""
        self.accumulate_failure_count()
        self.try_restore(self._MAX_FAIL_TIMES, self.reload_source)

        if self.interval:
            logger.debug('[{}] Read no frame, waiting for {:.3f}s',
                         self.name, self.interval)
            time.sleep(self.interval)

    @staticmethod
    def validate_source(source_uri, source_type, release=True):
        """验证视频源是否有效
        对应参数： source_uri、source_type
        :param source_uri 图像源配置地址
        :param source_type 图像源类型
        :param release 图像源校验完成后是否释放资源
        :return 校验通过的图像源
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
        logger.info('Setting frame size to {}', value)
        assert value and hasattr(value, '__len__') and len(value) == 2
        width, height = value
        if width == self.width and height == self.height:
            return
        width, height = ImageSourceUtil.check_frame_shape(*value)
        self.width, self.height = width, height

    @property
    def frames_key(self):
        return f'frames:{self.source_id}'

    @property
    def frame_shape(self):
        w, h = self.frame_size
        return h, w, 3

    @property
    def fps(self):
        return self._fps

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
        self.interval = float(1) / self._fps
        if self.__image_source_inited:
            logger.info('[{}] Set fps={}, frame interval={}',
                        self.alias, self.fps, self.interval)

    @property
    def alias(self):
        return self.name if self.name else str(self.source_uri)

    @property
    def config_section(self):
        return f'image_source_{self.source_id}'

    @property
    def info(self):
        return {
            Keys.ID: self.source_id,
            Keys.SOURCE_URI: self.source_uri,
            Keys.SOURCE_TYPE: self.source_type.value,
            Keys.NAME: self.name,
            Keys.DESCRIPTION: self.description
        }

    @property
    def uri_and_type(self):
        if self.source_uri is None or self.source_type is None:
            raise ValueError('Invalid video source={} or type={}'.format(
                self.source_uri, self.source_type))
        return self.source_uri, self.source_type

    def set_name_description(self, name, description):
        if self.name == name and self.description == description:
            return
        if self.name != name:
            self.name = name
        self.description = description
        if self.__image_source_inited:
            logger.info('[{}} Set name={}, description={}',
                        self.alias, self.name, self.description)

    def get_config(self):
        if not self.__image_source_inited:
            return None, {}
        _properties = self.properties
        if _properties is None:
            _properties = {}
        _properties.update({'id': self.source_id})
        return self.config_section, _properties


class VideoCaptureSource(BaseImageSource):
    """VideoCapture类型的视频源封装
    支持视频源类型：
    - 网络摄像头：ImageSourceType.IP_CAMERA
    - USB 摄像头：ImageSourceType.USB_CAMERA
    - 本地视频文件：ImageSourceType.VIDEO_FILE
    """
    source: cv2.VideoCapture

    handler_alias = ImageSourceHandler.video_capture

    @staticmethod
    def validate_source(source_uri, source_type, release=True):
        source_uri, source_type = ImageSourceUtil.parse_source_config(
            source_uri, source_type)
        """验证VideoCapture对象是否有效"""
        source_ = cv2.VideoCapture(source_uri)
        if not source_.isOpened():
            logger.warning('Failed connecting to camera=[{}], type={}',
                           source_uri, source_type)
            return None

        ret, frame = source_.read()

        if not ret:
            logger.warning('Camera[{}, type={}] opened but failed getting frame',
                           source_uri, source_type)
            return None

        if release:
            source_.release()
            return frame

        return source_

    def on_start(self):
        """创建VideoCapture对象"""
        source_ = self.validate_source(self.source_uri, self.source_type,
                                       release=False)
        if source_ is None or not source_.isOpened():
            raise Exception('Cannot connecting to image source, please check you configuration')

        self.source = source_
        self.frame_size = (self.source.get(cv2.CAP_PROP_FRAME_WIDTH),
                           self.source.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.fps = self.source.get(cv2.CAP_PROP_FPS)
        logger.info('Connected to image source[{}], type={}，size={}, fps={}',
                    self.source_uri, self.source_type,
                    self.frame_size, self.fps)

        super().on_start()

    def read_frame(self):
        """从视频源直接获取图像帧"""
        with self._lock:
            ret, camera_frame = self.source.read()
            if not ret or np.all(camera_frame == 0):
                return None
            return camera_frame

    def reload_source(self):
        """重新连接视频源

        USB 摄像头不允许并行连接，必须先释放现有连接
        """
        self.reset_failure_count()
        with self._lock:
            if self.source.isOpened() and ImageSourceType.USB_CAMERA == self.source_type:
                self.source.release()
            source_ = self.validate_source(
                self.source_uri, self.source_type, release=False)
            if source_ is None or not source_.isOpened():
                raise Exception('Failed initialized video source={}'.format(
                    self.source))
            if self.source.isOpened():
                self.source.release()
            self.source = source_
        logger.info('Reload video source={}', self.source)

    def on_stop(self):
        if self.source and self.source.isOpened():
            self.source.release()
            del self.source

        super().on_stop()


class VideoFileImageSource(VideoCaptureSource):
    handler_alias = ImageSourceHandler.video_file

    def __init__(self, **kwargs):
        self.endless = kwargs.pop('endless') if 'endless' in kwargs else False
        super().__init__(**kwargs)

    def on_empty_frame(self):
        logger.info('Finish reading {} with {} frames', self.source_uri, self.ticks)
        if not self.endless:
            self.stop()
        else:
            logger.debug('Reloading source={}, status={}', self.source_uri, self.is_alive())
            self.reload_source()
