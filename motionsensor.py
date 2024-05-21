#!/usr/bin/python
# -*- coding: iso-8859-1 -*-

from classes.MotionSensor import MotionSensor

def checkIfShairportIsNotStreaming(self, effectiveSensorState, sensorState):
    if (effectiveSensorState == "1" and sensorState == "0"):
        self.log("make sure shairport is not streaming before setting sensor state switch to 'Idle' (0)")
        return True

motionSensor=MotionSensor()
motionSensor.onBeforeTriggerStateChange = checkIfShairportIsNotStreaming
