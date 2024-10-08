

import os
import sys
import math
import time
import datetime
import RPi.GPIO



# GPIO Pin connected to IR receiver.
# GPIO_RX_PIN = 26
GPIO_RX_PIN = 21
# GPIO Pin connected to IR transmitter.
GPIO_TX_PIN = 19

# GPIO level to switch transmitter off.
TX_OFF_LEVEL = 0
# GPIO level to switch transmitter off.
TX_ON_LEVEL = 1
# Period to signify end of Rx message.
RX_END_PERIOD = 0.01
# Smallest period of high or low signal to consider noise rather than data, and flag as bad data. 
RX_REJECT_PERIOD = 0.000001
# Minimum received valid packet size.
MIN_RX_BYTES = 4



#  /*******************************************/
# /* Configure Raspberry Pi GPIO interfaces. */
#/*******************************************/
RPi.GPIO.setwarnings(False)
RPi.GPIO.setmode(RPi.GPIO.BCM)
RPi.GPIO.setup(GPIO_RX_PIN, RPi.GPIO.IN, pull_up_down=RPi.GPIO.PUD_UP)
RPi.GPIO.setup(GPIO_TX_PIN, RPi.GPIO.OUT, initial=TX_OFF_LEVEL)


# Initialise data.
StartBitFlag = True
ThisPeriod = RX_END_PERIOD
StartBitPeriod = RX_END_PERIOD
LastBitPeriod = RX_END_PERIOD
LastGpioLevel = TX_ON_LEVEL
DataValues = []

# Infinate loop for this application.
sys.stdout.write("\nWAITING FOR DATA...\n\n")
sys.stdout.flush()
ExitFlag = False
while ExitFlag == False:
   # Check if data is currently being received.
   ThisPeriod = time.time()
   DiffPeriod = ThisPeriod - LastBitPeriod

   # If data level changes, decode long period = 1, short period = 0.
   GpioLevel = RPi.GPIO.input(GPIO_RX_PIN)
   if GpioLevel != LastGpioLevel:
      # Ignore noise.
      if DiffPeriod > RX_REJECT_PERIOD:
         # Wait for start of communication.
         if StartBitFlag == True:
            # Calculate start bit period, consider as period for all following bits.
            if StartBitPeriod == RX_END_PERIOD:
               StartBitPeriod = ThisPeriod
            else:
               StartBitPeriod = (ThisPeriod - StartBitPeriod)
               StartBitFlag = False
         # Receiving a data level, convert into a data bit.
         if StartBitFlag == False:
            DataValues.append(DiffPeriod)
         LastBitPeriod = ThisPeriod
      LastGpioLevel = GpioLevel
   elif DiffPeriod > RX_END_PERIOD:
      # End of data reception.
      if len(DataValues) >= MIN_RX_BYTES and StartBitPeriod > RX_REJECT_PERIOD:
         sys.stdout.write("RECEIVED DATA:\n")
         for Count in range(len(DataValues)):
            sys.stdout.write("{:f} ".format(DataValues[Count]))
         sys.stdout.write("\n")
         GpioLevel = TX_ON_LEVEL
         for Count in range(len(DataValues)):
            if (Count % 5) == 0:
               sys.stdout.write("\n")
            sys.stdout.write("{:03d} {:d} {:f}\t".format(Count, GpioLevel, DataValues[Count]))
            if GpioLevel == TX_OFF_LEVEL:
               GpioLevel = TX_ON_LEVEL
            else:
               GpioLevel = TX_OFF_LEVEL
         sys.stdout.write("\n\n")
         sys.stdout.flush()

      # Reset data to start a new monitor period.
      StartBitFlag = True
      StartBitPeriod = RX_END_PERIOD
      DataValues = []