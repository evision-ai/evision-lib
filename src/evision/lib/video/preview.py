# -*- coding: utf-8 -*-
#
# Copyright 2019 eVision.ai Inc. All Rights Reserved.
#
# @author: Chen Shijiang (chenshijiang@evision.ai)
# @date: 2019-10-18 19:38
# @version: 1.0
#
from threading import Thread

import cv2

from evision.lib.video import BaseImageSource, ImageSourceType, VideoCaptureZoomedSource
from evision.lib.video.camera import VideoCaptureImageSource


class ImageSourcePreview(Thread):
    def __init__(self, source: BaseImageSource):
        Thread.__init__(self)
        self.source = source

    def process(self, frame):
        return frame

    def run(self):
        while True:
            frame = self.source.provide()
            frame = self.process(frame)
            if frame is None:
                continue
            cv2.imshow(self.source.name, frame)

            if cv2.waitKey(200) & 0xFF == ord('q'):
                cv2.destroyWindow(self.source.name)
                break
        print('Finished preview')


class VideoCapturePreview(ImageSourcePreview):
    """视频源预览,需要图形界面支持"""
    source: VideoCaptureZoomedSource

    def run(self):
        if hasattr(self.source, 'zone') and self.source.zone is not None:
            text_org = (self.source.zone.start_x + 4, self.source.zone.end_y - 4)
        else:
            text_org = None
        while True:
            frame = self.source.provide()
            if frame is None:
                continue
            if text_org:
                cv2.putText(frame, 'Detection Zone',
                            org=text_org,
                            fontFace=cv2.FONT_HERSHEY_SIMPLEX,
                            fontScale=0.5, color=(0, 255, 0), lineType=2)
                cv2.rectangle(frame,
                              self.source.zone.start_point,
                              self.source.zone.end_point,
                              (0, 255, 0), 2)
            cv2.imshow(self.source.alias, frame)

            if cv2.waitKey(200) & 0xFF == ord('q'):
                cv2.destroyWindow(self.source.alias)
                break


if __name__ == '__main__':
    # video_file = 'D:/test.mp4'
    # source = VideoCaptureImageSource(video_file, ImageSourceType.VIDEO_FILE,
    #                                  fps=24, debug=True)
    # source.daemon = True
    # source.start()
    # preview = ImageSourcePreview(source)
    # preview.run()
    # source.stop()
    import os

    source = os.path.expanduser('~/Downloads/test.avi')
    source_type = ImageSourceType.VIDEO_FILE

    source = 'rtsp://admin:1111aaaa@192.100.1.189:554/h264/ch1/main/av_stream'
    source_type = ImageSourceType.IP_CAMERA

    video_source = VideoCaptureImageSource(
        source=source, type=source_type,
        width=960, height=480,
        zone_width=960, zone_height=480, fps=5)
    video_source.daemon = True
    video_source.start()
    preview = VideoCapturePreview(video_source)
    preview.run()
    video_source.stop()
