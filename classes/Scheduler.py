import time
import datetime
from classes.TimedCommand import TimedCommand

class Scheduler():
    duration = 0
    interval = 1
    timeStart = 0
    timedCommands = []
    callback = None
    activeCommands = []

    def __init__(self, callback):
        self.time_start = time.time()
        self.callback = callback
    
    def run(self):
        run_start = time.time()
        trigger = 1
        firstRun = True
        while time.time() <= (run_start + self.duration) or not self.duration:
            if firstRun == False:
                time.sleep(self.interval)
            tasks = self.getCurrentTasks(trigger = trigger)
            if self.callback:
                self.callback(event = 'schedule', tasks = tasks)
            firstRun = False
    
    def set(self, schedule, useDefaults = '_defaults'):
        self.schedule = schedule
        self.timedCommands = []
        # populate timedCommands list by schedule configuration items, using defaults from "_defaults"
        for name in self.schedule:
            try:
                item = {**self.schedule[useDefaults], **self.schedule[name]} if useDefaults else self.schedule[name]
            except KeyError:
                item = self.schedule[name]
            if name != useDefaults or not useDefaults:
                tc = TimedCommand(periods = item.get('period'), priority = item.get('priority'), name = name, payload = item);
                self.timedCommands.append(tc)
        # sort timedCommands list by priority (0 = high, ..., 10 = low)w
        self.timedCommands.sort(key=lambda tc: tc.priority)

    def getMergedTask(self, trigger = None):
        tasks = self.getCurrentTasks(trigger = trigger, maxConcurrentTasks = None)
        try:
            mainTask = tasks[0]              
            tasks.sort(key=lambda tc: tc.priority, reverse=True)
            mergedPayload = None
            for task in tasks:
                mergedPayload = {**mergedPayload, **task.payload} if mergedPayload else task.payload
            mainTask.payload = mergedPayload
            return mainTask
        except IndexError:
            return None

    def getCurrentTasks(self, trigger = None, maxConcurrentTasks = None):
        tasks = []
        self.activeCommands = []
        for tc in self.timedCommands:
            if tc.isDue() and ((tc.get('trigger') == None) or (tc.get('trigger')==trigger)):
                tasks.append(tc)
                if maxConcurrentTasks == None or len(self.activeCommands) < maxConcurrentTasks: 
                    tc.activate()
                    self.activeCommands.append(tc)
                else:
                    tc.terminate()
            else:
                tc.terminate()
        return tasks