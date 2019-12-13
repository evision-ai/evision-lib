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
import datetime

import cv2

from evision.lib.entity import ImageFrame, Vertex
from evision.lib.util import DrawUtil
from evision.argus.video import BaseImageSource, ImageSourceWrapper
from evision.argus.video import ImageSourceReader

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
        if not image_frame:
            return None
        if image_frame.frame is None:
            byte_data = self.source._frame_queue.client.get(image_frame.frame_id)
            import cv2, numpy as np
            frame = cv2.imdecode(np.frombuffer(byte_data, dtype=np.uint8), cv2.IMREAD_COLOR)
            image_frame.frame = frame
        frame = image_frame.resized_frame
        DrawUtil.put_text(frame, 'Resized frame shape: {}'.format(image_frame.resized_size),
                          (10, 10))
        DrawUtil.put_text(frame, 'Frame ID: {}'.format(image_frame.frame_id),
                          (10, 100))
        if self.source.zone:
            text_org = Vertex(x=self.source.zone.start_x + 4, y=self.source.zone.end_y - 4)
            DrawUtil.put_text(frame, 'Detection Zone', text_org.to_tuple())
            DrawUtil.draw_zone(frame, self.source.zone)
        return frame

    def run(self):
        while True:
            frame = self.source.provide()
            if frame is None:
                time.sleep(0.02)
                continue
            print(datetime.datetime.now().time(), frame.frame_id)
            frame = self.process(frame)
            if frame is None:
                time.sleep(0.02)
                continue
            cv2.imshow(self.source.name, frame)

            if cv2.waitKey(200) & 0xFF == ord('q'):
                break
        cv2.destroyWindow(self.source.name)
