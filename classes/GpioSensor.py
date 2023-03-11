import RPi.GPIO as GPIO
import time
import FakeSensor

class GpioSensor(FakeSensor):
  def init(self):
    # BCM GPIO-Referenen verwenden (anstelle der Pin-Nummern)
    # und GPIO-Eingang definieren
    GPIO.setmode(GPIO.BCM)

    # Set pin as input
    GPIO.setup(self.gpioPir,GPIO.IN)

    self.callback(event = 'init', gpioPir = self.gpioPir)

  def getCurrentState(self):
    return GPIO.input(self.gpioPir)

  def stop(self):
    self.halt = True
    self.callback(event = 'exit')
    GPIO.cleanup()