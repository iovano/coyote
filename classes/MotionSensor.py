import argparse
import sys
import subprocess
import time

from classes.Scheduler import Scheduler
from classes.ConfigReader import ConfigReader
from classes.Logger import Logger
try:
    from classes.GpioSensor import GpioSensor
except ImportError:
    from classes.FakeSensor import FakeSensor

class MotionSensor():
    taskWaiting = None
    taskNext = None
    taskActive = None
    taskRecent = None

    scheduler = None
    sensor = None

    halt = False

    def __init__(self):
        self.init()

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

        args = vars(ap.parse_args())

        self.intervalTimedCommands = args['interval_commands'] or args['interval_commands'].get('default')
        self.intervalMotionDetection = args['interval_detection'] or args['interval_detection'].get('default')
        self.verbosity = int(args['verbosity']) or int(args['verbosity']).get('default')
        self.logfileName = self.logfileName = args['logfile'] or None
        self.mode = args['mode'] or args['mode'].get('default')
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

        self.config = ConfigReader('config/default.yaml', self.onConfigEvent)
        
        # LAUNCH SCHEDULER

        self.scheduler = Scheduler(self.onScheduleEvent)
        self.scheduler.set(self.config.read('schedule'))

        # LAUNCH MOTION SENSOR
        try:
            self.sensor = GpioSensor(self.onSensorEvent) 
        except NameError:
            self.sensor = FakeSensor(self.onSensorEvent)

        self.start()

    @staticmethod
    def dump(obj):
        for attr in dir(obj):
            print("obj.%s = %r" % (attr, getattr(obj, attr)))

    def start(self):
        first = True
        previousTask = None
        repeated = 0
        waitUntil = None
        # motion detection and command ignition loop
        while self.halt == False:
            try:
                if not first:
                    time.sleep(self.intervalMotionDetection)
                sensorState = self.sensor.getCurrentState()
                tc = self.scheduler.getMergedTask(sensorState)
                first = False
                
                # do not proceed unless the waiting period has expired (or 'wakeup' parameter is set for the current command)
                if not tc.get('wakeup') and waitUntil and time.time() < waitUntil:
                    self.log("waiting for "+str(int(waitUntil - time.time()))+" second(s)...", 5)
                    continue
                else:
                    waitUntil = None

                # avoid redundant command executions (unless redundant executions are within a potentially given "redundancy"-range)
                if (tc.get('do') == previousTask and not tc.get('redundancy') or repeated > (tc.get('redundancy') or 0)):
                    self.log("skipping redundant command execution ("+tc.get('do')+")", 5)
                    continue

                self.log(tc.name+": ["+str(tc.get('periods'))+"] "+tc.get('do')+" (trigger: "+str(tc.get('trigger'))+"/"+str(sensorState)+" prio: "+str(tc.get('priority'))+" duration: "+str(tc.get('duration'))+")")

                for i in range(tc.get('repeat') or 1):
                    # execute the command (once or repeatedly as specified)
                    self.execute(tc.get('do'))
                    repeated+=1
                    if tc.get('repeatInterval'):
                        time.sleep(tc.get('repeatInterval'))

                if previousTask != tc.get('do'):
                    previousTask = tc.get('do')
                    repeated = 0

                # if a duration has been specified, suspend loop accordingly
                sleep = tc.get('duration');
                if (sleep):
                    waitUntil = time.time() + int(sleep)
                    self.log("sleep for "+str(sleep)+" second(s)")

            except KeyboardInterrupt:
                self.stop()

    def onConfigEvent(self, **payload):   
        self.log(payload.get('event'))

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


    def log(self, message, level = 2):
        self.logger.log(message, level)

    def execute(self, command):
        cmd = self.config.read('prefix')+self.config.read(['alias',command])
        self.log("Executing Command: "+cmd)
        #  args = shlex.split(command)
        #  process = subprocess.Popen(args, stdout=subprocess.PIPE, smotionmotderr=subprocess.PIPE)
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        time.sleep(0.2)

    def stop(self):
        self.log("terminate motion surveillance")
        self.halt = True