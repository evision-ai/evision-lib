# -*- coding: utf-8 -*-
#
# Copyright 2019 eVision.ai Inc. All Rights Reserved.
#
# @author: Chen Shijiang (chenshijiang@evision.ai)
# @date: 2019-10-18 19:38
# @version: 1.0
#
import time
from threading import Thread
from typing import Union

import cv2

from evision.lib.entity import ImageFrame, Vertex
from evision.lib.util import DrawUtil
from evision.lib.video import BaseImageSource, ImageSourceWrapper
from evision.lib.video.wrapper import ImageSourceReader

__all__ = [
    'ImageSourcePreview'
]


class ImageSourcePreview(Thread):
    def __init__(self, source: Union[BaseImageSource, ImageSourceReader]):
        Thread.__init__(self)
        self.source = source

        _type_source = type(source)
        if _type_source == ImageSourceReader or _type_source == ImageSourceWrapper:
            self.process = self._process_source_wrapper
        else:
            self.process = lambda x: x

    def _process_source_wrapper(self, image_frame: ImageFrame):
        if not image_frame or image_frame.frame is None:
            return None
        frame = image_frame.resized_frame
        DrawUtil.put_text(frame, 'Resized frame shape: {}'.format(image_frame.resized_size),
                          (10, 10))
        if self.source.zone:
            text_org = Vertex(self.source.zone.start_x + 4, self.source.zone.end_y - 4)
            DrawUtil.put_text(frame, 'Detection Zone', text_org.to_tuple())
            DrawUtil.draw_zone(frame, self.source.zone)
        return frame

    def run(self):
        while True:
            frame = self.source.provide()
            if frame is None:
                time.sleep(0.1)
                continue
            frame = self.process(frame)
            if frame is None:
                time.sleep(0.1)
                continue
            cv2.imshow(self.source.name, frame)

            if cv2.waitKey(200) & 0xFF == ord('q'):
                break
        cv2.destroyWindow(self.source.name)
