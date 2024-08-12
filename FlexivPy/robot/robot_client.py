import time
import mujoco
import mujoco.viewer
import numpy as np
from scipy.spatial.transform import Rotation
import os

from cyclonedds.core import Listener, Qos, Policy
from cyclonedds.domain import DomainParticipant
from cyclonedds.topic import Topic
from cyclonedds.sub import Subscriber, DataReader
from cyclonedds.util import duration
import time

from cyclonedds.core import Qos, Policy
from cyclonedds.domain import DomainParticipant
from cyclonedds.pub import Publisher, DataWriter
from cyclonedds.topic import Topic
from cyclonedds.util import duration
from datetime import datetime


import time


from FlexivPy.robot.dds.flexiv_messages import FlexivCmd, FlexivState


class Flexiv_client:
    def __init__(self, dt=0.001, render=False, create_server=False):

        self.dt = dt
        self.domain_participant = DomainParticipant()
        self.topic_state = Topic(self.domain_participant, "FlexivState", FlexivState)
        self.topic_cmd = Topic(self.domain_participant, "FlexivCmd", FlexivCmd)
        self.publisher = Publisher(self.domain_participant)
        self.subscriber = Subscriber(self.domain_participant)
        self.writer = DataWriter(self.publisher, self.topic_cmd)
        self.reader = DataReader(self.subscriber, self.topic_state)
        self.warning_step_msg_send = False

        self.create_server = create_server
        self.server_process = None

        if self.create_server:
            import subprocess
            import time

            cmd = ["python", "FlexivPy/robot/sim/sim_robot_async.py"]
            if render:
                cmd += ["--render"]
            self.server_process = subprocess.Popen(cmd, env=os.environ.copy())

            time.sleep(0.01)

        # create a smiluation in another process

        print("waiting for robot to be ready...")
        while not self.is_ready():
            time.sleep(0.01)
        print("robot is ready!")

    def is_ready(self):
        return self.getJointStates() is not None

    def set_cmd(self, cmd):
        """ """
        # create the dds message
        # Get the current time
        now = datetime.now()

        # Format the time as a string with up to milliseconds
        timestamp_str = now.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

        # print("Timestamp with milliseconds:", timestamp_str)
        msg_out = FlexivCmd(
            tau_ff=cmd["tau_ff"],
            q=cmd["q"],
            dq=cmd["dq"],
            kp=cmd["kp"],
            kv=cmd["kv"],
            timestamp=timestamp_str,
        )

        self.writer.write(msg_out)

    def step(self):
        """ """
        if not self.warning_step_msg_send:
            self.warning_step_msg_send = True
            print(
                "WARNING: In the client the step runs asynchronusly! \n Wee keep the function here to use same interface!"
            )

    def close(self):
        """ """
        print("closing the robot!")
        if self.create_server:
            print("closing the server")
            self.server_process.terminate()  # Terminate the process
            self.server_process.wait()  # Wait for the process to fully close

    def getJointStates(self):
        """ """
        state = None
        last_msg = self.reader.take()  # last message is a list of 1 or empty

        if last_msg:
            while True:
                a = self.reader.take()
                if not a:
                    break
                else:
                    last_msg = a
            msg = last_msg[0]  # now this is the last message
            if msg and type(msg) is FlexivState:
                return {"q": msg.q, "dq": msg.dq}

        else:
            return None