import datetime

class TimedCommand():
  
  def __init__(self, periods = '00:00-23:59', priority = 1, name = '', payload = None):
    self.periods = periods
    self.priority = priority
    self.payload = payload
    self.name = name
    self.active = False

  def isDue(self):
    try:
        periods = self.periods.split(",")
    except AttributeError:
        return True
    match = 0
    for period in periods:
      if self.isTimeWithinRange(period):
        match = match + 1
    return match > 0
  
  def isTimeWithinRange(self, period):
    times = period.split("-")
    now = datetime.datetime.now()
    if len(times) == 1:
      t = self.createTimeFromString(times[0])
      if now.time()>=t.time() and now.time()<=(t + datetime.timedelta(seconds=60)).time():
        return True
    else:
      t1 = self.createTimeFromString(times[0])
      t2 = self.createTimeFromString(times[1])
      if now.time()>t1.time() and now.time()<t2.time():
        return True
      
  def createTimeFromString(self, string):
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