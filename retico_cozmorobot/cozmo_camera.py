import functools
import threading
import time
import asyncio
import sys

# retico
import retico_core
from retico_vision.vision import ImageIU

# cozmo
import sys
import os
sys.path.append(os.environ['COZMO'])
import cozmo
# import cv2
import time

from collections import deque
import numpy as np
from PIL import Image



class CozmoCameraModule(retico_core.AbstractProducingModule):
    '''
    use_viewer=True must be set in cozmo.run_program
    '''

    @staticmethod
    def name():
        return "Cozmo Camera Tracking Module"

    @staticmethod
    def description():
        return "A module that tracks cozmo camera frames."

    @staticmethod
    def output_iu():
        return ImageIU

    def __init__(self, robot, exposure=0.2, gain=0.1, **kwargs):
        # for exp room:exposure=0.05, gain=0.05
        super().__init__(**kwargs)
        self.robot = robot
        self.robot.move_lift(5)
        self.exposure_amount = exposure
        self.gain_amount = gain
        self.img_queue = deque(maxlen=1)
        
    def process_update(self, blank):
        if len(self.img_queue) > 0:
            img = self.img_queue.popleft()
            # img = np.array(img)
            # print('using image')
            output_iu = self.create_iu(None)
            output_iu.set_image(img, 1, 1)
            self.append(retico_core.UpdateMessage.from_iu(output_iu, retico_core.UpdateType.ADD))
        else:
            # this hack keeps the camera running semi-smoothly, otherwise it gets clogged
            # self.robot.camera.image_stream_enabled = False
            time.sleep(0.9)
            self.configure_camera()
    

    def configure_camera(self):
        self.robot.camera.image_stream_enabled = True
        self.robot.camera.color_image_enabled = True
        self.robot.camera.enable_auto_exposure = False # False means we can adjust manually
        # Lerp exposure between min and max times
        min_exposure = self.robot.camera.config.min_exposure_time_ms
        max_exposure = self.robot.camera.config.max_exposure_time_ms
        exposure_time = (1 - self.exposure_amount) * min_exposure + self.exposure_amount * max_exposure
        # Lerp gain
        min_gain = self.robot.camera.config.min_gain
        max_gain = self.robot.camera.config.max_gain
        actual_gain = (1-self.gain_amount)*min_gain + self.gain_amount*max_gain
        self.robot.camera.set_manual_exposure(exposure_time,actual_gain)

    def setup(self):
        def handle_image(evt, obj=None, tap_count=None,  **kwargs):
            self.img_queue.append(evt.image)

        # print("configuring camera")
        self.configure_camera()
        # print('adding event handler')
        self.robot.world.add_event_handler(cozmo.camera.EvtNewRawCameraImage, handle_image)



