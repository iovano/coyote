import RPi.GPIO as GPIO
import time

class GpioSensor():
  def __init__(self, callback, interval = 1, autoStart = False):
    self.interval = interval
    self.currentStatus = 0
    self.recentStatus = 0
    self.callback = callback
    self.halt = False

    self.gpioPir = 23

    self.init()

    if autoStart:
      self.start()

  def init(self):
    # BCM GPIO-Referenen verwenden (anstelle der Pin-Nummern)
    # und GPIO-Eingang definieren
    GPIO.setmode(GPIO.BCM)

    # Set pin as input
    GPIO.setup(self.gpioPir,GPIO.IN)

    self.callback(event = 'init', gpioPir = self.gpioPir)

  def listen(self):
    self.recentStatus = self.currentStatus
    self.currentStatus = self.getCurrentState()

    if self.currentStatus != self.recentStatus:
      self.callback(event = 'stateChange', current = self.currentStatus, recent = self.recentStatus)

    if self.currentStatus == 1 and self.recentStatus == 0:
      self.callback(event = 'signal', current = self.currentStatus, recent = self.recentStatus)
    elif self.currentStatus == 0 and self.recentStatus == 1:
      self.callback(event = 'idle', current = self.currentStatus, recent = self.recentStatus)

    return self.currentStatus

  def getCurrentState(self):
    return GPIO.input(self.gpioPir)

  def start(self):
    try:
      while not self.halt:
        self.listen()
        time.sleep(self.interval)
    except KeyboardInterrupt:
      self.stop()

  def stop(self):
    self.halt = True
    self.callback(event = 'exit')
    GPIO.cleanup()