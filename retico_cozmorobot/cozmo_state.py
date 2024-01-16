import functools
import threading
import time
import asyncio
import sys

# retico
import retico_core
from retico_core.robot import RobotStateIU

# cozmo
import sys
import os
sys.path.append(os.environ['COZMO'])
import cozmo

from collections import deque
import numpy as np
import threading



class CozmoStateModule(retico_core.AbstractProducingModule):
    '''
    use_viewer=True must be set in cozmo.run_program
    '''

    @staticmethod
    def name():
        return "Cozmo State Tracking Module"

    @staticmethod
    def description():
        return "A module that tracks the state of Cozmo, including camera frames."

    @staticmethod
    def output_iu():
        return RobotStateIU

    def __init__(self, robot, **kwargs):
        super().__init__(**kwargs)
        self.robot = robot
        self.num_states = 0
        self.state_queue = deque(maxlen=3)
        
    def run_state(self):

        while True:
            if len(self.state_queue) == 0:
                time.sleep(0.1)
                continue
            state = self.state_queue.popleft()
            output_iu = self.create_iu(None)
            output_iu.set_state(state)
            self.num_states += 1
            # print('number of states so far', self.num_states)
            self.append(output_iu)

    def process_update(self, update_message):

        return None

    
    def setup(self):

        self.num_frames = 0

        t = threading.Thread(target=self.run_state)
        t.start()

        def state_change_update(evt, obj=None, tap_count=None, **kwargs):
            if np.round(time.time() % 2, 1) < 0.1: # Get only about half of the frames per ten seconds
                robot = kwargs['robot']
                state = robot.get_robot_state_dict()
                state.update({"left_wheel_speed":str(robot.left_wheel_speed)})
                state.update({"right_wheel_speed":str(robot.right_wheel_speed)})
                state.update({"battery_voltage":str(robot.battery_voltage)})
                state.update({"robot_id":str(robot.robot_id)})
                state.update({"time":str(time.time())})
                state.update({'face_count': str(robot.world.visible_face_count())})
                self.state_queue.append(state)

        self.robot.world.add_event_handler(cozmo.robot.EvtRobotStateUpdated, state_change_update)





