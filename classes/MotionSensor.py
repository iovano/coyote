import argparse
import sys
import subprocess
import time
import datetime

from classes.Scheduler import Scheduler
from classes.ConfigReader import ConfigReader
from classes.Logger import Logger
from classes.TimedCommand import TimedCommand
try:
    from classes.GpioSensor import GpioSensor
except ImportError:
    from classes.FakeSensor import FakeSensor

class MotionSensor():
    scheduler = None
    sensor = None
    config = None

    halt = False

    def __init__(self):
        self.init()

    ################################
    #
    # OPTIONAL LISTENERS
    #

    onTriggerStateChange = None
    onBeforeTriggerStateChange = None
    onTriggerStateChange = None
    onExecuteCommand = None

    ################################
    #
    # DIGEST PARAMETERS
    #

    def parseArguments(self):
        # Construct the argument parser
        ap = argparse.ArgumentParser()

        # Add the arguments to the parser
        ap.add_argument("-v", "--verbosity", required=False, default='2',
            help="verbosity level. default: 2")
        ap.add_argument("-l", "--logfile", required=False,
            help="logfile name. if specified, all log messages will be written to the specified file instead of stdout. default: none")
        ap.add_argument("-m", "--mode", required=False, nargs='?', default='a+',
            help="open logfile in specified file mode (use w+ to create new file and overwrite existing messages). default: a+ (append)")
        ap.add_argument("-o", "--overwrite", required=False, nargs='?', const='w+', default='',
            help="open logfile and overwrite existing messages (uses w+ when opening log file)")
        ap.add_argument('-c', "--interval_commands", required=False, nargs='?', const=5, default=5,
            help="specifies the refreshment interval for timed commands. default: 5 seconds")
        ap.add_argument('-i', "--interval_detection", required=False, nargs='?', const=1, default=1,
            help="specifies the motion detection interval. default: 1 second")
        ap.add_argument('-r', "--interval_config_refresh", required=False, nargs='?', const=1, default=60,
            help="specifies configuration refresh interval. if the configuration file content has changed, "
                +"its new config be automatically loaded. if set to 0, configuration will never be refreshed. default: 60 seconds"
        )
        ap.add_argument("files",nargs="*", default=['config/default.yaml'])
        
        args = vars(ap.parse_args())

        self.configFiles = args['files'] or args['files'].get('default')
        self.intervalTimedCommands = args['interval_commands'] or args['interval_commands'].get('default')
        self.intervalMotionDetection = args['interval_detection'] or args['interval_detection'].get('default')
        self.verbosity = int(args['verbosity']) or int(args['verbosity']).get('default')
        self.logfileName = self.logfileName = args['logfile'] or None
        self.mode = args['mode'] or args['mode'].get('default')
        self.intervalRefreshConfig = int(args['interval_config_refresh']) or int(args['interval_config_refresh']).get('default')
        if args['overwrite'] != '':
            self.mode = 'w+'

    def init(self):
        self.parseArguments()
        self.logger = Logger(self.logfileName or 'STD', self.verbosity);
        self.log("*** PIR-Module started (CTRL-C to exit) ***")
        self.log("Starting Infrared Movement Detection Surveillance with verbosity level '"+str(self.verbosity)+"'",3)
        if self.logfileName:
            self.log("Using file '"+self.logfileName+"' with mode '"+self.mode+"' for log messages...",3)
        
        # READ CONFIG

        self.config = ConfigReader(self.configFiles, self.onConfigLoadedEvent, False)
        self.config.load()

        
        # LAUNCH MOTION SENSOR
        try:
            self.sensor = GpioSensor(self.onSensorEvent) 
            self.log("Using RPi.GPIO adapter", 3)
        except NameError:
            self.sensor = FakeSensor(self.onSensorEvent)
            self.log("Using FakeSensor as RPi.GPIO adapter seems unavailable", 2)

        self.start()


    @staticmethod
    def dump(obj):
        for attr in dir(obj):
            print("obj.%s = %r" % (attr, getattr(obj, attr)))

    def start(self):
        self.repeatedCommand = 0
        self.waitUntil = None
        self.previousTask = None

        first = True
        lastConfigCheck = time.time()
        lastSensorStateChange = None
        effectiveSensorState = None
        sensorState = None
        sensorPreviousState = None
        # motion detection and command ignition loop
        while self.halt == False:
            try:
                if not first:
                    time.sleep(self.intervalMotionDetection)

                sensorPreviousState = sensorState

                # get the current Sensor status from the GPIO port
                sensorState = self.sensor.getCurrentState()

                if (sensorState != sensorPreviousState):
                    self.log("Sensor State Change detected (last: "+str(sensorPreviousState or "-")+" new: "+str(sensorState or "-")+")",5)

                # if a sensor inertia is specified, the detected sensorState will only come into effect after is has been steady for at least x seconds
                sensorInertia = int(self.config.read('trigger.'+str(sensorState)+'.inertia') or 0)
                if (self.config.read('trigger.'+str(sensorState)+'.period')):
                    periods = self.config.read('trigger.'+str(sensorState)+'.period');
                    for period in periods:
                        if (TimedCommand.isWithinRange(period)):
                            sensorInertia = periods[period]['inertia']

                if (sensorPreviousState != None and sensorState != sensorPreviousState):
                    lastSensorStateChange = time.time()
                    if (sensorInertia > 0):
                        self.log("Sensor Inertia applies (wait for "+str(sensorInertia)+"s for new sensor state to come into effect)",5)

                if lastConfigCheck < time.time() - self.intervalRefreshConfig:
                    # Check if Configuration Files have been changed
                    for configFilePath in self.configFiles:
                        fileTimestamp = ConfigReader.getTimestamp(configFilePath);
                        self.log("Checking Configuration File "+configFilePath+" for potential modifications.", 5)
                        if fileTimestamp > lastConfigCheck:
                            self.log("Configuration updated. Reloading settings.", 3)
                            self.config.load(self.configFiles)        
                            continue
                    lastConfigCheck = time.time()

                if (not lastSensorStateChange or not sensorInertia or time.time() > lastSensorStateChange + sensorInertia):
                    if (not self.onBeforeTriggerStateChange or self.onBeforeTriggerStateChange(self, effectiveSensorState, sensorState) != False):
                        effectiveSensorState = sensorState

                first = False
                self._onTriggerStateChange(effectiveSensorState)

            except KeyboardInterrupt:
                self.stop()

    def _onTriggerStateChange(self, effectiveSensorState):
        if (self.onTriggerStateChange):
            if (self.onTriggerStateChange(self, effectiveSensorState) == False):
                return
            
        tc = self.scheduler.getMergedTask(effectiveSensorState)
        if not tc:
            self.log("No task available. Please check configuration", 3)
            return
        
        # do not proceed unless the waiting period has expired (or 'wakeup' parameter is set for the current command)
        if not tc.get('wakeup') and self.waitUntil and time.time() < self.waitUntil:
            return
        else:
            self.waitUntil = None

        # avoid redundant command executions (unless redundant executions are within a potentially given "redundancy"-range)
        if (tc.name == self.previousTask and not tc.get('redundancy') or self.repeatedCommand > (tc.get('redundancy') or 0)):
            self.log("skipping redundant command execution ("+tc.name+")", 5)
            return


        self.log(tc.name+": ["+str(tc.get('periods'))+"] (trigger: "+str(tc.get('trigger'))+"/"+str(effectiveSensorState)+" prio: "+str(tc.get('priority'))+" duration: "+str(tc.get('duration'))+")", 3)

        for i in range(tc.get('repeat') or 1):
            self._onExecuteCommand(tc)

        if self.previousTask != tc.name:
            self.previousTask = tc.name
            self.repeatedCommand = 0

        # if a duration has been specified, suspend loop accordingly
        sleep = tc.get('duration');
        if (sleep):
            self.waitUntil = time.time() + int(sleep)
            self.log("sleep: current state remains for "+str(sleep)+" second(s)", 5)

    def _onExecuteCommand(self, timedCommand):
        if (self.onExecuteCommand):
            if (self.onExecuteCommand(self, timedCommand) == False):
                return
        # execute the command (once or self.repeatedCommandly as specified)
        self.execute(timedCommand.get('do'))
        self.repeatedCommand+=1
        if timedCommand.get('repeatInterval'):
            time.sleep(timedCommand.get('repeatInterval'))


    def onConfigLoadedEvent(self, **payload):   
        if (payload.get('event') == 'ConfigLoaded'):
            self.log(payload.get('event')+" - last modified: "+str(round(payload.get('age')))+"s ago")

            self.scheduler = Scheduler(self.onScheduleEvent)
            self.scheduler.set(self.config.read('schedule'))


    def onScheduleEvent(self, **payload):
        t = payload.get('tasks')[0]
        self.log(payload.get('event')+" | "+t.name,4);

    def onSensorEvent(self, **payload):
        e = payload.get('event')
        if e == 'init':
            self.execute('KEY_POWER')
            time.sleep(0.2)

            self.execute('KEY_FLASH')
            time.sleep(0.5)

            self.execute('KEY_SUSPEND')
            time.sleep(0.2)
            self.log(e,5)
        if e == 'signal':
            self.log(e,4)
        if e == 'idle':
            self.log(e,4)


    def log(self, message, level = 4):
        levels = ['FATAL', 'CRITICAL', 'ERROR', 'WARN', 'NOTICE', 'DEBUG']
        self.logger.log(message, level)
        if (self.config):
            event = self.config.read('events.'+levels[level]+'.do');
            if (event):
                self.logger.log('Event Handler called for '+levels[level]+': '+event, 4)
                self.execute(event, False)

    def execute(self, command, logging = True):
        commands = command.split(',')
        for command in commands:
            resolvedCommand = None
            try:
                resolvedCommand = self.config.read(['alias',command]);
            except KeyError:
                if logging: self.log("Command Key '"+command+"' not found in configuration.", 3)
            if resolvedCommand:
                cmd = self.config.read('prefix')+resolvedCommand
            else:
                cmd = command
            if logging: self.log("Executing Command: "+cmd, 4)

            # execute shell command and return result if an error occurs
            pipe = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            res = pipe.communicate()
            if pipe.returncode != 0:
                if logging: self.log("Command execution failed (code "+str(int(pipe.returncode))+"): "+ str(res[1]), 2)
            time.sleep(0.2)

    def stop(self):
        self.log("terminate motion surveillance")
        self.halt = True