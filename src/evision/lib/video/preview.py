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

import cv2

from evision.lib.entity import ImageFrame, Vertex
from evision.lib.util import DrawUtil
from evision.lib.video import (BaseImageSource, ImageSourceType, ImageSourceWrapper, VideoCaptureSource)


class ImageSourcePreview(Thread):
    def __init__(self, source: [BaseImageSource, ImageSourceWrapper]):
        Thread.__init__(self)
        self.source = source

        _type_source = type(source)
        if _type_source == ImageSourceWrapper:
            self.process = self._process_source_wrapper
        else:
            self.process = lambda x: x

    def _process_source_wrapper(self, image_frame: ImageFrame):
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
                continue
            cv2.imshow(self.source.name, frame)

            if cv2.waitKey(200) & 0xFF == ord('q'):
                cv2.destroyWindow(self.source.name)
                break
        print('Finished preview')


if __name__ == '__main__':
    # video_file = 'D:/test.mp4'
    # source = VideoCaptureImageSource(video_file, ImageSourceType.VIDEO_FILE,
    #                                  fps=24, debug=True)
    # source.daemon = True
    # source.start()
    # preview = ImageSourcePreview(source)
    # preview.run()
    # source.stop()

    from evision.lib.video import ImageSourceWrapperConfig

    source = 'rtsp://admin:1111aaaa@192.100.1.189:554/h264/ch1/main/av_stream'
    source_type = ImageSourceType.IP_CAMERA

    video_source = VideoCaptureSource(source=source, type=source_type,
                                      width=960, height=480, fps=5)
    wrapper_config = ImageSourceWrapperConfig(
        width=960, height=540,
        zone_start_x=30, zone_start_y=20, zone_width=900, zone_height=500)
    wrapper = ImageSourceWrapper(video_source, wrapper_config)

    video_source.daemon = True
    video_source.start()
    preview = ImageSourcePreview(wrapper)
    preview.run()
    video_source.stop()
