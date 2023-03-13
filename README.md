# coyote

This application uses *ir-ctl* and *RPi.GPIO* to implement a infrared motion detection system on a *Raspberry Pi (RPi)* device. The app can be used to trigger various events (e.g. lighting control, audio playback, notification messages...) either on motion detection or according to a configured time schedule.

The file /config/default.yaml contains a configuration example of how to set up the COYOTE application.

# Prerequisites

In order to use this application, you will need these pieces of hardware:

* 1 Raspberry Pi (RPi 3 Model B or newer recommended): https://www.google.com/search?q=raspberry+model+b
* 1 Infrared Motion Detection device: https://www.google.com/search?q=RPI+HC-SR501
* 1 Infrared Receiver and Sender: https://www.google.com/search?q=KY-005 and https://www.google.com/search?q=KY-022
* OR 1 IR Transceiver (gadget capable of both sending and receiving IR signals): https://www.google.com/search?q=DEBO+IR+38KHZ

Optional:
* 1 RGB(W)-lighting component (e.g. an LED-strip) with infrared remote controlling capability
* Audio Speakers connected to your Raspberry Pi to trigger audio playback 

# Install and setup devices

Before you can use the motion detection bundle, you have to connect the depicted Infrared modules to your Raspberry Pi using the provided GPIO input/output pins on the device. A comprehensive GPIO pinout chart can be found here: https://community.element14.com/products/raspberry-pi/m/files/17428

After you have successfully connected and tested the IR modules, you will most likely need to scan the IR codes sent by the Infrared Remote Control of your Lighting device. There is a through description of how to do so here: https://blog.gordonturner.com/2020/05/31/raspberry-pi-ir-receiver/

You will need to either adjust the configuration file /config/default.yaml in order to use the correct IR signals for your lighting device or create a custom configuration file according to your needs (recommended).

# Furter Readings:
* RPI.GPIO: How to install, setup and use the GPIO bundle on Raspberry Pi devices: https://pypi.org/project/RPi.GPIO
* IR-CTL: Scan, store and trigger Infrared Commands via the command-line: https://manpages.ubuntu.com/manpages/bionic/man1/ir-ctl.1.html
