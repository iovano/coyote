#!/usr/bin/python3
# -*- coding: iso-8859-1 -*-

from classes.MotionSensor import MotionSensor
import os.path
import types

def checkIfShairportIsNotStreaming(self, effectiveSensorState, sensorState):
    if (effectiveSensorState == "1" and sensorState == "0"):
        isStreaming = os.path.isfile("/tmp/shairport-playing")
        if (isStreaming):
            self.log("shairport is streaming. preventing Idle mode", 4)
        return (not isStreaming)

motionSensor = MotionSensor(False)
motionSensor.onBeforeTriggerStateChange = types.MethodType(checkIfShairportIsNotStreaming, motionSensor)
motionSensor.start()