#!/usr/bin/python3
# -*- coding: iso-8859-1 -*-

from classes.MotionSensor import MotionSensor
import os.path
import types

def checkIfShairportIsNotStreaming(self, effectiveSensorState, sensorState):
    if (int(effectiveSensorState or 0) == 1 and int(sensorState) == 0):
        isStreaming = os.path.isfile("/tmp/shairport-playing")
        if (isStreaming):
            self.log("active shairport stream prevents Idle mode", 4)
        return (not isStreaming) # if shairport is streaming, return False and hereby prevent state change

motionSensor = MotionSensor(False)
motionSensor.onBeforeTriggerStateChange = types.MethodType(checkIfShairportIsNotStreaming, motionSensor)
motionSensor.start()