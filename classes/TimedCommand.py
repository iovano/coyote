import datetime

class TimedCommand():
  
  def __init__(self, periods = '00:00-23:59', priority = 1, name = '', payload = None):
    self.periods = periods
    self.priority = priority
    self.payload = payload
    self.name = name
    self.active = False

  def isDue(self, default = None):
    try:
      return self.isWithinRange(self.periods)
    except AttributeError:
      return default

  @staticmethod
  def isWithinRange(periods):
    periods = periods.split(",")
    for period in periods:
      times = period.split("-")
      now = datetime.datetime.now()
      if len(times) == 1: # we are dealing with a moment (e.g. 20:15)
        t = TimedCommand.createTimeFromString(times[0])
        if now.time()>=t.time() and now.time()<=(t + datetime.timedelta(seconds=60)).time():
          return True
      else: # we are dealing with a time range (e.g. 20:15-21:45)
        t1 = TimedCommand.createTimeFromString(times[0])
        t2 = TimedCommand.createTimeFromString(times[1])
        if now.time()>t1.time() and now.time()<t2.time():
          return True
    return False
      
  @staticmethod
  def createTimeFromString(string):
    try:
      time = datetime.datetime.strptime(string, '%H:%M:%S')
    except ValueError:
      time = datetime.datetime.strptime(string, '%H:%M')
    return time 
  
  def get(self, key, default = None):
    try:
      return getattr(self, key) if hasattr(self, key) else self.payload[key]
    except KeyError:
      return default
    
  def activate(self):
    self.active = True

  def terminate(self):
    self.active = False

  def isActive(self):
    return self.active