#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2019 eVision.ai Inc. All Rights Reserved.
#
# @author: Chen Shijiang(chenshijiang@evision.ai)
# @date: 2019-10-12 15:56
# @version: 1.0
#
import queue
import time
from threading import Thread

import cv2

from evision.lib.constant import VideoSourceType
from evision.lib.log import LogHandlers, logutil
from ._video_source import BaseVideoSource, VideoSourceUtil

logger = logutil.get_logger(LogHandlers.SERVICE_DEFAULT)


class VideoCaptureSource(BaseVideoSource):
    """VideoCapture类型的视频源封装"""
    __camera: cv2.VideoCapture

    def work(self):
        camera_frame = self.read_frame()
        if camera_frame is None:
            logger.info('Read no frame, waiting for {:.3f}s', self.frame_interval)
            time.sleep(self.frame_interval)
            return

        try:
            if not self._frame_queue.empty():
                self._frame_queue.get_nowait()
        except queue.Empty:
            pass
        self._frame_queue.put_nowait(camera_frame)

    def _init(self):
        """创建VideoCapture对象"""
        __camera = self.validate_camera_source(self.source, self.type,
                                               release=False)

        if __camera is None or not __camera.isOpened():
            raise Exception('摄像头无法连接，请检查')

        camera_frame_width = __camera.get(cv2.CAP_PROP_FRAME_WIDTH)
        camera_frame_height = __camera.get(cv2.CAP_PROP_FRAME_HEIGHT)
        camera_fps = __camera.get(cv2.CAP_PROP_FPS)
        logger.info('Camera connected, width={}, height={}, frame_rate={}',
                    camera_frame_width, camera_frame_height, camera_fps)
        self.original_frame_width = camera_frame_width
        self.original_frame_height = camera_frame_height
        self.original_fps = camera_fps

        # set properties according to camera type
        if self.type and VideoSourceType.USB_CAMERA.equals(self.type):
            __camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_width)
            __camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_height)
            __camera.set(cv2.CAP_PROP_FPS, self.fps)
            self.zoom_ratio = 1
        else:
            self.zoom_ratio = float(self.frame_width) / camera_frame_width

        return __camera

    def update_zoom_ratio(self):
        if self._camera and self.type and VideoSourceType.USB_CAMERA.equals(self.type):
            self._camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_width)
            self._camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_height)
            self._camera.set(cv2.CAP_PROP_FPS, self.fps)
            self.zoom_ratio = 1
        else:
            super().update_zoom_ratio()

    @staticmethod
    def validate_camera_source(camera_source,
                               camera_type=VideoSourceType.IP_CAMERA,
                               release=True):
        """验证VideoCapture对象是否有效"""
        camera_source, camera_type = VideoSourceUtil.parse_video_source(
            camera_source, camera_type)
        __camera = cv2.VideoCapture(camera_source)
        if not __camera.isOpened():
            logger.warning('Failed connecting to camera=[{}], type={}',
                           camera_source, camera_type)
            return None

        ret, frame = __camera.read()

        if not ret:
            logger.warning('Camera[{}, type={}] opened but failed getting frame',
                           camera_source, camera_type)
            return None

        if release:
            __camera.release()
            return frame

        return __camera

    def reload_source(self):
        self.reset_failure_count()
        with self._lock:
            try:
                source_ = cv2.VideoCapture(self.source)
                if source_ is None or not source_.isOpened():
                    raise Exception('Failed initialized video source={}'.format(
                        self.source))
                self._camera.release()
                self._camera = source_
            except Exception as e:
                logger.error('[{}] Failed reloading camera={}: {}',
                             self.id, self.source, e)
        logger.info('Reload video source={}', self.source)


class VideoCapturePreview(Thread):
    """视频源预览,需要图形界面支持"""

    def __init__(self, camera):
        Thread.__init__(self)
        self.camera = camera

    def run(self):
        if self.camera.zone is not None:
            text_org = (self.camera.zone.start_x + 4, self.camera.zone.end_y - 4)
        else:
            text_org = None
        while True:
            frame = self.camera.get()
            if frame is None:
                continue
            if text_org:
                cv2.putText(frame, 'Detection Zone',
                            org=text_org,
                            fontFace=cv2.FONT_HERSHEY_SIMPLEX,
                            fontScale=0.5, color=(0, 255, 0), lineType=2)
                cv2.rectangle(frame,
                              self.camera.zone.start_point,
                              self.camera.zone.end_point,
                              (0, 255, 0), 2)
            cv2.imshow(self.camera.alias, frame)

            if cv2.waitKey(200) & 0xFF == ord('q'):
                cv2.destroyWindow(self.camera.alias)
                break
